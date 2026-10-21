# -*- coding: utf-8 -*-
"""
EthosLogAnalyser - Flug- & Akku-Analyse für FrSky Ethos Logfiles (CSV)
=====================================================================
Wählt einen Ordner mit CSV-Logs und wertet alle Flüge aus (nur Flüge länger als die
eingestellte Mindestdauer, Standard 2 min):

  * Akku:       Innenwiderstand (gesamt und im Flugverlauf), Spannung bei Referenzlast,
                geschätzte Gesamtkapazität, Restkapazität (SoH), Reserve, Alterungstrend,
                Lebensdauer-Prognose, Timer-Empfehlung
                Ladezustand am Ende: Ladungszählung (entnommene mAh) mit Gegenprobe über die
                Ruhespannung - weichen beide stark ab, wird der Flug markiert
  * Belastung:  C-Rate, Leistung, Gas-Histogramm, Flugphasen (Steigflug/Reise/Sinkflug),
                Energie je Phase, Wh je 100 m Steigen, G-Kräfte
  * Antrieb:    Kennlinie Drehzahl -> elektrische Leistung (Verschleiß-/FOD-Check),
                Sensor-Plausibilität (integrierte mAh gegen ESC-Zähler)
  * Funk/Bordnetz: RSSI, VFR, Empfängerspannung/-strom, Sender-Akku,
                Stromspitzen des Empfängers mit Zuordnung zu Manöver / Start-Landung / ohne Anlass
  * Auffälligkeiten (Ausreißer-Erkennung) und Zusammenhänge zwischen Nutzung und Alterung

Benötigt: Python 3.9+, pandas, numpy, matplotlib   (tkinter ist in Python enthalten)
Start:    python EthosLogAnalyser.py
EXE:      pyinstaller --onefile --windowed EthosLogAnalyser.py
"""

import os
import re
import sys
import glob
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
#  Zellchemie-Daten (Näherungskennlinien Ruhespannung -> Ladezustand)
# --------------------------------------------------------------------------
CHEM = {
    "LiPo": dict(
        full=4.20, rest_min=3.70, load_min=3.00,
        soc=[(3.27, 0), (3.61, 5), (3.69, 10), (3.71, 15), (3.73, 20), (3.75, 25), (3.77, 30),
             (3.79, 35), (3.80, 40), (3.82, 45), (3.84, 50), (3.85, 55), (3.87, 60), (3.91, 65),
             (3.95, 70), (3.98, 75), (4.02, 80), (4.08, 85), (4.11, 90), (4.15, 95), (4.20, 100)]),
    "LiHV": dict(
        full=4.35, rest_min=3.75, load_min=3.00,
        soc=[(3.27, 0), (3.61, 5), (3.69, 10), (3.73, 20), (3.77, 30), (3.80, 40), (3.84, 50),
             (3.87, 60), (3.95, 70), (4.02, 80), (4.10, 85), (4.18, 90), (4.27, 95), (4.35, 100)]),
    "Li-Ion": dict(
        full=4.20, rest_min=3.30, load_min=2.80,
        soc=[(3.00, 0), (3.30, 10), (3.40, 20), (3.50, 30), (3.60, 40), (3.70, 50), (3.80, 60),
             (3.90, 70), (4.00, 80), (4.10, 90), (4.20, 100)]),
}

SOC_TOL_PCT = 15.0      # erlaubte Abweichung Ladezustand Spannung <-> Ladungszählung [Prozentpunkte]

# Farben und Bezeichnungen der Anlässe für Empfängerstrom-Spitzen
SPIKE_CAUSES = [("Schalter", "tab:green"), ("Manöver", "tab:orange"), ("Start/Landung", "tab:blue"),
                ("ohne erkennbaren Anlass", "black"), ("keine Lagedaten", "grey")]
SPIKE_COLS = ["RxSp_Schalter", "RxSp_Manoever", "RxSp_StartLandung", "RxSp_ohne", "RxSp_unbekannt"]
SPIKE_COLOR = dict(SPIKE_CAUSES)


def soc_pct(v_cell, chem):
    pts = CHEM[chem]["soc"]
    return np.interp(v_cell, [a for a, _ in pts], [b for _, b in pts])


@dataclass
class Params:
    cells: int = 0                 # Zellenzahl; 0 = automatisch aus Startspannung
    chem: str = "LiPo"             # LiPo / LiHV / Li-Ion
    nominal_mah: float = 0.0       # Nennkapazität (0 = unbekannt)
    min_flight_s: float = 120.0    # Mindest-Flugdauer (Motor aktiv)
    active_current_a: float = 1.0  # Strom, ab dem der Motor als "aktiv" gilt
    reserve_pct: float = 20.0      # gewünschte Restkapazität bei Landung (für Timer)
    col_voltage: str = ""          # optional: Spaltenname (Teilstring), leer = automatisch
    col_current: str = ""


class Result:
    def __init__(self, df, skipped, total, series, meta):
        self.df, self.skipped, self.total, self.series, self.meta = df, skipped, total, series, meta


# --------------------------------------------------------------------------
#  Einlesen
# --------------------------------------------------------------------------
VOLT_KEYS = ["vfas", "ecu", "pack", "voltage", "volt", "(v)"]
CURR_KEYS = ["current", "curr", "amp", "(a)"]
EXCLUDE = ("rx", "tx", "adc", "empf", "esc rpm", "consumption", "rssi", "vfr")   # Empfänger-/Sender-/Funkwerte


def _find_col(columns, keys, override=""):
    low = {c: str(c).lower() for c in columns}
    if override:
        for c, l in low.items():
            if override.lower() in l:
                return c
        return None
    pool = {c: l for c, l in low.items() if not l.startswith(EXCLUDE)}
    for k in keys:
        for c, l in pool.items():
            if k in l:
                return c
    return None


def _to_num(s):
    if s.dtype == object:
        s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _numeric_cols(df, keys, exclude=()):
    """Alle Spalten, deren Name einen der Schlüssel enthält und die Werte haben."""
    out = []
    for c in df.columns:
        l = str(c).lower()
        if any(k in l for k in keys) and not any(x in l for x in exclude):
            s = _to_num(df[c])
            if s.notna().sum() > 0:
                out.append((c, s))
    return out


def _first_series(df, keys, exclude=()):
    r = _numeric_cols(df, keys, exclude)
    return r[0][1] if r else None


def _active_series(df, keys, exclude=()):
    """Erste Spalte mit positiven Werten (z. B. RSSI des tatsächlich genutzten Empfängers)."""
    r = _numeric_cols(df, keys, exclude)
    for _, s in r:
        if s.max() > 0:
            return s
    return r[0][1] if r else None


def _exact_series(df, names):
    """Spalte mit exakt einem der Namen (ohne Groß-/Kleinschreibung), z. B. Knüppelkanäle 'QR', 'HR'."""
    want = {n.lower() for n in names}
    for c in df.columns:
        if str(c).strip().lower() in want:
            s = _to_num(df[c])
            if s.notna().sum() > 0:
                return s
    return None


SWITCH_SKIP = ("rx", "vfr", "rssi", "pot", "drehg", "r9m", "adc", "unnamed", "date", "time", "fuel")


def _switch_columns(df):
    """Schalter/Taster: Spalten nur mit Werten aus {-1, 0, 1}, die sich im Log mindestens einmal ändern."""
    out = []
    for c in df.columns:
        l = str(c).strip().lower()
        if l.startswith(SWITCH_SKIP):
            continue
        s = _to_num(df[c])
        v = s.dropna()
        if len(v) < 20:
            continue
        u = set(np.unique(v.to_numpy()))
        if len(u) >= 2 and u <= {-1.0, 0.0, 1.0}:
            out.append((str(c).strip(), s))
    return out


def _time_seconds(df):
    """Liefert Zeit in Sekunden ab Start (float-Array) oder None."""
    cols = {str(c).lower().strip(): c for c in df.columns}
    tcol = next((cols[k] for k in cols if k in ("time", "zeit", "t")), None)
    dcol = next((cols[k] for k in cols if k in ("date", "datum")), None)
    if tcol is None:
        tcol = next((cols[k] for k in cols if "time" in k), None)
    if tcol is None:
        return None
    raw = df[tcol]
    num = _to_num(raw)
    if num.notna().mean() > 0.9:                      # numerische Zeit
        t = num.to_numpy(dtype=float)
        if np.nanmax(t) - np.nanmin(t) > 20000 and "ms" in str(tcol).lower():
            t = t / 1000.0
        return t - np.nanmin(t)
    txt = raw.astype(str).str.strip()
    if dcol is not None:
        txt = df[dcol].astype(str).str.strip() + " " + txt
    dt = pd.to_datetime(txt, errors="coerce", format="mixed")
    if dt.notna().mean() < 0.9:
        return None
    sec = (dt - dt.iloc[0]).dt.total_seconds().to_numpy(dtype=float)
    jumps = np.where(np.diff(sec) < -43200)[0]        # Mitternachts-Überlauf bei reiner Uhrzeit
    for j in jumps:
        sec[j + 1:] += 86400
    return sec


def _file_datetime(path):
    name = os.path.basename(path)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})[-_ T]?(\d{2})[-_:]?(\d{2})[-_:]?(\d{2})", name)
    if m:
        try:
            return datetime(*map(int, m.groups()))
        except ValueError:
            pass
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    if m:
        try:
            return datetime(*map(int, m.groups()))
        except ValueError:
            pass
    return datetime.fromtimestamp(os.path.getmtime(path))


def _clean_name(c):
    """Ethos mischt in Spaltennamen UTF-8 und Codepage-Zeichen ('Â°', 'au›en') - lesbar machen."""
    c = str(c).strip()
    for a, b in (("Â°", "°"), ("›", "ß"), ("Ã¤", "ä"), ("Ã¶", "ö"), ("Ã¼", "ü"), ("ÃŸ", "ß")):
        c = c.replace(a, b)
    return c


def read_log(path):
    last = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):      # Ethos schreibt oft cp1252 (Umlaute, °)
        try:
            df = pd.read_csv(path, sep=None, engine="python", encoding=enc)
            df.columns = [_clean_name(c) for c in df.columns]
            return df
        except UnicodeDecodeError as e:
            last = e
    raise last


def _nanmin(vals):
    v = [x for x in vals if np.isfinite(x)]
    return float(min(v)) if v else np.nan


def _nanmax(vals):
    v = [x for x in vals if np.isfinite(x)]
    return float(max(v)) if v else np.nan


def _rolling(a, n, how="mean"):
    s = pd.Series(a).rolling(n, min_periods=1, center=True)
    return (s.median() if how == "median" else s.mean()).to_numpy()


def _f(v, fmt="{:.0f}", na="–"):
    """Zahl formatieren, NaN/None als Strich."""
    try:
        return fmt.format(v) if v is not None and np.isfinite(v) else na
    except (TypeError, ValueError):
        return na


# --------------------------------------------------------------------------
#  Empfängerstrom: Spitzen erkennen und einordnen
# --------------------------------------------------------------------------
STEP = 0.25   # Raster der Zeitreihen in s


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


