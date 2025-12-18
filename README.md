# Chess Agents for AgentBeats (Green Assessor + White Player)

This repository implements two chess agents that can be deployed to the **AgentBeats v2** platform **from the same codebase** (deploy twice with different environment variables):

- **Green Agent (Assessor)**: receives an assessment task, parses `<white_agent_url>...</white_agent_url>`, calls the White agent endpoints, runs a game, and returns an assessment summary.
- **White Agent (Participant)**: given a position (FEN + optional legal moves), returns the next move (LLM-backed).

Both agents are exposed through the **AgentBeats Controller** (`agentbeats run_ctrl`) and support **A2A JSON-RPC** (required by AgentBeats assessments).

---

## 1. Overview

### Key entrypoints

- `src/server.py`: selects Green vs White based on `AGENT_ROLE`
- `src/green_service.py`: Green HTTP service + A2A(JSON-RPC)
- `src/white_service.py`: White HTTP service + A2A(JSON-RPC)
- `src/a2a_handlers.py`: A2A `message/send` handler implementations
- `run.sh`: executed by the AgentBeats controller to start the internal agent process
- `Procfile`: starts the controller on Cloud Run (`web: agentbeats run_ctrl`)

### Public endpoints (via controller proxy)

Controller (public):
- `GET /status`
- `GET /agents` (lists internal agents and their `to_agent/<id>` URLs)
- `POST /agents/<id>/reset`
- `/<...>/to_agent/<id>/...` (reverse proxy to the internal agent)

Green agent (behind `to_agent/<id>`):
- `GET /.well-known/agent-card.json`
- `GET /healthz`
- `POST /` (A2A JSON-RPC, required for AgentBeats assessment `message/send`)
- `POST /play` (manual/local debugging)

White agent (behind `to_agent/<id>`):
- `GET /.well-known/agent-card.json`
- `GET /healthz`
- `POST /` (A2A JSON-RPC, optional)
- `POST /reset`
- `POST /move` (input `{fen, legal_moves, ...}` → output `move_uci`)

---

## 2. Requirements

### Python version

This repo depends on `earthshaker` (AgentBeats runtime/controller). Use **Python 3.13+**.

### Install dependencies

```bash
pip install -r requirements.txt
```

### LLM API keys (do not commit secrets)

Use environment variables:
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`

Optional simple auth (recommended for public deployments):
- `AGENT_API_KEY`: if set, `POST /play`, `POST /move`, `POST /reset` require header `X-API-Key: <AGENT_API_KEY>`

For local-only development you can create `src/api/api.txt` (ignored by git), but do not commit real keys.

---

## 3. Run locally (controller + internal agent)

```bash
agentbeats run_ctrl
```

Open the controller UI: `http://localhost:8010/info`

Get the internal agent ID:

```powershell
Invoke-WebRequest -Uri "http://localhost:8010/agents"
```

Then access the internal agent via `to_agent/<id>`:
- `GET http://localhost:8010/to_agent/<id>/.well-known/agent-card.json`
- `GET http://localhost:8010/to_agent/<id>/healthz`

---

## 4. Deploy to Cloud Run (deploy twice from the same repo)

You will deploy two Cloud Run services:

- `chess-green-agent`: `AGENT_ROLE=green`
- `chess-white-agent`: `AGENT_ROLE=white`

### 4.1 Deploy (build from source)

```bash
gcloud run deploy chess-green-agent --source . --allow-unauthenticated --port 8010 --region us-central1
gcloud run deploy chess-white-agent --source . --allow-unauthenticated --port 8010 --region us-central1
```

PowerShell (Windows):

```powershell
gcloud.cmd run deploy chess-green-agent --source . --allow-unauthenticated --port 8010 --region us-central1
gcloud.cmd run deploy chess-white-agent --source . --allow-unauthenticated --port 8010 --region us-central1
```

### 4.2 Set required env vars (critical)

Replace `<...-service-url-host>` with your Cloud Run hostname (without `https://`), for example:
`chess-green-agent-903107533568.us-central1.run.app`

**Green:**
```bash
gcloud run services update chess-green-agent --region us-central1 \
  --set-env-vars AGENT_ROLE=green \
  --set-env-vars PUBLIC_BASE_URL=https://<green-service-url-host> \
  --set-env-vars CLOUDRUN_HOST=<green-service-url-host> \
  --set-env-vars HTTPS_ENABLED=true
```

PowerShell (Windows):

