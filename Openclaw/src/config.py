from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _parse_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        parsed = int(raw_value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _parse_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    environment: str
    api_key: str
    openclaw_gateway_url: str
    openclaw_gateway_token: str
    openclaw_ws_timeout_seconds: int
    openclaw_default_deliver: bool
    openclaw_default_reply_channel: str | None
    openclaw_default_reply_to: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    gateway_url = os.getenv("OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789").strip()
    return Settings(
        app_name=os.getenv("APP_NAME", "OpenClaw API Gateway"),
        environment=os.getenv("ENVIRONMENT", "development"),
        api_key=os.getenv("API_KEY", "").strip(),
        openclaw_gateway_url=gateway_url or "ws://127.0.0.1:18789",
        openclaw_gateway_token=os.getenv("OPENCLAW_GATEWAY_TOKEN", "").strip(),
        openclaw_ws_timeout_seconds=_parse_positive_int("OPENCLAW_WS_TIMEOUT_SECONDS", 30),
        openclaw_default_deliver=_parse_bool("OPENCLAW_DEFAULT_DELIVER", False),
        openclaw_default_reply_channel=(os.getenv("OPENCLAW_DEFAULT_REPLY_CHANNEL") or "").strip() or None,
        openclaw_default_reply_to=(os.getenv("OPENCLAW_DEFAULT_REPLY_TO") or "").strip() or None,
    )
