# OpenClaw API Gateway (WebSocket)

FastAPI gateway that forwards messages to a local OpenClaw Gateway over WebSocket.

## OpenClaw CLI Setup

Run OpenClaw and verify gateway:

```bash
openclaw start
openclaw doctor --generate-gateway-token
openclaw dashboard
```

Gateway endpoint:

```text
ws://127.0.0.1:18789
```

## Project Structure

```text
src/
├── main.py
├── config.py
├── api/
│   ├── agent_router.py
│   └── routes.py
├── core/
│   ├── security.py
│   └── session_manager.py
├── schemas/
│   ├── message.py
│   └── agent_response.py
└── services/
    └── openclaw_ws_client.py
```

## Environment Variables

```env
OPENCLAW_GATEWAY_URL=ws://127.0.0.1:18789
OPENCLAW_GATEWAY_TOKEN=your_token_here
OPENCLAW_WS_TIMEOUT_SECONDS=30
OPENCLAW_DEFAULT_DELIVER=false
OPENCLAW_DEFAULT_REPLY_CHANNEL=
OPENCLAW_DEFAULT_REPLY_TO=
API_KEY=devkey
```

## API

### `POST /agent/message`

Request body:

```json
{
  "user_id": "123",
  "message": "latest AI news",
  "deliver": true,
  "reply_channel": "telegram",
  "reply_to": "12345678"
}
```

Behavior:

1. FastAPI sends the message to OpenClaw Gateway via WebSocket.
2. OpenClaw generates a response.
3. Backend returns the response JSON to the API caller.
4. If `deliver=true`, OpenClaw also delivers to configured channel/target.

## Install / Run

```bash
uv sync
uv run uvicorn src.main:app --reload
```

Equivalent pip requirement:

```bash
pip install websockets
```
