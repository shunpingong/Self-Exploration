from __future__ import annotations

from pydantic import BaseModel, Field


class AgentMessageRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=8000)
    deliver: bool | None = None
    reply_channel: str | None = Field(default=None, max_length=64)
    reply_to: str | None = Field(default=None, max_length=256)
