from __future__ import annotations

import asyncio
import json
import logging
import platform
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, WebSocketException

from src.config import get_settings
from src.core.session_manager import session_manager

logger = logging.getLogger(__name__)


class OpenClawBridgeError(Exception):
    """Raised when OpenClaw gateway communication fails."""


PROTOCOL_VERSION = 3
OPERATOR_ROLE = "operator"
OPERATOR_SCOPES = [
    "operator.admin",
    "operator.read",
    "operator.write",
    "operator.approvals",
    "operator.pairing",
]


async def send_message_to_openclaw(
    user_id: str,
    message: str,
    deliver: bool = False,
    reply_channel: str | None = None,
    reply_to: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    session_id = await session_manager.get_or_create_session(user_id)
    resolved_deliver = bool(deliver or settings.openclaw_default_deliver)
    resolved_reply_channel = (reply_channel or settings.openclaw_default_reply_channel or "").strip() or None
    resolved_reply_to = (reply_to or settings.openclaw_default_reply_to or "").strip() or None

    logger.info(
        "openclaw_request",
        extra={"event": "openclaw_request", "user_id": user_id, "session_id": session_id},
    )

    try:
        raw_result = await _send_and_wait_response(
            gateway_url=settings.openclaw_gateway_url,
            gateway_token=settings.openclaw_gateway_token,
            session_key=session_id,
            message=message,
            deliver=resolved_deliver,
            reply_channel=resolved_reply_channel,
            reply_to=resolved_reply_to,
            timeout_seconds=settings.openclaw_ws_timeout_seconds,
        )
        normalized = _normalize_response(raw_result, fallback_session_id=session_id)
    except OpenClawBridgeError:
        logger.error(
            "openclaw_error",
            extra={"event": "openclaw_error", "user_id": user_id, "session_id": session_id},
        )
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "openclaw_error",
            extra={
                "event": "openclaw_error",
                "user_id": user_id,
                "session_id": session_id,
                "error": str(exc),
            },
        )
        raise OpenClawBridgeError(f"OpenClaw WebSocket integration failed: {exc}") from exc

    logger.info(
        "openclaw_response",
        extra={
            "event": "openclaw_response",
            "user_id": user_id,
            "session_id": normalized["session_id"],
            "summary": normalized.get("summary", ""),
            "response": normalized.get("response", ""),
            "response_length": len(str(normalized.get("response", ""))),
        },
    )
    return normalized


