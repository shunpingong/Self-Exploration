from __future__ import annotations

import asyncio
from uuid import uuid4


class SessionManager:
    """In-memory session mapping for server runtime."""

    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_session(self, user_id: str) -> str:
        async with self._lock:
            if user_id not in self._sessions:
                self._sessions[user_id] = f"sess_{uuid4().hex}"
            return self._sessions[user_id]


session_manager = SessionManager()
