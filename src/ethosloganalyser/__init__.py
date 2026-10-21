# -*- coding: utf-8 -*-
"""EthosLogAnalyser - flight and battery analysis for FrSky Ethos log files (CSV).

Layout:
  io/        reading Ethos CSV logs
  analysis/  per-flight and cross-flight analysis, assessment
  report/    text reports
  plots/     charts (matplotlib, usable without the GUI)
  gui/       Tkinter user interface
"""

__version__ = "0.2.0"

from .config import Params, CHEM          # noqa: F401
from .analysis.flight import analyse_file  # noqa: F401
from .analysis.fleet import analyse_folder, Result  # noqa: F401
