# Example Ethos model files

Model files (`.bin`) copied from the `models` folder of an FrSky Ethos transmitter.
They are test data for the planned model plan feature (parser for Ethos model files).

| File | Model | Format version | Notes |
|------|-------|----------------|-------|
| `model01.bin` | Viper Jet | 0x23 (new format) | 15 mixes, 17 channels, 8 curves, 3 flight modes; checked against the transmitter |
| `avanti_s_v2.bin` | Avanti S V2 | header byte 7 is 0x23 like the Viper Jet | 2431 bytes; not checked against the transmitter. The earlier analysis described a 3020-byte file in the old format (0x0B), so this may be a different export. To be checked by the parser package. |

The Ethos model file format is not officially documented by FrSky. Everything the
app reads from these files was reverse-engineered from the bytes and may change
with new Ethos versions.

The files contain the receiver registration ID; the owner agreed to publish them.
