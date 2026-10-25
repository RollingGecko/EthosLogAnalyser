# -*- coding: utf-8 -*-
"""Tables of the flight database and its schema version.

The database is one SQLite file. It is recognised by ``PRAGMA application_id`` and versioned with
``PRAGMA user_version``; a later schema change adds a step to ``MIGRATIONS``. See docs/database.md.
"""

# "ELA1" - marks an SQLite file as an EthosLogAnalyser flight database
APPLICATION_ID = 0x454C4131

SCHEMA_VERSION = 1

# One statement per entry, executed in this order when a new database is created.
CREATE_STATEMENTS = (
    # an aircraft = a model name taken from the log file name ("" = no model part in the name)
    """
    CREATE TABLE aircraft (
        id   INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )
    """,
    # one imported log file; the same content (SHA-256) is stored only once
    """
    CREATE TABLE log_file (
        id            INTEGER PRIMARY KEY,
        sha256        TEXT NOT NULL UNIQUE,
        original_name TEXT NOT NULL,
        source_path   TEXT NOT NULL,
        size_bytes    INTEGER NOT NULL,
        imported_at   TEXT NOT NULL
    )
    """,
    # the raw log, lzma-compressed; kept apart so that queries on log_file never touch the large blobs
    """
    CREATE TABLE log_raw (
        log_id INTEGER PRIMARY KEY REFERENCES log_file(id) ON DELETE CASCADE,
        data   BLOB NOT NULL
    )
    """,
    # one log file = one flight (or a log that is not a flight, is_flight = 0)
    """
    CREATE TABLE flight (
        id                 INTEGER PRIMARY KEY,
        log_id             INTEGER NOT NULL UNIQUE REFERENCES log_file(id) ON DELETE CASCADE,
        aircraft_id        INTEGER NOT NULL REFERENCES aircraft(id),
        start_time         TEXT NOT NULL,
        duration_s         REAL,
        log_duration_s     REAL,
        is_flight          INTEGER NOT NULL,
        is_flight_manual   INTEGER,
        detection_method   TEXT NOT NULL,
        possible_duplicate INTEGER NOT NULL DEFAULT 0,
        analysis_version   INTEGER NOT NULL,
        analysis_params    TEXT NOT NULL,
        metrics            TEXT,
        skip_reason        TEXT
    )
    """,
    "CREATE INDEX flight_by_aircraft_and_time ON flight (aircraft_id, start_time)",
    "CREATE INDEX flight_by_time ON flight (start_time)",
    # the sensors (columns) of a log with their role; the time axis is a sensor with role "time"
    """
    CREATE TABLE sensor (
        id           INTEGER PRIMARY KEY,
        log_id       INTEGER NOT NULL REFERENCES log_file(id) ON DELETE CASCADE,
        position     INTEGER NOT NULL,
        column_name  TEXT NOT NULL,
        role         TEXT,
        sample_count INTEGER NOT NULL
    )
    """,
    "CREATE INDEX sensor_by_log ON sensor (log_id)",
    # the time series of one sensor, encoded by series_codec (scaled integers, delta-coded, zlib)
    """
    CREATE TABLE series (
        sensor_id INTEGER PRIMARY KEY REFERENCES sensor(id) ON DELETE CASCADE,
        data      BLOB NOT NULL
    )
    """,
)

# MIGRATIONS[n] upgrades a database from schema version n to n + 1 (list of SQL statements).
MIGRATIONS = {}


def create_schema(connection):
    """Creates all tables in an empty database and marks it as a flight database of the current version."""
    with connection:
        for statement in CREATE_STATEMENTS:
            connection.execute(statement)
        connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def migrate(connection, from_version):
    """Brings a database of an older schema version up to SCHEMA_VERSION."""
    with connection:
        for version in range(from_version, SCHEMA_VERSION):
            for statement in MIGRATIONS[version]:
                connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
