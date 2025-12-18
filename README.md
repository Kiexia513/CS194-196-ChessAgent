# Chess Agents for AgentBeats (Green Assessor + White Player)

这个仓库实现了两类可部署到 AgentBeats v2 的国际象棋 Agent（同一份代码、两次部署）：

- **Green Agent（Assessor / 评测者）**：接收评测任务，解析 `<white_agent_url>`，调用 White 的接口并跑一局对局，输出评测 summary。
- **White Agent（Participant / 参赛者）**：根据 FEN/合法走法给出下一步走子（可由 LLM 支持）。

> 两个 Agent 都通过 **AgentBeats Controller**（`agentbeats run_ctrl`）对外暴露，并且支持 **A2A JSON-RPC**（AgentBeats assessment 会用到）。

---

## 1. 快速概览

### 目录里关键入口

- `src/server.py`：根据环境变量 `AGENT_ROLE` 选择启动 green 或 white 服务
- `src/green_service.py`：Green HTTP + A2A(JSON-RPC) 服务
- `src/white_service.py`：White HTTP + A2A(JSON-RPC) 服务
- `src/a2a_handlers.py`：A2A `message/send` 的具体处理逻辑
- `run.sh`：AgentBeats controller 启动内部 agent 进程时执行
- `Procfile`：Cloud Run/平台启动 controller：`web: agentbeats run_ctrl`

### 支持的对外接口（通过 controller 代理）

Controller（对外）：
- `GET /status`
- `GET /agents`：列出内部 agent 实例（并给出 `to_agent/<id>` URL）
- `POST /agents/<id>/reset`
- `/<...>/to_agent/<id>/...`：代理到内部 agent

Green agent（被代理后，基于 `to_agent/<id>`）：
- `GET /.well-known/agent-card.json`
- `GET /healthz`
- `POST /`：A2A JSON-RPC（必须，用于 AgentBeats assessment 的 `message/send`）
- `POST /play`：手动跑一局（本地自测/调试用）

White agent（被代理后）：
- `GET /.well-known/agent-card.json`
- `GET /healthz`
- `POST /`：A2A JSON-RPC（可选，用于 A2A 方式请求 move/reset）
- `POST /reset`
- `POST /move`：输入 `{fen, legal_moves, ...}`，输出 `move_uci`

---

## 2. 环境准备

### Python 版本

由于依赖 `earthshaker`（AgentBeats runtime/controller），建议使用 **Python 3.13+**（你之前安装时也遇到过版本要求）。

### 安装依赖

```bash
pip install -r requirements.txt
```

### LLM API Key（不要写进仓库）

推荐用环境变量：
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`

可选的简单鉴权（建议线上开启）：
- `AGENT_API_KEY`：如果设置了，调用 `POST /play`、`POST /move`、`POST /reset` 需要带请求头 `X-API-Key: <AGENT_API_KEY>`

本地开发也可创建 `src/api/api.txt`（已在 `.gitignore` 中忽略），但不要提交真实 key。

---

## 3. 本地运行（controller + 内部 agent）

```bash
agentbeats run_ctrl
```

打开 controller 页面：`http://localhost:8010/info`  
拿到内部 agent 的 ID：

```powershell
Invoke-WebRequest -Uri "http://localhost:8010/agents"
```

然后用 `to_agent/<id>` 访问内部 agent：
- `GET http://localhost:8010/to_agent/<id>/.well-known/agent-card.json`
- `GET http://localhost:8010/to_agent/<id>/healthz`

---

## 4. Cloud Run 部署（同一仓库部署两次）

你需要部署两个 Cloud Run service：

- `chess-green-agent`：`AGENT_ROLE=green`
- `chess-white-agent`：`AGENT_ROLE=white`

### 4.1 部署（build from source）

```bash
gcloud run deploy chess-green-agent --source . --allow-unauthenticated --port 8010 --region us-central1
gcloud run deploy chess-white-agent --source . --allow-unauthenticated --port 8010 --region us-central1
```

PowerShell 版本（Windows）：

```powershell
gcloud.cmd run deploy chess-green-agent --source . --allow-unauthenticated --port 8010 --region us-central1
gcloud.cmd run deploy chess-white-agent --source . --allow-unauthenticated --port 8010 --region us-central1
```

### 4.2 设置关键环境变量（非常重要）

把 `<...-service-url-host>` 替换成 Cloud Run 的域名（不含 `https://`），例如：
`chess-green-agent-903107533568.us-central1.run.app`

**Green：**
```bash
gcloud run services update chess-green-agent --region us-central1 \
  --set-env-vars AGENT_ROLE=green \
  --set-env-vars PUBLIC_BASE_URL=https://<green-service-url-host> \
  --set-env-vars CLOUDRUN_HOST=<green-service-url-host> \
  --set-env-vars HTTPS_ENABLED=true
```

PowerShell 版本（Windows）：

