# The language gap: what a single global review score hides

Josiah Francis, September 2026

## The observation

Steam tags every user review with the language it was written in. Pulling the
review summary one language at a time, for three live-service shooters:

| Game | English | Traditional Chinese | Gap |
|---|---|---|---|
| Apex Legends | 76.6% positive | 40.1% positive | 36.5 pts |
| THE FINALS | 80.5% positive | 57.4% positive | 23.1 pts |
| Marvel Rivals | 76.6% positive | 54.5% positive | 22.1 pts |

Figures pulled 21 September 2026 from the public Steam review API.

## The hypothesis that failed, and why that matters

The study started as "Traditional Chinese players dislike The Finals". The
control test killed it in ten minutes: the gap is in all three games, so it is
not a property of The Finals.

That failure is kept in the write-up rather than edited out. It is the reason
the real finding is trustworthy.

## The question the study actually answers

There are two things inside that gap and they need separating:

1. **A baseline offset.** If English and Traditional Chinese reviewers rate
   every game roughly 22 points apart, that is a property of the review
   population, not of any game. No studio can fix it and no studio should try.
2. **A game-specific excess.** Apex Legends sits roughly 14 points below even
   that baseline. That part is not review culture. Something is happening to
   those players that is not happening to Marvel Rivals players.

**The question: how big is the baseline, and what explains Apex Legends
falling so far below it?**

## Why it matters commercially

A studio looking at one global score sees Apex at "Mixed, 76%" and treats it as
a broadly healthy game. Split by language and 35,000 Traditional Chinese
reviewers are at 40% positive, which is catastrophic, and invisible at the
aggregate level. If the cause is regional (latency, matchmaking pools,
localisation, cheating, pricing) it is fixable, and it is fixable by teams who
are currently not being shown the problem.

## Hypotheses

| # | Hypothesis | What would support it | What would kill it |
|---|---|---|---|
| H1 | Regional infrastructure: latency, server coverage, matchmaking pools | Negative reviews cluster on connection and matchmaking language; complaints spike after region-affecting patches | Complaints spread evenly across topics |
| H2 | Localisation quality: translated text is poor, so the game reads worse | Complaints name text, UI, translation, voice work | Localisation is barely mentioned |
| H3 | Cheating prevalence differs by region | Cheat and anti-cheat terms dominate in specific languages | Cheat mentions are proportionate across all languages |
| H4 | Review culture: some player communities review more harshly on Steam | The gap appears consistently across unrelated games | The gap is specific to certain games |
| H5 | Retention shape: low-rating languages bounce early rather than souring late | Negative reviews sit at low playtime_at_review | Negative reviews come from high-hour players |

H4 is now partly confirmed, which is why the study measures the baseline first
and treats only the excess above it as a finding.

## Controls

The baseline sample deliberately includes two control groups, because without
them H4 cannot be separated from H1 to H3:

- **Asian-developed games** (NARAKA BLADEPOINT, Black Myth Wukong). If the gap
  inverts here, Traditional Chinese reviewers are not simply harsher and the
  gap is about the games, not the reviewers.
- **Older Western live-service** (Team Fortress 2, Warframe). Tests whether the
  gap is recent or has always existed.

## Method

1. **Baseline.** Summary pull for 14 games across 7 languages. Establishes the
   size and consistency of the gap, and validates every app id against Steam so
   a mistyped id cannot poison the study.
2. **Deep dive collection.** Full review pull for Apex Legends per language,
   keeping text, timestamp, thumbs up or down, and playtime at review.
3. **Describe.** Positive rate by language over time, mapped against Apex
   season and patch dates.
4. **Read the text.** Extract what each language group complains about, then
   sample and read real reviews to check the extraction is not lying.
5. **Segment by playtime.** Split negative reviews into early bounce and late
   souring, per language. This is the H5 test and the most useful output for a
   live ops team.
6. **Conclude.** State what the data supports, what it only suggests, and what
   it cannot show.

## What this data honestly cannot do

Stated up front, because a study that hides its limits is worth less than one
that names them.

- Steam reviewers are not the playerbase. They skew toward strong opinions.
- Language is a proxy for region, not a measurement of it. A Taiwanese player
  writing in English is counted as English.
- Console players are entirely absent. Steam only.
- Review timestamps show when someone wrote, not when they played or quit.
- Correlation with patch dates is not proof a patch caused anything.
- Review bombing is a real confound and has to be looked for, not assumed away.

## Deliverable

A single web page: finding first, charts second, method and code below. Linked
from CV and LinkedIn, with code and data published alongside so anyone can
check the work.