```powershell
gcloud.cmd run services update chess-green-agent --region us-central1 `
  --set-env-vars AGENT_ROLE=green `
  --set-env-vars PUBLIC_BASE_URL=https://<green-service-url-host> `
  --set-env-vars CLOUDRUN_HOST=<green-service-url-host> `
  --set-env-vars HTTPS_ENABLED=true
```

**White:**
```bash
gcloud run services update chess-white-agent --region us-central1 \
  --set-env-vars AGENT_ROLE=white \
  --set-env-vars PUBLIC_BASE_URL=https://<white-service-url-host> \
  --set-env-vars CLOUDRUN_HOST=<white-service-url-host> \
  --set-env-vars HTTPS_ENABLED=true
```

PowerShell (Windows):

```powershell
gcloud.cmd run services update chess-white-agent --region us-central1 `
  --set-env-vars AGENT_ROLE=white `
  --set-env-vars PUBLIC_BASE_URL=https://<white-service-url-host> `
  --set-env-vars CLOUDRUN_HOST=<white-service-url-host> `
  --set-env-vars HTTPS_ENABLED=true
```

Why `PUBLIC_BASE_URL` matters: AgentBeats assessments read `/.well-known/agent-card.json` and use the `url` field as the A2A JSON-RPC base URL. If it becomes `0.0.0.0`/`localhost`, remote runners will fail to connect (503 connect errors).

### 4.3 Recommended stability settings (assessment-friendly)

```bash
gcloud run services update chess-green-agent --region us-central1 --min-instances 1 --cpu 1 --memory 1Gi --timeout 3600 --concurrency 1
gcloud run services update chess-white-agent --region us-central1 --min-instances 1 --cpu 1 --memory 1Gi --timeout 3600 --concurrency 1
```

PowerShell (Windows):

```powershell
gcloud.cmd run services update chess-green-agent --region us-central1 --min-instances 1 --cpu 1 --memory 1Gi --timeout 3600 --concurrency 1
gcloud.cmd run services update chess-white-agent --region us-central1 --min-instances 1 --cpu 1 --memory 1Gi --timeout 3600 --concurrency 1
```

---

## 5. Create an assessment on AgentBeats v2

1. Register both **controller URLs** on AgentBeats (the Green Cloud Run URL and the White Cloud Run URL).
2. Ensure both agents show a successful agent check and a valid agent card.
3. Create an assessment selecting Green as the **assessor** and White as the **participant**.

---

## 6. White Agent configuration (LLM)

Configure the White agent using environment variables (recommended on Cloud Run):

- `WHITE_API_PROVIDER`: default `deepseek` (or `openai` / `google`)
- `WHITE_MODEL`: default `deepseek-chat`
- `WHITE_USE_COT`: `true/false` (default `true`)
- `WHITE_TIMEOUT`: default `60` (seconds)

---

## 7. Green assessment settings (optional)

The Green A2A assessor supports:

- `ASSESSMENT_MAX_MOVES` (default `20`)
- `ASSESSMENT_BLACK_AGENT`: `greedy` (default) or `random`
- `ASSESSMENT_REMOTE_TIMEOUT` (default `60`) timeout for remote White `/move`
- `ASSESSMENT_USE_STOCKFISH`: default `false` (Cloud Run usually does not include Stockfish)

---

## 8. Troubleshooting

### 8.1 Assessment returns 404

AgentBeats sends A2A JSON-RPC to `POST /` at the agent base URL (from the agent card `url`). Make sure the service exposes A2A JSON-RPC at the root path.

### 8.2 Assessment returns 503 “All connection attempts failed”

This almost always means the agent card `url` is not reachable from the internet (e.g. `http://0.0.0.0:8010/...`).

Check:
```powershell
$green = "https://<green-service-url>"
$gid = (Invoke-WebRequest -Uri "$green/agents" | ConvertFrom-Json).psobject.Properties.Name | Select-Object -First 1
(Invoke-WebRequest -Uri "$green/to_agent/$gid/.well-known/agent-card.json" | ConvertFrom-Json).url
```

Make sure it returns `https://<green-service-url>/to_agent/<id>`.

---

## 9. Project layout (short)

```
src/
  server.py              # entrypoint: AGENT_ROLE=green/white
  green_service.py       # Green HTTP + A2A(JSON-RPC)
  white_service.py       # White HTTP + A2A(JSON-RPC)
  a2a_handlers.py        # A2A message/send handlers (green/white)
  green_agent/           # evaluation + game orchestration
  white_agent/           # White agent (LLM-backed)
tests/
run.sh                   # internal agent launcher (used by controller)
Procfile                 # controller entrypoint for Cloud Run
```

---

## License

Apache License 2.0
