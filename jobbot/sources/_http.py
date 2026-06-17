"""Shared HTTP helpers."""
from __future__ import annotations

import requests

UA = "Mozilla/5.0 (compatible; game-job-bot/1.0; +https://github.com)"
HEADERS = {"User-Agent": UA, "Accept": "application/json"}


def get_json(url: str, timeout: int = 25, headers: dict | None = None):
    h = dict(HEADERS)
    if headers:
        h.update(headers)
    resp = requests.get(url, headers=h, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
