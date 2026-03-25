from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException, status

from src.config import get_settings


async def verify_api_key(
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
) -> None:
    """Optional API key guard. Disabled when API_KEY is not configured."""
    configured_key = get_settings().api_key
    if not configured_key:
        return
    if x_api_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
