# -*- coding: utf-8 -*-
"""Auswertung einzelner Flüge: echte Beispiel-Logs und synthetische Logs mit bekannten Werten."""

import numpy as np

from helpers import EXAMPLE_FILES, ela, tmpdir, write_ethos_csv

# Referenzwerte der Beispiel-Logs (Stand der ersten Version); Abweichungen deuten auf geänderte Berechnung
REFERENZ = {
    "Viper-Jet-2026-09-13-13-56-38.csv": dict(dauer_s=483.9, entnommen_mAh=5559, Ri_mOhm=56.4),
    "Viper-Jet-2026-09-27-14-29-07.csv": dict(dauer_s=461.9, entnommen_mAh=6231, Ri_mOhm=56.0),
    "Viper-Jet-2026-10-18-13-04-31.csv": dict(dauer_s=538.2, entnommen_mAh=6687, Ri_mOhm=53.6),
}


def test_beispielfluege_referenzwerte():
    for f in EXAMPLE_FILES:
        row, msg = ela.analyse_file(str(f), ela.Params())
        assert msg == "ok", (f.name, msg)
        ref = REFERENZ[f.name]
        assert abs(row["dauer_s"] - ref["dauer_s"]) < 0.5, f.name
        assert abs(row["entnommen_mAh"] - ref["entnommen_mAh"]) <= 5, f.name
        assert abs(row["Ri_mOhm"] - ref["Ri_mOhm"]) < 1.0, f.name


def test_eigene_mah_berechnung_passt_zum_esc_zaehler():
    for f in EXAMPLE_FILES:
        row, _ = ela.analyse_file(str(f), ela.Params())
        assert abs(row["entnommen_mAh"] - row["ESC_mAh"]) / row["ESC_mAh"] < 0.05, f.name


def _profil(n, seed=1):
    rng = np.random.default_rng(seed)
    return np.clip(35 + 25 * np.sin(np.arange(n) / 7.0) + rng.normal(0, 4, n), 3, None)


def test_innenwiderstand_wird_aus_synthetischem_log_zurueckgerechnet():
    """U = U0 - Ri*I - k*Q mit Ri = 50 mOhm muss wieder ca. 50 mOhm ergeben."""
    t = np.arange(0, 300, 0.25)
    i = _profil(len(t))
    q_ah = np.cumsum(i * 0.25) / 3600.0
    u = 50.0 - 0.050 * i - 1.2 * q_ah
    d = tmpdir()
    path = write_ethos_csv(d, "Synth-2026-05-01-12-00-00.csv", t, u, i)
    row, msg = ela.analyse_file(str(path), ela.Params())
    assert msg == "ok"
    assert abs(row["Ri_mOhm"] - 50.0) < 2.0
    assert abs(row["entnommen_mAh"] - q_ah[-1] * 1000) / (q_ah[-1] * 1000) < 0.02


def test_motortest_vor_dem_start_zaehlt_nicht_zum_flug():
    """10 s Motortest, 60 s Pause, dann 200 s Flug: ausgewertet wird nur der Flug."""
    seg = [(0, 10, True), (10, 70, False), (70, 270, True), (270, 300, False)]
    t = np.arange(0, 300, 0.25)
    i = np.zeros_like(t)
    for a, b, on in seg:
        m = (t >= a) & (t < b)
        i[m] = _profil(m.sum(), seed=a) if on else 0.2
    u = 48.0 - 0.05 * i
    d = tmpdir()
    path = write_ethos_csv(d, "Synth-2026-05-01-12-00-00.csv", t, u, i)
    row, msg = ela.analyse_file(str(path), ela.Params())
    assert msg == "ok"
    assert 195 < row["dauer_s"] < 202


def test_zu_kurzer_flug_wird_uebersprungen():
    t = np.arange(0, 60, 0.25)
    i = _profil(len(t))
    d = tmpdir()
    path = write_ethos_csv(d, "Kurz-2026-05-01-12-00-00.csv", t, 48 - 0.05 * i, i)
    row, msg = ela.analyse_file(str(path), ela.Params())
    assert row is None and msg.startswith("zu kurz")


def test_bodenlog_ohne_akkuwerte_wird_uebersprungen():
    t = np.arange(0, 300, 0.25)
    z = np.zeros_like(t)
    d = tmpdir()
    path = write_ethos_csv(d, "Boden-2026-05-01-12-00-00.csv", t, z, z)
    row, msg = ela.analyse_file(str(path), ela.Params())
    assert row is None and "Nullwerte" in msg
