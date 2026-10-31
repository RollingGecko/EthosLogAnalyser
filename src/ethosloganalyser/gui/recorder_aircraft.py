# -*- coding: utf-8 -*-
"""The aircraft of the flight recorder on a Tk canvas: a simple 3D figure in the chase view that turns with the
attitude of the gyro, moves its control surfaces with the sticks and shows the throttle as an exhaust at the tail.

Same rules as for the other instruments (gui/recorder_instruments.py): one polygon per face of the figure and the
exhaust line are created once and then only moved, recoloured and put into the drawing order (``coords``,
``itemconfigure``, ``tag_raise``); the box and the note are drawn again only when the size or the language changes
(``place``). A stale attitude turns the aircraft grey (it keeps its last attitude); the geometry and the values
come from recorder/aircraft_shape.py.
"""

from ..i18n import N_, tr
from ..recorder.aircraft_shape import AIRCRAFT, BODY, FIXED, STICK_ROLES, aircraft_pose, project_aircraft
from .recorder_dials import STALE, fitting_size
from .recorder_instruments import BEZEL, NO_ATTITUDE, RIM, SCALE, SYMBOL

SURFACE = "#4fb3e8"            # control surfaces, set off against the aircraft in the colour of the horizon symbol
UNDERSIDE = "#b0603a"          # the underside of the aircraft (inverted flight is seen at once)
UNDERSIDE_SURFACE = "#2f6f9a"
STALE_SURFACE = "#a3aab3"
STALE_UNDERSIDE = "#5c626b"
EXHAUST = "#ff7a3d"
EDGE = "#14161a"
DARKEST_SHADE = 0.55           # brightness of a face seen edge-on (1.0 = facing the camera)

NO_STICKS = N_("keine Knüppeldaten")


def shaded(colour, shade):
    """The colour "#rrggbb" darkened for a face that is turned away from the camera (shade 0..1)."""
    factor = DARKEST_SHADE + (1.0 - DARKEST_SHADE) * min(max(shade, 0.0), 1.0)
    channels = (int(colour[index:index + 2], 16) for index in (1, 3, 5))
    return "#" + "".join(f"{round(channel * factor):02x}" for channel in channels)


def face_colour(face, stale):
    """Colour of a face before shading: aircraft or control surface, top or underside, grey when stale."""
    surface = face.part not in (BODY, FIXED)
    if stale:
        return STALE_UNDERSIDE if face.underside else (STALE_SURFACE if surface else STALE)
    if face.underside:
        return UNDERSIDE_SURFACE if surface else UNDERSIDE
    return SURFACE if surface else SYMBOL


class AircraftPanel:
    """The aircraft: place() draws the box for a rectangle, show() turns the figure to the values of a row."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.tag = "aircraft"
        self.box = None                                  # (x, y, width, height) the figure is drawn in
        self.visible = False
        dynamic = (self.tag, self.tag + "-dynamic")
        self.faces = {face.name: canvas.create_polygon(0, 0, 0, 0, 0, 0, outline=EDGE, state="hidden", tags=dynamic)
                      for face in AIRCRAFT.faces}
        self.exhaust = canvas.create_line(0, 0, 0, 0, fill=EXHAUST, capstyle="round", state="hidden", tags=dynamic)
        self.note = canvas.create_text(0, 0, fill=SCALE, state="hidden", tags=dynamic)

    # ---------------- static parts ----------------
    def place(self, rect, line_height, family, track):
        """Draws the box in rect and the note on missing data of the track (again after a size or language
        change)."""
        canvas, tag = self.canvas, self.tag
        canvas.delete(tag + "-back")
        canvas.create_rectangle(rect.x, rect.y, rect.right, rect.bottom, fill=BEZEL, outline=RIM, width=2,
                                tags=(tag, tag + "-back"))
        notes = []
        if track.attitude(0) is None:
            notes.append(tr(NO_ATTITUDE))
        if not any(track.has(role) for role in STICK_ROLES.values()):
            notes.append(tr(NO_STICKS))
        padding = max(4.0, line_height * 0.3)
        note_height = line_height * 1.2 if notes else 0.0
        self.box = (rect.x + padding, rect.y + padding, rect.width - 2 * padding,
                    rect.height - 2 * padding - note_height)
        text = " · ".join(notes)
        size = fitting_size(family, line_height * 0.8, 7,
                            lambda font, _bold: font.measure(text) <= rect.width - 2 * padding)
        canvas.coords(self.note, rect.x + rect.width / 2, rect.bottom - padding - note_height / 2)
        canvas.itemconfigure(self.note, text=text, font=(family, -size))
        canvas.tag_lower(tag + "-back")
        self.visible = True
        canvas.itemconfigure(tag + "-back", state="normal")
        canvas.itemconfigure(self.note, state="normal" if notes else "hidden")

    def hide(self):
        """The aircraft is not shown (no attitude and no sticks in the log, or the layout leaves it out)."""
        self.visible = False
        self.canvas.delete(self.tag + "-back")
        self.canvas.itemconfigure(self.tag, state="hidden")

    # ---------------- moving parts ----------------
    def show(self, track, row):
        """Turns the figure to the attitude and moves the control surfaces and the exhaust to the values of a row."""
        if not self.visible or track is None:
            return
        canvas = self.canvas
        pose = aircraft_pose(track, row)
        faces, exhaust = project_aircraft(pose, self.box)
        order = []
        for face in faces:
            item = self.faces[face.name]
            if not face.visible:
                canvas.itemconfigure(item, state="hidden")
                continue
            canvas.coords(item, *face.points)
            canvas.itemconfigure(item, state="normal", fill=shaded(face_colour(face, pose.stale), face.shade))
            order.append(item)
        if exhaust is not None:
            canvas.coords(self.exhaust, *exhaust.points)
            canvas.itemconfigure(self.exhaust, state="normal", width=exhaust.width,
                                 fill=STALE if pose.stale else EXHAUST)
            order = order + [self.exhaust] if exhaust.in_front else [self.exhaust] + order
        else:
            canvas.itemconfigure(self.exhaust, state="hidden")
        for item in order:                               # far faces first, each one raised over the ones before
            canvas.tag_raise(item)
