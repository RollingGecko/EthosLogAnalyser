# -*- coding: utf-8 -*-
"""Automatic anomalies of flights: the rules, their settings and how they judge the stored values.

Everything here works on the values stored with every flight (metrics of analysis/flight.py and the signal
metrics of db/signal_metrics.py) - no time series, no raw logs - so all flights are judged again in well under a
second. Every message is a hint or an estimate, never a diagnosis.

Four kinds of rules:

* MEDIAN - compare a flight with the median of all flights of the same aircraft (from MIN_FLIGHTS_FOR_MEDIAN on).
  Such a rule adapts to every aircraft; a fixed limit would fit only one of them.
* WITHIN_FLIGHT - a dip within the flight, relative to the flight's own typical value.
* CHEMISTRY - limits of the cell chemistry set for the aircraft (only when its battery settings have been
  chosen; with the assumed default LiPo the limits could be wrong).
* LIMIT - a fixed value: the receiver minimum voltage per aircraft (off until the user enters one) and the
  limits the statistics already use for receiver current spikes and the current sensor.

A rule judges only flights that have its values; aircraft without motor or battery sensors simply get no
findings from the battery rules. See docs/methodology.md for the standard values and how they were chosen.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd

from ..config import CHEM
from ..i18n import Msg, N_
from ..utils import _mmss
from .quality import cell_count, current_stuck, rest_voltage_invalid

INFO, WARNING, CRITICAL = "info", "warning", "critical"

MEDIAN, WITHIN_FLIGHT, CHEMISTRY, LIMIT = "median", "within_flight", "chemistry", "limit"

MIN_FLIGHTS_FOR_MEDIAN = 5

# above this many times the median, a receiver current or internal resistance is a measurement error rather than
# a finding (same limit as analysis/quality.py for the internal resistance)
MEASUREMENT_ERROR_FACTOR = 2.0


@dataclass(frozen=True)
class Rule:
    """One rule: its code (stored with every finding), kind, severity and adjustable threshold."""
    code: str
    kind: str
    severity: str
    label: str                       # N_() text: name of the rule
    threshold: Optional[float]       # standard value; None = the rule has no adjustable value
    unit: str = ""


RULES = (
    Rule("short_flight", MEDIAN, INFO, N_("Flug deutlich kürzer als üblich"), 50.0, "%"),
    Rule("ri_high", MEDIAN, WARNING, N_("Innenwiderstand höher als üblich"), 30.0, "%"),
    Rule("rx_current_high", MEDIAN, WARNING, N_("Empfängerstrom-Maximum höher als üblich"), 50.0, "%"),
    Rule("rssi_low", MEDIAN, WARNING, N_("RSSI-Minimum niedriger als üblich"), 10.0, "dB"),
    Rule("rx_voltage_dip", WITHIN_FLIGHT, WARNING, N_("Einbruch der Empfängerspannung im Flug"), 10.0, "%"),
    Rule("cell_voltage_load", CHEMISTRY, CRITICAL, N_("Zellspannung unter Last unter der Grenze der Zellchemie"),
         None),
    Rule("cell_voltage_rest", CHEMISTRY, CRITICAL, N_("Ruhespannung am Flugende unter der Grenze der Zellchemie"),
         None),
    Rule("rx_voltage_limit", LIMIT, WARNING, N_("Empfängerspannung unter der Mindestspannung des Modells"), None,
         "V"),
    Rule("rx_spikes_no_cause", LIMIT, WARNING, N_("Empfängerstrom-Spitzen ohne erkennbaren Anlass"), 3.0, ""),
    Rule("current_sensor_deviation", LIMIT, INFO, N_("Strommessung weicht vom ESC-Zähler ab"), 5.0, "%"),
)

RULES_BY_CODE = {rule.code: rule for rule in RULES}

# what the adjustable value of a rule means (shown next to the input field)
THRESHOLD_HINTS = {
    "short_flight": N_("kürzer als dieser Anteil des Medians"),
    "ri_high": N_("über dem Median"),
    "rx_current_high": N_("über dem Median"),
    "rssi_low": N_("unter dem Median"),
    "rx_voltage_dip": N_("unter dem eigenen Median des Flugs"),
    "rx_spikes_no_cause": N_("Spitzen je Flug"),
    "current_sensor_deviation": N_("Abweichung"),
}


@dataclass
class RuleSettings:
    """Which rules are on, their thresholds and the receiver minimum voltage per aircraft (0 / missing = off)."""
    enabled: Dict[str, bool] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    rx_min_voltage: Dict[str, float] = field(default_factory=dict)

    def is_enabled(self, code):
        return self.enabled.get(code, True)

    def threshold(self, code):
        value = self.thresholds.get(code)
        return RULES_BY_CODE[code].threshold if value is None else value

    @classmethod
    def from_dict(cls, stored):
        """Settings as saved in the settings file; unknown rules and invalid numbers are ignored."""
        stored = stored if isinstance(stored, dict) else {}

        def numbers(mapping, keys=None):
            result = {}
            for key, value in (mapping or {}).items() if isinstance(mapping, dict) else ():
                if keys is not None and key not in keys:
                    continue
                try:
                    number = float(value)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(number) and number >= 0:
                    result[key] = number
            return result

        enabled = stored.get("enabled") if isinstance(stored.get("enabled"), dict) else {}
        return cls(enabled={code: bool(value) for code, value in enabled.items() if code in RULES_BY_CODE},
                   thresholds=numbers(stored.get("thresholds"), RULES_BY_CODE),
                   rx_min_voltage=numbers(stored.get("rx_min_voltage")))

    def to_dict(self):
        return {"enabled": dict(self.enabled), "thresholds": dict(self.thresholds),
                "rx_min_voltage": {key: value for key, value in self.rx_min_voltage.items() if value > 0}}

    def signature(self):
        """Compact value that changes whenever a setting changes (to know when to judge the flights again)."""
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass
class Finding:
    """One anomaly found by a rule."""
    log_id: int
    rule: str
    severity: str
    message: Msg                 # language-neutral: msgid and values, translated when shown
    value: float                 # the value the rule judged


# ---------------- input ----------------
# stored per-flight metrics the rules use
METRIC_KEYS = ("Ri_mOhm", "RxStrom_max_A", "RSSI_min", "RxBatt_min_V", "U_min_V", "U_ruhe_start_V", "U_start_V",
               "U_ruhe_nach_V", "U_last_ende_V", "U_ocv_ende_V", "RxSp_ohne", "entnommen_mAh", "ESC_mAh",
               "I_mittel_A", "I_max_A")
SIGNAL_KEYS = ("rx_voltage_median_V", "rx_voltage_min_V", "rx_voltage_dip_pct", "rx_voltage_dip_time_s")


def _json_columns(texts, keys):
    """The keys of every stored JSON text as float columns (NaN where missing)."""
    values = {key: np.full(len(texts), np.nan) for key in keys}
    for position, text in enumerate(texts):
        if not isinstance(text, str) or not text:
            continue
        stored = json.loads(text)
        for key in keys:
            value = stored.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values[key][position] = value
    return values


def rule_input(rows):
    """The flights the rules judge, as one table: the effective flights of ``db.annotations.rule_input_rows``
    with their metrics and signal metrics as columns."""
    flights = rows[rows["is_flight"].astype(bool)].reset_index(drop=True)
    table = pd.DataFrame({"log_id": flights["log_id"].astype(int), "aircraft": flights["aircraft"],
                          "duration_s": pd.to_numeric(flights["duration_s"], errors="coerce")})
    for key, column in {**_json_columns(list(flights["metrics"]), METRIC_KEYS),
                        **_json_columns(list(flights["signal_metrics"]), SIGNAL_KEYS)}.items():
        table[key] = column
    return table


# ---------------- the rules ----------------
def _finding(flight, rule_code, message, value):
    return Finding(log_id=int(flight["log_id"]), rule=rule_code, severity=RULES_BY_CODE[rule_code].severity,
                   message=message, value=float(value))


def _median_of(values):
    """Median of the finite values, or None if there are fewer than MIN_FLIGHTS_FOR_MEDIAN."""
    finite = values[np.isfinite(values)]
    return float(np.median(finite)) if len(finite) >= MIN_FLIGHTS_FOR_MEDIAN else None


def _short_flights(flights, threshold):
    median = _median_of(flights["duration_s"].to_numpy(dtype=float))
    if not median:
        return []
    found = []
    for _, flight in flights.iterrows():
        duration = flight["duration_s"]
        if np.isfinite(duration) and duration < median * threshold / 100.0:
            found.append(_finding(flight, "short_flight", Msg(
                "Flug deutlich kürzer als üblich: {value} statt typisch {median} (Median der Flüge dieses "
                "Flugzeugs). Nur ein Hinweis – z. B. ein abgebrochener oder vorzeitig gelandeter Flug.",
                value=_mmss(duration), median=_mmss(median)), duration))
    return found


def _internal_resistance_high(flights, threshold):
    usable = flights[~current_stuck(flights["I_mittel_A"], flights["I_max_A"])]
    resistance = usable["Ri_mOhm"].to_numpy(dtype=float)
    median = _median_of(resistance)
    if not median:
        return []
    found = []
    for (_, flight), value in zip(usable.iterrows(), resistance):
        ratio = value / median if np.isfinite(value) else np.nan
        if np.isfinite(ratio) and 1 + threshold / 100.0 < ratio <= MEASUREMENT_ERROR_FACTOR:
            found.append(_finding(flight, "ri_high", Msg(
                "Innenwiderstand {value:.0f} mΩ, {percent:.0f} % über dem Median dieses Flugzeugs ({median:.0f} mΩ). "
                "Hinweis: kalter oder nicht voll geladener Akku, Alterung oder ein kurzer Flug mit wenig "
                "Entladung sind mögliche Gründe.", value=value, percent=(ratio - 1) * 100, median=median), value))
    return found


def _receiver_current_high(flights, threshold):
    current = flights["RxStrom_max_A"].to_numpy(dtype=float)
    median = _median_of(current)
    if not median:
        return []
    found = []
    for (_, flight), value in zip(flights.iterrows(), current):
        if np.isfinite(value) and value > median * (1 + threshold / 100.0):
            found.append(_finding(flight, "rx_current_high", Msg(
                "Höchster Empfängerstrom {value:.2f} A, {percent:.0f} % über dem Median dieses Flugzeugs "
                "({median:.2f} A). Hinweis: Servos auf Schwergängigkeit oder Blockieren prüfen; Zeitpunkte der "
                "Stromspitzen siehe Diagramm „Empfängerstrom“.", value=value,
                percent=(value / median - 1) * 100, median=median), value))
    return found


def _rssi_low(flights, threshold):
    rssi = flights["RSSI_min"].to_numpy(dtype=float)
    rssi = np.where(rssi > 0, rssi, np.nan)                 # 0 = no reception value, not a weak signal
    median = _median_of(rssi)
    if median is None:
        return []
    found = []
    for (_, flight), value in zip(flights.iterrows(), rssi):
        if np.isfinite(value) and value < median - threshold:
            found.append(_finding(flight, "rssi_low", Msg(
                "RSSI-Minimum {value:.0f} dB, {difference:.0f} dB unter dem Median dieses Flugzeugs ({median:.0f} dB). "
                "Hinweis: größere Entfernung, Fluglage oder Antennen prüfen.", value=value,
                difference=median - value, median=median), value))
    return found


def _receiver_voltage_dips(flights, threshold):
    found = []
    for _, flight in flights.iterrows():
        dip = flight["rx_voltage_dip_pct"]
        if np.isfinite(dip) and dip > threshold:
            found.append(_finding(flight, "rx_voltage_dip", Msg(
                "Empfängerspannung fiel bei {time} auf {low:.2f} V, {percent:.0f} % unter ihren üblichen Wert in "
                "diesem Flug ({median:.2f} V). Hinweis: Empfängerstromversorgung, Stecker und Kabel prüfen.",
                time=_mmss(flight["rx_voltage_dip_time_s"]), low=flight["rx_voltage_min_V"], percent=dip,
                median=flight["rx_voltage_median_V"]), dip))
    return found


def _cell_voltage_limits(flights, params):
    """Load and rest voltage per cell against the limits of the cell chemistry of the aircraft."""
    chemistry = CHEM.get(params.chem)
    if chemistry is None:
        return []
    highest_start = flights["U_ruhe_start_V"].fillna(flights["U_start_V"]).max()
    cells = cell_count(params.cells, highest_start, chemistry)
    if cells <= 0:
        return []
    found = []
    for _, flight in flights.iterrows():
        load = flight["U_min_V"] / cells
        # below half the load limit the sensor failed (analysis/quality.py: voltage_dropout), it is no finding
        if np.isfinite(load) and 0.5 * chemistry["load_min"] <= load < chemistry["load_min"]:
            found.append(_finding(flight, "cell_voltage_load", Msg(
                "Spannung unter Last fiel auf {value:.2f} V/Zelle, unter die Grenze von {limit:.2f} V/Zelle für "
                "{chem} ({cells} Zellen). Hinweis: möglicherweise zu tief entladen – bitte auch Zellchemie und "
                "Zellenzahl in den Akku-Einstellungen prüfen.", value=load, limit=chemistry["load_min"],
                chem=params.chem, cells=cells), load))
        rest = _rest_voltage_at_end(flight) / cells
        if np.isfinite(rest) and 0.5 * chemistry["load_min"] <= rest < chemistry["rest_min"]:
            found.append(_finding(flight, "cell_voltage_rest", Msg(
                "Ruhespannung am Flugende {value:.2f} V/Zelle, unter der Grenze von {limit:.2f} V/Zelle für {chem} "
                "({cells} Zellen). Hinweis: möglicherweise zu tief entladen – bitte auch Zellchemie und Zellenzahl "
                "prüfen.", value=rest, limit=chemistry["rest_min"], chem=params.chem, cells=cells), rest))
    return found


def _rest_voltage_at_end(flight):
    """Measured resting voltage after landing, or the model estimate if the measurement is impossible or missing
    (as analysis/fleet.py does for the column U_ende)."""
    measured = flight["U_ruhe_nach_V"]
    if np.isfinite(measured) and not rest_voltage_invalid(measured, flight["U_last_ende_V"]):
        return measured
    return flight["U_ocv_ende_V"]


def _receiver_voltage_limit(flights, minimum):
    found = []
    for _, flight in flights.iterrows():
        lowest = flight["rx_voltage_min_V"] if np.isfinite(flight["rx_voltage_min_V"]) else flight["RxBatt_min_V"]
        if np.isfinite(lowest) and lowest < minimum:
            found.append(_finding(flight, "rx_voltage_limit", Msg(
                "Empfängerspannung fiel auf {value:.2f} V, unter die eingestellte Mindestspannung von {limit:.2f} V "
                "für dieses Modell. Hinweis: Empfängerstromversorgung prüfen.", value=lowest, limit=minimum),
                lowest))
    return found


def _spikes_without_cause(flights, threshold):
    found = []
    for _, flight in flights.iterrows():
        count = flight["RxSp_ohne"]
        if np.isfinite(count) and count >= threshold:
            found.append(_finding(flight, "rx_spikes_no_cause", Msg(
                "{n} Empfängerstrom-Spitzen ohne Manöver, Start oder Landung. Hinweis: Servos auf Schwergängigkeit, "
                "Anschlag (Brummen in Endlage) und Defekte prüfen; Zeitpunkte siehe Einzelflug.", n=int(count)),
                count))
    return found


def _current_sensor_deviation(flights, threshold):
    usable = flights[~current_stuck(flights["I_mittel_A"], flights["I_max_A"])]
    found = []
    for _, flight in usable.iterrows():
        drawn, counter = flight["entnommen_mAh"], flight["ESC_mAh"]
        if not (np.isfinite(drawn) and np.isfinite(counter) and counter > 0):
            continue
        deviation = (drawn - counter) / counter * 100.0
        if abs(deviation) > threshold:
            found.append(_finding(flight, "current_sensor_deviation", Msg(
                "Entnommene Ladung aus der Strommessung ({drawn:.0f} mAh) weicht um {percent:+.1f} % vom ESC-Zähler "
                "({counter:.0f} mAh) ab. Hinweis: Stromsensor prüfen oder kalibrieren.", drawn=drawn,
                percent=deviation, counter=counter), deviation))
    return found


def _aircraft_findings(flights, settings, params):
    """All findings for the flights of one aircraft. params: its battery settings, None if not chosen yet."""
    found = []
    on = settings.is_enabled
    threshold = settings.threshold
    if on("short_flight"):
        found += _short_flights(flights, threshold("short_flight"))
    if on("ri_high"):
        found += _internal_resistance_high(flights, threshold("ri_high"))
    if on("rx_current_high"):
        found += _receiver_current_high(flights, threshold("rx_current_high"))
    if on("rssi_low"):
        found += _rssi_low(flights, threshold("rssi_low"))
    if on("rx_voltage_dip"):
        found += _receiver_voltage_dips(flights, threshold("rx_voltage_dip"))
    if params is not None:
        found += [finding for finding in _cell_voltage_limits(flights, params) if on(finding.rule)]
    return found


def find_anomalies(rows, settings, battery_for):
    """All automatic anomalies of the stored flights.

    rows: ``db.annotations.rule_input_rows``; settings: RuleSettings; battery_for(aircraft name): config.Params
    with the battery settings of that aircraft, or None if they have not been chosen yet (then the limits of the
    cell chemistry are not applied).
    """
    flights = rule_input(rows)
    found = []
    for aircraft, aircraft_flights in flights.groupby("aircraft", sort=True):
        found += _aircraft_findings(aircraft_flights, settings, battery_for(aircraft))
        minimum = settings.rx_min_voltage.get(aircraft, 0.0)
        if settings.is_enabled("rx_voltage_limit") and minimum > 0:
            found += _receiver_voltage_limit(aircraft_flights, minimum)
    if settings.is_enabled("rx_spikes_no_cause"):
        found += _spikes_without_cause(flights, settings.threshold("rx_spikes_no_cause"))
    if settings.is_enabled("current_sensor_deviation"):
        found += _current_sensor_deviation(flights, settings.threshold("current_sensor_deviation"))
    return found
