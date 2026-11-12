# Design system

Derived from the Tkinter code (mainly `gui/style.py`, `gui/common.py`, `gui/table_fit.py`). It documents what exists;
gaps are marked **GAP**. There is no formal design system in the code, colours are partly written inline.

## Theme and fonts
- ttk theme `clam`. Base font: the system default (`TkDefaultFont`), size 10; section titles bold 10; status and readouts 9.
- Sizes follow the line height of the font, not fixed pixels (Windows scaling up to 150 %): `table_fit.row_height()` for
  table rows, `scaled_window_size()` for window sizes.
- **GAP**: no named font scale; sizes 9 / 10 are repeated as numbers.

## Colours (`gui/style.py` unless noted)
| Role | Value | Where |
|---|---|---|
| Accent | `#1f5fa8` | selected tab, section titles, primary button, selected view button |
| Accent, hover/pressed | `#174a85`; disabled `#9fb3cc` | primary button |
| Window background | `#f4f6f9` | everything (`BG`) |
| Tab background / hover | `#dde3ec` / `#c5d3e8` | top level tabs, view buttons |
| Inner tab background / hover | `#e8edf4` / `#d5dfec` | pages inside an area |
| Border | `#c9d1dc`, tab border `#b7c2d1` | frames, tabs |
| Status bar | background `#e3e9f2`, text `#1f3b73` | `Status.TLabel` |
| Readout | white background, text `#222` | `Readout.TLabel` |
| Error / critical | `#b00020` | error texts, invalid date, critical hints |
| Warning | `#b36b00` | warnings, missing settings, possible duplicate |
| OK | `#1b7f3b` | positive tags |
| Info / note | `#1f3b73` | hint colour for notes |
| Dimmed / acknowledged / non-flight | `#888888` | list rows |
| Recorder dark face | `#24282e`, stale `#7d8590` | `recorder_dials.py`, `recorder_radio.py`, `recorder_instruments.py` |

**GAP**: only `ACCENT` and `BG` are named constants; the other values are repeated inline in several files. Charts
(matplotlib, `plots/`) use their own colours and are not covered by the table above.

## Layout and spacing
- Two levels of tabs: top level (Logbook, Statistics, Data & settings; bigger, accent when selected) and pages inside an
  area (`Pages.TNotebook`, smaller, white when selected, e.g. the statistics pages). The single flight is not a tab: it
  replaces the logbook page and returns with the button "< Logbook".
- Single flight has two tabs: *Charts* and *Flight recorder*, sharing one selection bar (back, flight, previous, next).
- Typical padding: 6 px between neighbours (`padx=(0, 6)` / `(6, 0)`), 3-4 px vertically, 10 px around headers. **GAP**:
  not defined as constants.
- Status line at the top of the window (`Status.TLabel`).

## Recurring widgets
- **Primary button** `Accent.TButton` (blue, bold white text); normal `TButton` otherwise.
- **View switch** `View.TRadiobutton` (button-like radio buttons, no indicator).
- **Sortable table**: `common.sortable_tree()` on `ttk.Treeview`, row height from the font; columns must not cut off text.
- **Multi select** with check boxes (`gui/multi_select.py`) for aircraft, year, month, shown with a summary text; shared
  filter bar (`gui/flight_filter.py`) in logbook and statistics.
- **Text report** `common.make_text()` with tags `ok`, `warn`, `bad`.
- **Scrollable frame** `common.scrollable_frame()`.
- **Charts**: matplotlib embedded; tooltip on hover, enlarge a single chart by double-click, recorder position as vertical line.
- **Recorder instruments**: canvas drawings; existing canvas items are moved (`coords`, `itemconfigure`), not recreated.

## UI principles
- All visible texts are translatable (de/en/es); text must fit at 125 % and 150 % scaling.
- Show a hint instead of an empty screen when data is missing (e.g. red hint for missing battery settings, notice on
  pages without sensor data). **GAP**: no common pattern for empty, loading and error states.
- Long work runs in the background with progress (import, preparation); the UI stays responsive.
- Diagnoses are worded as hints or estimates, never as fact. The statistics are labelled *experimental*.
- Only layouts that Tkinter/ttk can realise.
