# -*- coding: utf-8 -*-
"""Flights grouped for the logbook tree ("Group by"): by time or by aircraft.

* ``GROUP_BY_TIME``: year -> month -> aircraft
* ``GROUP_BY_AIRCRAFT``: aircraft -> year -> month

Every node has the number of flights and the summed flight time below it. The ``selector`` of a node says
which flights belong to it (``select_flights``), so a click on a row of the tree can filter the flight list.
The input is a flight table with the columns ``aircraft``, ``datum`` and ``dauer_s``.
"""

from dataclasses import dataclass, field
from typing import List

import pandas as pd

GROUP_BY_TIME = "time"
GROUP_BY_AIRCRAFT = "aircraft"

YEAR, MONTH, AIRCRAFT = "year", "month", "aircraft"
LEVELS = {
    GROUP_BY_TIME: (YEAR, MONTH, AIRCRAFT),
    GROUP_BY_AIRCRAFT: (AIRCRAFT, YEAR, MONTH),
}


@dataclass
class GroupNode:
    """One row of the tree."""
    level: str                                  # YEAR, MONTH or AIRCRAFT
    value: object                               # the year, the month number or the aircraft name
    selector: dict                              # {level: value} of this node and all its parents
    n_flights: int = 0
    duration_s: float = 0.0
    children: List["GroupNode"] = field(default_factory=list)


def _with_period_columns(flights):
    """The flights with the helper columns year and month (a flight without a date has none)."""
    grouped = pd.DataFrame({AIRCRAFT: flights["aircraft"].to_numpy(),
                            YEAR: flights["datum"].dt.year.to_numpy(),
                            MONTH: flights["datum"].dt.month.to_numpy(),
                            "duration_s": pd.to_numeric(flights["dauer_s"], errors="coerce").to_numpy()})
    return grouped.dropna(subset=[YEAR, MONTH])


def _build_level(rows, levels, parent_selector):
    """Nodes of the first of the levels for these rows, with the deeper levels as children."""
    level, deeper = levels[0], levels[1:]
    nodes = []
    for value, part in rows.groupby(level, sort=True):
        value = int(value) if level in (YEAR, MONTH) else value
        node = GroupNode(level=level, value=value, selector={**parent_selector, level: value},
                         n_flights=len(part), duration_s=float(part["duration_s"].sum()))
        if deeper:
            node.children = _build_level(part, deeper, node.selector)
        nodes.append(node)
    return nodes


def build_groups(flights, group_by):
    """The tree of the flights for the given grouping: a list of top-level nodes (empty without flights)."""
    if flights.empty:
        return []
    return _build_level(_with_period_columns(flights), LEVELS[group_by], {})


def all_selectors(nodes):
    """The selectors of all rows of a tree (all levels)."""
    selectors = []
    for node in nodes:
        selectors.append(node.selector)
        selectors.extend(all_selectors(node.children))
    return selectors


def select_flights(flights, selector):
    """The flights that belong to a node (a selector as in ``GroupNode.selector``); everything for ``None``."""
    if not selector:
        return flights
    mask = pd.Series(True, index=flights.index)
    if AIRCRAFT in selector:
        mask &= flights["aircraft"] == selector[AIRCRAFT]
    if YEAR in selector:
        mask &= flights["datum"].dt.year == selector[YEAR]
    if MONTH in selector:
        mask &= flights["datum"].dt.month == selector[MONTH]
    return flights[mask]
