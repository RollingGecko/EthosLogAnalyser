# -*- coding: utf-8 -*-
"""EthosLogAnalyser - Flug- & Akku-Analyse für FrSky-Ethos-Logfiles (CSV).

Aufbau:
  io/        Einlesen der Ethos-CSV-Logs
  analysis/  Auswertung je Flug und über alle Flüge, Bewertung
  report/    Textberichte
  plots/     Diagramme (matplotlib, ohne Oberfläche nutzbar)
  gui/       Tkinter-Oberfläche
"""

__version__ = "0.2.0"

from .config import Params, CHEM          # noqa: F401
from .analysis.flight import analyse_file  # noqa: F401
from .analysis.fleet import analyse_folder, Result  # noqa: F401
