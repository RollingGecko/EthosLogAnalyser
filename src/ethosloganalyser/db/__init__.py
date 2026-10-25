# -*- coding: utf-8 -*-
"""Flight database (SQLite file): import of Ethos logs with duplicate detection, flights, metrics and
time series. See docs/database.md for the schema and the decisions behind it.

Modules:
  schema            tables and schema version
  database          open, create, save as, empty
  importer          import of files and folders, import report
  log_analysis      what is stored about a log (metrics, sensors, flight detection)
  flight_store      writing and reading logs, flights and time series
  series_codec      compact lossless time series (scaled integers, delta-coded, zlib)
  sensor_roles      role of each log column (battery voltage, altitude, ...)
  flight_detection  is a log a flight? (motor, altitude, vario or radio link)
  reanalysis        calculating flights again after an analysis change
  signal_metrics    values from the time series of every log (receiver voltage) for the anomaly rules
  annotations       notes and anomalies of flights, acknowledgements, recalculation of the anomalies
"""

from .database import DatabaseError, DatabaseStats, FlightDatabase  # noqa: F401
from .importer import ImportReport, import_paths  # noqa: F401
