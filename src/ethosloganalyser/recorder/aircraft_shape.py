# -*- coding: utf-8 -*-
"""The aircraft of the flight recorder as plain functions: a simple 3D figure turned by roll and pitch, its control
surfaces moved by the sticks, projected to the canvas (pixels, y down). No Tkinter.

The figure is one general shape for all models (fuselage, wing with two ailerons, horizontal tail with elevator,
fin with rudder), stored as point lists in AIRCRAFT so that a figure per model type can be added later. Body axes:
x to the right wing, y to the nose, z up; the half span is 1.

It is seen from behind and above ("chase view", camera tilted down by VIEW_ELEVATION_DEG): the course is fixed, the
log has no yaw. The attitude comes only from the gyro (``FlightTrack.attitude``: bank > 0 = right wing down, pitch
> 0 = nose up), never from the sticks. The faces are drawn far ones first; a face that lies wholly on the camera
side of the plane of another face is drawn after it, which keeps inverted flight and a bank beyond 90° right. The
fuselage is a closed box, its faces turned away from the camera are left out.

Control surfaces: the deflection follows the stick, ±100 % stick = ±MAX_DEFLECTION_DEG (a picture only, nothing about
the real servo travel). The directions are assumptions, see the constants below.
"""

import math
from dataclasses import dataclass

from ..db import sensor_roles as roles
from .readouts import throttle_percent
from .stick_modes import FULL_DEFLECTION, POSITIVE_ELEVATOR_IS_UP

# ---- directions of the control surfaces: ASSUMPTIONS, to be checked by the owner with the test EXE -------------
# The only place that knows them. A deflection angle > 0 means trailing edge down (ailerons, elevator) or trailing
# edge to the right (rudder).
# Positive aileron stick (to the right) = right aileron up, left aileron down (roll to the right).
POSITIVE_AILERON_RAISES_RIGHT_AILERON = True
# Positive elevator stick = pushed = elevator trailing edge down (nose down); follows the radio, which draws a
# positive elevator value as the stick pushed up (stick_modes.POSITIVE_ELEVATOR_IS_UP).
POSITIVE_ELEVATOR_LOWERS_TRAILING_EDGE = POSITIVE_ELEVATOR_IS_UP
# Positive rudder stick (to the right) = rudder trailing edge to the right (yaw to the right).
POSITIVE_RUDDER_MOVES_TRAILING_EDGE_RIGHT = True

MAX_DEFLECTION_DEG = 25.0      # deflection at ±100 % stick
VIEW_ELEVATION_DEG = 35.0      # the camera looks down on the aircraft by this angle
CAMERA_DISTANCE = 6.0          # distance of the camera from the centre of the aircraft (in half spans)
EXHAUST_LENGTH = 0.3           # length of the exhaust at 100 % throttle (in half spans)
FIT = 0.94                     # share of the half size of the box the figure may take at most
EPSILON = 1e-6

FIXED, BODY = "fixed", "body"
LEFT_AILERON, RIGHT_AILERON, ELEVATOR, RUDDER = "left_aileron", "right_aileron", "elevator", "rudder"
SURFACES = (LEFT_AILERON, RIGHT_AILERON, ELEVATOR, RUDDER)
EXHAUST = "exhaust"


@dataclass(frozen=True)
class Face:
    """A flat face of the figure: its points (x, y, z) and what it belongs to (BODY: closed fuselage, FIXED: a
    surface seen from both sides, or the name of a control surface)."""
    name: str
    part: str
    points: tuple


@dataclass(frozen=True)
class Hinge:
    """Axis a control surface turns about: two points; turning by a positive angle about the direction from the
    first to the second moves the trailing edge down (x axis) or to the right (z axis)."""
    start: tuple
    end: tuple


@dataclass(frozen=True)
class AircraftFigure:
    """Point lists of one figure: faces, hinges of the control surfaces, and where the exhaust starts."""
    faces: tuple
    hinges: dict
    exhaust_start: tuple


