# Methodology

How the app derives its metrics from the log values – and where the limits are. Code references are relative to `src/ethosloganalyser/`.

## Determining the flight (`analysis/flight.py`)

Ethos writes each sensor in its own rows; gaps are filled with the last value (at most 20 rows). The flight is the period in which the battery current exceeds the “motor running” threshold. If several motor runs are more than 20 s apart (motor test before take-off, run after a battery swap), the block with the **largest drawn charge** is used.

- **Resting voltage before take-off**: median of the last 15 rows before the motor run.
- **Resting voltage after landing**: measured 5–30 s after the last motor current without load. The battery keeps recovering afterwards, so the value tends to be slightly low.
- All time series are interpolated onto a 0.25 s grid.

## Drawn charge and energy

Charge = sum of current × time step (gaps longer than 5 s are not integrated). As a check it is compared with the ESC consumption counter; a deviation beyond ±5 % raises a “Sensor deviation” warning.

## Internal resistance

Linear model of the battery voltage during the flight:

U = U₀ − Rᵢ · I − k · Q

with current I and charge Q drawn so far. The k · Q term absorbs the voltage drop caused by discharge so that it is not counted as internal resistance. Ethos logs current and voltage with a slight time offset; the model is therefore fitted for offsets from −1 to +1.5 s and the offset with the best fit (R²) is used. Values above 1 Ω are rejected as implausible.

Rᵢ is additionally determined separately for the first, middle and last third of the drawn charge (a rise towards the end of the flight is normal).

## State of charge at the end

1. **Coulomb counting** (used): state of charge at take-off from the resting voltage, minus drawn charge / capacity. Capacity is the nominal capacity or – if none is entered – the estimated capacity.
2. **Resting voltage** (cross-check): resting voltage at the end mapped through the curve of the cell chemistry. If both differ by more than 15 percentage points, the flight is flagged “Implausible state of charge”.

The curves (resting voltage → state of charge) live in `config.py` and are approximations.

## Measurement errors (`analysis/quality.py`)

Some log values are physically impossible. They are not findings about the battery: they are taken out of all battery values, trends, start values and limit warnings and listed under *Data quality* in the summary (column `Datenfehler` in the table) instead of being reported as deep discharge or voltage collapse.

| Code | Rule | Consequence |
| --- | --- | --- |
| `current_stuck` | mean current ≥ 97 % of the maximum current (sensor saturated or wrongly scaled) | drawn charge, state of charge by coulomb counting, capacity, Rᵢ, voltage at reference load and timer of the flight are not used |
| `voltage_dropout` | lowest voltage under load below half the load limit of the cell chemistry (e.g. 1.4 V/cell for Li-Ion) | voltage and battery values of the flight are not used |
| `rest_voltage_invalid` | measured resting voltage after landing below the lowest voltage under load in the last 10 s of the flight (typically: battery unplugged or sensor off within the 5–30 s window) | the model estimate of the resting voltage is used instead |
| `vfr_invalid` | VFR below 0 % or above 100 % | the VFR value is not used |
| `ri_implausible` | Rᵢ below half or above twice the median of all flights (fit failed) | Rᵢ and voltage at reference load of the flight are not used |

## Capacity and ageing (`analysis/ageing.py`)

