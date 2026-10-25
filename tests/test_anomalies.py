# -*- coding: utf-8 -*-
"""Anomaly rules (analysis/anomalies.py): pure functions on stored per-flight values."""

import json

import pandas as pd
import pytest

from helpers import ela  # noqa: F401  (puts src on the path)
from ethosloganalyser.analysis.anomalies import (CRITICAL, INFO, MIN_FLIGHTS_FOR_MEDIAN, RULES, RuleSettings,
                                                 WARNING, find_anomalies)
from ethosloganalyser.config import Params
from ethosloganalyser.i18n import set_language

LI_ION_13S = Params(chem="Li-Ion", cells=13, nominal_mah=9000)

# a normal flight of a 13S Li-Ion electric jet, like the example logs
NORMAL_METRICS = {"Ri_mOhm": 57.0, "RxStrom_max_A": 3.6, "RSSI_min": 37.0, "RxBatt_min_V": 7.9, "U_min_V": 40.5,
                  "U_ruhe_start_V": 54.7, "U_start_V": 54.6, "U_ruhe_nach_V": 45.5, "U_last_ende_V": 44.5,
                  "U_ocv_ende_V": 45.4, "RxSp_ohne": 0, "entnommen_mAh": 5900.0, "ESC_mAh": 5850.0,
                  "I_mittel_A": 42.0, "I_max_A": 118.0}
NORMAL_SIGNAL = {"rx_voltage_median_V": 8.0, "rx_voltage_min_V": 7.9, "rx_voltage_dip_pct": 1.5,
                 "rx_voltage_dip_time_s": 120.0}


def flight(log_id, aircraft="Jet", duration_s=500.0, metrics=None, signal=None, is_flight=1, **changes):
    """One row as db.annotations.rule_input_rows gives it; changes overwrite single metrics."""
    values = dict(NORMAL_METRICS if metrics is None else metrics)
    values.update(changes)
    return {"log_id": log_id, "aircraft": aircraft, "start_time": f"2026-05-{log_id:02d}T12:00:00",
            "is_flight": is_flight, "duration_s": duration_s,
            "metrics": json.dumps(values) if values else None,
            "signal_metrics": json.dumps(NORMAL_SIGNAL if signal is None else signal)}


def rows(*flights):
    return pd.DataFrame(list(flights))


def findings(table, settings=None, battery=LI_ION_13S):
    return find_anomalies(table, settings or RuleSettings(), lambda aircraft: battery)


def rules_found(found):
    return sorted((finding.log_id, finding.rule) for finding in found)


def normal_flights(count, **kwargs):
    return [flight(log_id, **kwargs) for log_id in range(1, count + 1)]


def test_normal_flights_have_no_anomalies():
    assert findings(rows(*normal_flights(8))) == []


def test_median_rules_need_five_flights_of_the_aircraft():
    few = normal_flights(MIN_FLIGHTS_FOR_MEDIAN - 2) + [flight(9, duration_s=150.0)]
    assert findings(rows(*few)) == []
    enough = normal_flights(MIN_FLIGHTS_FOR_MEDIAN - 1) + [flight(9, duration_s=150.0)]
    found = findings(rows(*enough))
    assert rules_found(found) == [(9, "short_flight")]
    assert found[0].severity == INFO and found[0].value == 150.0


def test_the_median_is_taken_per_aircraft():
    # the glider flies much shorter: compared with its own flights it is normal
    table = rows(*normal_flights(6), *[flight(20 + k, aircraft="Glider", duration_s=200.0) for k in range(6)])
    assert findings(table) == []


def test_non_flights_are_not_judged_and_do_not_count_for_the_median():
    table = rows(*normal_flights(6), flight(30, duration_s=30.0, is_flight=0))
    assert findings(table) == []


def test_internal_resistance_above_the_median_but_not_a_failed_fit():
    table = rows(*normal_flights(6), flight(10, Ri_mOhm=80.0), flight(11, Ri_mOhm=150.0))
    assert rules_found(findings(table)) == [(10, "ri_high")]       # 150 mΩ is more than twice: a failed fit


def test_receiver_current_and_rssi_against_the_median():
    table = rows(*normal_flights(6), flight(10, RxStrom_max_A=6.0), flight(11, RSSI_min=24.0))
    assert rules_found(findings(table)) == [(10, "rx_current_high"), (11, "rssi_low")]


def test_receiver_voltage_dip_within_the_flight():
    dip = dict(NORMAL_SIGNAL, rx_voltage_min_V=6.2, rx_voltage_dip_pct=22.5, rx_voltage_dip_time_s=488.0)
    found = findings(rows(flight(1, signal=dip)))
    assert rules_found(found) == [(1, "rx_voltage_dip")]
    set_language("de")
    assert "8:08" in str(found[0].message) and "6.20 V" in str(found[0].message)


