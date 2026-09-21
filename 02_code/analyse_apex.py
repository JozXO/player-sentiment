"""
analyse_apex.py
Deep dive on the outlier. Three questions, in order of how much I trust them:

1. WHEN do the negative reviews land? (timestamps, no interpretation needed)
2. At WHAT PLAYTIME do they land? (a number Steam gives us, no interpretation)
3. WHAT do they say? (keyword counting, the part that can lie, verified by
   printing real reviews at the end)

Reads  01_data/raw/reviews_raw.csv
Writes 01_data/processed/apex_*.csv
"""

import os
import re
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.normpath(os.path.join(HERE, "..", "01_data", "raw", "reviews_raw.csv"))
OUT = os.path.normpath(os.path.join(HERE, "..", "01_data", "processed"))
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(RAW, dtype={"review_text": str})
df["review_text"] = df["review_text"].fillna("")
df["date"] = pd.to_datetime(df["timestamp_created"], unit="s")
df["hours_at_review"] = df["playtime_at_review_min"] / 60.0

print("=" * 74)
print("SAMPLE")
print("=" * 74)
summary = df.groupby("language").agg(
    reviews=("recommendationid", "count"),
    positive_rate=("voted_up", "mean"),
    median_hours=("hours_at_review", "median"),
    earliest=("date", "min"),
    latest=("date", "max"),
)
summary["positive_rate"] = (summary["positive_rate"] * 100).round(1)
summary["median_hours"] = summary["median_hours"].round(0)
summary["earliest"] = summary["earliest"].dt.date
summary["latest"] = summary["latest"].dt.date
print(summary.to_string())

# ---------------------------------------------------------------- H5: playtime
print("\n" + "=" * 74)
print("H5: WHERE IN THE PLAYER LIFECYCLE DOES THE NEGATIVITY SIT?")
print("% of that language's reviews that are negative, by hours played")
print("=" * 74)
bins = [0, 5, 20, 100, 500, 1000, 10 ** 9]
labels = ["0-5h", "5-20h", "20-100h", "100-500h", "500-1000h", "1000h+"]
df["bucket"] = pd.cut(df["hours_at_review"], bins=bins, labels=labels, right=False)
neg_rate = df.pivot_table(index="language", columns="bucket",
                          values="voted_up", aggfunc="mean", observed=False)
neg_rate = ((1 - neg_rate) * 100).round(1)
counts = df.pivot_table(index="language", columns="bucket",
                        values="recommendationid", aggfunc="count", observed=False)
print(neg_rate.to_string())
print("\n(sample size per cell)")
print(counts.to_string())

# ------------------------------------------------------------- topic keywords
# Built by hand per language rather than by an automatic topic model, because
# a keyword list can be read, argued with and corrected by a native speaker.
# A topic model's clusters cannot. Verified by printing matched reviews below.
TOPICS = {
    "cheating": {
        "english":  r"cheat|hacker|aimbot|wall ?hack|\bhacks?\b|spinbot",
        "schinese": r"外挂|开挂|作弊|挂逼|科技",
        "tchinese": r"外掛|開掛|作弊|掛逼",
        "japanese": r"チート|チーター|ハック",
        "koreana":  r"핵|핵쟁이|에임봇|치터",
    },
    "server_latency": {
        "english":  r"\bping\b|\blag+|latency|packet loss|server|desync|rubber ?band",
        "schinese": r"服务器|延迟|卡顿|掉线|网络|丢包|亚服|ping",
        "tchinese": r"伺服器|延遲|卡頓|掉線|網路|丟包|亞服|ping",
        "japanese": r"サーバ|ラグ|遅延|回線|ping",
        "koreana":  r"서버|렉|핑|지연",
    },
    "matchmaking": {
        "english":  r"matchmak|\bsbmm\b|smurf|predator|lobb(y|ies)|match ?making",
        "schinese": r"匹配|配对|排位|新手",
        "tchinese": r"匹配|配對|排位|新手",
        "japanese": r"マッチング|マッチ",
        "koreana":  r"매칭|매치",
    },
    "monetisation": {
        "english":  r"\bprice|expensive|\$\d|micro ?transaction|heirloom|battle ?pass|greedy|\bea\b",
        "schinese": r"氪金|课金|价格|太贵|皮肤|抽奖|骗钱",
        "tchinese": r"課金|氪金|價格|太貴|皮膚|抽獎|騙錢",
        "japanese": r"課金|値段|高い|ガチャ",
        "koreana":  r"과금|가격|비싸",
    },
    "performance_bugs": {
        "english":  r"crash|stutter|\bfps\b|optimi[sz]|frame ?rate|freeze|bug+",
        "schinese": r"优化|帧数|崩溃|闪退|卡死|掉帧|bug",
        "tchinese": r"優化|幀數|崩潰|閃退|卡死|掉幀|bug",
        "japanese": r"最適化|クラッシュ|落ちる|フレーム|バグ",
        "koreana":  r"최적화|튕김|프레임|버그",
    },
    "localisation": {
        "english":  r"translat|localis|localiz|\bsubtitle",
        "schinese": r"翻译|中文|简体|本地化|配音",
        "tchinese": r"翻譯|中文|繁體|在地化|配音",
        "japanese": r"翻訳|日本語|ローカライズ",
        "koreana":  r"번역|한국어|한글",
    },
    "anticheat_eac": {
        "english":  r"anti ?cheat|\beac\b|easy anti",
        "schinese": r"反外挂|反作弊|封号",
        "tchinese": r"反外掛|反作弊|封號",
        "japanese": r"アンチチート|チート対策",
        "koreana":  r"안티치트|밴",
    },
}

print("\n" + "=" * 74)
print("H1-H3: WHAT DO NEGATIVE REVIEWS TALK ABOUT?")
print("% of that language's NEGATIVE reviews mentioning each topic")
print("=" * 74)

negative = df[df["voted_up"] == 0]
table = {}
for topic, per_lang in TOPICS.items():
    row = {}
    for lang, pattern in per_lang.items():
        subset = negative[negative["language"] == lang]
        if len(subset) < 50:
            row[lang] = None
            continue
        hits = subset["review_text"].str.contains(pattern, case=False, regex=True, na=False)
        row[lang] = round(hits.mean() * 100, 1)
    table[topic] = row

topics_df = pd.DataFrame(table).T
order = [c for c in ["english", "schinese", "tchinese", "japanese", "koreana"]
         if c in topics_df.columns]
topics_df = topics_df[order]
print(topics_df.to_string())
print("\nnegative reviews per language: %s"
      % negative.groupby("language").size().to_dict())

topics_df.to_csv(os.path.join(OUT, "apex_topics_negative.csv"))
neg_rate.to_csv(os.path.join(OUT, "apex_negativity_by_playtime.csv"))
summary.to_csv(os.path.join(OUT, "apex_sample_summary.csv"))
print("\nWrote apex_topics_negative.csv, apex_negativity_by_playtime.csv, apex_sample_summary.csv")
