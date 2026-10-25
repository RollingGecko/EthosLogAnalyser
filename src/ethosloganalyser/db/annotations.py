# -*- coding: utf-8 -*-
"""Notes and anomalies of flights in the database: reading and writing them.

Tables (schema version 2, see schema.py and docs/database.md):

* ``flight_note`` - one free-text note per log.
* ``anomaly`` - anomalies of a flight. Origin ``auto``: found by a rule of analysis/anomalies.py; all of them are
  replaced on every recalculation. Origin ``manual``: entered by the user with their own text and severity; a
  recalculation never touches them.
* ``anomaly_acknowledgement`` - which automatic anomaly (flight + rule) the user has acknowledged, with the
  value at that time. Kept apart from ``anomaly`` so an acknowledgement survives every recalculation and switching
  a rule off and on again. If the value of the rule changes clearly afterwards (REOPEN_CHANGE), the anomaly is
  open again: the acknowledgement was given for a different situation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd

from .flight_store import START_TIME_FORMAT
from .log_analysis import message_from_json, message_to_json
from . import sensor_roles
from .series_codec import decode_series
from .signal_metrics import signal_metrics, signal_metrics_to_json

AUTO = "auto"
MANUAL = "manual"
MANUAL_RULE = "manual"

INFO, WARNING, CRITICAL = "info", "warning", "critical"
SEVERITIES = (INFO, WARNING, CRITICAL)
SEVERITY_RANK = {INFO: 1, WARNING: 2, CRITICAL: 3}       # 0 = no open anomaly

# relative change of the judged value after which an acknowledged anomaly is open again
REOPEN_CHANGE = 0.2


def _now_text():
    return datetime.now().strftime(START_TIME_FORMAT)


@dataclass
class Anomaly:
    """One anomaly of a flight as stored."""
    anomaly_id: int
    log_id: int
    rule: str
    origin: str                 # AUTO or MANUAL
    severity: str               # INFO, WARNING or CRITICAL
    message: object             # AUTO: i18n.Msg (translated when shown); MANUAL: the user's text
    value: Optional[float]
    acknowledged: bool

    @property
    def text(self):
        """The text in the current language."""
        return str(self.message)


# ---------------- notes ----------------
def note_of(connection, log_id):
    """The note of a log ("" if there is none)."""
    row = connection.execute("SELECT text FROM flight_note WHERE log_id = ?", (log_id,)).fetchone()
    return row[0] if row else ""


def set_note(connection, log_id, text):
    """Stores the note of a log; an empty text (or only blanks) removes it."""
    text = (text or "").strip()
    with connection:
        if text:
            connection.execute("INSERT INTO flight_note (log_id, text, updated_at) VALUES (?, ?, ?) "
                               "ON CONFLICT (log_id) DO UPDATE SET text = excluded.text, "
                               "updated_at = excluded.updated_at", (log_id, text, _now_text()))
        else:
            connection.execute("DELETE FROM flight_note WHERE log_id = ?", (log_id,))


# ---------------- anomalies of one flight ----------------
def _anomaly_from_row(row):
    anomaly_id, log_id, rule, origin, severity, message, value, acknowledged = row
    text = message_from_json(message) if origin == AUTO else message
    return Anomaly(anomaly_id=anomaly_id, log_id=log_id, rule=rule, origin=origin, severity=severity,
                   message=text, value=value, acknowledged=bool(acknowledged))


def anomalies_of(connection, log_id):
    """All anomalies of a log, most severe first (automatic before manual ones of the same severity)."""
    rows = connection.execute(
        "SELECT id, log_id, rule, origin, severity, message, value, acknowledged FROM anomaly WHERE log_id = ? "
        "ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END, origin, id",
        (log_id,)).fetchall()
    return [_anomaly_from_row(row) for row in rows]


def add_manual_anomaly(connection, log_id, text, severity):
    """Adds an anomaly entered by the user. Returns its id."""
    if severity not in SEVERITIES:
        raise ValueError(f"unknown severity {severity!r}")
    with connection:
        return connection.execute(
            "INSERT INTO anomaly (log_id, rule, origin, severity, message, value, acknowledged, created_at) "
            "VALUES (?, ?, ?, ?, ?, NULL, 0, ?)",
            (log_id, MANUAL_RULE, MANUAL, severity, text.strip(), _now_text())).lastrowid


def delete_manual_anomaly(connection, anomaly_id):
    """Deletes an anomaly entered by the user (automatic ones cannot be deleted, only acknowledged)."""
    with connection:
        connection.execute("DELETE FROM anomaly WHERE id = ? AND origin = ?", (anomaly_id, MANUAL))


def set_acknowledged(connection, anomaly_id, acknowledged):
    """Acknowledges an anomaly or opens it again. For an automatic one the acknowledgement is also kept by flight
    and rule, so it survives recalculations."""
    with connection:
        row = connection.execute("SELECT log_id, rule, origin, value FROM anomaly WHERE id = ?",
                                 (anomaly_id,)).fetchone()
        if row is None:
            return
        log_id, rule, origin, value = row
        connection.execute("UPDATE anomaly SET acknowledged = ? WHERE id = ?", (int(acknowledged), anomaly_id))
        if origin != AUTO:
            return
        if acknowledged:
            connection.execute("INSERT INTO anomaly_acknowledgement (log_id, rule, value, acknowledged_at) "
                               "VALUES (?, ?, ?, ?) ON CONFLICT (log_id, rule) DO UPDATE SET "
                               "value = excluded.value, acknowledged_at = excluded.acknowledged_at",
                               (log_id, rule, value, _now_text()))
        else:
            connection.execute("DELETE FROM anomaly_acknowledgement WHERE log_id = ? AND rule = ?", (log_id, rule))


# ---------------- summary for the logbook ----------------
def annotation_summary(connection):
    """Per log with a note or an open anomaly: has_note (bool) and open_rank (highest SEVERITY_RANK of the
    anomalies not acknowledged, 0 if none). Logs with neither are not listed."""
    rows = connection.execute(
        "SELECT log_id, max(has_note), max(open_rank) FROM ("
        "  SELECT log_id, 1 AS has_note, 0 AS open_rank FROM flight_note"
        "  UNION ALL"
        "  SELECT log_id, 0, CASE severity WHEN 'critical' THEN 3 WHEN 'warning' THEN 2 ELSE 1 END"
        "  FROM anomaly WHERE acknowledged = 0"
        ") GROUP BY log_id").fetchall()
    return pd.DataFrame(rows, columns=["log_id", "has_note", "open_rank"]).astype(
        {"log_id": int, "has_note": bool, "open_rank": int})


# ---------------- recalculation ----------------
def clearly_changed(old_value, new_value):
    """True if the judged value changed by more than REOPEN_CHANGE (relative) since the acknowledgement."""
    if old_value is None or new_value is None:
        return old_value is not new_value
    reference = max(abs(old_value), 1e-9)
    return abs(new_value - old_value) / reference > REOPEN_CHANGE


def replace_automatic_anomalies(connection, findings):
    """Replaces all automatic anomalies by findings (list of analysis.anomalies.Finding) in one transaction.

    An acknowledgement (flight + rule) carries over unless the value changed clearly; then it is dropped and the
    anomaly is open again. Acknowledgements of findings that are gone are kept: if the rule finds the same thing
    again later (e.g. a rule switched off and on), it is still acknowledged. Manual anomalies are not touched.
    """
    with connection:
        acknowledged = {(log_id, rule): value for log_id, rule, value in connection.execute(
            "SELECT log_id, rule, value FROM anomaly_acknowledgement")}
        connection.execute("DELETE FROM anomaly WHERE origin = ?", (AUTO,))
        now = _now_text()
        rows, reopened = [], []
        for finding in findings:
            key = (finding.log_id, finding.rule)
            is_acknowledged = key in acknowledged and not clearly_changed(acknowledged[key], finding.value)
            if key in acknowledged and not is_acknowledged:
                reopened.append(key)
            rows.append((finding.log_id, finding.rule, AUTO, finding.severity, message_to_json(finding.message),
                         finding.value, int(is_acknowledged), now))
        connection.executemany(
            "INSERT INTO anomaly (log_id, rule, origin, severity, message, value, acknowledged, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
        connection.executemany("DELETE FROM anomaly_acknowledgement WHERE log_id = ? AND rule = ?", reopened)


def rule_input_rows(connection):
    """What the rules need of every stored log, without time series: log id, aircraft, effective flight decision,
    duration, metrics (JSON text) and signal metrics (JSON text)."""
    return pd.read_sql_query(
        "SELECT flight.log_id, aircraft.name AS aircraft, flight.start_time, "
        "coalesce(flight.is_flight_manual, flight.is_flight) AS is_flight, "
        "coalesce(flight.duration_s, flight.log_duration_s) AS duration_s, flight.metrics, flight.signal_metrics "
        "FROM flight JOIN aircraft ON aircraft.id = flight.aircraft_id ORDER BY flight.start_time", connection)


def logs_without_signal_metrics(connection):
    """Log ids whose signal metrics have not been worked out yet (databases from schema version 1)."""
    return [row[0] for row in connection.execute(
        "SELECT log_id FROM flight WHERE signal_metrics IS NULL ORDER BY start_time")]


def fill_signal_metrics(connection, log_ids, should_cancel=None):
    """Works out the signal metrics of these logs from their stored time series (not the raw logs). Returns the
    number of logs done; should_cancel() is checked before every log."""
    done = 0
    for log_id in log_ids:
        if should_cancel is not None and should_cancel():
            break
        rows = connection.execute(
            "SELECT sensor.column_name, sensor.role, series.data FROM sensor "
            "JOIN series ON series.sensor_id = sensor.id WHERE sensor.log_id = ?", (log_id,)).fetchall()
        roles = {name: role for name, role, _data in rows}
        needed = {name: decode_series(data) for name, role, data in rows
                  if role in (sensor_roles.TIME, sensor_roles.RX_VOLTAGE)}
        time_s = next((needed[name] for name, role, _data in rows if role == sensor_roles.TIME), None)
        values = signal_metrics(time_s, pd.DataFrame(needed), roles) if time_s is not None else {}
        with connection:
            connection.execute("UPDATE flight SET signal_metrics = ? WHERE log_id = ?",
                               (signal_metrics_to_json(values), log_id))
        done += 1
    return done


def recalculate_anomalies(connection, settings, battery_for, progress=None, should_cancel=None):
    """Judges all flights again and stores the automatic anomalies. Returns the number of findings, or None if
    cancelled.

    First the signal metrics missing from older databases are worked out from the stored time series (once);
    then the rules use only stored values. settings, battery_for: see analysis.anomalies.find_anomalies.
    progress(done, total) is called while signal metrics are worked out.
    """
    from ..analysis.anomalies import find_anomalies

    missing = logs_without_signal_metrics(connection)
    for done in range(0, len(missing), 20):
        if should_cancel is not None and should_cancel():
            return None
        fill_signal_metrics(connection, missing[done:done + 20])
        if progress is not None:
            progress(min(done + 20, len(missing)), len(missing))
    findings = find_anomalies(rule_input_rows(connection), settings, battery_for)
    replace_automatic_anomalies(connection, findings)
    return len(findings)
