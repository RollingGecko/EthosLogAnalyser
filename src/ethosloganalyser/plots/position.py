# -*- coding: utf-8 -*-
"""The vertical line that shows the position of the flight recorder in the time charts of a single flight.

The lines are "animated" artists: the chart itself is not redrawn when the position moves. ``Hover`` draws them
after every redraw of the figure and after every tooltip update (``Hover.overlay``), and ``PositionMarker.move``
draws just the lines over the saved picture of the chart (blitting). They are no data lines (their gid is
"position"), so the tooltip, the y range (``fit_y``) and the legend ignore them, and they do not change the
limits of the axes.
"""

from matplotlib.lines import Line2D

from ..recorder.chart_position import marker_time, time_axes

POSITION_GID = "position"
POSITION_COLOR = "#d6336c"      # stands out from the data colours and from the green switch lines


class PositionMarker:
    """The position line of one canvas, one line per time axes. hover: the canvas' ``Hover``."""

    def __init__(self, canvas, hover):
        self.canvas, self.hover = canvas, hover
        self.lines = []
        self.span = (0.0, 0.0)      # first and last time of the time axis of the charts
        self.time = None            # the position last shown [s]

    def attach(self, figure, position):
        """Puts a line on every time axes of the (new) figure; position None hides them."""
        self.lines = []
        times = getattr(figure, "_t", None)
        self.span = (float(times[0]), float(times[-1])) if times is not None and len(times) else (0.0, 0.0)
        for axes in time_axes(figure):
            line = Line2D([0.0, 0.0], [0.0, 1.0], transform=axes.get_xaxis_transform(), color=POSITION_COLOR,
                          lw=1.2, alpha=0.85, gid=POSITION_GID, label="_position", zorder=5, animated=True)
            axes.add_line(line)                   # the limits of the axes stay (set_xlim has switched autoscale off)
            self.lines.append(line)
        self.hover.overlay = self.lines
        self.time = None
        self._place(position)

    def _place(self, position):
        """Moves the lines without drawing; returns True if anything changed."""
        if position is None:
            changed = any(line.get_visible() for line in self.lines)
            for line in self.lines:
                line.set_visible(False)
            self.time = None
            return changed
        changed = False
        for line in self.lines:
            x = marker_time(position, *self.span)
            if not line.get_visible() or line.get_xdata()[0] != x:
                line.set_xdata([x, x])
                line.set_visible(True)
                changed = True
        self.time = position
        return changed

    def move(self, position):
        """Shows the position (None: no line). Draws only the lines over the saved chart."""
        if not self._place(position) or not self.lines:
            return
        hover = self.hover
        if getattr(hover, "_bg", None) is None:
            self.canvas.draw_idle()               # the chart has not been drawn yet
            return
        hover.redraw_overlay()
