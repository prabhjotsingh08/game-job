"""We Work Remotely category RSS feeds."""
from __future__ import annotations

import feedparser

from ..config import Config
from ..job import Job

FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
]


def fetch(cfg: Config) -> list[Job]:
    jobs: list[Job] = []
    for feed_url in FEEDS:
        parsed = feedparser.parse(feed_url)
        for e in parsed.entries:
            # WWR titles look like "Company: Job Title"
            raw = e.get("title", "")
            company, _, title = raw.partition(":")
            if not title:
                title, company = company, ""
            jobs.append(
                Job(
                    title=title.strip() or raw,
                    company=company.strip(),
                    url=e.get("link", ""),
                    location=e.get("region", "") or "Remote",
                    description=e.get("summary", ""),
                    source="WeWorkRemotely",
                )
            )
    return jobs
