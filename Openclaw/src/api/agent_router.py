from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.security import verify_api_key
from src.schemas.agent_response import AgentResponse
from src.schemas.message import AgentMessageRequest
from src.services.openclaw_ws_client import OpenClawBridgeError, send_message_to_openclaw

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/agent/message",
    response_model=AgentResponse,
    dependencies=[Depends(verify_api_key)],
)
async def post_agent_message(payload: AgentMessageRequest) -> AgentResponse:
    logger.info(
        "api_request",
        extra={
            "event": "api_request",
            "user_id": payload.user_id,
        },
    )

    try:
        bridge_result = await send_message_to_openclaw(
            user_id=payload.user_id,
            message=payload.message,
            deliver=bool(payload.deliver or False),
            reply_channel=payload.reply_channel,
            reply_to=payload.reply_to,
        )
    except OpenClawBridgeError as exc:
        logger.error(
            "openclaw_error",
            extra={
                "event": "openclaw_error",
                "user_id": payload.user_id,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenClaw runtime unavailable: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "openclaw_error",
            extra={
                "event": "openclaw_error",
                "user_id": payload.user_id,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process agent message.",
        ) from exc

    return AgentResponse(
        success=bool(bridge_result.get("success", True)),
        session_id=str(bridge_result.get("session_id", "")),
        summary=str(bridge_result.get("summary", "")),
        response=str(bridge_result.get("response", "")),
        actions=bridge_result.get("actions", []),
        metadata=bridge_result.get("metadata", {}),
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
