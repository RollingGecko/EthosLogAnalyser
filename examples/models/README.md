# Example Ethos model files

Model files (`.bin`) copied from the `models` folder of an FrSky Ethos transmitter.
They are test data for the planned model plan feature (parser for Ethos model files).

| File | Model | Format version | Notes |
|------|-------|----------------|-------|
| `model01.bin` | Viper Jet | 0x23 (new format) | 15 mixes, 17 channels, 8 curves, 3 flight modes; checked against the transmitter |
| `avanti_s_v2.bin` | Avanti S V2 | 0x0B (old format) | 3020 bytes; 9 mixes, 7 channels, 4 curves, 5 logic switches, 11 special functions, 2 timers, 13 sensors; not checked against the transmitter |
| `avanti_s_v2_format23.bin` | Avanti S V2 | 0x23 (new format) | 2431 bytes; a later export of the same model name in the new format; no reference data yet (useful to compare both formats) |

The Ethos model file format is not officially documented by FrSky. Everything the
app reads from these files was reverse-engineered from the bytes and may change
with new Ethos versions.

The files contain the receiver registration ID; the owner agreed to publish them.
