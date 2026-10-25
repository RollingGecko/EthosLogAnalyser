# -*- coding: utf-8 -*-
"""Import of log files and folders into the flight database.

Duplicates: a file whose content (SHA-256) is already in the database is skipped, whatever its name or
folder. A file with other content but the same aircraft and start time as a stored log is imported and
marked as a possible duplicate. The files themselves are only read, never changed or deleted.
"""

import glob
import hashlib
import os
from dataclasses import dataclass, field
from typing import List, Optional

from ..i18n import Msg
from ..io.ethos_log import _file_datetime, model_from_filename
from . import flight_preparation, flight_store
from .log_analysis import UnreadableLog, analyse_log_content

NEW = "new"
DUPLICATE = "duplicate"
SUSPICIOUS = "suspicious"
UNREADABLE = "unreadable"


@dataclass
class ImportEntry:
    """One file of an import and what happened to it."""
    file_name: str
    path: str
    outcome: str                       # NEW, DUPLICATE, SUSPICIOUS or UNREADABLE
    other_file: str = ""               # DUPLICATE/SUSPICIOUS: the stored log it matches
    reason: Optional[Msg] = None       # UNREADABLE: why
    is_flight: bool = False            # NEW/SUSPICIOUS: detected as a flight


@dataclass
class ImportReport:
    """Result of an import: every file with its outcome."""
    entries: List[ImportEntry] = field(default_factory=list)
    cancelled: bool = False

    def with_outcome(self, outcome):
        return [entry for entry in self.entries if entry.outcome == outcome]

    def count(self, outcome):
        return len(self.with_outcome(outcome))

    @property
    def flight_count(self):
        """Imported logs (new or suspicious) that are flights."""
        return sum(1 for entry in self.entries if entry.outcome in (NEW, SUSPICIOUS) and entry.is_flight)


def find_logs(folder):
    """All CSV files in folder and its subfolders, sorted."""
    return sorted(glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True))


def collect_log_files(paths):
    """The CSV files to import: files as given, folders with all their subfolders. Sorted, without repeats."""
    files = []
    for path in paths:
        if os.path.isdir(path):
            files.extend(find_logs(path))
        else:
            files.append(path)
    seen, unique = set(), []
    for path in files:
        key = os.path.normcase(os.path.abspath(path))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def import_file(database, path, params):
    """Imports one log file and returns its ImportEntry."""
    file_name = os.path.basename(path)
    try:
        with open(path, "rb") as handle:
            content = handle.read()
    except OSError as error:
        return ImportEntry(file_name, path, UNREADABLE, reason=Msg("Lesefehler: {err}", err=str(error)))

    connection = database.connection
    sha256 = hashlib.sha256(content).hexdigest()
    stored = flight_store.find_log_by_hash(connection, sha256)
    if stored is not None:
        return ImportEntry(file_name, path, DUPLICATE, other_file=stored[1])

    start_time = _file_datetime(path)
    try:
        analysed = analyse_log_content(content, file_name, start_time, params)
    except UnreadableLog as error:
        return ImportEntry(file_name, path, UNREADABLE, reason=error.args[0])

    model = model_from_filename(path)
    with connection:                      # one transaction per file: a broken import leaves nothing behind
        aircraft = flight_store.aircraft_id(connection, model)
        same_start = flight_store.find_flight_at(connection, aircraft, start_time)
        log_id = flight_store.insert_log(connection, sha256=sha256, original_name=file_name,
                                         source_path=os.path.abspath(path), content=content, model=model,
                                         analysed=analysed, possible_duplicate=same_start is not None)
        flight_preparation.store_for_new_analysis(connection, log_id, file_name, analysed)
    outcome = SUSPICIOUS if same_start is not None else NEW
    return ImportEntry(file_name, path, outcome, other_file=same_start or "",
                       is_flight=analysed.detection.is_flight)


def import_paths(database, paths, params, progress=None, should_cancel=None):
    """Imports files and folders (with subfolders).

    progress(done, total, file_name) is called after every file; should_cancel() is checked before every
    file - files imported until then stay in the database.
    """
    files = collect_log_files(paths)
    report = ImportReport()
    for done, path in enumerate(files, start=1):
        if should_cancel is not None and should_cancel():
            report.cancelled = True
            break
        report.entries.append(import_file(database, path, params))
        if progress is not None:
            progress(done, len(files), os.path.basename(path))
    return report