```powershell
gcloud.cmd run services update chess-green-agent --region us-central1 `
  --set-env-vars AGENT_ROLE=green `
  --set-env-vars PUBLIC_BASE_URL=https://<green-service-url-host> `
  --set-env-vars CLOUDRUN_HOST=<green-service-url-host> `
  --set-env-vars HTTPS_ENABLED=true
```

**White：**
```bash
gcloud run services update chess-white-agent --region us-central1 \
  --set-env-vars AGENT_ROLE=white \
  --set-env-vars PUBLIC_BASE_URL=https://<white-service-url-host> \
  --set-env-vars CLOUDRUN_HOST=<white-service-url-host> \
  --set-env-vars HTTPS_ENABLED=true
```

PowerShell 版本（Windows）：

```powershell
gcloud.cmd run services update chess-white-agent --region us-central1 `
  --set-env-vars AGENT_ROLE=white `
  --set-env-vars PUBLIC_BASE_URL=https://<white-service-url-host> `
  --set-env-vars CLOUDRUN_HOST=<white-service-url-host> `
  --set-env-vars HTTPS_ENABLED=true
```

> 为什么 `PUBLIC_BASE_URL` 必须设置：AgentBeats assessment 会读取 agent-card.json 里的 `url` 字段并对这个 URL 发起 A2A JSON-RPC；如果 `url` 变成 `0.0.0.0`/`localhost`，远端 runner 会连接失败（你之前的 503 就是这个原因）。

### 4.3（建议）为 assessment 稳定性调参

```bash
gcloud run services update chess-green-agent --region us-central1 --min-instances 1 --cpu 1 --memory 1Gi --timeout 3600 --concurrency 1
gcloud run services update chess-white-agent --region us-central1 --min-instances 1 --cpu 1 --memory 1Gi --timeout 3600 --concurrency 1
```

PowerShell 版本（Windows）：

```powershell
gcloud.cmd run services update chess-green-agent --region us-central1 --min-instances 1 --cpu 1 --memory 1Gi --timeout 3600 --concurrency 1
gcloud.cmd run services update chess-white-agent --region us-central1 --min-instances 1 --cpu 1 --memory 1Gi --timeout 3600 --concurrency 1
```

---

## 5. 在 AgentBeats v2 上创建 Assessment

1. 在 AgentBeats 平台分别注册 **两个 controller URL**（green 的 Cloud Run URL、white 的 Cloud Run URL）
2. 确认两边的 agent check 都能加载到 agent card
3. 创建 assessment：选择 Green 为 assessor，White 为 participant

---

## 6. White Agent 配置（LLM）

White agent 的 LLM 由以下环境变量控制（Cloud Run 上建议配置）：

- `WHITE_API_PROVIDER`：默认 `deepseek`（可选 `openai` / `google`）
- `WHITE_MODEL`：默认 `deepseek-chat`
- `WHITE_USE_COT`：`true/false`（默认 `true`）
- `WHITE_TIMEOUT`：默认 `60`（单步超时，单位秒）

---

## 7. Green 评测参数（可选）

Green 在 A2A assessment 模式下，会读取：

- `ASSESSMENT_MAX_MOVES`：默认 `20`
- `ASSESSMENT_BLACK_AGENT`：`greedy`（默认）或 `random`
- `ASSESSMENT_REMOTE_TIMEOUT`：调用远端 white `/move` 的超时（默认 `60`）
- `ASSESSMENT_USE_STOCKFISH`：是否用 stockfish（默认 `false`，Cloud Run 上通常不带 stockfish）

---

## 8. 常见问题排查

### 8.1 AgentBeats assessment 报 404

多半是 A2A JSON-RPC 路由缺失或路径不对。AgentBeats 会对 `agent-card.json` 里 `url` 对应的地址 `POST /`（JSON-RPC）。

### 8.2 assessment 报 503 “All connection attempts failed”

几乎都是因为 agent card 的 `url` 指向了不可从外网访问的地址（例如 `http://0.0.0.0:8010/...`）。

检查：
```powershell
$green = "https://<green-service-url>"
$gid = (Invoke-WebRequest -Uri "$green/agents" | ConvertFrom-Json).psobject.Properties.Name | Select-Object -First 1
(Invoke-WebRequest -Uri "$green/to_agent/$gid/.well-known/agent-card.json" | ConvertFrom-Json).url
```

确保返回的是 `https://<green-service-url>/to_agent/<id>`。

---

## 9. 项目结构（简版）

```
src/
  server.py              # 入口：AGENT_ROLE=green/white
  green_service.py       # Green HTTP + A2A(JSON-RPC)
  white_service.py       # White HTTP + A2A(JSON-RPC)
  a2a_handlers.py        # A2A message/send 实现（green/white）
  green_agent/           # 评测与对局逻辑（Stockfish 可选）
  white_agent/           # White agent（LLM-backed）实现
tests/
run.sh                   # controller 启动内部 agent 时执行
Procfile                 # Cloud Run 启动 controller
```

---

## License

Apache License 2.0
