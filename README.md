# Chess Green Agent + Chess White Agent

This repository implements a two-agent chess evaluation workflow:

- **Green Agent** (evaluator/orchestrator): runs a chess game between agents, validates moves, logs traces, and computes evaluation metrics.
- **White Agent** (player): selects a legal move (UCI) given a board state (FEN + optional legal moves), optionally using an LLM with structured output and fallbacks.

In addition to the core agent implementations, the repo includes lightweight HTTP and A2A interfaces and a controller so the benchmark can also run remotely (e.g. on AgentBeats).

---

## 1. Green Agent: implementation and evaluation philosophy

**Core module:** `src/green_agent/chess_green_agent.py`

The Green Agent is designed as an *evaluation harness* rather than a chess engine:

1. **Environment-first**: the authoritative game state lives in `src/environment/chess_environment.py`. Agents only see a serialized view (FEN + minimal metadata).
2. **Move validation and robustness**: for each ply, the Green agent:
   - asks the current agent for a UCI move
   - validates legality
   - retries illegal moves (up to a small limit)
   - falls back to a random legal move if needed (to keep the game progressing)
3. **Separation of concerns**:
   - orchestration: `ChessGreenAgent.run_game`
   - game state + rules: `ChessEnvironment`
   - scoring: `src/evaluation/metrics.py` (+ optional `stockfish_evaluator.py`)
4. **Metrics as the output**: the evaluation output is a JSON object containing:
   - result (`1-0`, `0-1`, `1/2-1/2`, or `*`)
   - move-by-move log (including legality feedback and optional reasoning)
   - aggregated metrics per side (ACPL, blunders/mistakes, etc.)

### Stockfish integration (optional)

If Stockfish is available, Green can compute centipawn-loss-based metrics (ACPL). This keeps evaluation objective and comparable across agents.

---

## 2. White Agent: implementation and decision pipeline

**Core module:** `src/white_agent/agent.py`

The White Agent follows a modular pipeline and prioritizes *interpretable decisions with safe fallbacks*:

1. **Perception** (`src/white_agent/perception.py`):
   - parses `fen` into a `python-chess` board
   - derives lightweight features (material balance, center control, captures, etc.)
2. **Memory** (`src/white_agent/memory.py`):
   - stores recent moves and simple opponent-style heuristics
   - provides compact context for prompting (recent move history + opponent summary)
3. **Reasoning** (`src/white_agent/reasoning.py`):
   - generates a small set of candidate legal moves (checks/captures/center-control first)
   - assigns heuristic scores and produces a recommended move
4. **LLM decision (optional)**:
   - if `use_chain_of_thought` is enabled and an API key is available, the agent asks the LLM to pick among candidates
   - the prompt enforces a strict JSON output format: `{ "move": "...", "reasoning": "...", "confidence": ... }`
5. **Validation and fallback**:
   - the final move is checked against the legal move list
   - if invalid, the agent selects a fallback move (best remaining candidate, else random legal move)

This design makes it possible to evaluate the same White agent both as:
- a pure heuristic agent (no API key)
- an LLM-backed agent (with structured decision output and robust fallbacks)

---

## 3. How to run White agent (complete the task)

The White agent’s task: **given a board state, return a legal chess move in UCI format**.

### A) Run White as a Python class (single move)

```bash
python -c "import sys; sys.path.insert(0,'src'); from white_agent import AgentConfig, WhiteAgent; cfg=AgentConfig(api_provider='deepseek', model='deepseek-chat', use_chain_of_thought=True, timeout=60); ag=WhiteAgent(agent_id='w', agent_name='White', config=cfg); s={'fen':'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1','legal_moves':['e2e4','d2d4','g1f3','c2c4'],'move_number':1}; print(ag.get_move(s))"
```

### B) Run White as an HTTP service and call `/move`

Start White:

```bash
AGENT_ROLE=white python -m uvicorn src.server:app --host 0.0.0.0 --port 8002
```

Request a move:

```bash
curl -X POST "http://localhost:8002/move" \
  -H "Content-Type: application/json" \
  -d "{\"fen\":\"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\",\"legal_moves\":[\"e2e4\",\"d2d4\",\"g1f3\",\"c2c4\"],\"move_number\":1}"
```

---

## 4. How to run Green agent (evaluate White agents)

### A) Evaluate a White agent locally (Python-to-Python)

```python
from green_agent import ChessGreenAgent, RandomAgent, SimpleGreedyAgent

green = ChessGreenAgent(agent_id="local_green", use_stockfish=False)

white = SimpleGreedyAgent(agent_id="white", agent_name="Greedy White")
black = RandomAgent(agent_id="black", agent_name="Random Black")

result = green.run_game(white_agent=white, black_agent=black, max_moves=30)
print(result["result"], result["total_moves"])
green.close()
```

### B) Evaluate an HTTP White agent (reproducible command)

If White is exposed via HTTP (local or remote), evaluate it with:

```bash
python scripts/evaluate_http_white.py --white-url http://localhost:8002 --max-moves 30 --black greedy
```

This prints a JSON result and writes game logs under `logs/http_eval/`.

---

## 5. Test Green evaluation outputs (test cases)

### Validation examples (short, mostly deterministic)

```bash
python tests/validation_examples.py
```

### Unit/integration tests

```bash
python tests/test_environment.py
python tests/test_evaluation.py
python tests/test_complete_system.py
```

Notes:
- Some evaluation tests require Stockfish. Install Stockfish and set `STOCKFISH_PATH` if needed.

---

## 6. Reproduce baseline benchmark runs (existing benchmark)

This repo includes a simple baseline runner for quick smoke tests:

```bash
python tests/test_llm_agents.py quick
```

For a longer LLM-vs-LLM run (requires API keys):

```bash
python tests/test_llm_agents.py full
```

---

## 7. Remote deployment (AgentBeats / Cloud Run)

This repository includes a controller + proxy pattern so both Green and White can run remotely:

- A controller process exposes `/agents` and proxies requests to an internal agent instance.
- The internal agent serves `/.well-known/agent-card.json` and A2A JSON-RPC at `POST /` (used by remote assessments).

Full, step-by-step deployment notes (including the required env vars like `PUBLIC_BASE_URL` to avoid `0.0.0.0` agent-card URLs) are in:
- `AGENTBEATS_DEPLOY.md`

---

## Project layout (short)

```
src/
  green_agent/           # Green evaluator + baseline/LLM agents
  white_agent/           # White player agent implementation
  environment/           # Chess environment + models
  evaluation/            # Stockfish evaluator + metrics
  visualization/         # Report/chart generation
  green_service.py       # Optional HTTP interface (Green)
  white_service.py       # Optional HTTP interface (White)
tests/
scripts/
  evaluate_http_white.py # Evaluate an HTTP White agent via Green
```

---

## License

Apache License 2.0
