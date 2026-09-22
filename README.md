# player-sentiment

A study of how Steam review scores differ by the language a review is written
in, across live-service shooters, and what that hides from a studio reading a
single global score.

Read `00_brief/project_brief.md` first.

## Running it

Needs Python 3. No packages to install, standard library only.

```powershell
cd "D:\Portfolio Project\player-sentiment\02_code"

py collect_baseline.py     # 14 games x 7 languages, review summaries
py collect_reviews.py      # full Apex Legends review pull, per language
py analyse_apex.py         # every figure in the write-up
py build_pages.py          # rebuilds docs/index.html from 04_writeup/
```

`build_pages.py` exists because the two copies of the write-up need different
shapes. `04_writeup/index.html` is authored as a fragment for a host that
supplies its own document skeleton. `docs/index.html` is served directly, so it
needs a real `<head>` with Open Graph tags, or LinkedIn and Slack show a bare
URL with no preview. Run it after editing the write-up.

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
two control groups are in the sample, and what the conclusion of the study could
claim honestly. The Python was written with the help of AI, and the analysis was
done in dialogue with it, including the two methodological corrections described
in the write-up.

Working with AI tools is now part of how analysis gets done, and the
part worth judging is the reasoning: the controls that made the first hypothesis
falsifiable, the decision to publish that hypothesis after it failed, and the
choice to end on an honest negative result rather than a tidy one.

## Findings

Based on 218,380 Apex Legends reviews plus summary data for 14 games in 7
languages. All comparisons use the window all five languages cover
(July 2024 to September 2026) with the July 2024 review bomb removed.

- **Not review culture.** On Chinese-developed games the English versus
  Traditional Chinese gap disappears (Black Myth: Wukong +0.7 points,
  Counter-Strike 2 Simplified Chinese -3.1). Across 12 Western live-service
  shooters the median gap is 18.2 points.
- **Not localisation.** Under 0.1% of negative reviews in any language mention
  translation.
- **A review bomb was faking one of the gaps.** July 2024 spiked every language
  at once, hardest in Simplified Chinese at 14.9x normal volume and 9% positive.
  Removing it drops the Simplified Chinese gap from 20.8 points to 4.1, and
  inverts Korean from 3.3 to -0.9.
- **Two gaps survive.** Traditional Chinese at 23.1 points and Japanese at 18.1.
- **Not sample composition.** Holding playtime constant, the Traditional Chinese
  gap runs +9.6 under 20 hours to +25.4 between 100 and 500. Japanese starts at
  +1.1, not distinguishable from zero, and reaches +20.0 past 500 hours: a clean
  late-souring curve.
- **It cannot be diagnosed from review text.** 73 to 77% of negative reviews
  match no topic in any language, and the median Traditional Chinese negative
  review is 10 characters long against 53 for English.

The same question answered four ways, depending on how the window is handled:
31.9 points with no control, 2.2 with a 5-month shared window, 20.8 with a
2-year one, 4.1 once the review bomb comes out. The window has to be justified,
not just applied.

Read the full write-up at `docs/index.html`, or live at
https://jozxo.github.io/player-sentiment/
