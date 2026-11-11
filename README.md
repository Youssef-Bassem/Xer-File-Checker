# XER Schedule Checker

A small command-line tool that reads a Primavera P6 schedule export (`.xer`), flags structurally broken rows, runs three basic schedule checks, and shows one chart.

## What it does

1. **Parses** the XER file (tab-delimited `%T` table, `%F` fields, `%R` row, `%E` end markers) into pandas DataFrames.
2. **Flags broken rows** while parsing, each with a line number:
   - a data row whose value count differs from its field definition
   - a table marker with no name
   - a field definition with empty or duplicate names
   - a data row that appears before a table or field definition
3. **Runs three checks** on the `TASK` and `TASKPRED` tables:

| Check | Rule |
|---|---|
| Missing links | Activity has no predecessor or no successor (see exceptions below) |
| Negative float | `total_float_hr_cnt < 0` |
| High float | `total_float_hr_cnt > 80` hours (10 working days at 8 h/day) |

4. **Charts** the number of findings per check as a bar chart (Plotly).

### Missing links: milestone exceptions

Activities at the edge of the network are expected to have a missing link, so they are not flagged:

- **Start milestones** (`TT_Mile`) are not flagged for a missing predecessor.
- **Finish milestones** (`TT_FinMile`) are not flagged for a missing successor.

Every other activity needs both a predecessor and a successor. Each activity appears once in the results, labelled `Predecessor`, `Successor`, or `Predecessor and Successor` depending on what is missing. Relationships that point to an activity not present in the file are ignored.

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py "damac-hyde park.xer"
python main.py "shooting club tower.xer"
```

The tool prints parser issues, a summary of the three checks, the detailed findings for each check, and then opens the chart in your browser.

## Results on the included files

| File | Parser issues | Missing links | Negative float | High float (> 80 h) |
|---|---|---|---|---|
| `damac-hyde park.xer` | 0 | 15 | 0 | 46 |
| `shooting club tower.xer` | 0 | 2 | 0 | 40 |

Neither file has negative float, so that bar is empty on both charts. This is expected for these schedules, not a bug in the check.

## Data

Two public Primavera P6 schedules are included in the repo:

- `damac-hyde park.xer`: source: _add link_
- `shooting club tower.xer`: source: _add link_

## Project layout

| File | Purpose |
|---|---|
| `XerParser.py` | Reads the XER file into DataFrames and records `ParseIssue`s |
| `XerValidator.py` | The three checks |
| `XerChartGenerator.py` | The summary bar chart |
| `main.py` | Command-line entry point |

## Assumptions and limitations

- Float is read in **hours** as stored by P6 and is not converted using each activity's calendar. The 80-hour threshold is hard-coded in `validate_xer` (`high_float_threshold`). Many scheduling standards use more than 44 working days instead.
- Float checks do not skip completed activities. Both sample files contain only not-started activities, so this has no effect here.
- Only `TASK` and `TASKPRED` are used. Other tables are parsed but not checked.
- The chart is displayed, not saved to disk.
- There are no automated tests yet.
