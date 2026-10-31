# -*- coding: utf-8 -*-
"""EthosLogAnalyser - flight and battery analysis for FrSky Ethos log files (CSV).

Layout:
  io/        reading Ethos CSV logs
  analysis/  per-flight and cross-flight analysis, assessment
  report/    text reports
  plots/     charts (matplotlib, usable without the GUI)
  gui/       Tkinter user interface
"""

__version__ = "1.0.0-beta.1"

from .config import Params, CHEM          # noqa: F401
from .analysis.flight import analyse_frame  # noqa: F401
from .analysis.fleet import analyse_flights, Result  # noqa: F401
