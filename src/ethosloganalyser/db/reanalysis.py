# -*- coding: utf-8 -*-
"""Calculating flights again after the analysis has changed (log_analysis.ANALYSIS_VERSION).

Every flight stores the analysis version it was calculated with. Flights with an older version are analysed
again from their stored raw log - in the background, without the original files - with the analysis
settings they were imported with. Their prepared values for the statistics are worked out again with them
(flight_preparation.py).
"""

import dataclasses
import json

from . import flight_preparation, flight_store
from .log_analysis import ANALYSIS_VERSION, UnreadableLog, analyse_log_content


def outdated_log_ids(connection):
    """Log ids whose flight was calculated with an older analysis version."""
    return [row[0] for row in connection.execute(
        "SELECT log_id FROM flight WHERE analysis_version < ? ORDER BY start_time", (ANALYSIS_VERSION,))]


def reanalyse_outdated(database, params, progress=None, should_cancel=None):
    """Analyses all outdated flights again. Returns the number of flights updated.

    params supplies the settings that are not stored with a flight (config.Params).

    progress(done, total) is called after every flight; should_cancel() is checked before every flight.
    """
    connection = database.connection
    log_ids = outdated_log_ids(connection)
    updated = 0
    for done, log_id in enumerate(log_ids, start=1):
        if should_cancel is not None and should_cancel():
            break
        file_name, start_text, stored_params = connection.execute(
            "SELECT log_file.original_name, flight.start_time, flight.analysis_params FROM log_file "
            "JOIN flight ON flight.log_id = log_file.id WHERE log_file.id = ?", (log_id,)).fetchone()
        flight_params = dataclasses.replace(params, **json.loads(stored_params))
        try:
            analysed = analyse_log_content(flight_store.raw_content(connection, log_id), file_name,
                                           flight_store.parse_start_time(start_text), flight_params)
        except UnreadableLog:
            continue                      # was readable at import; leave it as it is
        with connection:
            flight_store.replace_analysis(connection, log_id, analysed)
            flight_preparation.store_for_new_analysis(connection, log_id, file_name, analysed)
        updated += 1
        if progress is not None:
            progress(done, len(log_ids))
    return updated
