# -*- coding: utf-8 -*-
"""Flight recorder: playing a flight back from the time series stored in the flight database.

Everything in this package is plain Python and numpy (no Tkinter), so it is tested without a window:

  flight_track  the stored series of one log, "last value holds until the next row", end of the flight
  playback      the playback clock: position from the wall clock, speed steps, seek, row steps
  layout        where the instruments and the timeline go for a given window size
  gauges        geometry of the artificial horizon
  dials         geometry of the round gauges and bars, nice scales
  readouts      what the gauges show: scales per flight, values as text, gauges a log has data for

The drawing on the Tk canvas lives in gui/recorder_page.py, gui/recorder_timeline.py,
gui/recorder_instruments.py and gui/recorder_dials.py.
"""
