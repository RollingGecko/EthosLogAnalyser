# -*- coding: utf-8 -*-
"""Notes and anomalies in the flight database: schema migration, acknowledging, own entries, recalculation."""

import json
import sqlite3

import pytest

from helpers import EXAMPLE_FILES, ela
from ethosloganalyser.analysis.anomalies import Finding, RuleSettings
from ethosloganalyser.db import FlightDatabase, annotations, import_paths, schema
from ethosloganalyser.i18n import Msg

LI_ION_13S = ela.Params(chem="Li-Ion", cells=13, nominal_mah=9000)


def _write_version_1_database(path, flights=3):
    """A database as the app wrote it before notes and anomalies (schema version 1), with a few flights."""
    connection = sqlite3.connect(str(path))
    for statement in schema.CREATE_STATEMENTS:
        connection.execute(statement)
    connection.execute(f"PRAGMA application_id = {schema.APPLICATION_ID}")
    connection.execute("PRAGMA user_version = 1")
    connection.execute("INSERT INTO aircraft (id, name) VALUES (1, 'Jet')")
    for log_id in range(1, flights + 1):
        connection.execute("INSERT INTO log_file (id, sha256, original_name, source_path, size_bytes, imported_at) "
                           "VALUES (?, ?, ?, '', 10, '2026-10-01T10:00:00')", (log_id, f"hash{log_id}", f"{log_id}.csv"))
        connection.execute("INSERT INTO flight (log_id, aircraft_id, start_time, duration_s, log_duration_s, is_flight, "
                           "detection_method, analysis_version, analysis_params, metrics) "
                           "VALUES (?, 1, ?, 500, 510, 1, 'motor', 1, '{}', ?)",
                           (log_id, f"2026-05-{log_id:02d}T12:00:00", json.dumps({"entnommen_mAh": 5000})))
    connection.commit()
    connection.close()


@pytest.fixture
def database(tmp_path):
    db = FlightDatabase(str(tmp_path / "flights.db"))
    import_paths(db, [str(path) for path in EXAMPLE_FILES], LI_ION_13S)
    yield db
    db.close()


def _log_ids(database):
    return [row[0] for row in database.connection.execute("SELECT log_id FROM flight ORDER BY start_time")]


def _finding(log_id, rule="rx_voltage_dip", value=20.0, severity="warning"):
    return Finding(log_id=log_id, rule=rule, severity=severity, message=Msg("Flug {no}", no=log_id), value=value)


# ---------------- schema ----------------
def test_a_version_1_database_is_migrated_without_losing_flights(tmp_path):
    path = tmp_path / "flugbuch.db"
    _write_version_1_database(path)
    database = FlightDatabase(str(path))
    connection = database.connection
    assert connection.execute("PRAGMA user_version").fetchone()[0] == schema.SCHEMA_VERSION == 3
    assert database.stats().flight_count == 3
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"flight_note", "anomaly", "anomaly_acknowledgement"} <= tables
    assert annotations.logs_without_signal_metrics(connection) == [1, 2, 3]
    # the signal metrics are filled in once (these logs have no stored time series: nothing to find)
    assert annotations.recalculate_anomalies(connection, RuleSettings(), lambda aircraft: None) == 0
    assert annotations.logs_without_signal_metrics(connection) == []
    annotations.set_note(connection, 2, "after the migration")
    database.close()
    again = FlightDatabase(str(path))
    assert annotations.note_of(again.connection, 2) == "after the migration"
    again.close()


def test_a_failed_migration_leaves_the_old_version(tmp_path, monkeypatch):
    path = tmp_path / "flugbuch.db"
    _write_version_1_database(path)
    monkeypatch.setitem(schema.MIGRATIONS, 1, schema.VERSION_2_STATEMENTS + ("THIS IS NOT SQL",))
    with pytest.raises(Exception):
        FlightDatabase(str(path))
    connection = sqlite3.connect(str(path))
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
    columns = {row[1] for row in connection.execute("PRAGMA table_info(flight)")}
    assert "signal_metrics" not in columns
    connection.close()


def test_signal_metrics_from_the_stored_series_equal_those_of_the_import(database):
    connection = database.connection
    imported = dict(connection.execute("SELECT log_id, signal_metrics FROM flight").fetchall())
    assert all(json.loads(text).get("rx_voltage_median_V") for text in imported.values())
    connection.execute("UPDATE flight SET signal_metrics = NULL")
    connection.commit()
    annotations.fill_signal_metrics(connection, annotations.logs_without_signal_metrics(connection))
    assert dict(connection.execute("SELECT log_id, signal_metrics FROM flight").fetchall()) == imported


# ---------------- notes ----------------
def test_a_note_is_stored_changed_and_removed(database):
    log_id = _log_ids(database)[0]
    connection = database.connection
    assert annotations.note_of(connection, log_id) == ""
    annotations.set_note(connection, log_id, "  aileron servo felt stiff  ")
    assert annotations.note_of(connection, log_id) == "aileron servo felt stiff"
    annotations.set_note(connection, log_id, "servo replaced")
    assert annotations.note_of(connection, log_id) == "servo replaced"
    annotations.set_note(connection, log_id, "   ")
    assert annotations.note_of(connection, log_id) == ""
    assert connection.execute("SELECT count(*) FROM flight_note").fetchone()[0] == 0


