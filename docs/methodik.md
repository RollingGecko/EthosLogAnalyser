# Methodik

Wie die App aus den Logwerten ihre Kennzahlen berechnet – und wo die Grenzen liegen. Code-Verweise beziehen sich auf `src/ethosloganalyser/`.

## Flugabschnitt bestimmen (`analysis/flight.py`)

Ethos schreibt jeden Sensor in eigene Zeilen; Lücken werden mit dem letzten Wert aufgefüllt (höchstens 20 Zeilen). Als Flug gilt der Zeitraum mit Akkustrom über „Motor aktiv ab“. Liegen mehrere Motorläufe mehr als 20 s auseinander (Motortest vor dem Start, Lauf nach Akkuwechsel), wird der Block mit der **größten entnommenen Ladung** genommen.

- **Ruhespannung vor dem Start**: Median der letzten 15 Zeilen vor dem Motorlauf.
- **Ruhespannung nach der Landung**: gemessen 5–30 s nach dem letzten Motorstrom ohne Last. Der Akku erholt sich danach noch weiter, der Wert ist also eher etwas zu niedrig.
- Alle Zeitreihen werden auf ein Raster von 0,25 s interpoliert.

## Entnommene Ladung und Energie

Ladung = Summe aus Strom × Zeitschritt (Lücken über 5 s werden nicht mitintegriert). Zur Kontrolle wird sie mit dem ESC-Verbrauchszähler verglichen; über ±5 % Abweichung meldet die App „Sensorabweichung“.

## Innenwiderstand

Lineares Modell für die Akkuspannung während des Fluges:

U = U₀ − Rᵢ · I − k · Q

mit Strom I und bisher entnommener Ladung Q. Der Term k · Q fängt den Spannungsabfall durch Entladung ab, damit er nicht als Innenwiderstand gezählt wird. Ethos loggt Strom und Spannung mit leichtem Zeitversatz; deshalb wird das Modell für Versätze von −1 bis +1,5 s gerechnet und der Versatz mit der besten Anpassung (R²) genommen. Werte über 1 Ω gelten als unplausibel.

Zusätzlich wird Rᵢ getrennt für das erste, mittlere und letzte Drittel der entnommenen Ladung bestimmt (Anstieg zum Flugende ist normal).

## Ladezustand am Ende

1. **Ladungszählung** (verwendet): Ladezustand beim Start aus der Ruhespannung, minus entnommene Ladung / Kapazität. Kapazität ist die Nennkapazität oder – falls nicht eingetragen – die geschätzte Kapazität.
2. **Ruhespannung** (Gegenprobe): Ruhespannung am Ende über die Kennlinie der Zellchemie. Weichen beide um mehr als 15 Prozentpunkte ab, wird der Flug als „Ladezustand unplausibel“ markiert.

Die Kennlinien (Ruhespannung → Ladezustand) stehen in `config.py` und sind Näherungen.

## Kapazität und Alterung (`analysis/fleet.py`)

- **Geschätzte Kapazität** = entnommene Ladung / Abnahme des Ladezustands laut Ruhespannung, nur bei mindestens 40 % Entladetiefe; grobe Ausreißer (Faktor 1,6 vom Median) werden verworfen.
- **Restkapazität (SoH)**: Median der letzten gegen Median der ersten Flüge.
- **Spannung bei Referenzlast**: aus dem Modell oben für alle Flüge bei gleichem Strom und gleicher entnommener Ladung berechnet – macht Flüge mit unterschiedlichem Profil vergleichbar.
- **Lebensdauer-Prognose**: linearer Trend bis 80 % Kapazität bzw. +50 % Innenwiderstand, das frühere Kriterium zählt.

## Timer-Empfehlung

Für jeden Flug: Zeitpunkt, an dem die entnommene Ladung die Kapazität bis zur gewünschten Reserve erreicht (bei Bedarf mit dem mittleren Strom der letzten 60 s extrapoliert). Empfohlen wird der Median der letzten fünf Flüge.

## Antrieb

Elektrische Leistung über Drehzahl wird als Potenzgesetz P = a · nᵇ angepasst. Der Leistungsbedarf bei einer festen Referenzdrehzahl ist über die Flüge vergleichbar; steigt er, läuft der Antrieb schwerer (Lager, Verschmutzung, Fremdkörper).

## Empfängerstrom-Spitzen (`analysis/rx_spikes.py`)

Schwelle = Maximum aus Grundlast + 4 · robuste Streuung, 1,5 × Grundlast und Grundlast + 0,3 A. Spitzen mit weniger als 1 s Abstand werden zusammengefasst. Jede Spitze bekommt einen Anlass, in dieser Reihenfolge:

1. **Schalter** – ein Schalter wurde 3 s vor bis 1 s nach Beginn der Spitze umgelegt.
2. **Manöver** – schnelle Knüppelbewegung, hohe Drehrate (Roll/Nick) oder hohe G-Last.
3. **Start/Landung** – erste 30 s, letzte 45 s oder unter 15 m Höhe.
4. **Ohne erkennbaren Anlass** – nichts davon; Hinweis auf schwergängige oder defekte Servos.

Ohne Lagedaten (Knüppel, Drehrate, G-Last) heißt der Anlass „keine Lagedaten“.

## Auffälligkeiten (`analysis/evaluate.py`)

Grenzwerte (Tiefentladung, Spannungseinbruch unter Last, Sensorabweichung, Spitzen ohne Anlass) gelten für jeden Flug. Statistische Ausreißer werden erst ab 6 Flügen gesucht: robuster z-Wert über 3,5, bei Alterungsgrößen relativ zum Trend.

## Grenzen

- Keine Temperaturdaten: Der Innenwiderstand hängt stark von der Akkutemperatur ab.
- Keine Einzelzellspannungen: schwache Zellen und Balancing-Probleme sind nicht erkennbar.
- Ladezustand und Timer sind nur so gut wie die Nennkapazität bzw. Kapazitätsschätzung.
- Flugphasen und Wh je 100 m Steigen sind Richtwerte (Höhe geglättet).
