# -*- coding: utf-8 -*-
"""Spanish translation. Keys are the German source texts from the code (see i18n.py)."""

CATALOG = {
    # ---------------- formats and file names ----------------
    "%d.%m.%Y": "%d/%m/%Y",
    "%d.%m.%Y %H:%M": "%d/%m/%Y %H:%M",
    "zusammenfassung.txt": "resumen.txt",
    "fluege.csv": "vuelos.csv",
    "flug{no}_details.txt": "vuelo{no}_detalles.txt",
    "flug{no}_{view}.png": "vuelo{no}_{view}.png",

    # ---------------- window, tabs, settings ----------------
    "EthosLogAnalyser – Flug- und Akku-Analyse (FrSky Ethos Logs)":
        "EthosLogAnalyser – análisis de vuelo y batería (logs de FrSky Ethos)",
    "Noch nicht ausgewertet – Ordner und Akku im Reiter „Daten & Einstellungen“ festlegen.":
        "Aún sin analizar – elija la carpeta y la batería en la pestaña «Datos y ajustes».",
    "Daten & Einstellungen": "Datos y ajustes",
    "Zusammenfassung": "Resumen",
    "Akku": "Batería",
    "Belastung & Flugprofil": "Carga y perfil de vuelo",
    "Antrieb": "Propulsión",
    "Funk & Bordnetz": "Radio y alimentación a bordo",
    "Einzelflug": "Vuelo individual",
    "Tabelle": "Tabla",
    "Logdaten": "Datos de log",
    "Ordner mit Ethos-CSV-Logs (Unterordner werden mit durchsucht):":
        "Carpeta con logs CSV de Ethos (se incluyen las subcarpetas):",
    "Ordner wählen …": "Elegir carpeta …",
    "Auswerten": "Analizar",
    "Auswertung": "Análisis",
    "Zellchemie": "Química de celda",
    "LiPo, LiHV oder Li-Ion": "LiPo, LiHV o Li-Ion",
    "Zellenzahl": "Número de celdas",
    "0 = automatisch aus der Startspannung": "0 = automático a partir de la tensión inicial",
    "Nennkapazität [mAh]": "Capacidad nominal [mAh]",
    "0 = unbekannt (wird geschätzt)": "0 = desconocida (se estima)",
    "Min. Flugdauer [s]": "Duración mín. de vuelo [s]",
    "kürzere Logs werden übersprungen": "los logs más cortos se omiten",
    "Motor aktiv ab [A]": "Motor activo desde [A]",
    "Strom, ab dem der Flug zählt": "corriente a partir de la cual cuenta el vuelo",
    "Reserve bei Landung [%]": "Reserva al aterrizar [%]",
    "für die Timer-Empfehlung": "para la recomendación del temporizador",
    "Spalte Spannung (optional)": "Columna de tensión (opcional)",
    "Teil des Spaltennamens": "parte del nombre de la columna",
    "Spalte Strom (optional)": "Columna de corriente (opcional)",
    "Sprache (Language)": "Idioma (Language)",
    "wird gespeichert und beim nächsten Start verwendet": "se guarda y se usa en el próximo inicio",
    "Export": "Exportar",
    "Tabelle als CSV speichern …": "Guardar tabla como CSV …",
    "Bericht + alle Diagramme speichern …": "Guardar informe + todos los gráficos …",
    "Übersprungene Dateien": "Archivos omitidos",
    "Datei": "Archivo",
    "Grund": "Motivo",

    # ---------------- single-flight tab ----------------
    "Flug:": "Vuelo:",
    "‹ zurück": "‹ anterior",
    "vor ›": "siguiente ›",
    "Details ausblenden": "Ocultar detalles",
    "Details einblenden": "Mostrar detalles",
    "Bild speichern …": "Guardar imagen …",
    "Ansicht:": "Vista:",
    "Zeit:": "Tiempo:",
    "Ganzer Flug": "Vuelo completo",
    "Start (60 s)": "Despegue (60 s)",
    "Landung (60 s)": "Aterrizaje (60 s)",
    "Zoom +": "Zoom +",
    "Zoom −": "Zoom −",
    "‹ früher": "‹ antes",
    "später ›": "después ›",
    "Stromspitze:": "Pico de corriente:",
    "keine Spitzen": "sin picos",
    "Maus über das Diagramm bewegen: Werte zum Zeitpunkt.   Mausrad: zoomen  ·  Ziehen mit linker Maustaste: "
    "verschieben  ·  Doppelklick: ganzer Flug":
        "Mueva el ratón sobre el gráfico: valores en ese instante.   Rueda: zoom  ·  Arrastrar con botón izquierdo: "
        "desplazar  ·  Doble clic: vuelo completo",

    # ---------------- messages ----------------
    "Werte aus …": "Analizando …",
    ", Kapazität unbekannt": ", capacidad desconocida",
    "{folder}  ·  {n} Flüge ausgewertet, {skipped} von {total} Dateien übersprungen  ·  Akku {cells}S {chem}{cap}":
        "{folder}  ·  {n} vuelos analizados, {skipped} de {total} archivos omitidos  ·  batería {cells}S {chem}{cap}",
    "Eingabefehler": "Error de entrada",
    "Bitte gültige Zahlen in den Einstellungen eintragen.": "Introduzca números válidos en los ajustes.",
    "Ordner": "Carpeta",
    "Bitte zuerst einen gültigen Ordner wählen.": "Elija primero una carpeta válida.",
    "Fehler bei der Auswertung": "Error en el análisis",
    "Fehler bei der Auswertung.": "Error en el análisis.",
    "Bitte zuerst auswerten.": "Analice primero.",
    "Zielordner für Bericht und Diagramme": "Carpeta de destino para informe y gráficos",
    "Ordner mit Ethos-Logfiles wählen": "Elegir carpeta con archivos de log de Ethos",
    "Gespeichert": "Guardado",
    "Bericht, Tabelle und Diagramme wurden in\n{folder}\ngespeichert.":
        "El informe, la tabla y los gráficos se han guardado en\n{folder}",

    # ---------------- reasons for skipped files ----------------
    "Lesefehler: {err}": "Error de lectura: {err}",
    "Spalten nicht gefunden (Spannung={cv}, Strom={ci}). Verfügbar: {cols}":
        "Columnas no encontradas (tensión={cv}, corriente={ci}). Disponibles: {cols}",
    "Zeitspalte nicht erkannt": "columna de tiempo no reconocida",
    "Spannung/Strom kaum vorhanden (Sensor nicht verbunden?)": "casi sin valores de tensión/corriente (¿sensor no conectado?)",
    "nur Nullwerte in {cv}/{ci} (Bodenlog ohne Akku-Telemetrie)":
        "solo valores cero en {cv}/{ci} (log en tierra sin telemetría de batería)",
    "zu wenige Datenpunkte": "muy pocos puntos de datos",
    "kein Motorstrom erkannt": "no se detectó corriente de motor",
    "zu kurz ({dur:.0f} s < {min:.0f} s)": "demasiado corto ({dur:.0f} s < {min:.0f} s)",

    # ---------------- labels: spike causes, signals, sticks, sources ----------------
    "Schalter": "Interruptor",
    "Manöver": "Maniobra",
    "Start/Landung": "Despegue/aterrizaje",
    "ohne erkennbaren Anlass": "sin causa aparente",
    "keine Lagedaten": "sin datos de actitud",
    "Knüppelaktivität": "actividad de sticks",
    "Drehrate": "Velocidad de giro",
    "G-Last": "Carga G",
    "Gas": "Gas",
    "Querruder": "Alerones",
    "Höhenruder": "Profundidad",
    "Seitenruder": "Dirección",
    "gemessen": "medida",
    "geschätzt": "estimada",
    "Nennkapazität": "capacidad nominal",
    "geschätzte Kapazität": "capacidad estimada",

    # ---------------- flags and usage factors ----------------
    "Ladezustand unplausibel": "Estado de carga inverosímil",
    "Tiefentladung": "Descarga profunda",
    "Spannungseinbruch": "Caída de tensión",
    "Sensorabweichung": "Desviación del sensor",
    "Empfängerstrom-Spitzen ohne Anlass": "Picos de corriente del receptor sin causa",
    "Innenwiderstand": "Resistencia interna",
    "Spannung bei Referenzlast": "Tensión con carga de referencia",
    "Antriebsleistung bei Referenzdrehzahl": "Potencia de propulsión a rpm de referencia",
    "RSSI-Minimum": "Mínimo de RSSI",
    "VFR-Minimum": "Mínimo de VFR",
    "Empfängerspannung": "Tensión del receptor",
    "Empfängerstrom-Maximum": "Máximo de corriente del receptor",
    "Abweichung Strommessung/ESC-Zähler": "Desviación sensor de corriente/contador del ESC",
    "Spitzen-C-Rate": "tasa C de pico",
    "Entladetiefe": "profundidad de descarga",
    "Endspannung": "tensión final",
    "Ladezustand beim Start": "estado de carga al despegar",
    "Pause seit letztem Flug": "pausa desde el último vuelo",
    "mittlerer Strom": "corriente media",
    "Flugdauer": "duración del vuelo",

    # ---------------- warnings ----------------
    "{label} in {n} von {total} Flügen (Flug {flights}): {text}": "{label} en {n} de {total} vuelos (vuelo {flights}): {text}",
    "Flug {no} ({date}): auffälliger Wert bei {label} ({value}, erwartet ca. {expected}).":
        "Vuelo {no} ({date}): valor llamativo en {label} ({value}, esperado aprox. {expected}).",
    "Ladezustand aus der Endspannung weicht im Mittel um {dev:+.0f} Prozentpunkte von der Ladungszählung ab "
    "(entnommen / {src} {cap:.0f} mAh). Verwendet wird die Ladungszählung. Mögliche Ursachen: Akkuwechsel oder "
    "Motorlauf nach der Landung im selben Log, Spannungssensor, falsche Nennkapazität oder Zellchemie.":
        "El estado de carga según la tensión final difiere de media {dev:+.0f} puntos porcentuales del recuento de "
        "carga (consumido / {src} {cap:.0f} mAh). Se usa el recuento de carga. Posibles causas: cambio de batería o "
        "motor en marcha tras el aterrizaje en el mismo log, sensor de tensión, capacidad nominal o química de celda "
        "incorrectas.",
    "Ruhespannung am Ende unter {rest:.2f} V/Zelle ({chem}) oder rechnerischer Ladezustand unter 5 % (tiefste "
    "Endspannung {low:.2f} V/Zelle). Bitte auch Zellchemie und Nennkapazität prüfen.":
        "Tensión en reposo al final por debajo de {rest:.2f} V/celda ({chem}) o estado de carga calculado inferior "
        "al 5 % (tensión final más baja {low:.2f} V/celda). Compruebe también la química de celda y la capacidad nominal.",
    "Spannung unter Last fiel bis auf {low:.2f} V/Zelle (Grenze {limit:.2f} V).":
        "La tensión bajo carga cayó hasta {low:.2f} V/celda (límite {limit:.2f} V).",
    "Strommessung weicht mehr als 5 % vom ESC-Zähler ab (Sensor prüfen/kalibrieren).":
        "La medición de corriente difiere más de un 5 % del contador del ESC (compruebe/calibre el sensor).",
    "mindestens 3 Stromspitzen ohne Manöver, Start oder Landung. Servos auf Schwergängigkeit, Anschlag (Brummen in "
    "Endlage) und Defekte prüfen; Zeitpunkte siehe Einzelflug.":
        "al menos 3 picos de corriente sin maniobra, despegue ni aterrizaje. Compruebe si los servos van duros, "
        "topan (zumbido en el extremo) o están defectuosos; los instantes, en la pestaña Vuelo individual.",

    # ---------------- summary report ----------------
    "Keine auswertbaren Flüge gefunden.": "No se encontraron vuelos analizables.",
    "ÜBERSICHT": "VISTA GENERAL",
    "{n} Flüge ausgewertet ({first} – {last}), {skipped} Dateien übersprungen":
        "{n} vuelos analizados ({first} – {last}), {skipped} archivos omitidos",
    "Akku: {cells}S {chem}": "Batería: {cells}S {chem}",
    "  (Zellenzahl automatisch erkannt)": "  (número de celdas detectado automáticamente)",
    ", Nennkapazität {cap:.0f} mAh": ", capacidad nominal {cap:.0f} mAh",
    "Gesamt entnommen: {ah:.1f} Ah": "Total consumido: {ah:.1f} Ah",
    "  (≈ {cycles:.1f} Vollzyklen)": "  (≈ {cycles:.1f} ciclos completos)",
    "AKKU ÜBER ALLE FLÜGE": "BATERÍA EN TODOS LOS VUELOS",
    "Details zu jedem einzelnen Flug (auch zum letzten) stehen im Reiter Einzelflug.":
        "Los detalles de cada vuelo (también del último) están en la pestaña Vuelo individual.",
    "Typischer Flug (Median): {dur}, {drawn} mAh entnommen, Ladezustand am Ende ≈ {soc} %, Spitze {imax} A / "
    "{pmax} W, min. {umin} V/Zelle unter Last":
        "Vuelo típico (mediana): {dur}, {drawn} mAh consumidos, estado de carga al final ≈ {soc} %, pico {imax} A / "
        "{pmax} W, mín. {umin} V/celda bajo carga",
    "Innenwiderstand je Zelle: Median {med} mΩ, Spanne {lo} – {hi} mΩ":
        "Resistencia interna por celda: mediana {med} mΩ, rango {lo} – {hi} mΩ",
    "Zellchemie prüfen: Mit {chem} passen Ruhespannung und entnommene Ladung nicht zusammen (Abweichung im Median "
    "{dev:.0f} Prozentpunkte), mit {best} sehr gut ({best_dev:.0f} Pkt.). Ist der Akku ein {best}-Akku? Falls es "
    "wirklich {chem} ist, liefert er deutlich weniger als die eingetragenen {cap:.0f} mAh (geschätzt ca. {est} mAh).":
        "Compruebe la química de celda: con {chem}, la tensión en reposo y la carga consumida no concuerdan "
        "(desviación mediana {dev:.0f} puntos porcentuales); con {best} concuerdan muy bien ({best_dev:.0f} ptos.). "
        "¿Es una batería {best}? Si de verdad es {chem}, entrega bastante menos que los {cap:.0f} mAh introducidos "
        "(estimado aprox. {est} mAh).",
    "Ruhespannung und entnommene Ladung passen zur Einstellung {chem} / {cap:.0f} mAh (Abweichung im Median "
    "{dev:.0f} Pkt.).":
        "La tensión en reposo y la carga consumida concuerdan con el ajuste {chem} / {cap:.0f} mAh (desviación "
        "mediana {dev:.0f} ptos.).",
    "Nennkapazität nicht eingetragen: Ladezustand und Timer beruhen nur auf der Spannungskennlinie.":
        "Capacidad nominal no introducida: el estado de carga y el temporizador se basan solo en la curva de tensión.",
    "ALTERUNG UND RESTKAPAZITÄT": "ENVEJECIMIENTO Y CAPACIDAD RESTANTE",
    "Für Trend, Restkapazität (SoH) und Lebensdauer-Prognose werden mindestens 4 Flüge mit gültigen Werten benötigt.":
        "Para la tendencia, la capacidad restante (SoH) y el pronóstico de vida útil se necesitan al menos 4 vuelos "
        "con valores válidos.",
    "Restkapazität (SoH): ca. {soh:.0f} % der Anfangskapazität  ({first:.0f} → {cur:.0f} mAh)":
        "Capacidad restante (SoH): aprox. {soh:.0f} % de la capacidad inicial  ({first:.0f} → {cur:.0f} mAh)",
    "  - unzuverlässig, solange die Zellchemie nicht passt (siehe oben)":
        "  - poco fiable mientras la química de celda no concuerde (ver arriba)",
    "  absolut: ca. {cur:.0f} mAh = {pct:.0f} % der Nennkapazität":
        "  absoluta: aprox. {cur:.0f} mAh = {pct:.0f} % de la capacidad nominal",
    "  Prognose: 80 % SoH in ca. {n:.0f} weiteren Flügen": "  Pronóstico: 80 % SoH en aprox. {n:.0f} vuelos más",
    "Kapazitäts-SoH nicht bestimmbar: zu wenige Flüge mit ≥ 40 % Entladetiefe.":
        "No se puede determinar el SoH de capacidad: muy pocos vuelos con ≥ 40 % de profundidad de descarga.",
    "Innenwiderstand je Zelle: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)":
        "Resistencia interna por celda: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)",
    "  Prognose: +50 % Ri (Faustregel Lebensende) in ca. {n:.0f} weiteren Flügen":
        "  Pronóstico: +50 % Ri (regla práctica de fin de vida) en aprox. {n:.0f} vuelos más",
    "Spannung bei {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/Zelle ({mv:+.0f} mV)":
        "Tensión a {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/celda ({mv:+.0f} mV)",
    "Restlebensdauer (früheres Kriterium): ca. {n:.0f} Flüge": "Vida útil restante (criterio más temprano): aprox. {n:.0f} vuelos",
    ", ≈ {cycles:.0f} Vollzyklen": ", ≈ {cycles:.0f} ciclos completos",
    "Zusammenhang Nutzung ↔ Ri-Abweichung (Hinweis, keine Kausalität):":
        "Relación uso ↔ desviación de Ri (indicio, no causalidad):",
    "TIMER-EMPFEHLUNG": "RECOMENDACIÓN DE TEMPORIZADOR",
    "Landung bei {reserve:.0f} % Restkapazität: Timer ca. {timer} (Median der letzten Flüge; geflogen: {flown})":
        "Aterrizaje con {reserve:.0f} % de capacidad restante: temporizador aprox. {timer} (mediana de los últimos "
        "vuelos; volado: {flown})",
    "Basis: Kapazität ≈ {cap:.0f} mAh, Leistungsprofil der letzten Flüge.":
        "Base: capacidad ≈ {cap:.0f} mAh, perfil de potencia de los últimos vuelos.",
    "Nicht bestimmbar (Kapazität unbekannt: Nennkapazität eintragen oder Flüge mit ≥ 40 % Entladetiefe).":
        "No se puede determinar (capacidad desconocida: introduzca la capacidad nominal o realice vuelos con ≥ 40 % "
        "de profundidad de descarga).",
    "ANTRIEB UND SENSOREN": "PROPULSIÓN Y SENSORES",
    "Leistungsbedarf bei {rpm:.0f} U/min: {p0:.0f} → {p1:.0f} W ({pct:+.0f} %)":
        "Demanda de potencia a {rpm:.0f} rpm: {p0:.0f} → {p1:.0f} W ({pct:+.0f} %)",
    "  - Anstieg kann auf Verschleiß/Lagerschaden/Fremdkörper hindeuten":
        "  - un aumento puede indicar desgaste, daño en rodamientos o cuerpos extraños",
    "Antriebs-Trend: ab 4 Flügen verfügbar.": "Tendencia de propulsión: disponible a partir de 4 vuelos.",
    "Antriebs-Kennlinie nicht verfügbar (keine Drehzahl im Log).": "Curva de propulsión no disponible (sin rpm en el log).",
    "Strommessung vs. ESC-Zähler: Median {dev:+.1f} % Abweichung":
        "Sensor de corriente vs. contador del ESC: desviación mediana {dev:+.1f} %",
    "FUNK UND BORDNETZ (schlechtester Wert über alle Flüge)": "RADIO Y ALIMENTACIÓN A BORDO (peor valor de todos los vuelos)",
    "Empfängerakku": "Batería del receptor",
    "Empfängerstrom max": "Corriente máx. del receptor",
    "Senderakku": "Batería de la emisora",
    "{label} {value}{unit} (Flug {no})": "{label} {value}{unit} (vuelo {no})",
    "keine Funkwerte im Log": "sin valores de radio en el log",
    "Empfängerstrom: Grundlast Ø {base:.2f} A (Median der Flüge)":
        "Corriente del receptor: carga base Ø {base:.2f} A (mediana de los vuelos)",
    ", Spitzen bis {peak:.2f} A": ", picos de hasta {peak:.2f} A",
    "Stromspitzen (alle Flüge): {n} - {shares}": "Picos de corriente (todos los vuelos): {n} - {shares}",
    "Strom folgt deutlich den Steuerausschlägen (Servolast)": "la corriente sigue claramente los mandos (carga de servos)",
    "mäßiger Zusammenhang mit den Steuerausschlägen": "relación moderada con los mandos",
    "kaum Zusammenhang mit den Steuerausschlägen": "apenas relación con los mandos",
    "Zusammenhang Empfängerstrom ↔ {signal}: r = {r:+.2f} (Median) - {verdict}":
        "Relación corriente del receptor ↔ {signal}: r = {r:+.2f} (mediana) - {verdict}",
    "WARNUNGEN UND AUFFÄLLIGKEITEN": "AVISOS Y ANOMALÍAS",
    "… und {n} weitere": "… y {n} más",
    "Keine Auffälligkeiten festgestellt.": "No se detectaron anomalías.",
    " (Ausreißer-Erkennung erst ab 6 Flügen aktiv.)": " (la detección de valores atípicos solo actúa a partir de 6 vuelos.)",
    "GRENZEN DER AUSWERTUNG": "LÍMITES DEL ANÁLISIS",
    "Ohne Temperaturdaten: Ri hängt stark von der Akku-Temperatur ab - kalte Flüge wirken schlechter, als der Akku ist.":
        "Sin datos de temperatura: Ri depende mucho de la temperatura de la batería; los vuelos en frío parecen "
        "peores de lo que es la batería.",
    "Keine Einzelzellspannungen: schwache Zellen/Balancing sind nicht erkennbar.":
        "Sin tensiones de celdas individuales: no se detectan celdas débiles ni el balanceo.",
    "Ladezustand am Ende: Ladungszählung, abhängig von der richtigen Nennkapazität bzw. Kapazitätsschätzung. Die "
    "Ruhespannung ist nur eine Gegenprobe (Näherungskennlinie, Akku erholt sich nach der Landung).":
        "Estado de carga al final: recuento de carga, depende de la capacidad nominal o de la estimación de "
        "capacidad correctas. La tensión en reposo es solo una comprobación (curva aproximada; la batería se "
        "recupera tras el aterrizaje).",
    "Empfängerstrom-Spitzen: Zuordnung über Schalterbetätigung, Knüppelbewegung, Drehrate (Roll/Nick), G-Last, "
    "Flugzeit und Höhe - soweit diese Werte im Log stehen. Welcher Schalter z. B. das Fahrwerk schaltet, weiß die App "
    "nicht; sie nennt den Namen der Ethos-Quelle.":
        "Picos de corriente del receptor: se asignan por accionamiento de interruptores, movimiento de sticks, "
        "velocidad de giro (alabeo/cabeceo), carga G, tiempo de vuelo y altura, en la medida en que estén en el log. "
        "La app no sabe qué interruptor acciona, p. ej., el tren de aterrizaje; muestra el nombre de la fuente de Ethos.",
    "Flugphasen und Wh je 100 m Steigen sind indikativ (Höhenwerte geglättet).":
        "Las fases de vuelo y los Wh por cada 100 m de ascenso son orientativos (altura suavizada).",
    "ÜBERSPRUNGENE DATEIEN": "ARCHIVOS OMITIDOS",

    # ---------------- state of charge lines ----------------
    "Ladezustand: Start ≈ {start} %, Ende ≈ {end:.0f} %  (Ladungszählung: {drawn:.0f} mAh entnommen von {cap:.0f} mAh "
    "{src})":
        "Estado de carga: despegue ≈ {start} %, final ≈ {end:.0f} %  (recuento de carga: {drawn:.0f} mAh consumidos "
        "de {cap:.0f} mAh, {src})",
    "  Gegenprobe Ruhespannung: {u0} → {u1} V/Zelle ({src}) ≙ {soc} % - passt nicht zur entnommenen Ladung "
    "({dev:+.0f} Pkt.), verworfen":
        "  Comprobación con tensión en reposo: {u0} → {u1} V/celda ({src}) ≙ {soc} % - no concuerda con la carga "
        "consumida ({dev:+.0f} ptos.), descartada",
    "  Gegenprobe Ruhespannung: {u0} → {u1} V/Zelle ({src}) ≙ {soc} % - passt":
        "  Comprobación con tensión en reposo: {u0} → {u1} V/celda ({src}) ≙ {soc} % - concuerda",
    "Ladezustand: Start ≈ {start} %, Ende ≈ {end} % nur aus Ruhespannung ({u1} V/Zelle, {src}) - ohne Gegenprobe. "
    "Nennkapazität eintragen für die Ladungszählung.":
        "Estado de carga: despegue ≈ {start} %, final ≈ {end} % solo según la tensión en reposo ({u1} V/celda, {src}) "
        "- sin comprobación. Introduzca la capacidad nominal para el recuento de carga.",

    # ---------------- single-flight report ----------------
    "{value}{unit} (Median {median}{unit})": "{value}{unit} (mediana {median}{unit})",
    " V/Zelle": " V/celda",
    " U/min": " rpm",
    "Flug {no} – {date} – {dur} – {drawn:.0f} mAh – {file}": "Vuelo {no} – {date} – {dur} – {drawn:.0f} mAh – {file}",
    "AUFFÄLLIGKEITEN IN DIESEM FLUG": "ANOMALÍAS EN ESTE VUELO",
    "AKKU": "BATERÍA",
    "Innenwiderstand je Zelle: {value}": "Resistencia interna por celda: {value}",
    "  im Flugverlauf: Anfang {r0:.2f} → Ende {r1:.2f} mΩ ({pct:+.0f} %)":
        "  durante el vuelo: inicio {r0:.2f} → final {r1:.2f} mΩ ({pct:+.0f} %)",
    "Innenwiderstand: nicht bestimmbar (zu gleichmäßige Last)":
        "Resistencia interna: no se puede determinar (carga demasiado uniforme)",
    "Reserve zur Mindest-Ruhespannung ({rest:.2f} V/Zelle): {reserve:+.2f} V/Zelle":
        "Reserva hasta la tensión mínima en reposo ({rest:.2f} V/celda): {reserve:+.2f} V/celda",
    "Geschätzte Gesamtkapazität: {value}": "Capacidad total estimada: {value}",
    "Minimale Spannung unter Last: {value} bei {imax:.0f} A Spitze": "Tensión mínima bajo carga: {value} con {imax:.0f} A de pico",
    "Spannung bei {iref:.0f} A / {qref:.0f} mAh: {value}": "Tensión a {iref:.0f} A / {qref:.0f} mAh: {value}",
    "BELASTUNG UND FLUGPROFIL": "CARGA Y PERFIL DE VUELO",
    "C-Rate Spitze {value}": "Tasa C de pico {value}",
    "Spitzenleistung {value}": "Potencia de pico {value}",
    "Mittlere Leistung {value}, {t80:.0f} s über 80 % des Spitzenstroms, mittleres Gas {gas} %":
        "Potencia media {value}, {t80:.0f} s por encima del 80 % de la corriente de pico, gas medio {gas} %",
    "Energie nach Phase: Steigflug {up:.0f} Wh ({pct:.0f} %), Reise {cr:.0f} Wh, Sinkflug {dn:.0f} Wh":
        "Energía por fase: ascenso {up:.0f} Wh ({pct:.0f} %), crucero {cr:.0f} Wh, descenso {dn:.0f} Wh",
    "Max. Höhe {value}": "Altura máx. {value}",
    ", {wh} Wh je 100 m Steigen": ", {wh} Wh por cada 100 m de ascenso",
    "G-Kräfte: max {value}, 95. Perzentil {p95:.1f} g": "Fuerzas G: máx. {value}, percentil 95 {p95:.1f} g",
    "TIMER": "TEMPORIZADOR",
    "Empfehlung für {reserve:.0f} % Rest bei diesem Flugprofil: {timer}, geflogen {flown} ":
        "Recomendación para {reserve:.0f} % restante con este perfil de vuelo: {timer}, volado {flown} ",
    "({diff} länger als empfohlen)": "({diff} más de lo recomendado)",
    "(innerhalb der Empfehlung)": "(dentro de la recomendación)",
    "Keine Timer-Empfehlung (Kapazität unbekannt).": "Sin recomendación de temporizador (capacidad desconocida).",
    "Drehzahl (90. Perzentil): {value}": "Rpm (percentil 90): {value}",
    "; Leistung bei {rpm:.0f} U/min: {value}": "; potencia a {rpm:.0f} rpm: {value}",
    "Eigene mAh-Berechnung gegen ESC-Zähler: {own:.0f} gegen {esc:.0f} mAh ({dev:+.1f} %)":
        "Cálculo propio de mAh vs. contador del ESC: {own:.0f} vs. {esc:.0f} mAh ({dev:+.1f} %)",
    "FUNK UND BORDNETZ": "RADIO Y ALIMENTACIÓN A BORDO",
    "RSSI min. {rssi}, VFR min. {vfr}": "RSSI mín. {rssi}, VFR mín. {vfr}",
    "Empfängerakku min. {rx}, Senderakku min. {tx} V": "Batería del receptor mín. {rx}, batería de la emisora mín. {tx} V",
    "Empfängerstrom: Grundlast {base:.2f} A, Maximum {value}, Spitzenschwelle {thr:.2f} A":
        "Corriente del receptor: carga base {base:.2f} A, máximo {value}, umbral de pico {thr:.2f} A",
    "Zusammenhang mit dem Empfängerstrom: {values}": "Relación con la corriente del receptor: {values}",
    "EMPFÄNGERSTROM-SPITZEN ({n})": "PICOS DE CORRIENTE DEL RECEPTOR ({n})",
    "Keine Spitzen über der Schwelle.": "Ningún pico por encima del umbral.",
    "  t = {t:6.1f} s  {peak:.2f} A, {dur:.1f} s  →  {why}:  Knüppel {stick} %/s, Drehrate {rate} °/s, {g} g, "
    "Gas {gas} %, Höhe {alt} m":
        "  t = {t:6.1f} s  {peak:.2f} A, {dur:.1f} s  →  {why}:  sticks {stick} %/s, velocidad de giro {rate} °/s, "
        "{g} g, gas {gas} %, altura {alt} m",
    "Kein Empfängerstrom im Log.": "Sin corriente del receptor en el log.",
    "SCHALTERBETÄTIGUNGEN ({n})": "ACCIONAMIENTOS DE INTERRUPTORES ({n})",

    # ---------------- charts: common ----------------
    "keine Daten": "sin datos",
    "Keine Daten": "Sin datos",
    "Flug Nr.": "Vuelo n.º",
    " Rot umkreist: auffälliger Flug.": " Rodeado en rojo: vuelo llamativo.",
    "Flug": "Vuelo",

    # ---------------- charts: battery ----------------
    "Akku-Zustand und Alterung": "Estado y envejecimiento de la batería",
    "80 % der Anfangskapazität": "80 % de la capacidad inicial",
    "Geschätzte Gesamtkapazität [mAh]": "Capacidad total estimada [mAh]",
    "Aus entnommener Ladung und Spannungsabfall. Fallender Trend = Alterung.":
        "A partir de la carga consumida y la caída de tensión. Tendencia descendente = envejecimiento.",
    "Innenwiderstand je Zelle [mΩ]": "Resistencia interna por celda [mΩ]",
    "Ø Flug": "Ø vuelo",
    "Steigender Trend = Alterung; +50 % gilt als Lebensende.":
        "Tendencia ascendente = envejecimiento; +50 % se considera fin de vida.",
    "Flugbeginn": "Inicio del vuelo",
    "Flugende": "Final del vuelo",
    "Spannung bei {iref:.0f} A und {qref:.0f} mAh [V/Zelle]": "Tensión a {iref:.0f} A y {qref:.0f} mAh [V/celda]",
    "Vergleich unter gleichen Bedingungen. Fallender Trend = Akku wird schwächer.":
        "Comparación en las mismas condiciones. Tendencia descendente = la batería pierde fuerza.",
    "Ruhespannung Start / Ende [V/Zelle]": "Tensión en reposo inicio / final [V/celda]",
    "Start": "Inicio",
    "Start: voll geladen? Ende: sollte über der roten Linie liegen.":
        "Inicio: ¿carga completa? Final: debería estar por encima de la línea roja.",
    "Ende (rot umkreist: passt nicht zur Ladung)": "Final (rodeado en rojo: no concuerda con la carga)",
    "Mindestwert": "Mínimo",
    "Ladezustand Start / Ende [%]": "Estado de carga inicio / final [%]",
    "Ende sollte über der Reserve-Linie liegen.": "El final debería estar por encima de la línea de reserva.",
    "Ende (Ladungszählung)": "Final (recuento de carga)",
    "Reserve": "Reserva",
    "Ende (aus Spannung)": "Final (según tensión)",
    "Min. Spannung unter Last [V/Zelle]": "Tensión mín. bajo carga [V/celda]",
    "Grenze": "Límite",
    "Tiefster Spannungseinbruch bei Volllast. Unter der roten Linie: Zellen überlastet.":
        "Mayor caída de tensión a plena carga. Por debajo de la línea roja: celdas sobrecargadas.",

    # ---------------- charts: load ----------------
    "Belastung und Flugprofil": "Carga y perfil de vuelo",
    "alle Flüge": "todos los vuelos",
    "letzter Flug": "último vuelo",
    "Zeitanteil [%]": "Porcentaje de tiempo [%]",
    "kein Gaskanal im Log": "sin canal de gas en el log",
    "Gas-Histogramm": "Histograma de gas",
    "Wie viel Prozent der Flugzeit bei welcher Gasstellung geflogen wurde.":
        "Qué porcentaje del tiempo de vuelo se voló con cada posición de gas.",
    "Gas [%]": "Gas [%]",
    "Spitzen-C-Rate je Flug [C]": "Tasa C de pico por vuelo [C]",
    "Höchster Strom geteilt durch Kapazität. Dauerhaft hohe Werte altern den Akku schneller.":
        "Corriente máxima dividida por la capacidad. Valores altos de forma continua envejecen antes la batería.",
    "Steigflug": "Ascenso",
    "Reise": "Crucero",
    "Sinkflug": "Descenso",
    "keine Höhe im Log": "sin altura en el log",
    "Energie je Flugphase [Wh]": "Energía por fase de vuelo [Wh]",
    "Wofür die Energie verbraucht wurde (aus Höhenänderung).": "En qué se gastó la energía (según el cambio de altura).",
    "Spitzenleistung je Flug [W]": "Potencia de pico por vuelo [W]",
    "Höchste elektrische Leistung (Spannung × Strom).": "Mayor potencia eléctrica (tensión × corriente).",
    "G-Kräfte [g]": "Fuerzas G [g]",
    "Maß für die Härte der Flugmanöver.": "Medida de la dureza de las maniobras.",
    "95. Perzentil": "Percentil 95",
    "Flugzeit": "Tiempo de vuelo",
    "Timer für {reserve:.0f} % Rest": "Temporizador para {reserve:.0f} % restante",
    "Flugzeit und Timer-Empfehlung [s]": "Tiempo de vuelo y recomendación de temporizador [s]",
    "Balken über dem roten Punkt: länger geflogen als für die Reserve empfohlen.":
        "Barra por encima del punto rojo: se voló más tiempo del recomendado para la reserva.",

    # ---------------- charts: drive ----------------
    "Antrieb und Sensor-Plausibilität": "Propulsión y plausibilidad del sensor",
    "keine Drehzahl im Log": "sin rpm en el log",
    "Kennlinie: Leistung gegen Drehzahl": "Curva: potencia frente a rpm",
    "Farbe: frühe Flüge violett → späte gelb. Wandert die Kurve nach oben: Verschleiß/Fremdkörper.":
        "Color: primeros vuelos violeta → últimos amarillo. Si la curva sube: desgaste/cuerpo extraño.",
    "Drehzahl [1000 U/min]": "Rpm [1000 rpm]",
    "Leistung [kW]": "Potencia [kW]",
    "Leistungsbedarf bei {rpm} U/min [W]": "Demanda de potencia a {rpm} rpm [W]",
    "Steigt der Bedarf bei gleicher Drehzahl, läuft der Antrieb schwerer.":
        "Si la demanda sube a las mismas rpm, la propulsión va más dura.",
    "Drehzahl, 90. Perzentil [U/min]": "Rpm, percentil 90 [rpm]",
    "Typische Höchstdrehzahl im Flug. Fallender Trend: Akku oder Antrieb lassen nach.":
        "Rpm máximas típicas en vuelo. Tendencia descendente: la batería o la propulsión pierden rendimiento.",
    "Plausibilität: eigene mAh-Berechnung gegen ESC-Zähler [%]": "Plausibilidad: cálculo propio de mAh vs. contador del ESC [%]",
    "Innerhalb ±5 %: Verbrauchswerte verlässlich (Grundlage für Ladezustand und Timer).":
        "Dentro de ±5 %: valores de consumo fiables (base del estado de carga y del temporizador).",
    "verlässlich": "fiable",
    "Sensor prüfen": "comprobar sensor",

    # ---------------- charts: radio ----------------
    "Funk und Bordnetz": "Radio y alimentación a bordo",
    "RSSI-Minimum im Flug": "Mínimo de RSSI en vuelo",
    "Schlechteste Empfangsstärke je Flug. Ethos warnt üblicherweise unter 45.":
        "Peor intensidad de señal por vuelo. Ethos suele avisar por debajo de 45.",
    "VFR-Minimum im Flug [%]": "Mínimo de VFR en vuelo [%]",
    "Anteil korrekt empfangener Telemetrie-Rahmen. Unter ca. 80 % wird es kritisch.":
        "Porcentaje de tramas de telemetría recibidas correctamente. Por debajo de aprox. 80 % es crítico.",
    "Empfängerakku: Minimum im Flug [V]": "Batería del receptor: mínimo en vuelo [V]",
    "Tiefster Wert der Empfängerversorgung. Einbrüche deuten auf Akku, Kabel oder Servolast.":
        "Valor más bajo de la alimentación del receptor. Las caídas apuntan a batería, cables o carga de servos.",
    "Empfängerstrom [A]": "Corriente del receptor [A]",
    "Maximum": "Máximo",
    "Grundlast (grau) und Spitzen (rot) der Servoversorgung.": "Carga base (gris) y picos (rojo) de la alimentación de servos.",
    "Mittelwert": "Media",
    "kein Empfängerstrom im Log": "sin corriente del receptor en el log",
    "Empfängerstrom-Spitzen je Flug nach Anlass": "Picos de corriente del receptor por vuelo según causa",
    "Schwarz = ohne erkennbaren Anlass: Servos prüfen. Details im Reiter Einzelflug.":
        "Negro = sin causa aparente: compruebe los servos. Detalles en la pestaña Vuelo individual.",
    "Senderakku min. [V]": "Batería de la emisora mín. [V]",
    "Tiefster Wert des Senderakkus im Flug.": "Valor más bajo de la batería de la emisora en vuelo.",

    # ---------------- charts: single flight ----------------
    "Akku & Antrieb": "Batería y propulsión",
    "Empfang": "Recepción",
    "Empfängerstrom & Steuerung": "Corriente del receptor y mandos",
    "Fluglage": "Actitud de vuelo",
    "Ri {ri:.2f} mΩ/Zelle": "Ri {ri:.2f} mΩ/celda",
    "Flug {no} – {date} – {dur} – {drawn:.0f} mAh – {ri}": "Vuelo {no} – {date} – {dur} – {drawn:.0f} mAh – {ri}",
    "Für diese Ansicht sind keine Daten im Log.": "El log no contiene datos para esta vista.",
    "Zeit seit Motorstart [s]": "Tiempo desde el arranque del motor [s]",
    " Timer-Empfehlung": " recomendación de temporizador",
    "entnommen": "consumido",
    "Leistung": "Potencia",
    "Akkuspannung": "Tensión de la batería",
    "Gestrichelt: geschätzte Spannung ohne Last. Abstand = Spannungsabfall durch den Innenwiderstand.":
        "Discontinua: tensión estimada sin carga. Diferencia = caída de tensión por la resistencia interna.",
    "Spannung": "Tensión",
    "Ruhespannung (geschätzt)": "Tensión en reposo (estimada)",
    "Akkustrom": "Corriente de la batería",
    "Strom aus dem Flugakku.": "Corriente de la batería de vuelo.",
    "Strom": "Corriente",
    "Drehzahl": "Rpm",
    "1000 U/min": "1000 rpm",
    "Drehzahl des Antriebs.": "Rpm de la propulsión.",
    "Höhe": "Altura",
    "Relative Höhe über dem Startpunkt.": "Altura relativa sobre el punto de despegue.",
    "Empfangsstärke (RSSI)": "Intensidad de señal (RSSI)",
    "Ethos warnt üblicherweise unter 45.": "Ethos suele avisar por debajo de 45.",
    "Telemetrie-Rahmen (VFR)": "Tramas de telemetría (VFR)",
    "Anteil korrekt empfangener Rahmen. Einbrüche = Empfangsstörung.":
        "Porcentaje de tramas recibidas correctamente. Caídas = problema de recepción.",
    "Zum Abgleich: Einbrüche bei großer Höhe/Entfernung oder in bestimmten Fluglagen?":
        "Para comparar: ¿caídas a gran altura/distancia o en ciertas actitudes de vuelo?",
    "Empfängerstrom": "Corriente del receptor",
    "Dreiecke: Spitzen über der gestrichelten Schwelle, Farbe = Anlass.":
        "Triángulos: picos por encima del umbral discontinuo, color = causa.",
    "Spitzenschwelle {thr:.2f} A": "Umbral de pico {thr:.2f} A",
    "Spitze: {cause}": "Pico: {cause}",
    "Knüppelwege": "Recorrido de los sticks",
    "Schnelle, große Ausschläge erzeugen Servolast. Senkrechte Linien: Schalter.":
        "Los movimientos rápidos y amplios generan carga en los servos. Líneas verticales: interruptores.",
    "Gasknüppel.": "Stick de gas.",
    "Bricht sie bei Stromspitzen ein, ist die Versorgung zu schwach.":
        "Si cae durante los picos de corriente, la alimentación es demasiado débil.",
    "Roll- und Nickwinkel.": "Ángulos de alabeo y cabeceo.",
    "Roll": "Alabeo",
    "Nick": "Cabeceo",
    "Wie schnell sich die Lage ändert (aus Roll und Nick).": "Con qué rapidez cambia la actitud (según alabeo y cabeceo).",
    "Beschleunigung, 1 g = Geradeausflug.": "Aceleración, 1 g = vuelo recto y nivelado.",

    # ---------------- table headings ----------------
    "Datum": "Fecha",
    "Dauer s": "Duración s",
    "entnommen mAh": "consumido mAh",
    "ESC mAh": "ESC mAh",
    "Abw. %": "Desv. %",
    "Energie Wh": "Energía Wh",
    "Ø A": "Ø A",
    "max A": "máx A",
    "P max W": "P máx W",
    "C Spitze": "C pico",
    "SoC Start %": "SoC inicio %",
    "SoC Ende %": "SoC final %",
    "SoC Ende (U) %": "SoC final (U) %",
    "SoC Abw. Pkt": "SoC desv. ptos",
    "Kapazität mAh": "Capacidad mAh",
    "Ri/Zelle mΩ": "Ri/celda mΩ",
    "Ri Anfang": "Ri inicio",
    "Ri Ende": "Ri final",
    "U Ref V/Z": "U ref V/c",
    "U min V/Z": "U mín V/c",
    "U Ende V/Z": "U final V/c",
    "U Ende Quelle": "Origen U final",
    "Reserve V/Z": "Reserva V/c",
    "Timer s": "Temp. s",
    "rpm P90": "rpm P90",
    "P Ref W": "P ref W",
    "Höhe max": "Altura máx",
    "Wh/100m": "Wh/100m",
    "g max": "g máx",
    "RSSI min": "RSSI mín",
    "VFR min": "VFR mín",
    "Rx V min": "Rx V mín",
    "Rx A Ø": "Rx A Ø",
    "Rx A max": "Rx A máx",
    "Rx Spitzen": "Rx picos",
    "Sp. Schalter": "Picos interr.",
    "Sp. o. Anlass": "Picos sin causa",
    "r Rx/Knüppel": "r Rx/sticks",
    "R² Fit": "R² ajuste",
    "Versatz s": "Desfase s",
    "Auffälligkeiten": "Anomalías",
}