- **Estimated capacity** = drawn charge / drop in state of charge according to the resting voltage, only for a depth of discharge of at least 40 %; gross outliers (factor 1.6 from the median) are discarded. Flights below 40 % depth of discharge (short flights) are not used for the capacity nor for the internal-resistance trend: their resistance fit only covers the flat top of the discharge curve.
- **Depth correction**: the estimate depends strongly on the depth of discharge, because the resting-voltage curve is only an approximation and the voltage has not fully recovered when it is measured after landing (on the real logs −35 to −56 mAh per percentage point: deeper flights estimate lower). This bias must not be estimated from the same time series as the trend: when later flights go deeper – which is common – a fit of capacity over flight number and depth cannot tell the bias from ageing, and the correction takes the ageing trend with it (or invents one). The effect is therefore estimated **only from flights of the same day** (same battery age): capacity and depth are centred per day and the centred capacity is regressed on the centred depth. At least 3 days with two or more valid flights are needed; the effect is used if it is negative and significant (|t| ≥ 2). All capacities are then referred to the median depth of the analysed flights (column `Kap_norm_mAh`). If no within-day estimate is possible and the depth is correlated with the flight number (|r| ≥ 0.3), the capacity trend is marked as uncertain. The summary shows the effect with its standard error and the number of days used; if the direction of the trend flips with the correction, it says so instead of showing a trend.
- **One model for everything**: capacity, internal resistance and voltage at reference load are each described by one robust straight line over the flight number (Huber-weighted least squares). Huber weights only limit the influence of large residuals; no value is dropped by the fit, so low values at the end of the series that follow the trend stay fully in (measurement errors are removed beforehand). Values more than 3.5 robust standard deviations from the line are listed as strongly down-weighted. The *trend* is the slope with a 90 % range.
- **Shown values**: if the trend is significant and plausible, the *start value* is the line at the first flight and the *current value* the line at the last flight. Otherwise both are the robust mean level of the period (“no confirmed change”) and the chart draws it as a dashed horizontal line – a non-significant or implausible slope never appears as a rising or falling value. Implausible are: a significantly **rising capacity** (a battery does not gain capacity), a capacity trend that **contradicts the voltage at reference load** (one of them significantly falling, the other one not – both describe the same ageing), and a depth effect that could not be separated (see above). In these cases no forecast is made.
- **State of health (SoH)**: current capacity / nominal capacity. Without a nominal capacity: current / start value. With a nominal capacity the change against the start value of the selected period is shown as well.
- **Trend**: “reliably falling/rising” only if the 90 % range of the slope does not include zero; at least 10 valid values spread over at least 10 flights are needed.
- **Forecast**: flights until the line reaches 80 % of the SoH reference (capacity) or +50 % of the start value (Rᵢ), with the 90 % range from the slope. No forecast – with the reason stated – if there are too few values, if they scatter too much (capacity ±6 %, Rᵢ ±15 %), if the trend is not significant or uncertain (see *Shown values*), or if the value improves (e.g. a falling Rᵢ, which without temperature data is usually seasonal). The voltage at reference load is shown with its trend but has no end-of-life criterion.
- **Several batteries**: if the capacity values around the trend form two clearly separated groups (bimodality coefficient > 0.555, both groups ≥ 20 % of the flights, Ashman’s D > 3), the summary warns that ageing statements over the period apply to no single battery. Two batteries whose capacities differ by less than the scatter of the estimate (about ±2 %) cannot be told apart this way; then the period filter or a battery identifier in the log is needed.
- **Period filter**: *Data & settings → Period from/to* limits the analysis to the flights in that period (by the date in the file name), e.g. the flights of one battery.

## Timer recommendation

Per flight: the time at which the drawn charge reaches the capacity down to the desired reserve (extrapolated with the mean current of the last 60 s if needed). The recommendation is the median of the last five flights. Because the capacity estimate depends on the depth of discharge, the timer uses the estimate at the depth that corresponds to the reserve (within the observed range); with a nominal capacity entered, the smaller of the two is used.

## Drive

Electrical power over RPM is fitted as a power law P = a · nᵇ. The power demand at a fixed reference RPM is comparable across flights; if it rises, the drive is running harder (bearings, dirt, foreign object).

### Overall motor curve (`analysis/motor_curve.py`)

The points of one flight scatter too much to show a clear curve, so the chart *Curve: power vs. RPM* also draws an overall curve from all analysed flights:

1. **Steady points only.** Per flight, RPM (rolling median over 1 s) and power (rolling mean over 1 s) on the 0.25 s grid; a point is used if RPM > 1000, power > 100 W and the RPM changes by less than 5 % per second. Run-up, throttle changes and spool-down are left out: power and RPM are not in equilibrium there, and the two sensors are logged with a small time offset. Flights whose current is invalid (stuck current sensor, voltage dropouts; see *Measurement errors*) do not contribute.
2. **RPM classes.** The class width is a round value (250 … 20 000 RPM) giving about 25 classes between the 1st and 99th percentile of the pooled RPM (2026 logs: 5000 RPM).
3. **Median and band.** Per class: median power (black line, plotted at the median RPM of the class) and the 25–75 % quantiles (grey band). Median and quartiles are not moved by single outliers.
4. **Too few data → no class.** A class is used only with at least 40 points (10 s) from at least 3 flights (from all flights if fewer were analysed). Classes are connected by straight lines; there is no extrapolation beyond the outermost classes.
5. **Deviation per flight** (column `P_Kurve_Abw_pct`, table *P dev. curve %*, single-flight details): median of the relative deviations of the flight's steady points from the curve, linearly interpolated at their RPM. Positive = the flight needed more power for the same RPM. At least 40 steady points inside the curve are required.

Overall curve 2026 (33 flights, Li-Ion 13S): 17 classes from 23 700 to 101 500 RPM; flights deviate by −2.2 … +2.7 %.

## Receiver current spikes (`analysis/rx_spikes.py`)

Threshold = maximum of baseline + 4 · robust spread, 1.5 × baseline and baseline + 0.3 A. Spikes less than 1 s apart are merged. Each spike gets a cause, in this order (English label, internal code in brackets):

1. **Switch** (`switch`) – a switch was flipped from 3 s before to 1 s after the spike started.
2. **Manoeuvre** (`manoeuvre`) – fast stick movement, high rotation rate (roll/pitch) or high g-load.
3. **Take-off/landing** (`takeoff_landing`) – first 30 s, last 45 s or below 15 m altitude.
4. **No apparent cause** (`no_cause`) – none of the above; hints at binding or faulty servos.

