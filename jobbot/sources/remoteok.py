"""RemoteOK public JSON API: https://remoteok.com/api"""
from __future__ import annotations

from ..config import Config
from ..job import Job
from ._http import get_json

URL = "https://remoteok.com/api"


def fetch(cfg: Config) -> list[Job]:
    data = get_json(URL)
    jobs: list[Job] = []
    # First element is a legal/metadata notice; skip non-dict / metadata rows.
    for row in data:
        if not isinstance(row, dict) or "position" not in row:
            continue
        jobs.append(
            Job(
                title=row.get("position", ""),
                company=row.get("company", ""),
                url=row.get("url", "") or row.get("apply_url", ""),
                location=row.get("location", "") or "Remote",
                tags=row.get("tags", []) or [],
                description=row.get("description", "") or "",
                source="RemoteOK",
            )
        )
    return jobs
