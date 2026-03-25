from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from textwrap import indent
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from settings import settings as app_settings
from tool_features import (
    DEFAULT_TOOLS,
    build_assistant_tool_call_message,
    build_tool_result_messages,
    execute_tool_calls,
)

logging.basicConfig(level=app_settings.log_level, format=app_settings.log_format)
logger = logging.getLogger(app_settings.app_log_name)


class QueryRequest(BaseModel):
    query: str = Field(..., description="Prompt to send to Nemotron.")

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("query must not be empty")
        return cleaned


class QueryResponse(BaseModel):
    model: str
    response: str
    reasoning: str
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    latency: float


class HealthResponse(BaseModel):
    status: str
    model: str
    base_url: str


def build_default_messages(query: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": app_settings.system_prompt},
        {"role": "user", "content": query},
    ]


def add_default_system_message(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if any(message.get("role") == "system" for message in messages):
        return messages
    return [{"role": "system", "content": app_settings.system_prompt}, *messages]


def extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        return "\n".join(part for part in text_parts if part)
    return ""


def extract_messages_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("query"), str) and payload["query"].strip():
        return build_default_messages(payload["query"].strip())

    raw_messages = payload.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
        raise HTTPException(
            status_code=400,
            detail="Request body must include either 'query' or a non-empty 'messages' array.",
        )

    normalized_messages: list[dict[str, Any]] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        if not isinstance(role, str) or not role.strip():
            continue

        message: dict[str, Any] = {"role": role.strip()}
        if "content" in item:
            message["content"] = item["content"]
        if "tool_call_id" in item:
            message["tool_call_id"] = item["tool_call_id"]
        if "tool_calls" in item:
            message["tool_calls"] = item["tool_calls"]
        normalized_messages.append(message)

    if not normalized_messages:
        raise HTTPException(status_code=400, detail="No valid messages were found in the request body.")

    return add_default_system_message(normalized_messages)


def extract_query_preview(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            preview = extract_text_content(message.get("content"))
            if preview:
                return preview
    return "chat request"


def extract_system_prompts(messages: list[dict[str, Any]]) -> list[str]:
    prompts: list[str] = []
    for message in messages:
        if message.get("role") != "system":
            continue
        prompt = extract_text_content(message.get("content"))
        if prompt:
            prompts.append(prompt)
    return prompts


def extract_payload_system_prompts(payload: dict[str, Any]) -> list[str]:
    raw_messages = payload.get("messages")
    if not isinstance(raw_messages, list):
        return []

    prompts: list[str] = []
    for item in raw_messages:
        if not isinstance(item, dict) or item.get("role") != "system":
            continue
        prompt = extract_text_content(item.get("content"))
        if prompt:
            prompts.append(prompt)
    return prompts


def stringify_for_log(value: Any) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    normalized_lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(normalized_lines).strip()


def truncate_for_log(value: Any, limit: int = 1200) -> str:
    text = stringify_for_log(value)
    if not text:
        return "(empty)"
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated]"


def log_block(label: str, section: str, value: Any, *, limit: int = 1200) -> None:
    logger.info(
        "\n[BEGIN %s | %s]\n%s\n[END %s | %s]",
        label,
        section,
        indent(truncate_for_log(value, limit), "  "),
        label,
        section,
    )


def log_model_pass_summary(label: str, result: dict[str, Any]) -> None:
    logger.info(
        "%s completed | response_chars=%d | reasoning_chars=%d | tool_calls=%d",
        label,
        len(result.get("response", "")),
        len(result.get("reasoning", "")),
        len(result.get("tool_calls") or []),
    )


def log_chat_request_summary(preview: str, settings: dict[str, Any]) -> None:
    logger.info(
        "Chat completion request received | preview=%s | stream=%s | tools=%s | "
        "temperature=%.3f | top_p=%.3f | max_tokens=%d",
        truncate_for_log(preview, limit=200),
        settings["stream_response"],
        settings["include_tools"],
        settings["temperature"],
        settings["top_p"],
        settings["max_tokens"],
    )


