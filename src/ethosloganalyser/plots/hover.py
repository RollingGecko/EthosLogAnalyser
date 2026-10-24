# -*- coding: utf-8 -*-
"""Mouse-over tooltip for every chart: shows the data point nearest to the mouse pointer.

One ``Hover`` per canvas (embedded chart or full-screen window). It works on any matplotlib figure without
changes to the chart code:

* data points are taken from lines (with markers, or with at least 3 points), scatter plots and bar charts in
  data coordinates; helper lines (axhline/axvline, 2-point trend lines) are ignored,
* all axes of the figure are searched, including twin axes (secondary y axis),
* the search runs on screen coordinates cached at every redraw (vectorised, also fast with 10 000+ points), and
  the tooltip is drawn with blitting, so the chart itself is not redrawn while the mouse moves.

How values are written is taken from ``ax._hover`` (see plots.common.hover_info, e.g. flight number -> flight
and date, seconds -> min:s), otherwise from the unit in the axis label ("Current [A]" -> "12.3 A").
"""

import re

import numpy as np

MAX_DIST_PX = 25        # pointer further away from every point: no tooltip


def nearest(points, x, y, max_dist=MAX_DIST_PX):
    """Nearest point to the screen position (x, y).

    points: list of (N_i, 2) arrays of screen coordinates (one per series; NaN rows are ignored).
    Returns (series index, point index, distance) or None if no point is within max_dist.
    """
    best = None
    for k, p in enumerate(points):
        if p is None or len(p) == 0:
            continue
        d2 = (p[:, 0] - x) ** 2 + (p[:, 1] - y) ** 2
        if not np.isfinite(d2).any():
            continue
        i = int(np.nanargmin(d2))
        if best is None or d2[i] < best[2]:
            best = (k, i, float(d2[i]))
    if best is None or best[2] > max_dist ** 2:
        return None
    return best[0], best[1], float(np.sqrt(best[2]))


_UNIT = re.compile(r"\[([^\]]+)\]\s*$")


def _unit(text):
    """Unit from an axis label or title: "Current [A]" -> "A"."""
    m = _UNIT.search(text or "")
    return m.group(1) if m else ""


def _num(v):
    if not np.isfinite(v):
        return "–"
    if abs(v) >= 1000:
        return f"{v:.0f}"
    return f"{v:.4g}"


def series_points(ax):
    """Data series of one axes: [(name, x, y, value)] arrays (see module docstring for what counts).

    value is the y value to show; it differs from y only for stacked bars (y = top of the segment, value = its
    height).
    """
    from matplotlib.collections import PathCollection
    from matplotlib.container import BarContainer
    out = []
    for ln in ax.get_lines():
        if not ln.get_visible() or ln.get_animated() or ln.get_gid() in ("hover", "cross"):
            continue
        if ln.get_transform() != ax.transData:          # axhline/axvline and other helper lines
            continue
        x = np.asarray(ln.get_xdata(), dtype=float)
        y = np.asarray(ln.get_ydata(), dtype=float)
        marker = ln.get_marker()
        if len(x) < 3 and marker in (None, "", "None", " "):
            continue                                     # 2-point trend/model lines
        out.append((ln.get_label(), x, y, y))
    for c in ax.collections:
        if isinstance(c, PathCollection) and c.get_visible() and c.get_offset_transform() == ax.transData:
            off = np.asarray(c.get_offsets(), dtype=float)
            if off.ndim == 2 and len(off):
                out.append((c.get_label(), off[:, 0], off[:, 1], off[:, 1]))
    for cont in ax.containers:
        if isinstance(cont, BarContainer) and len(cont.patches):
            xs = [r.get_x() + r.get_width() / 2 for r in cont.patches]
            ys = [r.get_y() + r.get_height() for r in cont.patches]
            vs = [r.get_height() for r in cont.patches]
            if cont.orientation == "horizontal":
                xs = [r.get_x() + r.get_width() for r in cont.patches]
                ys = [r.get_y() + r.get_height() / 2 for r in cont.patches]
                vs = [r.get_width() for r in cont.patches]
            out.append((cont.get_label(), np.asarray(xs, float), np.asarray(ys, float), np.asarray(vs, float)))
    return out


def point_text(ax, name, x, y):
    """Tooltip text for one data point: series name, x value and y value with unit."""
    info = getattr(ax, "_hover", {})
    if not name or name.startswith("_"):
        name = info.get("name") or ax.get_title(loc="left") or ax.get_ylabel()
    xt = info["x"](x) if "x" in info else f"x = {_num(x)} {_unit(ax.get_xlabel())}".rstrip()
    yu = _unit(ax.get_ylabel()) or _unit(ax.get_title(loc="left"))
    yt = info["y"](y) if "y" in info else f"{_num(y)} {yu}".rstrip()
    return f"{name}\n{xt}\n{yt}"