def _general_figure():
    """The general figure for all models (see the module text)."""
    width, height = 0.075, 0.085              # half width and half height of the fuselage
    tail_y, nose_base_y, nose_y = -0.95, 0.42, 0.78
    w, h = width, height
    faces = [
        # fuselage: a box from the tail to the nose base and a pointed nose
        Face("fuselage_top", BODY, ((-w, tail_y, h), (w, tail_y, h), (w, nose_base_y, h), (-w, nose_base_y, h))),
        Face("fuselage_bottom", BODY, ((-w, tail_y, -h), (-w, nose_base_y, -h), (w, nose_base_y, -h),
                                      (w, tail_y, -h))),
        Face("fuselage_right", BODY, ((w, tail_y, -h), (w, nose_base_y, -h), (w, nose_base_y, h), (w, tail_y, h))),
        Face("fuselage_left", BODY, ((-w, tail_y, -h), (-w, tail_y, h), (-w, nose_base_y, h),
                                    (-w, nose_base_y, -h))),
        Face("fuselage_tail", BODY, ((-w, tail_y, -h), (w, tail_y, -h), (w, tail_y, h), (-w, tail_y, h))),
        Face("nose_top", BODY, ((-w, nose_base_y, h), (w, nose_base_y, h), (0.0, nose_y, 0.0))),
        Face("nose_bottom", BODY, ((-w, nose_base_y, -h), (0.0, nose_y, 0.0), (w, nose_base_y, -h))),
        Face("nose_right", BODY, ((w, nose_base_y, -h), (0.0, nose_y, 0.0), (w, nose_base_y, h))),
        Face("nose_left", BODY, ((-w, nose_base_y, -h), (-w, nose_base_y, h), (0.0, nose_y, 0.0))),
    ]
    hinges = {}
    # wing halves with the aileron cut out of the trailing edge (outer part)
    root_le, root_te, tip_le, tip_te, aileron_from, aileron_chord = 0.2, -0.12, 0.08, -0.05, 0.45, 0.08

    def trailing_edge(x):
        return root_te + (tip_te - root_te) * (x - w) / (1.0 - w)

    for side, sign in (("right", 1.0), ("left", -1.0)):
        hinge_inner = (sign * aileron_from, trailing_edge(aileron_from) + aileron_chord, 0.0)
        hinge_outer = (sign * 1.0, tip_te + aileron_chord, 0.0)
        faces.append(Face(f"wing_{side}", FIXED, (
            (sign * w, root_le, 0.0), (sign * 1.0, tip_le, 0.0), hinge_outer, hinge_inner,
            (sign * aileron_from, trailing_edge(aileron_from), 0.0), (sign * w, root_te, 0.0))))
        aileron = RIGHT_AILERON if sign > 0 else LEFT_AILERON
        faces.append(Face(aileron, aileron, (hinge_inner, hinge_outer, (sign * 1.0, tip_te, 0.0),
                                             (sign * aileron_from, trailing_edge(aileron_from), 0.0))))
        # x axis from the left to the right point: a positive angle moves the trailing edge down
        hinges[aileron] = Hinge(hinge_inner, hinge_outer) if sign > 0 else Hinge(hinge_outer, hinge_inner)
    # horizontal tail: stabiliser halves and one elevator over the full span of the tail
    tail_span, tail_le, hinge_y, tail_te = 0.36, -0.66, -0.82, -0.95
    for side, sign in (("right", 1.0), ("left", -1.0)):
        faces.append(Face(f"stabiliser_{side}", FIXED, (
            (sign * w, tail_le, 0.0), (sign * tail_span, tail_le - 0.06, 0.0), (sign * tail_span, hinge_y, 0.0),
            (sign * w, hinge_y, 0.0))))
    faces.append(Face(ELEVATOR, ELEVATOR, ((-tail_span, hinge_y, 0.0), (tail_span, hinge_y, 0.0),
                                           (tail_span, tail_te, 0.0), (-tail_span, tail_te, 0.0))))
    hinges[ELEVATOR] = Hinge((-tail_span, hinge_y, 0.0), (tail_span, hinge_y, 0.0))
    # fin and rudder on top of the fuselage (z axis upwards: a positive angle moves the trailing edge right)
    fin_top, fin_hinge_y = 0.42, -0.84
    faces.append(Face("fin", FIXED, ((0.0, -0.55, h), (0.0, -0.78, fin_top), (0.0, fin_hinge_y, fin_top),
                                     (0.0, fin_hinge_y, h))))
    faces.append(Face(RUDDER, RUDDER, ((0.0, fin_hinge_y, h), (0.0, fin_hinge_y, fin_top), (0.0, tail_y, fin_top),
                                       (0.0, tail_y, h))))
    hinges[RUDDER] = Hinge((0.0, fin_hinge_y, h), (0.0, fin_hinge_y, fin_top))
    return AircraftFigure(faces=tuple(faces), hinges=hinges, exhaust_start=(0.0, tail_y, 0.0))