def format_prompt_list_for_log(prompts: list[str]) -> str:
    if not prompts:
        return "(empty)"
    if len(prompts) == 1:
        return prompts[0]
    return "\n\n".join(f"[System prompt {index}]\n{prompt}" for index, prompt in enumerate(prompts, start=1))


def log_chat_request_system_prompts(payload: dict[str, Any], messages: list[dict[str, Any]]) -> None:
    payload_system_prompts = extract_payload_system_prompts(payload)
    effective_system_prompts = extract_system_prompts(messages)

    if payload_system_prompts:
        logger.info(
            "Incoming payload included %d system message(s); using payload-provided system prompt(s).",
            len(payload_system_prompts),
        )
        log_block(
            "Incoming request",
            "payload system prompt" if len(payload_system_prompts) == 1 else "payload system prompts",
            format_prompt_list_for_log(payload_system_prompts),
            limit=4000,
        )
        return

    if effective_system_prompts:
        logger.info("Incoming payload included no system message; using the configured default system prompt.")
        log_block(
            "Incoming request",
            "effective system prompt",
            format_prompt_list_for_log(effective_system_prompts),
            limit=4000,
        )


def parse_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value: Any, default: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return default


def build_chat_settings(payload: dict[str, Any]) -> dict[str, Any]:
    requested_model = payload.get("model")
    return {
        "model": app_settings.nvidia_model,
        "requested_model": requested_model if isinstance(requested_model, str) else None,
        "temperature": parse_float(payload.get("temperature"), app_settings.default_temperature),
        "top_p": parse_float(payload.get("top_p"), app_settings.default_top_p),
        "max_tokens": parse_int(payload.get("max_tokens"), app_settings.default_max_tokens),
        "stream_response": bool(payload.get("stream", False)),
        "frequency_penalty": parse_float(payload.get("frequency_penalty"), 0.0),
        "presence_penalty": parse_float(payload.get("presence_penalty"), 0.0),
        "include_tools": payload.get("tool_choice") != "none",
    }


def chunk_text(text: str, chunk_size: int = 160) -> list[str]:
    if not text:
        return []
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


def build_openai_chat_response(result: dict[str, Any], latency: float) -> dict[str, Any]:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": result["model"],
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["response"],
                    "tool_calls": result["tool_calls"] or None,
                },
                "finish_reason": "stop",
            }
        ],
        "reasoning": result["reasoning"],
        "tool_calls": result["tool_calls"],
        "tool_results": result["tool_results"],
        "latency": latency,
    }


def build_streaming_chat_response(result: dict[str, Any], latency: float) -> StreamingResponse:
    response_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    def event_stream():
        role_chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": result["model"],
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(role_chunk)}\n\n"

        for piece in chunk_text(result["response"]):
            content_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": result["model"],
                "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(content_chunk)}\n\n"

        final_chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": result["model"],
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            "reasoning": result["reasoning"],
            "tool_calls": result["tool_calls"],
            "tool_results": result["tool_results"],
            "latency": latency,
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def collect_tool_call(tool_call_accumulator: dict[int, dict[str, Any]], tool_call: Any) -> None:
    index = getattr(tool_call, "index", 0) or 0
    entry = tool_call_accumulator.setdefault(
        index,
        {
            "id": None,
            "type": "function",
            "function": {"name": "", "arguments": ""},
        },
    )

    tool_id = getattr(tool_call, "id", None)
    if tool_id:
        entry["id"] = tool_id

    tool_type = getattr(tool_call, "type", None)
    if tool_type:
        entry["type"] = tool_type

    function = getattr(tool_call, "function", None)
    if function is None:
        return

    function_name = getattr(function, "name", None)
    if function_name:
        entry["function"]["name"] = function_name

    arguments = getattr(function, "arguments", None)
    if arguments:
        entry["function"]["arguments"] += arguments


