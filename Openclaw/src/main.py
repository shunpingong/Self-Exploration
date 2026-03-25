from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI

from src.api.agent_router import router
from src.config import get_settings


_RESERVED_LOG_RECORD_FIELDS = set(
    logging.LogRecord(
        name="",
        level=0,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__.keys()
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_FIELDS:
                continue
            if key in payload:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "startup_ready",
        extra={
            "event": "startup_ready",
            "path": settings.openclaw_gateway_url,
        },
    )
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(router)
