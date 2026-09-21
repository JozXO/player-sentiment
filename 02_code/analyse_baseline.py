"""
analyse_baseline.py
Separates the two things hiding inside the English vs non-English review gap:
a baseline offset that applies to every game, and the excess that belongs to
a specific game.

Reads  01_data/raw/baseline_summaries.csv
Writes 01_data/processed/gaps_by_game.csv
"""

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.normpath(os.path.join(HERE, "..", "01_data", "raw", "baseline_summaries.csv"))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "01_data", "processed"))
os.makedirs(OUT_DIR, exist_ok=True)

ASIAN_DEVELOPED = {"NARAKA BLADEPOINT", "Black Myth Wukong"}
COMPARE = ["tchinese", "schinese", "japanese", "koreana", "russian"]
# a language needs this many reviews on a game before its rate means anything
MIN_REVIEWS = 200

df = pd.read_csv(RAW)
df = df[df["total_reviews"] > 0].copy()
df["positive_rate"] = df["total_positive"] / df["total_reviews"]

wide = df.pivot_table(index="game_name_expected", columns="language",
                      values="positive_rate")
counts = df.pivot_table(index="game_name_expected", columns="language",
                        values="total_reviews")

rows = []
for game in wide.index:
    english = wide.loc[game, "english"]
    row = {"game": game,
           "asian_developed": game in ASIAN_DEVELOPED,
           "english_rate": english,
           "english_n": int(counts.loc[game, "english"])}
    for lang in COMPARE:
        rate = wide.loc[game, lang] if lang in wide.columns else None
        n = counts.loc[game, lang] if lang in counts.columns else 0
        n = 0 if pd.isna(n) else int(n)
        row[lang + "_n"] = n
        if pd.isna(rate) or n < MIN_REVIEWS:
            row[lang + "_rate"] = None
            row[lang + "_gap"] = None
        else:
            row[lang + "_rate"] = rate
            # positive number means that language rates the game LOWER
            row[lang + "_gap"] = (english - rate) * 100
    rows.append(row)

gaps = pd.DataFrame(rows).set_index("game")

western = gaps[~gaps["asian_developed"]]
asian = gaps[gaps["asian_developed"]]

pd.set_option("display.width", 200)

print("=" * 78)
print("GAP IN PERCENTAGE POINTS (positive number = that language rates it LOWER)")
print("=" * 78)
display = gaps[["english_rate"] + [l + "_gap" for l in COMPARE]].copy()
display["english_rate"] = (display["english_rate"] * 100).round(1)
for lang in COMPARE:
    display[lang + "_gap"] = display[lang + "_gap"].round(1)
display.columns = ["EN %"] + [l[:4].upper() for l in COMPARE]
print(display.sort_values("TCHI", ascending=False).to_string())

print("\n" + "=" * 78)
print("BASELINE: median gap across the 12 Western-developed games")
print("=" * 78)
for lang in COMPARE:
    series = western[lang + "_gap"].dropna()
    if len(series):
        print("  %-9s median %6.1f pts   range %5.1f to %5.1f   (n=%d games)"
              % (lang, series.median(), series.min(), series.max(), len(series)))

print("\n" + "=" * 78)
print("CONTROL GROUP: Asian-developed games")
print("=" * 78)
for game in asian.index:
    parts = []
    for lang in COMPARE:
        gap = asian.loc[game, lang + "_gap"]
        if pd.notna(gap):
            parts.append("%s %+.1f" % (lang[:4], gap))
    print("  %-22s EN %.1f%%   %s"
          % (game, asian.loc[game, "english_rate"] * 100, "   ".join(parts)))

print("\n" + "=" * 78)
print("EXCESS ABOVE BASELINE (gap minus the Western median for that language)")
print("Positive = this game is worse for that language than the genre norm")
print("=" * 78)
excess = pd.DataFrame(index=western.index)
for lang in COMPARE:
    median = western[lang + "_gap"].dropna().median()
    excess[lang[:4].upper()] = (western[lang + "_gap"] - median).round(1)
excess["MEAN"] = excess.mean(axis=1, numeric_only=True).round(1)
print(excess.sort_values("MEAN", ascending=False).to_string())

gaps.to_csv(os.path.join(OUT_DIR, "gaps_by_game.csv"))
excess.to_csv(os.path.join(OUT_DIR, "excess_above_baseline.csv"))
print("\nWrote gaps_by_game.csv and excess_above_baseline.csv")
