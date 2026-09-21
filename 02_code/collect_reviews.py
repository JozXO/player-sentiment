"""
collect_reviews.py
Pulls Steam user reviews for one game, one language at a time, into a CSV.

Why it is written this way:

1. Standard library only (urllib, json, csv, time). No pip install, so it runs
   on any machine with Python 3 and cannot break because a package moved.

2. filter=recent, not filter=all. "all" ranks by helpfulness and the cursor
   stops paginating after a few thousand rows. "recent" is strict reverse
   chronological order, so the cursor walks the whole history without
   repeating or stalling.

3. One language per pass. Steam tags every review with the language it was
   written in. Looping per language is what makes the comparison possible,
   and it lets us cap each language separately instead of drowning in English.

4. playtime_at_review is captured. This is the field most people ignore and
   it is the whole analysis: a negative review at 4 hours is a bad first
   impression, a negative review at 900 hours is a live ops failure. Very
   different problems, very different fixes.

5. Resumable and deduplicated. Every run appends and skips recommendationids
   already in the file, so a dropped connection costs you nothing.

Run it:
    py collect_reviews.py
    py collect_reviews.py --app 1172470 --out apex_reviews.csv
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

# Apex Legends. Change with --app to study a different game.
DEFAULT_APP_ID = 1172470  # Apex Legends, the deep-dive game

# language code -> how many reviews to pull at most.
# English is capped because 158k reviews would take hours and we do not need
# them: a few thousand recent ones is plenty for a comparison. The smaller
# languages are capped above their total review count, so we take all of them.
LANGUAGE_CAPS = {
    "english": 15000,
    "schinese": 15000,   # Simplified Chinese, mostly mainland players
    "tchinese": 5000,    # Traditional Chinese, mostly Taiwan and Hong Kong
    "japanese": 5000,
    "koreana": 8000,
}

PAGE_SIZE = 100          # Steam's maximum per request
DELAY_SECONDS = 1.0      # be a polite guest on someone else's API

FIELDS = [
    "recommendationid", "language", "voted_up", "timestamp_created",
    "timestamp_updated", "playtime_at_review_min", "playtime_forever_min",
    "num_games_owned", "num_reviews_by_author", "votes_up", "votes_funny",
    "weighted_vote_score", "comment_count", "steam_purchase",
    "received_for_free", "written_during_early_access", "review_text",
]


def fetch_page(app_id, language, cursor):
    """One request to Steam. Returns (list of reviews, next cursor)."""
    params = {
        "json": 1,
        "language": language,
        "filter": "recent",
        "purchase_type": "all",
        "num_per_page": PAGE_SIZE,
        "cursor": cursor,          # must be URL encoded, it contains + and =
    }
    url = ("https://store.steampowered.com/appreviews/%d?%s"
           % (app_id, urllib.parse.urlencode(params)))
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-study/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("success") != 1:
        raise RuntimeError("Steam returned success != 1 for %s" % language)
    return payload.get("reviews", []), payload.get("cursor", "*")


def flatten(review, language):
    """Steam nests author data. Flatten it into one row we can write to CSV."""
    author = review.get("author", {})
    return {
        "recommendationid": review.get("recommendationid"),
        "language": language,
        "voted_up": 1 if review.get("voted_up") else 0,
        "timestamp_created": review.get("timestamp_created"),
        "timestamp_updated": review.get("timestamp_updated"),
        "playtime_at_review_min": author.get("playtime_at_review"),
        "playtime_forever_min": author.get("playtime_forever"),
        "num_games_owned": author.get("num_games_owned"),
        "num_reviews_by_author": author.get("num_reviews"),
        "votes_up": review.get("votes_up"),
        "votes_funny": review.get("votes_funny"),
        "weighted_vote_score": review.get("weighted_vote_score"),
        "comment_count": review.get("comment_count"),
        "steam_purchase": 1 if review.get("steam_purchase") else 0,
        "received_for_free": 1 if review.get("received_for_free") else 0,
        "written_during_early_access": 1 if review.get("written_during_early_access") else 0,
        # newlines inside review text would break a naive CSV reader,
        # so collapse them here and keep the file one row per review
        "review_text": (review.get("review") or "").replace("\r", " ").replace("\n", " "),
    }


def load_existing_ids(path):
    """So a re-run tops up the file instead of duplicating it."""
    if not os.path.exists(path):
        return set()
    seen = set()
    with open(path, "r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            seen.add(row["recommendationid"])
    return seen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=int, default=DEFAULT_APP_ID)
    parser.add_argument("--out", default="reviews_raw.csv")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "..", "01_data", "raw", args.out)
    out_path = os.path.normpath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    seen = load_existing_ids(out_path)
    is_new_file = not os.path.exists(out_path)
    print("Writing to: %s" % out_path)
    print("Already have %d reviews on disk" % len(seen))

    handle = open(out_path, "a", encoding="utf-8", newline="")
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    if is_new_file:
        writer.writeheader()

    grand_total = 0
    try:
        for language, cap in LANGUAGE_CAPS.items():
            cursor = "*"           # "*" means start at the beginning
            collected = 0
            print("\n--- %s (cap %d) ---" % (language, cap))
            while collected < cap:
                try:
                    reviews, next_cursor = fetch_page(args.app, language, cursor)
                except Exception as error:
                    print("  request failed (%s), waiting 10s and retrying once" % error)
                    time.sleep(10)
                    try:
                        reviews, next_cursor = fetch_page(args.app, language, cursor)
                    except Exception as second_error:
                        print("  failed twice, moving to next language: %s" % second_error)
                        break

                if not reviews:
                    print("  no more reviews, this language is exhausted")
                    break

                written_this_page = 0
                for review in reviews:
                    rid = review.get("recommendationid")
                    if rid in seen:
                        continue
                    seen.add(rid)
                    writer.writerow(flatten(review, language))
                    written_this_page += 1

                handle.flush()
                collected += written_this_page
                grand_total += written_this_page
                print("  +%d (this language: %d, total: %d)"
                      % (written_this_page, collected, grand_total))

                if next_cursor == cursor:
                    print("  cursor stopped moving, end of history")
                    break
                cursor = next_cursor
                time.sleep(DELAY_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped by you. The file is valid, re-run to carry on.")
    finally:
        handle.close()

    print("\nDone. %d new reviews written to %s" % (grand_total, out_path))


if __name__ == "__main__":
    main()
