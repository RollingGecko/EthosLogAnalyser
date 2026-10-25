# -*- coding: utf-8 -*-
"""Everything the database keeps about one log, worked out from its file content.

Used by the import and by the recalculation after an analysis change. The analysis itself is the existing
one (analysis/flight.py); this module only collects its result, the sensors and the flight detection.
"""

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

from ..analysis.flight import analyse_frame
from ..i18n import Msg
from ..io.ethos_log import _time_seconds, _to_num, read_log_bytes
from . import sensor_roles
from .flight_detection import FlightDetection, detect_flight
from .series_codec import encode_series

# Raise when the per-flight metrics change (analysis/flight.py, sensor roles, flight detection): flights stored
# with an older version are then calculated again from their raw log in the background (reanalysis.py).
ANALYSIS_VERSION = 1

# keys of the analysis result that are stored as columns of the flight table or not at all
_NOT_A_METRIC = ("datei", "pfad", "datum", "_series")

# the parameters of config.Params that change the per-flight result
ANALYSIS_PARAM_NAMES = ("min_flight_s", "active_current_a", "col_voltage", "col_current")

TIME_COLUMN_NAME = "Time"


class UnreadableLog(Exception):
    """The content is not a log that can be read (no CSV, no time column). args[0] is a Msg."""


@dataclass
class SensorSeries:
    """One stored column of a log."""
    position: int
    column_name: str
    role: Optional[str]
    sample_count: int
    encoded: bytes


@dataclass
class AnalysedLog:
    """What is stored about a log apart from its raw content."""
    start_time: datetime
    log_duration_s: float
    detection: FlightDetection
    metrics: Optional[Dict]
    skip_reason: Optional[Msg]
    analysis_params: Dict
    sensors: List[SensorSeries] = field(default_factory=list)


def _plain_value(value):
    """A value of the analysis result as plain JSON (NaN -> None, numpy numbers -> Python numbers)."""
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return None if not math.isfinite(float(value)) else float(value)
    if value is None:
        return None
    return str(value)


def metrics_to_json(metrics):
    """Metrics dict of the analysis -> compact JSON text (None if there are no metrics)."""
    if metrics is None:
        return None
    plain = {key: _plain_value(value) for key, value in metrics.items() if key not in _NOT_A_METRIC}
    return json.dumps(plain, separators=(",", ":"), ensure_ascii=False)


def metrics_from_json(text):
    """Stored metrics -> dict (missing values as NaN, as in the flight table of the analysis)."""
    if text is None:
        return None
    return {key: (np.nan if value is None else value) for key, value in json.loads(text).items()}


def message_to_json(message):
    """A lazily translated message (i18n.Msg) as JSON, so it can be shown in any language later."""
    if message is None:
        return None
    arguments = {key: value if isinstance(value, (int, float, str)) else str(value)
                 for key, value in message.kw.items()}
    return json.dumps({"msgid": message.msgid, "kw": arguments}, ensure_ascii=False)


def message_from_json(text):
    if text is None:
        return None
    data = json.loads(text)
    return Msg(data["msgid"], **data["kw"])


def analysis_params_of(params):
    """The analysis settings that influence the per-flight result, as stored with every flight."""
    return {name: getattr(params, name) for name in ANALYSIS_PARAM_NAMES}


def _sensor_series(frame, time_s, roles):
    """All numeric columns of the log plus the time axis, encoded for storage."""
    sensors = [SensorSeries(position=0, column_name=TIME_COLUMN_NAME, role=sensor_roles.TIME,
                            sample_count=int(np.isfinite(time_s).sum()), encoded=encode_series(time_s))]
    for position, column in enumerate(frame.columns, start=1):
        if sensor_roles.is_date_time_column(column):
            continue
        values = _to_num(frame[column]).to_numpy(dtype=float)
        count = int(np.isfinite(values).sum())
        if count == 0:
            continue                          # empty column (sensor not connected, trailing separator)
        sensors.append(SensorSeries(position=position, column_name=str(column), role=roles.get(column),
                                    sample_count=count, encoded=encode_series(values)))
    return sensors


def analyse_log_content(content, file_name, start_time, params):
    """Reads a log from its content and works out everything that is stored about it.

    file_name gives the analysis its file name; start_time is the start of the log (from the file name).
    Raises UnreadableLog if the content cannot be read as an Ethos log.
    """
    try:
        frame = read_log_bytes(content)
    except Exception as error:                # pandas raises many different errors for broken files
        raise UnreadableLog(Msg("Lesefehler: {err}", err=str(error))) from error
    time_s = _time_seconds(frame)
    if time_s is None:
        raise UnreadableLog(Msg("Zeitspalte nicht erkannt"))
    time_s = np.asarray(time_s, dtype=float)

    try:
        metrics, reason = analyse_frame(frame, file_name, params, start_time=start_time)
    except Exception as error:                # an analysis error must not stop the import of the others
        metrics, reason = None, Msg("Analysefehler: {err}", err=str(error))
    if metrics is not None:
        reason = None

    roles = sensor_roles.assign_roles(frame, params)
    detection = detect_flight(frame, time_s, roles, metrics, params)
    finite_time = time_s[np.isfinite(time_s)]
    log_duration = float(finite_time.max() - finite_time.min()) if len(finite_time) else 0.0
    return AnalysedLog(start_time=start_time, log_duration_s=log_duration, detection=detection,
                       metrics=metrics, skip_reason=reason, analysis_params=analysis_params_of(params),
                       sensors=_sensor_series(frame, time_s, roles))
