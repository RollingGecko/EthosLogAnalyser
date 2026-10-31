# -*- coding: utf-8 -*-
"""Aircraft of the flight recorder (recorder/aircraft_shape.py): turning and projection at bank 0/90/180/−180 and
pitch ±90, drawing order, control surface angles, missing sticks, attitude and throttle, gaps, a real log row."""

import itertools

import numpy as np
import pytest

from helpers import ROOT
from ethosloganalyser.config import Params
from ethosloganalyser.db import FlightDatabase, import_paths
from ethosloganalyser.db import sensor_roles as roles
from ethosloganalyser.recorder import aircraft_shape
from ethosloganalyser.recorder.aircraft_shape import (AIRCRAFT, ELEVATOR, LEFT_AILERON, MAX_DEFLECTION_DEG,
                                                      RIGHT_AILERON, RUDDER, AircraftPose, aircraft_pose,
                                                      attitude_point, deflection, has_aircraft, project_aircraft,
                                                      rotate_about_axis, surface_deflections)
from ethosloganalyser.recorder.flight_track import build_track, load_track

LARGEST_FLIGHT_LOG = ROOT / "examples" / "logs_2026" / "-Viper-Jet-2026-07-20-14-46-48.csv"
BOX = (10, 20, 320, 200)
NEUTRAL = surface_deflections(None, None, None)


def _pose(bank=0.0, pitch=0.0, deflections=NEUTRAL, throttle=None, stale=False):
    return AircraftPose(bank=bank, pitch=pitch, stale=stale, deflections=deflections, throttle=throttle)


def _faces(pose):
    """name -> ProjectedFace, and the names of the shown faces in drawing order."""
    faces, _exhaust = project_aircraft(pose, BOX)
    return {face.name: face for face in faces}, [face.name for face in faces if face.visible]


def _centre(face):
    xs, ys = face.points[0::2], face.points[1::2]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _track(time_s, **columns):
    """Track from columns given as role = values (a column is named like its role)."""
    return build_track(time_s, [(role, role, values) for role, values in columns.items()])


# ---------------- turning ----------------
@pytest.mark.parametrize("bank, pitch, point, expected", [
    (0, 0, (1, 0, 0), (1, 0, 0)),
    (90, 0, (1, 0, 0), (0, 0, -1)),          # bank > 0: the right wing goes down
    (-90, 0, (1, 0, 0), (0, 0, 1)),
    (180, 0, (1, 0, 0), (-1, 0, 0)), (180, 0, (0, 0, 1), (0, 0, -1)),
    (-180, 0, (1, 0, 0), (-1, 0, 0)), (-180, 0, (0, 0, 1), (0, 0, -1)),
    (0, 90, (0, 1, 0), (0, 0, 1)),           # pitch > 0: the nose goes up
    (0, -90, (0, 1, 0), (0, 0, -1)),
    (0, 90, (0, 0, 1), (0, -1, 0)),          # nose up: the top of the aircraft faces backwards
    (90, 90, (1, 0, 0), (0, 1, 0)),          # roll first, then pitch
])
def test_turning_by_bank_and_pitch(bank, pitch, point, expected):
    assert attitude_point(point, bank, pitch) == pytest.approx(expected, abs=1e-9)


def test_rotation_about_a_hinge_keeps_the_hinge_and_the_distance():
    start, end, point = (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, -0.1, 0.0)
    turned = rotate_about_axis(point, start, end, 30)
    assert turned[0] == 0.5 and turned[1] ** 2 + turned[2] ** 2 == pytest.approx(0.01)
    assert rotate_about_axis(start, start, end, 30) == pytest.approx(start)


# ---------------- projection ----------------
def test_level_flight_is_symmetric_in_the_middle_of_the_box():
    faces, _order = _faces(_pose())
    (right_x, right_y), (left_x, left_y) = _centre(faces["wing_right"]), _centre(faces["wing_left"])
    middle = BOX[0] + BOX[2] / 2
    assert right_x > middle > left_x and right_x - middle == pytest.approx(middle - left_x)
    assert right_y == pytest.approx(left_y)
    assert _centre(faces["fin"])[1] < _centre(faces["fuselage_tail"])[1]           # the fin points up


