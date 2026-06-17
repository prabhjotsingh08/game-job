"""Keyword include / exclude matching with whole-word boundaries.

Substring matching is a trap: "unity" lives inside "comm*unity*", "game" inside
"*game*plan". We match each keyword/phrase only when it's bounded by non-alphanumerics
(or string edges), which still allows phrases like "c# game" and "ar/vr".
"""
from __future__ import annotations

import re
from functools import lru_cache

from .config import Config
from .job import Job


@lru_cache(maxsize=512)
def _pattern(keyword: str) -> re.Pattern:
    # No alphanumeric immediately before/after the keyword.
    return re.compile(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])")


def _hit(terms: tuple[str, ...], text: str) -> bool:
    return any(_pattern(t).search(text) for t in terms)


# Sources whose body text is trustworthy signal, so we match against it too.
# Only HackerNews: each "who is hiring" comment IS one job post. Generic boards
# (and Remotive/Himalayas, which already pre-search for Unity) stay title/tags-only
# — body-matching them lets "Unity Catalog" (a Databricks data term) etc. slip in.
BODY_MATCH_SOURCES = {"HackerNews"}

# Sources to match on TITLE ONLY (ignore tags). Remotive attaches huge kitchen-sink
# tag lists (e.g. an agency "Data Scientist" tagged with 'unity' for Databricks Unity
# Catalog) — title-only keeps real "Unity Developer" posts and drops that noise.
TITLE_ONLY_SOURCES = {"Remotive"}


def matches(job: Job, cfg: Config) -> bool:
    if job.source in TITLE_ONLY_SOURCES:
        text = job.title.lower()
    else:
        text = job.match_text()
    if job.source in BODY_MATCH_SOURCES:
        text = text + " " + job.description.lower()

    if _hit(tuple(cfg.exclude), text):
        return False
    return _hit(tuple(cfg.keywords), text)
