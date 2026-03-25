from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    success: bool = True
    session_id: str
    summary: str
    response: str
    actions: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
