# -*- coding: utf-8 -*-
"""Single-flight page: flight selection, views, time window (zoom, pan, drag), details, current spikes.

The page shows flights it is given as choices [(label, key)]; resolve(key) returns (result, params, path)
for drawing with plots/flight.py, where result is an analysis result (analysis/fleet.Result) that contains
the flight under path - or None if the flight cannot be drawn (yet); the page then shows message_for(key).
before_select(key) is called first, e.g. to show only the views the flight has data for (show_views).
"""

import numpy as np

from ..config import SPIKE_LABELS, label
from ..i18n import tr
from ..plots.flight import FLIGHT_VIEWS, VIEW_LABELS, draw_flight, fit_y
from ..plots.hover import Hover
from ..report.text import flight_detail_lines
from ..utils import fmt_duration
from .common import fill_text, make_text


class FlightPage:
    """The widgets and the behaviour of the single-flight page."""

    def __init__(self, parent, charts, family, filedialog, back=None):
        self.charts = charts
        self.filedialog = filedialog
        self.back = back                  # "Back to the logbook" (button shown if given)
        self.choices = []                 # [(label, key)] of the selectable flights
        self.resolve = lambda key: None   # key -> (result, params, path) or None
        self.before_select = None         # key -> None, called before a flight is shown
        self.message_for = lambda key: ""  # text shown instead of the charts when resolve gives None
        self.shown_path = None
        self.axes = []
        self.drag = None
        self.details_visible = True
        self.spike_times = []
        self._build(parent, family)

    # ---------------- widgets ----------------
    def _build(self, parent, family):
        import tkinter as tk
        from tkinter import ttk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self.frame = parent
        self._build_selection_bar(parent)
        self._build_view_bar(parent)
        self._build_time_bar(parent)
        self.readout_hint = tr(
            "Maus über das Diagramm bewegen: Werte zum Zeitpunkt.   Mausrad: zoomen  ·  Ziehen mit linker Maustaste: "
            "verschieben  ·  Doppelklick oder Rechtsklick: Diagramm vergrößern")
        self.readout = tk.StringVar(value=self.readout_hint)
        ttk.Label(parent, textvariable=self.readout, style="Readout.TLabel").pack(fill="x", padx=6)

        self.paned = ttk.PanedWindow(parent, orient="vertical")
        self.paned.pack(fill="both", expand=True, padx=6, pady=4)
        plot_frame = ttk.Frame(self.paned)
        self.details_frame = ttk.Frame(self.paned)
        self.paned.add(plot_frame, weight=4)
        self.paned.add(self.details_frame, weight=1)
        self.details = make_text(self.details_frame, family, height=10)
        scrollbar = ttk.Scrollbar(self.details_frame, orient="vertical", command=self.details.yview)
        self.details.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.details.pack(side="left", fill="both", expand=True)

        self.figure = Figure(figsize=(12, 7), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas._hover = Hover(self.canvas, crosshair=True, on_move=self.show_readout)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        for event_name, handler in (("scroll_event", self._on_scroll), ("button_press_event", self._on_press),
                                    ("button_release_event", self._on_release),
                                    ("motion_notify_event", self._on_motion)):
            self.canvas.mpl_connect(event_name, handler)

    def _build_selection_bar(self, parent):
        import tkinter as tk
        from tkinter import ttk
        bar = ttk.Frame(parent, padding=(6, 6, 6, 2))
        bar.pack(fill="x")
        self.selection_bar = bar
        if self.back is not None:
            ttk.Button(bar, text=tr("‹ Logbuch"), command=self.back).pack(side="left", padx=(0, 14))
        ttk.Label(bar, text=tr("Flug:")).pack(side="left")
        self.flight_var = tk.StringVar()
        self.flight_box = ttk.Combobox(bar, textvariable=self.flight_var, width=46, state="readonly")
        self.flight_box.pack(side="left", padx=(4, 4))
        self.flight_box.bind("<<ComboboxSelected>>", self.select_flight)
        ttk.Button(bar, text=tr("‹ zurück"), command=lambda: self.step_flight(-1)).pack(side="left")
        ttk.Button(bar, text=tr("vor ›"), command=lambda: self.step_flight(1)).pack(side="left", padx=(2, 14))
        self.details_button = ttk.Button(bar, text=tr("Details ausblenden"), command=self.toggle_details)
        self.details_button.pack(side="right")
        ttk.Button(bar, text=tr("Bild speichern …"), command=self.save_png).pack(side="right", padx=6)
        ttk.Button(bar, text=tr("Ganze Seite vergrößern"),
                   command=lambda: self.charts.open_fullscreen(self.builder, tr("Einzelflug"), flight=True)).pack(
            side="right")

    def _build_view_bar(self, parent):
        import tkinter as tk
        from tkinter import ttk
        # views in a row of their own: the labels are much longer in some languages
        bar = ttk.Frame(parent, padding=(6, 0, 6, 4))
        bar.pack(fill="x")
        ttk.Label(bar, text=tr("Ansicht:")).pack(side="left", padx=(0, 4))
        self.view_var = tk.StringVar(value=FLIGHT_VIEWS[0])
        self.view_buttons = {}
        self.no_view_label = ttk.Label(bar, text=tr("keine Diagramme für diesen Flug"), foreground="#666")
        for view in FLIGHT_VIEWS:
            button = ttk.Radiobutton(bar, text=label(VIEW_LABELS, view), value=view, variable=self.view_var,
                                     style="View.TRadiobutton", command=self.redraw)
            button.pack(side="left", padx=1)
            self.view_buttons[view] = button

    def _build_time_bar(self, parent):
        import tkinter as tk
        from tkinter import ttk
        bar = ttk.Frame(parent, padding=(6, 0, 6, 4))
        bar.pack(fill="x")
        ttk.Label(bar, text=tr("Zeit:")).pack(side="left")
        for text, command in [(tr("Ganzer Flug"), lambda: self.zoom_to(None)),
                              (tr("Start (60 s)"), lambda: self.zoom_to("start")),
                              (tr("Landung (60 s)"), lambda: self.zoom_to("end")),
                              (tr("Zoom +"), lambda: self.zoom_by(1 / 1.5)), (tr("Zoom −"), lambda: self.zoom_by(1.5)),
                              (tr("‹ früher"), lambda: self.pan_by(-0.3)), (tr("später ›"), lambda: self.pan_by(0.3))]:
            ttk.Button(bar, text=text, command=command).pack(side="left", padx=1)
        ttk.Label(bar, text="   " + tr("Stromspitze:")).pack(side="left")
        self.spike_var = tk.StringVar()
        self.spike_box = ttk.Combobox(bar, textvariable=self.spike_var, width=44, state="readonly")
        self.spike_box.pack(side="left", padx=4)
        self.spike_box.bind("<<ComboboxSelected>>", self.goto_spike)

    # ---------------- flights ----------------
    def set_choices(self, choices, resolve, selected_key=None, empty_message=""):
        """Sets the selectable flights and selects one (default: the last). Without flights the page shows
        empty_message."""
        self.choices = list(choices)
        self.resolve = resolve
        labels = [text for text, _key in self.choices]
        self.flight_box["values"] = labels
        if not labels:
            self.flight_var.set("")
            self.show_message(empty_message)
            return
        keys = [key for _text, key in self.choices]
        index = keys.index(selected_key) if selected_key in keys else len(labels) - 1
        self.flight_var.set(labels[index])
        self.select_flight()

    def current_key(self):
        labels = [text for text, _key in self.choices]
        if self.flight_var.get() not in labels:
            return None
        return self.choices[labels.index(self.flight_var.get())][1]

    def current(self):
        """(result, params, path) of the selected flight, or None."""
        key = self.current_key()
        return None if key is None else self.resolve(key)

    def builder(self):
        """Current flight, view and zoom as a new figure (for the full-screen window)."""
        from matplotlib.figure import Figure
        fig = Figure(figsize=(12, 7), dpi=100)
        selected = self.current()
        if selected is not None:
            axes = draw_flight(fig, *selected, self.view_var.get())
            if axes and self.axes:
                axes[0].set_xlim(self.axes[0].get_xlim())
        return fig

    def redraw(self, *_, keep_zoom=True):
        selected = self.current()
        if selected is None:
            return
        path = selected[2]
        old = self.axes[0].get_xlim() if (keep_zoom and self.axes and self.shown_path == path) else None
        self.axes = draw_flight(self.figure, *selected, self.view_var.get())
        if old and self.axes:
            self.axes[0].set_xlim(old)
            fit_y(self.axes)
        self.shown_path = path
        self.canvas.draw_idle()

    def show_views(self, views):
        """Shows only the view buttons in views; selects the first of them if the current one is hidden."""
        for button in self.view_buttons.values():
            button.pack_forget()
        self.no_view_label.pack_forget()
        for view in FLIGHT_VIEWS:
            if view in views:
                self.view_buttons[view].pack(side="left", padx=1)
        if not views:
            self.no_view_label.pack(side="left", padx=4)
        elif self.view_var.get() not in views:
            self.view_var.set(views[0])

    def show_message(self, text):
        """A text instead of the charts (no flight, flight without data, flight being prepared)."""
        if not self.axes and getattr(self, "_message", None) == text:
            return                                    # already shown: do not draw the figure again
        self._message = text
        self.axes = []
        self.shown_path = None
        self.figure.clear()
        self.figure.text(0.5, 0.5, text, ha="center", va="center", color="grey", fontsize=12, wrap=True)
        self.canvas.draw_idle()
        fill_text(self.details, [])
        self.spike_times = []
        self.spike_box["values"] = []
        self.spike_var.set("")

    def select_flight(self, *_):
        key = self.current_key()
        if key is None:
            return
        if self.before_select is not None:
            self.before_select(key)
        selected = self.resolve(key)
        if selected is None:
            self.show_message(self.message_for(key))
            return
        self._message = None
        self.readout.set(self.readout_hint)
        result, params, path = selected
        self.shown_path = None
        self.redraw(keep_zoom=False)
        fill_text(self.details, flight_detail_lines(result, params, path))
        rx = result.series[path].get("rx")
        items = []
        if rx:
            items = [f"{fmt_duration(sp['t'])} – {sp['peak']:.2f} A – {label(SPIKE_LABELS, sp['anlass'])}"
                     + (f" ({sp['schalter']})" if sp["schalter"] else "") for sp in rx["spikes"]]
        self.spike_times = [sp["t"] for sp in rx["spikes"]] if rx else []
        self.spike_box["values"] = items
        self.spike_var.set("" if items else tr("keine Spitzen"))

    def step_flight(self, step):
        labels = list(self.flight_box["values"])
        if not labels:
            return
        index = labels.index(self.flight_var.get()) if self.flight_var.get() in labels else len(labels) - 1
        self.flight_var.set(labels[max(0, min(len(labels) - 1, index + step))])
        self.select_flight()

    # ---------------- time window ----------------
    def full_range(self):
        result, _params, path = self.current()
        t = result.series[path]["t"]
        return float(t[0]), float(t[-1])

    def set_xlim(self, lo, hi):
        if not self.axes:
            return
        t0, t1 = self.full_range()
        span = min(max(hi - lo, 3.0), t1 - t0)
        lo = max(t0, min(lo, t1 - span))
        self.axes[0].set_xlim(lo, lo + span)
        fit_y(self.axes)
        self.canvas.draw_idle()

    def zoom_to(self, where):
        if not self.axes:
            return
        t0, t1 = self.full_range()
        if where is None:
            self.set_xlim(t0, t1)
        elif where == "start":
            self.set_xlim(t0, t0 + 60)
        else:
            self.set_xlim(t1 - 60, t1)

    def zoom_by(self, factor, center=None):
        if not self.axes:
            return
        lo, hi = self.axes[0].get_xlim()
        c = (lo + hi) / 2 if center is None else center
        self.set_xlim(c - (c - lo) * factor, c + (hi - c) * factor)

    def pan_by(self, fraction):
        if not self.axes:
            return
        lo, hi = self.axes[0].get_xlim()
        shift = (hi - lo) * fraction
        self.set_xlim(lo + shift, hi + shift)

    def goto_spike(self, *_):
        items = list(self.spike_box["values"])
        if self.spike_var.get() not in items:
            return
        t = self.spike_times[items.index(self.spike_var.get())]
        self.set_xlim(t - 10, t + 10)

    # ---------------- mouse ----------------
    def show_readout(self, x):
        t = getattr(self.figure, "_t", None)
        if x is None or t is None:
            return
        k = int(np.clip(np.searchsorted(t, x), 0, len(t) - 1))
        parts = [f"t = {fmt_duration(t[k])}"]
        for name, unit, y in self.figure._readout:
            if y is not None and k < len(y) and np.isfinite(y[k]):
                parts.append(f"{name} {y[k]:.4g} {unit}")
        self.readout.set("   ·   ".join(parts))

    def _on_scroll(self, ev):
        if ev.inaxes is None or ev.xdata is None:
            return
        self.zoom_by(1 / 1.25 if ev.button == "up" else 1.25, center=ev.xdata)

    def _on_press(self, ev):
        if ev.inaxes is None or ev.xdata is None:
            return
        if ev.dblclick:
            self.drag = None
            self.charts.open_chart(self.canvas, self.builder, tr("Einzelflug"), ev.inaxes, flight=True)
            return
        if ev.button == 3:
            self.charts.chart_menu(ev, self.canvas, self.builder, tr("Einzelflug"), flight=True)
            return
        if ev.button == 1:
            self.drag = (ev.x, self.axes[0].get_xlim())

    def _on_release(self, _ev):
        self.drag = None

    def _on_motion(self, ev):
        if self.drag is not None and ev.x is not None and self.axes:
            x0, (lo, hi) = self.drag
            bbox = self.axes[0].get_window_extent()
            shift = (ev.x - x0) / max(bbox.width, 1) * (hi - lo)
            self.set_xlim(lo - shift, hi - shift)
        # tooltip, crosshair and read-out: plots/hover.py (show_readout)

    # ---------------- details, saving ----------------
    def toggle_details(self):
        if self.details_visible:
            self.paned.forget(self.details_frame)
            self.details_button.configure(text=tr("Details einblenden"))
        else:
            self.paned.add(self.details_frame, weight=1)
            self.details_button.configure(text=tr("Details ausblenden"))
        self.details_visible = not self.details_visible

    def save_png(self):
        if self.current() is None:
            return
        path = self.filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self.figure.savefig(path, dpi=150)

    # ---------------- language switch ----------------
    def snapshot(self):
        """What the user is looking at on this page - restored after a language switch."""
        return {"view": self.view_var.get(), "details": self.details_visible, "flight": self.current_key(),
                "xlim": self.axes[0].get_xlim() if self.axes else None}

    def restore(self, snap):
        self.view_var.set(snap["view"])
        keys = [key for _text, key in self.choices]
        if snap["flight"] in keys:
            self.flight_var.set(self.choices[keys.index(snap["flight"])][0])
        self.select_flight()
        if snap["xlim"] and self.axes:
            self.set_xlim(*snap["xlim"])
        if not snap["details"]:
            self.toggle_details()
