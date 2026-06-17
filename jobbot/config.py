"""Load and expose config.yaml plus environment secrets."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"


class Config:
    def __init__(self, data: dict):
        self.keywords = [k.lower() for k in data.get("keywords", [])]
        self.exclude = [k.lower() for k in data.get("exclude", [])]
        self.remoteok_tags = data.get("remoteok_tags", [])
        studios = data.get("studios") or {}
        self.greenhouse = studios.get("greenhouse") or []
        self.lever = studios.get("lever") or []
        self.ashby = studios.get("ashby") or []
        self.seen_retention_days = int(data.get("seen_retention_days", 60))
        self.remote_only = bool(data.get("remote_only", True))

    # Secrets come from the environment (GitHub Actions secrets / local .env).
    @property
    def telegram_token(self) -> str:
        return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()

    @property
    def telegram_chat_id(self) -> str:
        return os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_token and self.telegram_chat_id)

    @property
    def whatsapp_phone(self) -> str:
        return os.environ.get("WHATSAPP_PHONE", "").strip()

    @property
    def whatsapp_apikey(self) -> str:
        return os.environ.get("WHATSAPP_APIKEY", "").strip()

    @property
    def whatsapp_enabled(self) -> bool:
        return bool(self.whatsapp_phone and self.whatsapp_apikey)

    @property
    def discord_webhook(self) -> str:
        return os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    @property
    def discord_enabled(self) -> bool:
        return bool(self.discord_webhook)


def load_config() -> Config:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return Config(yaml.safe_load(f) or {})
