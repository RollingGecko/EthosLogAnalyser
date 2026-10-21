# Translations

The user interface, the text reports, the charts and the exports are available in German, English and Spanish.

## How it works

The source language of all user-facing texts is **German**. In the code every such text is written in German and passed through one of three functions from `ethosloganalyser/i18n.py`:

| Function | Use |
|---|---|
| `tr("Text {x}", x=...)` | translates immediately into the current language and fills in the placeholders. Use it wherever text is put on the screen, into a chart or into a report. |
| `N_("Text")` | only marks a string for translation (for constants and label tables at module level). Translate it later with `tr(text)` or `config.label(table, code)`. |
| `Msg("Text {x}", x=...)` | a message that is translated only when it is shown (`str(msg)`). The analysis stores `Msg` objects (warnings, reasons for skipped files), so a result can be shown in another language without analysing the logs again. |

The translations are plain Python dictionaries in `ethosloganalyser/locales/en.py` and `locales/es.py`:

```python
CATALOG = {
    "Zusammenfassung": "Summary",
    "zu kurz ({dur:.0f} s < {min:.0f} s)": "too short ({dur:.0f} s < {min:.0f} s)",
}
```

The key is the German text exactly as it appears in the code, the value is the translation. Placeholders such as `{dur:.0f}` must appear in the translation with the same names; their order may change. A missing translation falls back to the German text.

Analysis results do not contain user-facing text. Values that are shown to the user are stored as codes and translated through label tables, e.g. spike causes (`config.SPIKE_LABELS`), flags (`analysis.evaluate.FLAG_LABELS`) or the views of the single flight tab (`plots.flight.VIEW_LABELS`).

## Changing or adding a text

1. Write the German text in the code with `tr()`, `N_()` or `Msg()`. The first argument must be a string literal, otherwise the tests cannot find it.
2. Add the translation to every catalog in `locales/`.
3. Run `python -m pytest tests/test_i18n.py`. The tests list every text without translation, every translation that is no longer used and every translation whose placeholders differ from the German text.

To correct a translation, change only the value in the catalog.

## Adding a language

1. Copy `locales/en.py` to `locales/<code>.py` (e.g. `fr.py`) and translate the values.
2. In `i18n.py`, import the module and add it to `LANGUAGES` (code → name of the language in that language) and `CATALOGS`. Add the language to `detect_language()` if the app should start in it automatically.
3. Run the tests; they check the new catalog automatically.

The date formats are part of the catalogs (keys `"%d.%m.%Y"` and `"%d.%m.%Y %H:%M"`).