# --------------------------------------------------------------------------
#  Einzelflug-Analyse
# --------------------------------------------------------------------------
def analyse_file(path, p: Params):
    """Wertet eine Logdatei aus. Gibt (dict | None, Meldung) zurück."""
    try:
        df = read_log(path)
    except Exception as e:
        return None, f"Lesefehler: {e}"

    cv = _find_col(df.columns, VOLT_KEYS, p.col_voltage)
    ci = _find_col(df.columns, CURR_KEYS, p.col_current)
    if cv is None or ci is None:
        return None, f"Spalten nicht gefunden (Spannung={cv}, Strom={ci}). Verfügbar: {list(df.columns)}"
    t = _time_seconds(df)
    if t is None:
        return None, "Zeitspalte nicht erkannt"

    # Ethos loggt jeden Sensor in eigenen Zeilen -> Lücken mit dem letzten Wert auffüllen
    work = pd.DataFrame({"t": t, "u": _to_num(df[cv]).to_numpy(dtype=float),
                         "i": _to_num(df[ci]).to_numpy(dtype=float)}, index=df.index)
    extras = {
        "gas": _first_series(df, ["gas", "thr"]),
        "rpm": (_first_series(df, ["esc rpm"]) if _first_series(df, ["esc rpm"]) is not None
                else _first_series(df, ["rpm"])),
        "alt": _first_series(df, ["altitude", "höhe", "hoehe"]),
        "ax": _first_series(df, ["accx"]), "ay": _first_series(df, ["accy"]), "az": _first_series(df, ["accz"]),
        "rssi": _active_series(df, ["rssi"]),
        "vfr": _active_series(df, ["vfr"]),
        "rxi": _active_series(df, ["rxcurrent", "rx current", "rx curr"]),
        "rxu": _active_series(df, ["rxbatt", "rx batt", "rxbat"]),
        "roll": _first_series(df, ["roll", "r.angle"]),
        "pitch": _first_series(df, ["pitch", "nick", "p.angle"]),
        # Knüppelkanäle (Ethos-Quellen, exakte Namen): Quer-, Höhen-, Seitenruder
        "qr": _exact_series(df, ["QR", "Quer", "Ail", "Aileron", "Querruder"]),
        "hr": _exact_series(df, ["HR", "Ele", "Elevator", "Höhenruder"]),
        "sr": _exact_series(df, ["SR", "Rud", "Rudder", "Seite", "Seitenruder"]),
    }
    switch_cols = _switch_columns(df)
    for k_, (name, sr) in enumerate(switch_cols):
        extras[f"sw{k_}"] = sr
    for k, sr in extras.items():
        if sr is not None:
            work[k] = sr.to_numpy(dtype=float)
    work = work[np.isfinite(work["t"])].sort_values("t")
    if work["u"].notna().sum() < 20 or work["i"].notna().sum() < 20:
        return None, "Spannung/Strom kaum vorhanden (Sensor nicht verbunden?)"
    if work["u"].abs().max() < 1.0 and work["i"].abs().max() < 0.5:
        return None, f"nur Nullwerte in {cv}/{ci} (Bodenlog ohne Akku-Telemetrie)"
    fillc = [c for c in work.columns if c != "t"]
    work[fillc] = work[fillc].ffill(limit=20)
    work = work.dropna(subset=["u", "i"]).reset_index(drop=True)
    if len(work) < 20:
        return None, "zu wenige Datenpunkte"

    # Nur Zeitraum mit aktivem Motor betrachten
    act = np.where(work["i"].to_numpy() > p.active_current_a)[0]
    if len(act) < 10:
        return None, "kein Motorstrom erkannt"
    # Motorlauf in Blöcke teilen (Pause > 20 s) und den Block mit der größten Ladung nehmen -
    # ein kurzer Motortest vor dem Start oder nach einem Akkuwechsel zählt so nicht zum Flug.
    ta, ia = work["t"].to_numpy()[act], work["i"].to_numpy()[act]
    cut = np.flatnonzero(np.diff(ta) > 20.0) + 1
    blocks = np.split(np.arange(len(act)), cut)
    blk = max(blocks, key=lambda b: float(np.sum(ia[b])))
    a0, a1 = act[blk[0]], act[blk[-1]]
    pre = work.iloc[max(0, a0 - 15):a0]
    u_rest_start = float(np.median(pre["u"])) if len(pre) >= 3 else np.nan   # Ruhespannung vor dem Start

    # Gemessene Spannung nach dem Abstellen (5-30 s nach dem letzten Motorstrom, ohne Last).
    # Der Akku erholt sich noch weiter, der Wert ist also eher etwas zu niedrig (vorsichtig).
    u_rest_after = np.nan
    post = work.iloc[a1 + 1:]
    if len(post):
        tp = post["t"].to_numpy() - float(work["t"].iloc[a1])
        m = (tp >= 5) & (tp <= 30) & (post["i"].to_numpy() < p.active_current_a)
        if m.sum() >= 3:      # letzte Werte im Fenster: am nächsten an der echten Ruhespannung
            u_rest_after = float(np.median(post["u"].to_numpy()[m][-3:]))

    win = work.iloc[a0:a1 + 1]
    idx = win.index
    t = win["t"].to_numpy()
    u = win["u"].to_numpy()
    i = win["i"].to_numpy()
    dur = float(t[-1] - t[0])
    if dur < p.min_flight_s:
        return None, f"zu kurz ({dur:.0f} s < {p.min_flight_s:.0f} s)"

    dt = np.clip(np.diff(t, prepend=t[0]), 0, 5.0)         # Lücken im Log nicht mitintegrieren
    q_mah = np.cumsum(i * dt) / 3.6                        # A*s -> mAh
    e_wh = float(np.sum(u * i * dt) / 3600.0)

    # --- Zeitraster ------------------------------------------------------------
    tg = np.arange(t[0], t[-1], STEP)
    if len(tg) < 40:
        return None, "zu wenige Datenpunkte"

    def grid(col):
        if col in win.columns and win[col].notna().sum() > 5:
            return np.interp(tg, t, win[col].ffill().bfill().to_numpy(dtype=float))
        return None

    ug, ig = np.interp(tg, t, u), np.interp(tg, t, i)
    qg_mah = np.interp(tg, t, q_mah)
    pg = ug * ig
    gasg, rpmg, altg = grid("gas"), grid("rpm"), grid("alt")
    axg, ayg, azg = grid("ax"), grid("ay"), grid("az")
    rssig, vfrg, rxig, rxug = grid("rssi"), grid("vfr"), grid("rxi"), grid("rxu")
    rollg, pitchg = grid("roll"), grid("pitch")
    sticks = {}
    for key, label in [("qr", "Querruder"), ("hr", "Höhenruder"), ("sr", "Seitenruder")]:
        g_ = grid(key)
        if g_ is not None and np.ptp(g_) > 20:
            sticks[label] = np.clip(g_ / 1024.0 * 100.0, -100, 100)          # Knüppelweg [%]
    stick_act = None
    if sticks:      # Knüppelaktivität: Summe der Knüppelgeschwindigkeiten [%/s] - Maß für Servoarbeit
        stick_act = np.sum([np.abs(np.gradient(_rolling(v, 2), STEP)) for v in sticks.values()], axis=0)
        stick_act = _rolling(stick_act, 3)
    # Schalterereignisse im Flugzeitraum (Zeit relativ zum Motorstart)
    switch_ev = []
    t_win = win["t"].to_numpy()
    for k_, (name, _) in enumerate(switch_cols):
        col = f"sw{k_}"
        if col not in win.columns:
            continue
        v = win[col].ffill().bfill().to_numpy(dtype=float)
        for j in np.flatnonzero(np.diff(v) != 0):
            if np.isfinite(v[j]) and np.isfinite(v[j + 1]):
                switch_ev.append((float(t_win[j + 1] - tg[0]), name, v[j], v[j + 1]))
    switch_ev.sort()

    # --- Innenwiderstand: U = c0 + c1*I + c2*Q  (Ri = -c1) ------------------------
    # Strom wird in Ethos mit Zeitversatz zur Spannung geloggt -> besten Versatz suchen.
    ri = u0 = k_v = r2 = lag_best = np.nan
    ri_seg = [np.nan, np.nan, np.nan]
    ocv_g = None
    qg_ah = qg_mah / 1000.0
    best = None
    for lag in np.arange(-1.0, 1.51, STEP):
        sh = int(round(lag / STEP))
        if sh > 0:
            uu, ii, qq = ug[sh:], ig[:-sh], qg_ah[sh:]
        elif sh < 0:
            uu, ii, qq = ug[:sh], ig[-sh:], qg_ah[:sh]
        else:
            uu, ii, qq = ug, ig, qg_ah
        m = ii > max(2.0, p.active_current_a)
        if m.sum() < 30 or np.std(ii[m]) < 1.0:
            continue
        X = np.column_stack([np.ones(m.sum()), ii[m], qq[m]])
        coef, *_ = np.linalg.lstsq(X, uu[m], rcond=None)
        res = uu[m] - X @ coef
        tot = np.var(uu[m])
        r2_ = 1 - np.var(res) / tot if tot > 0 else np.nan
        if np.isfinite(r2_) and (best is None or r2_ > best[0]):
            best = (r2_, coef, lag, sh)
    if best is not None:
        r2, coef, lag_best, sh = best
        u0, ri, k_v = float(coef[0]), float(-coef[1]), float(coef[2])
        if not (0 < ri < 1.0):                              # unplausibel (> 1 Ohm Pack)
            ri = u0 = k_v = np.nan
        else:
            # Ri im Flugverlauf (Anfang / Mitte / Ende nach entnommener Kapazität)
            if sh > 0:
                uu, ii, qq = ug[sh:], ig[:-sh], qg_ah[sh:]
            elif sh < 0:
                uu, ii, qq = ug[:sh], ig[-sh:], qg_ah[:sh]
            else:
                uu, ii, qq = ug, ig, qg_ah
            uadj = uu - k_v * qq
            qmax = qq.max()
            edges = [0, qmax / 3, 2 * qmax / 3, qmax + 1]
            for s_i in range(3):
                m = (qq >= edges[s_i]) & (qq < edges[s_i + 1]) & (ii > max(2.0, p.active_current_a))
                if m.sum() >= 25 and np.std(ii[m]) > 1.0:
                    sl, _ = np.polyfit(ii[m], uadj[m], 1)
                    if 0 < -sl < 1.0:
                        ri_seg[s_i] = float(-sl)
            # Ruhespannung (lastfrei geschätzt) mit zeitlich passendem Strom, ~10 s geglättet
            i_al = np.interp(tg - sh * STEP, tg, ig)
            ocv_g = _rolling(ug + ri * i_al, 40)

    # Ruhespannung am Ende (aus dem Modell geschätzt)
    if ocv_g is not None:
        u_ocv_end = float(np.mean(ocv_g[-40:]))
    else:
        low = np.where(ig < p.active_current_a)[0]
        u_ocv_end = float(np.median(ug[low[-20:]])) if len(low) >= 5 else np.nan

    # --- Belastung -----------------------------------------------------------------
    p_max = float(np.max(_rolling(pg, 4)))
    p_mean = float(e_wh * 3600.0 / max(dur, 1))
    zeit80 = float(np.sum(ig > 0.8 * ig.max()) * STEP)
    gas_pct = None
    gas_hist = None
    if gasg is not None:
        gas_pct = np.clip((gasg + 1024.0) / 2048.0 * 100.0, 0, 100)
        gas_hist = np.histogram(gas_pct, bins=np.arange(0, 101, 10))[0] * STEP     # Sekunden je 10-%-Klasse

    # --- Antrieb: P_el = exp(a) * rpm^n -----------------------------------------------
    rpm_p90 = rpm_max = p_n = p_a = np.nan
    if rpmg is not None and np.nanmax(rpmg) > 1000:
        rs = _rolling(rpmg, 4, "median")
        ps = _rolling(pg, 4)
        rpm_max = float(np.max(rs))
        rpm_p90 = float(np.percentile(rs[rs > 1000], 90)) if np.any(rs > 1000) else np.nan
        m = (rs > 0.3 * rs.max()) & (ps > 200)
        if m.sum() > 40 and np.ptp(np.log(rs[m])) > 0.15:
            n_, a_ = np.polyfit(np.log(rs[m]), np.log(ps[m]), 1)
            if 1.0 < n_ < 6.0:
                p_n, p_a = float(n_), float(a_)

    # --- Flugphasen (aus Höhe) -------------------------------------------------------------
    e_up = e_cr = e_dn = t_up = t_cr = t_dn = wh100 = alt_max = np.nan
    alt_rel = None
    if altg is not None and np.ptp(altg) > 5:
        alt_s = _rolling(altg, 8)
        alt_rel = alt_s - np.median(alt_s[:8])
        vz = np.gradient(alt_s, STEP)
        up, dn = vz > 1.0, vz < -1.0
        cr = ~(up | dn)
        e_step = pg * STEP / 3600.0
        e_up, e_dn, e_cr = float(e_step[up].sum()), float(e_step[dn].sum()), float(e_step[cr].sum())
        t_up, t_dn, t_cr = float(up.sum() * STEP), float(dn.sum() * STEP), float(cr.sum() * STEP)
        dalt = np.diff(alt_s)
        climb = float(np.sum(np.clip(dalt, 0, None)[up[1:]]))
        wh100 = e_up / climb * 100.0 if climb > 20 else np.nan
        alt_max = float(alt_rel.max())

    # --- G-Kräfte und Drehrate ---------------------------------------------------------------
    g_max = g_p95 = rate_p95 = np.nan
    gg = None
    if axg is not None and ayg is not None and azg is not None:
        gg = np.sqrt(axg ** 2 + ayg ** 2 + azg ** 2)
        g_max, g_p95 = float(np.max(gg)), float(np.percentile(gg, 95))
    rateg = None
    comps = [np.abs(np.gradient(_rolling(np.degrees(np.unwrap(np.radians(a))), 3), STEP))
             for a in (rollg, pitchg) if a is not None]
    if comps:
        rateg = np.sqrt(np.sum([c ** 2 for c in comps], axis=0))      # Drehrate Roll+Nick [°/s]
        rate_p95 = float(np.percentile(rateg, 95))

    # --- Funk / Bordnetz (nur im Zeitraum mit aktivem Motor) ---------------------------------------
    def win_vals(keys, how, need_pos=False):
        vals = []
        for _, s in _numeric_cols(df, keys):
            sv = s.iloc[_orig_idx]
            if sv.notna().sum() == 0 or (need_pos and sv.max() <= 0):
                continue
            vals.append(float(sv.min() if how == "min" else sv.max()))
        return _nanmin(vals) if how == "min" else _nanmax(vals)

    # Zeilen der Originaldatei im Flugzeitraum (work wurde neu nummeriert)
    t_all = np.asarray(_time_seconds(df), dtype=float)
    _orig_idx = np.flatnonzero((t_all >= t[0]) & (t_all <= t[-1]))

    rssi_min = win_vals(["rssi"], "min", need_pos=True)
    vfr_min = win_vals(["vfr"], "min", need_pos=True)
    rxb_min = win_vals(["rxbatt", "rx batt", "rxbat"], "min")
    rxc_max = win_vals(["rxcurrent", "rx current", "rx curr"], "max")
    txb_min = win_vals(["txbat"], "min")

    rx = rx_spike_analysis(tg - tg[0], rxig, gas_pct, alt_rel, rateg, gg, rollg, pitchg, stick_act, switch_ev)
    cnt = {c: 0 for c, _ in SPIKE_CAUSES}
    if rx:
        for sp in rx["spikes"]:
            cnt[sp["anlass"]] += 1

    esc = _first_series(df, ["esc consumption", "consumption"])
    esc_mah = np.nan
    if esc is not None:
        ev = esc.iloc[_orig_idx].dropna()
        if len(ev):
            esc_mah = float(ev.max() - ev.min())

    umin = float(np.min(_rolling(u, 5)))
    row = dict(
        datei=os.path.basename(path), pfad=path,
        datum=_file_datetime(path),
        dauer_s=round(dur, 1),
        entnommen_mAh=round(float(q_mah[-1]), 0), ESC_mAh=round(esc_mah, 0) if np.isfinite(esc_mah) else np.nan,
        energie_Wh=round(e_wh, 2),
        I_mittel_A=round(float(np.mean(i)), 1), I_max_A=round(float(np.max(i)), 1),
        P_max_W=round(p_max, 0), P_mittel_W=round(p_mean, 0), Zeit_80_s=round(zeit80, 1),
        Gas_mittel_pct=round(float(np.mean(gas_pct)), 1) if gas_pct is not None else np.nan,
        U_start_V=round(float(np.max(u[:max(3, len(u) // 50)])), 2),
        U_ruhe_start_V=round(u_rest_start, 2) if np.isfinite(u_rest_start) else np.nan,
        U_min_V=round(umin, 2), U_ocv_ende_V=round(u_ocv_end, 2) if np.isfinite(u_ocv_end) else np.nan,
        U_ruhe_nach_V=round(u_rest_after, 2) if np.isfinite(u_rest_after) else np.nan,
        Ri_mOhm=round(ri * 1000, 1) if np.isfinite(ri) else np.nan,
        Ri_Anfang_mOhm=round(ri_seg[0] * 1000, 1) if np.isfinite(ri_seg[0]) else np.nan,
        Ri_Mitte_mOhm=round(ri_seg[1] * 1000, 1) if np.isfinite(ri_seg[1]) else np.nan,
        Ri_Ende_mOhm=round(ri_seg[2] * 1000, 1) if np.isfinite(ri_seg[2]) else np.nan,
        U0_V=round(u0, 3) if np.isfinite(u0) else np.nan, k_V_je_Ah=k_v,
        fit_R2=round(float(r2), 2) if np.isfinite(r2) else np.nan,
        versatz_s=round(float(lag_best), 2) if np.isfinite(lag_best) else np.nan,
        rpm_max=round(rpm_max, 0) if np.isfinite(rpm_max) else np.nan,
        rpm_p90=round(rpm_p90, 0) if np.isfinite(rpm_p90) else np.nan, P_n=p_n, P_a=p_a,
        E_steig_Wh=e_up, E_reise_Wh=e_cr, E_sink_Wh=e_dn, t_steig_s=t_up, t_reise_s=t_cr, t_sink_s=t_dn,
        Wh_je_100m=wh100, Hoehe_max_m=alt_max, g_max=g_max, g_p95=g_p95, Drehrate_p95=rate_p95,
        RSSI_min=rssi_min, VFR_min=vfr_min, RxBatt_min_V=rxb_min, RxStrom_max_A=rxc_max, TxBat_min_V=txb_min,
        RxStrom_mittel_A=round(rx["mean"], 2) if rx else np.nan,
        RxSpitzen_n=len(rx["spikes"]) if rx else np.nan,
        RxSp_Schalter=cnt["Schalter"] if rx else np.nan,
        RxSp_Manoever=cnt["Manöver"] if rx else np.nan,
        RxSp_StartLandung=cnt["Start/Landung"] if rx else np.nan,
        RxSp_ohne=cnt["ohne erkennbaren Anlass"] if rx else np.nan,
        RxSp_unbekannt=cnt["keine Lagedaten"] if rx else np.nan,
        Rx_r_Drehrate=round(rx["corr"]["Drehrate"], 2) if rx and "Drehrate" in rx["corr"] else np.nan,
        Rx_r_Knueppel=round(rx["corr"]["Knüppelaktivität"], 2) if rx and "Knüppelaktivität" in rx["corr"] else np.nan,
        Knueppel_p95=round(float(np.percentile(stick_act, 95)), 0) if stick_act is not None else np.nan,
        Schalter_n=len(switch_ev),
        Rx_r_G=round(rx["corr"]["G-Last"], 2) if rx and "G-Last" in rx["corr"] else np.nan,
    )
    row["_series"] = dict(
        t=tg - tg[0], u=ug, i=ig, p=pg, q=qg_mah, gas=gas_pct, rpm=rpmg, alt=alt_rel, ocv=ocv_g,
        gas_hist=gas_hist, rssi=rssig, vfr=vfrg, rxi=rxig, rxu=rxug, rate=rateg, g=gg, rx=rx,
        roll=rollg, pitch=pitchg, sticks=sticks, stick=stick_act, switches=switch_ev,
    )
    return row, "ok"


# --------------------------------------------------------------------------
#  Ordner-Auswertung (Querschnitt über alle Flüge)
# --------------------------------------------------------------------------
def _col(df, name):
    return df[name].to_numpy(dtype=float) if name in df.columns else np.full(len(df), np.nan)


def _timer_s(series, q_limit):
    """Zeit, zu der die entnommene Kapazität q_limit [mAh] erreicht wird (bei Bedarf extrapoliert)."""
    t, q = series["t"], np.maximum.accumulate(series["q"])
    if q[-1] >= q_limit:
        return float(np.interp(q_limit, q, t))
    tail = series["i"][-240:]                          # letzte 60 s
    i_mean = max(float(np.mean(tail)), 1.0)
    return float(t[-1] + (q_limit - q[-1]) / (i_mean / 3.6))


def analyse_folder(folder, p: Params, progress=None):
    files = sorted(glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True))
    rows, skipped, series = [], [], {}
    for n, f in enumerate(files):
        res, msg = analyse_file(f, p)
        if res is None:
            skipped.append((os.path.basename(f), msg))
        else:
            series[res["pfad"]] = res.pop("_series")
            rows.append(res)
        if progress:
            progress(n + 1, len(files))

    meta = {}
    if not rows:
        return Result(pd.DataFrame(), skipped, len(files), series, meta)

    df = pd.DataFrame(rows).sort_values("datum").reset_index(drop=True)
    df.insert(0, "Flug", np.arange(1, len(df) + 1))
    ch = CHEM[p.chem]

    # Zellenzahl: vorgegeben oder aus der höchsten Startspannung geschätzt
    ustart = df["U_ruhe_start_V"].fillna(df["U_start_V"])
    cells = p.cells if p.cells > 0 else int(np.ceil(ustart.max() / (ch["full"] + 0.05)))
    meta["cells"] = cells
    df["Zellen"] = cells

    for src, dst in [("U_min_V", "U_min_Zelle_V"), ("U_ruhe_start_V", "U_start_Zelle_V"),
                     ("U_ocv_ende_V", "U_ende_gesch_Zelle_V"), ("U_ruhe_nach_V", "U_ende_mess_Zelle_V"),
                     ("U0_V", "U0_Zelle_V")]:
        df[dst] = (df[src] / cells).round(3)
    for src, dst in [("Ri_mOhm", "Ri_Zelle_mOhm"), ("Ri_Anfang_mOhm", "Ri_Anf_Zelle_mOhm"),
                     ("Ri_Ende_mOhm", "Ri_End_Zelle_mOhm")]:
        df[dst] = (df[src] / cells).round(2)

    # Ruhespannung am Ende: gemessen nach dem Abstellen bevorzugt, sonst Modellschätzung.
    # Ein Wert über der Startspannung ist physikalisch unmöglich (z. B. Akkuwechsel im selben Log) -> verwerfen.
    u_st = df["U_start_Zelle_V"].to_numpy(dtype=float)
    u_me = df["U_ende_mess_Zelle_V"].to_numpy(dtype=float)
    u_ge = df["U_ende_gesch_Zelle_V"].to_numpy(dtype=float)
    below = lambda v: np.isfinite(v) & (~np.isfinite(u_st) | (v < u_st - 0.03))
    ok_me, ok_ge = below(u_me), below(u_ge)
    df["U_ende_Zelle_V"] = np.where(ok_me, u_me, np.where(ok_ge, u_ge, np.nan)).round(3)
    df["U_ende_Quelle"] = np.where(ok_me, "gemessen", np.where(ok_ge, "geschätzt", "–"))

    # Ladezustand aus Ruhespannung (Näherungskennlinie) und Kapazitätsschätzung
    df["SoC_start_pct"] = np.round(soc_pct(df["U_start_Zelle_V"].to_numpy(dtype=float), p.chem), 0)
    df["SoC_ende_U_pct"] = np.round(soc_pct(df["U_ende_Zelle_V"].to_numpy(dtype=float), p.chem), 0)
    dsoc_u = (df["SoC_start_pct"] - df["SoC_ende_U_pct"]).to_numpy(dtype=float)
    ent = df["entnommen_mAh"].to_numpy(dtype=float)
    kap = np.where(dsoc_u >= 40, np.round(ent / (np.where(dsoc_u > 0, dsoc_u, np.nan) / 100.0), 0), np.nan)
    kf = kap[np.isfinite(kap)]
    if len(kf) >= 3:                                    # grobe Ausreißer (Faktor 1,6) verwerfen
        med = np.median(kf)
        kap = np.where((kap > med / 1.6) & (kap < med * 1.6), kap, np.nan)
    df["Kap_gesch_mAh"] = kap

    # Sensor-Plausibilität und Pausen
    esc = df["ESC_mAh"].to_numpy(dtype=float)
    df["Sensor_Abw_pct"] = np.where(esc > 100, np.round((ent - esc) / np.where(esc > 0, esc, np.nan) * 100, 1), np.nan)
    df["Pause_h"] = df["datum"].diff().dt.total_seconds() / 3600.0

    # Kapazitätsbezug: aktuelle Schätzung (letzte 3 gültige Flüge) bzw. Nennkapazität
    kv = df["Kap_gesch_mAh"].dropna()
    cap_est = float(kv.iloc[-3:].median()) if len(kv) else np.nan
    cap_ref = p.nominal_mah if p.nominal_mah > 0 else cap_est
    meta.update(cap_est=cap_est, cap_ref=cap_ref,
                cap_src="Nennkapazität" if p.nominal_mah > 0 else "geschätzte Kapazität")

    # Ladezustand am Ende: Ladungszählung (Start-SoC - entnommen/Kapazität) ist robust gegen
    # Erholung, Akkuwechsel und Sensorfehler am Logende. Die Spannung dient als Gegenprobe.
    if np.isfinite(cap_ref) and cap_ref > 0:
        soc0 = df["SoC_start_pct"].fillna(100.0).to_numpy(dtype=float)
        df["SoC_ende_Q_pct"] = np.round(soc0 - ent / cap_ref * 100.0, 0)
    else:
        df["SoC_ende_Q_pct"] = np.nan
    sq, su = df["SoC_ende_Q_pct"].to_numpy(dtype=float), df["SoC_ende_U_pct"].to_numpy(dtype=float)
    df["SoC_Abw_pct"] = np.where(np.isfinite(sq) & np.isfinite(su), su - sq, np.nan)
    df["SoC_ende_pct"] = np.where(np.isfinite(sq), sq, su)
    df["dSoC_pct"] = df["SoC_start_pct"] - df["SoC_ende_pct"]
    abw = df["SoC_Abw_pct"].to_numpy(dtype=float)
    df["SoC_plausibel"] = np.where(np.isfinite(abw), np.abs(abw) <= SOC_TOL_PCT, np.isfinite(su))
    # Spannungsreserve nur, wenn die Endspannung zur entnommenen Ladung passt
    df["Reserve_Zelle_V"] = np.where(df["SoC_plausibel"], (df["U_ende_Zelle_V"] - ch["rest_min"]).round(3), np.nan)

    # Zellchemie-Prüfung: Mit welcher Kennlinie passen Ruhespannung und Ladungszählung zusammen?
    # (nur mit eingetragener Nennkapazität aussagekräftig, sonst wäre die Prüfung zirkulär)
    meta["chem_fit"] = {}
    if p.nominal_mah > 0:
        u_end_all = df["U_ende_Zelle_V"].to_numpy(dtype=float)
        for chem_ in CHEM:
            s0 = soc_pct(u_st, chem_)
            s0 = np.where(np.isfinite(u_st), s0, 100.0)
            dd = np.abs(soc_pct(u_end_all, chem_) - (s0 - ent / p.nominal_mah * 100.0))
            dd = dd[np.isfinite(dd) & np.isfinite(u_end_all)]
            if len(dd) >= 3:
                meta["chem_fit"][chem_] = float(np.median(dd))

    # Referenzbedingungen für fairen Vergleich über alle Flüge
    iref = max(5.0, round(float(df["I_mittel_A"].median()) / 5) * 5)
    qref = max(100.0, round(0.5 * float(df["entnommen_mAh"].median()) / 100) * 100)
    meta.update(iref=iref, qref=qref)
    ok = (df["entnommen_mAh"] >= qref) & df["U0_V"].notna()
    df["U_ref_Zelle_V"] = np.where(
        ok, (df["U0_V"] - df["Ri_mOhm"] / 1000.0 * iref + df["k_V_je_Ah"] * qref / 1000.0) / cells, np.nan)
    df["U_ref_Zelle_V"] = df["U_ref_Zelle_V"].round(3)

    rpm_ref = np.nan
    if df["rpm_p90"].notna().any():
        rpm_ref = round(float(df["rpm_p90"].median()) / 1000) * 1000
        okr = (df["rpm_p90"] >= 0.9 * rpm_ref) & df["P_n"].notna()
        df["P_ref_W"] = np.where(okr, np.round(np.exp(df["P_a"] + df["P_n"] * np.log(rpm_ref)), 0), np.nan)
    else:
        df["P_ref_W"] = np.nan
    meta["rpm_ref"] = rpm_ref

    df["C_peak"] = df["I_max_A"] / (cap_ref / 1000.0) if np.isfinite(cap_ref) and cap_ref > 0 else np.nan
    if np.isfinite(cap_ref) and cap_ref > 0:
        df["Vollzyklen_kum"] = (df["entnommen_mAh"].cumsum() / cap_ref).round(2)
    else:
        df["Vollzyklen_kum"] = np.nan

    # Timer: Zeit bis zur Reserve (Restkapazität = reserve_pct), je Flug aus seinem eigenen Profil
    cap_timer = cap_est if np.isfinite(cap_est) else (p.nominal_mah if p.nominal_mah > 0 else np.nan)
    if p.nominal_mah > 0:
        cap_timer = p.nominal_mah if not np.isfinite(cap_est) else min(cap_est, p.nominal_mah)
    timers = []
    for _, r in df.iterrows():
        s = series[r["pfad"]]
        soc0 = r["SoC_start_pct"] if np.isfinite(r["SoC_start_pct"]) else 100.0
        if np.isfinite(cap_timer) and soc0 > p.reserve_pct:
            timers.append(round(_timer_s(s, cap_timer * (soc0 - p.reserve_pct) / 100.0), 0))
        else:
            timers.append(np.nan)
    df["Timer_s"] = timers
    meta["timer_s"] = float(np.nanmedian(df["Timer_s"].iloc[-5:])) if df["Timer_s"].notna().any() else np.nan
    meta["cap_timer"] = cap_timer

    warnings, flags = evaluate(df, p, meta)
    meta["warnings"], meta["flags"] = warnings, flags
    df["Auffaellig"] = [
        ", ".join(name for name, fl in flags.items() if int(r["Flug"]) in fl) for _, r in df.iterrows()]
    meta["corr"] = usage_correlations(df)
    return Result(df, skipped, len(files), series, meta)


# --------------------------------------------------------------------------
#  Bewertung: Warnungen, Ausreißer, Zusammenhänge
# --------------------------------------------------------------------------
ANOM_METRICS = [
    ("Ri_Zelle_mOhm", "hoch", "Innenwiderstand"),
    ("U_ref_Zelle_V", "niedrig", "Spannung bei Referenzlast"),
    ("Kap_gesch_mAh", "niedrig", "geschätzte Kapazität"),
    ("P_ref_W", "hoch", "Antriebsleistung bei Referenzdrehzahl"),
    ("RSSI_min", "niedrig", "RSSI-Minimum"),
    ("VFR_min", "niedrig", "VFR-Minimum"),
    ("RxBatt_min_V", "niedrig", "Empfängerspannung"),
    ("RxStrom_max_A", "hoch", "Empfängerstrom-Maximum"),
    ("Sensor_Abw_pct", "abs", "Abweichung Strommessung/ESC-Zähler"),
]


def _ranges(nums):
    """[1,2,3,5,7,8] -> '1-3, 5, 7-8'"""
    nums = sorted(int(n) for n in nums)
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(f"{start}" if start == prev else f"{start}-{prev}")
            start = prev = n
    if start is not None:
        out.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(out)


TREND_METRICS = {"Ri_Zelle_mOhm", "U_ref_Zelle_V", "Kap_gesch_mAh", "P_ref_W"}


def evaluate(df, p, meta):
    """Gibt (Liste[(Stufe, Text)], {Metrikname: Set(Flugnummern)}) zurück."""
    ch = CHEM[p.chem]
    warns, flags = [], {}
    n = len(df)
    fmt = lambda r: f"Flug {int(r['Flug'])} ({r['datum']:%d.%m.%Y})"

    # absolute Grenzwerte - gleichartige Warnungen werden zu einer Zeile zusammengefasst
    def group(mask, label, tag, text):
        if mask.any():
            nums = df.loc[mask, "Flug"].astype(int).tolist()
            flags[label] = set(nums)
            warns.append((tag, f"{label} in {len(nums)} von {n} Flügen (Flug {_ranges(nums)}): {text}"))

    abw = df["SoC_Abw_pct"].to_numpy(dtype=float)
    unpl = np.isfinite(abw) & (np.abs(abw) > SOC_TOL_PCT)
    if unpl.any():
        group(unpl, "Ladezustand unplausibel", "warn",
              f"Ladezustand aus der Endspannung weicht im Mittel um {np.mean(abw[unpl]):+.0f} Prozentpunkte von der "
              f"Ladungszählung ab (entnommen / {meta['cap_src']} {meta['cap_ref']:.0f} mAh). Verwendet wird die "
              "Ladungszählung. Mögliche Ursachen: Akkuwechsel oder Motorlauf nach der Landung im selben Log, "
              "Spannungssensor, falsche Nennkapazität oder Zellchemie.")

    res_v = df["Reserve_Zelle_V"].to_numpy(dtype=float)
    socq = df["SoC_ende_Q_pct"].to_numpy(dtype=float)
    u_end = df["U_ende_Zelle_V"].to_numpy(dtype=float)
    measured_low = (df["U_ende_Quelle"] == "gemessen").to_numpy() & np.isfinite(u_end) & (u_end < ch["rest_min"])
    deep = (np.isfinite(res_v) & (res_v < 0)) | (np.isfinite(socq) & (socq < 5)) | measured_low
    if deep.any():
        group(deep, "Tiefentladung", "bad",
              f"Ruhespannung am Ende unter {ch['rest_min']:.2f} V/Zelle ({p.chem}) oder rechnerischer Ladezustand "
              f"unter 5 % (tiefste Endspannung {np.nanmin(np.where(deep, u_end, np.nan)):.2f} V/Zelle). "
              "Bitte auch Zellchemie und Nennkapazität prüfen.")
    umin = df["U_min_Zelle_V"].to_numpy(dtype=float)
    low = np.isfinite(umin) & (umin < ch["load_min"])
    group(low, "Spannungseinbruch", "bad",
          f"Spannung unter Last fiel bis auf {np.nanmin(umin):.2f} V/Zelle (Grenze {ch['load_min']:.2f} V).")
    sab = df["Sensor_Abw_pct"].to_numpy(dtype=float)
    sens = np.isfinite(sab) & (np.abs(sab) > 5)
    group(sens, "Sensorabweichung", "warn",
          "Strommessung weicht mehr als 5 % vom ESC-Zähler ab (Sensor prüfen/kalibrieren).")
    ohne = df["RxSp_ohne"].to_numpy(dtype=float)
    group(np.isfinite(ohne) & (ohne >= 3), "Empfängerstrom-Spitzen ohne Anlass", "warn",
          "mindestens 3 Stromspitzen ohne Manöver, Start oder Landung. Servos auf Schwergängigkeit, "
          "Anschlag (Brummen in Endlage) und Defekte prüfen; Zeitpunkte siehe Einzelflug.")

    # statistische Ausreißer (robuster z-Wert, bei Alterungsgrößen relativ zum Trend), erst ab 6 Flügen
    if n >= 6:
        fl = df["Flug"].to_numpy(dtype=float)
        for col, direction, label in ANOM_METRICS:
            x = df[col].to_numpy(dtype=float)
            good = np.isfinite(x)
            if good.sum() < 6:
                continue
            med = float(np.median(x[good]))
            if col in TREND_METRICS and np.ptp(fl[good]) > 0:
                sl, ic = np.polyfit(fl[good], x[good], 1)
                ref = sl * fl + ic
            else:
                ref = np.full(n, med)
            resid = x - ref
            rmed = float(np.median(resid[good]))
            mad = float(np.median(np.abs(resid[good] - rmed))) * 1.4826
            floor = 0.5 if col == "Sensor_Abw_pct" else max(abs(med) * 0.01, 1e-9)
            z = (resid - rmed) / max(mad, floor)
            bad = {"hoch": z > 3.5, "niedrig": z < -3.5}.get(direction, np.abs(z) > 3.5) & good
            if label == "Abweichung Strommessung/ESC-Zähler" and sens.any():
                bad &= ~sens
            if bad.any():
                flags[label] = set(int(v) for v in df.loc[bad, "Flug"])
                for k in np.where(bad)[0]:
                    warns.append(("warn", f"{fmt(df.iloc[k])}: auffälliger Wert bei {label} "
                                          f"({x[k]:.4g}, erwartet ca. {ref[k]:.4g})."))
    return warns, flags


def _trend(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3 or np.ptp(x[m]) == 0:
        return None
    s, b = np.polyfit(x[m], y[m], 1)
    return s, b


def usage_correlations(df):
    """Korreliert die Ri-Abweichung vom Trend mit Nutzungsfaktoren (nur Hinweise, keine Kausalität)."""
    out = []
    if len(df) < 8:
        return out
    x = df["Flug"].to_numpy(dtype=float)
    ri = df["Ri_Zelle_mOhm"].to_numpy(dtype=float)
    tr = _trend(x, ri)
    if tr is None:
        return out
    resid = ri - (tr[0] * x + tr[1])
    factors = [("C_peak", "Spitzen-C-Rate"), ("dSoC_pct", "Entladetiefe"), ("U_ende_Zelle_V", "Endspannung"),
               ("SoC_start_pct", "Ladezustand beim Start"), ("Pause_h", "Pause seit letztem Flug"),
               ("I_mittel_A", "mittlerer Strom"), ("dauer_s", "Flugdauer")]
    for col, label in factors:
        f = df[col].to_numpy(dtype=float)
        m = np.isfinite(f) & np.isfinite(resid)
        if m.sum() >= 8 and np.std(f[m]) > 0 and np.std(resid[m]) > 0:
            r = float(np.corrcoef(f[m], resid[m])[0, 1])
            if abs(r) >= 0.6:
                out.append((label, r))
    return sorted(out, key=lambda a: -abs(a[1]))


# --------------------------------------------------------------------------
#  Zusammenfassung (Liste aus (Tag, Text); Tags: h, ok, warn, bad, info)
# --------------------------------------------------------------------------
def _mmss(s):
    return "–" if not np.isfinite(s) else f"{int(s // 60)}:{int(s % 60):02d} min"


def _window_change(df, col, k):
    v = df[col].to_numpy(dtype=float)
    v = v[np.isfinite(v)]
    if len(v) < 4:
        return None
    return float(np.median(v[:k])), float(np.median(v[-k:]))


def soc_lines(r, meta):
    """Zeilen zum Ladezustand eines Fluges (Zusammenfassung und Einzelflug)."""
    L = []
    q = r["SoC_ende_Q_pct"]
    if np.isfinite(q):
        tag = "bad" if q < 5 else ("warn" if q < 20 else "info")
        L.append((tag, f"Ladezustand: Start ≈ {_f(r['SoC_start_pct'])} %, Ende ≈ {q:.0f} %  "
                       f"(Ladungszählung: {r['entnommen_mAh']:.0f} mAh entnommen von {meta['cap_ref']:.0f} mAh "
                       f"{meta['cap_src']})"))
        txt = (f"  Gegenprobe Ruhespannung: {_f(r['U_start_Zelle_V'], '{:.2f}')} → "
               f"{_f(r['U_ende_Zelle_V'], '{:.2f}')} V/Zelle ({r['U_ende_Quelle']}) ≙ {_f(r['SoC_ende_U_pct'])} %")
        if np.isfinite(r["SoC_Abw_pct"]) and abs(r["SoC_Abw_pct"]) > SOC_TOL_PCT:
            L.append(("warn", txt + f" - passt nicht zur entnommenen Ladung ({r['SoC_Abw_pct']:+.0f} Pkt.), verworfen"))
        else:
            L.append(("info", txt + " - passt"))
    else:
        L.append(("warn", f"Ladezustand: Start ≈ {_f(r['SoC_start_pct'])} %, Ende ≈ {_f(r['SoC_ende_U_pct'])} % "
                          f"nur aus Ruhespannung ({_f(r['U_ende_Zelle_V'], '{:.2f}')} V/Zelle, {r['U_ende_Quelle']}) - "
                          "ohne Gegenprobe. Nennkapazität eintragen für die Ladungszählung."))
    return L


def summary_lines(res, p):
    df, meta = res.df, res.meta
    L = []
    if df.empty:
        return [("bad", "Keine auswertbaren Flüge gefunden.")]
    n = len(df)
    ch = CHEM[p.chem]
    cells = meta["cells"]
    x = df["Flug"].to_numpy(dtype=float)
    k = max(1, min(3, n // 3))
    last = df.iloc[-1]

    L.append(("h", "ÜBERSICHT"))
    L.append(("info", f"{n} Flüge ausgewertet ({df['datum'].min():%d.%m.%Y} – {df['datum'].max():%d.%m.%Y}), "
                      f"{len(res.skipped)} Dateien übersprungen"))
    L.append(("info", f"Akku: {cells}S {p.chem}" + ("  (Zellenzahl automatisch erkannt)" if p.cells <= 0 else "")
             + (f", Nennkapazität {p.nominal_mah:.0f} mAh" if p.nominal_mah > 0 else "")))
    L.append(("info", f"Gesamt entnommen: {df['entnommen_mAh'].sum() / 1000:.1f} Ah"
                      + (f"  (≈ {df['Vollzyklen_kum'].iloc[-1]:.1f} Vollzyklen)" if np.isfinite(df['Vollzyklen_kum'].iloc[-1]) else "")))

    # ---------------- Akku ----------------
    L.append(("h", "AKKU ÜBER ALLE FLÜGE"))
    L.append(("info", "Details zu jedem einzelnen Flug (auch zum letzten) stehen im Reiter Einzelflug."))
    med = lambda c: float(df[c].median()) if df[c].notna().any() else np.nan
    L.append(("info", f"Typischer Flug (Median): {_mmss(med('dauer_s'))}, {_f(med('entnommen_mAh'))} mAh entnommen, "
                      f"Ladezustand am Ende ≈ {_f(med('SoC_ende_pct'))} %, Spitze {_f(med('I_max_A'))} A / "
                      f"{_f(med('P_max_W'))} W, min. {_f(med('U_min_Zelle_V'), '{:.2f}')} V/Zelle unter Last"))
    L.append(("info", f"Innenwiderstand je Zelle: Median {_f(med('Ri_Zelle_mOhm'), '{:.2f}')} mΩ, "
                      f"Spanne {_f(df['Ri_Zelle_mOhm'].min(), '{:.2f}')} – {_f(df['Ri_Zelle_mOhm'].max(), '{:.2f}')} mΩ"))
    fit = meta.get("chem_fit", {})
    if p.chem in fit:
        best = min(fit, key=fit.get)
        if fit[p.chem] > SOC_TOL_PCT and best != p.chem and fit[best] < 10:
            L.append(("bad", f"Zellchemie prüfen: Mit {p.chem} passen Ruhespannung und entnommene Ladung nicht zusammen "
                             f"(Abweichung im Median {fit[p.chem]:.0f} Prozentpunkte), mit {best} sehr gut "
                             f"({fit[best]:.0f} Pkt.). Ist der Akku ein {best}-Akku? Falls es wirklich {p.chem} ist, liefert "
                             f"er deutlich weniger als die eingetragenen {p.nominal_mah:.0f} mAh "
                             f"(geschätzt ca. {_f(meta['cap_est'])} mAh)."))
        elif fit[p.chem] <= SOC_TOL_PCT:
            L.append(("ok", f"Ruhespannung und entnommene Ladung passen zur Einstellung {p.chem} / "
                            f"{p.nominal_mah:.0f} mAh (Abweichung im Median {fit[p.chem]:.0f} Pkt.)."))
    elif p.nominal_mah <= 0:
        L.append(("warn", "Nennkapazität nicht eingetragen: Ladezustand und Timer beruhen nur auf der Spannungskennlinie."))

    # ---------------- Alterung ----------------
    L.append(("h", "ALTERUNG UND RESTKAPAZITÄT"))
    if n < 4:
        L.append(("warn", "Für Trend, Restkapazität (SoH) und Lebensdauer-Prognose werden mindestens 4 Flüge "
                          "mit gültigen Werten benötigt."))
    else:
        life = []
        cw = _window_change(df, "Kap_gesch_mAh", k)
        if cw:
            first, cur = cw
            soh = cur / first * 100
            tag = "ok" if soh >= 90 else ("warn" if soh >= 80 else "bad")
            fit = meta.get("chem_fit", {})
            shaky = p.chem in fit and fit[p.chem] > SOC_TOL_PCT
            L.append(("warn" if shaky else tag,
                      f"Restkapazität (SoH): ca. {soh:.0f} % der Anfangskapazität  ({first:.0f} → {cur:.0f} mAh)"
                      + ("  - unzuverlässig, solange die Zellchemie nicht passt (siehe oben)" if shaky else "")))
            if p.nominal_mah > 0:
                L.append(("info", f"  absolut: ca. {cur:.0f} mAh = {cur / p.nominal_mah * 100:.0f} % der Nennkapazität"))
            tr = _trend(x, df["Kap_gesch_mAh"].to_numpy(dtype=float))
            if tr and tr[0] < 0:
                fl = max((0.8 * first - (tr[0] * x[-1] + tr[1])) / tr[0], 0)
                life.append(fl)
                L.append(("info", f"  Prognose: 80 % SoH in ca. {fl:.0f} weiteren Flügen"))
        else:
            L.append(("warn", "Kapazitäts-SoH nicht bestimmbar: zu wenige Flüge mit ≥ 40 % Entladetiefe."))
        rw = _window_change(df, "Ri_Zelle_mOhm", k)
        if rw:
            r0, r1 = rw
            ch_pct = (r1 / r0 - 1) * 100
            tag = "ok" if ch_pct < 20 else ("warn" if ch_pct < 50 else "bad")
            L.append((tag, f"Innenwiderstand je Zelle: {r0:.2f} → {r1:.2f} mΩ ({ch_pct:+.0f} %)"))
            tr = _trend(x, df["Ri_Zelle_mOhm"].to_numpy(dtype=float))
            if tr and tr[0] > 0:
                fl = max((1.5 * r0 - (tr[0] * x[-1] + tr[1])) / tr[0], 0)
                life.append(fl)
                L.append(("info", f"  Prognose: +50 % Ri (Faustregel Lebensende) in ca. {fl:.0f} weiteren Flügen"))
        uw = _window_change(df, "U_ref_Zelle_V", k)
        if uw:
            L.append(("info", f"Spannung bei {meta['iref']:.0f} A / {meta['qref']:.0f} mAh: "
                              f"{uw[0]:.3f} → {uw[1]:.3f} V/Zelle ({(uw[1] - uw[0]) * 1000:+.0f} mV)"))
        if life:
            fl = min(life)
            avg = float(df["entnommen_mAh"].mean())
            cap = meta["cap_ref"]
            cyc = f", ≈ {fl * avg / cap:.0f} Vollzyklen" if np.isfinite(cap) and cap > 0 else ""
            L.append(("info", f"Restlebensdauer (früheres Kriterium): ca. {fl:.0f} Flüge{cyc}"))
        if meta["corr"]:
            L.append(("info", "Zusammenhang Nutzung ↔ Ri-Abweichung (Hinweis, keine Kausalität):"))
            for label, r in meta["corr"][:3]:
                L.append(("info", f"  {label}: r = {r:+.2f}"))

    # ---------------- Timer ----------------
    L.append(("h", "TIMER-EMPFEHLUNG"))
    if np.isfinite(meta["timer_s"]):
        L.append(("ok", f"Landung bei {p.reserve_pct:.0f} % Restkapazität: Timer ca. {_mmss(meta['timer_s'])} "
                        f"(Median der letzten Flüge; geflogen: {_mmss(float(df['dauer_s'].iloc[-5:].median()))})"))
        L.append(("info", f"Basis: Kapazität ≈ {meta['cap_timer']:.0f} mAh, Leistungsprofil der letzten Flüge."))
    else:
        L.append(("warn", "Nicht bestimmbar (Kapazität unbekannt: Nennkapazität eintragen oder Flüge mit ≥ 40 % Entladetiefe)."))

    # ---------------- Antrieb ----------------
    L.append(("h", "ANTRIEB UND SENSOREN"))
    pw = _window_change(df, "P_ref_W", k)
    if pw:
        d = (pw[1] / pw[0] - 1) * 100
        tag = "ok" if d < 5 else ("warn" if d < 10 else "bad")
        L.append((tag, f"Leistungsbedarf bei {meta['rpm_ref']:.0f} U/min: {pw[0]:.0f} → {pw[1]:.0f} W ({d:+.0f} %)"
                       + ("  - Anstieg kann auf Verschleiß/Lagerschaden/Fremdkörper hindeuten" if d >= 10 else "")))
    elif np.isfinite(meta["rpm_ref"]):
        L.append(("info", "Antriebs-Trend: ab 4 Flügen verfügbar."))
    else:
        L.append(("info", "Antriebs-Kennlinie nicht verfügbar (keine Drehzahl im Log)."))
    sd = df["Sensor_Abw_pct"].dropna()
    if len(sd):
        med = float(sd.median())
        L.append(("ok" if abs(med) <= 3 else "warn",
                  f"Strommessung vs. ESC-Zähler: Median {med:+.1f} % Abweichung"))

    # ---------------- Funk ----------------
    L.append(("h", "FUNK UND BORDNETZ (schlechtester Wert über alle Flüge)"))
    parts = []
    for col, lab, unit in [("RSSI_min", "RSSI", ""), ("VFR_min", "VFR", " %"), ("RxBatt_min_V", "Empfängerakku", " V"),
                           ("RxStrom_max_A", "Empfängerstrom max", " A"), ("TxBat_min_V", "Senderakku", " V")]:
        v = df[col].dropna()
        if len(v):
            val = v.max() if col == "RxStrom_max_A" else v.min()
            fl_no = int(df.loc[v.idxmax() if col == "RxStrom_max_A" else v.idxmin(), "Flug"])
            parts.append(f"{lab} {val:.4g}{unit} (Flug {fl_no})")
    L.append(("info", "; ".join(parts) if parts else "keine Funkwerte im Log"))
    if df["RxSpitzen_n"].notna().any():
        L.extend(rx_summary_lines(df))

    # ---------------- Warnungen ----------------
    L.append(("h", "WARNUNGEN UND AUFFÄLLIGKEITEN"))
    if meta["warnings"]:
        for tag, text in meta["warnings"][:60]:
            L.append((tag, "• " + text))
        if len(meta["warnings"]) > 60:
            L.append(("info", f"… und {len(meta['warnings']) - 60} weitere"))
    else:
        L.append(("ok", "Keine Auffälligkeiten festgestellt."
                        + (" (Ausreißer-Erkennung erst ab 6 Flügen aktiv.)" if n < 6 else "")))

    L.append(("h", "GRENZEN DER AUSWERTUNG"))
    for s in ["Ohne Temperaturdaten: Ri hängt stark von der Akku-Temperatur ab - kalte Flüge wirken schlechter, als der Akku ist.",
              "Keine Einzelzellspannungen: schwache Zellen/Balancing sind nicht erkennbar.",
              "Ladezustand am Ende: Ladungszählung, abhängig von der richtigen Nennkapazität bzw. Kapazitätsschätzung. "
              "Die Ruhespannung ist nur eine Gegenprobe (Näherungskennlinie, Akku erholt sich nach der Landung).",
              "Empfängerstrom-Spitzen: Zuordnung über Schalterbetätigung, Knüppelbewegung, Drehrate (Roll/Nick), "
              "G-Last, Flugzeit und Höhe - soweit diese Werte im Log stehen. Welcher Schalter z. B. das Fahrwerk "
              "schaltet, weiß die App nicht; sie nennt den Namen der Ethos-Quelle.",
              "Flugphasen und Wh je 100 m Steigen sind indikativ (Höhenwerte geglättet)."]:
        L.append(("info", "• " + s))
    if res.skipped:
        L.append(("h", "ÜBERSPRUNGENE DATEIEN"))
        for nme, msg in res.skipped[:40]:
            L.append(("info", f"• {nme}: {msg}"))
        if len(res.skipped) > 40:
            L.append(("info", f"… und {len(res.skipped) - 40} weitere"))
    return L


def rx_summary_lines(df):
    L = []
    base = df["RxStrom_mittel_A"].dropna()
    peak = df["RxStrom_max_A"].dropna()
    if len(base):
        L.append(("info", f"Empfängerstrom: Grundlast Ø {base.median():.2f} A (Median der Flüge)"
                          + (f", Spitzen bis {peak.max():.2f} A" if len(peak) else "")))
    tot = {c: int(np.nansum(df[col])) for (c, _), col in zip(SPIKE_CAUSES, SPIKE_COLS) if col in df.columns}
    n = sum(tot.values())
    if n:
        txt = ", ".join(f"{c} {v / n * 100:.0f} %" for c, v in tot.items() if v)
        share_ohne = tot.get("ohne erkennbaren Anlass", 0) / n
        L.append(("warn" if share_ohne > 0.3 and n >= 5 else "info",
                  f"Stromspitzen (alle Flüge): {n} - {txt}"))
    for col, label in [("Rx_r_Knueppel", "Knüppelaktivität"), ("Rx_r_Drehrate", "Drehrate")]:
        r = df[col].dropna() if col in df.columns else pd.Series(dtype=float)
        if len(r):
            med = float(r.median())
            interp = ("Strom folgt deutlich den Steuerausschlägen (Servolast)" if med >= 0.5 else
                      "mäßiger Zusammenhang mit den Steuerausschlägen" if med >= 0.3 else
                      "kaum Zusammenhang mit den Steuerausschlägen")
            L.append(("info", f"Zusammenhang Empfängerstrom ↔ {label}: r = {med:+.2f} (Median) - {interp}"))
            break
    return L


# --------------------------------------------------------------------------
#  Einzelflug: Detailbericht
# --------------------------------------------------------------------------
def flight_detail_lines(res, p, path):
    """Alle Detailwerte eines Fluges mit Vergleich zum Median aller Flüge."""
    df, meta = res.df, res.meta
    r = df[df["pfad"] == path].iloc[0]
    s = res.series[path]
    no = int(r["Flug"])
    ch = CHEM[p.chem]

    def cmp(col, fmt="{:.0f}", unit=""):
        v = r[col]
        med = df[col].median() if df[col].notna().any() else np.nan
        return f"{_f(v, fmt)}{unit} (Median {_f(med, fmt)}{unit})"

    L = [("h", f"Flug {no} – {r['datum']:%d.%m.%Y %H:%M} – {_mmss(r['dauer_s'])} – {r['entnommen_mAh']:.0f} mAh – "
               f"{r['datei']}")]

    # Warnungen zu diesem Flug zuerst
    own = [name for name, fl in meta["flags"].items() if no in fl]
    if own:
        L.append(("h", "AUFFÄLLIGKEITEN IN DIESEM FLUG"))
        for name in own:
            tag = "bad" if name in ("Tiefentladung", "Spannungseinbruch") else "warn"
            L.append((tag, f"• {name}"))

    L.append(("h", "AKKU"))
    if np.isfinite(r["Ri_mOhm"]):
        L.append(("info", f"Innenwiderstand je Zelle: {cmp('Ri_Zelle_mOhm', '{:.2f}', ' mΩ')}"))
        if np.isfinite(r["Ri_Anfang_mOhm"]) and np.isfinite(r["Ri_Ende_mOhm"]):
            L.append(("info", f"  im Flugverlauf: Anfang {r['Ri_Anf_Zelle_mOhm']:.2f} → Ende {r['Ri_End_Zelle_mOhm']:.2f} mΩ "
                              f"({(r['Ri_Ende_mOhm'] / r['Ri_Anfang_mOhm'] - 1) * 100:+.0f} %)"))
    else:
        L.append(("info", "Innenwiderstand: nicht bestimmbar (zu gleichmäßige Last)"))
    L += soc_lines(r, meta)
    if np.isfinite(r["Reserve_Zelle_V"]):
        tag = "ok" if r["Reserve_Zelle_V"] >= 0.05 else ("warn" if r["Reserve_Zelle_V"] >= 0 else "bad")
        L.append((tag, f"Reserve zur Mindest-Ruhespannung ({ch['rest_min']:.2f} V/Zelle): {r['Reserve_Zelle_V']:+.2f} V/Zelle"))
    if np.isfinite(r["Kap_gesch_mAh"]):
        L.append(("info", f"Geschätzte Gesamtkapazität: {cmp('Kap_gesch_mAh', unit=' mAh')}"))
    tag = "bad" if r["U_min_Zelle_V"] < ch["load_min"] else "info"
    L.append((tag, f"Minimale Spannung unter Last: {cmp('U_min_Zelle_V', '{:.2f}', ' V/Zelle')} bei {r['I_max_A']:.0f} A Spitze"))
    if np.isfinite(r["U_ref_Zelle_V"]):
        L.append(("info", f"Spannung bei {meta['iref']:.0f} A / {meta['qref']:.0f} mAh: {cmp('U_ref_Zelle_V', '{:.3f}', ' V/Zelle')}"))

    L.append(("h", "BELASTUNG UND FLUGPROFIL"))
    cp = f"C-Rate Spitze {cmp('C_peak', '{:.1f}', ' C')}, " if np.isfinite(r["C_peak"]) else ""
    L.append(("info", f"{cp}Spitzenleistung {cmp('P_max_W', unit=' W')}"))
    L.append(("info", f"Mittlere Leistung {cmp('P_mittel_W', unit=' W')}, {r['Zeit_80_s']:.0f} s über 80 % des Spitzenstroms, "
                      f"mittleres Gas {_f(r['Gas_mittel_pct'])} %"))
    if np.isfinite(r["E_steig_Wh"]):
        tot = r["E_steig_Wh"] + r["E_reise_Wh"] + r["E_sink_Wh"]
        L.append(("info", f"Energie nach Phase: Steigflug {r['E_steig_Wh']:.0f} Wh ({r['E_steig_Wh'] / tot * 100:.0f} %), "
                          f"Reise {r['E_reise_Wh']:.0f} Wh, Sinkflug {r['E_sink_Wh']:.0f} Wh"))
        L.append(("info", f"Max. Höhe {cmp('Hoehe_max_m', unit=' m')}"
                          + (f", {_f(r['Wh_je_100m'], '{:.1f}')} Wh je 100 m Steigen" if np.isfinite(r["Wh_je_100m"]) else "")))
    if np.isfinite(r["g_max"]):
        L.append(("info", f"G-Kräfte: max {cmp('g_max', '{:.1f}', ' g')}, 95. Perzentil {r['g_p95']:.1f} g"))

    L.append(("h", "TIMER"))
    if np.isfinite(r["Timer_s"]):
        diff = r["dauer_s"] - r["Timer_s"]
        tag = "warn" if diff > 15 else "ok"
        L.append((tag, f"Empfehlung für {p.reserve_pct:.0f} % Rest bei diesem Flugprofil: {_mmss(r['Timer_s'])}, "
                       f"geflogen {_mmss(r['dauer_s'])} "
                       + (f"({_mmss(diff)} länger als empfohlen)" if diff > 15 else "(innerhalb der Empfehlung)")))
    else:
        L.append(("info", "Keine Timer-Empfehlung (Kapazität unbekannt)."))

    L.append(("h", "ANTRIEB UND SENSOREN"))
    L.append(("info", f"Drehzahl (90. Perzentil): {cmp('rpm_p90', unit=' U/min')}"
                      + (f"; Leistung bei {meta['rpm_ref']:.0f} U/min: {cmp('P_ref_W', unit=' W')}" if np.isfinite(r["P_ref_W"]) else "")))
    if np.isfinite(r["Sensor_Abw_pct"]):
        tag = "ok" if abs(r["Sensor_Abw_pct"]) <= 5 else "warn"
        L.append((tag, f"Eigene mAh-Berechnung gegen ESC-Zähler: {r['entnommen_mAh']:.0f} gegen {r['ESC_mAh']:.0f} mAh "
                       f"({r['Sensor_Abw_pct']:+.1f} %)"))

    L.append(("h", "FUNK UND BORDNETZ"))
    L.append(("info", f"RSSI min. {cmp('RSSI_min')}, VFR min. {cmp('VFR_min', unit=' %')}"))
    L.append(("info", f"Empfängerakku min. {cmp('RxBatt_min_V', '{:.2f}', ' V')}, Senderakku min. {_f(r['TxBat_min_V'], '{:.2f}')} V"))
    rx = s.get("rx")
    if rx:
        L.append(("info", f"Empfängerstrom: Grundlast {rx['base']:.2f} A, Maximum {cmp('RxStrom_max_A', '{:.2f}', ' A')}, "
                          f"Spitzenschwelle {rx['thr']:.2f} A"))
        if rx["corr"]:
            L.append(("info", "Zusammenhang mit dem Empfängerstrom: "
                              + ", ".join(f"{k} r = {v:+.2f}" for k, v in rx["corr"].items())))
        L.append(("h", f"EMPFÄNGERSTROM-SPITZEN ({len(rx['spikes'])})"))
        if not rx["spikes"]:
            L.append(("ok", "Keine Spitzen über der Schwelle."))
        for sp in rx["spikes"]:
            tag = "warn" if sp["anlass"] == "ohne erkennbaren Anlass" else "info"
            why = sp["anlass"] + (f" ({sp['schalter']})" if sp["schalter"] else "")
            L.append((tag, f"  t = {sp['t']:6.1f} s  {sp['peak']:.2f} A, {sp['dauer']:.1f} s  →  {why}:  "
                           f"Knüppel {_f(sp['stick'])} %/s, Drehrate {_f(sp['rate'])} °/s, {_f(sp['g'], '{:.1f}')} g, "
                           f"Gas {_f(sp['gas'])} %, Höhe {_f(sp['alt'])} m"))
    else:
        L.append(("info", "Kein Empfängerstrom im Log."))
    sw = s.get("switches") or []
    if sw:
        L.append(("h", f"SCHALTERBETÄTIGUNGEN ({len(sw)})"))
        txt = "; ".join(f"{t_:.0f} s {name} {a:+.0f}→{b:+.0f}" for t_, name, a, b in sw[:40])
        L.append(("info", txt + (" …" if len(sw) > 40 else "")))
    return L


# --------------------------------------------------------------------------
#  Diagramme: gemeinsame Gestaltung
# --------------------------------------------------------------------------
def _style_mpl():
    import matplotlib as mpl
    mpl.rcParams.update({
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "lines.linewidth": 1.4,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3,
        "axes.titleweight": "bold", "axes.titlelocation": "left",
    })


def _new_fig(rows, cols, size=(11, 8)):
    from matplotlib.figure import Figure
    _style_mpl()
    fig = Figure(figsize=size, dpi=100, layout="constrained")
    fig.get_layout_engine().set(h_pad=0.08, hspace=0.06)
    axes = fig.subplots(rows, cols, squeeze=False)
    return fig, axes


def _empty_fig(text):
    from matplotlib.figure import Figure
    fig = Figure(figsize=(8, 5), dpi=100)
    fig.text(0.5, 0.5, text, ha="center", va="center", fontsize=12)
    return fig


def _note(ax, text):
    """Kurze Erklärung unter dem Diagrammtitel: was man sieht und was gut ist."""
    if text:
        ax.text(0, 1.012, text, transform=ax.transAxes, fontsize=7.5, color="#555555", va="bottom", ha="left")
        ax.set_title(ax.get_title(loc="left"), loc="left", pad=14)


def _bottom_labels_only(ax):
    """x-Beschriftung nur in der untersten Zeile - sonst ragt sie in den Titel darunter."""
    for row in ax[:-1]:
        for a in row:
            a.set_xlabel("")


def _legend(*axes, loc="best", ncol=1):
    """Eine gemeinsame Legende für Diagramme mit zweiter y-Achse."""
    h, l = [], []
    for a in axes:
        hh, ll = a.get_legend_handles_labels()
        h += hh
        l += ll
    if h:
        axes[0].legend(h, l, fontsize=7, loc=loc, ncol=ncol, framealpha=0.85)


def _axis_color(a, color, label, side="left"):
    a.set_ylabel(label, color=color, fontsize=8)
    a.tick_params(axis="y", colors=color, labelsize=8)


def _plot_trend(ax, df, col, color, title, flags=None, flag_label=None, hlines=(), label=None, trend=True, marker="o",
                note=None):
    x = df["Flug"].to_numpy(dtype=float)
    y = df[col].to_numpy(dtype=float)
    good = np.isfinite(y)
    if not good.any():
        ax.text(0.5, 0.5, "keine Daten", transform=ax.transAxes, ha="center", va="center", color="grey")
    else:
        ax.plot(x[good], y[good], marker, ms=5, color=color, label=label, ls="none")
        if trend:
            tr = _trend(x, y)
            if tr:
                ax.plot(x, tr[0] * x + tr[1], "-", color=color, alpha=0.5, lw=1.5)
        if flags and flag_label in flags:
            sel = np.isin(x, list(flags[flag_label])) & good
            ax.plot(x[sel], y[sel], "o", ms=12, mfc="none", mec="red", mew=1.5)
    for val, txt, c in hlines:
        ax.axhline(val, color=c, ls="--", lw=1)
        ax.text(0.01, val, txt, transform=ax.get_yaxis_transform(), fontsize=8, color=c, va="bottom")
    ax.set_title(title, loc="left")
    ax.set_xlabel("Flug Nr.", fontsize=8)
    _note(ax, note)


FLAG_NOTE = " Rot umkreist: auffälliger Flug."


def figure_akku(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig("Keine Daten")
    ch = CHEM[p.chem]
    fl = meta["flags"]
    fig, ax = _new_fig(3, 2, size=(11, 9))
    h = []
    if p.nominal_mah > 0:
        h.append((p.nominal_mah, "Nennkapazität", "grey"))
    kv = df["Kap_gesch_mAh"].dropna()
    if len(kv) >= 4:
        ref = float(np.median(kv.iloc[:max(1, min(3, len(kv) // 3))]))
        h.append((0.8 * ref, "80 % der Anfangskapazität", "tab:red"))
    _plot_trend(ax[0][0], df, "Kap_gesch_mAh", "tab:green", "Geschätzte Gesamtkapazität [mAh]", fl, "geschätzte Kapazität", h,
                note="Aus entnommener Ladung und Spannungsabfall. Fallender Trend = Alterung." + FLAG_NOTE)
    a = ax[0][1]
    _plot_trend(a, df, "Ri_Zelle_mOhm", "tab:red", "Innenwiderstand je Zelle [mΩ]", fl, "Innenwiderstand", label="Ø Flug",
                note="Steigender Trend = Alterung; +50 % gilt als Lebensende.")
    _plot_trend(a, df, "Ri_Anf_Zelle_mOhm", "tab:orange", "Innenwiderstand je Zelle [mΩ]", label="Flugbeginn", trend=False, marker="^")
    _plot_trend(a, df, "Ri_End_Zelle_mOhm", "tab:purple", "Innenwiderstand je Zelle [mΩ]", label="Flugende", trend=False, marker="v")
    a.legend(fontsize=7)
    _plot_trend(ax[1][0], df, "U_ref_Zelle_V", "tab:blue",
                f"Spannung bei {meta['iref']:.0f} A und {meta['qref']:.0f} mAh [V/Zelle]", fl, "Spannung bei Referenzlast",
                note="Vergleich unter gleichen Bedingungen. Fallender Trend = Akku wird schwächer.")
    a = ax[1][1]
    _plot_trend(a, df, "U_start_Zelle_V", "tab:blue", "Ruhespannung Start / Ende [V/Zelle]", label="Start", trend=False,
                note="Start: voll geladen? Ende: sollte über der roten Linie liegen.")
    _plot_trend(a, df, "U_ende_Zelle_V", "tab:orange", "Ruhespannung Start / Ende [V/Zelle]", fl,
                "Ladezustand unplausibel", label="Ende (rot umkreist: passt nicht zur Ladung)",
                trend=False, hlines=[(ch["rest_min"], "Mindestwert", "tab:red")])
    a.legend(fontsize=7)
    a = ax[2][0]
    _plot_trend(a, df, "SoC_start_pct", "tab:blue", "Ladezustand Start / Ende [%]", label="Start", trend=False,
                note="Ende sollte über der Reserve-Linie liegen." + FLAG_NOTE)
    _plot_trend(a, df, "SoC_ende_pct", "tab:orange", "Ladezustand Start / Ende [%]", fl, "Tiefentladung",
                label="Ende (Ladungszählung)", trend=False, hlines=[(p.reserve_pct, "Reserve", "tab:red")])
    if df["SoC_ende_Q_pct"].notna().any():
        _plot_trend(a, df, "SoC_ende_U_pct", "grey", "Ladezustand Start / Ende [%]", label="Ende (aus Spannung)",
                    trend=False, marker="x")
    a.legend(fontsize=7)
    _plot_trend(ax[2][1], df, "U_min_Zelle_V", "tab:purple", "Min. Spannung unter Last [V/Zelle]", trend=True,
                hlines=[(ch["load_min"], "Grenze", "tab:red")],
                note="Tiefster Spannungseinbruch bei Volllast. Unter der roten Linie: Zellen überlastet.")
    _bottom_labels_only(ax)
    fig.suptitle("Akku-Zustand und Alterung", fontsize=12, fontweight="bold")
    return fig


def figure_belastung(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig("Keine Daten")
    fig, ax = _new_fig(3, 2, size=(11, 9))
    a = ax[0][0]
    hists = [res.series[r["pfad"]]["gas_hist"] for _, r in df.iterrows() if res.series[r["pfad"]]["gas_hist"] is not None]
    if hists:
        tot = np.sum(hists, axis=0)
        centers = np.arange(5, 100, 10)
        a.bar(centers, tot / tot.sum() * 100, width=8, color="tab:blue", alpha=0.6, label="alle Flüge")
        lastr = hists[-1]
        a.step(np.arange(0, 101, 10), np.append(lastr, lastr[-1]) / lastr.sum() * 100, where="post",
               color="tab:red", lw=1.5, label="letzter Flug")
        a.legend(fontsize=7)
        a.set_ylabel("Zeitanteil [%]", fontsize=8)
    else:
        a.text(0.5, 0.5, "kein Gaskanal im Log", transform=a.transAxes, ha="center", color="grey")
    a.set_title("Gas-Histogramm", loc="left")
    _note(a, "Wie viel Prozent der Flugzeit bei welcher Gasstellung geflogen wurde.")
    a.set_xlabel("Gas [%]", fontsize=8)
    _plot_trend(ax[0][1], df, "C_peak", "tab:red", "Spitzen-C-Rate je Flug [C]", trend=False,
                note="Höchster Strom geteilt durch Kapazität. Dauerhaft hohe Werte altern den Akku schneller.")
    a = ax[1][0]
    xx = df["Flug"].to_numpy(dtype=float)
    if df["E_steig_Wh"].notna().any():
        e1, e2, e3 = (np.nan_to_num(df[c].to_numpy(dtype=float)) for c in ("E_steig_Wh", "E_reise_Wh", "E_sink_Wh"))
        a.bar(xx, e1, color="tab:red", label="Steigflug")
        a.bar(xx, e2, bottom=e1, color="tab:blue", label="Reise")
        a.bar(xx, e3, bottom=e1 + e2, color="tab:green", label="Sinkflug")
        a.legend(fontsize=7)
    else:
        a.text(0.5, 0.5, "keine Höhe im Log", transform=a.transAxes, ha="center", color="grey")
    a.set_title("Energie je Flugphase [Wh]", loc="left")
    _note(a, "Wofür die Energie verbraucht wurde (aus Höhenänderung).")
    a.set_xlabel("Flug Nr.", fontsize=8)
    _plot_trend(ax[1][1], df, "P_max_W", "tab:blue", "Spitzenleistung je Flug [W]", trend=False,
                note="Höchste elektrische Leistung (Spannung × Strom).")
    a = ax[2][0]
    _plot_trend(a, df, "g_max", "tab:red", "G-Kräfte [g]", label="max", trend=False,
                note="Maß für die Härte der Flugmanöver.")
    _plot_trend(a, df, "g_p95", "tab:blue", "G-Kräfte [g]", label="95. Perzentil", trend=False, marker="s")
    a.legend(fontsize=7)
    a = ax[2][1]
    a.bar(df["Flug"], df["dauer_s"], color="tab:blue", alpha=0.5, label="Flugzeit")
    a.plot(df["Flug"], df["Timer_s"], "o", color="tab:red", ms=5, label=f"Timer für {p.reserve_pct:.0f} % Rest")
    a.legend(fontsize=7)
    a.set_title("Flugzeit und Timer-Empfehlung [s]", loc="left")
    _note(a, "Balken über dem roten Punkt: länger geflogen als für die Reserve empfohlen.")
    a.set_xlabel("Flug Nr.", fontsize=8)
    _bottom_labels_only(ax)
    fig.suptitle("Belastung und Flugprofil", fontsize=12, fontweight="bold")
    return fig


def figure_antrieb(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig("Keine Daten")
    fig, ax = _new_fig(2, 2, size=(11, 8))
    a = ax[0][0]
    n = len(df)
    import matplotlib
    cm = matplotlib.colormaps["viridis"]
    have = False
    for k, (_, r) in enumerate(df.iterrows()):
        s = res.series[r["pfad"]]
        if s["rpm"] is None:
            continue
        have = True
        c = cm(k / max(n - 1, 1))
        m = (s["rpm"] > 1000) & (s["p"] > 100)
        a.plot(s["rpm"][m][::3] / 1000, s["p"][m][::3] / 1000, ".", ms=2, color=c, alpha=0.5)
        if np.isfinite(r["P_n"]):
            rr = np.linspace(max(s["rpm"][m].min(), 1000) if m.any() else 1000, np.max(s["rpm"]), 50)
            a.plot(rr / 1000, np.exp(r["P_a"] + r["P_n"] * np.log(rr)) / 1000, "-", color=c, lw=1.2)
    if not have:
        a.text(0.5, 0.5, "keine Drehzahl im Log", transform=a.transAxes, ha="center", color="grey")
    a.set_title("Kennlinie: Leistung gegen Drehzahl", loc="left")
    _note(a, "Farbe: frühe Flüge violett → späte gelb. Wandert die Kurve nach oben: Verschleiß/Fremdkörper.")
    a.set_xlabel("Drehzahl [1000 U/min]", fontsize=8)
    a.set_ylabel("Leistung [kW]", fontsize=8)
    rr_txt = f"{meta['rpm_ref']:.0f}" if np.isfinite(meta["rpm_ref"]) else "–"
    _plot_trend(ax[0][1], df, "P_ref_W", "tab:red", f"Leistungsbedarf bei {rr_txt} U/min [W]", meta["flags"],
                "Antriebsleistung bei Referenzdrehzahl",
                note="Steigt der Bedarf bei gleicher Drehzahl, läuft der Antrieb schwerer.")
    _plot_trend(ax[1][0], df, "rpm_p90", "tab:blue", "Drehzahl, 90. Perzentil [U/min]",
                note="Typische Höchstdrehzahl im Flug. Fallender Trend: Akku oder Antrieb lassen nach.")
    a = ax[1][1]
    _plot_trend(a, df, "Sensor_Abw_pct", "tab:purple", "Plausibilität: eigene mAh-Berechnung gegen ESC-Zähler [%]",
                meta["flags"], "Abweichung Strommessung/ESC-Zähler",
                hlines=[(5, "+5 %", "tab:red"), (-5, "-5 %", "tab:red")], trend=False,
                note="Innerhalb ±5 %: Verbrauchswerte verlässlich (Grundlage für Ladezustand und Timer).")
    sd = df["Sensor_Abw_pct"].dropna()
    if len(sd):
        med = float(sd.median())
        a.axhline(med, color="tab:purple", lw=1, alpha=0.6)
        ok = abs(med) <= 5
        a.text(0.99, 0.95, f"Median {med:+.1f} % – {'verlässlich' if ok else 'Sensor prüfen'}", transform=a.transAxes,
               ha="right", va="top", fontsize=9, color="#1b7f3b" if ok else "#b00020", fontweight="bold")
        a.set_ylim(min(-6.5, sd.min() - 1), max(6.5, sd.max() + 1))
    _bottom_labels_only(ax)
    fig.suptitle("Antrieb und Sensor-Plausibilität", fontsize=12, fontweight="bold")
    return fig


def figure_funk(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig("Keine Daten")
    fig, ax = _new_fig(3, 2, size=(11, 9))
    fl = meta["flags"]
    _plot_trend(ax[0][0], df, "RSSI_min", "tab:blue", "RSSI-Minimum im Flug", fl, "RSSI-Minimum", trend=False,
                note="Schlechteste Empfangsstärke je Flug. Ethos warnt üblicherweise unter 45." + FLAG_NOTE)
    _plot_trend(ax[0][1], df, "VFR_min", "tab:green", "VFR-Minimum im Flug [%]", fl, "VFR-Minimum", trend=False,
                note="Anteil korrekt empfangener Telemetrie-Rahmen. Unter ca. 80 % wird es kritisch.")
    _plot_trend(ax[1][0], df, "RxBatt_min_V", "tab:orange", "Empfängerakku: Minimum im Flug [V]",
                fl, "Empfängerspannung", trend=False,
                note="Tiefster Wert der Empfängerversorgung. Einbrüche deuten auf Akku, Kabel oder Servolast." + FLAG_NOTE)
    a = ax[1][1]
    _plot_trend(a, df, "RxStrom_max_A", "tab:red", "Empfängerstrom [A]", fl, "Empfängerstrom-Maximum",
                label="Maximum", trend=False, marker="s", note="Grundlast (grau) und Spitzen (rot) der Servoversorgung.")
    _plot_trend(a, df, "RxStrom_mittel_A", "grey", "Empfängerstrom [A]", label="Mittelwert", trend=False)
    a.legend(fontsize=7)
    a = ax[2][0]
    xx = df["Flug"].to_numpy(dtype=float)
    if df["RxSpitzen_n"].notna().any():
        bottom = np.zeros(len(df))
        for (cause, color), col in zip(SPIKE_CAUSES, SPIKE_COLS):
            if col not in df.columns:
                continue
            v = np.nan_to_num(df[col].to_numpy(dtype=float))
            if v.any():
                a.bar(xx, v, bottom=bottom, color=color, alpha=0.8 if color != "black" else 0.6, label=cause)
                bottom += v
        a.legend(fontsize=7)
    else:
        a.text(0.5, 0.5, "kein Empfängerstrom im Log", transform=a.transAxes, ha="center", color="grey")
    a.set_title("Empfängerstrom-Spitzen je Flug nach Anlass", loc="left")
    _note(a, "Schwarz = ohne erkennbaren Anlass: Servos prüfen. Details im Reiter Einzelflug.")
    a.set_xlabel("Flug Nr.", fontsize=8)
    _plot_trend(ax[2][1], df, "TxBat_min_V", "tab:purple", "Senderakku min. [V]", trend=False,
                note="Tiefster Wert des Senderakkus im Flug.")
    _bottom_labels_only(ax)
    fig.suptitle("Funk und Bordnetz", fontsize=12, fontweight="bold")
    return fig


# --------------------------------------------------------------------------
#  Einzelflug: Zeitverläufe in Ansichten mit je höchstens 4 Diagrammen
# --------------------------------------------------------------------------
FLIGHT_VIEWS = ["Akku & Antrieb", "Empfang", "Empfängerstrom & Steuerung", "Fluglage"]


def _flight_panels(s, view):
    """Liste von Diagrammen: dict(title, unit, note, lines=[(label, y, color, kw)], extra)."""
    rx = s.get("rx")
    P = []
    add = lambda title, unit, note, lines, **kw: P.append(dict(title=title, unit=unit, note=note,
                                                               lines=[l for l in lines if l[1] is not None], **kw))
    if view == FLIGHT_VIEWS[0]:
        add("Akkuspannung", "V", "Gestrichelt: geschätzte Spannung ohne Last. Abstand = Spannungsabfall durch den Innenwiderstand.",
            [("Spannung", s["u"], "tab:blue", {}), ("Ruhespannung (geschätzt)", s["ocv"], "grey", {"ls": "--"})])
        add("Akkustrom", "A", "Strom aus dem Flugakku.", [("Strom", s["i"], "tab:red", {})])
        add("Drehzahl", "1000 U/min", "Drehzahl des Antriebs.",
            [("Drehzahl", s["rpm"] / 1000 if s["rpm"] is not None else None, "tab:purple", {})])
        add("Höhe", "m", "Relative Höhe über dem Startpunkt.", [("Höhe", s["alt"], "tab:brown", {})])
    elif view == FLIGHT_VIEWS[1]:
        add("Empfangsstärke (RSSI)", "dB", "Ethos warnt üblicherweise unter 45.", [("RSSI", s.get("rssi"), "tab:blue", {})])
        add("Telemetrie-Rahmen (VFR)", "%", "Anteil korrekt empfangener Rahmen. Einbrüche = Empfangsstörung.",
            [("VFR", s.get("vfr"), "tab:green", {})])
        add("Höhe", "m", "Zum Abgleich: Einbrüche bei großer Höhe/Entfernung oder in bestimmten Fluglagen?",
            [("Höhe", s["alt"], "tab:brown", {})])
    elif view == FLIGHT_VIEWS[2]:
        add("Empfängerstrom", "A", "Dreiecke: Spitzen über der gestrichelten Schwelle, Farbe = Anlass.",
            [("Empfängerstrom", rx["rs"] if rx else s.get("rxi"), "tab:red", {})], spikes=True)
        sticks = s.get("sticks") or {}
        add("Knüppelwege", "%", "Schnelle, große Ausschläge erzeugen Servolast. Senkrechte Linien: Schalter.",
            [(k, v, c, {"lw": 1.1}) for (k, v), c in zip(sticks.items(), ["tab:blue", "tab:orange", "tab:green"])],
            switches=True)
        add("Gas", "%", "Gasknüppel.", [("Gas", s["gas"], "tab:green", {})])
        add("Empfängerspannung", "V", "Bricht sie bei Stromspitzen ein, ist die Versorgung zu schwach.",
            [("Empfängerspannung", s.get("rxu"), "tab:orange", {})])
    else:
        add("Fluglage", "°", "Roll- und Nickwinkel.",
            [("Roll", s.get("roll"), "tab:blue", {}), ("Nick", s.get("pitch"), "tab:orange", {})])
        add("Drehrate", "°/s", "Wie schnell sich die Lage ändert (aus Roll und Nick).",
            [("Drehrate", s.get("rate"), "tab:purple", {})])
        add("G-Last", "g", "Beschleunigung, 1 g = Geradeausflug.", [("G-Last", s.get("g"), "tab:brown", {})])
        add("Höhe", "m", "Relative Höhe über dem Startpunkt.", [("Höhe", s["alt"], "tab:brown", {})])
    return [pp for pp in P if pp["lines"]]


def draw_flight(fig, res, p, path, view=FLIGHT_VIEWS[0]):
    """Zeichnet die gewählte Ansicht eines Fluges in fig. Gibt die Achsen zurück (für Zoom/Fadenkreuz)."""
    _style_mpl()
    fig.clear()
    fig.set_layout_engine("constrained")
    df = res.df
    r = df[df["pfad"] == path].iloc[0]
    s = res.series[path]
    t = s["t"]
    panels = _flight_panels(s, view)
    ri = f"Ri {r['Ri_Zelle_mOhm']:.2f} mΩ/Zelle" if np.isfinite(r["Ri_Zelle_mOhm"]) else "Ri n/a"
    fig.suptitle(f"Flug {int(r['Flug'])} – {r['datum']:%d.%m.%Y %H:%M} – {_mmss(r['dauer_s'])} – "
                 f"{r['entnommen_mAh']:.0f} mAh – {ri}", fontsize=11, fontweight="bold")
    fig._readout = []
    if not panels:
        fig.text(0.5, 0.5, "Für diese Ansicht sind keine Daten im Log.", ha="center", va="center", color="grey", fontsize=12)
        return []
    axes = fig.subplots(len(panels), 1, sharex=True, squeeze=False)[:, 0]
    rx = s.get("rx")
    for a, pn in zip(axes, panels):
        for label, y, color, kw in pn["lines"]:
            a.plot(t, y, color=color, label=label, gid="data", **kw)
            fig._readout.append((label, pn["unit"], y))
        a.set_ylabel(pn["unit"])
        a.set_title(pn["title"], loc="left")
        _note(a, pn["note"])
        if pn.get("spikes") and rx:
            a.axhline(rx["thr"], color="tab:red", ls="--", lw=0.9, label=f"Spitzenschwelle {rx['thr']:.2f} A")
            if s.get("rxi") is not None:
                a.plot(t, s["rxi"], color="tab:red", lw=0.6, alpha=0.25)
            for cause, color in SPIKE_CAUSES:
                pts = [sp for sp in rx["spikes"] if sp["anlass"] == cause]
                if pts:
                    a.plot([sp["t"] for sp in pts], [sp["peak"] for sp in pts], "v", ms=9, color=color,
                           label=f"Spitze: {cause}", ls="none")
        if pn.get("switches"):
            groups = []                                   # Schalter innerhalb von 2 s zusammenfassen
            for t_, name, _, _ in s.get("switches") or []:
                if groups and t_ - groups[-1][0] < 2.0:
                    groups[-1][1].add(name)
                else:
                    groups.append([t_, {name}])
            for t_, names in groups:
                a.axvline(t_, color="tab:green", lw=0.9, ls=":", alpha=0.9)
                a.text(t_, 0.99, " " + "/".join(sorted(names)), transform=a.get_xaxis_transform(), fontsize=7,
                       color="#1b6e1b", rotation=90, va="top", ha="left", clip_on=True, in_layout=False)
        a.legend(loc="upper left", bbox_to_anchor=(1.005, 1.0), frameon=False, fontsize=8)
    if view in (FLIGHT_VIEWS[2], FLIGHT_VIEWS[3]) and rx:
        for sp in rx["spikes"]:
            for a in axes:
                a.axvline(sp["t"], color=SPIKE_COLOR[sp["anlass"]], lw=0.8, alpha=0.35)
    if view == FLIGHT_VIEWS[0] and np.isfinite(r["Timer_s"]) and r["Timer_s"] <= t[-1]:
        for a in axes:
            a.axvline(r["Timer_s"], color="tab:red", ls=":", lw=1.2)
        axes[0].text(r["Timer_s"], 0.02, " Timer-Empfehlung", transform=axes[0].get_xaxis_transform(),
                     color="tab:red", fontsize=8, va="bottom", clip_on=True, in_layout=False)
    # Zusatzwerte für das Fadenkreuz
    extra = [("entnommen", "mAh", s["q"]), ("Leistung", "kW", s["p"] / 1000)]
    if view != FLIGHT_VIEWS[2] and s["gas"] is not None:
        extra.append(("Gas", "%", s["gas"]))
    fig._readout += extra
    fig._t = t
    axes[-1].set_xlabel("Zeit seit Motorstart [s]")
    axes[-1].set_xlim(t[0], t[-1])
    return list(axes)


def figure_flight(res, p, path, view=FLIGHT_VIEWS[0]):
    """Einzelflug als eigenständige Figure (für den Export)."""
    from matplotlib.figure import Figure
    fig = Figure(figsize=(12, 8.5), dpi=100)
    draw_flight(fig, res, p, path, view)
    return fig


# --------------------------------------------------------------------------
#  Tabelle
# --------------------------------------------------------------------------
TABLE_COLS = [
    ("Flug", "Flug", 45), ("datum", "Datum", 120), ("dauer_s", "Dauer s", 60), ("entnommen_mAh", "entnommen mAh", 90),
    ("ESC_mAh", "ESC mAh", 65), ("Sensor_Abw_pct", "Abw. %", 55), ("energie_Wh", "Energie Wh", 75),
    ("I_mittel_A", "Ø A", 50), ("I_max_A", "max A", 55), ("P_max_W", "P max W", 65), ("C_peak", "C Spitze", 60),
    ("SoC_start_pct", "SoC Start %", 75), ("SoC_ende_pct", "SoC Ende %", 75), ("SoC_ende_U_pct", "SoC Ende (U) %", 90),
    ("SoC_Abw_pct", "SoC Abw. Pkt", 80), ("Kap_gesch_mAh", "Kapazität mAh", 90),
    ("Ri_Zelle_mOhm", "Ri/Zelle mΩ", 80), ("Ri_Anf_Zelle_mOhm", "Ri Anfang", 70), ("Ri_End_Zelle_mOhm", "Ri Ende", 65),
    ("U_ref_Zelle_V", "U Ref V/Z", 70), ("U_min_Zelle_V", "U min V/Z", 70), ("U_ende_Zelle_V", "U Ende V/Z", 75),
    ("U_ende_Quelle", "U Ende Quelle", 85), ("Reserve_Zelle_V", "Reserve V/Z", 80), ("Timer_s", "Timer s", 55),
    ("rpm_p90", "rpm P90", 70), ("P_ref_W", "P Ref W", 65), ("Hoehe_max_m", "Höhe max", 65), ("Wh_je_100m", "Wh/100m", 65),
    ("g_max", "g max", 50), ("RSSI_min", "RSSI min", 65), ("VFR_min", "VFR min", 60), ("RxBatt_min_V", "Rx V min", 65),
    ("RxStrom_mittel_A", "Rx A Ø", 55), ("RxStrom_max_A", "Rx A max", 65), ("RxSpitzen_n", "Rx Spitzen", 70),
    ("RxSp_Schalter", "Sp. Schalter", 80), ("RxSp_ohne", "Sp. o. Anlass", 85), ("Rx_r_Knueppel", "r Rx/Knüppel", 85),
    ("fit_R2", "R² Fit", 50), ("versatz_s", "Versatz s", 60), ("Auffaellig", "Auffälligkeiten", 260),
]


def fmt_cell(key, v):
    if key == "datum":
        return f"{v:%d.%m.%Y %H:%M}"
    if isinstance(v, (float, np.floating)):
        return "–" if not np.isfinite(v) else f"{v:.5g}"
    return "" if v is None else str(v)


# --------------------------------------------------------------------------
#  Einstellungen speichern
# --------------------------------------------------------------------------
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".akku_analyse.json")


def load_settings():
    import json
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_settings(d):
    import json
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1)
    except Exception:
        pass


# --------------------------------------------------------------------------
#  GUI
# --------------------------------------------------------------------------
ACCENT = "#1f5fa8"
BG = "#f4f6f9"


def _setup_style(root):
    from tkinter import ttk, font as tkfont
    st = ttk.Style(root)
    st.theme_use("clam")
    base = tkfont.nametofont("TkDefaultFont")
    base.configure(size=10)
    fam = base.actual("family")
    st.configure(".", background=BG, font=(fam, 10))
    st.configure("TFrame", background=BG)
    st.configure("TLabel", background=BG)
    st.configure("TLabelframe", background=BG, bordercolor="#c9d1dc")
    st.configure("TLabelframe.Label", background=BG, foreground=ACCENT, font=(fam, 10, "bold"))
    st.configure("Status.TLabel", background="#e3e9f2", foreground="#1f3b73", padding=(10, 4), font=(fam, 9))
    st.configure("Readout.TLabel", background="#ffffff", foreground="#222", padding=(8, 3), font=(fam, 9))
    # Reiter: klar abgegrenzt, aktiver Reiter farbig und fett
    st.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(8, 6, 8, 0))
    st.configure("TNotebook.Tab", padding=(16, 7), background="#dde3ec", foreground="#3a4656",
                 bordercolor="#b7c2d1", lightcolor="#dde3ec", font=(fam, 10))
    st.map("TNotebook.Tab",
           background=[("selected", ACCENT), ("active", "#c5d3e8")],
           foreground=[("selected", "#ffffff")],
           lightcolor=[("selected", ACCENT)],
           font=[("selected", (fam, 10, "bold"))],
           expand=[("selected", (2, 3, 2, 0))])
    st.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", padding=(14, 6), font=(fam, 10, "bold"))
    st.map("Accent.TButton", background=[("active", "#174a85"), ("disabled", "#9fb3cc")])
    st.configure("TButton", padding=(10, 4))
    st.configure("View.TRadiobutton", padding=(10, 4), background="#dde3ec", indicatorsize=0)
    st.map("View.TRadiobutton", background=[("selected", ACCENT), ("active", "#c5d3e8")],
           foreground=[("selected", "#ffffff")])
    st.configure("Treeview", rowheight=22)
    st.configure("Treeview.Heading", font=(fam, 9, "bold"))
    return fam


def run_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure

    try:                                         # scharfe Darstellung unter Windows
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.title("EthosLogAnalyser – Flug- und Akku-Analyse (FrSky Ethos Logs)")
    root.geometry("1400x950")
    root.configure(background=BG)
    fam = _setup_style(root)

    saved = load_settings()
    state = {"res": None, "p": None, "figs": {}, "path": None}
    folder_var = tk.StringVar(value=saved.get("folder", ""))
    V = {
        "chem": tk.StringVar(value=saved.get("chem", "LiPo")), "cells": tk.StringVar(value=saved.get("cells", "0")),
        "nominal_mah": tk.StringVar(value=saved.get("nominal_mah", "0")),
        "min_flight_s": tk.StringVar(value=saved.get("min_flight_s", "120")),
        "active_current_a": tk.StringVar(value=saved.get("active_current_a", "1.0")),
        "reserve_pct": tk.StringVar(value=saved.get("reserve_pct", "20")),
        "col_voltage": tk.StringVar(value=saved.get("col_voltage", "")),
        "col_current": tk.StringVar(value=saved.get("col_current", "")),
    }

    def store_settings():
        d = {k: v.get() for k, v in V.items()}
        d["folder"] = folder_var.get()
        save_settings(d)

    # ---------------- Statuszeile ----------------
    status = tk.StringVar(value="Noch nicht ausgewertet – Ordner und Akku im Reiter „Daten & Einstellungen“ festlegen.")
    ttk.Label(root, textvariable=status, style="Status.TLabel").pack(fill="x")

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=6, pady=(4, 6))
    tabs = {}
    for key, title in [("settings", "Daten & Einstellungen"), ("summary", "Zusammenfassung"), ("akku", "Akku"),
                       ("belastung", "Belastung & Flugprofil"), ("antrieb", "Antrieb"), ("funk", "Funk & Bordnetz"),
                       ("flight", "Einzelflug"), ("table", "Tabelle")]:
        fr = ttk.Frame(nb)
        nb.add(fr, text=title)
        tabs[key] = fr

    def make_text(parent, height=None):
        kw = dict(wrap="word", font=(fam, 10), padx=12, pady=8, relief="flat", background="#ffffff",
                  borderwidth=0, highlightthickness=0)
        if height:
            kw["height"] = height
        t_ = tk.Text(parent, **kw)
        t_.tag_configure("h", font=(fam, 11, "bold"), spacing1=10, spacing3=3, foreground="#1f3b73")
        t_.tag_configure("ok", foreground="#1b7f3b")
        t_.tag_configure("warn", foreground="#b36b00")
        t_.tag_configure("bad", foreground="#b00020")
        t_.tag_configure("info")
        return t_

    def fill_text(t_, lines):
        t_.configure(state="normal")
        t_.delete("1.0", "end")
        for tag, line in lines:
            t_.insert("end", line + "\n", tag)
        t_.configure(state="disabled")

    # ---------------- Reiter: Daten & Einstellungen ----------------
    st_tab = ttk.Frame(tabs["settings"], padding=14)
    st_tab.pack(fill="both", expand=True)
    st_tab.columnconfigure(0, weight=1)
    st_tab.columnconfigure(1, weight=1)

    lf = ttk.LabelFrame(st_tab, text="Logdaten", padding=10)
    lf.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 10))
    lf.columnconfigure(1, weight=1)
    ttk.Label(lf, text="Ordner mit Ethos-CSV-Logs (Unterordner werden mit durchsucht):").grid(row=0, column=0, columnspan=3, sticky="w")
    ttk.Button(lf, text="Ordner wählen …", command=lambda: choose()).grid(row=1, column=0, padx=(0, 8), pady=4)
    ttk.Entry(lf, textvariable=folder_var).grid(row=1, column=1, sticky="we", pady=4)
    run_btn = ttk.Button(lf, text="Auswerten", style="Accent.TButton", command=lambda: run())
    run_btn.grid(row=1, column=2, padx=(8, 0), pady=4)
    prog = ttk.Progressbar(lf, mode="determinate")
    prog.grid(row=2, column=0, columnspan=3, sticky="we", pady=(6, 0))

    def field(parent, row, label, key, hint="", combo=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        if combo:
            w = ttk.Combobox(parent, textvariable=V[key], values=combo, width=12, state="readonly")
        else:
            w = ttk.Entry(parent, textvariable=V[key], width=14)
        w.grid(row=row, column=1, sticky="w", padx=8, pady=3)
        if hint:
            ttk.Label(parent, text=hint, foreground="#666").grid(row=row, column=2, sticky="w")

    lf = ttk.LabelFrame(st_tab, text="Akku", padding=10)
    lf.grid(row=1, column=0, sticky="nwe", padx=(0, 6))
    field(lf, 0, "Zellchemie", "chem", "LiPo, LiHV oder Li-Ion", list(CHEM.keys()))
    field(lf, 1, "Zellenzahl", "cells", "0 = automatisch aus der Startspannung")
    field(lf, 2, "Nennkapazität [mAh]", "nominal_mah", "0 = unbekannt (wird geschätzt)")

    lf = ttk.LabelFrame(st_tab, text="Auswertung", padding=10)
    lf.grid(row=1, column=1, sticky="nwe", padx=(6, 0))
    field(lf, 0, "Min. Flugdauer [s]", "min_flight_s", "kürzere Logs werden übersprungen")
    field(lf, 1, "Motor aktiv ab [A]", "active_current_a", "Strom, ab dem der Flug zählt")
    field(lf, 2, "Reserve bei Landung [%]", "reserve_pct", "für die Timer-Empfehlung")
    field(lf, 3, "Spalte Spannung (optional)", "col_voltage", "Teil des Spaltennamens")
    field(lf, 4, "Spalte Strom (optional)", "col_current", "")

    lf = ttk.LabelFrame(st_tab, text="Export", padding=10)
    lf.grid(row=2, column=0, columnspan=2, sticky="we", pady=10)
    ttk.Button(lf, text="Tabelle als CSV speichern …", command=lambda: export_csv()).pack(side="left", padx=(0, 8))
    ttk.Button(lf, text="Bericht + alle Diagramme speichern …", command=lambda: export_all()).pack(side="left")

    lf = ttk.LabelFrame(st_tab, text="Übersprungene Dateien", padding=6)
    lf.grid(row=3, column=0, columnspan=2, sticky="nsew")
    st_tab.rowconfigure(3, weight=1)
    skip_tree = ttk.Treeview(lf, columns=("datei", "grund"), show="headings", height=8)
    skip_tree.heading("datei", text="Datei")
    skip_tree.heading("grund", text="Grund")
    skip_tree.column("datei", width=320, stretch=False)
    skip_tree.column("grund", width=700)
    sk_sb = ttk.Scrollbar(lf, orient="vertical", command=skip_tree.yview)
    skip_tree.configure(yscrollcommand=sk_sb.set)
    sk_sb.pack(side="right", fill="y")
    skip_tree.pack(fill="both", expand=True)

    # ---------------- Reiter: Zusammenfassung ----------------
    txt = make_text(tabs["summary"])
    sb = ttk.Scrollbar(tabs["summary"], orient="vertical", command=txt.yview)
    txt.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    txt.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)

    # ---------------- Reiter: Einzelflug ----------------
    ft = tabs["flight"]
    bar = ttk.Frame(ft, padding=(6, 6, 6, 2))
    bar.pack(fill="x")
    ttk.Label(bar, text="Flug:").pack(side="left")
    flight_var = tk.StringVar()
    flight_box = ttk.Combobox(bar, textvariable=flight_var, width=46, state="readonly")
    flight_box.pack(side="left", padx=(4, 4))
    ttk.Button(bar, text="‹ zurück", width=9, command=lambda: step_flight(-1)).pack(side="left")
    ttk.Button(bar, text="vor ›", width=7, command=lambda: step_flight(1)).pack(side="left", padx=(2, 14))
    view_var = tk.StringVar(value=FLIGHT_VIEWS[0])
    for v_ in FLIGHT_VIEWS:
        ttk.Radiobutton(bar, text=v_, value=v_, variable=view_var, style="View.TRadiobutton",
                        command=lambda: redraw_flight()).pack(side="left", padx=1)
    details_btn = ttk.Button(bar, text="Details ausblenden", command=lambda: toggle_details())
    details_btn.pack(side="right")
    ttk.Button(bar, text="Bild speichern …", command=lambda: save_flight_png()).pack(side="right", padx=6)

    zbar = ttk.Frame(ft, padding=(6, 0, 6, 4))
    zbar.pack(fill="x")
    ttk.Label(zbar, text="Zeit:").pack(side="left")
    for txt_, cmd in [("Ganzer Flug", lambda: zoom_to(None)), ("Start (60 s)", lambda: zoom_to("start")),
                      ("Landung (60 s)", lambda: zoom_to("end")), ("Zoom +", lambda: zoom_by(1 / 1.5)),
                      ("Zoom −", lambda: zoom_by(1.5)), ("‹ früher", lambda: pan_by(-0.3)), ("später ›", lambda: pan_by(0.3))]:
        ttk.Button(zbar, text=txt_, command=cmd).pack(side="left", padx=1)
    ttk.Label(zbar, text="   Stromspitze:").pack(side="left")
    spike_var = tk.StringVar()
    spike_box = ttk.Combobox(zbar, textvariable=spike_var, width=44, state="readonly")
    spike_box.pack(side="left", padx=4)

    readout = tk.StringVar(value="Maus über das Diagramm bewegen: Werte zum Zeitpunkt.   Mausrad: zoomen  ·  "
                                 "Ziehen mit linker Maustaste: verschieben  ·  Doppelklick: ganzer Flug")
    ttk.Label(ft, textvariable=readout, style="Readout.TLabel").pack(fill="x", padx=6)

    paned = ttk.PanedWindow(ft, orient="vertical")
    paned.pack(fill="both", expand=True, padx=6, pady=4)
    plot_frame = ttk.Frame(paned)
    det_frame = ttk.Frame(paned)
    paned.add(plot_frame, weight=4)
    paned.add(det_frame, weight=1)
    det_txt = make_text(det_frame, height=10)
    dsb = ttk.Scrollbar(det_frame, orient="vertical", command=det_txt.yview)
    det_txt.configure(yscrollcommand=dsb.set)
    dsb.pack(side="right", fill="y")
    det_txt.pack(side="left", fill="both", expand=True)

    flight_fig = Figure(figsize=(12, 7), dpi=100)
    flight_canvas = FigureCanvasTkAgg(flight_fig, master=plot_frame)
    flight_canvas.get_tk_widget().pack(fill="both", expand=True)
    fs = {"axes": [], "cross": [], "drag": None, "details": True}

    # ---------------- Reiter: Tabelle ----------------
    cols = [c[0] for c in TABLE_COLS]
    tree = ttk.Treeview(tabs["table"], columns=cols, show="headings")
    for key, head, w in TABLE_COLS:
        tree.heading(key, text=head)
        tree.column(key, width=w, anchor="center", stretch=False)
    ysb = ttk.Scrollbar(tabs["table"], orient="vertical", command=tree.yview)
    xsb = ttk.Scrollbar(tabs["table"], orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
    ysb.pack(side="right", fill="y")
    xsb.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)

    # ---------------- Funktionen ----------------
    def choose():
        d = filedialog.askdirectory(title="Ordner mit Ethos-Logfiles wählen", initialdir=folder_var.get() or None)
        if d:
            folder_var.set(d)

    def read_params():
        try:
            num = lambda k: float(V[k].get().replace(",", "."))
            return Params(cells=int(num("cells")), chem=V["chem"].get(), nominal_mah=num("nominal_mah"),
                          min_flight_s=num("min_flight_s"), active_current_a=num("active_current_a"),
                          reserve_pct=num("reserve_pct"), col_voltage=V["col_voltage"].get().strip(),
                          col_current=V["col_current"].get().strip())
        except ValueError:
            messagebox.showerror("Eingabefehler", "Bitte gültige Zahlen in den Einstellungen eintragen.")
            return None

    def show_fig(frame, fig):
        for w in frame.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def flight_label(r):
        return f"{int(r['Flug'])} | {r['datum']:%d.%m.%Y %H:%M} | {_mmss(r['dauer_s'])} | {r['entnommen_mAh']:.0f} mAh"

    # --- Einzelflug zeichnen, zoomen, Fadenkreuz ---
    def current_path():
        res = state["res"]
        if res is None or res.df.empty or not flight_var.get():
            return None
        no = int(flight_var.get().split("|")[0])
        return res.df.loc[res.df["Flug"] == no, "pfad"].iloc[0]

    def redraw_flight(*_, keep_zoom=True):
        path = current_path()
        if path is None:
            return
        old = fs["axes"][0].get_xlim() if (keep_zoom and fs["axes"] and state["path"] == path) else None
        fs["axes"] = draw_flight(flight_fig, state["res"], state["p"], path, view_var.get())
        fs["cross"] = [a.axvline(np.nan, color="#333", lw=0.8, alpha=0.7) for a in fs["axes"]]
        if old and fs["axes"]:
            fs["axes"][0].set_xlim(old)
            autoscale_y()
        state["path"] = path
        flight_canvas.draw_idle()

    def select_flight(*_):
        path = current_path()
        if path is None:
            return
        res = state["res"]
        state["path"] = None
        redraw_flight(keep_zoom=False)
        fill_text(det_txt, flight_detail_lines(res, state["p"], path))
        rx = res.series[path].get("rx")
        items = []
        if rx:
            items = [f"{sp['t']:.0f} s – {sp['peak']:.2f} A – {sp['anlass']}"
                     + (f" ({sp['schalter']})" if sp["schalter"] else "") for sp in rx["spikes"]]
        spike_box["values"] = items
        spike_var.set("" if items else "keine Spitzen")

    def step_flight(d):
        vals = list(flight_box["values"])
        if not vals:
            return
        i = vals.index(flight_var.get()) if flight_var.get() in vals else len(vals) - 1
        flight_var.set(vals[max(0, min(len(vals) - 1, i + d))])
        select_flight()

    def full_range():
        path = current_path()
        t = state["res"].series[path]["t"]
        return float(t[0]), float(t[-1])

    def set_xlim(lo, hi):
        if not fs["axes"]:
            return
        t0, t1 = full_range()
        span = min(max(hi - lo, 3.0), t1 - t0)
        lo = max(t0, min(lo, t1 - span))
        fs["axes"][0].set_xlim(lo, lo + span)
        autoscale_y()
        flight_canvas.draw_idle()

    def autoscale_y():
        """y-Achsen an den sichtbaren Ausschnitt anpassen."""
        lo, hi = fs["axes"][0].get_xlim()
        for a in fs["axes"]:
            ys = []
            for ln in a.get_lines():
                if ln.get_gid() != "data":          # Hilfslinien (Schwellen, Markierungen) nicht berücksichtigen
                    continue
                x = np.asarray(ln.get_xdata(), dtype=float)
                if len(x) < 2:
                    continue
                y = np.asarray(ln.get_ydata(), dtype=float)
                m = (x >= lo) & (x <= hi) & np.isfinite(y)
                if m.any():
                    ys.append((y[m].min(), y[m].max()))
            if ys:
                y0, y1 = min(v[0] for v in ys), max(v[1] for v in ys)
                pad = (y1 - y0) * 0.08 or 0.5
                a.set_ylim(y0 - pad, y1 + pad)

    def zoom_to(where):
        if not fs["axes"]:
            return
        t0, t1 = full_range()
        if where is None:
            set_xlim(t0, t1)
        elif where == "start":
            set_xlim(t0, t0 + 60)
        else:
            set_xlim(t1 - 60, t1)

    def zoom_by(f, center=None):
        if not fs["axes"]:
            return
        lo, hi = fs["axes"][0].get_xlim()
        c = (lo + hi) / 2 if center is None else center
        set_xlim(c - (c - lo) * f, c + (hi - c) * f)

    def pan_by(frac):
        if not fs["axes"]:
            return
        lo, hi = fs["axes"][0].get_xlim()
        d = (hi - lo) * frac
        set_xlim(lo + d, hi + d)

    def goto_spike(*_):
        sel = spike_var.get()
        if not sel or not sel[0].isdigit():
            return
        t_ = float(sel.split(" s")[0])
        set_xlim(t_ - 10, t_ + 10)

    spike_box.bind("<<ComboboxSelected>>", goto_spike)

    def on_scroll(ev):
        if ev.inaxes is None or ev.xdata is None:
            return
        zoom_by(1 / 1.25 if ev.button == "up" else 1.25, center=ev.xdata)

    def on_press(ev):
        if ev.inaxes is None or ev.xdata is None:
            return
        if ev.dblclick:
            zoom_to(None)
            return
        if ev.button == 1:
            fs["drag"] = (ev.x, fs["axes"][0].get_xlim())

    def on_release(ev):
        fs["drag"] = None

    def on_motion(ev):
        if fs["drag"] is not None and ev.x is not None and fs["axes"]:
            x0, (lo, hi) = fs["drag"]
            bbox = fs["axes"][0].get_window_extent()
            dt = (ev.x - x0) / max(bbox.width, 1) * (hi - lo)
            set_xlim(lo - dt, hi - dt)
            return
        if ev.inaxes is None or ev.xdata is None or not fs["axes"]:
            return
        t = getattr(flight_fig, "_t", None)
        if t is None:
            return
        k = int(np.clip(np.searchsorted(t, ev.xdata), 0, len(t) - 1))
        for ln in fs["cross"]:
            ln.set_xdata([t[k], t[k]])
        parts = [f"t = {t[k]:.1f} s"]
        for label, unit, y in flight_fig._readout:
            if y is not None and k < len(y) and np.isfinite(y[k]):
                parts.append(f"{label} {y[k]:.4g} {unit}")
        readout.set("   ·   ".join(parts))
        flight_canvas.draw_idle()

    for ev_name, fn in [("scroll_event", on_scroll), ("button_press_event", on_press),
                        ("button_release_event", on_release), ("motion_notify_event", on_motion)]:
        flight_canvas.mpl_connect(ev_name, fn)

    def toggle_details():
        if fs["details"]:
            paned.forget(det_frame)
            details_btn.configure(text="Details einblenden")
        else:
            paned.add(det_frame, weight=1)
            details_btn.configure(text="Details ausblenden")
        fs["details"] = not fs["details"]

    def save_flight_png():
        path = current_path()
        if path is None:
            return
        f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if f:
            flight_fig.savefig(f, dpi=150)

    flight_box.bind("<<ComboboxSelected>>", select_flight)

    # --- Auswertung ---
    def run():
        folder = folder_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Ordner", "Bitte zuerst einen gültigen Ordner wählen.")
            return
        p = read_params()
        if p is None:
            return
        store_settings()
        status.set("Werte aus …")
        run_btn.state(["disabled"])
        root.update_idletasks()

        def cb(n, tot):
            prog["maximum"] = max(tot, 1)
            prog["value"] = n
            root.update_idletasks()

        try:
            res = analyse_folder(folder, p, cb)
        except Exception as e:                       # unerwarteter Fehler: verständlich melden
            messagebox.showerror("Fehler bei der Auswertung", f"{type(e).__name__}: {e}")
            status.set("Fehler bei der Auswertung.")
            return
        finally:
            run_btn.state(["!disabled"])
        state["res"], state["p"] = res, p
        df = res.df
        cells = res.meta.get("cells", p.cells)
        status.set(f"{os.path.basename(os.path.normpath(folder))}  ·  {len(df)} Flüge ausgewertet, "
                   f"{len(res.skipped)} von {res.total} Dateien übersprungen  ·  Akku {cells}S {p.chem}"
                   + (f", {p.nominal_mah:.0f} mAh" if p.nominal_mah > 0 else ", Kapazität unbekannt"))

        skip_tree.delete(*skip_tree.get_children())
        for nme, msg in res.skipped:
            skip_tree.insert("", "end", values=(nme, msg))
        fill_text(txt, summary_lines(res, p))
        tree.delete(*tree.get_children())
        for _, r in df.iterrows():
            tree.insert("", "end", values=[fmt_cell(k, r[k]) for k in cols])

        state["figs"] = {}
        if not df.empty:
            for key, fn in [("akku", figure_akku), ("belastung", figure_belastung),
                            ("antrieb", figure_antrieb), ("funk", figure_funk)]:
                fig = fn(res, p)
                state["figs"][key] = fig
                show_fig(tabs[key], fig)
            labels = [flight_label(r) for _, r in df.iterrows()]
            flight_box["values"] = labels
            flight_var.set(labels[-1])
            select_flight()
        nb.select(tabs["summary"])

    def export_csv():
        res = state["res"]
        if res is None or res.df.empty:
            messagebox.showinfo("Export", "Bitte zuerst auswerten.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if f:
            out = res.df.drop(columns=["pfad", "P_a", "P_n", "k_V_je_Ah"], errors="ignore")
            out.to_csv(f, index=False, sep=";", decimal=",", encoding="utf-8-sig")

    def export_all():
        res = state["res"]
        if res is None or res.df.empty:
            messagebox.showinfo("Export", "Bitte zuerst auswerten.")
            return
        d = filedialog.askdirectory(title="Zielordner für Bericht und Diagramme")
        if not d:
            return
        with open(os.path.join(d, "zusammenfassung.txt"), "w", encoding="utf-8") as fh:
            for _, line in summary_lines(res, state["p"]):
                fh.write(line + "\n")
        for name, fig in state["figs"].items():
            fig.savefig(os.path.join(d, f"{name}.png"), dpi=150)
        path = current_path()
        if path is not None:
            no = int(res.df.loc[res.df["pfad"] == path, "Flug"].iloc[0])
            with open(os.path.join(d, f"flug{no}_details.txt"), "w", encoding="utf-8") as fh:
                for _, line in flight_detail_lines(res, state["p"], path):
                    fh.write(line + "\n")
            for k, v_ in enumerate(FLIGHT_VIEWS):
                figure_flight(res, state["p"], path, v_).savefig(os.path.join(d, f"flug{no}_{k + 1}.png"), dpi=130)
        out = res.df.drop(columns=["pfad", "P_a", "P_n", "k_V_je_Ah"], errors="ignore")
        out.to_csv(os.path.join(d, "fluege.csv"), index=False, sep=";", decimal=",", encoding="utf-8-sig")
        messagebox.showinfo("Gespeichert", f"Bericht, Tabelle und Diagramme wurden in\n{d}\ngespeichert.")

    def on_close():
        store_settings()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    nb.select(tabs["settings"])
    root._akku = dict(fbox=flight_box, run=run, nb=nb, tabs=tabs, flight_var=flight_var, view_var=view_var, select_flight=select_flight,
                      redraw=redraw_flight, set_xlim=set_xlim, goto_spike=goto_spike, spike_var=spike_var)  # für Tests
    return root


if __name__ == "__main__":
    run_gui().mainloop()