@pytest.mark.parametrize("bank", [90, 180, -180])
def test_the_figure_turns_like_the_attitude(bank):
    faces, _order = _faces(_pose(bank=bank))
    right, left = _centre(faces["wing_right"]), _centre(faces["wing_left"])
    if bank == 90:
        assert right[1] > left[1] and abs(right[0] - left[0]) < 15        # right wing down, wings upright
    else:
        assert right[0] < left[0]                                           # inverted: right wing on the left
        assert _centre(faces["fin"])[1] > _centre(faces["fuselage_tail"])[1]   # the fin points down


@pytest.mark.parametrize("pitch", [90, -90])
def test_pitch_moves_the_nose_up_and_down(pitch):
    faces, _order = _faces(_pose(pitch=pitch))
    nose = next(face for name, face in faces.items() if name.startswith("nose_") and face.visible)
    tail = faces["fuselage_tail"]
    nose_y, tail_y = max(nose.points[1::2]) if pitch > 0 else min(nose.points[1::2]), _centre(tail)[1]
    assert (nose_y < tail_y) if pitch > 0 else (nose_y > tail_y)


def test_the_figure_stays_inside_its_box_at_every_attitude():
    full = {name: MAX_DEFLECTION_DEG * sign for name, sign in zip((RIGHT_AILERON, LEFT_AILERON, ELEVATOR, RUDDER),
                                                                    (1, -1, 1, -1))}
    x0, y0, width, height = BOX
    for bank, pitch in itertools.product(range(-180, 181, 30), range(-90, 91, 30)):
        faces, exhaust = project_aircraft(_pose(bank, pitch, full, throttle=1.0), BOX)
        points = [c for face in faces for c in face.points] + list(exhaust.points)
        assert all(x0 <= x <= x0 + width for x in points[0::2]), (bank, pitch)
        assert all(y0 <= y <= y0 + height for y in points[1::2]), (bank, pitch)


# ---------------- drawing order ----------------
def test_level_flight_shows_the_top_and_draws_the_fin_over_the_fuselage():
    faces, order = _faces(_pose())
    assert faces["fuselage_top"].visible and not faces["fuselage_bottom"].visible
    assert order.index("fin") > order.index("fuselage_top")
    assert order.index("rudder") > order.index("fuselage_top")


@pytest.mark.parametrize("bank", [180, -180, 150, -120])
def test_inverted_flight_hides_the_fin_behind_the_fuselage(bank):
    faces, order = _faces(_pose(bank=bank))
    assert faces["fuselage_bottom"].visible and not faces["fuselage_top"].visible
    assert order.index("fin") < order.index("fuselage_bottom")
    assert order.index("rudder") < order.index("fuselage_bottom")


@pytest.mark.parametrize("bank, pitch, underside", [(0, 0, False), (30, 10, False), (180, 0, True),
                                                   (-180, 0, True), (-135, -20, True), (0, 90, False),
                                                   (0, -90, True)])   # nose down: the camera behind sees the belly
def test_the_underside_is_marked_so_inverted_flight_shows(bank, pitch, underside):
    faces, _order = _faces(_pose(bank=bank, pitch=pitch))
    assert faces["wing_right"].underside == underside and faces["stabiliser_left"].underside == underside
    assert not faces["fin"].underside                          # the fin has no top or underside


def test_hidden_faces_are_listed_first_and_every_face_once():
    faces, _exhaust = project_aircraft(_pose(bank=35, pitch=20), BOX)
    visible = [face.visible for face in faces]
    assert visible == sorted(visible)                         # False first
    assert sorted(face.name for face in faces) == sorted(face.name for face in AIRCRAFT.faces)


