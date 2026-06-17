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


# Sources whose body text is trustworthy signal, so we match against it (for both the
# Unity keyword and the remote check):
# - HackerNews: each "who is hiring" comment IS one job post.
# - Adzuna/Jooble: aggregators queried with "unity developer"; they return a city
#   location (no remote flag), so unity+remote signal lives in the description.
# "unity catalog" is in config exclude to kill the Databricks false positive this opens.
BODY_MATCH_SOURCES = {"HackerNews", "Adzuna", "Jooble"}

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


# Boards that ONLY list remote jobs — every result is remote by definition, even if
# the location field names a country (e.g. Himalayas shows allowed countries).
REMOTE_ONLY_SOURCES = {"RemoteOK", "WeWorkRemotely", "Jobicy", "Remotive", "Himalayas"}


# Any of these in location/title (or body for body-match sources) marks a job remote.
REMOTE_TERMS = (
    "remote", "anywhere", "distributed", "wfh", "work from home", "work-from-home",
    "worldwide", "global", "fully remote", "remote-first",
)


def is_remote(job: Job) -> bool:
    """True if the job is remote. Remote-only boards always pass; mixed sources
    (studios, HN, aggregators) must contain a remote term in location/title
    (or body for body-match sources)."""
    if job.source in REMOTE_ONLY_SOURCES:
        return True
    text = f"{job.location} {job.title}".lower()
    if job.source in BODY_MATCH_SOURCES:
        text += " " + job.description.lower()
    return any(term in text for term in REMOTE_TERMS)
