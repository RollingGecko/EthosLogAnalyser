# -*- coding: utf-8 -*-
"""English translation. Keys are the German source texts from the code (see i18n.py)."""

CATALOG = {
    # ---------------- formats and file names ----------------
    "%d.%m.%Y": "%d/%m/%Y",
    "%d.%m.%Y %H:%M": "%d/%m/%Y %H:%M",
    "zusammenfassung.txt": "summary.txt",
    "fluege.csv": "flights.csv",
    "flug{no}_details.txt": "flight{no}_details.txt",
    "flug{no}_{view}.png": "flight{no}_{view}.png",

    # ---------------- window, tabs, settings ----------------
    "Daten & Einstellungen": "Data & settings",
    "Zusammenfassung": "Summary",
    "Akku": "Battery",
    "Belastung & Flugprofil": "Load & flight profile",
    "Antrieb": "Drive",
    "Funk & Bordnetz": "Radio & onboard power",
    "Einzelflug": "Single flight",
    "Tabelle": "Table",
    "Auswertung": "Analysis",
    "Zellchemie": "Cell chemistry",
    "LiPo, LiHV oder Li-Ion": "LiPo, LiHV or Li-Ion",
    "Zellenzahl": "Cell count",
    "0 = automatisch aus der Startspannung": "0 = automatic from the start voltage",
    "Nennkapazität [mAh]": "Nominal capacity [mAh]",
    "0 = unbekannt (wird geschätzt)": "0 = unknown (will be estimated)",
    "Min. Flugdauer [s]": "Min. flight duration [s]",
    "kürzere Logs werden übersprungen": "shorter logs are skipped",
    "Motor aktiv ab [A]": "Motor running from [A]",
    "Strom, ab dem der Flug zählt": "current from which the flight counts",
    "Reserve bei Landung [%]": "Reserve at landing [%]",
    "für die Timer-Empfehlung": "for the timer recommendation",
    "Spalte Spannung (optional)": "Voltage column (optional)",
    "Teil des Spaltennamens": "part of the column name",
    "Spalte Strom (optional)": "Current column (optional)",
    "Sprache (Language)": "Language",
    "wird gespeichert und beim nächsten Start verwendet": "is saved and used at the next start",
    "Export": "Export",
    "Tabelle als CSV speichern …": "Save table as CSV …",
    "Bericht + alle Diagramme speichern …": "Save report + all charts …",
    "Datei": "File",

    # ---------------- single-flight tab ----------------
    "Flug:": "Flight:",
    "‹ zurück": "‹ previous",
    "vor ›": "next ›",
    "Details ausblenden": "Hide details",
    "Details einblenden": "Show details",
    "Bild speichern …": "Save image …",
    "Ansicht:": "View:",
    "Zeit:": "Time:",
    "Ganzer Flug": "Whole flight",
    "Start (60 s)": "Take-off (60 s)",
    "Landung (60 s)": "Landing (60 s)",
    "Zoom +": "Zoom +",
    "Zoom −": "Zoom −",
    "‹ früher": "‹ earlier",
    "später ›": "later ›",
    "Stromspitze:": "Current spike:",
    "keine Spitzen": "no spikes",

    # ---------------- messages ----------------
    "Eingabefehler": "Input error",
    "Bitte gültige Zahlen in den Einstellungen eintragen.": "Please enter valid numbers in the settings.",
    "Zielordner für Bericht und Diagramme": "Target folder for report and charts",
    "Gespeichert": "Saved",
    "Bericht, Tabelle und Diagramme wurden in\n{folder}\ngespeichert.":
        "Report, table and charts were saved in\n{folder}",

    # ---------------- reasons for skipped files ----------------
    "Lesefehler: {err}": "Read error: {err}",
    "Spalten nicht gefunden (Spannung={cv}, Strom={ci}). Verfügbar: {cols}":
        "Columns not found (voltage={cv}, current={ci}). Available: {cols}",
    "Zeitspalte nicht erkannt": "time column not recognised",
    "Spannung/Strom kaum vorhanden (Sensor nicht verbunden?)": "hardly any voltage/current values (sensor not connected?)",
    "nur Nullwerte in {cv}/{ci} (Bodenlog ohne Akku-Telemetrie)": "only zero values in {cv}/{ci} (ground log without battery telemetry)",
    "zu wenige Datenpunkte": "too few data points",
    "kein Motorstrom erkannt": "no motor current detected",

    # ---------------- labels: spike causes, signals, sticks, sources ----------------
    "Schalter": "Switch",
    "Manöver": "Manoeuvre",
    "Start/Landung": "Take-off/landing",
    "ohne erkennbaren Anlass": "no apparent cause",
    "keine Lagedaten": "no attitude data",
    "Knüppelaktivität": "stick activity",
    "Drehrate": "Rotation rate",
    "G-Last": "G-load",
    "Gas": "Throttle",
    "Querruder": "Aileron",
    "Höhenruder": "Elevator",
    "Seitenruder": "Rudder",
    "gemessen": "measured",
    "geschätzt": "estimated",
    "Nennkapazität": "nominal capacity",
    "geschätzte Kapazität": "estimated capacity",

    # ---------------- flags and usage factors ----------------
    "Ladezustand unplausibel": "Implausible state of charge",
    "Tiefentladung": "Deep discharge",
    "Spannungseinbruch": "Voltage sag",
    "Sensorabweichung": "Sensor deviation",
    "Empfängerstrom-Spitzen ohne Anlass": "Receiver current spikes without cause",
    "Innenwiderstand": "Internal resistance",
    "Spannung bei Referenzlast": "Voltage at reference load",
    "Antriebsleistung bei Referenzdrehzahl": "Drive power at reference RPM",
    "RSSI-Minimum": "RSSI minimum",
    "VFR-Minimum": "VFR minimum",
    "Empfängerspannung": "Receiver voltage",
    "Empfängerstrom-Maximum": "Receiver current maximum",
    "Abweichung Strommessung/ESC-Zähler": "Deviation current sensor/ESC counter",
    "Spitzen-C-Rate": "peak C-rate",
    "Entladetiefe": "depth of discharge",
    "Endspannung": "end voltage",
    "Ladezustand beim Start": "state of charge at take-off",
    "Pause seit letztem Flug": "break since last flight",
    "mittlerer Strom": "mean current",
    "Flugdauer": "flight duration",

    # ---------------- warnings ----------------
    "{label} in {n} von {total} Flügen (Flug {flights}): {text}": "{label} in {n} of {total} flights (flight {flights}): {text}",
    "Flug {no} ({date}): auffälliger Wert bei {label} ({value}, erwartet ca. {expected}).":
        "Flight {no} ({date}): unusual value for {label} ({value}, expected approx. {expected}).",
    "Ladezustand aus der Endspannung weicht im Mittel um {dev:+.0f} Prozentpunkte von der Ladungszählung ab "
    "(entnommen / {src} {cap:.0f} mAh). Verwendet wird die Ladungszählung. Mögliche Ursachen: Akkuwechsel oder "
    "Motorlauf nach der Landung im selben Log, Spannungssensor, falsche Nennkapazität oder Zellchemie.":
        "The state of charge from the end voltage differs on average by {dev:+.0f} percentage points from coulomb "
        "counting (drawn / {src} {cap:.0f} mAh). Coulomb counting is used. Possible causes: battery swap or motor run "
        "after landing in the same log, voltage sensor, wrong nominal capacity or cell chemistry.",
    "Ruhespannung am Ende unter {rest:.2f} V/Zelle ({chem}) oder rechnerischer Ladezustand unter 5 % (tiefste "
    "Endspannung {low:.2f} V/Zelle). Bitte auch Zellchemie und Nennkapazität prüfen.":
        "Resting voltage at the end below {rest:.2f} V/cell ({chem}) or calculated state of charge below 5 % (lowest "
        "end voltage {low:.2f} V/cell). Please also check cell chemistry and nominal capacity.",
    "Spannung unter Last fiel bis auf {low:.2f} V/Zelle (Grenze {limit:.2f} V).":
        "Voltage under load dropped to {low:.2f} V/cell (limit {limit:.2f} V).",
    "Strommessung weicht mehr als 5 % vom ESC-Zähler ab (Sensor prüfen/kalibrieren).":
        "Current measurement differs by more than 5 % from the ESC counter (check/calibrate the sensor).",
    "mindestens 3 Stromspitzen ohne Manöver, Start oder Landung. Servos auf Schwergängigkeit, Anschlag (Brummen in "
    "Endlage) und Defekte prüfen; Zeitpunkte siehe Einzelflug.":
        "at least 3 current spikes without manoeuvre, take-off or landing. Check servos for binding, end stops "
        "(buzzing at end position) and defects; see the single flight for the times.",

    # ---------------- summary report ----------------
    "Keine auswertbaren Flüge gefunden.": "No flights that could be analysed were found.",
    "ÜBERSICHT": "OVERVIEW",
    "Akku: {cells}S {chem}": "Battery: {cells}S {chem}",
    "  (Zellenzahl automatisch erkannt)": "  (cell count detected automatically)",
    ", Nennkapazität {cap:.0f} mAh": ", nominal capacity {cap:.0f} mAh",
    "Gesamt entnommen: {ah:.1f} Ah": "Total drawn: {ah:.1f} Ah",
    "  (≈ {cycles:.1f} Vollzyklen)": "  (≈ {cycles:.1f} full cycles)",
    "AKKU ÜBER ALLE FLÜGE": "BATTERY ACROSS ALL FLIGHTS",
    "Details zu jedem einzelnen Flug (auch zum letzten) stehen im Einzelflug (Doppelklick auf den Flug im Logbuch).":
        "Details of each flight (including the last one) are in the single flight (double-click the flight in the logbook).",
    "Typischer Flug (Median): {dur}, {drawn} mAh entnommen, Ladezustand am Ende ≈ {soc} %, Spitze {imax} A / "
    "{pmax} W, min. {umin} V/Zelle unter Last":
        "Typical flight (median): {dur}, {drawn} mAh drawn, state of charge at the end ≈ {soc} %, peak {imax} A / "
        "{pmax} W, min. {umin} V/cell under load",
    "Innenwiderstand je Zelle: Median {med} mΩ, Spanne {lo} – {hi} mΩ":
        "Internal resistance per cell: median {med} mΩ, range {lo} – {hi} mΩ",
    "Zellchemie prüfen: Mit {chem} passen Ruhespannung und entnommene Ladung nicht zusammen (Abweichung im Median "
    "{dev:.0f} Prozentpunkte), mit {best} sehr gut ({best_dev:.0f} Pkt.). Ist der Akku ein {best}-Akku? Falls es "
    "wirklich {chem} ist, liefert er deutlich weniger als die eingetragenen {cap:.0f} mAh (geschätzt ca. {est} mAh).":
        "Check the cell chemistry: with {chem}, resting voltage and drawn charge do not match (median deviation "
        "{dev:.0f} percentage points), with {best} they match very well ({best_dev:.0f} pts). Is it a {best} battery? "
        "If it really is {chem}, it delivers clearly less than the {cap:.0f} mAh entered (estimated approx. {est} mAh).",
    "Ruhespannung und entnommene Ladung passen zur Einstellung {chem} / {cap:.0f} mAh (Abweichung im Median "
    "{dev:.0f} Pkt.).":
        "Resting voltage and drawn charge match the setting {chem} / {cap:.0f} mAh (median deviation {dev:.0f} pts).",
    "Nennkapazität nicht eingetragen: Ladezustand und Timer beruhen nur auf der Spannungskennlinie.":
        "Nominal capacity not entered: state of charge and timer are based on the voltage curve only.",
    "ALTERUNG UND RESTKAPAZITÄT": "AGEING AND REMAINING CAPACITY",
    "  - unzuverlässig, solange die Zellchemie nicht passt (siehe oben)":
        "  - unreliable as long as the cell chemistry does not match (see above)",
    "Innenwiderstand je Zelle: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)":
        "Internal resistance per cell: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)",
    "Spannung bei {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/Zelle ({mv:+.0f} mV)":
        "Voltage at {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/cell ({mv:+.0f} mV)",
    ", ≈ {cycles:.0f} Vollzyklen": ", ≈ {cycles:.0f} full cycles",
    "Zusammenhang Nutzung ↔ Ri-Abweichung (Hinweis, keine Kausalität):":
        "Relation usage ↔ Ri deviation (hint, not causality):",
    "TIMER-EMPFEHLUNG": "TIMER RECOMMENDATION",
    "Landung bei {reserve:.0f} % Restkapazität: Timer ca. {timer} (Median der letzten Flüge; geflogen: {flown})":
        "Landing at {reserve:.0f} % remaining capacity: timer approx. {timer} (median of the last flights; flown: {flown})",
    "Basis: Kapazität ≈ {cap:.0f} mAh, Leistungsprofil der letzten Flüge.":
        "Basis: capacity ≈ {cap:.0f} mAh, power profile of the last flights.",
    "Nicht bestimmbar (Kapazität unbekannt: Nennkapazität eintragen oder Flüge mit ≥ 40 % Entladetiefe).":
        "Cannot be determined (capacity unknown: enter the nominal capacity or fly with ≥ 40 % depth of discharge).",
    "ANTRIEB UND SENSOREN": "DRIVE AND SENSORS",
    "Leistungsbedarf bei {rpm:.0f} U/min: {p0:.0f} → {p1:.0f} W ({pct:+.0f} %)":
        "Power demand at {rpm:.0f} rpm: {p0:.0f} → {p1:.0f} W ({pct:+.0f} %)",
    "  - Anstieg kann auf Verschleiß/Lagerschaden/Fremdkörper hindeuten":
        "  - an increase can indicate wear, bearing damage or foreign objects",
    "Antriebs-Trend: ab 4 Flügen verfügbar.": "Drive trend: available from 4 flights.",
    "Antriebs-Kennlinie nicht verfügbar (keine Drehzahl im Log).": "Drive curve not available (no RPM in the log).",
    "Strommessung vs. ESC-Zähler: Median {dev:+.1f} % Abweichung": "Current sensor vs. ESC counter: median deviation {dev:+.1f} %",
    "FUNK UND BORDNETZ (schlechtester Wert über alle Flüge)": "RADIO AND ONBOARD POWER (worst value across all flights)",
    "Empfängerakku": "Receiver battery",
    "Empfängerstrom max": "Receiver current max",
    "Senderakku": "Transmitter battery",
    "{label} {value}{unit} (Flug {no})": "{label} {value}{unit} (flight {no})",
    "keine Funkwerte im Log": "no radio values in the log",
    "Empfängerstrom: Grundlast Ø {base:.2f} A (Median der Flüge)": "Receiver current: base load Ø {base:.2f} A (median of the flights)",
    ", Spitzen bis {peak:.2f} A": ", spikes up to {peak:.2f} A",
    "Stromspitzen (alle Flüge): {n} - {shares}": "Current spikes (all flights): {n} - {shares}",
    "Strom folgt deutlich den Steuerausschlägen (Servolast)": "current clearly follows the control inputs (servo load)",
    "mäßiger Zusammenhang mit den Steuerausschlägen": "moderate relation to the control inputs",
    "kaum Zusammenhang mit den Steuerausschlägen": "hardly any relation to the control inputs",
    "Zusammenhang Empfängerstrom ↔ {signal}: r = {r:+.2f} (Median) - {verdict}":
        "Relation receiver current ↔ {signal}: r = {r:+.2f} (median) - {verdict}",
    "WARNUNGEN UND AUFFÄLLIGKEITEN": "WARNINGS AND ANOMALIES",
    "… und {n} weitere": "… and {n} more",
    "Keine Auffälligkeiten festgestellt.": "No anomalies found.",
    " (Ausreißer-Erkennung erst ab 6 Flügen aktiv.)": " (outlier detection only from 6 flights on.)",
    "GRENZEN DER AUSWERTUNG": "LIMITS OF THE ANALYSIS",
    "Ohne Temperaturdaten: Ri hängt stark von der Akku-Temperatur ab - kalte Flüge wirken schlechter, als der Akku ist.":
        "No temperature data: Ri depends strongly on battery temperature - cold flights look worse than the battery is.",
    "Keine Einzelzellspannungen: schwache Zellen/Balancing sind nicht erkennbar.":
        "No individual cell voltages: weak cells/balancing cannot be detected.",
    "Ladezustand am Ende: Ladungszählung, abhängig von der richtigen Nennkapazität bzw. Kapazitätsschätzung. Die "
    "Ruhespannung ist nur eine Gegenprobe (Näherungskennlinie, Akku erholt sich nach der Landung).":
        "State of charge at the end: coulomb counting, depends on the correct nominal capacity or capacity estimate. "
        "The resting voltage is only a cross-check (approximate curve, the battery recovers after landing).",
    "Empfängerstrom-Spitzen: Zuordnung über Schalterbetätigung, Knüppelbewegung, Drehrate (Roll/Nick), G-Last, "
    "Flugzeit und Höhe - soweit diese Werte im Log stehen. Welcher Schalter z. B. das Fahrwerk schaltet, weiß die App "
    "nicht; sie nennt den Namen der Ethos-Quelle.":
        "Receiver current spikes: assigned via switch operation, stick movement, rotation rate (roll/pitch), g-load, "
        "flight time and altitude - as far as these values are in the log. The app does not know which switch "
        "operates e.g. the landing gear; it shows the name of the Ethos source.",
    "Flugphasen und Wh je 100 m Steigen sind indikativ (Höhenwerte geglättet).":
        "Flight phases and Wh per 100 m climb are indicative (altitude values smoothed).",

    # ---------------- state of charge lines ----------------
    "Ladezustand: Start ≈ {start} %, Ende ≈ {end:.0f} %  (Ladungszählung: {drawn:.0f} mAh entnommen von {cap:.0f} mAh "
    "{src})":
        "State of charge: take-off ≈ {start} %, end ≈ {end:.0f} %  (coulomb counting: {drawn:.0f} mAh drawn of "
        "{cap:.0f} mAh {src})",
    "  Gegenprobe Ruhespannung: {u0} → {u1} V/Zelle ({src}) ≙ {soc} % - passt nicht zur entnommenen Ladung "
    "({dev:+.0f} Pkt.), verworfen":
        "  Cross-check resting voltage: {u0} → {u1} V/cell ({src}) ≙ {soc} % - does not match the drawn charge "
        "({dev:+.0f} pts), discarded",
    "  Gegenprobe Ruhespannung: {u0} → {u1} V/Zelle ({src}) ≙ {soc} % - passt":
        "  Cross-check resting voltage: {u0} → {u1} V/cell ({src}) ≙ {soc} % - matches",
    "Ladezustand: Start ≈ {start} %, Ende ≈ {end} % nur aus Ruhespannung ({u1} V/Zelle, {src}) - ohne Gegenprobe. "
    "Nennkapazität eintragen für die Ladungszählung.":
        "State of charge: take-off ≈ {start} %, end ≈ {end} % from resting voltage only ({u1} V/cell, {src}) - without "
        "cross-check. Enter the nominal capacity for coulomb counting.",

    # ---------------- single-flight report ----------------
    "{value}{unit} (Median {median}{unit})": "{value}{unit} (median {median}{unit})",
    " V/Zelle": " V/cell",
    " U/min": " rpm",
    "Flug {no} – {date} – {dur} – {drawn:.0f} mAh – {file}": "Flight {no} – {date} – {dur} – {drawn:.0f} mAh – {file}",
    "AUFFÄLLIGKEITEN IN DIESEM FLUG": "ANOMALIES IN THIS FLIGHT",
    "AKKU": "BATTERY",
    "Innenwiderstand je Zelle: {value}": "Internal resistance per cell: {value}",
    "  im Flugverlauf: Anfang {r0:.2f} → Ende {r1:.2f} mΩ ({pct:+.0f} %)":
        "  during the flight: start {r0:.2f} → end {r1:.2f} mΩ ({pct:+.0f} %)",
    "Innenwiderstand: nicht bestimmbar (zu gleichmäßige Last)": "Internal resistance: cannot be determined (load too steady)",
    "Reserve zur Mindest-Ruhespannung ({rest:.2f} V/Zelle): {reserve:+.2f} V/Zelle":
        "Reserve to the minimum resting voltage ({rest:.2f} V/cell): {reserve:+.2f} V/cell",
    "Geschätzte Gesamtkapazität: {value}": "Estimated total capacity: {value}",
    "Minimale Spannung unter Last: {value} bei {imax:.0f} A Spitze": "Minimum voltage under load: {value} at {imax:.0f} A peak",
    "Spannung bei {iref:.0f} A / {qref:.0f} mAh: {value}": "Voltage at {iref:.0f} A / {qref:.0f} mAh: {value}",
    "BELASTUNG UND FLUGPROFIL": "LOAD AND FLIGHT PROFILE",
    "C-Rate Spitze {value}": "Peak C-rate {value}",
    "Spitzenleistung {value}": "Peak power {value}",
    "Energie nach Phase: Steigflug {up:.0f} Wh ({pct:.0f} %), Reise {cr:.0f} Wh, Sinkflug {dn:.0f} Wh":
        "Energy by phase: climb {up:.0f} Wh ({pct:.0f} %), cruise {cr:.0f} Wh, descent {dn:.0f} Wh",
    "Max. Höhe {value}": "Max. altitude {value}",
    ", {wh} Wh je 100 m Steigen": ", {wh} Wh per 100 m climb",
    "G-Kräfte: max {value}, 95. Perzentil {p95:.1f} g": "G-forces: max {value}, 95th percentile {p95:.1f} g",
    "TIMER": "TIMER",
    "Empfehlung für {reserve:.0f} % Rest bei diesem Flugprofil: {timer}, geflogen {flown} ":
        "Recommendation for {reserve:.0f} % remaining with this flight profile: {timer}, flown {flown} ",
    "({diff} länger als empfohlen)": "({diff} longer than recommended)",
    "(innerhalb der Empfehlung)": "(within the recommendation)",
    "Keine Timer-Empfehlung (Kapazität unbekannt).": "No timer recommendation (capacity unknown).",
    "Drehzahl (90. Perzentil): {value}": "RPM (90th percentile): {value}",
    "; Leistung bei {rpm:.0f} U/min: {value}": "; power at {rpm:.0f} rpm: {value}",
    "Eigene mAh-Berechnung gegen ESC-Zähler: {own:.0f} gegen {esc:.0f} mAh ({dev:+.1f} %)":
        "Own mAh calculation vs. ESC counter: {own:.0f} vs. {esc:.0f} mAh ({dev:+.1f} %)",
    "FUNK UND BORDNETZ": "RADIO AND ONBOARD POWER",
    "RSSI min. {rssi}, VFR min. {vfr}": "RSSI min. {rssi}, VFR min. {vfr}",
    "Empfängerakku min. {rx}, Senderakku min. {tx} V": "Receiver battery min. {rx}, transmitter battery min. {tx} V",
    "Empfängerstrom: Grundlast {base:.2f} A, Maximum {value}, Spitzenschwelle {thr:.2f} A":
        "Receiver current: base load {base:.2f} A, maximum {value}, spike threshold {thr:.2f} A",
    "Zusammenhang mit dem Empfängerstrom: {values}": "Relation to the receiver current: {values}",
    "EMPFÄNGERSTROM-SPITZEN ({n})": "RECEIVER CURRENT SPIKES ({n})",
    "Keine Spitzen über der Schwelle.": "No spikes above the threshold.",
    "Kein Empfängerstrom im Log.": "No receiver current in the log.",
    "SCHALTERBETÄTIGUNGEN ({n})": "SWITCH OPERATIONS ({n})",

    # ---------------- charts: common ----------------
    "keine Daten": "no data",
    "Keine Daten": "No data",
    "Flug Nr.": "Flight no.",
    " Rot umkreist: auffälliger Flug.": " Circled in red: unusual flight.",
    "Flug": "Flight",

    # ---------------- charts: battery ----------------
    "Akku-Zustand und Alterung": "Battery condition and ageing",
    "80 % der Anfangskapazität": "80 % of the initial capacity",
    "Geschätzte Gesamtkapazität [mAh]": "Estimated total capacity [mAh]",
    "Aus entnommener Ladung und Spannungsabfall. Fallender Trend = Alterung.":
        "From drawn charge and voltage drop. Falling trend = ageing.",
    "Innenwiderstand je Zelle [mΩ]": "Internal resistance per cell [mΩ]",
    "Ø Flug": "Ø flight",
    "Steigender Trend = Alterung; +50 % gilt als Lebensende.": "Rising trend = ageing; +50 % is considered end of life.",
    "Flugbeginn": "Start of flight",
    "Flugende": "End of flight",
    "Spannung bei {iref:.0f} A und {qref:.0f} mAh [V/Zelle]": "Voltage at {iref:.0f} A and {qref:.0f} mAh [V/cell]",
    "Vergleich unter gleichen Bedingungen. Fallender Trend = Akku wird schwächer.":
        "Comparison under the same conditions. Falling trend = battery is getting weaker.",
    "Ruhespannung Start / Ende [V/Zelle]": "Resting voltage start / end [V/cell]",
    "Start": "Start",
    "Start: voll geladen? Ende: sollte über der roten Linie liegen.": "Start: fully charged? End: should be above the red line.",
    "Ende (rot umkreist: passt nicht zur Ladung)": "End (circled in red: does not match the charge)",
    "Mindestwert": "Minimum",
    "Ladezustand Start / Ende [%]": "State of charge start / end [%]",
    "Ende sollte über der Reserve-Linie liegen.": "End should be above the reserve line.",
    "Ende (Ladungszählung)": "End (coulomb counting)",
    "Reserve": "Reserve",
    "Ende (aus Spannung)": "End (from voltage)",
    "Min. Spannung unter Last [V/Zelle]": "Min. voltage under load [V/cell]",
    "Grenze": "Limit",
    "Tiefster Spannungseinbruch bei Volllast. Unter der roten Linie: Zellen überlastet.":
        "Deepest voltage sag at full load. Below the red line: cells overloaded.",

    # ---------------- charts: load ----------------
    "Belastung und Flugprofil": "Load and flight profile",
    "alle Flüge": "all flights",
    "letzter Flug": "last flight",
    "Zeitanteil [%]": "Share of time [%]",
    "kein Gaskanal im Log": "no throttle channel in the log",
    "Gas-Histogramm": "Throttle histogram",
    "Wie viel Prozent der Flugzeit bei welcher Gasstellung geflogen wurde.":
        "Which percentage of the flight time was flown at which throttle position.",
    "Gas [%]": "Throttle [%]",
    "Spitzen-C-Rate je Flug [C]": "Peak C-rate per flight [C]",
    "Höchster Strom geteilt durch Kapazität. Dauerhaft hohe Werte altern den Akku schneller.":
        "Highest current divided by capacity. Constantly high values age the battery faster.",
    "Steigflug": "Climb",
    "Reise": "Cruise",
    "Sinkflug": "Descent",
    "keine Höhe im Log": "no altitude in the log",
    "Energie je Flugphase [Wh]": "Energy per flight phase [Wh]",
    "Wofür die Energie verbraucht wurde (aus Höhenänderung).": "What the energy was used for (from altitude change).",
    "Spitzenleistung je Flug [W]": "Peak power per flight [W]",
    "Höchste elektrische Leistung (Spannung × Strom).": "Highest electrical power (voltage × current).",
    "G-Kräfte [g]": "G-forces [g]",
    "Maß für die Härte der Flugmanöver.": "A measure of how hard the manoeuvres were.",
    "95. Perzentil": "95th percentile",
    "Flugzeit": "Flight time",
    "Timer für {reserve:.0f} % Rest": "Timer for {reserve:.0f} % remaining",
    "Balken über dem roten Punkt: länger geflogen als für die Reserve empfohlen.":
        "Bar above the red dot: flown longer than recommended for the reserve.",

    # ---------------- charts: drive ----------------
    "Antrieb und Sensor-Plausibilität": "Drive and sensor plausibility",
    "keine Drehzahl im Log": "no RPM in the log",
    "Kennlinie: Leistung gegen Drehzahl": "Curve: power vs. RPM",
    "Drehzahl [1000 U/min]": "RPM [1000 rpm]",
    "Leistung [kW]": "Power [kW]",
    "Leistungsbedarf bei {rpm} U/min [W]": "Power demand at {rpm} rpm [W]",
    "Steigt der Bedarf bei gleicher Drehzahl, läuft der Antrieb schwerer.":
        "If the demand rises at the same RPM, the drive runs harder.",
    "Drehzahl, 90. Perzentil [U/min]": "RPM, 90th percentile [rpm]",
    "Typische Höchstdrehzahl im Flug. Fallender Trend: Akku oder Antrieb lassen nach.":
        "Typical maximum RPM in flight. Falling trend: battery or drive is weakening.",
    "Plausibilität: eigene mAh-Berechnung gegen ESC-Zähler [%]": "Plausibility: own mAh calculation vs. ESC counter [%]",
    "Innerhalb ±5 %: Verbrauchswerte verlässlich (Grundlage für Ladezustand und Timer).":
        "Within ±5 %: consumption values are reliable (basis for state of charge and timer).",
    "verlässlich": "reliable",
    "Sensor prüfen": "check sensor",

    # ---------------- charts: radio ----------------
    "Funk und Bordnetz": "Radio and onboard power",
    "RSSI-Minimum im Flug": "RSSI minimum in flight",
    "Schlechteste Empfangsstärke je Flug. Ethos warnt üblicherweise unter 45.":
        "Worst signal strength per flight. Ethos usually warns below 45.",
    "VFR-Minimum im Flug [%]": "VFR minimum in flight [%]",
    "Anteil korrekt empfangener Telemetrie-Rahmen. Unter ca. 80 % wird es kritisch.":
        "Share of correctly received telemetry frames. Below approx. 80 % it becomes critical.",
    "Empfängerakku: Minimum im Flug [V]": "Receiver battery: minimum in flight [V]",
    "Tiefster Wert der Empfängerversorgung. Einbrüche deuten auf Akku, Kabel oder Servolast.":
        "Lowest value of the receiver supply. Dips point to battery, cables or servo load.",
    "Empfängerstrom [A]": "Receiver current [A]",
    "Maximum": "Maximum",
    "Grundlast (grau) und Spitzen (rot) der Servoversorgung.": "Base load (grey) and spikes (red) of the servo supply.",
    "Mittelwert": "Mean",
    "kein Empfängerstrom im Log": "no receiver current in the log",
    "Empfängerstrom-Spitzen je Flug nach Anlass": "Receiver current spikes per flight by cause",
    "Schwarz = ohne erkennbaren Anlass: Servos prüfen. Details im Einzelflug (Doppelklick im Logbuch).":
        "Black = no apparent cause: check servos. Details in the single flight (double-click in the logbook).",
    "Senderakku min. [V]": "Transmitter battery min. [V]",
    "Tiefster Wert des Senderakkus im Flug.": "Lowest value of the transmitter battery in flight.",

    # ---------------- charts: single flight ----------------
    "Akku & Antrieb": "Battery & drive",
    "Empfang": "Reception",
    "Empfängerstrom & Steuerung": "Receiver current & controls",
    "Fluglage": "Attitude",
    "Ri {ri:.2f} mΩ/Zelle": "Ri {ri:.2f} mΩ/cell",
    "Flug {no} – {date} – {dur} – {drawn:.0f} mAh – {ri}": "Flight {no} – {date} – {dur} – {drawn:.0f} mAh – {ri}",
    "Für diese Ansicht sind keine Daten im Log.": "The log contains no data for this view.",
    " Timer-Empfehlung": " timer recommendation",
    "entnommen": "drawn",
    "Leistung": "Power",
    "Gestrichelt: geschätzte Spannung ohne Last. Abstand = Spannungsabfall durch den Innenwiderstand.":
        "Dashed: estimated voltage without load. Gap = voltage drop across the internal resistance.",
    "Spannung": "Voltage",
    "Ruhespannung (geschätzt)": "Resting voltage (estimated)",
    "Akkustrom": "Battery current",
    "Strom aus dem Flugakku.": "Current from the flight battery.",
    "Strom": "Current",
    "Drehzahl": "RPM",
    "1000 U/min": "1000 rpm",
    "Drehzahl des Antriebs.": "RPM of the drive.",
    "Höhe": "Altitude",
    "Relative Höhe über dem Startpunkt.": "Relative altitude above the take-off point.",
    "Empfangsstärke (RSSI)": "Signal strength (RSSI)",
    "Ethos warnt üblicherweise unter 45.": "Ethos usually warns below 45.",
    "Telemetrie-Rahmen (VFR)": "Telemetry frames (VFR)",
    "Anteil korrekt empfangener Rahmen. Einbrüche = Empfangsstörung.":
        "Share of correctly received frames. Dips = reception problem.",
    "Zum Abgleich: Einbrüche bei großer Höhe/Entfernung oder in bestimmten Fluglagen?":
        "For comparison: dips at high altitude/distance or in certain attitudes?",
    "Empfängerstrom": "Receiver current",
    "Dreiecke: Spitzen über der gestrichelten Schwelle, Farbe = Anlass.":
        "Triangles: spikes above the dashed threshold, colour = cause.",
    "Spitzenschwelle {thr:.2f} A": "Spike threshold {thr:.2f} A",
    "Spitze: {cause}": "Spike: {cause}",
    "Knüppelwege": "Stick travel",
    "Schnelle, große Ausschläge erzeugen Servolast. Senkrechte Linien: Schalter.":
        "Fast, large deflections create servo load. Vertical lines: switches.",
    "Gasknüppel.": "Throttle stick.",
    "Bricht sie bei Stromspitzen ein, ist die Versorgung zu schwach.":
        "If it drops during current spikes, the supply is too weak.",
    "Roll": "Roll",
    "Nick": "Pitch",
    "Beschleunigung, 1 g = Geradeausflug.": "Acceleration, 1 g = straight and level flight.",

    # ---------------- table headings ----------------
    "Datum": "Date",
    "entnommen mAh": "drawn mAh",
    "ESC mAh": "ESC mAh",
    "Abw. %": "Dev. %",
    "Energie Wh": "Energy Wh",
    "Ø A": "Ø A",
    "max A": "max A",
    "P max W": "P max W",
    "C Spitze": "C peak",
    "SoC Start %": "SoC start %",
    "SoC Ende %": "SoC end %",
    "SoC Ende (U) %": "SoC end (V) %",
    "SoC Abw. Pkt": "SoC dev. pts",
    "Kapazität mAh": "Capacity mAh",
    "Ri/Zelle mΩ": "Ri/cell mΩ",
    "Ri Anfang": "Ri start",
    "Ri Ende": "Ri end",
    "U Ref V/Z": "V ref V/c",
    "U min V/Z": "V min V/c",
    "U Ende V/Z": "V end V/c",
    "U Ende Quelle": "V end source",
    "Reserve V/Z": "Reserve V/c",
    "rpm P90": "rpm P90",
    "P Ref W": "P ref W",
    "Höhe max": "Alt. max",
    "Wh/100m": "Wh/100m",
    "g max": "g max",
    "RSSI min": "RSSI min",
    "VFR min": "VFR min",
    "Rx V min": "Rx V min",
    "Rx A Ø": "Rx A Ø",
    "Rx A max": "Rx A max",
    "Rx Spitzen": "Rx spikes",
    "Sp. Schalter": "Sp. switch",
    "Sp. o. Anlass": "Sp. no cause",
    "r Rx/Knüppel": "r Rx/stick",
    "R² Fit": "R² fit",
    "Versatz s": "Offset s",
    "Auffälligkeiten": "Anomalies",

    # ---------------- data quality, ageing model, period filter ----------------
    "Stromsensor hängt am Anschlag":
        "Current sensor stuck at its limit",
    "Spannungsausfall":
        "Voltage dropout",
    "Ruhespannung nach der Landung unmöglich":
        "Impossible rest voltage after landing",
    "VFR außerhalb 0–100 %":
        "VFR outside 0–100 %",
    "Innenwiderstand unplausibel":
        "Implausible internal resistance",
    "Der Strom liegt fast den ganzen Flug am Höchstwert (Sensor übersteuert oder falsch skaliert). Entnommene Ladung, Ladezustand, Kapazität, Innenwiderstand und Timer dieser Flüge werden nicht verwendet.":
        "The current stays at its maximum for almost the whole flight (sensor saturated or wrongly scaled). Drawn charge, state of charge, capacity, internal resistance and timer of these flights are not used.",
    "Die Spannung fällt im Flug auf unter {limit:.1f} V/Zelle (Sensor- oder Kabelausfall, kein Spannungseinbruch des Akkus). Spannungs- und Akkuwerte dieser Flüge werden nicht verwendet.":
        "The voltage drops below {limit:.1f} V/cell during the flight (sensor or cable failure, not a voltage sag of the battery). Voltage and battery values of these flights are not used.",
    "Die gemessene Spannung nach der Landung liegt unter der Spannung unter Last am Flugende – das ist physikalisch unmöglich (Akku vermutlich abgesteckt oder Sensor aus, bevor die Messung fertig war). Verwendet wird die Modellschätzung der Ruhespannung; keine Tiefentladung.":
        "The voltage measured after landing is below the voltage under load at the end of the flight – physically impossible (battery probably unplugged or sensor switched off before the measurement was complete). The model estimate of the rest voltage is used; no deep discharge.",
    "VFR-Werte außerhalb von 0–100 % (ältere Firmware oder Sensorfehler) werden nicht verwendet.":
        "VFR values outside 0–100 % (older firmware or sensor error) are not used.",
    "Innenwiderstand weniger als halb oder mehr als doppelt so groß wie der Median aller Flüge (Fit gescheitert, z. B. wegen fehlerhafter Strom- oder Spannungswerte). Wird nicht für Trends verwendet.":
        "Internal resistance less than half or more than twice the median of all flights (fit failed, e.g. because of faulty current or voltage values). Not used for trends.",
    "Kapazität normiert":
        "Capacity normalised",
    "Messfehler":
        "Measurement errors",
    "Auf {depth:.0f} % Entladetiefe bezogen.":
        "Referred to {depth:.0f} % depth of discharge.",
    "80 % der Nennkapazität":
        "80 % of the nominal capacity",
    "zu wenige Flüge mit gültigen Werten für einen Trend (mindestens {min} über {span} Flüge)":
        "too few flights with valid values for a trend (at least {min} over {span} flights)",
    "  Trend: {slope} {unit} je 100 Flüge (90 %-Bereich {lo} bis {hi}) – {verdict}":
        "  Trend: {slope} {unit} per 100 flights (90 % range {lo} to {hi}) – {verdict}",
    "die Werte streuen zu stark (±{pct:.0f} %)":
        "the values scatter too much (±{pct:.0f} %)",
    "kein gesicherter Trend – der 90-%-Bereich der Steigung schließt null ein":
        "no reliable trend – the 90 % range of the slope includes zero",
    "der Wert verbessert sich über den Zeitraum – kein Alterungssignal (z. B. Temperatur, Jahreszeit oder Einfliegen)":
        "the value improves over the period – no sign of ageing (e.g. temperature, season or breaking in)",
    "  Trend: zu wenige Flüge für einen Trend (mindestens {min} über {span} Flüge)":
        "  Trend: too few flights for a trend (at least {min} over {span} flights)",
    "kein gesicherter Trend":
        "no reliable trend",
    "gesichert fallend":
        "reliably falling",
    "gesichert steigend":
        "reliably rising",
    "DATENQUALITÄT (Messfehler, nicht in Trends und Warnungen)":
        "DATA QUALITY (measurement errors, not used in trends and warnings)",
    "Restkapazität (SoH): ca. {soh:.0f} % der Nennkapazität  (aktuell ≈ {cur:.0f} ± {err} mAh, Nennkapazität {nom:.0f} mAh)":
        "Remaining capacity (SoH): approx. {soh:.0f} % of the nominal capacity  (currently ≈ {cur:.0f} ± {err} mAh, nominal capacity {nom:.0f} mAh)",
    "Restkapazität (SoH): ca. {soh:.0f} % der Anfangskapazität  (aktuell ≈ {cur:.0f} ± {err} mAh, Anfangswert ≈ {start:.0f} mAh; Nennkapazität nicht eingetragen)":
        "Remaining capacity (SoH): approx. {soh:.0f} % of the initial capacity  (currently ≈ {cur:.0f} ± {err} mAh, initial value ≈ {start:.0f} mAh; nominal capacity not entered)",
    "Restlebensdauer: ca. {n:.0f} Flüge (90 %-Bereich {lo:.0f}–{hi:.0f}) – das frühere der Kriterien 80 % SoH und +50 % Ri":
        "Remaining life: approx. {n:.0f} flights (90 % range {lo:.0f}–{hi:.0f}) – the earlier of the criteria 80 % SoH and +50 % Ri",
    "Hinweis auf mehrere Akkus: Die Kapazitätswerte bilden zwei Gruppen (≈ {low:.0f} mAh in {n_low} Flügen, ≈ {high:.0f} mAh in {n_high} Flügen). Alterungsaussagen über diesen Zeitraum gelten dann für keinen einzelnen Akku. Zeitraum auf einen Akku eingrenzen (Daten & Einstellungen → Zeitraum).":
        "Sign of several batteries: the capacity values form two groups (≈ {low:.0f} mAh in {n_low} flights, ≈ {high:.0f} mAh in {n_high} flights). Statements about ageing over this period then apply to no single battery. Limit the period to one battery (Data & settings → Period).",
    "Kapazitäts-SoH nicht bestimmbar: zu wenige Flüge mit gültiger Kapazitätsschätzung (≥ 40 % Entladetiefe; vorhanden {n}, nötig {min}).":
        "Capacity SoH cannot be determined: too few flights with a valid capacity estimate (≥ 40 % depth of discharge; available {n}, needed {min}).",
    "Keine Messfehler erkannt.":
        "No measurement errors detected.",
    "MESSFEHLER IN DIESEM FLUG (nicht in Trends und Warnungen)":
        "MEASUREMENT ERRORS IN THIS FLIGHT (not used in trends and warnings)",
    "  gegenüber dem Anfangswert dieses Zeitraums (≈ {start:.0f} mAh bei Flug {first:.0f}): {pct:+.1f} %":
        "  compared with the initial value of this period (≈ {start:.0f} mAh at flight {first:.0f}): {pct:+.1f} %",
    "  Prognose: 80 % SoH in ca. {n:.0f} weiteren Flügen (90 %-Bereich {lo:.0f}–{hi:.0f})":
        "  Forecast: 80 % SoH in approx. {n:.0f} more flights (90 % range {lo:.0f}–{hi:.0f})",
    "  Prognose: +50 % Ri (Faustregel Lebensende) in ca. {n:.0f} weiteren Flügen (90 %-Bereich {lo:.0f}–{hi:.0f})":
        "  Forecast: +50 % Ri (rule of thumb for end of life) in approx. {n:.0f} more flights (90 % range {lo:.0f}–{hi:.0f})",
    "Restlebensdauer: keine belastbare Prognose im gewählten Zeitraum (Gründe siehe oben).":
        "Remaining life: no reliable forecast for the selected period (reasons see above).",
    "  80 % SoH ist bereits erreicht.":
        "  80 % SoH has already been reached.",
    "  Keine Prognose: {reason}.":
        "  No forecast: {reason}.",
    "  +50 % Ri ist bereits erreicht.":
        "  +50 % Ri has already been reached.",
    "  Keine Ri-Prognose: {reason}.":
        "  No Ri forecast: {reason}.",
    "  Trend nicht belastbar: ohne Entladetiefen-Korrektur {raw:+.0f} mAh je 100 Flüge, mit Korrektur {corr:+.0f} mAh je 100 Flüge – die Richtung hängt allein an der Korrektur, weil später tiefer geflogen wurde.":
        "  Trend not reliable: without depth-of-discharge correction {raw:+.0f} mAh per 100 flights, with correction {corr:+.0f} mAh per 100 flights – the direction depends only on the correction, because later flights went deeper.",
    " Linie gestrichelt: kein gesicherter Trend (Mittelwert).":
        " Dashed line: no reliable trend (mean value).",
    "Trend unsicher, siehe Bericht.":
        "Trend uncertain, see report.",
    "steigend":
        "rising",
    "fallend":
        "falling",
    "ohne gesicherten Trend":
        "no reliable trend",
    "die Trendaussage ist unsicher (siehe oben)":
        "the trend is uncertain (see above)",
    "rechnerisch {verdict}, aber unsicher":
        "computed {verdict}, but uncertain",
    "  Unsicher: Die Kapazität scheint zu steigen – bei einem Akku unplausibel (Streuung der Schätzung, Temperatur, Jahreszeit). Angezeigt wird der Mittelwert ohne Trend.":
        "  Uncertain: the capacity appears to rise – implausible for a battery (scatter of the estimate, temperature, season). The mean value without trend is shown.",
    "  Kapazität einheitlich auf {depth:.0f} % Entladetiefe bezogen. Die Schätzung hängt von der Entladetiefe ab: {coef:+.0f} ± {se:.0f} mAh je Prozentpunkt, ermittelt nur aus Flügen am selben Tag ({days} Tage), damit der Alterungstrend nicht mitgeschätzt wird.":
        "  Capacity uniformly referred to {depth:.0f} % depth of discharge. The estimate depends on the depth of discharge: {coef:+.0f} ± {se:.0f} mAh per percentage point, determined only from flights on the same day ({days} days), so that the ageing trend is not estimated along with it.",
    "Innenwiderstand je Zelle: ≈ {r:.2f} mΩ, keine gesicherte Änderung (Mittelwert)":
        "Internal resistance per cell: ≈ {r:.2f} mΩ, no confirmed change (mean value)",
    "  Kurzflüge unter {pct:.0f} % Entladetiefe zählen nicht für Kapazität und Innenwiderstand: Flug {flights}":
        "  Short flights below {pct:.0f} % depth of discharge are not used for capacity and internal resistance: flight {flights}",
    "Spannung bei {iref:.0f} A / {qref:.0f} mAh: ≈ {u:.3f} V/Zelle, keine gesicherte Änderung (Mittelwert)":
        "Voltage at {iref:.0f} A / {qref:.0f} mAh: ≈ {u:.3f} V/cell, no confirmed change (mean value)",
    "  Unsicher: Kapazität und Spannung bei Referenzlast zeigen nicht in dieselbe Richtung (Kapazität: {cap}, Spannung: {uref}). Kapazität ohne Trend angezeigt, keine Prognose.":
        "  Uncertain: capacity and voltage at reference load do not point in the same direction (capacity: {cap}, voltage: {uref}). Capacity shown without trend, no forecast.",
    "  gegenüber dem Anfang dieses Zeitraums: keine gesicherte Änderung (Wert = Mittelwert über den Zeitraum)":
        "  compared with the start of this period: no confirmed change (value = mean over the period)",
    "  Unsicher: Die Entladetiefe ändert sich über den Zeitraum (r = {r:.2f}). Ohne mehrere Flüge am selben Tag lässt sich ihr Einfluss nicht vom Alterungstrend trennen.":
        "  Uncertain: the depth of discharge changes over the period (r = {r:.2f}). Without several flights on the same day its effect cannot be separated from the ageing trend.",
    "EthosLogAnalyser {version} – Flug- und Akku-Analyse (FrSky Ethos Logs)":
        "EthosLogAnalyser {version} – flight and battery analysis (FrSky Ethos logs)",
    "TESTVERSION {version} – EthosLogAnalyser – nicht für den normalen Gebrauch":
        "TEST VERSION {version} – EthosLogAnalyser – not for regular use",
    "EthosLogAnalyser, Version {version}":
        "EthosLogAnalyser, version {version}",
    "Testversion ({tag}) aus der automatischen Prüfung eines Pull-Requests bzw. Branches – zum Abnahmetest, kein Release.":
        "Test version ({tag}) from the automatic checks of a pull request or branch – for acceptance testing, not a release.",
    "Quellcode, Releases und Anleitung: github.com/RollingGecko/EthosLogAnalyser":
        "Source code, releases and documentation: github.com/RollingGecko/EthosLogAnalyser",
    "Über":
        "About",
    "  t = {t}  {peak:.2f} A, {dur:.1f} s  →  {why}:  Knüppel {stick} %/s, Drehrate {rate} °/s, {g} g, Gas {gas} %, Höhe {alt} m":
        "  t = {t}  {peak:.2f} A, {dur:.1f} s  →  {why}:  stick {stick} %/s, rotation rate {rate} °/s, {g} g, throttle {gas} %, altitude {alt} m",
    "Mittlere Leistung {value}, {t80} über 80 % des Spitzenstroms, mittleres Gas {gas} %":
        "Mean power {value}, {t80} above 80 % of the peak current, mean throttle {gas} %",
    "zu kurz ({dur} < {min})":
        "too short ({dur} < {min})",
    "Zeit seit Motorstart [min:s]":
        "Time since motor start [min:s]",
    "Flugzeit und Timer-Empfehlung [min:s]":
        "Flight time and timer recommendation [min:s]",
    "Dauer min:s":
        "Duration min:s",
    "Timer min:s":
        "Timer min:s",
    "Flug {no} – {date}":
        "Flight {no} – {date}",
    "Flug {no}":
        "Flight {no}",
    "Schließen (Esc)":
        "Close (Esc)",
    "{title} – Vollbild (Esc schließt)":
        "{title} – full screen (Esc closes)",
    "Maus über einen Datenpunkt: Wert.  Werkzeugleiste unten: zoomen, verschieben, speichern.":
        "Mouse over a data point: its value.  Toolbar below: zoom, pan, save.",
    "Maus über das Diagramm bewegen: Werte zum Zeitpunkt.   Mausrad: zoomen  ·  Ziehen mit linker Maustaste: verschieben  ·  Doppelklick oder Rechtsklick: Diagramm vergrößern":
        "Move the mouse over the chart: values at that time.   Mouse wheel: zoom  ·  drag with the left mouse button: pan  ·  double-click or right-click: enlarge the chart",
    "Ganze Seite vergrößern":
        "Enlarge whole page",
    "Dieses Diagramm vergrößern":
        "Enlarge this chart",
    "Doppelklick oder Rechtsklick auf ein Diagramm: allein vergrößern":
        "Double-click or right-click a chart to enlarge it on its own",
    "P Abw. Kurve %":
        "P dev. curve %",
    "V/Zelle":
        "V/cell",
    "Akkuspannung je Zelle":
        "Battery voltage per cell",
    "Akkuspannung (gesamt)":
        "Battery voltage (total)",
    "Mittlere Zellspannung = Gesamtspannung / {cells} Zellen.":
        "Mean cell voltage = total voltage / {cells} cells.",
    "Zellenzahl unbekannt: Gesamtspannung des Akkus.":
        "Cell count unknown: total battery voltage.",
    "Rollwinkel und Querruder":
        "Roll angle and aileron",
    "Links Rollwinkel [°], rechts Querruder-Knüppel [%] (Ethos-Kanalwert, ±100 % = Vollausschlag).":
        "Left: roll angle [°], right: aileron stick [%] (Ethos channel value, ±100 % = full deflection).",
    "Nickwinkel und Höhenruder":
        "Pitch angle and elevator",
    "Links Nickwinkel [°], rechts Höhenruder-Knüppel [%] (Ethos-Kanalwert).":
        "Left: pitch angle [°], right: elevator stick [%] (Ethos channel value).",
    "Gas und Seitenruder":
        "Throttle and rudder",
    "Gas 0–100 %, Seitenruder-Knüppel ±100 %. Senkrechte Linien: Schalter.":
        "Throttle 0–100 %, rudder stick ±100 %. Vertical lines: switches.",
    "Grenze unter Last {v:.2f} V/Zelle":
        "Limit under load {v:.2f} V/cell",
    "Mindest-Ruhespannung {v:.2f} V/Zelle":
        "Minimum resting voltage {v:.2f} V/cell",
    "{stick} (Knüppel)":
        "{stick} (stick)",
    "Nicht im Log oder nicht bewegt: {channels}.":
        "Not in the log or not moved: {channels}.",
    "Farbe: frühe Flüge violett → späte gelb. Schwarz: Gesamtkennlinie aller Flüge mit Streuband. Liegt ein Flug darüber, braucht er mehr Leistung bei gleicher Drehzahl: Verschleiß/Fremdkörper.":
        "Colour: early flights purple → late yellow. Black: overall curve of all flights with spread band. A flight above it needs more power at the same RPM: wear/foreign object.",
    "Gesamtkennlinie (Median aller Flüge)":
        "Overall curve (median of all flights)",
    "Streuband 25–75 %":
        "Spread band 25–75 %",
    "Gesamtkennlinie: {classes} Drehzahlklassen aus {n} Flügen; Flüge weichen {lo:+.1f} bis {hi:+.1f} % davon ab (größte Abweichung: Flug {no})":
        "Overall curve: {classes} RPM classes from {n} flights; flights deviate from it by {lo:+.1f} to {hi:+.1f} % (largest deviation: flight {no})",
    "Leistung gegenüber der Gesamtkennlinie aller Flüge: {dev:+.1f} % (Median bei gleicher Drehzahl)":
        "Power compared with the overall curve of all flights: {dev:+.1f} % (median at the same RPM)",
    "(unbekannt)":
        "(unknown)",
    "Für das Modell {model} sind noch keine Akku-Einstellungen gespeichert: Bitte im Reiter „Daten & Einstellungen“ die Zellchemie auswählen und die Nennkapazität eintragen. Bis dahin wird LiPo angenommen – Ladezustand, Alterung und Restkapazität können falsch sein.":
        "No battery settings are stored for the model {model} yet: please choose the cell chemistry and enter the nominal capacity in the tab “Data & settings”. Until then LiPo is assumed – state of charge, ageing and remaining capacity may be wrong.",
    "Für dieses Modell noch nicht eingestellt: bitte Zellchemie auswählen und Nennkapazität eintragen (bis dahin wird LiPo angenommen).":
        "Not set up for this model yet: please choose the cell chemistry and enter the nominal capacity (until then LiPo is assumed).",
    "Akku-Einstellungen für dieses Modell fehlen":
        "Battery settings missing for this model",
    "Logbuch":
        "Logbook",
    "Summen":
        "Totals",
    "Je Flugzeug":
        "Per aircraft",
    "Je Jahr":
        "Per year",
    "Jahr":
        "Year",
    "Je Monat":
        "Per month",
    "Monat":
        "Month",
    "Uhrzeit":
        "Time",
    "Log-Dauer":
        "Log duration",
    "{ah:.1f} Ah ({mah:.0f} mAh)":
        "{ah:.1f} Ah ({mah:.0f} mAh)",
    "Flüge":
        "Flights",
    "Flugtage":
        "Flying days",
    "Log-Dauer gesamt":
        "Total log duration",
    "Längster Flug (Log-Dauer)":
        "Longest flight (log duration)",
    "Kürzester Flug (Log-Dauer)":
        "Shortest flight (log duration)",
    "Entnommen gesamt":
        "Total drawn",
    "{n} Flüge ohne Datum oder Log-Dauer – in den Summen nicht enthalten.":
        "{n} flights without date or log duration – not included in the totals.",
    "{n}  ({first} – {last})":
        "{n}  ({first} – {last})",
    "Log-Dauer = Zeit von „Motor scharf“ bis „Motor gesperrt“ im Log, nicht die reine Flugzeit.":
        "Log duration = time from “motor armed” to “motor disarmed” in the log, not the pure flight time.",
    "{dur}  (Flug {no}, {date})":
        "{dur}  (flight {no}, {date})",

    # ---------------- flight database ----------------
    "Analysefehler: {err}":
        "Analysis error: {err}",
    "Datenbank":
        "Database",
    "Es wurde eine neue Flug-Datenbank angelegt:\n{path}\n\nSollen die Logs aus dem bisher genutzten Ordner importiert werden?\n{folder}":
        "A new flight database has been created:\n{path}\n\nImport the logs from the folder used so far?\n{folder}",
    "neu":
        "new",
    "doppelt":
        "duplicate",
    "mögliches Duplikat":
        "possible duplicate",
    "nicht lesbar":
        "unreadable",
    "{size} MB":
        "{size} MB",
    "{size} kB":
        "{size} kB",
    "{new} neu (davon {flights} Flüge), {duplicate} doppelt, {suspicious} mögliche Duplikate, {unreadable} nicht lesbar":
        "{new} new ({flights} of them flights), {duplicate} duplicates, {suspicious} possible duplicates, {unreadable} unreadable",
    "gleicher Inhalt wie {file} (übersprungen)":
        "same content as {file} (skipped)",
    "gleiches Modell und gleiche Startzeit wie {file} (importiert, markiert)":
        "same model and start time as {file} (imported, marked)",
    "kein Flug":
        "not a flight",
    "Import-Bericht":
        "Import report",
    "abgebrochen":
        "cancelled",
    "Ergebnis":
        "Result",
    "Hinweis":
        "Note",
    "Datenbank leeren":
        "Empty database",
    "Alle importierten Logs und Flüge aus der Datenbank löschen?\n\nDie Logdateien selbst bleiben unverändert.":
        "Delete all imported logs and flights from the database?\n\nThe log files themselves stay unchanged.",
    "Neu …":
        "New …",
    "Öffnen …":
        "Open …",
    "Speichern unter …":
        "Save as …",
    "Leeren …":
        "Empty …",
    "Dateien importieren …":
        "Import files …",
    "Ordner importieren …":
        "Import folder …",
    "Flug-Datenbank":
        "Flight database",
    "Alle Dateien":
        "All files",
    "Neue Datenbank anlegen":
        "Create new database",
    "Datenbank öffnen":
        "Open database",
    "Datenbank speichern unter":
        "Save database as",
    "Eine Kopie der Datenbank wurde gespeichert:\n{path}\n\nGeöffnet bleibt weiterhin:\n{current}":
        "A copy of the database has been saved:\n{path}\n\nStill open:\n{current}",
    "Logdateien importieren":
        "Import log files",
    "Ordner importieren (mit Unterordnern)":
        "Import folder (with subfolders)",
    "keine Datenbank geöffnet":
        "no database open",
    "{logs} Logs: {flights} Flüge, {other} ohne Flug · Flugzeuge: {aircraft} · {size}":
        "{logs} logs: {flights} flights, {other} without flight · aircraft: {aircraft} · {size}",
    "Die Datei kann nicht als Flug-Datenbank geöffnet werden:\n{path}\n\n{error}":
        "The file cannot be opened as a flight database:\n{path}\n\n{error}",
    "Die Datenbank kann nicht angelegt werden:\n{path}\n\n{error}":
        "The database cannot be created:\n{path}\n\n{error}",
    "Die Kopie kann nicht gespeichert werden:\n{path}\n\n{error}":
        "The copy cannot be saved:\n{path}\n\n{error}",
    "Die zuletzt geöffnete Datenbank wurde nicht gefunden:\n{path}\n\nEs wird die Standard-Datenbank verwendet.":
        "The database opened last was not found:\n{path}\n\nThe default database is used.",
    "Fehler bei der Verarbeitung:\n{error}":
        "Processing error:\n{error}",
    "Schließen":
        "Close",
    "Datei:":
        "File:",
    "{done} von {total}: {file}":
        "{done} of {total}: {file}",
    "wird vorbereitet …":
        "preparing …",
    "Letzter Import: {summary}":
        "Last import: {summary}",
    "Ethos-Logs":
        "Ethos logs",
    "Auswertungswerte für die Statistik werden vorbereitet":
        "Preparing the values for the statistics",
    "Neuberechnung":
        "Recalculation",

    # ---------------- areas, single flight from the database ----------------
    "Statistik":
        "Statistics",
    "Noch keine Flüge in der Datenbank.\n\nLogs importieren: „Daten & Einstellungen“ → Bereich „Datenbank“ → „Ordner importieren …“ oder „Dateien importieren …“.":
        "No flights in the database yet.\n\nImport logs: “Data & settings” → section “Database” → “Import folder …” or “Import files …”.",
    "Für diesen Flug sind keine Spannungs- und Stromdaten des Flugakkus im Log.\nDie Einzelflug-Ansichten brauchen sie bisher.":
        "The log of this flight has no voltage and current of the flight battery.\nThe single-flight views need them so far.",
    "Die Flüge von {aircraft} konnten nicht aus der Datenbank vorbereitet werden.":
        "The flights of {aircraft} could not be prepared from the database.",
    "Die Flüge von {aircraft} werden aus der Datenbank vorbereitet …":
        "Preparing the flights of {aircraft} from the database …",
    "Vorbereitet: {done} von {total} Flügen":
        "Prepared: {done} of {total} flights",
    "keine Diagramme für diesen Flug":
        "no charts for this flight",
    "‹ Logbuch":
        "‹ Logbook",
    "Flüge (Klick auf eine Spaltenüberschrift sortiert, Doppelklick öffnet den Einzelflug)":
        "Flights (click a column heading to sort, double-click opens the single flight)",
    "Flug-Datenbank  ·  {flights} Flüge, {aircraft} Flugzeuge  ·  {first} – {last}":
        "Flight database  ·  {flights} flights, {aircraft} aircraft  ·  {first} – {last}",
    "Die Flug-Datenbank enthält noch keine Flüge – Logs unter „Daten & Einstellungen“ → „Datenbank“ importieren.":
        "The flight database has no flights yet – import logs under “Data & settings” → “Database”.",
    "  ·  {n} Logs ohne Flug":
        "  ·  {n} logs that are not flights",
    "Dieser Log ist nicht als Flug gezählt. Zum Ansehen im Logbuch in der Spalte „Flug“ auf ☑ umschalten.":
        "This log is not counted as a flight. To look at it, switch it to ☑ in the “Flight” column of the logbook.",
    "alle":
        "all",
    "Flugzeug":
        "Aircraft",
    "von":
        "from",
    "bis":
        "to",
    "Zurücksetzen":
        "Reset",
    "Filter:":
        "Filter:",
    "Nr.":
        "No.",
    "Mögliches Duplikat: gleiches Flugzeug und gleiche Startzeit wie ein anderer Flug":
        "Possible duplicate: same aircraft and start time as another flight",
    "Summe":
        "Total",
    "{n} von {total} Flügen der Datenbank":
        "{n} of {total} flights of the database",
    "  – ohne {n} Flüge ohne gültige Akkuwerte":
        "  – without {n} flights without valid battery values",
    "Nicht-Flüge anzeigen":
        "Show non-flights",
    "{dur}  (Flug {no} der {aircraft}, {date})":
        "{dur}  (flight {no} of {aircraft}, {date})",
    "  ·  Filter aktiv":
        "  ·  filter active",
    "Noch keine Flüge in der Datenbank. Logs importieren: „Daten & Einstellungen“ → „Datenbank“ → „Ordner importieren …“ oder „Dateien importieren …“.":
        "No flights in the database yet. Import logs: “Data & settings” → “Database” → “Import folder …” or “Import files …”.",
    # notes and anomalies (WP-18)
    'kürzer als dieser Anteil des Medians': 'shorter than this share of the median',
    'über dem Median': 'above the median',
    'unter dem Median': 'below the median',
    'unter dem eigenen Median des Flugs': "below the flight's own median",
    'Spitzen je Flug': 'spikes per flight',
    'Abweichung': 'deviation',
    'Flug deutlich kürzer als üblich': 'Flight much shorter than usual',
    'Innenwiderstand höher als üblich': 'Internal resistance higher than usual',
    'Empfängerstrom-Maximum höher als üblich': 'Receiver current maximum higher than usual',
    'RSSI-Minimum niedriger als üblich': 'RSSI minimum lower than usual',
    'Einbruch der Empfängerspannung im Flug': 'Receiver voltage dip during the flight',
    'Zellspannung unter Last unter der Grenze der Zellchemie': 'Cell voltage under load below the limit of the cell chemistry',
    'Ruhespannung am Flugende unter der Grenze der Zellchemie': 'Resting voltage at the end below the limit of the cell chemistry',
    'Empfängerspannung unter der Mindestspannung des Modells': "Receiver voltage below the model's minimum voltage",
    'Empfängerstrom-Spitzen ohne erkennbaren Anlass': 'Receiver current spikes without apparent cause',
    'Strommessung weicht vom ESC-Zähler ab': 'Current measurement deviates from the ESC counter',
    'Flug deutlich kürzer als üblich: {value} statt typisch {median} (Median der Flüge dieses Flugzeugs). Nur ein Hinweis – z. B. ein abgebrochener oder vorzeitig gelandeter Flug.': 'Flight much shorter than usual: {value} instead of typically {median} (median of the flights of this aircraft). Only a hint – e.g. an aborted flight or an early landing.',
    'Innenwiderstand {value:.0f} mΩ, {percent:.0f} % über dem Median dieses Flugzeugs ({median:.0f} mΩ). Hinweis: kalter oder nicht voll geladener Akku, Alterung oder ein kurzer Flug mit wenig Entladung sind mögliche Gründe.': 'Internal resistance {value:.0f} mΩ, {percent:.0f} % above the median of this aircraft ({median:.0f} mΩ). Hint: a cold or not fully charged battery, ageing or a short flight with little discharge are possible reasons.',
    'Höchster Empfängerstrom {value:.2f} A, {percent:.0f} % über dem Median dieses Flugzeugs ({median:.2f} A). Hinweis: Servos auf Schwergängigkeit oder Blockieren prüfen; Zeitpunkte der Stromspitzen siehe Diagramm „Empfängerstrom“.': 'Highest receiver current {value:.2f} A, {percent:.0f} % above the median of this aircraft ({median:.2f} A). Hint: check the servos for stiffness or binding; times of the current spikes see the chart “Receiver current”.',
    'RSSI-Minimum {value:.0f} dB, {difference:.0f} dB unter dem Median dieses Flugzeugs ({median:.0f} dB). Hinweis: größere Entfernung, Fluglage oder Antennen prüfen.': 'RSSI minimum {value:.0f} dB, {difference:.0f} dB below the median of this aircraft ({median:.0f} dB). Hint: check for a larger distance, the attitude or the antennas.',
    'Empfängerspannung fiel bei {time} auf {low:.2f} V, {percent:.0f} % unter ihren üblichen Wert in diesem Flug ({median:.2f} V). Hinweis: Empfängerstromversorgung, Stecker und Kabel prüfen.': 'Receiver voltage dropped to {low:.2f} V at {time}, {percent:.0f} % below its usual value in this flight ({median:.2f} V). Hint: check the receiver power supply, connectors and cables.',
    'Spannung unter Last fiel auf {value:.2f} V/Zelle, unter die Grenze von {limit:.2f} V/Zelle für {chem} ({cells} Zellen). Hinweis: möglicherweise zu tief entladen – bitte auch Zellchemie und Zellenzahl in den Akku-Einstellungen prüfen.': 'Voltage under load fell to {value:.2f} V/cell, below the limit of {limit:.2f} V/cell for {chem} ({cells} cells). Hint: possibly discharged too deeply – please also check cell chemistry and cell count in the battery settings.',
    'Ruhespannung am Flugende {value:.2f} V/Zelle, unter der Grenze von {limit:.2f} V/Zelle für {chem} ({cells} Zellen). Hinweis: möglicherweise zu tief entladen – bitte auch Zellchemie und Zellenzahl prüfen.': 'Resting voltage at the end of the flight {value:.2f} V/cell, below the limit of {limit:.2f} V/cell for {chem} ({cells} cells). Hint: possibly discharged too deeply – please also check cell chemistry and cell count.',
    'Empfängerspannung fiel auf {value:.2f} V, unter die eingestellte Mindestspannung von {limit:.2f} V für dieses Modell. Hinweis: Empfängerstromversorgung prüfen.': 'Receiver voltage fell to {value:.2f} V, below the minimum voltage of {limit:.2f} V set for this model. Hint: check the receiver power supply.',
    '{n} Empfängerstrom-Spitzen ohne Manöver, Start oder Landung. Hinweis: Servos auf Schwergängigkeit, Anschlag (Brummen in Endlage) und Defekte prüfen; Zeitpunkte siehe Einzelflug.': '{n} receiver current spikes without manoeuvre, take-off or landing. Hint: check the servos for stiffness, stalling at the end stop (buzzing) and defects; times see the single flight.',
    'Entnommene Ladung aus der Strommessung ({drawn:.0f} mAh) weicht um {percent:+.1f} % vom ESC-Zähler ({counter:.0f} mAh) ab. Hinweis: Stromsensor prüfen oder kalibrieren.': 'Drawn charge from the current measurement ({drawn:.0f} mAh) deviates by {percent:+.1f} % from the ESC counter ({counter:.0f} mAh). Hint: check or calibrate the current sensor.',
    'Zuletzt gefunden: {n} automatische Hinweise.': 'Last found: {n} automatic hints.',
    'Regeln für die automatischen Hinweise je Flug (immer nur Hinweise, keine Diagnose). Vergleiche mit dem Median gelten ab 5 Flügen eines Flugzeugs.': 'Rules for the automatic hints per flight (always hints only, never a diagnosis). Comparisons with the median apply from 5 flights of an aircraft on.',
    'V (leer = aus)': 'V (empty = off)',
    'Info': 'Info',
    'Warnung': 'Warning',
    'Kritisch': 'Critical',
    'automatisch': 'automatic',
    'eigener Eintrag': 'own entry',
    'quittiert': 'acknowledged',
    'offen': 'open',
    'Stufe': 'Level',
    'Status': 'Status',
    'Herkunft': 'Origin',
    'Eigener Eintrag': 'Own entry',
    'Notiz und Auffälligkeiten': 'Note and anomalies',
    'Notiz speichern': 'Save note',
    'Quittieren / wieder öffnen': 'Acknowledge / reopen',
    'Eigener Eintrag …': 'Own entry …',
    'Eintrag löschen': 'Delete entry',
    'Keine Auffälligkeiten für diesen Flug.': 'No anomalies for this flight.',
    'Notiz:': 'Note:',
    'Hinweis:': 'Hint:',
    'Stufe:': 'Level:',
    'OK': 'OK',
    'Abbrechen': 'Cancel',
    'nur mit Notiz oder Auffälligkeit': 'only with note or anomaly',
    # statistics from the flight database (WP-19)
    'Statistik  ·  {n} von {total} Flügen der Datenbank': 'Statistics  ·  {n} of {total} flights of the database',
    'Filter: {filter}': 'Filter: {filter}',
    'Die Statistik zeigt gerade keine Flüge:\n{reason}': 'The statistics show no flights at the moment:\n{reason}',
    'Kein Flug passt zum Filter.': 'No flight matches the filter.',
    'Dieser Bereich ist noch experimentell: Werte und Auswertungen können sich ändern.': 'This area is still experimental: values and analyses may change.',
    'Bitte im Filter ein Flugzeug wählen: Die Statistik wertet immer genau ein Flugzeug aus (gefiltert sind Flüge von {aircraft}).': 'Please choose an aircraft in the filter: the statistics always analyse exactly one aircraft (the filtered flights belong to {aircraft}).',
    'Für diese Flüge von {aircraft} sind keine Spannungs- und Stromdaten des Flugakkus im Log. Die Statistik-Seiten brauchen sie bisher.': 'These flights of {aircraft} have no flight battery voltage and current in the log. The statistics pages need them so far.',
    'Monat {month:02d}': 'month {month:02d}',
    '{aircraft}: {n} Flüge ausgewertet ({first} – {last})': '{aircraft}: {n} flights analysed ({first} – {last})',
    'keine': 'none',
    '{count} von {total}': '{count} of {total}',
    'Alle auswählen': 'Select all',
    'Alle abwählen': 'Deselect all',
    'keine Jahre': 'no years',
    '{count} Jahre': '{count} years',
    'keine Monate': 'no months',
    '{count} Monate': '{count} months',
    'Monate {months}': 'months {months}',
    'Diagramme': 'Charts',
    'Flugrekorder': 'Flight recorder',
    '▶ Abspielen': '▶ Play',
    '■ Stopp': '■ Stop',
    'Tempo': 'Speed',
    'Roll {bank}° · Nick {pitch}°': 'Bank {bank}° · Pitch {pitch}°',
    'keine Lagedaten': 'no attitude data',
    'Für diesen Flug sind keine Daten für die Anzeigen des Flugrekorders im Log (Lage, Höhe, Steigen/Sinken, Antrieb, Akku, Knüppel).': 'This flight has no data for the instruments of the flight recorder in its log (attitude, altitude, vertical speed, drive, battery, sticks).',
    'Steigen/Sinken': 'Vertical speed',
    'U/min': 'rpm',
    'Gas / Seite': 'Throttle / Rudder',
    'Höhe / Quer': 'Elevator / Aileron',
    'Höhe / Seite': 'Elevator / Rudder',
    'Gas / Quer': 'Throttle / Aileron',
    'Mode {number}': 'Mode {number}',
    'Links: {left} · Rechts: {right}': 'Left: {left} · Right: {right}',
    'Knüppelmodus': 'Stick mode',
    'Gilt für alle Flugzeuge und wirkt sofort im Flugrekorder.': 'Applies to all aircraft and takes effect at once in the flight recorder.',
    'Dieser Log enthält keine Zeitreihen.': 'This log contains no time series.',
    'keine Knüppeldaten': 'no stick data',
}
