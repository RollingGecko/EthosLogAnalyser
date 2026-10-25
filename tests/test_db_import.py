# -*- coding: utf-8 -*-
"""Flight database: import of files and folders, duplicates, flight detection, emptying, recalculation."""

import json
import shutil

import numpy as np
import pandas as pd
import pytest

from helpers import EXAMPLE_FILES, ROOT, ela, write_ethos_csv
from ethosloganalyser.db import FlightDatabase, flight_store, import_paths, importer
from ethosloganalyser.db import flight_detection, log_analysis, reanalysis, sensor_roles
from ethosloganalyser.analysis.flight import analyse_frame
from ethosloganalyser.db.log_analysis import metrics_from_json
from ethosloganalyser.io.ethos_log import read_log

LOGS_2026 = ROOT / "examples" / "logs_2026"


def _motor_flight(folder, name, seconds=300.0):
    """Synthetic electric flight: motor on from 10 s to seconds - 20 s. The log starts at the time in its name,
    so logs with different names have different content."""
    t = np.arange(0, seconds, 0.25)
    current = np.where((t > 10) & (t < seconds - 20), 20 + 10 * np.sin(t / 7), 0.0)
    voltage = 50 - 0.05 * current - 0.002 * t
    stamp = name[-23:-4]                                    # YYYY-MM-DD-hh-mm-ss
    start = f"{stamp[:10]} {stamp[11:].replace('-', ':')}"
    return write_ethos_csv(folder, name, t, voltage, current, start=start)


def _glider_log(folder, name, airborne_s, start="2026-06-01 14:00:00"):
    """Log without current sensor: altitude, vario and receiver signal only (e.g. a glider)."""
    t = np.arange(0, airborne_s + 120, 0.5)
    altitude = np.where((t > 60) & (t < 60 + airborne_s), 120.0, 0.0) + 0.3 * np.sin(t)
    times = pd.Timestamp(start) + pd.to_timedelta(t, unit="s")
    frame = pd.DataFrame({"Date": times.strftime("%Y-%m-%d"), "Time": times.strftime("%H:%M:%S.%f").str[:-3],
                          "Altitude(m)": np.round(altitude, 2), "VSpeed(m/s)": np.round(np.gradient(altitude), 2),
                          "RSSI 2.4G(dB)": 90, "RxBatt(V)": 5.1})
    path = folder / name
    frame.to_csv(path, index=False)
    return path


@pytest.fixture
def database(tmp_path):
    db = FlightDatabase(str(tmp_path / "flights.db"))
    yield db
    db.close()


def test_import_of_a_folder_with_subfolders(database, tmp_path):
    logs = tmp_path / "logs"
    (logs / "2026" / "may").mkdir(parents=True)
    _motor_flight(logs, "Synth-2026-05-01-12-00-00.csv")
    _motor_flight(logs / "2026" / "may", "Synth-2026-05-02-12-00-00.csv")
    _motor_flight(logs / "2026", "Other-Plane-2026-05-03-12-00-00.csv")
    report = import_paths(database, [str(logs)], ela.Params())
    assert report.count(importer.NEW) == 3 and report.flight_count == 3
    stats = database.stats()
    assert (stats.log_count, stats.flight_count, stats.aircraft_count) == (3, 3, 2)
    names = {row[0] for row in database.connection.execute("SELECT name FROM aircraft")}
    assert names == {"Synth", "Other-Plane"}


def test_import_keeps_the_files_unchanged(database, tmp_path):
    path = _motor_flight(tmp_path, "Synth-2026-05-01-12-00-00.csv")
    before = path.read_bytes()
    import_paths(database, [str(path)], ela.Params())
    assert path.read_bytes() == before
    log_id = database.connection.execute("SELECT id FROM log_file").fetchone()[0]
    assert flight_store.raw_content(database.connection, log_id) == before


def test_same_content_under_another_name_is_a_duplicate(database, tmp_path):
    original = _motor_flight(tmp_path, "Synth-2026-05-01-12-00-00.csv")
    (tmp_path / "copy").mkdir()
    renamed = tmp_path / "copy" / "Renamed-2026-07-07-07-07-07.csv"
    shutil.copy(original, renamed)
    first = import_paths(database, [str(original)], ela.Params())
    second = import_paths(database, [str(renamed), str(original)], ela.Params())
    assert first.count(importer.NEW) == 1
    assert second.count(importer.DUPLICATE) == 2
    assert {entry.other_file for entry in second.entries} == {original.name}
    assert database.stats().log_count == 1