@pytest.mark.parametrize("bank, raised_first", [(0, False), (180, True)])
def test_a_raised_aileron_is_drawn_over_the_wing_seen_from_above(bank, raised_first):
    """Aileron stick to the right: right aileron up (in front of the wing from above), left one down."""
    _faces_by_name, order = _faces(_pose(bank=bank, deflections=surface_deflections(1024, None, None)))
    assert (order.index(RIGHT_AILERON) < order.index("wing_right")) == raised_first
    assert (order.index(LEFT_AILERON) > order.index("wing_left")) == raised_first


def test_the_exhaust_follows_the_throttle():
    _faces_none, no_exhaust = project_aircraft(_pose(), BOX)
    _faces_half, half = project_aircraft(_pose(throttle=0.5), BOX)
    _faces_full, full = project_aircraft(_pose(throttle=1.0), BOX)
    assert no_exhaust is None and project_aircraft(_pose(throttle=0.0), BOX)[1] is None

    def length(exhaust):
        x0, y0, x1, y1 = exhaust.points
        return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    assert length(full) > length(half) > 0 and half.in_front          # it points to the camera behind the tail


# ---------------- control surfaces ----------------
@pytest.mark.parametrize("raw, angle", [(None, 0.0), (0, 0.0), (1024, 25.0), (-1024, -25.0), (512, 12.5),
                                        (2048, 25.0), (-3000, -25.0)])
def test_deflection_is_proportional_to_the_stick_and_stops_at_25_degrees(raw, angle):
    assert MAX_DEFLECTION_DEG == 25.0
    assert deflection(raw) == pytest.approx(angle)


def test_the_ailerons_move_against_each_other():
    for raw in (-1024, -300, 0, 512, 1024):
        angles = surface_deflections(raw, None, None)
        assert angles[RIGHT_AILERON] == pytest.approx(-angles[LEFT_AILERON])
    angles = surface_deflections(1024, 1024, 1024)
    assert angles == {RIGHT_AILERON: -25.0, LEFT_AILERON: 25.0, ELEVATOR: 25.0, RUDDER: 25.0}


def test_the_directions_of_the_surfaces_in_the_figure():
    """Positive aileron stick: right aileron trailing edge up, left down; positive elevator stick (pushed):
    elevator trailing edge down; positive rudder stick: rudder trailing edge to the right."""
    assert aircraft_shape.POSITIVE_AILERON_RAISES_RIGHT_AILERON
    assert aircraft_shape.POSITIVE_ELEVATOR_LOWERS_TRAILING_EDGE
    assert aircraft_shape.POSITIVE_RUDDER_MOVES_TRAILING_EDGE_RIGHT
    angles = surface_deflections(1024, 1024, 1024)

    def trailing_edge(name):
        face = next(face for face in AIRCRAFT.faces if face.name == name)
        hinge = AIRCRAFT.hinges[name]
        edge = min(face.points, key=lambda point: point[1])         # the rearmost point
        return rotate_about_axis(edge, hinge.start, hinge.end, angles[name])
    assert trailing_edge(RIGHT_AILERON)[2] > 0 and trailing_edge(LEFT_AILERON)[2] < 0
    assert trailing_edge(ELEVATOR)[2] < 0
    assert trailing_edge(RUDDER)[0] > 0


# ---------------- values of a row ----------------
def test_without_sticks_the_surfaces_stay_neutral_and_without_attitude_the_aircraft_is_level():
    time_s = np.arange(0, 5, 0.5)
    count = len(time_s)
    attitude_only = _track(time_s, **{roles.ROLL_ANGLE: np.full(count, 30.0), roles.PITCH_ANGLE: np.zeros(count)})
    pose = aircraft_pose(attitude_only, 3)
    assert (pose.bank, pose.pitch, pose.stale, pose.throttle) == (30.0, 0.0, False, None)
    assert set(pose.deflections.values()) == {0.0}
    sticks_only = _track(time_s, **{roles.STICK_AILERON: np.full(count, 512.0), roles.THROTTLE: np.zeros(count)})
    pose = aircraft_pose(sticks_only, 3)
    assert (pose.bank, pose.pitch, pose.stale) == (0.0, 0.0, False)
    assert pose.deflections[RIGHT_AILERON] == -12.5 and pose.deflections[ELEVATOR] == 0.0
    assert pose.throttle == pytest.approx(0.5)
    assert has_aircraft(attitude_only) and has_aircraft(sticks_only)


