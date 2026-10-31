# -*- coding: utf-8 -*-
"""Chart canvases of the window: toolbar, tooltip, context menu, enlarging a chart or a whole page."""

from ..gui.style import BG
from ..i18n import tr
from ..plots.flight import fit_y
from ..plots.hover import Hover
from ..plots.position import PositionMarker
from ..plots.single import chart_index, chart_title, single_chart


class ChartManager:
    """Creates chart canvases and the full-screen windows for one build of the window content.

    fullscreen: the open full-screen windows; page_canvases: {str(frame): canvas} of the chart pages shown
    with show_fig (both also used by tests). position_source: function that returns the position of the flight
    recorder [s] (or None); the enlarged single-flight charts show it as a line (set by the single-flight page).
    """

    def __init__(self, root):
        self.root = root
        self.fullscreen = []
        self.page_canvases = {}
        self.position_source = None

    def chart_canvas(self, parent, fig, builder, title, crosshair=False, on_move=None, flight=False,
                     whole_page=True):
        """Canvas with toolbar and tooltip (plots/hover.py) - the same for every chart.

        With a builder (function that draws the page again): a double-click or the context menu (right-click)
        enlarges the chart under the mouse on its own; the toolbar button enlarges the whole page.
        whole_page=False: the canvas already shows the whole page (full-screen window) - no button and no menu
        entry for it, but double-click and "Enlarge this chart" still work. flight: single-flight page.
        """
        from tkinter import ttk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

        canvas = FigureCanvasTkAgg(fig, master=parent)
        toolbar = NavigationToolbar2Tk(canvas, parent)
        if builder is not None and whole_page:
            ttk.Button(toolbar, text=tr("Ganze Seite vergrößern"),
                       command=lambda: self.open_fullscreen(builder, title)).pack(side="left", padx=6)
            ttk.Label(toolbar, text=tr("Doppelklick oder Rechtsklick auf ein Diagramm: allein vergrößern"),
                      foreground="#666", background=toolbar.cget("background")).pack(side="left", padx=6)
        toolbar.update()
        canvas._hover = Hover(canvas, crosshair=crosshair, on_move=on_move)     # keep a reference
        if builder is not None:
            def on_press(ev):
                if ev.inaxes is None or getattr(toolbar.mode, "name", "NONE") != "NONE":
                    return                            # zoom/pan mode of the toolbar uses the mouse buttons
                if ev.dblclick:
                    self.open_chart(canvas, builder, title, ev.inaxes, flight=flight)
                elif ev.button == 3:
                    self.chart_menu(ev, canvas, builder, title, flight=flight, whole_page=whole_page)
            canvas.mpl_connect("button_press_event", on_press)
            canvas._on_press = on_press               # connected again when the figure is replaced
        canvas._toolbar = toolbar
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        return canvas

    def chart_menu(self, ev, canvas, builder, title, flight=False, whole_page=True):
        """Context menu of a chart: enlarge this chart or (whole_page) the whole page."""
        import tkinter as tk
        if ev.inaxes is None:
            return
        ax = ev.inaxes
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=tr("Dieses Diagramm vergrößern"),
                         command=lambda: self.open_chart(canvas, builder, title, ax, flight=flight))
        if whole_page:
            menu.add_command(label=tr("Ganze Seite vergrößern"),
                             command=lambda: self.open_fullscreen(builder, title, flight=flight))
        gui = getattr(ev, "guiEvent", None)
        x, y = (gui.x_root, gui.y_root) if gui is not None and hasattr(gui, "x_root") else (
            self.root.winfo_pointerx(), self.root.winfo_pointery())
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def open_chart(self, canvas, builder, title, ax, flight=False):
        """The chart ax of the page shown in canvas on its own in a full-screen window."""
        return self.open_fullscreen(builder, title, index=chart_index(canvas.figure, ax), flight=flight)

    def open_fullscreen(self, builder, title, index=None, flight=False):
        """A page (index None) or one chart of it (index of its axes) in its own window filling the screen.

        The page is drawn again by builder; for one chart all other charts are removed (plots/single.py).
        flight: single-flight chart - the window gets the button "Whole flight". Esc closes the window.
        """
        import tkinter as tk
        from tkinter import ttk

        fig = builder()
        axes = []
        if index is not None and index < len(fig.axes):
            axes = single_chart(fig, index)
            name = chart_title(axes[0])
            if name:
                title = f"{name} – {title}"
        elif flight:
            axes = [a for a in fig.axes if a.get_subplotspec() is not None]
        win = tk.Toplevel(self.root)
        win.title(tr("{title} – Vollbild (Esc schließt)", title=title))
        win.configure(background=BG)
        self._maximise(win)
        bar = ttk.Frame(win)
        bar.pack(side="top", fill="x")

        def close(*_):
            if win in self.fullscreen:
                self.fullscreen.remove(win)
            win.destroy()

        ttk.Button(bar, text=tr("Schließen (Esc)"), command=close).pack(side="right", padx=6, pady=2)
        is_flight = flight and getattr(fig, "_t", None) is not None and axes
        if is_flight:
            def whole_flight():
                t = fig._t
                axes[0].set_xlim(t[0], t[-1])
                fit_y(axes)
                canvas.draw_idle()
            ttk.Button(bar, text=tr("Ganzer Flug"), command=whole_flight).pack(side="right", padx=6, pady=2)
            fit_y(axes)                               # y range of the zoomed time window, as in the tab
        ttk.Label(bar, text=tr("Maus über einen Datenpunkt: Wert.  Werkzeugleiste unten: zoomen, verschieben, "
                               "speichern."), foreground="#666").pack(side="left", padx=6)
        page_builder = None
        if index is None:
            # whole page: a double-click (or right-click) on one of its charts enlarges that chart on its own,
            # as on the normal page. Single-flight pages keep the time window zoomed in this window.
            def page_builder():
                f = builder()
                if getattr(f, "_t", None) is not None and f.axes and fig.axes:
                    f.axes[0].set_xlim(fig.axes[0].get_xlim())
                return f
        canvas = self.chart_canvas(win, fig, page_builder, title, crosshair=getattr(fig, "_t", None) is not None,
                                   flight=flight, whole_page=False)
        if flight and self.position_source is not None:       # only shown here, a click sets nothing
            canvas._marker = PositionMarker(canvas, canvas._hover)
            canvas._marker.attach(fig, self.position_source())
        canvas.draw()
        win.bind("<Escape>", close)
        win.protocol("WM_DELETE_WINDOW", close)
        win.focus_set()
        self.fullscreen.append(win)
        win._fig = fig                                # for tests
        return win

    def _maximise(self, win):
        import tkinter as tk
        try:
            win.state("zoomed")                       # Windows
        except tk.TclError:
            try:
                win.attributes("-zoomed", True)       # Linux
            except tk.TclError:
                win.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")

    def replace_fig(self, frame, fig):
        """Shows another figure in the canvas already in frame (False if there is none yet).

        Much faster than show_fig because the canvas and the toolbar stay; used by pages that redraw often
        (the statistics, when the filter changes). The builder given to show_fig keeps working.
        """
        canvas = self.page_canvases.get(str(frame))
        if canvas is None or not canvas.get_tk_widget().winfo_exists():
            return False
        widget = canvas.get_tk_widget()
        old_figure = canvas.figure
        canvas._hover.disconnect()
        fig.set_dpi(old_figure.dpi)
        fig.set_size_inches(old_figure.get_size_inches())            # the size the canvas has been resized to
        canvas.figure = fig
        fig.set_canvas(canvas)
        # the mouse handlers are registered with the figure: connect them to the new one (double-click and
        # context menu to enlarge, the coordinates in the toolbar)
        if getattr(canvas, "_on_press", None) is not None:
            canvas.mpl_connect("button_press_event", canvas._on_press)
        toolbar = getattr(canvas, "_toolbar", None)
        if toolbar is not None:
            toolbar._id_drag = canvas.mpl_connect("motion_notify_event", toolbar.mouse_move)
        canvas._hover = Hover(canvas)
        canvas.draw()
        old_figure.clear()
        return widget.winfo_exists()

    def show_fig(self, frame, fig, builder=None, title=""):
        """Shows fig as the chart page in frame (replaces what was there)."""
        for widget in frame.winfo_children():
            widget.destroy()
        canvas = self.chart_canvas(frame, fig, builder, title)
        canvas.draw()
        self.page_canvases[str(frame)] = canvas