def finalize_tool_calls(tool_call_accumulator: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    finalized: list[dict[str, Any]] = []
    for index in sorted(tool_call_accumulator):
        entry = tool_call_accumulator[index]
        if not entry["id"]:
            entry["id"] = f"tool_call_{index}"

        arguments = entry["function"]["arguments"].strip()
        if arguments:
            try:
                entry["function"]["arguments_json"] = json.loads(arguments)
            except json.JSONDecodeError:
                pass
        finalized.append(entry)
    return finalized


def create_completion(
    client: OpenAI,
    messages: list[dict[str, Any]],
    *,
    settings: dict[str, Any],
    include_tools: bool,
) -> Any:
    request_kwargs: dict[str, Any] = {
        "model": settings["model"],
        "messages": messages,
        "temperature": settings["temperature"],
        "top_p": settings["top_p"],
        "max_tokens": settings["max_tokens"],
        "frequency_penalty": settings["frequency_penalty"],
        "presence_penalty": settings["presence_penalty"],
        "extra_body": {
            "chat_template_kwargs": {"enable_thinking": app_settings.default_enable_thinking},
            "reasoning_budget": app_settings.default_reasoning_budget,
        },
        "stream": True,
    }
    if include_tools:
        request_kwargs["tools"] = DEFAULT_TOOLS
        request_kwargs["tool_choice"] = "auto"
    return client.chat.completions.create(**request_kwargs)


def stream_completion(
    client: OpenAI,
    messages: list[dict[str, Any]],
    *,
    settings: dict[str, Any],
    include_tools: bool,
) -> dict[str, Any]:
    reasoning_parts: list[str] = []
    response_parts: list[str] = []
    tool_call_accumulator: dict[int, dict[str, Any]] = {}

    completion = create_completion(client, messages, settings=settings, include_tools=include_tools)
    for chunk in completion:
        if not getattr(chunk, "choices", None):
            continue

        delta = chunk.choices[0].delta
        reasoning = getattr(delta, "reasoning_content", None)
        if reasoning:
            reasoning_parts.append(reasoning)

        if delta.content:
            response_parts.append(delta.content)

        if getattr(delta, "tool_calls", None):
            for tool_call in delta.tool_calls:
                collect_tool_call(tool_call_accumulator, tool_call)

    return {
        "response": "".join(response_parts).strip(),
        "reasoning": "".join(reasoning_parts).strip(),
        "tool_calls": finalize_tool_calls(tool_call_accumulator),
    }


def run_messages(
    client: OpenAI,
    base_messages: list[dict[str, Any]],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_settings = settings or build_chat_settings({})
    logger.info(
        "Starting model pass 1 | tools_enabled=%s | model=%s",
        active_settings["include_tools"],
        active_settings["model"],
    )
    first_pass = stream_completion(
        client,
        base_messages,
        settings=active_settings,
        include_tools=active_settings["include_tools"],
    )
    log_model_pass_summary("Model pass 1", first_pass)

    tool_calls = first_pass["tool_calls"]
    tool_results: list[dict[str, Any]] = []
    reasoning_segments = [segment for segment in [first_pass["reasoning"]] if segment]
    response_text = first_pass["response"]

    if tool_calls:
        logger.info("Model pass 1 requested %d tool call(s).", len(tool_calls))
        log_block("Model pass 1", "tool calls", tool_calls)
    else:
        logger.info("Model pass 1 requested no tool calls; using pass 1 output as the final answer.")

    if tool_calls:
        logger.info("Executing %d tool call(s).", len(tool_calls))
        tool_results = execute_tool_calls(tool_calls)
        log_block("Tool execution", "tool results", tool_results)
        follow_up_messages = [
            *base_messages,
            build_assistant_tool_call_message(tool_calls),
            *build_tool_result_messages(tool_results),
        ]
        logger.info("Starting model pass 2 with tool results.")
        second_pass = stream_completion(
            client,
            follow_up_messages,
            settings=active_settings,
            include_tools=False,
        )
        if second_pass["reasoning"]:
            reasoning_segments.append(second_pass["reasoning"])
        if second_pass["response"]:
            response_text = second_pass["response"]
        log_model_pass_summary("Model pass 2", second_pass)

    if not response_text and tool_results:
        response_text = json.dumps([tool_result["result"] for tool_result in tool_results], indent=2)

    combined_reasoning = "\n\n".join(reasoning_segments).strip()
    log_block("Final result", "assistant answer", response_text)
    log_block("Final result", "combined reasoning trace", combined_reasoning)
    return {
        "model": active_settings["model"],
        "response": response_text,
        "reasoning": combined_reasoning,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
    }


def run_query(client: OpenAI, query: str) -> dict[str, Any]:
    return run_messages(client, build_default_messages(query), build_chat_settings({}))


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not app_settings.nvidia_api_key:
        raise RuntimeError("NVIDIA_API_KEY is required. Set it in your .env file before starting the API.")

    app.state.client = OpenAI(
        base_url=app_settings.nvidia_api_base,
        api_key=app_settings.nvidia_api_key,
    )
    logger.info(
        "Configured NVIDIA client for model '%s' via %s",
        app_settings.nvidia_model,
        app_settings.nvidia_api_base,
    )
    yield


app = FastAPI(title="Nemotron Exploration", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(app_settings.cors_allow_origins) or ["*"],
    allow_credentials=app_settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=app_settings.nvidia_model,
        base_url=app_settings.nvidia_api_base,
    )


@app.post("/query", response_model=QueryResponse)
async def query(request_body: QueryRequest, request: Request) -> QueryResponse:
    if not hasattr(request.app.state, "client"):
        raise HTTPException(status_code=503, detail="NVIDIA client is not configured.")

    logger.info("Simple query request received | preview=%s", truncate_for_log(request_body.query, limit=200))
    started_at = time.perf_counter()
    try:
        result = await asyncio.to_thread(run_query, request.app.state.client, request_body.query)
    except Exception as exc:
        logger.exception("Nemotron request failed.")
        detail = str(exc).strip() or exc.__class__.__name__
        raise HTTPException(status_code=500, detail=detail) from exc

    latency = time.perf_counter() - started_at
    logger.info(
        "Query completed in %.3fs with %d tool call(s).",
        latency,
        len(result["tool_calls"]),
    )
    return QueryResponse(latency=latency, **result)


@app.post("/query/chat/completions")
async def query_chat_completions(request: Request) -> dict[str, Any]:
    if not hasattr(request.app.state, "client"):
        raise HTTPException(status_code=503, detail="NVIDIA client is not configured.")

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON.") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")

    messages = extract_messages_from_payload(payload)
    settings = build_chat_settings(payload)
    query_preview = extract_query_preview(messages)
    if settings["requested_model"] and settings["requested_model"] != settings["model"]:
        logger.info(
            "Ignoring requested model '%s' and using configured model '%s'.",
            settings["requested_model"],
            settings["model"],
        )
    log_chat_request_summary(query_preview, settings)
    log_chat_request_system_prompts(payload, messages)

    started_at = time.perf_counter()
    try:
        result = await asyncio.to_thread(run_messages, request.app.state.client, messages, settings)
    except Exception as exc:
        logger.exception("Nemotron chat completion failed.")
        detail = str(exc).strip() or exc.__class__.__name__
        raise HTTPException(status_code=500, detail=detail) from exc

    latency = time.perf_counter() - started_at
    logger.info(
        "Chat completion completed in %.3fs with %d tool call(s).",
        latency,
        len(result["tool_calls"]),
    )

    if settings["stream_response"]:
        return build_streaming_chat_response(result, latency)

    return build_openai_chat_response(result, latency)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=app_settings.host, port=app_settings.port, reload=True)
