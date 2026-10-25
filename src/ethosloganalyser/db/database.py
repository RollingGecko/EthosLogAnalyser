# -*- coding: utf-8 -*-
"""Opening, creating, copying and emptying a flight database file."""

import os
import sqlite3
from dataclasses import dataclass

from . import schema


class DatabaseError(Exception):
    """The file cannot be used as a flight database (not SQLite, another program's database, newer version)."""


@dataclass
class DatabaseStats:
    """What the database holds, for the overview on the page Data & settings."""
    log_count: int
    flight_count: int
    non_flight_count: int
    aircraft_count: int
    size_bytes: int


def _connect(path):
    # check_same_thread stays on: every thread (e.g. the background import) opens its own connection
    connection = sqlite3.connect(path, timeout=30.0)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _pragma(connection, name):
    return connection.execute(f"PRAGMA {name}").fetchone()[0]


def _has_tables(connection):
    return connection.execute("SELECT count(*) FROM sqlite_master WHERE type = 'table'").fetchone()[0] > 0


class FlightDatabase:
    """A flight database file. Every change is written at once (SQLite); there is no separate "save".

    Opening a file that does not exist creates a new, empty database.
    """

    def __init__(self, path):
        self.path = os.path.abspath(path)
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        try:
            self.connection = _connect(self.path)
            self._prepare()
        except sqlite3.DatabaseError as error:
            self._close_quietly()
            raise DatabaseError(str(error)) from error
        except DatabaseError:
            self._close_quietly()
            raise

    def _prepare(self):
        """Creates the schema in a new file, checks and upgrades an existing one."""
        connection = self.connection
        if not _has_tables(connection):
            schema.create_schema(connection)
            return
        if _pragma(connection, "application_id") != schema.APPLICATION_ID:
            raise DatabaseError("not an EthosLogAnalyser flight database")
        version = _pragma(connection, "user_version")
        if version > schema.SCHEMA_VERSION:
            raise DatabaseError(f"database schema version {version} is newer than this program "
                                f"({schema.SCHEMA_VERSION})")
        if version < schema.SCHEMA_VERSION:
            schema.migrate(connection, version)

    def _close_quietly(self):
        connection = getattr(self, "connection", None)
        if connection is not None:
            connection.close()
            self.connection = None

    @classmethod
    def create_new(cls, path):
        """Creates a new, empty database at path; an existing file there is replaced."""
        if os.path.exists(path):
            os.remove(path)
        return cls(path)

    def close(self):
        """Closes the connection (all changes are already stored)."""
        self._close_quietly()

    def save_as(self, target_path):
        """Writes a copy of the database to target_path. This database stays the open one."""
        target_path = os.path.abspath(target_path)
        if target_path == self.path:
            return
        if os.path.exists(target_path):
            os.remove(target_path)
        target = sqlite3.connect(target_path)
        try:
            self.connection.backup(target)
        finally:
            target.close()

    def clear(self):
        """Deletes all imported logs and flights and shrinks the file (VACUUM). The tables stay."""
        with self.connection:
            for table in ("series", "sensor", "flight", "log_raw", "log_file", "aircraft"):
                self.connection.execute(f"DELETE FROM {table}")
        self.connection.execute("VACUUM")

    def stats(self):
        """Number of logs, flights and aircraft, and the file size."""
        log_count, flight_count, aircraft_count = self.connection.execute(
            "SELECT (SELECT count(*) FROM log_file),"
            "       (SELECT count(*) FROM flight WHERE coalesce(is_flight_manual, is_flight) = 1),"
            "       (SELECT count(DISTINCT aircraft_id) FROM flight)").fetchone()
        size = os.path.getsize(self.path) if os.path.exists(self.path) else 0
        return DatabaseStats(log_count=log_count, flight_count=flight_count,
                             non_flight_count=log_count - flight_count, aircraft_count=aircraft_count,
                             size_bytes=size)
