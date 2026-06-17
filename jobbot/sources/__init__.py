"""Job sources. Each module exposes fetch(cfg) -> list[Job] and never raises;
on error it logs and returns []. collect_all() runs every enabled source that is
due (per its MIN_INTERVAL_HOURS and the SourceState).
"""
from __future__ import annotations

from ..config import Config
from ..job import Job
from ..schedule import SourceState
from . import (
    adzuna,
    arbeitnow,
    ashby,
    greenhouse,
    hackernews,
    himalayas,
    jobicy,
    jooble,
    lever,
    remoteok,
    remotive,
    weworkremotely,
)

# Generic boards always run; studio boards only run if configured.
# Order doesn't matter; rate-limited sources self-gate via MIN_INTERVAL_HOURS, and
# aggregators (adzuna/jooble) no-op until their API keys are set.
_GENERIC = [
    remoteok, weworkremotely, arbeitnow, jobicy, hackernews, remotive, himalayas,
    adzuna, jooble,
]


def collect_all(cfg: Config, state: SourceState) -> list[Job]:
    jobs: list[Job] = []
    for mod in _GENERIC:
        name = mod.__name__.split(".")[-1]
        interval = getattr(mod, "MIN_INTERVAL_HOURS", 0)
        if not state.is_due(name, interval):
            print(f"  [{name}] skipped (not due, every {interval}h)")
            continue
        try:
            found = mod.fetch(cfg)
            print(f"  [{name}] {len(found)} jobs")
            jobs.extend(found)
            state.mark(name)
        except Exception as e:  # a source must never kill the run
            print(f"  [{name}] ERROR: {e}")

    for token in cfg.greenhouse:
        _run_studio(greenhouse, token, jobs)
    for token in cfg.lever:
        _run_studio(lever, token, jobs)
    for token in cfg.ashby:
        _run_studio(ashby, token, jobs)

    return jobs


def _run_studio(mod, token: str, jobs: list[Job]) -> None:
    name = mod.__name__.split(".")[-1]
    try:
        found = mod.fetch(token)
        print(f"  [{name}:{token}] {len(found)} jobs")
        jobs.extend(found)
    except Exception as e:
        print(f"  [{name}:{token}] ERROR: {e}")
