# -*- coding: utf-8 -*-
"""A selection field with several values: a button with a short text that opens a list of check buttons.

``selection_summary`` and ``shortened`` work out the short text and need no window, so they are tested directly.
``MultiSelect`` is the Tk widget: the button shows the short text ("alle", "2024, 2025", "3 von 5"), a click opens
a popup with one check button per value plus "Alle auswählen" and "Alle abwählen". The popup stays open while the
user ticks values and closes on a click outside of it or on Esc; Tab moves between the check buttons and the
space bar ticks one.

A selection is ``None`` (every value, no restriction) or a collection of the chosen values - the same convention
as the fields of ``analysis.periods.FlightFilter``.
"""

from ..i18n import tr

ARROW = " ▼"                      # marks the button as a drop-down; the same glyph as the sort mark of the tables
ELLIPSIS = "…"


def shortened(text, fits):
    """The text cut at the end (with an ellipsis) until ``fits(text)`` is true; unchanged if it fits already."""
    if fits(text):
        return text
    cut = text
    while cut and not fits(cut + ELLIPSIS):
        cut = cut[:-1]
    return cut + ELLIPSIS


def selection_summary(selection, options, fits=lambda text: True):
    """Short text for a selection. ``options`` is a list of (value, label) in display order; ``fits(text)`` says
    whether a text has room on the button.

    Every value chosen (or ``None``) is "alle", nothing chosen is "keine". Otherwise the labels of the chosen
    values joined by commas, if that fits; else "k von n"; a single chosen value that is too long is cut instead.
    """
    chosen = [label for value, label in options if selection is None or value in selection]
    if selection is None or (options and len(chosen) == len(options)):
        return tr("alle")
    if not chosen:
        return tr("keine")
    joined = ", ".join(chosen)
    if fits(joined):
        return joined
    if len(chosen) == 1:
        return shortened(joined, fits)
    return tr("{count} von {total}", count=len(chosen), total=len(options))