class Hover:
    """Tooltip (and optionally a vertical crosshair over all axes) for one canvas.

    on_move(x or None) is called with the x data value under the pointer (for read-outs outside the chart).
    """

    def __init__(self, canvas, crosshair=False, on_move=None, max_dist=MAX_DIST_PX):
        self.canvas, self.fig = canvas, canvas.figure
        self.crosshair, self.on_move, self.max_dist = crosshair, on_move, max_dist
        self._bg = None
        self._series = []            # [(ax, name, x, value, screen points)]
        self._last = None
        self._artists = {}
        self._cids = [canvas.mpl_connect(ev, fn) for ev, fn in (
            ("draw_event", self._on_draw), ("motion_notify_event", self._on_motion),
            ("figure_leave_event", self._on_leave))]

    def disconnect(self):
        for cid in self._cids:
            self.canvas.mpl_disconnect(cid)
        self._cids = []

    # -- artists (recreated after fig.clear(), e.g. when the flight view changes)
    def _artist(self, key, make):
        a = self._artists.get(key)
        owner = key[1] if isinstance(key, tuple) else self.fig
        alive = a is not None and (a.figure is self.fig) and (owner is self.fig or owner in self.fig.axes)
        if not alive:
            a = make()
            a.set_animated(True)
            self._artists[key] = a
        return a

    def _text(self):
        from matplotlib.transforms import IdentityTransform
        return self._artist("text", lambda: self.fig.text(
            0, 0, "", transform=IdentityTransform(), fontsize=8, zorder=1000, va="bottom", ha="left",
            bbox=dict(boxstyle="round,pad=0.4", fc="#fffff0", ec="#888888", alpha=0.95), visible=False))

    def _marker(self, ax):
        return self._artist(("marker", ax), lambda: ax.plot([np.nan], [np.nan], "o", ms=9, mfc="none", mec="#222",
                                                              mew=1.5, gid="hover", zorder=1000)[0])

    def _cross(self, ax):
        return self._artist(("cross", ax), lambda: ax.axvline(np.nan, color="#333", lw=0.8, alpha=0.7, gid="cross"))

    # -- events
    def _on_draw(self, _ev=None):
        self._bg = self.canvas.copy_from_bbox(self.fig.bbox) if hasattr(self.canvas, "copy_from_bbox") else None
        self._series = []
        for ax in self.fig.axes:
            if not ax.get_visible():
                continue
            bb = ax.bbox
            for name, x, y, v in series_points(ax):
                ok = np.isfinite(x) & np.isfinite(y)
                if not ok.any():
                    continue
                pts = np.full((len(x), 2), np.nan)
                pts[ok] = ax.transData.transform(np.column_stack([x[ok], y[ok]]))
                inside = (pts[:, 0] >= bb.x0 - 1) & (pts[:, 0] <= bb.x1 + 1) & (pts[:, 1] >= bb.y0 - 1) & \
                         (pts[:, 1] <= bb.y1 + 1)
                pts[~inside] = np.nan
                self._series.append((ax, name, x, v, pts, y))
        self._last = None

    def find(self, x_px, y_px):
        """(ax, name, x, value, y) of the data point nearest to the screen position, or None."""
        hit = nearest([s[4] for s in self._series], x_px, y_px, self.max_dist)
        if hit is None:
            return None
        ax, name, x, v, _, y = self._series[hit[0]]
        i = hit[1]
        return ax, name, float(x[i]), float(v[i]), float(y[i])

    def _on_leave(self, _ev=None):
        self._show(None, None)

    def _on_motion(self, ev):
        if ev.x is None or not any(ax.bbox.contains(ev.x, ev.y) for ax in self.fig.axes):
            self._show(None, None)
            return
        hit = self.find(ev.x, ev.y)
        xdata = hit[2] if hit else (ev.xdata if ev.inaxes is not None else None)
        self._show(hit, xdata, (ev.x, ev.y))

    def _show(self, hit, xdata, pos=None):
        key = (None if hit is None else (id(hit[0]), hit[1], hit[2], hit[3]),
               None if not self.crosshair or xdata is None else round(float(xdata), 6))
        if key == self._last:
            return
        self._last = key
        if self.on_move:
            self.on_move(xdata)
        if self._bg is None:
            return
        txt = self._text()
        self.canvas.restore_region(self._bg)
        if self.crosshair and xdata is not None:
            for ax in self.fig.axes:
                if ax.get_visible():
                    cr = self._cross(ax)
                    cr.set_xdata([xdata, xdata])
                    ax.draw_artist(cr)
        if hit is not None:
            ax, name, x, v, y = hit
            m = self._marker(ax)
            m.set_data([x], [y])
            ax.draw_artist(m)
            txt.set_text(point_text(ax, name, x, v))
            fx, fy = pos
            W, H = self.fig.bbox.width, self.fig.bbox.height
            txt.set_ha("right" if fx > 0.65 * W else "left")
            txt.set_va("top" if fy > 0.7 * H else "bottom")
            txt.set_position((fx + (-14 if fx > 0.65 * W else 14), fy + (-14 if fy > 0.7 * H else 14)))
            txt.set_visible(True)
            self.fig.draw_artist(txt)
        self.canvas.blit(self.fig.bbox)