AIRCRAFT = _general_figure()


# ---------------- what the aircraft shows in a row ----------------
@dataclass(frozen=True)
class AircraftPose:
    """Attitude and control surfaces of one row: bank and pitch [°] (0 without attitude data), stale = the attitude
    is older than the limit of the track, deflections [°] per control surface, throttle 0..1 or None."""
    bank: float
    pitch: float
    stale: bool
    deflections: dict
    throttle: float = None


STICK_ROLES = {"aileron": roles.STICK_AILERON, "elevator": roles.STICK_ELEVATOR, "rudder": roles.STICK_RUDDER}


def deflection(raw):
    """Deflection [°] for a stick value (-1024 .. +1024), limited to ±MAX_DEFLECTION_DEG; 0 without a value."""
    if raw is None:
        return 0.0
    share = min(max(float(raw) / FULL_DEFLECTION, -1.0), 1.0)
    return share * MAX_DEFLECTION_DEG


def surface_deflections(aileron, elevator, rudder):
    """Deflection of every control surface [°] for the three stick values (None = no value: the surface stays
    neutral). The ailerons move against each other."""
    roll = deflection(aileron) * (-1.0 if POSITIVE_AILERON_RAISES_RIGHT_AILERON else 1.0)
    return {RIGHT_AILERON: roll, LEFT_AILERON: -roll,
            ELEVATOR: deflection(elevator) * (1.0 if POSITIVE_ELEVATOR_LOWERS_TRAILING_EDGE else -1.0),
            RUDDER: deflection(rudder) * (1.0 if POSITIVE_RUDDER_MOVES_TRAILING_EDGE_RIGHT else -1.0)}


def _recent(track, role, row):
    """Value of a role in a row, None if the log has no such column or its value is older than the limit."""
    if not track.has(role) or track.is_stale(role, row):
        return None
    return track.value(role, row)


def has_aircraft(track):
    """True if the log has an attitude or at least one stick or the throttle (without all of them the aircraft is
    left out)."""
    if track.is_empty:
        return False
    return track.attitude(0) is not None or any(track.has(role) for role in (*STICK_ROLES.values(), roles.THROTTLE))


def aircraft_pose(track, row):
    """AircraftPose of a row: the attitude of the gyro (the last one when it is old, level without any), the
    surfaces from the sticks (neutral when a stick is missing or old), the throttle if the log has it."""
    attitude = track.attitude(row)
    bank, pitch, stale = attitude if attitude is not None else (0.0, 0.0, False)
    sticks = {axis: _recent(track, role, row) for axis, role in STICK_ROLES.items()}
    throttle = None
    if track.has(roles.THROTTLE):
        value = _recent(track, roles.THROTTLE, row)
        throttle = throttle_percent(value) / 100.0 if value is not None else 0.0
    return AircraftPose(bank=bank, pitch=pitch, stale=stale,
                        deflections=surface_deflections(sticks["aileron"], sticks["elevator"], sticks["rudder"]),
                        throttle=throttle)


# ---------------- turning and projection ----------------
def rotate_about_axis(point, start, end, angle_deg):
    """The point turned by angle_deg about the axis from start to end (right-hand rule)."""
    axis = [b - a for a, b in zip(start, end)]
    length = math.sqrt(sum(c * c for c in axis))
    if length < EPSILON or not angle_deg:
        return tuple(point)
    kx, ky, kz = (c / length for c in axis)
    px, py, pz = (p - a for p, a in zip(point, start))
    cos, sin = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    dot = kx * px + ky * py + kz * pz
    cross = (ky * pz - kz * py, kz * px - kx * pz, kx * py - ky * px)
    turned = [p * cos + c * sin + k * dot * (1 - cos) for p, c, k in zip((px, py, pz), cross, (kx, ky, kz))]
    return tuple(t + a for t, a in zip(turned, start))


def attitude_point(point, bank_deg, pitch_deg):
    """A point of the body turned to the attitude (roll first, then pitch; the course stays fixed)."""
    x, y, z = point
    bank, pitch = math.radians(bank_deg), math.radians(pitch_deg)
    # roll about the y axis: bank > 0 puts the right wing (x > 0) down
    x, z = x * math.cos(bank) + z * math.sin(bank), -x * math.sin(bank) + z * math.cos(bank)
    # pitch about the x axis: pitch > 0 lifts the nose (y > 0)
    y, z = y * math.cos(pitch) - z * math.sin(pitch), y * math.sin(pitch) + z * math.cos(pitch)
    return x, y, z


