# Nemotron

This folder contains the Nemotron exploration project inside the parent exploration workspace. It is a minimal FastAPI service that wraps NVIDIA Nemotron through the OpenAI-compatible NVIDIA API.

## Files

- `main.py`
- `settings.py`
- `tool_features.py`
- `requirements.txt`
- `.env`
- `.env.example`
- `.venv/` (optional local virtual environment)

## What It Does

- Starts a local FastAPI server
- Exposes `POST /query` and `POST /query/chat/completions` endpoints
- Sends the query to the configured Nemotron model
- Lets Nemotron call built-in tools
- Executes those tool calls locally
- Sends the tool results back to Nemotron for the final answer
- Returns streamed reasoning, final response text, tool calls, and tool results
- Keeps tool schemas and tool logic in a separate importable Python module
- Loads runtime configuration from a dedicated `settings.py` module

## How Tool Calls Work

Each request goes through a short two-step loop:

- Nemotron sees the user message and decides whether to answer directly or emit a tool call.
- If a tool call is emitted, the backend runs that tool locally in `tool_features.py`.
- The tool result is sent back to Nemotron so it can write the final user-facing answer.

The backend also logs the first model pass, any tool calls, the local tool results, and the final generated response so the full execution flow is visible during development.

## Quick Start

1. From the repository root, move into this project folder.

```powershell
cd Nemotron
```

2. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install the dependencies.

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Create an NVIDIA API key.

- Open the NVIDIA API Catalog and navigate to the Nemotron model page.
- Click `Get API Key`.
- Sign in with an NVIDIA Developer account or create one if needed.
- Generate the key and keep it available for the `.env` file.

Reference pages:

- [NVIDIA API Catalog Quickstart](https://docs.api.nvidia.com/nim/docs/api-quickstart)
- [Nemotron 3 Super model page](https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b)

5. Copy `.env.example` to `.env` and set the NVIDIA API values.

```env
HOST=0.0.0.0
PORT=8080
NVIDIA_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://nemobot-neue-experiment.vercel.app
CORS_ALLOW_CREDENTIALS=true
```

The environment variables are loaded in `settings.py`, which exposes one shared `settings` object that `main.py` imports.

6. Start the API server.

From inside the `Nemotron/` folder:

```powershell
uvicorn main:app --host 0.0.0.0 --port 8080
```

From the repository root:

```powershell
uvicorn Nemotron.main:app --host 0.0.0.0 --port 8080
```

The API can also be started with:

```powershell
python main.py
```

Or from the repository root:

```powershell
python Nemotron\main.py
```

If the frontend runs on a different origin, add it to `CORS_ALLOW_ORIGINS` in `.env` and restart the server.

## Configuration

`settings.py` centralizes the app configuration instead of keeping environment parsing and defaults inline in `main.py`.

- Runtime values such as `HOST`, `PORT`, `NVIDIA_API_BASE`, `NVIDIA_API_KEY`, `NVIDIA_MODEL`, and the CORS settings are read from `.env`.
- Application defaults like the system prompt, temperature, `top_p`, max tokens, and reasoning budget live alongside those environment-backed settings.
- The rest of the app imports the shared `settings` instance, which keeps `main.py` focused on request handling.

## Endpoints

Swagger UI:

```text
http://127.0.0.1:8080/docs
```

Health check:

```text
http://127.0.0.1:8080/health
```

## Request Example

```powershell
curl -X POST "http://127.0.0.1:8080/query" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"Explain what a GPU does in simple terms.\"}"
```

OpenAI-style chat request:

```powershell
curl -X POST "http://127.0.0.1:8080/query/chat/completions" `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"gpt-3.5-turbo\",\"temperature\":0.67,\"max_tokens\":5000,\"top_p\":0.95,\"stream\":true,\"messages\":[{\"role\":\"system\",\"content\":\"You are an intelligent reasoning assistant.\"},{\"role\":\"user\",\"content\":\"Tell me about Hermione Jean Granger\"}]}"
```

Notes for the chat-completions route:

- It accepts OpenAI-style fields like `messages`, `temperature`, `top_p`, `max_tokens`, `stream`, `frequency_penalty`, and `presence_penalty`.
- It always uses the configured `NVIDIA_MODEL`, even if the frontend sends a different `model` value.
- If `stream` is `true`, the route returns an SSE-style chat completion stream.

## Frontend Setup

If you are using this on a frontend application like https://nemobot-neue-experiment.vercel.app/ , only fill `LLM_CHAT_COMPLETION_API_URL` with:

```env
LLM_CHAT_COMPLETION_API_KEY=
LLM_CHAT_COMPLETION_API_URL=http://localhost:8080/query
LLM_CHAT_COMPLETION_MODEL=
```

Leave `LLM_CHAT_COMPLETION_API_KEY` and `LLM_CHAT_COMPLETION_MODEL` blank.

With that setup, the frontend will automatically call the locally running `http://localhost:8080/query/chat/completions` endpoint.

## Response Shape

```json
{
  "model": "nvidia/nemotron-3-super-120b-a12b",
  "response": "final answer text",
  "reasoning": "streamed reasoning text",
  "tool_calls": [],
  "tool_results": [],
  "latency": 1.23
}
```

## Notes

- The server runs locally, while model inference is handled by the configured NVIDIA API endpoint.
- The built-in tool declarations are passed to the model using the OpenAI-compatible `tools` format.
- Tool schemas and execution helpers live in `tool_features.py`, and runtime configuration now lives in `settings.py`, so `main.py` stays focused on the FastAPI flow.
- The backend executes the built-in tools locally and feeds those results back into Nemotron before returning the final answer.
- The Harry Potter tool returns structured character profiles, and the color tool returns normalized hex, RGB, HSL, brightness, luminance, dominant channel, warmth, likely names, and a recommended text color.
