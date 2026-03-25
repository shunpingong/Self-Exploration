from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://nemobot-neue-experiment.vercel.app",
)
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Use tools when they provide grounded information. "
    "If you call a tool, wait for the tool result, then answer the user using that result. /think"
)
TRUE_ENV_VALUES = {"1", "true", "yes", "on"}


def parse_csv_env(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def parse_bool_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in TRUE_ENV_VALUES


def parse_int_env(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    host: str
    port: int
    nvidia_api_base: str
    nvidia_api_key: str
    nvidia_model: str
    cors_allow_origins: tuple[str, ...]
    cors_allow_credentials: bool
    system_prompt: str
    default_temperature: float
    default_top_p: float
    default_max_tokens: int
    default_reasoning_budget: int
    default_enable_thinking: bool
    app_log_name: str
    log_level: int
    log_format: str

    @classmethod
    def from_env(cls) -> "Settings":
        cors_allow_origins = parse_csv_env(
            os.getenv("CORS_ALLOW_ORIGINS", ",".join(DEFAULT_CORS_ALLOW_ORIGINS))
        )
        cors_allow_credentials = parse_bool_env(os.getenv("CORS_ALLOW_CREDENTIALS"), True)
        if cors_allow_origins == ("*",):
            cors_allow_credentials = False

        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=parse_int_env(os.getenv("PORT"), 8080),
            nvidia_api_base=os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1").rstrip("/"),
            nvidia_api_key=os.getenv("NVIDIA_API_KEY", "").strip(),
            nvidia_model=os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b"),
            cors_allow_origins=cors_allow_origins,
            cors_allow_credentials=cors_allow_credentials,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            default_temperature=1.0,
            default_top_p=0.95,
            default_max_tokens=16384,
            default_reasoning_budget=16384,
            default_enable_thinking=True,
            app_log_name="nemotron_fastapi",
            log_level=logging.INFO,
            log_format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )


settings = Settings.from_env()
