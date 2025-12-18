# Deploy to AgentBeats (LLM-enabled)

This repo exposes a controller-managed A2A HTTP agent via `agentbeats run_ctrl` + `run.sh`.

It can run in two modes from the same codebase (deploy the same source twice with different env vars):
- **Green (assessor)**: `AGENT_ROLE=green` (default), exposes `POST /play`
- **White (participant)**: `AGENT_ROLE=white`, exposes `POST /move`

## 1) Configure API keys (required for real LLM games)

Set at least one of these environment variables:
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`

Do **not** commit keys to the repo.

## 2) Optional protection (recommended for public deployment)

If you set `AGENT_API_KEY`, then `POST /play` (green) and `POST /move` (white) require the request header:
- `X-API-Key: <AGENT_API_KEY>`

The controller's health checks and agent card remain public.

## 3) Local run (Windows)

You already verified the controller + proxy works on your machine.

To call the agent through the controller proxy:
- `GET http://localhost:8010/to_agent/<id>/.well-known/agent-card.json`
- `GET http://localhost:8010/to_agent/<id>/healthz`
- `POST http://localhost:8010/to_agent/<id>/play` (green)
- `POST http://localhost:8010/to_agent/<id>/move` (white)

To see supported agent types:
- `GET /capabilities`

## 4) Deploy (container)

### Option A: Any Docker host

Build and run:
```bash
docker build -t chess-green-agent .
docker run -p 8010:8010 \
  -e OPENAI_API_KEY=... \
  -e AGENT_ROLE=green \
  -e AGENT_API_KEY=... \
  chess-green-agent
```

### Option B: Cloud Run (recommended)

Deploy the image to Cloud Run and set environment variables there:
- `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` / `GOOGLE_API_KEY`
- (optional) `AGENT_API_KEY`

After deployment, publish your **public controller URL** on AgentBeats.