def test_cell_chemistry_limits_only_with_chosen_battery_settings():
    table = rows(flight(1, U_min_V=35.0, U_last_ende_V=40.0, U_ruhe_nach_V=41.0))   # 2.69 V/cell loaded, 3.15 at rest
    assert rules_found(findings(table)) == [(1, "cell_voltage_load"), (1, "cell_voltage_rest")]
    assert {finding.severity for finding in findings(table)} == {CRITICAL}
    assert findings(table, battery=None) == []                       # assumed defaults: no limits


def test_impossible_rest_voltage_uses_the_model_estimate():
    # measured resting voltage below the voltage under load at the end: battery unplugged, not a deep discharge
    table = rows(flight(1, U_ruhe_nach_V=38.0, U_last_ende_V=44.9, U_ocv_ende_V=46.5))
    assert findings(table) == []


def test_sensor_dropout_is_no_cell_voltage_finding():
    table = rows(flight(1, U_min_V=12.0))                             # 0.9 V/cell: the sensor failed
    assert findings(table) == []


def test_cell_count_is_estimated_when_not_configured():
    automatic = Params(chem="Li-Ion", cells=0)
    table = rows(flight(1, U_min_V=35.0))
    assert rules_found(findings(table, battery=automatic)) == [(1, "cell_voltage_load")]


def test_aircraft_without_battery_or_motor_data_gets_the_rules_it_has_data_for():
    gliders = [flight(k, aircraft="Glider", metrics={}, duration_s=900.0) for k in range(1, 7)]
    dip = dict(NORMAL_SIGNAL, rx_voltage_dip_pct=30.0)
    table = rows(*gliders, flight(7, aircraft="Glider", metrics={}, duration_s=200.0, signal=dip))
    assert rules_found(findings(table)) == [(7, "rx_voltage_dip"), (7, "short_flight")]
    no_signal = rows(*[flight(k, metrics={}, signal={}) for k in range(1, 7)])
    assert findings(no_signal) == []


def test_receiver_minimum_voltage_per_aircraft():
    settings = RuleSettings(rx_min_voltage={"Jet": 7.95})
    table = rows(flight(1), flight(2, aircraft="Other"))
    found = findings(table, settings)
    assert rules_found(found) == [(1, "rx_voltage_limit")] and found[0].severity == WARNING
    assert findings(table) == []                                     # off without a value


def test_fixed_limits_for_spikes_and_current_sensor():
    table = rows(flight(1, RxSp_ohne=3), flight(2, ESC_mAh=5000.0))
    assert rules_found(findings(table)) == [(1, "rx_spikes_no_cause"), (2, "current_sensor_deviation")]


def test_rules_can_be_switched_off_and_thresholds_changed():
    table = rows(*normal_flights(6), flight(10, duration_s=150.0))
    assert findings(table, RuleSettings(enabled={"short_flight": False})) == []
    assert findings(table, RuleSettings(thresholds={"short_flight": 20.0})) == []
    stricter = RuleSettings(thresholds={"rx_voltage_dip": 1.0})
    assert len(findings(rows(flight(1)), stricter)) == 1


def test_rule_settings_are_stored_and_read_back():
    settings = RuleSettings(enabled={"ri_high": False}, thresholds={"rssi_low": 15.0},
                            rx_min_voltage={"Jet": 7.2, "Other": 0.0})
    stored = settings.to_dict()
    assert stored["rx_min_voltage"] == {"Jet": 7.2}
    again = RuleSettings.from_dict(json.loads(json.dumps(stored)))
    assert again.signature() == settings.signature()
    assert not again.is_enabled("ri_high") and again.threshold("rssi_low") == 15.0
    junk = RuleSettings.from_dict({"enabled": {"unknown": True}, "thresholds": {"rssi_low": "x", "ri_high": -1}})
    assert junk.enabled == {} and junk.thresholds == {}
    assert RuleSettings.from_dict(None).threshold("short_flight") == 50.0


@pytest.mark.parametrize("language", ["de", "en", "es"])
def test_messages_are_language_neutral_and_shown_in_every_language(language):
    table = rows(*normal_flights(6), flight(10, duration_s=150.0, U_min_V=35.0, RxSp_ohne=4))
    set_language(language)
    try:
        texts = [str(finding.message) for finding in findings(table)]
    finally:
        set_language("de")
    assert len(texts) == 3 and all(texts)


def test_every_rule_has_a_unique_code():
    codes = [rule.code for rule in RULES]
    assert len(codes) == len(set(codes))
