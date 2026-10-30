# -*- coding: utf-8 -*-
"""The period the flight recorder plays (TW-057, TW-058): the same as the single-flight charts show.

Time 0, start and end of the recorder equal those of the charts and of the logbook; a log that starts without
telemetry (the log of 07.03.2025) shows data from its first row; a log that runs on after the landing is cut there.
"""

import numpy as np
import pytest

from helpers import ROOT, analyse_log, ela, read_log, tmpdir, write_ethos_csv
from ethosloganalyser.analysis.flight import flight_window_times
from ethosloganalyser.config import STEP
from ethosloganalyser.db import FlightDatabase, import_paths
from ethosloganalyser.gui.database_flights import complete_flight
from ethosloganalyser.recorder.flight_track import load_track

LOG_2025 = ROOT / "examples" / "-Viper-Jet-2025-03-07-18-45-50.csv"
LOGS_2026 = ROOT / "examples" / "logs_2026"
NAN = float("nan")


def _current_profile(time_s, motor_periods, seed=1):
    """Motor current [A] that is on in the given periods (start, end) and about 0.2 A elsewhere."""
    rng = np.random.default_rng(seed)
    current = np.full(len(time_s), 0.2)
    for start, end in motor_periods:
        running = (time_s >= start) & (time_s < end)
        current[running] = np.clip(35 + 25 * np.sin(np.arange(running.sum()) / 7.0) + rng.normal(0, 4, running.sum()), 3, None)
    return current


def _synthetic_log(folder, name, length_s, motor_periods, telemetry_ends_s=None, telemetry_starts_s=0.0):
    """A log of length_s seconds with the motor running in motor_periods. The aircraft telemetry (voltage, current,
    altitude) exists from telemetry_starts_s to telemetry_ends_s; the sticks are logged until the end of the log."""
    time_s = np.arange(0, length_s, 0.25)
    current = _current_profile(time_s, motor_periods)
    voltage = 48.0 - 0.05 * current
    altitude = np.where((time_s > motor_periods[-1][0]) & (time_s < motor_periods[-1][1]), 80.0, 0.0)
    has_telemetry = (time_s >= telemetry_starts_s) & (time_s < (telemetry_ends_s if telemetry_ends_s else length_s + 1))
    stick = np.round(300 * np.sin(time_s / 5.0))
    extra = {"Altitude(m)": np.where(has_telemetry, altitude, NAN), "QR": stick, "HR": -stick, "SR": 0 * stick}
    return write_ethos_csv(folder, name, time_s, np.where(has_telemetry, voltage, NAN),
                           np.where(has_telemetry, current, NAN), extra)


def _recorder_and_charts(tmp_path, path):
    """(track, logbook duration, length of the time axis of the charts) of a log imported into a database."""
    database = FlightDatabase(str(tmp_path / "span.db"))
    try:
        import_paths(database, [str(path)], ela.Params())
        log_id, duration = database.connection.execute("SELECT log_id, duration_s FROM flight").fetchone()
        track = load_track(database.connection, log_id)
        chart_time = complete_flight(database.connection, log_id)[1]["t"]
    finally:
        database.close()
    return track, duration, float(chart_time[-1] - chart_time[0])


def _assert_same_period(track, logbook_duration, chart_length):
    assert track.start_time == 0.0 and track.time[0] == 0.0
    assert track.end_time == pytest.approx(logbook_duration, abs=0.06)       # the logbook rounds to 0.1 s
    assert 0 <= track.end_time - chart_length < STEP + 1e-6                  # the charts end on a point of their grid


# ---------------- the window of the analysis ----------------
def test_the_window_is_the_period_the_analysis_works_on():
    """A motor test before take-off is not part of the flight: its window starts with the real flight."""
    time_s = np.arange(0, 300, 0.25)
    current = _current_profile(time_s, [(0, 10), (70, 270)])
    path = write_ethos_csv(tmpdir(), "Synth-2026-05-01-12-00-00.csv", time_s, 48.0 - 0.05 * current, current)
    start, end = flight_window_times(read_log(path), ela.Params())
    assert 70 <= start < 71 and 269 <= end < 270
    row, _reason = analyse_log(path, ela.Params())
    assert end - start == pytest.approx(row["dauer_s"], abs=0.06)           # dauer_s is rounded to 0.1 s


def test_there_is_no_window_without_motor_or_when_too_short_or_without_battery_data():
    time_s = np.arange(0, 300, 0.25)
    folder = tmpdir()
    ground = write_ethos_csv(folder, "Ground-2026-05-01-12-00-00.csv", time_s, np.zeros(len(time_s)), np.zeros(len(time_s)))
    assert flight_window_times(read_log(ground), ela.Params()) is None
    short_time = np.arange(0, 60, 0.25)
    current = _current_profile(short_time, [(0, 60)])
    short = write_ethos_csv(folder, "Short-2026-05-01-12-00-00.csv", short_time, 48.0 - 0.05 * current, current)
    assert flight_window_times(read_log(short), ela.Params()) is None
    glider = write_ethos_csv(folder, "Glider-2026-05-01-12-00-00.csv", time_s, np.full(len(time_s), NAN),
                             np.full(len(time_s), NAN), {"Altitude(m)": np.linspace(0, 100, len(time_s))})
    assert flight_window_times(read_log(glider), ela.Params()) is None


