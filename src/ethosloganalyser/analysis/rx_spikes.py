# -*- coding: utf-8 -*-
"""Empfängerstrom: Spitzen erkennen und einem Anlass zuordnen."""

import numpy as np

from ..config import STEP
from ..utils import _rolling


def _corr_lag(a, b, max_shift):
    """Größte Korrelation (Betrag) zwischen a und b bei Versatz bis +-max_shift Rasterpunkte."""
    best = np.nan
    for sh in range(-max_shift, max_shift + 1):
        if sh > 0:
            x, y = a[sh:], b[:-sh]
        elif sh < 0:
            x, y = a[:sh], b[-sh:]
        else:
            x, y = a, b
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() < 30 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
            continue
        r = float(np.corrcoef(x[m], y[m])[0, 1])
        if not np.isfinite(best) or abs(r) > abs(best):
            best = r
    return best


def rx_spike_analysis(t, rx, gas=None, alt=None, rate=None, g=None, roll=None, pitch=None,
                      stick=None, switches=()):
    """Erkennt Stromspitzen des Empfängers und ordnet jede einem Anlass zu.

    Anlass:  Schalter       - ein Schalter wurde 3 s vor bis 1 s nach Beginn der Spitze umgelegt
                              (typisch Fahrwerk, Klappen, Bremsen)
             Manöver        - schnelle Knüppelbewegung, hohe Drehrate (Roll/Nick) oder hohe G-Last (+-1 s)
             Start/Landung  - erste 30 s, letzte 45 s oder unter 15 m Höhe
             ohne erkennbaren Anlass - nichts davon; Hinweis auf schwergängiges/defektes Servo
    """
    if rx is None or not np.any(np.isfinite(rx)) or np.nanmax(rx) <= 0:
        return None
    rs = _rolling(rx, 3)
    base = float(np.median(rs))
    mad = float(np.median(np.abs(rs - base))) * 1.4826
    thr = max(base + 4.0 * mad, base * 1.5, base + 0.3)
    above = rs > thr
    d = np.diff(np.r_[0, above.astype(int), 0])
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    segs = []
    for s0, s1 in zip(starts, ends):                      # Spitzen < 1 s auseinander zusammenfassen
        if segs and s0 - segs[-1][1] < int(1.0 / STEP):
            segs[-1][1] = s1
        else:
            segs.append([s0, s1])

    have_att = rate is not None or g is not None or stick is not None
    rate_hi = float(np.percentile(rate, 90)) if rate is not None else np.nan
    g_hi = max(float(np.percentile(g, 95)), 1.5) if g is not None else np.nan
    st_hi = max(float(np.percentile(stick, 90)), 50.0) if stick is not None else np.nan
    n = len(t)
    pick = lambda arr, k: float(arr[k]) if arr is not None else np.nan
    win_max = lambda arr, lo, hi: float(np.max(arr[lo:hi])) if arr is not None else np.nan
    spikes = []
    for s0, s1 in segs:
        k = s0 + int(np.argmax(rs[s0:s1]))
        lo, hi = max(0, min(s0, k - 4)), min(n, k + 5)    # Beginn der Spitze bis +1 s nach dem Maximum
        sp = dict(t=float(t[k]), t0=float(t[s0]), peak=float(rs[k]), dauer=float((s1 - s0) * STEP),
                  rate=win_max(rate, lo, hi), g=win_max(g, lo, hi), stick=win_max(stick, lo, hi),
                  roll=pick(roll, k), pitch=pick(pitch, k), gas=pick(gas, k), alt=pick(alt, k), schalter="")
        sw = [ev for ev in switches if t[s0] - 3.0 <= ev[0] <= t[s0] + 1.0]
        if sw:
            sp["schalter"] = ", ".join(sorted({ev[1] for ev in sw}))
            sp["anlass"] = "Schalter"
        elif ((np.isfinite(sp["stick"]) and sp["stick"] >= st_hi) or (np.isfinite(sp["rate"]) and sp["rate"] >= rate_hi)
              or (np.isfinite(sp["g"]) and sp["g"] >= g_hi)):
            sp["anlass"] = "Manöver"
        elif t[k] - t[0] < 30 or t[-1] - t[k] < 45 or (np.isfinite(sp["alt"]) and sp["alt"] < 15):
            sp["anlass"] = "Start/Landung"
        elif have_att:
            sp["anlass"] = "ohne erkennbaren Anlass"
        else:
            sp["anlass"] = "keine Lagedaten"
        spikes.append(sp)

    corr = {}
    for label, arr in [("Knüppelaktivität", stick), ("Drehrate", rate), ("G-Last", g), ("Gas", gas)]:
        if arr is not None:
            r = _corr_lag(rs, arr, int(1.0 / STEP))
            if np.isfinite(r):
                corr[label] = r
    return dict(rs=rs, base=base, thr=thr, mean=float(np.mean(rx)), max=float(np.max(rs)),
                spikes=spikes, corr=corr)