def camera_point(point):
    """World point in camera coordinates (x right, depth away from the camera, up) of the chase view."""
    x, y, z = point
    elevation = math.radians(VIEW_ELEVATION_DEG)
    return (x, y * math.cos(elevation) - z * math.sin(elevation), y * math.sin(elevation) + z * math.cos(elevation))


def view_matrix(bank_deg, pitch_deg):
    """3 x 3 matrix (rows) from body to camera coordinates: attitude_point, then camera_point."""
    columns = [camera_point(attitude_point(axis, bank_deg, pitch_deg)) for axis in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
    return tuple(tuple(column[row] for column in columns) for row in range(3))


def apply(matrix, point):
    """matrix x point."""
    x, y, z = point
    (a, b, c), (d, e, f), (g, h, i) = matrix
    return a * x + b * y + c * z, d * x + e * y + f * z, g * x + h * y + i * z


def perspective(depth):
    """Size factor of a point at a depth (the camera stands at -CAMERA_DISTANCE)."""
    return CAMERA_DISTANCE / max(CAMERA_DISTANCE + depth, EPSILON)


def _bounding_radius(figure):
    """Largest distance of a point from the centre, with the surfaces at full deflection and the full exhaust."""
    points = [point for face in figure.faces for point in face.points]
    for name, hinge in figure.hinges.items():
        for face in figure.faces:
            if face.part == name:
                points += [rotate_about_axis(point, hinge.start, hinge.end, angle)
                           for point in face.points for angle in (-MAX_DEFLECTION_DEG, MAX_DEFLECTION_DEG)]
    x, y, z = figure.exhaust_start
    points.append((x, y - EXHAUST_LENGTH, z))
    return max(math.sqrt(sum(c * c for c in point)) for point in points)


BOUNDING_RADIUS = _bounding_radius(AIRCRAFT)


def figure_scale(width, height):
    """Pixels per half span so that the figure stays inside a box of width x height at every attitude."""
    largest = BOUNDING_RADIUS * perspective(-BOUNDING_RADIUS)
    return FIT * min(width, height) / 2 / largest


# ---------------- faces in drawing order ----------------
@dataclass(frozen=True)
class ProjectedFace:
    """A face ready to draw: its name and part, the canvas points (x0, y0, x1, y1, ...), a shade 0..1 (1 = facing
    the camera), whether it is shown (faces of the fuselage turned away are not), and whether the camera sees the
    underside of the aircraft on it (drawn in another colour, so inverted flight is seen at once)."""
    name: str
    part: str
    points: tuple
    shade: float
    visible: bool
    underside: bool = False


def _subtract(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _centroid(points):
    return tuple(sum(c) / len(points) for c in zip(*points))


def _normal(points):
    """Unit normal of a flat face (Newell's method, works for any polygon); None for a degenerate one."""
    normal = [0.0, 0.0, 0.0]
    for index, (x, y, z) in enumerate(points):
        nx, ny, nz = points[(index + 1) % len(points)]
        normal[0] += (y - ny) * (z + nz)
        normal[1] += (z - nz) * (x + nx)
        normal[2] += (x - nx) * (y + ny)
    length = math.sqrt(_dot(normal, normal))
    return tuple(c / length for c in normal) if length > EPSILON else None


CAMERA = (0.0, -CAMERA_DISTANCE, 0.0)      # the camera in camera coordinates


@dataclass
class _Placed:
    """A face in camera coordinates while the drawing order is worked out."""
    face: Face
    points: list
    normal: tuple          # unit normal turned to the camera, None for a degenerate face
    offset: float          # normal . point of the plane
    depth: float
    facing: float          # |cos| of the angle between the normal and the line to the camera
    visible: bool
    underside: bool        # a face lying flat in the aircraft, seen from below


LYING_FLAT = 0.5           # |cos| between the normal of a face and the up axis of the aircraft from which it lies flat


def _place(face, points, body_centre, body_up):
    """_Placed of a face from its points in camera coordinates; body_up: the up axis of the aircraft in them."""
    normal = _normal(points)
    centre = _centroid(points)
    to_camera = _subtract(CAMERA, centre)
    distance = math.sqrt(_dot(to_camera, to_camera)) or 1.0
    visible, facing, offset, underside = True, 0.0, 0.0, False
    if normal is not None:
        underside = abs(_dot(normal, body_up)) > LYING_FLAT and _dot(body_up, to_camera) < 0
        if face.part == BODY:                       # a face of the closed fuselage turned away is not seen
            outward = _dot(normal, _subtract(centre, body_centre)) > 0
            visible = (_dot(normal, to_camera) > EPSILON) == outward
        if _dot(normal, to_camera) < 0:
            normal = (-normal[0], -normal[1], -normal[2])
        facing = _dot(normal, to_camera) / distance
        offset = _dot(normal, points[0])
    return _Placed(face, points, normal, offset, centre[1], facing, visible, underside)


def _side_of(points, plane):
    """+1 if all points lie on the camera side of the plane of a face, -1 if all lie on the far side, 0 if mixed
    or the plane is seen edge-on."""
    if plane.normal is None or plane.facing < EPSILON:
        return 0
    nx, ny, nz = plane.normal
    distances = [nx * x + ny * y + nz * z for x, y, z in points]
    if min(distances) >= plane.offset - EPSILON:
        return 1
    if max(distances) <= plane.offset + EPSILON:
        return -1
    return 0


def _plane_order(first, second):
    """Order of two faces by their planes: -1 draw first before second, +1 after, 0 if the planes do not decide
    (the faces cut each other's planes, or a plane is seen edge-on)."""
    side = _side_of(second.points, first)
    if side:
        return -side                       # second on the camera side of the plane of first: first is drawn first
    return _side_of(first.points, second)


def project_aircraft(pose, rect, figure=AIRCRAFT):
    """Faces of the figure for a pose in a rectangle (x, y, width, height): the hidden faces of the fuselage first,
    then the shown ones in drawing order; and the exhaust or None. Returns (faces, exhaust)."""
    x0, y0, width, height = rect
    centre_x, centre_y = x0 + width / 2, y0 + height / 2
    scale = figure_scale(width, height)

    matrix = view_matrix(pose.bank, pose.pitch)

    def to_canvas(point):
        x, depth, up = point
        factor = perspective(depth) * scale
        return centre_x + x * factor, centre_y - up * factor

    body_centre = apply(matrix, (0.0, -0.1, 0.0))
    body_up = apply(matrix, (0.0, 0.0, 1.0))
    placed = []
    for face in figure.faces:
        points = face.points
        if face.part in figure.hinges:
            hinge = figure.hinges[face.part]
            points = [rotate_about_axis(point, hinge.start, hinge.end, pose.deflections.get(face.part, 0.0))
                      for point in points]
        placed.append(_place(face, [apply(matrix, point) for point in points], body_centre, body_up))
    hidden = [item for item in placed if not item.visible]
    ordered = _paint_order([item for item in placed if item.visible])
    faces = [ProjectedFace(name=item.face.name, part=item.face.part,
                           points=tuple(c for point in item.points for c in to_canvas(point)),
                           shade=item.facing, visible=item.visible, underside=item.underside)
             for item in hidden + ordered]
    exhaust = None
    if pose.throttle:
        x, y, z = figure.exhaust_start
        start, end = apply(matrix, (x, y, z)), apply(matrix, (x, y - EXHAUST_LENGTH * pose.throttle, z))
        exhaust = Exhaust(points=to_canvas(start) + to_canvas(end), width=max(2.0, 0.09 * scale),
                          in_front=(start[1] + end[1]) / 2 < body_centre[1])
    return faces, exhaust


@dataclass(frozen=True)
class Exhaust:
    """The exhaust as a line: canvas points (x0, y0, x1, y1), line width, and whether it is drawn over the figure
    (it points to the camera) or behind it."""
    points: tuple
    width: float
    in_front: bool


def _paint_order(items):
    """Faces in drawing order: a face on the camera side of another one's plane after it, else far ones first.

    A topological order of the "drawn before" pairs the planes decide, taking the farthest face whose predecessors
    are all drawn; should the pairs ever form a cycle, the farthest face left is taken."""
    count = len(items)
    before = [set() for _item in range(count)]          # before[b]: faces that must be drawn before face b
    for a in range(count):
        for b in range(a + 1, count):
            order = _plane_order(items[a], items[b])
            if order < 0:
                before[b].add(a)
            elif order > 0:
                before[a].add(b)
    ordered, done = [], set()
    remaining = sorted(range(count), key=lambda index: -items[index].depth)
    while remaining:
        ready = next((index for index in remaining if before[index] <= done), remaining[0])
        remaining.remove(ready)
        done.add(ready)
        ordered.append(items[ready])
    return ordered
