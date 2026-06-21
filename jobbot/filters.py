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

# Studio / ATS source families (named "Family/<token>") whose job DESCRIPTIONS are
# trustworthy Unity signal — a studio's title is often "Gameplay Programmer" while only
# the JD names Unity. We scan their body for the INCLUDE keyword (and for the remote
# check), but NOT for excludes (see matches()), so JD boilerplate can't false-drop a role.
STUDIO_FAMILIES = {"Greenhouse", "Lever", "Ashby", "Recruitee", "Workable"}

# Sources whose API query already guarantees Unity relevance (queried literally for
# "unity developer"). For these the title need NOT contain the word "unity" — only a
# developer role term — which recovers real roles titled e.g. "Game Developer". Every other
# source still requires "unity" in the title.
UNITY_PREFILTERED_SOURCES = {"Adzuna", "Jooble"}


def _family(source: str) -> str:
    return source.split("/", 1)[0]


def _scans_body(source: str) -> bool:
    """True if the description is reliable signal for this source (aggregators/HN and
    every studio/ATS board)."""
    return source in BODY_MATCH_SOURCES or _family(source) in STUDIO_FAMILIES


def matches(job: Job, cfg: Config) -> bool:
    """Strict Unity-developer match: the TITLE must name a Unity keyword AND a developer
    role term. Deliberately title-only (no description, no tags) — a studio JD almost always
    mentions Unity, and tags are noisy, so both produce false positives like "UX Designer"
    or "Data Engineer" at a Unity studio. Title-only keeps real "Unity Developer" roles.
    """
    title = job.title.lower()
    if _hit(tuple(cfg.exclude), title):
        return False
    if not _hit(tuple(cfg.role_terms), title):     # must be a developer/engineer role
        return False
    if job.source in UNITY_PREFILTERED_SOURCES:    # API already filtered to "unity developer"
        return True
    return _hit(tuple(cfg.keywords), title)        # else the title must name Unity


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
    if _scans_body(job.source):
        text += " " + job.description.lower()
    # Whole-word match (like matches()) so "global" doesn't fire inside "globalization".
    return _hit(REMOTE_TERMS, text)
