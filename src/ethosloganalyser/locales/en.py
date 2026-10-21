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
    "EthosLogAnalyser – Flug- und Akku-Analyse (FrSky Ethos Logs)":
        "EthosLogAnalyser – flight and battery analysis (FrSky Ethos logs)",
    "Noch nicht ausgewertet – Ordner und Akku im Reiter „Daten & Einstellungen“ festlegen.":
        "Not analysed yet – choose the folder and battery in the \"Data & settings\" tab.",
    "Daten & Einstellungen": "Data & settings",
    "Zusammenfassung": "Summary",
    "Akku": "Battery",
    "Belastung & Flugprofil": "Load & flight profile",
    "Antrieb": "Drive",
    "Funk & Bordnetz": "Radio & onboard power",
    "Einzelflug": "Single flight",
    "Tabelle": "Table",
    "Logdaten": "Log data",
    "Ordner mit Ethos-CSV-Logs (Unterordner werden mit durchsucht):": "Folder with Ethos CSV logs (subfolders are included):",
    "Ordner wählen …": "Choose folder …",
    "Auswerten": "Analyse",
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
    "Übersprungene Dateien": "Skipped files",
    "Datei": "File",
    "Grund": "Reason",

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
    "Maus über das Diagramm bewegen: Werte zum Zeitpunkt.   Mausrad: zoomen  ·  Ziehen mit linker Maustaste: "
    "verschieben  ·  Doppelklick: ganzer Flug":
        "Move the mouse over the chart: values at that time.   Mouse wheel: zoom  ·  Drag with left mouse button: "
        "pan  ·  Double-click: whole flight",

    # ---------------- messages ----------------
    "Werte aus …": "Analysing …",
    ", Kapazität unbekannt": ", capacity unknown",
    "{folder}  ·  {n} Flüge ausgewertet, {skipped} von {total} Dateien übersprungen  ·  Akku {cells}S {chem}{cap}":
        "{folder}  ·  {n} flights analysed, {skipped} of {total} files skipped  ·  battery {cells}S {chem}{cap}",
    "Eingabefehler": "Input error",
    "Bitte gültige Zahlen in den Einstellungen eintragen.": "Please enter valid numbers in the settings.",
    "Ordner": "Folder",
    "Bitte zuerst einen gültigen Ordner wählen.": "Please choose a valid folder first.",
    "Fehler bei der Auswertung": "Analysis error",
    "Fehler bei der Auswertung.": "Analysis error.",
    "Bitte zuerst auswerten.": "Please analyse first.",
    "Zielordner für Bericht und Diagramme": "Target folder for report and charts",
    "Ordner mit Ethos-Logfiles wählen": "Choose folder with Ethos log files",
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
    "zu kurz ({dur:.0f} s < {min:.0f} s)": "too short ({dur:.0f} s < {min:.0f} s)",

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
        "(buzzing at end position) and defects; see the single flight tab for the times.",

    # ---------------- summary report ----------------
    "Keine auswertbaren Flüge gefunden.": "No flights that could be analysed were found.",
    "ÜBERSICHT": "OVERVIEW",
    "{n} Flüge ausgewertet ({first} – {last}), {skipped} Dateien übersprungen":
        "{n} flights analysed ({first} – {last}), {skipped} files skipped",
    "Akku: {cells}S {chem}": "Battery: {cells}S {chem}",
    "  (Zellenzahl automatisch erkannt)": "  (cell count detected automatically)",
    ", Nennkapazität {cap:.0f} mAh": ", nominal capacity {cap:.0f} mAh",
    "Gesamt entnommen: {ah:.1f} Ah": "Total drawn: {ah:.1f} Ah",
    "  (≈ {cycles:.1f} Vollzyklen)": "  (≈ {cycles:.1f} full cycles)",
    "AKKU ÜBER ALLE FLÜGE": "BATTERY ACROSS ALL FLIGHTS",
    "Details zu jedem einzelnen Flug (auch zum letzten) stehen im Reiter Einzelflug.":
        "Details of each flight (including the last one) are in the single flight tab.",
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
    "Für Trend, Restkapazität (SoH) und Lebensdauer-Prognose werden mindestens 4 Flüge mit gültigen Werten benötigt.":
        "Trend, remaining capacity (SoH) and life forecast need at least 4 flights with valid values.",
    "Restkapazität (SoH): ca. {soh:.0f} % der Anfangskapazität  ({first:.0f} → {cur:.0f} mAh)":
        "Remaining capacity (SoH): approx. {soh:.0f} % of the initial capacity  ({first:.0f} → {cur:.0f} mAh)",
    "  - unzuverlässig, solange die Zellchemie nicht passt (siehe oben)":
        "  - unreliable as long as the cell chemistry does not match (see above)",
    "  absolut: ca. {cur:.0f} mAh = {pct:.0f} % der Nennkapazität":
        "  absolute: approx. {cur:.0f} mAh = {pct:.0f} % of the nominal capacity",
    "  Prognose: 80 % SoH in ca. {n:.0f} weiteren Flügen": "  Forecast: 80 % SoH in approx. {n:.0f} more flights",
    "Kapazitäts-SoH nicht bestimmbar: zu wenige Flüge mit ≥ 40 % Entladetiefe.":
        "Capacity SoH cannot be determined: too few flights with ≥ 40 % depth of discharge.",
    "Innenwiderstand je Zelle: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)":
        "Internal resistance per cell: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)",
    "  Prognose: +50 % Ri (Faustregel Lebensende) in ca. {n:.0f} weiteren Flügen":
        "  Forecast: +50 % Ri (rule of thumb for end of life) in approx. {n:.0f} more flights",
    "Spannung bei {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/Zelle ({mv:+.0f} mV)":
        "Voltage at {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/cell ({mv:+.0f} mV)",
    "Restlebensdauer (früheres Kriterium): ca. {n:.0f} Flüge": "Remaining life (earlier criterion): approx. {n:.0f} flights",
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
    "ÜBERSPRUNGENE DATEIEN": "SKIPPED FILES",

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
    "Mittlere Leistung {value}, {t80:.0f} s über 80 % des Spitzenstroms, mittleres Gas {gas} %":
        "Mean power {value}, {t80:.0f} s above 80 % of the peak current, mean throttle {gas} %",
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
    "  t = {t:6.1f} s  {peak:.2f} A, {dur:.1f} s  →  {why}:  Knüppel {stick} %/s, Drehrate {rate} °/s, {g} g, "
    "Gas {gas} %, Höhe {alt} m":
        "  t = {t:6.1f} s  {peak:.2f} A, {dur:.1f} s  →  {why}:  stick {stick} %/s, rotation rate {rate} °/s, {g} g, "
        "throttle {gas} %, altitude {alt} m",
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
    "Flugzeit und Timer-Empfehlung [s]": "Flight time and timer recommendation [s]",
    "Balken über dem roten Punkt: länger geflogen als für die Reserve empfohlen.":
        "Bar above the red dot: flown longer than recommended for the reserve.",

    # ---------------- charts: drive ----------------
    "Antrieb und Sensor-Plausibilität": "Drive and sensor plausibility",
    "keine Drehzahl im Log": "no RPM in the log",
    "Kennlinie: Leistung gegen Drehzahl": "Curve: power vs. RPM",
    "Farbe: frühe Flüge violett → späte gelb. Wandert die Kurve nach oben: Verschleiß/Fremdkörper.":
        "Colour: early flights violet → late ones yellow. If the curve moves up: wear/foreign object.",
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
    "Schwarz = ohne erkennbaren Anlass: Servos prüfen. Details im Reiter Einzelflug.":
        "Black = no apparent cause: check servos. Details in the single flight tab.",
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
    "Zeit seit Motorstart [s]": "Time since motor start [s]",
    " Timer-Empfehlung": " timer recommendation",
    "entnommen": "drawn",
    "Leistung": "Power",
    "Akkuspannung": "Battery voltage",
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
    "Roll- und Nickwinkel.": "Roll and pitch angle.",
    "Roll": "Roll",
    "Nick": "Pitch",
    "Wie schnell sich die Lage ändert (aus Roll und Nick).": "How fast the attitude changes (from roll and pitch).",
    "Beschleunigung, 1 g = Geradeausflug.": "Acceleration, 1 g = straight and level flight.",

    # ---------------- table headings ----------------
    "Datum": "Date",
    "Dauer s": "Duration s",
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
    "Timer s": "Timer s",
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
}