# ---------------- recorder, logbook and charts ----------------
def test_a_log_that_runs_on_after_the_landing_ends_with_the_flight(tmp_path):
    """Motor from 70 s to 270 s, no telemetry after 290 s, the sticks are logged until the log ends at 600 s."""
    path = _synthetic_log(tmpdir(), "Synth-2026-05-01-12-00-00.csv", 600, [(70, 270)], telemetry_ends_s=290)
    track, logbook_duration, chart_length = _recorder_and_charts(tmp_path, path)
    _assert_same_period(track, logbook_duration, chart_length)
    assert 199 < track.end_time < 201 and 69 < track.origin < 71
    assert track.row_at(10_000) == track.end_row                              # nothing is played after the landing


def test_a_log_with_a_long_lead_in_starts_with_the_flight(tmp_path):
    """Telemetry from the start of the log, the motor starts after 150 s: time 0 is the motor start, as in the
    charts ("Zeit seit Motorstart"), and the recorder shows data there."""
    path = _synthetic_log(tmpdir(), "Synth-2026-05-01-12-00-00.csv", 500, [(150, 350)])
    track, logbook_duration, chart_length = _recorder_and_charts(tmp_path, path)
    _assert_same_period(track, logbook_duration, chart_length)
    assert 149 < track.origin < 151
    assert all(track.value(role, 0) is not None and not track.is_stale(role, 0) for role in track.series)


def test_a_log_that_starts_without_telemetry_shows_data_at_the_start_of_the_flight(tmp_path):
    path = _synthetic_log(tmpdir(), "Synth-2026-05-01-12-00-00.csv", 500, [(100, 300)], telemetry_starts_s=40)
    track, logbook_duration, chart_length = _recorder_and_charts(tmp_path, path)
    _assert_same_period(track, logbook_duration, chart_length)
    assert all(track.value(role, 0) is not None and not track.is_stale(role, 0) for role in track.series)


# ---------------- real logs ----------------
def test_the_log_of_march_2025_shows_data_from_its_first_row(tmp_path):
    """TW-057: the log has no telemetry in its first 14 s (all instruments were empty there, the horizon said "keine
    Lagedaten"). The flight starts 45 s into the log, with data on every instrument."""
    track, logbook_duration, chart_length = _recorder_and_charts(tmp_path, LOG_2025)
    _assert_same_period(track, logbook_duration, chart_length)
    assert track.origin == pytest.approx(45.1, abs=0.1) and track.end_time == pytest.approx(582.0, abs=0.06)
    assert len(track.series) == 11                                           # every sensor the log has
    assert all(track.value(role, 0) is not None and not track.is_stale(role, 0) for role in track.series)
    bank, pitch, stale = track.attitude(0)
    assert not stale and -180 <= bank <= 180 and -90 <= pitch <= 90


@pytest.fixture(scope="module")
def example_flights(tmp_path_factory):
    """Every flight of the example logs, imported once: [(name, track, logbook duration, chart axis length)]."""
    database = FlightDatabase(str(tmp_path_factory.mktemp("span") / "examples.db"))
    try:
        import_paths(database, [str(LOGS_2026), str(LOG_2025)], ela.Params())
        found = []
        for log_id, name, duration in database.connection.execute(
                "SELECT flight.log_id, log_file.original_name, flight.duration_s FROM flight JOIN log_file ON "
                "log_file.id = flight.log_id WHERE flight.is_flight = 1 AND flight.metrics IS NOT NULL "
                "ORDER BY log_file.original_name").fetchall():
            chart_time = complete_flight(database.connection, log_id)[1]["t"]
            found.append((name, load_track(database.connection, log_id), duration, float(chart_time[-1] - chart_time[0])))
    finally:
        database.close()
    return found


def test_every_example_flight_has_the_same_period_in_recorder_logbook_and_charts(example_flights):
    assert len(example_flights) >= 33
    for name, track, logbook_duration, chart_length in example_flights:
        try:
            _assert_same_period(track, logbook_duration, chart_length)
        except AssertionError as problem:
            raise AssertionError(f"{name}: {problem}") from problem


def test_the_recorder_is_nowhere_empty_where_the_log_has_data(example_flights):
    """At the first row every instrument of every example flight shows a fresh value (no "—", no grey horizon)."""
    for name, track, _duration, _chart_length in example_flights:
        assert track.series, name
        for role in track.series:
            assert track.value(role, 0) is not None and not track.is_stale(role, 0), (name, role)
