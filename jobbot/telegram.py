"""Send formatted job alerts to a Telegram chat via the Bot API."""
from __future__ import annotations

import html
import time

import requests

from .job import Job

API = "https://api.telegram.org/bot{token}/sendMessage"


def _format(job: Job) -> str:
    title = html.escape(job.title)
    company = html.escape(job.company)
    loc = f" · {html.escape(job.location)}" if job.location else ""
    src = html.escape(job.source)
    return (
        f"🎮 <b>{title}</b>\n"
        f"🏢 {company}{loc}\n"
        f"🔗 <a href=\"{html.escape(job.url)}\">Apply</a>\n"
        f"<i>via {src}</i>"
    )


def send_jobs(jobs: list[Job], token: str, chat_id: str) -> int:
    """Send each job as its own message. Returns count successfully sent."""
    if not token or not chat_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set in environment."
        )
    url = API.format(token=token)
    sent = 0
    for job in jobs:
        try:
            resp = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": _format(job),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=20,
            )
            if resp.status_code == 429:
                # Respect Telegram rate limiting and retry once.
                retry_after = resp.json().get("parameters", {}).get("retry_after", 3)
                time.sleep(retry_after + 1)
                resp = requests.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": _format(job),
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                    timeout=20,
                )
            if resp.ok:
                sent += 1
            else:
                print(f"  ! Telegram send failed ({resp.status_code}): {resp.text[:200]}")
            time.sleep(0.5)  # stay under ~1 msg/sec to the same chat
        except requests.RequestException as e:
            print(f"  ! Telegram error: {e}")
    return sent
