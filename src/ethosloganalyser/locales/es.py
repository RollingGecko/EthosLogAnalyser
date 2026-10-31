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
    "Daten & Einstellungen": "Datos y ajustes",
    "Zusammenfassung": "Resumen",
    "Akku": "Batería",
    "Belastung & Flugprofil": "Carga y perfil de vuelo",
    "Antrieb": "Propulsión",
    "Funk & Bordnetz": "Radio y alimentación a bordo",
    "Einzelflug": "Vuelo individual",
    "Tabelle": "Tabla",
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
    "Datei": "Archivo",

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

    # ---------------- messages ----------------
    "Eingabefehler": "Error de entrada",
    "Bitte gültige Zahlen in den Einstellungen eintragen.": "Introduzca números válidos en los ajustes.",
    "Zielordner für Bericht und Diagramme": "Carpeta de destino para informe y gráficos",
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
        "topan (zumbido en el extremo) o están defectuosos; los instantes, en el vuelo individual.",

    # ---------------- summary report ----------------
    "Keine auswertbaren Flüge gefunden.": "No se encontraron vuelos analizables.",
    "ÜBERSICHT": "VISTA GENERAL",
    "Akku: {cells}S {chem}": "Batería: {cells}S {chem}",
    "  (Zellenzahl automatisch erkannt)": "  (número de celdas detectado automáticamente)",
    ", Nennkapazität {cap:.0f} mAh": ", capacidad nominal {cap:.0f} mAh",
    "Gesamt entnommen: {ah:.1f} Ah": "Total consumido: {ah:.1f} Ah",
    "  (≈ {cycles:.1f} Vollzyklen)": "  (≈ {cycles:.1f} ciclos completos)",
    "AKKU ÜBER ALLE FLÜGE": "BATERÍA EN TODOS LOS VUELOS",
    "Details zu jedem einzelnen Flug (auch zum letzten) stehen im Einzelflug (Doppelklick auf den Flug im Logbuch).":
        "Los detalles de cada vuelo (también del último) están en el vuelo individual (doble clic en el vuelo del libro de vuelo).",
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
    "  - unzuverlässig, solange die Zellchemie nicht passt (siehe oben)":
        "  - poco fiable mientras la química de celda no concuerde (ver arriba)",
    "Innenwiderstand je Zelle: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)":
        "Resistencia interna por celda: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)",
    "Spannung bei {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/Zelle ({mv:+.0f} mV)":
        "Tensión a {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/celda ({mv:+.0f} mV)",
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
    "Balken über dem roten Punkt: länger geflogen als für die Reserve empfohlen.":
        "Barra por encima del punto rojo: se voló más tiempo del recomendado para la reserva.",

    # ---------------- charts: drive ----------------
    "Antrieb und Sensor-Plausibilität": "Propulsión y plausibilidad del sensor",
    "keine Drehzahl im Log": "sin rpm en el log",
    "Kennlinie: Leistung gegen Drehzahl": "Curva: potencia frente a rpm",
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
    "Schwarz = ohne erkennbaren Anlass: Servos prüfen. Details im Einzelflug (Doppelklick im Logbuch).":
        "Negro = sin causa aparente: compruebe los servos. Detalles en el vuelo individual (doble clic en el libro de vuelo).",
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
    " Timer-Empfehlung": " recomendación de temporizador",
    "entnommen": "consumido",
    "Leistung": "Potencia",
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
    "Roll": "Alabeo",
    "Nick": "Cabeceo",
    "Beschleunigung, 1 g = Geradeausflug.": "Aceleración, 1 g = vuelo recto y nivelado.",

    # ---------------- table headings ----------------
    "Datum": "Fecha",
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

    # ---------------- data quality, ageing model, period filter ----------------
    "Stromsensor hängt am Anschlag":
        "Sensor de corriente bloqueado en el máximo",
    "Spannungsausfall":
        "Caída de la señal de tensión",
    "Ruhespannung nach der Landung unmöglich":
        "Tensión en reposo tras el aterrizaje imposible",
    "VFR außerhalb 0–100 %":
        "VFR fuera de 0–100 %",
    "Innenwiderstand unplausibel":
        "Resistencia interna inverosímil",
    "Der Strom liegt fast den ganzen Flug am Höchstwert (Sensor übersteuert oder falsch skaliert). Entnommene Ladung, Ladezustand, Kapazität, Innenwiderstand und Timer dieser Flüge werden nicht verwendet.":
        "La corriente se mantiene en su máximo casi todo el vuelo (sensor saturado o mal escalado). La carga consumida, el estado de carga, la capacidad, la resistencia interna y el temporizador de estos vuelos no se usan.",
    "Die Spannung fällt im Flug auf unter {limit:.1f} V/Zelle (Sensor- oder Kabelausfall, kein Spannungseinbruch des Akkus). Spannungs- und Akkuwerte dieser Flüge werden nicht verwendet.":
        "La tensión cae por debajo de {limit:.1f} V/celda durante el vuelo (fallo de sensor o de cable, no una caída de tensión de la batería). Los valores de tensión y de batería de estos vuelos no se usan.",
    "Die gemessene Spannung nach der Landung liegt unter der Spannung unter Last am Flugende – das ist physikalisch unmöglich (Akku vermutlich abgesteckt oder Sensor aus, bevor die Messung fertig war). Verwendet wird die Modellschätzung der Ruhespannung; keine Tiefentladung.":
        "La tensión medida tras el aterrizaje es inferior a la tensión bajo carga al final del vuelo, algo físicamente imposible (probablemente se desconectó la batería o se apagó el sensor antes de terminar la medición). Se usa la estimación del modelo de la tensión en reposo; no hay descarga profunda.",
    "VFR-Werte außerhalb von 0–100 % (ältere Firmware oder Sensorfehler) werden nicht verwendet.":
        "Los valores de VFR fuera de 0–100 % (firmware antiguo o error de sensor) no se usan.",
    "Innenwiderstand weniger als halb oder mehr als doppelt so groß wie der Median aller Flüge (Fit gescheitert, z. B. wegen fehlerhafter Strom- oder Spannungswerte). Wird nicht für Trends verwendet.":
        "Resistencia interna inferior a la mitad o superior al doble de la mediana de todos los vuelos (ajuste fallido, p. ej. por valores de corriente o tensión erróneos). No se usa para las tendencias.",
    "Kapazität normiert":
        "Capacidad normalizada",
    "Messfehler":
        "Errores de medición",
    "Auf {depth:.0f} % Entladetiefe bezogen.":
        "Referida a una profundidad de descarga del {depth:.0f} %.",
    "80 % der Nennkapazität":
        "80 % de la capacidad nominal",
    "zu wenige Flüge mit gültigen Werten für einen Trend (mindestens {min} über {span} Flüge)":
        "demasiados pocos vuelos con valores válidos para una tendencia (al menos {min} a lo largo de {span} vuelos)",
    "  Trend: {slope} {unit} je 100 Flüge (90 %-Bereich {lo} bis {hi}) – {verdict}":
        "  Tendencia: {slope} {unit} cada 100 vuelos (intervalo del 90 %: {lo} a {hi}) – {verdict}",
    "die Werte streuen zu stark (±{pct:.0f} %)":
        "los valores tienen demasiada dispersión (±{pct:.0f} %)",
    "kein gesicherter Trend – der 90-%-Bereich der Steigung schließt null ein":
        "sin tendencia fiable: el intervalo del 90 % de la pendiente incluye el cero",
    "der Wert verbessert sich über den Zeitraum – kein Alterungssignal (z. B. Temperatur, Jahreszeit oder Einfliegen)":
        "el valor mejora a lo largo del periodo: no hay señal de envejecimiento (p. ej. temperatura, estación del año o rodaje)",
    "  Trend: zu wenige Flüge für einen Trend (mindestens {min} über {span} Flüge)":
        "  Tendencia: demasiados pocos vuelos para una tendencia (al menos {min} a lo largo de {span} vuelos)",
    "kein gesicherter Trend":
        "sin tendencia fiable",
    "gesichert fallend":
        "descenso fiable",
    "gesichert steigend":
        "aumento fiable",
    "DATENQUALITÄT (Messfehler, nicht in Trends und Warnungen)":
        "CALIDAD DE LOS DATOS (errores de medición, no usados en tendencias ni avisos)",
    "Restkapazität (SoH): ca. {soh:.0f} % der Nennkapazität  (aktuell ≈ {cur:.0f} ± {err} mAh, Nennkapazität {nom:.0f} mAh)":
        "Capacidad restante (SoH): aprox. {soh:.0f} % de la capacidad nominal  (actualmente ≈ {cur:.0f} ± {err} mAh, capacidad nominal {nom:.0f} mAh)",
    "Restkapazität (SoH): ca. {soh:.0f} % der Anfangskapazität  (aktuell ≈ {cur:.0f} ± {err} mAh, Anfangswert ≈ {start:.0f} mAh; Nennkapazität nicht eingetragen)":
        "Capacidad restante (SoH): aprox. {soh:.0f} % de la capacidad inicial  (actualmente ≈ {cur:.0f} ± {err} mAh, valor inicial ≈ {start:.0f} mAh; capacidad nominal no introducida)",
    "Restlebensdauer: ca. {n:.0f} Flüge (90 %-Bereich {lo:.0f}–{hi:.0f}) – das frühere der Kriterien 80 % SoH und +50 % Ri":
        "Vida útil restante: aprox. {n:.0f} vuelos (intervalo del 90 %: {lo:.0f}–{hi:.0f}), el primero de los criterios 80 % SoH y +50 % Ri",
    "Hinweis auf mehrere Akkus: Die Kapazitätswerte bilden zwei Gruppen (≈ {low:.0f} mAh in {n_low} Flügen, ≈ {high:.0f} mAh in {n_high} Flügen). Alterungsaussagen über diesen Zeitraum gelten dann für keinen einzelnen Akku. Zeitraum auf einen Akku eingrenzen (Daten & Einstellungen → Zeitraum).":
        "Indicio de varias baterías: los valores de capacidad forman dos grupos (≈ {low:.0f} mAh en {n_low} vuelos, ≈ {high:.0f} mAh en {n_high} vuelos). Las conclusiones sobre el envejecimiento en este periodo no se aplican entonces a ninguna batería concreta. Limite el periodo a una batería (Datos y ajustes → Periodo).",
    "Kapazitäts-SoH nicht bestimmbar: zu wenige Flüge mit gültiger Kapazitätsschätzung (≥ 40 % Entladetiefe; vorhanden {n}, nötig {min}).":
        "No se puede determinar el SoH de capacidad: demasiados pocos vuelos con una estimación de capacidad válida (≥ 40 % de profundidad de descarga; disponibles {n}, necesarios {min}).",
    "Keine Messfehler erkannt.":
        "No se detectaron errores de medición.",
    "MESSFEHLER IN DIESEM FLUG (nicht in Trends und Warnungen)":
        "ERRORES DE MEDICIÓN EN ESTE VUELO (no usados en tendencias ni avisos)",
    "  gegenüber dem Anfangswert dieses Zeitraums (≈ {start:.0f} mAh bei Flug {first:.0f}): {pct:+.1f} %":
        "  respecto al valor inicial de este periodo (≈ {start:.0f} mAh en el vuelo {first:.0f}): {pct:+.1f} %",
    "  Prognose: 80 % SoH in ca. {n:.0f} weiteren Flügen (90 %-Bereich {lo:.0f}–{hi:.0f})":
        "  Pronóstico: 80 % SoH en aprox. {n:.0f} vuelos más (intervalo del 90 %: {lo:.0f}–{hi:.0f})",
    "  Prognose: +50 % Ri (Faustregel Lebensende) in ca. {n:.0f} weiteren Flügen (90 %-Bereich {lo:.0f}–{hi:.0f})":
        "  Pronóstico: +50 % Ri (regla práctica de fin de vida) en aprox. {n:.0f} vuelos más (intervalo del 90 %: {lo:.0f}–{hi:.0f})",
    "Restlebensdauer: keine belastbare Prognose im gewählten Zeitraum (Gründe siehe oben).":
        "Vida útil restante: no hay pronóstico fiable para el periodo seleccionado (motivos arriba).",
    "  80 % SoH ist bereits erreicht.":
        "  Ya se ha alcanzado el 80 % de SoH.",
    "  Keine Prognose: {reason}.":
        "  Sin pronóstico: {reason}.",
    "  +50 % Ri ist bereits erreicht.":
        "  Ya se ha alcanzado +50 % de Ri.",
    "  Keine Ri-Prognose: {reason}.":
        "  Sin pronóstico de Ri: {reason}.",
    "  Trend nicht belastbar: ohne Entladetiefen-Korrektur {raw:+.0f} mAh je 100 Flüge, mit Korrektur {corr:+.0f} mAh je 100 Flüge – die Richtung hängt allein an der Korrektur, weil später tiefer geflogen wurde.":
        "  Tendencia no fiable: sin corrección de la profundidad de descarga {raw:+.0f} mAh por cada 100 vuelos, con corrección {corr:+.0f} mAh por cada 100 vuelos; la dirección depende solo de la corrección, porque los vuelos posteriores fueron más profundos.",
    " Linie gestrichelt: kein gesicherter Trend (Mittelwert).":
        " Línea discontinua: sin tendencia confirmada (valor medio).",
    "Trend unsicher, siehe Bericht.":
        "Tendencia incierta, ver informe.",
    "steigend":
        "ascendente",
    "fallend":
        "descendente",
    "ohne gesicherten Trend":
        "sin tendencia confirmada",
    "die Trendaussage ist unsicher (siehe oben)":
        "la tendencia es incierta (ver arriba)",
    "rechnerisch {verdict}, aber unsicher":
        "calculado {verdict}, pero incierto",
    "  Unsicher: Die Kapazität scheint zu steigen – bei einem Akku unplausibel (Streuung der Schätzung, Temperatur, Jahreszeit). Angezeigt wird der Mittelwert ohne Trend.":
        "  Incierto: la capacidad parece aumentar, lo que no es plausible en una batería (dispersión de la estimación, temperatura, estación del año). Se muestra el valor medio sin tendencia.",
    "  Kapazität einheitlich auf {depth:.0f} % Entladetiefe bezogen. Die Schätzung hängt von der Entladetiefe ab: {coef:+.0f} ± {se:.0f} mAh je Prozentpunkt, ermittelt nur aus Flügen am selben Tag ({days} Tage), damit der Alterungstrend nicht mitgeschätzt wird.":
        "  Capacidad referida uniformemente a {depth:.0f} % de profundidad de descarga. La estimación depende de la profundidad de descarga: {coef:+.0f} ± {se:.0f} mAh por punto porcentual, determinado solo a partir de vuelos del mismo día ({days} días), para que la tendencia de envejecimiento no se estime junto con ella.",
    "Innenwiderstand je Zelle: ≈ {r:.2f} mΩ, keine gesicherte Änderung (Mittelwert)":
        "Resistencia interna por celda: ≈ {r:.2f} mΩ, sin cambio confirmado (valor medio)",
    "  Kurzflüge unter {pct:.0f} % Entladetiefe zählen nicht für Kapazität und Innenwiderstand: Flug {flights}":
        "  Los vuelos cortos por debajo del {pct:.0f} % de profundidad de descarga no cuentan para la capacidad ni la resistencia interna: vuelo {flights}",
    "Spannung bei {iref:.0f} A / {qref:.0f} mAh: ≈ {u:.3f} V/Zelle, keine gesicherte Änderung (Mittelwert)":
        "Tensión a {iref:.0f} A / {qref:.0f} mAh: ≈ {u:.3f} V/celda, sin cambio confirmado (valor medio)",
    "  Unsicher: Kapazität und Spannung bei Referenzlast zeigen nicht in dieselbe Richtung (Kapazität: {cap}, Spannung: {uref}). Kapazität ohne Trend angezeigt, keine Prognose.":
        "  Incierto: la capacidad y la tensión a carga de referencia no apuntan en la misma dirección (capacidad: {cap}, tensión: {uref}). Capacidad mostrada sin tendencia, sin pronóstico.",
    "  gegenüber dem Anfang dieses Zeitraums: keine gesicherte Änderung (Wert = Mittelwert über den Zeitraum)":
        "  respecto al inicio de este periodo: sin cambio confirmado (valor = media del periodo)",
    "  Unsicher: Die Entladetiefe ändert sich über den Zeitraum (r = {r:.2f}). Ohne mehrere Flüge am selben Tag lässt sich ihr Einfluss nicht vom Alterungstrend trennen.":
        "  Incierto: la profundidad de descarga cambia a lo largo del periodo (r = {r:.2f}). Sin varios vuelos el mismo día, su efecto no puede separarse de la tendencia de envejecimiento.",
    "EthosLogAnalyser {version} – Flug- und Akku-Analyse (FrSky Ethos Logs)":
        "EthosLogAnalyser {version} – análisis de vuelos y baterías (logs de FrSky Ethos)",
    "TESTVERSION {version} – EthosLogAnalyser – nicht für den normalen Gebrauch":
        "VERSIÓN DE PRUEBA {version} – EthosLogAnalyser – no para el uso normal",
    "EthosLogAnalyser, Version {version}":
        "EthosLogAnalyser, versión {version}",
    "Testversion ({tag}) aus der automatischen Prüfung eines Pull-Requests bzw. Branches – zum Abnahmetest, kein Release.":
        "Versión de prueba ({tag}) de la comprobación automática de un pull request o una rama: para pruebas de aceptación, no es una versión publicada.",
    "Quellcode, Releases und Anleitung: github.com/RollingGecko/EthosLogAnalyser":
        "Código fuente, versiones y documentación: github.com/RollingGecko/EthosLogAnalyser",
    "Über":
        "Acerca de",
    "  t = {t}  {peak:.2f} A, {dur:.1f} s  →  {why}:  Knüppel {stick} %/s, Drehrate {rate} °/s, {g} g, Gas {gas} %, Höhe {alt} m":
        "  t = {t}  {peak:.2f} A, {dur:.1f} s  →  {why}:  sticks {stick} %/s, velocidad de giro {rate} °/s, {g} g, gas {gas} %, altura {alt} m",
    "Mittlere Leistung {value}, {t80} über 80 % des Spitzenstroms, mittleres Gas {gas} %":
        "Potencia media {value}, {t80} por encima del 80 % de la corriente de pico, gas medio {gas} %",
    "zu kurz ({dur} < {min})":
        "demasiado corto ({dur} < {min})",
    "Zeit seit Motorstart [min:s]":
        "Tiempo desde el arranque del motor [min:s]",
    "Flugzeit und Timer-Empfehlung [min:s]":
        "Tiempo de vuelo y recomendación de temporizador [min:s]",
    "Dauer min:s":
        "Duración min:s",
    "Timer min:s":
        "Temp. min:s",
    "Flug {no} – {date}":
        "Vuelo {no} – {date}",
    "Flug {no}":
        "Vuelo {no}",
    "Schließen (Esc)":
        "Cerrar (Esc)",
    "{title} – Vollbild (Esc schließt)":
        "{title} – pantalla completa (Esc cierra)",
    "Maus über einen Datenpunkt: Wert.  Werkzeugleiste unten: zoomen, verschieben, speichern.":
        "Ratón sobre un punto: su valor.  Barra de herramientas abajo: zoom, desplazar, guardar.",
    "Maus über das Diagramm bewegen: Werte zum Zeitpunkt.   Mausrad: zoomen  ·  Ziehen mit linker Maustaste: verschieben  ·  Doppelklick oder Rechtsklick: Diagramm vergrößern":
        "Mueva el ratón sobre el gráfico: valores en ese instante.   Rueda del ratón: zoom  ·  arrastrar con el botón izquierdo: desplazar  ·  doble clic o clic derecho: ampliar el gráfico",
    "Ganze Seite vergrößern":
        "Ampliar página completa",
    "Dieses Diagramm vergrößern":
        "Ampliar este gráfico",
    "Doppelklick oder Rechtsklick auf ein Diagramm: allein vergrößern":
        "Doble clic o clic derecho en un gráfico: ampliarlo solo",
    "P Abw. Kurve %":
        "P desv. curva %",
    "V/Zelle":
        "V/celda",
    "Akkuspannung je Zelle":
        "Tensión de la batería por celda",
    "Akkuspannung (gesamt)":
        "Tensión de la batería (total)",
    "Mittlere Zellspannung = Gesamtspannung / {cells} Zellen.":
        "Tensión media por celda = tensión total / {cells} celdas.",
    "Zellenzahl unbekannt: Gesamtspannung des Akkus.":
        "Número de celdas desconocido: tensión total de la batería.",
    "Rollwinkel und Querruder":
        "Ángulo de alabeo y alerones",
    "Links Rollwinkel [°], rechts Querruder-Knüppel [%] (Ethos-Kanalwert, ±100 % = Vollausschlag).":
        "Izquierda: ángulo de alabeo [°], derecha: stick de alerones [%] (valor del canal Ethos, ±100 % = recorrido máximo).",
    "Nickwinkel und Höhenruder":
        "Ángulo de cabeceo y profundidad",
    "Links Nickwinkel [°], rechts Höhenruder-Knüppel [%] (Ethos-Kanalwert).":
        "Izquierda: ángulo de cabeceo [°], derecha: stick de profundidad [%] (valor del canal Ethos).",
    "Gas und Seitenruder":
        "Gas y dirección",
    "Gas 0–100 %, Seitenruder-Knüppel ±100 %. Senkrechte Linien: Schalter.":
        "Gas 0–100 %, stick de dirección ±100 %. Líneas verticales: interruptores.",
    "Grenze unter Last {v:.2f} V/Zelle":
        "Límite bajo carga {v:.2f} V/celda",
    "Mindest-Ruhespannung {v:.2f} V/Zelle":
        "Tensión mínima en reposo {v:.2f} V/celda",
    "{stick} (Knüppel)":
        "{stick} (stick)",
    "Nicht im Log oder nicht bewegt: {channels}.":
        "No están en el log o no se movieron: {channels}.",
    "Farbe: frühe Flüge violett → späte gelb. Schwarz: Gesamtkennlinie aller Flüge mit Streuband. Liegt ein Flug darüber, braucht er mehr Leistung bei gleicher Drehzahl: Verschleiß/Fremdkörper.":
        "Color: primeros vuelos violeta → últimos amarillo. Negro: curva global de todos los vuelos con banda de dispersión. Un vuelo por encima necesita más potencia a las mismas rpm: desgaste/cuerpo extraño.",
    "Gesamtkennlinie (Median aller Flüge)":
        "Curva global (mediana de todos los vuelos)",
    "Streuband 25–75 %":
        "Banda de dispersión 25–75 %",
    "Gesamtkennlinie: {classes} Drehzahlklassen aus {n} Flügen; Flüge weichen {lo:+.1f} bis {hi:+.1f} % davon ab (größte Abweichung: Flug {no})":
        "Curva global: {classes} clases de rpm de {n} vuelos; los vuelos se desvían de ella entre {lo:+.1f} y {hi:+.1f} % (mayor desviación: vuelo {no})",
    "Leistung gegenüber der Gesamtkennlinie aller Flüge: {dev:+.1f} % (Median bei gleicher Drehzahl)":
        "Potencia frente a la curva global de todos los vuelos: {dev:+.1f} % (mediana a las mismas rpm)",
    "(unbekannt)":
        "(desconocido)",
    "Für das Modell {model} sind noch keine Akku-Einstellungen gespeichert: Bitte im Reiter „Daten & Einstellungen“ die Zellchemie auswählen und die Nennkapazität eintragen. Bis dahin wird LiPo angenommen – Ladezustand, Alterung und Restkapazität können falsch sein.":
        "Todavía no hay ajustes de batería guardados para el modelo {model}: elija la química de celda e introduzca la capacidad nominal en la pestaña «Datos y ajustes». Hasta entonces se supone LiPo; el estado de carga, el envejecimiento y la capacidad restante pueden ser incorrectos.",
    "Für dieses Modell noch nicht eingestellt: bitte Zellchemie auswählen und Nennkapazität eintragen (bis dahin wird LiPo angenommen).":
        "Aún no configurado para este modelo: elija la química de celda e introduzca la capacidad nominal (hasta entonces se supone LiPo).",
    "Akku-Einstellungen für dieses Modell fehlen":
        "Faltan los ajustes de batería de este modelo",
    "Logbuch":
        "Libro de vuelo",
    "Summen":
        "Totales",
    "Je Flugzeug":
        "Por aeronave",
    "Je Jahr":
        "Por año",
    "Jahr":
        "Año",
    "Je Monat":
        "Por mes",
    "Monat":
        "Mes",
    "Uhrzeit":
        "Hora",
    "Log-Dauer":
        "Duración del registro",
    "{ah:.1f} Ah ({mah:.0f} mAh)":
        "{ah:.1f} Ah ({mah:.0f} mAh)",
    "Flüge":
        "Vuelos",
    "Flugtage":
        "Días de vuelo",
    "Log-Dauer gesamt":
        "Duración total de registros",
    "Längster Flug (Log-Dauer)":
        "Vuelo más largo (duración del registro)",
    "Kürzester Flug (Log-Dauer)":
        "Vuelo más corto (duración del registro)",
    "Entnommen gesamt":
        "Total consumido",
    "{n} Flüge ohne Datum oder Log-Dauer – in den Summen nicht enthalten.":
        "{n} vuelos sin fecha o duración del registro – no incluidos en los totales.",
    "{n}  ({first} – {last})":
        "{n}  ({first} – {last})",
    "Log-Dauer = Zeit von „Motor scharf“ bis „Motor gesperrt“ im Log, nicht die reine Flugzeit.":
        "Duración del registro = tiempo desde «motor armado» hasta «motor bloqueado» en el registro, no el tiempo de vuelo puro.",
    "{dur}  (Flug {no}, {date})":
        "{dur}  (vuelo {no}, {date})",

    # ---------------- flight database ----------------
    "Analysefehler: {err}":
        "Error de análisis: {err}",
    "Datenbank":
        "Base de datos",
    "Es wurde eine neue Flug-Datenbank angelegt:\n{path}\n\nSollen die Logs aus dem bisher genutzten Ordner importiert werden?\n{folder}":
        "Se ha creado una nueva base de datos de vuelos:\n{path}\n\n¿Importar los logs de la carpeta usada hasta ahora?\n{folder}",
    "neu":
        "nuevo",
    "doppelt":
        "duplicado",
    "mögliches Duplikat":
        "posible duplicado",
    "nicht lesbar":
        "ilegible",
    "{size} MB":
        "{size} MB",
    "{size} kB":
        "{size} kB",
    "{new} neu (davon {flights} Flüge), {duplicate} doppelt, {suspicious} mögliche Duplikate, {unreadable} nicht lesbar":
        "{new} nuevos ({flights} de ellos vuelos), {duplicate} duplicados, {suspicious} posibles duplicados, {unreadable} ilegibles",
    "gleicher Inhalt wie {file} (übersprungen)":
        "mismo contenido que {file} (omitido)",
    "gleiches Modell und gleiche Startzeit wie {file} (importiert, markiert)":
        "mismo modelo y misma hora de inicio que {file} (importado, marcado)",
    "kein Flug":
        "sin vuelo",
    "Import-Bericht":
        "Informe de importación",
    "abgebrochen":
        "cancelado",
    "Ergebnis":
        "Resultado",
    "Hinweis":
        "Nota",
    "Datenbank leeren":
        "Vaciar base de datos",
    "Alle importierten Logs und Flüge aus der Datenbank löschen?\n\nDie Logdateien selbst bleiben unverändert.":
        "¿Borrar de la base de datos todos los logs y vuelos importados?\n\nLos archivos de log no se modifican.",
    "Neu …":
        "Nueva …",
    "Öffnen …":
        "Abrir …",
    "Speichern unter …":
        "Guardar como …",
    "Leeren …":
        "Vaciar …",
    "Dateien importieren …":
        "Importar archivos …",
    "Ordner importieren …":
        "Importar carpeta …",
    "Flug-Datenbank":
        "Base de datos de vuelos",
    "Alle Dateien":
        "Todos los archivos",
    "Neue Datenbank anlegen":
        "Crear nueva base de datos",
    "Datenbank öffnen":
        "Abrir base de datos",
    "Datenbank speichern unter":
        "Guardar base de datos como",
    "Eine Kopie der Datenbank wurde gespeichert:\n{path}\n\nGeöffnet bleibt weiterhin:\n{current}":
        "Se ha guardado una copia de la base de datos:\n{path}\n\nSigue abierta:\n{current}",
    "Logdateien importieren":
        "Importar archivos de log",
    "Ordner importieren (mit Unterordnern)":
        "Importar carpeta (con subcarpetas)",
    "keine Datenbank geöffnet":
        "ninguna base de datos abierta",
    "{logs} Logs: {flights} Flüge, {other} ohne Flug · Flugzeuge: {aircraft} · {size}":
        "{logs} logs: {flights} vuelos, {other} sin vuelo · aeronaves: {aircraft} · {size}",
    "Die Datei kann nicht als Flug-Datenbank geöffnet werden:\n{path}\n\n{error}":
        "El archivo no se puede abrir como base de datos de vuelos:\n{path}\n\n{error}",
    "Die Datenbank kann nicht angelegt werden:\n{path}\n\n{error}":
        "No se puede crear la base de datos:\n{path}\n\n{error}",
    "Die Kopie kann nicht gespeichert werden:\n{path}\n\n{error}":
        "No se puede guardar la copia:\n{path}\n\n{error}",
    "Die zuletzt geöffnete Datenbank wurde nicht gefunden:\n{path}\n\nEs wird die Standard-Datenbank verwendet.":
        "No se encontró la última base de datos abierta:\n{path}\n\nSe usa la base de datos predeterminada.",
    "Fehler bei der Verarbeitung:\n{error}":
        "Error durante el procesamiento:\n{error}",
    "Schließen":
        "Cerrar",
    "Datei:":
        "Archivo:",
    "{done} von {total}: {file}":
        "{done} de {total}: {file}",
    "wird vorbereitet …":
        "preparando …",
    "Letzter Import: {summary}":
        "Última importación: {summary}",
    "Ethos-Logs":
        "Logs de Ethos",
    "Auswertungswerte für die Statistik werden vorbereitet":
        "Preparando los valores para la estadística",
    "Neuberechnung":
        "Recálculo",

    # ---------------- areas, single flight from the database ----------------
    "Statistik":
        "Estadísticas",
    "Noch keine Flüge in der Datenbank.\n\nLogs importieren: „Daten & Einstellungen“ → Bereich „Datenbank“ → „Ordner importieren …“ oder „Dateien importieren …“.":
        "Todavía no hay vuelos en la base de datos.\n\nImportar logs: «Datos y ajustes» → sección «Base de datos» → «Importar carpeta …» o «Importar archivos …».",
    "Für diesen Flug sind keine Spannungs- und Stromdaten des Flugakkus im Log.\nDie Einzelflug-Ansichten brauchen sie bisher.":
        "El log de este vuelo no tiene tensión ni corriente de la batería de vuelo.\nPor ahora las vistas de vuelo individual las necesitan.",
    "Die Flüge von {aircraft} konnten nicht aus der Datenbank vorbereitet werden.":
        "No se pudieron preparar los vuelos de {aircraft} desde la base de datos.",
    "Die Flüge von {aircraft} werden aus der Datenbank vorbereitet …":
        "Preparando los vuelos de {aircraft} desde la base de datos …",
    "Vorbereitet: {done} von {total} Flügen":
        "Preparados: {done} de {total} vuelos",
    "keine Diagramme für diesen Flug":
        "sin gráficos para este vuelo",
    "‹ Logbuch":
        "‹ Libro de vuelo",
    "Flüge (Klick auf eine Spaltenüberschrift sortiert, Doppelklick öffnet den Einzelflug)":
        "Vuelos (clic en un encabezado para ordenar, doble clic abre el vuelo individual)",
    "Flug-Datenbank  ·  {flights} Flüge, {aircraft} Flugzeuge  ·  {first} – {last}":
        "Base de datos de vuelos  ·  {flights} vuelos, {aircraft} aeronaves  ·  {first} – {last}",
    "Die Flug-Datenbank enthält noch keine Flüge – Logs unter „Daten & Einstellungen“ → „Datenbank“ importieren.":
        "La base de datos aún no tiene vuelos: importe registros en «Datos y ajustes» → «Base de datos».",
    "  ·  {n} Logs ohne Flug":
        "  ·  {n} registros que no son vuelos",
    "Dieser Log ist nicht als Flug gezählt. Zum Ansehen im Logbuch in der Spalte „Flug“ auf ☑ umschalten.":
        "Este registro no cuenta como vuelo. Para verlo, cámbielo a ☑ en la columna «Vuelo» del libro de vuelos.",
    "alle":
        "todos",
    "Flugzeug":
        "Aeronave",
    "von":
        "desde",
    "bis":
        "hasta",
    "Zurücksetzen":
        "Restablecer",
    "Filter:":
        "Filtro:",
    "Nr.":
        "N.º",
    "Mögliches Duplikat: gleiches Flugzeug und gleiche Startzeit wie ein anderer Flug":
        "Posible duplicado: misma aeronave y misma hora de inicio que otro vuelo",
    "Summe":
        "Total",
    "{n} von {total} Flügen der Datenbank":
        "{n} de {total} vuelos de la base de datos",
    "  – ohne {n} Flüge ohne gültige Akkuwerte":
        "  – sin {n} vuelos sin valores de batería válidos",
    "Nicht-Flüge anzeigen":
        "Mostrar registros que no son vuelos",
    "{dur}  (Flug {no} der {aircraft}, {date})":
        "{dur}  (vuelo {no} de {aircraft}, {date})",
    "  ·  Filter aktiv":
        "  ·  filtro activo",
    "Noch keine Flüge in der Datenbank. Logs importieren: „Daten & Einstellungen“ → „Datenbank“ → „Ordner importieren …“ oder „Dateien importieren …“.":
        "Aún no hay vuelos en la base de datos. Importe registros: «Datos y ajustes» → «Base de datos» → «Importar carpeta …» o «Importar archivos …».",
    # notes and anomalies (WP-18)
    'kürzer als dieser Anteil des Medians': 'más corto que esta parte de la mediana',
    'über dem Median': 'sobre la mediana',
    'unter dem Median': 'bajo la mediana',
    'unter dem eigenen Median des Flugs': 'bajo la mediana propia del vuelo',
    'Spitzen je Flug': 'picos por vuelo',
    'Abweichung': 'desviación',
    'Flug deutlich kürzer als üblich': 'Vuelo mucho más corto de lo habitual',
    'Innenwiderstand höher als üblich': 'Resistencia interna mayor de lo habitual',
    'Empfängerstrom-Maximum höher als üblich': 'Máximo de corriente del receptor mayor de lo habitual',
    'RSSI-Minimum niedriger als üblich': 'Mínimo de RSSI menor de lo habitual',
    'Einbruch der Empfängerspannung im Flug': 'Caída de la tensión del receptor en vuelo',
    'Zellspannung unter Last unter der Grenze der Zellchemie': 'Tensión de celda bajo carga por debajo del límite de la química',
    'Ruhespannung am Flugende unter der Grenze der Zellchemie': 'Tensión en reposo al final por debajo del límite de la química',
    'Empfängerspannung unter der Mindestspannung des Modells': 'Tensión del receptor por debajo de la tensión mínima del modelo',
    'Empfängerstrom-Spitzen ohne erkennbaren Anlass': 'Picos de corriente del receptor sin causa aparente',
    'Strommessung weicht vom ESC-Zähler ab': 'La medición de corriente difiere del contador del ESC',
    'Flug deutlich kürzer als üblich: {value} statt typisch {median} (Median der Flüge dieses Flugzeugs). Nur ein Hinweis – z. B. ein abgebrochener oder vorzeitig gelandeter Flug.': 'Vuelo mucho más corto de lo habitual: {value} en lugar de {median} típico (mediana de los vuelos de este avión). Solo una indicación – p. ej. un vuelo interrumpido o un aterrizaje anticipado.',
    'Innenwiderstand {value:.0f} mΩ, {percent:.0f} % über dem Median dieses Flugzeugs ({median:.0f} mΩ). Hinweis: kalter oder nicht voll geladener Akku, Alterung oder ein kurzer Flug mit wenig Entladung sind mögliche Gründe.': 'Resistencia interna {value:.0f} mΩ, {percent:.0f} % sobre la mediana de este avión ({median:.0f} mΩ). Indicación: una batería fría o no cargada del todo, el envejecimiento o un vuelo corto con poca descarga son causas posibles.',
    'Höchster Empfängerstrom {value:.2f} A, {percent:.0f} % über dem Median dieses Flugzeugs ({median:.2f} A). Hinweis: Servos auf Schwergängigkeit oder Blockieren prüfen; Zeitpunkte der Stromspitzen siehe Diagramm „Empfängerstrom“.': 'Corriente máxima del receptor {value:.2f} A, {percent:.0f} % sobre la mediana de este avión ({median:.2f} A). Indicación: revisar si los servos van duros o se bloquean; momentos de los picos en el gráfico «Corriente del receptor».',
    'RSSI-Minimum {value:.0f} dB, {difference:.0f} dB unter dem Median dieses Flugzeugs ({median:.0f} dB). Hinweis: größere Entfernung, Fluglage oder Antennen prüfen.': 'Mínimo de RSSI {value:.0f} dB, {difference:.0f} dB bajo la mediana de este avión ({median:.0f} dB). Indicación: revisar mayor distancia, actitud de vuelo o antenas.',
    'Empfängerspannung fiel bei {time} auf {low:.2f} V, {percent:.0f} % unter ihren üblichen Wert in diesem Flug ({median:.2f} V). Hinweis: Empfängerstromversorgung, Stecker und Kabel prüfen.': 'La tensión del receptor bajó a {low:.2f} V en {time}, {percent:.0f} % por debajo de su valor habitual en este vuelo ({median:.2f} V). Indicación: revisar la alimentación del receptor, conectores y cables.',
    'Spannung unter Last fiel auf {value:.2f} V/Zelle, unter die Grenze von {limit:.2f} V/Zelle für {chem} ({cells} Zellen). Hinweis: möglicherweise zu tief entladen – bitte auch Zellchemie und Zellenzahl in den Akku-Einstellungen prüfen.': 'La tensión bajo carga bajó a {value:.2f} V/celda, por debajo del límite de {limit:.2f} V/celda para {chem} ({cells} celdas). Indicación: posiblemente descargada en exceso – revise también la química y el número de celdas en los ajustes de batería.',
    'Ruhespannung am Flugende {value:.2f} V/Zelle, unter der Grenze von {limit:.2f} V/Zelle für {chem} ({cells} Zellen). Hinweis: möglicherweise zu tief entladen – bitte auch Zellchemie und Zellenzahl prüfen.': 'Tensión en reposo al final del vuelo {value:.2f} V/celda, por debajo del límite de {limit:.2f} V/celda para {chem} ({cells} celdas). Indicación: posiblemente descargada en exceso – revise también la química y el número de celdas.',
    'Empfängerspannung fiel auf {value:.2f} V, unter die eingestellte Mindestspannung von {limit:.2f} V für dieses Modell. Hinweis: Empfängerstromversorgung prüfen.': 'La tensión del receptor bajó a {value:.2f} V, por debajo de la tensión mínima de {limit:.2f} V configurada para este modelo. Indicación: revisar la alimentación del receptor.',
    '{n} Empfängerstrom-Spitzen ohne Manöver, Start oder Landung. Hinweis: Servos auf Schwergängigkeit, Anschlag (Brummen in Endlage) und Defekte prüfen; Zeitpunkte siehe Einzelflug.': '{n} picos de corriente del receptor sin maniobra, despegue ni aterrizaje. Indicación: revisar si los servos van duros, topan (zumbido en el extremo) o están defectuosos; momentos en el vuelo individual.',
    'Entnommene Ladung aus der Strommessung ({drawn:.0f} mAh) weicht um {percent:+.1f} % vom ESC-Zähler ({counter:.0f} mAh) ab. Hinweis: Stromsensor prüfen oder kalibrieren.': 'La carga consumida según la medición de corriente ({drawn:.0f} mAh) difiere un {percent:+.1f} % del contador del ESC ({counter:.0f} mAh). Indicación: revisar o calibrar el sensor de corriente.',
    'Zuletzt gefunden: {n} automatische Hinweise.': 'Última búsqueda: {n} indicaciones automáticas.',
    'Regeln für die automatischen Hinweise je Flug (immer nur Hinweise, keine Diagnose). Vergleiche mit dem Median gelten ab 5 Flügen eines Flugzeugs.': 'Reglas para las indicaciones automáticas por vuelo (siempre solo indicaciones, nunca un diagnóstico). Las comparaciones con la mediana se aplican a partir de 5 vuelos de un avión.',
    'V (leer = aus)': 'V (vacío = desactivado)',
    'Info': 'Info',
    'Warnung': 'Advertencia',
    'Kritisch': 'Crítico',
    'automatisch': 'automática',
    'eigener Eintrag': 'entrada propia',
    'quittiert': 'confirmada',
    'offen': 'abierta',
    'Stufe': 'Nivel',
    'Status': 'Estado',
    'Herkunft': 'Origen',
    'Eigener Eintrag': 'Entrada propia',
    'Notiz und Auffälligkeiten': 'Nota y anomalías',
    'Notiz speichern': 'Guardar nota',
    'Quittieren / wieder öffnen': 'Confirmar / reabrir',
    'Eigener Eintrag …': 'Entrada propia …',
    'Eintrag löschen': 'Borrar entrada',
    'Keine Auffälligkeiten für diesen Flug.': 'Sin anomalías en este vuelo.',
    'Notiz:': 'Nota:',
    'Hinweis:': 'Indicación:',
    'Stufe:': 'Nivel:',
    'OK': 'Aceptar',
    'Abbrechen': 'Cancelar',
    'nur mit Notiz oder Auffälligkeit': 'solo con nota o anomalía',
    # statistics from the flight database (WP-19)
    'Statistik  ·  {n} von {total} Flügen der Datenbank': 'Estadística  ·  {n} de {total} vuelos de la base de datos',
    'Filter: {filter}': 'Filtro: {filter}',
    'Die Statistik zeigt gerade keine Flüge:\n{reason}': 'La estadística no muestra vuelos en este momento:\n{reason}',
    'Kein Flug passt zum Filter.': 'Ningún vuelo coincide con el filtro.',
    'Dieser Bereich ist noch experimentell: Werte und Auswertungen können sich ändern.': 'Esta área es todavía experimental: los valores y análisis pueden cambiar.',
    'Bitte im Filter ein Flugzeug wählen: Die Statistik wertet immer genau ein Flugzeug aus (gefiltert sind Flüge von {aircraft}).': 'Elija un avión en el filtro: la estadística siempre analiza exactamente un avión (los vuelos filtrados son de {aircraft}).',
    'Für diese Flüge von {aircraft} sind keine Spannungs- und Stromdaten des Flugakkus im Log. Die Statistik-Seiten brauchen sie bisher.': 'Estos vuelos de {aircraft} no tienen tensión ni corriente de la batería de vuelo en el log. Por ahora las páginas de estadística las necesitan.',
    'Monat {month:02d}': 'mes {month:02d}',
    '{aircraft}: {n} Flüge ausgewertet ({first} – {last})': '{aircraft}: {n} vuelos analizados ({first} – {last})',
    'keine': 'ninguno',
    '{count} von {total}': '{count} de {total}',
    'Alle auswählen': 'Seleccionar todo',
    'Alle abwählen': 'Quitar todo',
    'keine Jahre': 'ningún año',
    '{count} Jahre': '{count} años',
    'keine Monate': 'ningún mes',
    '{count} Monate': '{count} meses',
    'Monate {months}': 'meses {months}',
    'Diagramme': 'Gráficos',
    'Flugrekorder': 'Grabador de vuelo',
    '▶ Abspielen': '▶ Reproducir',
    '■ Stopp': '■ Parar',
    'Tempo': 'Velocidad',
    'Roll {bank}° · Nick {pitch}°': 'Alabeo {bank}° · Cabeceo {pitch}°',
    'keine Lagedaten': 'sin datos de actitud',
    'Für diesen Flug sind keine Daten für die Anzeigen des Flugrekorders im Log (Lage, Höhe, Steigen/Sinken, Antrieb, Akku, Knüppel).': 'Este vuelo no tiene datos para los instrumentos del registrador de vuelo en su registro (actitud, altura, velocidad vertical, propulsión, batería, mandos).',
    'Steigen/Sinken': 'Velocidad vertical',
    'U/min': 'rpm',
    'Gas / Seite': 'Gas / Timón',
    'Höhe / Quer': 'Profundidad / Alerón',
    'Höhe / Seite': 'Profundidad / Timón',
    'Gas / Quer': 'Gas / Alerón',
    'Mode {number}': 'Modo {number}',
    'Links: {left} · Rechts: {right}': 'Izquierda: {left} · Derecha: {right}',
    'Knüppelmodus': 'Modo de mandos',
    'Gilt für alle Flugzeuge und wirkt sofort im Flugrekorder.': 'Se aplica a todos los aviones y actúa de inmediato en el registrador de vuelo.',
    'Dieser Log enthält keine Zeitreihen.': 'Este registro no contiene series temporales.',
    'keine Knüppeldaten': 'sin datos de los mandos',
}
