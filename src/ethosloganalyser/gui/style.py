# -*- coding: utf-8 -*-
"""Colours and ttk styles of the user interface."""

from .table_fit import row_height

ACCENT = "#1f5fa8"


BG = "#f4f6f9"


def _setup_style(root):
    from tkinter import ttk, font as tkfont
    st = ttk.Style(root)
    st.theme_use("clam")
    base = tkfont.nametofont("TkDefaultFont")
    base.configure(size=10)
    fam = base.actual("family")
    st.configure(".", background=BG, font=(fam, 10))
    st.configure("TFrame", background=BG)
    st.configure("TLabel", background=BG)
    st.configure("TLabelframe", background=BG, bordercolor="#c9d1dc")
    st.configure("TLabelframe.Label", background=BG, foreground=ACCENT, font=(fam, 10, "bold"))
    st.configure("Status.TLabel", background="#e3e9f2", foreground="#1f3b73", padding=(10, 4), font=(fam, 9))
    st.configure("Readout.TLabel", background="#ffffff", foreground="#222", padding=(8, 3), font=(fam, 9))
    # tabs: clearly separated, active tab coloured and bold
    st.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(8, 6, 8, 0))
    st.configure("TNotebook.Tab", padding=(16, 7), background="#dde3ec", foreground="#3a4656",
                 bordercolor="#b7c2d1", lightcolor="#dde3ec", font=(fam, 10))
    st.map("TNotebook.Tab",
           background=[("selected", ACCENT), ("active", "#c5d3e8")],
           foreground=[("selected", "#ffffff")],
           lightcolor=[("selected", ACCENT)],
           font=[("selected", (fam, 10, "bold"))],
           expand=[("selected", (2, 3, 2, 0))])
    # pages inside an area (e.g. Statistics): smaller, lighter tabs, so the two levels can be told apart
    st.configure("Pages.TNotebook", background=BG, borderwidth=0, tabmargins=(4, 4, 4, 0))
    st.configure("Pages.TNotebook.Tab", padding=(12, 4), background="#e8edf4", foreground="#3a4656",
                 bordercolor="#c9d1dc", lightcolor="#e8edf4", font=(fam, 9))
    st.map("Pages.TNotebook.Tab",
           background=[("selected", "#ffffff"), ("active", "#d5dfec")],
           foreground=[("selected", ACCENT)],
           lightcolor=[("selected", "#ffffff")],
           font=[("selected", (fam, 9, "bold"))])
    st.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", padding=(14, 6), font=(fam, 10, "bold"))
    st.map("Accent.TButton", background=[("active", "#174a85"), ("disabled", "#9fb3cc")])
    st.configure("TButton", padding=(10, 4))
    st.configure("View.TRadiobutton", padding=(10, 4), background="#dde3ec", indicatorsize=0)
    st.map("View.TRadiobutton", background=[("selected", ACCENT), ("active", "#c5d3e8")],
           foreground=[("selected", "#ffffff")])
    st.configure("Treeview", rowheight=row_height(base.metrics("linespace")))    # follows the font and the scaling
    st.configure("Treeview.Heading", font=(fam, 9, "bold"))
    return fam
