# -*- coding: utf-8 -*-
"""Detection of measurement errors (physically impossible values) across all flights.

A data error is not a finding about the battery: the affected values are taken out of trends, start values and
limit warnings and reported as a data-quality hint instead (e.g. "rest voltage impossible" instead of
"deep discharge"). The rules only use values that cannot occur with working sensors.
"""

import numpy as np

from ..i18n import Msg, N_
from ..utils import _col


# data-error codes (column "Datenfehler", meta["quality"]) -> user-facing label
QUALITY_LABELS = {
    "current_stuck": N_("Stromsensor hängt am Anschlag"),
    "voltage_dropout": N_("Spannungsausfall"),
    "rest_voltage_invalid": N_("Ruhespannung nach der Landung unmöglich"),
    "vfr_invalid": N_("VFR außerhalb 0–100 %"),
    "ri_implausible": N_("Innenwiderstand unplausibel"),
}


# explanation and consequence per code (shown in the summary)
QUALITY_HINTS = {
    "current_stuck": N_("Der Strom liegt fast den ganzen Flug am Höchstwert (Sensor übersteuert oder falsch "
                        "skaliert). Entnommene Ladung, Ladezustand, Kapazität, Innenwiderstand und Timer dieser "
                        "Flüge werden nicht verwendet."),
    "voltage_dropout": N_("Die Spannung fällt im Flug auf unter {limit:.1f} V/Zelle (Sensor- oder Kabelausfall, "
                          "kein Spannungseinbruch des Akkus). Spannungs- und Akkuwerte dieser Flüge werden nicht "
                          "verwendet."),
    "rest_voltage_invalid": N_("Die gemessene Spannung nach der Landung liegt unter der Spannung unter Last am "
                               "Flugende – das ist physikalisch unmöglich (Akku vermutlich abgesteckt oder Sensor aus, "
                               "bevor die Messung fertig war). Verwendet wird die Modellschätzung der Ruhespannung; "
                               "keine Tiefentladung."),
    "vfr_invalid": N_("VFR-Werte außerhalb von 0–100 % (ältere Firmware oder Sensorfehler) werden nicht "
                      "verwendet."),
    "ri_implausible": N_("Innenwiderstand weniger als halb oder mehr als doppelt so groß wie der Median aller Flüge "
                         "(Fit gescheitert, z. B. wegen fehlerhafter Strom- oder Spannungswerte). Wird nicht für "
                         "Trends verwendet."),
}


# errors after which no battery value of the flight can be trusted
BATTERY_INVALID = ("current_stuck", "voltage_dropout")

# margin above the full cell voltage when the cell count is estimated from the highest start voltage
CELL_ESTIMATE_MARGIN_V = 0.05


def cell_count(configured_cells, highest_start_voltage, chemistry):
    """The cell count of a battery: the configured one, or - if none is configured (0) - estimated from the
    highest start voltage of its flights (0 if that is unknown). chemistry: an entry of config.CHEM."""
    if configured_cells > 0:
        return int(configured_cells)
    if not np.isfinite(highest_start_voltage):
        return 0
    return int(np.ceil(highest_start_voltage / (chemistry["full"] + CELL_ESTIMATE_MARGIN_V)))


def current_stuck(mean_current, max_current):
    """Current sensor saturated or wrongly scaled: mean current close to the maximum (arrays or numbers)."""
    mean_current, max_current = np.asarray(mean_current, dtype=float), np.asarray(max_current, dtype=float)
    return np.isfinite(mean_current) & np.isfinite(max_current) & (max_current > 10) & \
        (mean_current >= 0.97 * max_current)


def rest_voltage_invalid(u_rest, u_min, tol=0.02):
    """Rest voltage after landing below the voltage under load at the end of the flight (per cell): impossible.

    u_min is the lowest voltage in the last seconds under load - not of the whole flight, because after a deep
    discharge the resting voltage may legitimately be lower than a load peak early in the flight.
    """
    u_rest, u_min = np.asarray(u_rest, dtype=float), np.asarray(u_min, dtype=float)
    return np.isfinite(u_rest) & np.isfinite(u_min) & (u_rest < u_min - tol)


def detect_data_errors(df, ch):
    """Flight-level data errors that do not depend on derived values.

    df needs the per-cell columns (U_min_Zelle_V, Ri_Zelle_mOhm) and I_mittel_A, I_max_A, VFR_min.
    Returns {code: bool array}; "rest_voltage_invalid" is detected separately (see rest_voltage_invalid).
    """
    n = len(df)
    imean, imax = _col(df, "I_mittel_A"), _col(df, "I_max_A")
    umin = _col(df, "U_min_Zelle_V")
    vfr = _col(df, "VFR_min")
    ri = _col(df, "Ri_Zelle_mOhm")
    out = {}
    # a real flight alternates between part and full throttle: mean current close to the maximum = stuck sensor
    out["current_stuck"] = current_stuck(imean, imax)
    out["voltage_dropout"] = np.isfinite(umin) & (umin < 0.5 * ch["load_min"])
    out["vfr_invalid"] = np.isfinite(vfr) & ((vfr < 0) | (vfr > 100))
    bad_ri = np.zeros(n, dtype=bool)
    good = np.isfinite(ri) & ~out["current_stuck"] & ~out["voltage_dropout"]
    if good.sum() >= 5:
        med = float(np.median(ri[good]))
        bad_ri = np.isfinite(ri) & ((ri > 2.0 * med) | (ri < 0.5 * med))
    out["ri_implausible"] = bad_ri
    return out


def quality_messages(quality, n, ch):
    """[(tag, Msg)] for the summary: one line per kind of data error."""
    from ..utils import _ranges
    lines = []
    for code in QUALITY_LABELS:
        nums = sorted(quality.get(code, ()))
        if not nums:
            continue
        lines.append(("info", Msg("{label} in {n} von {total} Flügen (Flug {flights}): {text}",
                                  label=Msg(QUALITY_LABELS[code]), n=len(nums), total=n, flights=_ranges(nums),
                                  text=Msg(QUALITY_HINTS[code], limit=0.5 * ch["load_min"]))))
    return lines
