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

## How this was built

I directed this study: the question, which hypotheses were worth testing, why the
two control groups are in the sample, and what the conclusion could honestly
claim. The Python was written with Claude, and the analysis was done in dialogue
with it, including the two methodological corrections described in the write-up.

I am not disguising that. Working with AI tools is part of how analysis gets done
now, and the part worth judging is the reasoning: the controls that made the
first hypothesis falsifiable, the decision to publish that hypothesis after it
failed, and the choice to end on an honest negative result rather than a tidy
one.

## Findings

- The English versus Traditional Chinese review gap is a genre-wide pattern, with
  a median of 18.2 points across 12 Western-developed live-service shooters.
- It is not review culture. On Chinese-developed games the gap disappears
  (Black Myth: Wukong +0.7 points, Counter-Strike 2 Simplified Chinese -3.1).
- It is not localisation. Under 0.4% of negative reviews in any language mention
  translation.
- It is not sample composition. The gap survives controlling for playtime and
  widens with it, from 14.3 points under 20 hours to 31.4 points past 500.
- It cannot be diagnosed from review text. 68 to 79% of negative reviews match no
  topic in any language, and the median Traditional Chinese negative review is 10
  characters long.

Read the full write-up at `docs/index.html`.