async def _send_and_wait_response(
    gateway_url: str,
    gateway_token: str,
    session_key: str,
    message: str,
    deliver: bool,
    reply_channel: str | None,
    reply_to: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not gateway_token:
        raise OpenClawBridgeError("OPENCLAW_GATEWAY_TOKEN is not set.")

    try:
        websocket = await asyncio.wait_for(
            connect(gateway_url, max_size=25 * 1024 * 1024),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError as exc:
        raise OpenClawBridgeError("Timed out connecting to OpenClaw gateway.") from exc
    except (ConnectionClosed, OSError, WebSocketException) as exc:
        raise OpenClawBridgeError(f"Failed connecting to OpenClaw gateway at {gateway_url}: {exc}") from exc

    async with websocket:
        try:
            challenge = await _wait_for_connect_challenge(websocket, timeout_seconds)
            nonce = _extract_nonce(challenge)
            if not nonce:
                raise OpenClawBridgeError("OpenClaw gateway connect challenge missing nonce.")

            connect_request_id = str(uuid4())
            connect_payload = _build_connect_payload(
                gateway_token=gateway_token,
            )
            await _send_request_frame(
                websocket=websocket,
                request_id=connect_request_id,
                method="connect",
                params=connect_payload,
                timeout_seconds=timeout_seconds,
            )
            await _wait_for_response_frame(
                websocket=websocket,
                request_id=connect_request_id,
                timeout_seconds=timeout_seconds,
            )

            run_id = str(uuid4())
            chat_request_id = str(uuid4())
            chat_params = _build_chat_send_params(
                session_key=session_key,
                message=message,
                deliver=deliver,
                run_id=run_id,
            )
            await _send_request_frame(
                websocket=websocket,
                request_id=chat_request_id,
                method="chat.send",
                params=chat_params,
                timeout_seconds=timeout_seconds,
            )

            return await _wait_for_chat_terminal_state(
                websocket=websocket,
                chat_request_id=chat_request_id,
                run_id=run_id,
                session_key=session_key,
                deliver=deliver,
                timeout_seconds=timeout_seconds,
                reply_channel=reply_channel,
                reply_to=reply_to,
            )
        except ConnectionClosed as exc:
            raise OpenClawBridgeError(f"OpenClaw gateway connection closed before final response: {exc}") from exc


async def _wait_for_connect_challenge(websocket, timeout_seconds: int) -> dict[str, Any]:
    while True:
        frame = await _recv_frame(websocket, timeout_seconds)
        if frame.get("type") == "event" and frame.get("event") == "connect.challenge":
            return frame


def _extract_nonce(challenge_frame: dict[str, Any]) -> str | None:
    payload = challenge_frame.get("payload")
    if not isinstance(payload, dict):
        return None
    nonce = payload.get("nonce")
    if not isinstance(nonce, str):
        return None
    nonce = nonce.strip()
    return nonce or None


def _build_connect_payload(gateway_token: str) -> dict[str, Any]:
    return {
        "minProtocol": PROTOCOL_VERSION,
        "maxProtocol": PROTOCOL_VERSION,
        "client": {
            "id": "gateway-client",
            "version": "openclaw-api-gateway/0.1.0",
            "platform": platform.system().lower() or "python",
            "mode": "backend",
        },
        "role": OPERATOR_ROLE,
        "scopes": OPERATOR_SCOPES,
        "caps": [],
        "auth": {"token": gateway_token},
        "locale": "en-US",
        "userAgent": "openclaw-api-gateway/0.1.0",
    }


def _build_chat_send_params(
    session_key: str,
    message: str,
    deliver: bool,
    run_id: str,
) -> dict[str, Any]:
    return {
        "sessionKey": session_key,
        "message": message,
        "deliver": deliver,
        "idempotencyKey": run_id,
    }


async def _send_request_frame(
    websocket,
    request_id: str,
    method: str,
    params: dict[str, Any],
    timeout_seconds: int,
) -> None:
    frame = {
        "type": "req",
        "id": request_id,
        "method": method,
        "params": params,
    }
    try:
        await asyncio.wait_for(websocket.send(json.dumps(frame)), timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        raise OpenClawBridgeError(f"Timed out sending OpenClaw request '{method}'.") from exc


async def _wait_for_response_frame(
    websocket,
    request_id: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    while True:
        frame = await _recv_frame(websocket, timeout_seconds)
        if frame.get("type") != "res" or frame.get("id") != request_id:
            continue

        if frame.get("ok") is True:
            payload = frame.get("payload")
            return payload if isinstance(payload, dict) else {}

        raise OpenClawBridgeError(_format_gateway_error(frame.get("error")))


async def _wait_for_chat_terminal_state(
    websocket,
    chat_request_id: str,
    run_id: str,
    session_key: str,
    deliver: bool,
    timeout_seconds: int,
    reply_channel: str | None,
    reply_to: str | None,
) -> dict[str, Any]:
    req_payload: dict[str, Any] | None = None
    latest_text = ""
    final_text = ""
    final_state = "ok"
    final_error = ""

    while True:
        frame = await _recv_frame(websocket, timeout_seconds)
        frame_type = frame.get("type")

        if frame_type == "res" and frame.get("id") == chat_request_id:
            if frame.get("ok") is not True:
                raise OpenClawBridgeError(_format_gateway_error(frame.get("error")))
            payload = frame.get("payload")
            req_payload = payload if isinstance(payload, dict) else {}
            status = str(req_payload.get("status") or "").lower()
            # In some gateway versions, terminal status can arrive in the response frame.
            if status in {"ok", "error", "timeout", "aborted"}:
                if status != "ok":
                    final_state = status
                    final_error = str(req_payload.get("summary") or req_payload.get("error") or status)
                break
            continue

        if frame_type == "event" and frame.get("event") == "chat":
            payload = frame.get("payload")
            if not isinstance(payload, dict):
                continue

            event_run_id = payload.get("runId")
            event_session_key = payload.get("sessionKey")
            if event_run_id != run_id and event_session_key != session_key:
                continue

            state = str(payload.get("state") or "").lower()
            if state == "delta":
                delta_text = _extract_message_text(payload.get("message"))
                if delta_text:
                    latest_text = delta_text
                continue

            if state == "final":
                final_state = "ok"
                final_text = _extract_message_text(payload.get("message")) or latest_text
                break

            if state == "aborted":
                final_state = "aborted"
                final_text = _extract_message_text(payload.get("message")) or latest_text
                final_error = str(payload.get("stopReason") or "OpenClaw chat run aborted.")
                break

            if state == "error":
                final_state = "error"
                final_error = str(payload.get("errorMessage") or "OpenClaw chat run failed.")
                break

    if final_state == "error":
        raise OpenClawBridgeError(final_error or "OpenClaw chat run failed.")

    if final_state == "aborted":
        raise OpenClawBridgeError(final_error or "OpenClaw chat run aborted.")

    response_text = final_text
    if not response_text and isinstance(req_payload, dict):
        response_text = str(req_payload.get("summary") or "")

    metadata: dict[str, Any] = {
        "source": "openclaw_gateway_ws",
        "run_id": run_id,
        "status": final_state,
    }
    if reply_channel:
        metadata["requested_reply_channel"] = reply_channel
    if reply_to:
        metadata["requested_reply_to"] = reply_to

    if deliver and reply_channel and reply_to and response_text:
        delivery_result = await _try_send_explicit_delivery(
            websocket=websocket,
            timeout_seconds=timeout_seconds,
            channel=reply_channel,
            to=reply_to,
            message=response_text,
        )
        metadata["delivery"] = delivery_result

    return {
        "success": True,
        "session_id": session_key,
        "response": response_text,
        "summary": response_text[:120] if response_text else "",
        "actions": [],
        "metadata": metadata,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _try_send_explicit_delivery(
    websocket,
    timeout_seconds: int,
    channel: str,
    to: str,
    message: str,
) -> dict[str, Any]:
    request_id = str(uuid4())
    send_params: dict[str, Any] = {
        "to": to,
        "message": message,
        "channel": channel,
        "idempotencyKey": str(uuid4()),
    }
    try:
        await _send_request_frame(
            websocket=websocket,
            request_id=request_id,
            method="send",
            params=send_params,
            timeout_seconds=timeout_seconds,
        )
        send_payload = await _wait_for_response_frame(
            websocket=websocket,
            request_id=request_id,
            timeout_seconds=timeout_seconds,
        )
        delivery_meta: dict[str, Any] = {
            "requested": True,
            "ok": True,
            "channel": channel,
            "to": to,
        }
        if isinstance(send_payload, dict):
            for key in ("messageId", "channel", "conversationId", "chatId", "toJid", "runId"):
                if key in send_payload:
                    delivery_meta[key] = send_payload[key]
        return delivery_meta
    except OpenClawBridgeError as exc:
        logger.warning(
            "openclaw_delivery_error",
            extra={
                "event": "openclaw_error",
                "error": str(exc),
            },
        )
        return {
            "requested": True,
            "ok": False,
            "channel": channel,
            "to": to,
            "error": str(exc),
        }


def _extract_message_text(message: Any) -> str:
    if isinstance(message, str):
        return message.strip()
    if not isinstance(message, dict):
        return ""

    direct_text = message.get("text")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                if item.strip():
                    text_parts.append(item.strip())
                continue
            if not isinstance(item, dict):
                continue
            item_text = item.get("text")
            if isinstance(item_text, str) and item_text.strip():
                text_parts.append(item_text.strip())
        return "\n".join(text_parts).strip()

    return ""


async def _recv_frame(websocket, timeout_seconds: int) -> dict[str, Any]:
    try:
        frame = await asyncio.wait_for(websocket.recv(), timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        raise OpenClawBridgeError("Timed out waiting for OpenClaw gateway response.") from exc

    decoded = _parse_frame(frame)
    if decoded is None:
        raise OpenClawBridgeError("OpenClaw gateway returned an invalid JSON frame.")
    return decoded


def _parse_frame(frame: Any) -> dict[str, Any] | None:
    if isinstance(frame, bytes):
        frame = frame.decode("utf-8", errors="replace")
    if isinstance(frame, str):
        text = frame.strip()
        if not text:
            return None
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, dict) else None
    if isinstance(frame, dict):
        return frame
    return None


def _format_gateway_error(error_payload: Any) -> str:
    if not isinstance(error_payload, dict):
        return "OpenClaw gateway request failed."
    message = str(error_payload.get("message") or "OpenClaw gateway request failed.")
    details = error_payload.get("details")
    if isinstance(details, dict):
        detail_code = details.get("code")
        next_step = details.get("recommendedNextStep")
        if detail_code:
            message = f"{message} (code={detail_code})"
        if next_step:
            message = f"{message} next={next_step}"
    return message


def _normalize_response(raw: dict[str, Any], fallback_session_id: str) -> dict[str, Any]:
    payload = raw.get("data") if isinstance(raw.get("data"), dict) else raw

    response_text = str(
        payload.get("response")
        or payload.get("message")
        or payload.get("text")
        or ""
    )
    summary_text = str(payload.get("summary") or (response_text[:120] if response_text else ""))
    actions = payload.get("actions") if isinstance(payload.get("actions"), list) else []
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    metadata.setdefault("source", "openclaw_gateway_ws")

    return {
        "success": bool(payload.get("success", True)),
        "session_id": str(payload.get("session_id") or fallback_session_id),
        "response": response_text,
        "summary": summary_text,
        "actions": actions,
        "metadata": metadata,
    }
