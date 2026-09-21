# player-sentiment

A study of how Steam review scores differ by the language a review is written
in, across live-service shooters, and what that hides from a studio reading a
single global score.

Read `00_brief/project_brief.md` first.

## Running it

Needs Python 3. No packages to install, standard library only.

```powershell
cd "D:\Portfolio Project\player-sentiment\02_code"

py collect_baseline.py     # ~2 minutes, 14 games x 7 languages
py collect_reviews.py      # ~15 minutes, full Apex Legends review pull
```

Both write into `01_data/raw/`. Both are safe to stop with Ctrl+C and re-run:
`collect_reviews.py` skips anything already on disk.

## Layout

| Folder | Holds |
|---|---|
| `00_brief/` | The question, the hypotheses, the method, the limits |
| `01_data/raw/` | Untouched API output, never edited by hand |
| `01_data/processed/` | Cleaned tables the charts are built from |
| `02_code/` | Collection and analysis scripts |
| `03_charts/` | Exported figures |
| `04_writeup/` | The case study text |

Raw data stays raw. Every transformation happens in code in `02_code/` so the
whole chain from API response to published chart can be re-run and checked.
