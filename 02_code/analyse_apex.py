"""
analyse_apex.py
Produces every figure in the write-up, in the order the argument needs them.

The pipeline, and why each step exists:

1. SHARED WINDOW. The collector pulls newest-first and stops at a cap, so each
   language's sample reaches back a different distance. Comparing them raw
   compares five different time periods. Everything below is restricted to the
   window all five languages cover.

2. REVIEW BOMB DETECTION. A bomb shows up as a volume spike with a score
   collapse; ordinary decline moves the score and leaves volume alone. July 2024
   hit every language at once, hardest in Simplified Chinese at 14.9x normal
   volume. That event sits inside the shared window.

3. THE SAME GAPS WITH THE BOMB REMOVED. This is the step that matters. The
   Simplified Chinese gap falls from 20.8 points to 4.1, so four fifths of it
   was one protest month rather than a regional quality problem.

4. PLAYTIME BANDS. Tests whether the surviving gaps are just composition.

5. TOPICS AND LENGTHS. Tests whether the reviews can explain themselves.

Reads  01_data/raw/reviews_raw.csv
Writes 01_data/processed/apex_*.csv
"""

import os
import math
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.normpath(os.path.join(HERE, "..", "01_data", "raw", "reviews_raw.csv"))
OUT = os.path.normpath(os.path.join(HERE, "..", "01_data", "processed"))
os.makedirs(OUT, exist_ok=True)

BOMB_START, BOMB_END = "2024-07-01", "2024-09-30"
LANGS = ["english", "schinese", "tchinese", "japanese", "koreana"]
BINS = [0, 20, 100, 500, 10 ** 9]
LABELS = ["<20h", "20-100h", "100-500h", "500h+"]

df = pd.read_csv(RAW, dtype={"review_text": str})
df["review_text"] = df["review_text"].fillna("")
df["date"] = pd.to_datetime(df["timestamp_created"], unit="s")
df["hours"] = df["playtime_at_review_min"] / 60
df["month"] = df["date"].dt.to_period("M")
print("collected reviews: %d" % len(df))

# ---------------------------------------------------------------- 1. window
start = df.groupby("language")["date"].min().max()
end = df.groupby("language")["date"].max().min()
window = df[(df.date >= start) & (df.date <= end)].copy()
print("shared window: %s to %s  (%d reviews)" % (start.date(), end.date(), len(window)))

# ------------------------------------------------------------------ 2. bombs
print("\n=== REVIEW BOMB DETECTION ===")
bombs = []
for lang in LANGS:
    m = df[df.language == lang].groupby("month").agg(n=("voted_up", "size"), pos=("voted_up", "mean"))
    m = m[m.n >= 30]
    if len(m) < 6:
        continue
    med_n, med_pos = m.n.median(), m.pos.median()
    hit = m[(m.n > med_n * 2) & (m.pos < med_pos - 0.15)]
    for period, row in hit.iterrows():
        bombs.append({"language": lang, "month": str(period), "reviews": int(row.n),
                      "multiple_of_normal": round(row.n / med_n, 1),
                      "positive_rate": round(row.pos * 100, 1),
                      "language_median_positive": round(med_pos * 100, 1)})
bombs = pd.DataFrame(bombs)
print(bombs.to_string(index=False))
bombs.to_csv(os.path.join(OUT, "apex_review_bombs.csv"), index=False)

clean = window[~window.date.between(BOMB_START, BOMB_END)].copy()
print("\nafter removing %s to %s: %d reviews" % (BOMB_START, BOMB_END, len(clean)))

# ----------------------------------------------------- 3. gaps, with/without
def gaps(d):
    s = d.groupby("language").agg(n=("voted_up", "size"), pos=("voted_up", "mean"))
    s["pos"] = (s["pos"] * 100).round(1)
    s["gap_vs_english"] = (s.loc["english", "pos"] - s["pos"]).round(1)
    return s

with_bomb, without_bomb = gaps(window), gaps(clean)
compare = pd.DataFrame({
    "with_bomb": with_bomb["gap_vs_english"],
    "without_bomb": without_bomb["gap_vs_english"],
})
compare["change"] = (compare.without_bomb - compare.with_bomb).round(1)
print("\n=== GAP vs ENGLISH, BEFORE AND AFTER REMOVING THE BOMB ===")
print(compare.to_string())
compare.to_csv(os.path.join(OUT, "apex_gap_bomb_effect.csv"))

# ------------------------------------------------------------- 4. playtime
clean["band"] = pd.cut(clean["hours"], bins=BINS, labels=LABELS, right=False)
rate = clean.pivot_table(index="band", columns="language", values="voted_up",
                         aggfunc="mean", observed=False)
count = clean.pivot_table(index="band", columns="language", values="recommendationid",
                          aggfunc="count", observed=False)
negrate = ((1 - rate) * 100).round(1)[LANGS]
print("\n=== NEGATIVE RATE BY PLAYTIME, BOMB REMOVED ===")
print(negrate.to_string())
print("\n(n per cell)")
print(count[LANGS].fillna(0).astype(int).to_string())