class MultiSelect:
    """Button with the short text of a selection and a popup of check buttons to change it.

    ``on_change(chosen)`` is called with the set of ticked values whenever the user changes the selection; the
    owner stores it and calls ``show`` again with what is now valid (the widget never keeps a state of its own
    beyond what it was told to show).
    """

    def __init__(self, parent, width, on_change):
        from tkinter import ttk

        self.on_change = on_change
        self.options = []                    # [(value, label)] in display order
        self.selection = None                # what is shown: None = all values
        self.summary = ""                    # the short text on the button (without the arrow)
        self.popup = None                    # the open popup window, if any
        self._variables = {}                 # value -> BooleanVar of its check button
        self._checkbuttons = {}              # value -> ttk.Checkbutton
        self._has_grab = False
        self._closer = None                  # id of the binding that closes the popup when another one opens
        self._font = None                    # the font of the button (see _button_font)
        self._font_spec = None
        self._width = width                  # button width in characters of the default font
        self.button = ttk.Button(parent, width=width + len(ARROW), command=self.toggle_popup)
        self.button.bind("<Destroy>", lambda event: self.close() if event.widget is self.button else None)

    def pack(self, **options):
        self.button.pack(**options)

    # ---------------- showing ----------------
    def show(self, options, selection):
        """Shows the given values and selection. A popup that is open follows the selection; if the values
        themselves changed it is closed."""
        options = list(options)
        if options != self.options:
            self.close()
        self.options, self.selection = options, selection
        self.summary = selection_summary(selection, options, self._fits)
        self.button.configure(text=self.summary + ARROW)
        for value, variable in self._variables.items():
            variable.set(selection is None or value in selection)

    def _button_font(self):
        """The font the style gives to buttons (it follows the display scaling); looked up again whenever the
        style changed it."""
        from tkinter import font, ttk
        spec = str(ttk.Style(self.button).lookup("TButton", "font") or "TkDefaultFont")
        if spec != self._font_spec:
            self._font, self._font_spec = font.Font(root=self.button, font=spec), spec
        return self._font

    def _fits(self, text):
        """True if the text, with the arrow, fits into the width of the button. The width of a button is counted
        in digits, but the letters of a name are wider than that, so the text is measured in the font."""
        button_font = self._button_font()
        return button_font.measure(text + ARROW) <= button_font.measure("0") * (self._width + len(ARROW))

    # ---------------- popup ----------------
    @property
    def is_open(self):
        return self.popup is not None

    def toggle_popup(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def open(self):
        """Opens the list of check buttons below the button (and closes the popup of another field)."""
        import tkinter as tk
        from tkinter import ttk

        if self.is_open or not self.options:
            return
        self.button.winfo_toplevel().event_generate("<<CloseSelectPopups>>")     # at most one popup at a time
        popup = self.popup = tk.Toplevel(self.button)
        popup.wm_overrideredirect(True)
        popup.bind("<Escape>", lambda _event: self.close(refocus=True))
        popup.bind("<ButtonPress>", self._pressed)
        outer = self.button.winfo_toplevel()
        self._closer = outer.bind("<<CloseSelectPopups>>", lambda _event: self.close(), add="+")

        frame = ttk.Frame(popup, relief="solid", borderwidth=1, padding=4)
        frame.pack(fill="both", expand=True)
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(0, 4))
        self.select_all_button = ttk.Button(buttons, text=tr("Alle auswählen"), command=lambda: self._set_all(True))
        self.select_all_button.pack(side="left", padx=(0, 4))
        self.select_none_button = ttk.Button(buttons, text=tr("Alle abwählen"), command=lambda: self._set_all(False))
        self.select_none_button.pack(side="left")
        self._variables, self._checkbuttons = {}, {}
        for value, label in self.options:
            variable = tk.BooleanVar(master=popup, value=self.selection is None or value in self.selection)
            check = ttk.Checkbutton(frame, text=label, variable=variable, command=self._ticked)
            check.pack(anchor="w")
            self._variables[value], self._checkbuttons[value] = variable, check

        self._place(popup)
        self._has_grab = self._grab(popup)
        if not self._has_grab:                          # no grab (rare): close when the focus goes elsewhere
            popup.bind("<FocusOut>", lambda _event: popup.after_idle(self._close_if_focus_left))
        first = self._checkbuttons[self.options[0][0]]
        first.focus_set()

    def _place(self, popup):
        """Puts the popup below the button, as wide as the button at least, and inside the screen."""
        popup.update_idletasks()
        width = max(popup.winfo_reqwidth(), self.button.winfo_width())
        height = popup.winfo_reqheight()
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height()
        x = max(0, min(x, popup.winfo_screenwidth() - width))
        if y + height > popup.winfo_screenheight():
            y = max(0, self.button.winfo_rooty() - height)          # above the button if there is no room below
        popup.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def _grab(popup):
        """Directs the mouse to the popup so a click outside of it can be seen; False if that is not possible."""
        import tkinter as tk
        try:
            popup.update()
            popup.focus_force()
            popup.grab_set()
            return True
        except tk.TclError:
            return False

    def _pressed(self, event):
        """A click that lands outside of the popup (the grab delivers it to the popup) closes it."""
        popup = self.popup
        if popup is None:
            return
        inside = (popup.winfo_rootx() <= event.x_root < popup.winfo_rootx() + popup.winfo_width()
                  and popup.winfo_rooty() <= event.y_root < popup.winfo_rooty() + popup.winfo_height())
        if not inside:
            self.close()

    def _close_if_focus_left(self):
        popup = self.popup
        if popup is None:
            return
        focused = popup.focus_get()
        if focused is None or not str(focused).startswith(str(popup)):
            self.close()

    def close(self, refocus=False):
        """Closes the popup (if open)."""
        popup, self.popup = self.popup, None
        if popup is None:
            return
        self._variables, self._checkbuttons = {}, {}
        try:
            self.button.winfo_toplevel().unbind("<<CloseSelectPopups>>", self._closer)
        except Exception:                               # the window is already gone
            pass
        try:
            popup.grab_release()
            popup.destroy()
        except Exception:
            pass
        if refocus:
            try:
                self.button.focus_set()
            except Exception:
                pass

    # ---------------- changes made by the user ----------------
    def ticked(self):
        """The values that are ticked in the open popup."""
        return frozenset(value for value, variable in self._variables.items() if variable.get())

    def _ticked(self):
        """A check button was clicked: reports the ticked values."""
        self.on_change(self.ticked())

    def _set_all(self, ticked):
        """"Alle auswählen" / "Alle abwählen"."""
        for variable in self._variables.values():
            variable.set(ticked)
        self._ticked()

    def tick(self, value):
        """Clicks the check button of a value (what the user does with the mouse or the space bar)."""
        self._checkbuttons[value].invoke()
