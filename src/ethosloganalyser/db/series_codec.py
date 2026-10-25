# -*- coding: utf-8 -*-
"""Compact, lossless storage of one sensor time series.

Ethos writes values with a few decimals (e.g. 54.63 V). Such values are stored as integers scaled by
10^decimals; the differences between neighbouring values are small and compress very well with zlib.
Missing values (NaN: Ethos logs every sensor in its own rows) are kept in a bit mask. Values that cannot be
written with at most MAX_DECIMALS decimals are stored as plain float64 instead, so nothing is ever rounded.

Blob layout: header (struct HEADER) followed by the zlib-compressed payload
``[packed missing-value mask if any value is missing] + [differences or float64 values]``.
"""

import struct
import zlib

import numpy as np

FORMAT_VERSION = 1
MAX_DECIMALS = 6
FLOAT_STORAGE = -1          # "decimals" value of a series stored as float64

# format version, decimals (or FLOAT_STORAGE), bytes per stored difference, total count, valid count
HEADER = struct.Struct("<BbBII")

_INTEGER_TYPES = (np.int8, np.int16, np.int32, np.int64)


class SeriesFormatError(ValueError):
    """The blob is not a series written by this module."""


def decimals_needed(values):
    """Smallest number of decimals (0..MAX_DECIMALS) that represents all finite values exactly, or
    FLOAT_STORAGE if there is none (or the scaled values would be too large for exact integers)."""
    for decimals in range(MAX_DECIMALS + 1):
        scale = 10.0 ** decimals
        scaled = np.round(values * scale)
        if np.any(np.abs(scaled) >= 2.0 ** 53):
            return FLOAT_STORAGE
        if np.array_equal(scaled / scale, values):
            return decimals
    return FLOAT_STORAGE


def _smallest_integer_type(differences):
    if len(differences) == 0:
        return np.int8
    largest = int(np.max(np.abs(differences)))
    for integer_type in _INTEGER_TYPES:
        if largest <= np.iinfo(integer_type).max:
            return integer_type
    return np.int64


def encode_series(values):
    """Encodes a 1-D array of floats (NaN = missing) into a compact blob."""
    values = np.asarray(values, dtype=float)
    missing = np.isnan(values)
    present = values[~missing]
    if np.all(np.isfinite(present)):
        decimals = decimals_needed(present)
    else:                                   # +-inf cannot be scaled
        decimals = FLOAT_STORAGE

    payload = np.packbits(missing).tobytes() if missing.any() else b""
    if decimals == FLOAT_STORAGE:
        item_size = 8
        payload += present.astype("<f8").tobytes()
    else:
        integers = np.round(present * 10.0 ** decimals).astype(np.int64)
        differences = np.diff(integers, prepend=np.int64(0))
        integer_type = _smallest_integer_type(differences)
        item_size = np.dtype(integer_type).itemsize
        payload += differences.astype(np.dtype(integer_type).newbyteorder("<")).tobytes()

    header = HEADER.pack(FORMAT_VERSION, decimals, item_size, len(values), len(present))
    return header + zlib.compress(payload, 6)


def decode_series(blob):
    """Turns a blob from encode_series back into the float array (NaN where a value was missing)."""
    if len(blob) < HEADER.size:
        raise SeriesFormatError("blob too short")
    version, decimals, item_size, total, valid = HEADER.unpack_from(blob)
    if version != FORMAT_VERSION:
        raise SeriesFormatError(f"unknown series format {version}")
    payload = zlib.decompress(blob[HEADER.size:])

    mask_bytes = 0
    missing = None
    if valid < total:
        mask_bytes = (total + 7) // 8
        missing = np.unpackbits(np.frombuffer(payload[:mask_bytes], dtype=np.uint8), count=total).astype(bool)
    data = payload[mask_bytes:]

    if decimals == FLOAT_STORAGE:
        present = np.frombuffer(data, dtype="<f8", count=valid).astype(float)
    else:
        integer_type = {1: np.int8, 2: np.int16, 4: np.int32, 8: np.int64}[item_size]
        differences = np.frombuffer(data, dtype=np.dtype(integer_type).newbyteorder("<"), count=valid)
        present = np.cumsum(differences.astype(np.int64)) / 10.0 ** decimals

    if missing is None:
        return present
    values = np.full(total, np.nan)
    values[~missing] = present
    return values
