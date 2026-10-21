# Methodology

How the app derives its metrics from the log values – and where the limits are. Code references are relative to `src/ethosloganalyser/`.

## Determining the flight (`analysis/flight.py`)

Ethos writes each sensor in its own rows; gaps are filled with the last value (at most 20 rows). The flight is the period in which the battery current exceeds the “motor running” threshold. If several motor runs are more than 20 s apart (motor test before take-off, run after a battery swap), the block with the **largest drawn charge** is used.

- **Resting voltage before take-off**: median of the last 15 rows before the motor run.
- **Resting voltage after landing**: measured 5–30 s after the last motor current without load. The battery keeps recovering afterwards, so the value tends to be slightly low.
- All time series are interpolated onto a 0.25 s grid.

## Drawn charge and energy

Charge = sum of current × time step (gaps longer than 5 s are not integrated). As a check it is compared with the ESC consumption counter; a deviation beyond ±5 % raises a “Sensorabweichung” (sensor deviation) warning.

## Internal resistance

Linear model of the battery voltage during the flight:

U = U₀ − Rᵢ · I − k · Q

with current I and charge Q drawn so far. The k · Q term absorbs the voltage drop caused by discharge so that it is not counted as internal resistance. Ethos logs current and voltage with a slight time offset; the model is therefore fitted for offsets from −1 to +1.5 s and the offset with the best fit (R²) is used. Values above 1 Ω are rejected as implausible.

Rᵢ is additionally determined separately for the first, middle and last third of the drawn charge (a rise towards the end of the flight is normal).

## State of charge at the end

1. **Coulomb counting** (used): state of charge at take-off from the resting voltage, minus drawn charge / capacity. Capacity is the nominal capacity or – if none is entered – the estimated capacity.
2. **Resting voltage** (cross-check): resting voltage at the end mapped through the curve of the cell chemistry. If both differ by more than 15 percentage points, the flight is flagged “Ladezustand unplausibel” (implausible state of charge).

The curves (resting voltage → state of charge) live in `config.py` and are approximations.

## Capacity and ageing (`analysis/fleet.py`)

- **Estimated capacity** = drawn charge / drop in state of charge according to the resting voltage, only for a depth of discharge of at least 40 %; gross outliers (factor 1.6 from the median) are discarded.
- **State of health (SoH)**: median of the latest flights vs. median of the first flights.
- **Voltage at reference load**: computed from the model above for every flight at the same current and drawn charge – makes flights with different profiles comparable.
- **Remaining life forecast**: linear trend until 80 % capacity or +50 % internal resistance, whichever comes first.

## Timer recommendation

Per flight: the time at which the drawn charge reaches the capacity down to the desired reserve (extrapolated with the mean current of the last 60 s if needed). The recommendation is the median of the last five flights.

## Drive

Electrical power over RPM is fitted as a power law P = a · nᵇ. The power demand at a fixed reference RPM is comparable across flights; if it rises, the drive is running harder (bearings, dirt, foreign object).

## Receiver current spikes (`analysis/rx_spikes.py`)

Threshold = maximum of baseline + 4 · robust spread, 1.5 × baseline and baseline + 0.3 A. Spikes less than 1 s apart are merged. Each spike gets a cause, in this order (labels as shown in the app):

1. **Schalter** (switch) – a switch was flipped from 3 s before to 1 s after the spike started.
2. **Manöver** (manoeuvre) – fast stick movement, high rotation rate (roll/pitch) or high g-load.
3. **Start/Landung** (take-off/landing) – first 30 s, last 45 s or below 15 m altitude.
4. **Ohne erkennbaren Anlass** (no apparent cause) – none of the above; hints at binding or faulty servos.

Without attitude data (sticks, rotation rate, g-load) the cause is “keine Lagedaten” (no attitude data).

## Anomalies (`analysis/evaluate.py`)

Limits (deep discharge, voltage collapse under load, sensor deviation, spikes without cause) apply to every flight. Statistical outliers are only searched from 6 flights on: robust z-score above 3.5, for ageing metrics relative to the trend.

## Limitations

- No temperature data: internal resistance depends strongly on battery temperature.
- No individual cell voltages: weak cells and balancing problems cannot be detected.
- State of charge and timer are only as good as the nominal capacity or capacity estimate.
- Flight phases and Wh per 100 m climb are indicative (altitude is smoothed).