def test_same_model_and_start_time_with_other_content_is_a_possible_duplicate(database, tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = _motor_flight(tmp_path / "a", "Synth-2026-05-01-12-00-00.csv", seconds=300)
    second = _motor_flight(tmp_path / "b", "Synth-2026-05-01-12-00-00.csv", seconds=320)
    import_paths(database, [str(first)], ela.Params())
    report = import_paths(database, [str(second)], ela.Params())
    assert report.count(importer.SUSPICIOUS) == 1
    assert report.entries[0].other_file == first.name
    flags = [row[0] for row in database.connection.execute("SELECT possible_duplicate FROM flight ORDER BY id")]
    assert flags == [0, 1]


def test_unreadable_files_are_reported_and_not_imported(database, tmp_path):
    (tmp_path / "broken-2026-01-01-10-00-00.csv").write_bytes(b"\x00\x01\x02 no csv \xff")
    (tmp_path / "notime-2026-01-01-10-00-00.csv").write_text("A;B\n1;2\n3;4\n", encoding="utf-8")
    report = import_paths(database, [str(tmp_path)], ela.Params())
    assert report.count(importer.UNREADABLE) == 2
    assert all(str(entry.reason) for entry in report.entries)
    assert database.stats().log_count == 0


def test_too_short_log_is_imported_as_non_flight(database, tmp_path):
    path = _motor_flight(tmp_path, "Synth-2026-05-01-12-00-00.csv", seconds=60)
    report = import_paths(database, [str(path)], ela.Params())
    assert report.count(importer.NEW) == 1 and report.flight_count == 0
    is_flight, method, reason = database.connection.execute(
        "SELECT is_flight, detection_method, skip_reason FROM flight").fetchone()
    assert (is_flight, method) == (0, flight_detection.MOTOR)
    assert json.loads(reason)["msgid"].startswith("zu kurz")


def test_flight_detection_without_motor_sensor_uses_altitude(database, tmp_path):
    flown = _glider_log(tmp_path, "Glider-2026-06-01-14-00-00.csv", airborne_s=600)
    ground = _glider_log(tmp_path, "Glider-2026-06-01-15-00-00.csv", airborne_s=0, start="2026-06-01 15:00:00")
    report = import_paths(database, [str(flown), str(ground)], ela.Params())
    assert report.count(importer.NEW) == 2 and report.flight_count == 1
    rows = database.connection.execute(
        "SELECT log_file.original_name, is_flight, detection_method, duration_s, metrics FROM flight "
        "JOIN log_file ON log_file.id = flight.log_id ORDER BY start_time").fetchall()
    assert [(name, flag, method) for name, flag, method, _, _ in rows] == [
        (flown.name, 1, flight_detection.ALTITUDE), (ground.name, 0, flight_detection.ALTITUDE)]
    assert rows[0][3] == pytest.approx(600, abs=2)
    assert rows[0][4] is None                       # no battery or motor metrics without those sensors


def test_flight_detection_falls_back_to_vario_and_radio_link(tmp_path):
    params = ela.Params()
    t = np.arange(0, 400, 0.5)
    climbing = pd.DataFrame({"VSpeed(m/s)": np.where((t > 50) & (t < 350), 3.0 * np.sign(np.sin(t / 20)), 0.0)})
    roles = sensor_roles.assign_roles(climbing, params)
    found = flight_detection.detect_flight(climbing, t, roles, None, params)
    assert (found.is_flight, found.method) == (True, flight_detection.VERTICAL_SPEED)

    link_only = pd.DataFrame({"RSSI 2.4G(dB)": np.where(t < 100, 90, np.nan)})
    found = flight_detection.detect_flight(link_only, t, sensor_roles.assign_roles(link_only, params), None,
                                           params)
    assert (found.is_flight, found.method) == (False, flight_detection.RADIO_LINK)

    nothing = pd.DataFrame({"TxBat(V)": np.full(len(t), 7.8)})
    found = flight_detection.detect_flight(nothing, t, sensor_roles.assign_roles(nothing, params), None, params)
    assert (found.is_flight, found.method) == (False, flight_detection.NO_SENSOR)


def test_sensor_roles_of_an_ethos_log():
    frame = read_log(str(EXAMPLE_FILES[0]))
    roles = sensor_roles.assign_roles(frame, ela.Params())
    assert roles["VFAS(V)"] == sensor_roles.BATTERY_VOLTAGE
    assert roles["Current(A)"] == sensor_roles.MOTOR_CURRENT
    assert roles["Altitude(m)"] == sensor_roles.ALTITUDE
    assert roles["RxBatt1(V)"] == sensor_roles.RX_VOLTAGE
    assert roles["ESC consumption(mAh)"] == sensor_roles.ESC_CONSUMPTION
    assert roles["QR"] == sensor_roles.STICK_AILERON
    assert roles["Gas"] == sensor_roles.THROTTLE


def test_stored_time_series_give_the_same_metrics(database):
    """The time series in the database are complete: analysing them again gives the stored metrics."""
    import_paths(database, [str(path) for path in EXAMPLE_FILES], ela.Params())
    connection = database.connection
    for log_id, metrics, start, name in connection.execute(
            "SELECT log_id, metrics, start_time, original_name FROM flight JOIN log_file ON log_file.id = log_id"):
        frame = flight_store.load_log_frame(connection, log_id)
        again, _ = analyse_frame(frame, name, ela.Params(), start_time=flight_store.parse_start_time(start))
        for key, value in metrics_from_json(metrics).items():
            if isinstance(value, float) and np.isnan(value):
                assert again[key] is None or np.isnan(again[key]), key
            else:
                assert again[key] == pytest.approx(value), key


def test_example_logs_match_the_folder_analysis(database):
    report = import_paths(database, [str(path) for path in EXAMPLE_FILES], ela.Params())
    assert report.flight_count == 3
    folder = ela.analyse_folder(str(EXAMPLE_FILES[0].parent), ela.Params())
    stored = flight_store.flight_rows(database.connection)
    assert sorted(stored["original_name"]) == sorted(folder.df["datei"])
    durations = dict(zip(stored["original_name"], stored["duration_s"]))
    for name, duration in zip(folder.df["datei"], folder.df["dauer_s"]):
        assert durations[name] == pytest.approx(duration)


@pytest.mark.skipif(not LOGS_2026.is_dir(), reason="examples/logs_2026 not available")
def test_logs_2026_give_the_33_flights_of_the_folder_analysis(database):
    report = import_paths(database, [str(LOGS_2026)], ela.Params())
    assert report.count(importer.NEW) == 71 and report.flight_count == 33
    folder = ela.analyse_folder(str(LOGS_2026), ela.Params())
    flights = set(flight_store.flight_rows(database.connection).query("is_flight == 1")["original_name"])
    assert flights == set(folder.df["datei"])


def test_clear_empties_the_database(database, tmp_path):
    import_paths(database, [str(_motor_flight(tmp_path, "Synth-2026-05-01-12-00-00.csv"))], ela.Params())
    size_before = database.stats().size_bytes
    database.clear()
    stats = database.stats()
    assert (stats.log_count, stats.flight_count, stats.aircraft_count) == (0, 0, 0)
    assert stats.size_bytes < size_before
    assert database.connection.execute("SELECT count(*) FROM series").fetchone()[0] == 0


def test_outdated_flights_are_calculated_again_from_the_raw_log(database, tmp_path):
    import_paths(database, [str(_motor_flight(tmp_path, "Synth-2026-05-01-12-00-00.csv"))], ela.Params())
    connection = database.connection
    expected = connection.execute("SELECT metrics, duration_s FROM flight").fetchone()
    with connection:
        connection.execute("UPDATE flight SET analysis_version = 0, metrics = NULL, duration_s = NULL")
    (tmp_path / "Synth-2026-05-01-12-00-00.csv").unlink()        # the original file is not needed
    assert reanalysis.outdated_log_ids(connection) == [1]
    assert reanalysis.reanalyse_outdated(database, ela.Params()) == 1
    assert connection.execute("SELECT metrics, duration_s FROM flight").fetchone() == expected
    assert connection.execute("SELECT analysis_version FROM flight").fetchone()[0] == log_analysis.ANALYSIS_VERSION
    assert reanalysis.outdated_log_ids(connection) == []


def test_import_can_be_cancelled(database, tmp_path):
    for minute in range(3):
        _motor_flight(tmp_path, f"Synth-2026-05-01-12-0{minute}-00.csv")
    calls = []
    report = import_paths(database, [str(tmp_path)], ela.Params(), progress=lambda *state: calls.append(state),
                          should_cancel=lambda: len(calls) >= 1)
    assert report.cancelled and len(report.entries) == 1
    assert database.stats().log_count == 1