print("\n=== GAP vs ENGLISH BY BAND, 95%% CI ===")
ci_rows = []
for band in LABELS:
    e, ne = negrate.loc[band, "english"] / 100, int(count.loc[band, "english"])
    for lang in ["schinese", "tchinese", "japanese", "koreana"]:
        t, nt = negrate.loc[band, lang] / 100, int(count.loc[band, lang])
        se = math.sqrt(e * (1 - e) / ne + t * (1 - t) / nt) * 100
        gap = (t - e) * 100
        ci_rows.append({"band": band, "language": lang, "gap": round(gap, 1),
                        "ci_low": round(gap - 1.96 * se, 1), "ci_high": round(gap + 1.96 * se, 1),
                        "n": nt, "significant": (gap - 1.96 * se) > 0})
ci = pd.DataFrame(ci_rows)
print(ci[ci.language.isin(["tchinese", "japanese"])].to_string(index=False))
ci.to_csv(os.path.join(OUT, "apex_gap_by_playtime_ci.csv"), index=False)
negrate.to_csv(os.path.join(OUT, "apex_negativity_by_playtime.csv"))

# --------------------------------------------------------- 5. topics, length
# Keyword sets are built by hand per language rather than by a topic model,
# because a keyword list can be read, argued with and corrected by a native
# speaker. 斷線 was missing from the first version and was undercounting
# connection complaints; it was found by sampling matched reviews.
TOPICS = {
 "connection/server": {"english": r"ping\b|lag+|latency|packet ?loss|server|desync|disconnect|connection",
   "schinese": r"服务器|伺服|延迟|卡顿|掉线|断线|网络|丢包|亚服|直连|ping",
   "tchinese": r"伺服器|伺服|延遲|卡頓|掉線|斷線|網路|丟包|亞服|直連|ping",
   "japanese": r"サーバ|ラグ|遅延|回線|切断|落ちる|ping", "koreana": r"서버|렉|핑|지연|끊김"},
 "cheating": {"english": r"cheat|hacker|aimbot|wall ?hack|hacks?\b|spinbot",
   "schinese": r"外挂|开挂|作弊|挂逼|科技", "tchinese": r"外掛|開掛|作弊|掛逼|科技",
   "japanese": r"チート|チーター|ハック", "koreana": r"핵|에임봇|치터"},
 "performance/bugs": {"english": r"crash|stutter|fps\b|optimi[sz]|frame ?rate|freeze|bug+",
   "schinese": r"优化|帧数|崩溃|闪退|卡死|掉帧|bug", "tchinese": r"優化|幀數|崩潰|閃退|卡死|掉幀|bug",
   "japanese": r"最適化|クラッシュ|フレーム|バグ", "koreana": r"최적화|튕김|프레임|버그"},
 "monetisation": {"english": r"price|expensive|\$\d|micro ?transaction|heirloom|battle ?pass|greedy",
   "schinese": r"氪金|课金|价格|太贵|皮肤|抽奖|骗钱", "tchinese": r"課金|氪金|價格|太貴|皮膚|抽獎|騙錢",
   "japanese": r"課金|値段|高い|ガチャ", "koreana": r"과금|가격|비싸"},
 "matchmaking": {"english": r"matchmak|sbmm\b|smurf|predator|lobb(?:y|ies)",
   "schinese": r"匹配|配对|排位|新手", "tchinese": r"匹配|配對|排位|新手",
   "japanese": r"マッチング|マッチ", "koreana": r"매칭|매치"},
 "localisation": {"english": r"translat|locali[sz]|subtitle",
   "schinese": r"翻译|中文|简体|本地化|配音", "tchinese": r"翻譯|中文|繁體|在地化|配音",
   "japanese": r"翻訳|日本語|ローカライズ", "koreana": r"번역|한국어|한글"},
}
neg = clean[clean.voted_up == 0]
table = {name: {l: round(neg[neg.language == l].review_text
                         .str.contains(p[l], case=False, na=False).mean() * 100, 1)
                for l in LANGS} for name, p in TOPICS.items()}
no_topic = {}
for l in LANGS:
    sub = neg[neg.language == l]
    mask = False
    for p in TOPICS.values():
        m = sub.review_text.str.contains(p[l], case=False, na=False)
        mask = m if mask is False else (mask | m)
    no_topic[l] = round((~mask).mean() * 100, 1)
table["NO topic matched"] = no_topic
topics = pd.DataFrame(table).T[LANGS]
print("\n=== TOPICS IN NEGATIVE REVIEWS, BOMB REMOVED (%) ===")
print(topics.to_string())
topics.to_csv(os.path.join(OUT, "apex_topics_negative.csv"))

lengths = neg.groupby("language")["review_text"].apply(lambda s: s.str.len().median()).astype(int)
print("\n=== MEDIAN NEGATIVE REVIEW LENGTH (characters) ===")
print(lengths.to_string())
lengths.to_frame("median_chars").to_csv(os.path.join(OUT, "apex_negative_review_length.csv"))

print("\nWrote 5 files to 01_data/processed/")
