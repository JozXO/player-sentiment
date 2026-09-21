"""
collect_baseline.py
Pulls the headline review summary for a list of games, broken down by the
language each review was written in, and writes one tidy CSV.

This is the backbone of the study. Before reading a single review we need to
know whether the English vs Traditional Chinese gap is a property of one game
or a property of the Steam review population. That is what this measures.

Two control groups are deliberately included:

  - Asian-developed games (Naraka Bladepoint, Black Myth Wukong). If the gap
    inverts for these, then Traditional Chinese reviewers are not simply
    harsher, and the gap is telling us something about the games instead.
  - Older Western live-service shooters (Team Fortress 2, Warframe). These
    test whether the gap is a recent phenomenon or has always been there.

Without those controls the study cannot separate "reviewer culture" from
"regional player experience", and that distinction is the entire point.

Run it:
    py collect_baseline.py
"""

import csv
import json
import os
import time
import urllib.parse
import urllib.request

GAMES = {
    # live-service shooters, the core sample
    1172470: "Apex Legends",
    2073850: "THE FINALS",
    2767030: "Marvel Rivals",
    730:     "Counter-Strike 2",
    1085660: "Destiny 2",
    2357570: "Overwatch 2",
    578080:  "PUBG BATTLEGROUNDS",
    359550:  "Rainbow Six Siege",
    2507950: "Delta Force",
    2074920: "THE FIRST DESCENDANT",
    # older live-service, tests whether the gap is new
    440:     "Team Fortress 2",
    230410:  "Warframe",
    # Asian-developed control group
    1203220: "NARAKA BLADEPOINT",
    2358720: "Black Myth Wukong",
}

LANGUAGES = ["all", "english", "schinese", "tchinese", "japanese", "koreana", "russian"]

DELAY_SECONDS = 1.0

FIELDS = [
    "app_id", "game_name_expected", "game_name_confirmed", "language",
    "total_reviews", "total_positive", "total_negative",
    "positive_rate", "review_score", "review_score_desc",
]


def confirm_name(app_id):
    """
    Ask Steam what this app id actually is.

    An app id typed from memory is the easiest way to quietly poison a whole
    study, so the script checks every id against Steam and writes both the
    name we expected and the name Steam returned. If those two disagree in
    the output CSV, the row is wrong and we can see it immediately.
    """
    url = ("https://store.steampowered.com/api/appdetails?appids=%d&filters=basic"
           % app_id)
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-study/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        entry = payload.get(str(app_id), {})
        if entry.get("success"):
            return entry.get("data", {}).get("name", "UNKNOWN")
        return "LOOKUP_FAILED"
    except Exception as error:
        return "LOOKUP_ERROR: %s" % error


def fetch_summary(app_id, language):
    """
    One summary request. num_per_page=1 because we only want query_summary,
    not the reviews themselves, and asking for fewer rows is the polite way
    to ask a question of someone else's server.
    """
    params = {
        "json": 1,
        "language": language,
        "filter": "all",
        "purchase_type": "all",
        "num_per_page": 1,
    }
    url = ("https://store.steampowered.com/appreviews/%d?%s"
           % (app_id, urllib.parse.urlencode(params)))
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-study/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("query_summary", {})


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.normpath(
        os.path.join(here, "..", "01_data", "raw", "baseline_summaries.csv"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    rows = []
    for app_id, expected_name in GAMES.items():
        confirmed = confirm_name(app_id)
        flag = "" if confirmed.lower().startswith(expected_name.lower()[:6]) else "   <-- CHECK THIS"
        print("\n%d  expected '%s'  Steam says '%s'%s"
              % (app_id, expected_name, confirmed, flag))
        time.sleep(DELAY_SECONDS)

        for language in LANGUAGES:
            try:
                summary = fetch_summary(app_id, language)
            except Exception as error:
                print("   %-10s FAILED: %s" % (language, error))
                time.sleep(3)
                continue

            total = summary.get("total_reviews") or 0
            positive = summary.get("total_positive") or 0
            negative = summary.get("total_negative") or 0
            rate = round(positive / total, 4) if total else ""

            rows.append({
                "app_id": app_id,
                "game_name_expected": expected_name,
                "game_name_confirmed": confirmed,
                "language": language,
                "total_reviews": total,
                "total_positive": positive,
                "total_negative": negative,
                "positive_rate": rate,
                "review_score": summary.get("review_score"),
                "review_score_desc": summary.get("review_score_desc"),
            })
            pct = ("%.1f%%" % (rate * 100)) if rate != "" else "n/a"
            print("   %-10s %8d reviews   %s" % (language, total, pct))
            time.sleep(DELAY_SECONDS)

    with open(out_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print("\nWrote %d rows to %s" % (len(rows), out_path))
    print("Check the game_name_confirmed column before trusting anything.")


if __name__ == "__main__":
    main()
