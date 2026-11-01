# Example Ethos model files

Model files (`.bin`) copied from the `models` folder of an FrSky Ethos transmitter.
They are test data for the planned model plan feature (parser for Ethos model files).

| File | Model | Format version | Notes |
|------|-------|----------------|-------|
| `model01.bin` | Viper Jet | 0x23 (new format) | 15 mixes, 17 channels, 8 curves, 3 flight modes; checked against the transmitter |

The Ethos model file format is not officially documented by FrSky. Everything the
app reads from these files was reverse-engineered from the bytes and may change
with new Ethos versions.

The files contain the receiver registration ID; the owner agreed to publish them.