# ---------------- anomalies ----------------
def test_acknowledgement_survives_a_recalculation(database):
    connection = database.connection
    first, second = _log_ids(database)[:2]
    annotations.replace_automatic_anomalies(connection, [_finding(first), _finding(second)])
    anomaly = annotations.anomalies_of(connection, first)[0]
    annotations.set_acknowledged(connection, anomaly.anomaly_id, True)
    annotations.replace_automatic_anomalies(connection, [_finding(first, value=21.0), _finding(second)])
    assert annotations.anomalies_of(connection, first)[0].acknowledged
    assert not annotations.anomalies_of(connection, second)[0].acknowledged


def test_a_clearly_changed_value_opens_the_anomaly_again(database):
    connection = database.connection
    log_id = _log_ids(database)[0]
    annotations.replace_automatic_anomalies(connection, [_finding(log_id, value=20.0)])
    annotations.set_acknowledged(connection, annotations.anomalies_of(connection, log_id)[0].anomaly_id, True)
    annotations.replace_automatic_anomalies(connection, [_finding(log_id, value=30.0)])      # +50 %
    assert not annotations.anomalies_of(connection, log_id)[0].acknowledged
    # and stays open: the old acknowledgement is gone
    annotations.replace_automatic_anomalies(connection, [_finding(log_id, value=20.0)])
    assert not annotations.anomalies_of(connection, log_id)[0].acknowledged


def test_acknowledgement_is_kept_while_a_rule_is_switched_off(database):
    connection = database.connection
    log_id = _log_ids(database)[0]
    annotations.replace_automatic_anomalies(connection, [_finding(log_id)])
    annotations.set_acknowledged(connection, annotations.anomalies_of(connection, log_id)[0].anomaly_id, True)
    annotations.replace_automatic_anomalies(connection, [])                                 # rule off
    assert annotations.anomalies_of(connection, log_id) == []
    annotations.replace_automatic_anomalies(connection, [_finding(log_id)])                 # rule on again
    assert annotations.anomalies_of(connection, log_id)[0].acknowledged


def test_opening_an_acknowledged_anomaly_again(database):
    connection = database.connection
    log_id = _log_ids(database)[0]
    annotations.replace_automatic_anomalies(connection, [_finding(log_id)])
    anomaly_id = annotations.anomalies_of(connection, log_id)[0].anomaly_id
    annotations.set_acknowledged(connection, anomaly_id, True)
    annotations.set_acknowledged(connection, anomaly_id, False)
    annotations.replace_automatic_anomalies(connection, [_finding(log_id)])
    assert not annotations.anomalies_of(connection, log_id)[0].acknowledged


def test_own_entries_are_never_touched_by_a_recalculation(database):
    connection = database.connection
    log_id = _log_ids(database)[0]
    own = annotations.add_manual_anomaly(connection, log_id, "landing gear door hangs", "critical")
    annotations.replace_automatic_anomalies(connection, [_finding(log_id)])
    annotations.replace_automatic_anomalies(connection, [])
    entries = annotations.anomalies_of(connection, log_id)
    assert [(entry.anomaly_id, entry.origin, entry.text, entry.severity) for entry in entries] == \
        [(own, annotations.MANUAL, "landing gear door hangs", "critical")]
    with pytest.raises(ValueError):
        annotations.add_manual_anomaly(connection, log_id, "x", "severe")


def test_only_own_entries_can_be_deleted(database):
    connection = database.connection
    log_id = _log_ids(database)[0]
    annotations.replace_automatic_anomalies(connection, [_finding(log_id)])
    automatic = annotations.anomalies_of(connection, log_id)[0]
    own = annotations.add_manual_anomaly(connection, log_id, "checked: all fine", "info")
    annotations.delete_manual_anomaly(connection, automatic.anomaly_id)
    annotations.delete_manual_anomaly(connection, own)
    assert [entry.anomaly_id for entry in annotations.anomalies_of(connection, log_id)] == [automatic.anomaly_id]


def test_summary_gives_note_and_highest_open_severity(database):
    connection = database.connection
    first, second, third = _log_ids(database)
    annotations.set_note(connection, first, "note")
    annotations.replace_automatic_anomalies(connection, [_finding(second, severity="info"),
                                                         _finding(second, rule="ri_high", severity="warning"),
                                                         _finding(third, severity="critical")])
    annotations.set_acknowledged(connection, annotations.anomalies_of(connection, third)[0].anomaly_id, True)
    summary = annotations.annotation_summary(connection).set_index("log_id")
    assert summary.loc[first].tolist() == [True, 0]
    assert summary.loc[second].tolist() == [False, 2]
    assert third not in summary.index                     # only an acknowledged anomaly: nothing to show


def test_emptying_the_database_removes_notes_and_anomalies(database):
    connection = database.connection
    log_id = _log_ids(database)[0]
    annotations.set_note(connection, log_id, "note")
    annotations.add_manual_anomaly(connection, log_id, "own", "info")
    database.clear()
    for table in ("flight_note", "anomaly", "anomaly_acknowledgement"):
        assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_recalculation_with_the_example_logs(database, tmp_path):
    connection = database.connection
    # three flights: too few for the median rules; nothing in these logs crosses a limit
    assert annotations.recalculate_anomalies(connection, RuleSettings(), lambda aircraft: LI_ION_13S) == 0
    strict = RuleSettings(thresholds={"rx_voltage_dip": 0.1})
    count = annotations.recalculate_anomalies(connection, strict, lambda aircraft: LI_ION_13S)
    assert count == 3 and len(annotations.annotation_summary(connection)) == 3
    copy = tmp_path / "copy.db"
    database.save_as(str(copy))                           # notes and anomalies are part of the file
    other = FlightDatabase(str(copy))
    assert len(annotations.annotation_summary(other.connection)) == 3
    other.close()