Without attitude data (sticks, rotation rate, g-load) the cause is “no attitude data” (`no_attitude`).

## Receiver current per control surface (`analysis/rx_surfaces.py`)

**Status: analysis module only, not shown in the app yet.** The log contains only the **total** current of the receiver (`RxCurrent`), not the current of a single servo. A current per control surface can therefore only be **estimated** from how the sticks were moved; every value below is an estimate with an uncertainty range, never a measurement, and does not diagnose a fault.

Stick channels come from an assignment code → log column (`config.STICK_CHANNELS`, defaults `QR` aileron, `HR` elevator, `SR` rudder, `Gas` throttle; `Params.channels` can name other columns, e.g. for other transmitters). The stick inputs are logged, not the servo outputs: transmitter mixes (e.g. rudder → aileron) are invisible, and one channel may drive several servos (two aileron servos, a nose-wheel steering servo on the rudder channel).

Steps per flight (airborne part only: without the first 30 s and the last 45 s, above 15 m):

1. **Delay**: the receiver current is updated only about every 0.5 s and follows the stick with a delay. The delay (0–2 s) is chosen by the best fit; on the real logs it is 0.75 s in almost all flights.
2. **Regression**: receiver current(t + delay) = base current + Σ per surface (a · |deflection| + b · |stick speed|), deflection in fractions of full travel. *a* is the estimated current per 100 % deflection (holding the surface against the air load), *b* the extra current per 100 %/s of stick speed, the intercept the current with all sticks at neutral (base current). 90 % ranges come from a moving-block bootstrap with 10 s blocks (neighbouring samples are not independent).
3. **Combined manoeuvres**: periods in which all surfaces are at least 85 % deflected at the same time for 1 s or more (e.g. spins, snap rolls) are left out of the regression, including 4 s before and after – nothing in them separates the surfaces. They are reported separately with the receiver current during them, which makes them a repeated, comparable load across flights.
4. **Status per surface**: “few data” with less than 10 s of use (deflection ≥ 25 %); “not separable” if its deflection correlates with that of another surface by |r| ≥ 0.7; otherwise “ok”.
5. **Clean events** (plausibility check): periods of at least 0.75 s in which only this surface is deflected ≥ 25 % and all others are below 10 %. They are counted; an event-based value is only given from 5 events on.
6. **Spike → probable surface**: for every receiver current spike the surface with the largest deflection in the window from 1 s before to 0.25 s after (spike time − delay); “several” if a second surface is deflected at least 80 % as much (and ≥ 30 %), “none” if no surface reaches 30 %.
7. **Across flights**: a robust line (Huber weights as for battery ageing) through the per-flight values of one surface, weighted by the width of their 90 % range. A change is only reported when the 90 % range of the slope excludes zero **and** the change over the period is at least 0.1 A per 100 %.

What it showed on the 2026 logs of the reference model (33 flights, aileron servo known to bind since about April 2026):

- Delay 0.75 s, fit quality R² 0.2–0.55: much of the receiver current is not explained by the sticks (air load grows with speed², the current is sampled coarsely).
- Aileron and elevator could be separated statistically (|r| of the deflections ≤ 0.3), but **clean aileron events are rare** (median 7 per flight; the aileron is almost always moved together with the elevator). Elevator: about 50 per flight, rudder: about 2.
- Rudder: used only about 17 s per flight, mostly together with the aileron; its value per 100 % is the largest and the most uncertain.
- All receiver current spikes of 3 A and more (31) happened in combined full-deflection manoeuvres, with a flat 3.5–4.2 A from May to October. In April no such manoeuvre was flown, which alone explains the lower spike maxima of April.
- Across 2026: base current 0.61 → 0.90 A (rising), aileron 0.30 → 0.43 A per 100 % (rising), elevator 0.16 → 0.28 A per 100 % (rising), rudder no confirmed change. The method shows a general rise of the receiver current, but does **not** single out the aileron.

Limits: no airspeed (throttle and RPM as a stand-in made the fit worse), no servo temperature, no receiver voltage effect modelled, mixes and servo count per channel unknown, current resolution 0.01 A at about 2 Hz.

## Anomalies (`analysis/evaluate.py`)

Limits (deep discharge, voltage collapse under load, sensor deviation, spikes without cause) apply to every flight except for values that were recognised as measurement errors. Statistical outliers are only searched from 6 flights on: robust z-score above 3.5, for ageing metrics relative to the trend.

## Limitations

- No temperature data: internal resistance depends strongly on battery temperature.
- No individual cell voltages: weak cells and balancing problems cannot be detected.
- State of charge and timer are only as good as the nominal capacity or capacity estimate.
- Flight phases and Wh per 100 m climb are indicative (altitude is smoothed).
