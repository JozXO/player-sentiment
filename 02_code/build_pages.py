"""
build_pages.py
Wraps the authored write-up into the version GitHub Pages serves.

Why this exists. 04_writeup/index.html is authored as a fragment: a title, a
stylesheet link and a style block, then the content. That is the form the
Claude artifact host wants, because it supplies its own document skeleton.

A file served directly needs a real document with a real <head>, and social
platforms need Open Graph tags in it. Without them LinkedIn shows "we couldn't
generate a preview for this link" and the share is a bare URL.

So this script builds docs/index.html from 04_writeup/index.html: same content,
wrapped in a proper document, with the OG and Twitter card tags added. Run it
after editing the write-up.
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "04_writeup", "index.html"))
DST = os.path.normpath(os.path.join(HERE, "..", "docs", "index.html"))

SITE = "https://jozxo.github.io/player-sentiment/"
TITLE = "The Language Gap: what a single review score hides"
DESC = ("Apex Legends scores 76.6% positive in English and 40.1% in Traditional "
        "Chinese. 218,380 Steam reviews, three explanations rejected, and a "
        "review-bombing event that was faking a fourth.")

source = open(SRC, encoding="utf-8").read()

# the authored file is <title> + links + <style>...</style> + content
split = source.index("</style>") + len("</style>")
head_bits, body = source[:split], source[split:]

head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="Josiah Francis">
<meta name="description" content="{DESC}">
<link rel="canonical" href="{SITE}">

<meta property="og:type" content="article">
<meta property="og:site_name" content="Josiah Francis">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{SITE}">
<meta property="og:image" content="{SITE}og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The same game, rated 36 points apart. English 76.6% positive, Traditional Chinese 40.1% positive.">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="{SITE}og-image.png">

{head_bits}
</head>
<body>
"""

open(DST, "w", encoding="utf-8").write(head + body + "\n</body>\n</html>\n")

built = open(DST, encoding="utf-8").read()
print("wrote %s (%d bytes)" % (DST, len(built)))
for tag in ["og:title", "og:description", "og:image", "og:url", "twitter:card"]:
    print("  %-16s %s" % (tag, "present" if tag in built else "MISSING"))
assert built.count("<style>") == 1 and built.count("</style>") == 1
assert "<div class=\"wrap\">" in built
print("  structure       ok")