def test_without_attitude_and_sticks_there_is_no_aircraft():
    time_s = np.arange(0, 5, 0.5)
    assert not has_aircraft(_track(time_s, **{roles.ALTITUDE: np.zeros(len(time_s))}))
    assert not has_aircraft(_track(np.array([])))
    assert has_aircraft(_track(time_s, **{roles.THROTTLE: np.zeros(len(time_s))}))      # the throttle alone


def test_gaps_grey_the_attitude_and_put_a_quiet_stick_to_neutral():
    time_s = np.arange(0, 10, 0.25)
    count = len(time_s)
    roll = np.where(time_s < 3, 45.0, np.nan)                 # the gyro stops after 3 s
    elevator = np.where(time_s < 3, 1024.0, np.nan)           # the elevator channel too
    track = _track(time_s, **{roles.ROLL_ANGLE: roll, roles.STICK_ELEVATOR: elevator,
                              roles.STICK_RUDDER: np.full(count, -512.0), roles.THROTTLE: np.full(count, 1024.0),
                              roles.ALTITUDE: np.zeros(count)})        # telemetry goes on: the flight lasts 10 s
    held = aircraft_pose(track, track.row_at(4.0))            # 1.25 s old: still held
    assert (held.bank, held.stale, held.deflections[ELEVATOR]) == (45.0, False, 25.0)
    gone = aircraft_pose(track, track.row_at(6.0))            # older than 2 s
    assert (gone.bank, gone.stale) == (45.0, True)            # grey, keeps the last attitude
    assert gone.deflections[ELEVATOR] == 0.0 and gone.deflections[RUDDER] == -12.5
    assert gone.throttle == 1.0


def test_an_attitude_that_never_came_is_level_and_grey():
    time_s = np.arange(0, 5, 0.5)
    track = _track(time_s, **{roles.PITCH_ANGLE: np.full(len(time_s), np.nan),
                              roles.STICK_RUDDER: np.zeros(len(time_s))})
    pose = aircraft_pose(track, 2)
    assert (pose.bank, pose.pitch, pose.stale) == (0.0, 0.0, True)


@pytest.fixture(scope="module")
def largest_flight(tmp_path_factory):
    database = FlightDatabase(tmp_path_factory.mktemp("aircraft") / "flights.db")
    import_paths(database, [LARGEST_FLIGHT_LOG], Params(chem="Li-Ion", cells=13, nominal_mah=9000))
    log_id = database.connection.execute("SELECT id FROM log_file").fetchone()[0]
    return load_track(database.connection, log_id)


def test_one_row_of_a_real_log_matches_the_columns_of_the_log(largest_flight):
    """Row 731 of the log (log time 199.85 s) of the flight of 20 July 2026: QR -263, HR -799, SR 0, Gas -454."""
    track = largest_flight
    row = track.row_at(199.86 - track.origin)
    pose = aircraft_pose(track, row)
    assert pose.deflections[RIGHT_AILERON] == pytest.approx(263 / 1024 * 25)        # +6.4°: right aileron down
    assert pose.deflections[LEFT_AILERON] == pytest.approx(-263 / 1024 * 25)
    assert pose.deflections[ELEVATOR] == pytest.approx(-799 / 1024 * 25)            # −19.5°: trailing edge up
    assert pose.deflections[RUDDER] == 0.0
    assert pose.throttle == pytest.approx((-454 + 1024) / 2048)
    assert has_aircraft(track)
