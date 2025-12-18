# Chess Green Agent - LLM Chess Evaluation System

**LLM Agent Evaluations Project for Berkeley CS194 - Unit 3**

A comprehensive evaluation framework for assessing Large Language Model (LLM) agents' chess-playing capabilities using objective metrics and professional chess engine analysis.

## 🎯 What is a Green Agent?

The **Green Agent** acts as an evaluator and orchestrator, responsible for:
- 🎮 Setting up chess game environments
- 📋 Distributing tasks to participant agents (LLM agents)
- 📊 Collecting and analyzing game results
- ✅ Validating environment correctness
- 📈 Reporting evaluation metrics

## 📊 Project Status

- ✅ **Step 1**: Task Selection - Chess Game Evaluation
- ✅ **Step 2**: Environment Design - Tools, actions, and feedback mechanisms
- ✅ **Step 3**: Evaluation Metrics - Stockfish integration and ACPL calculation
- ✅ **Step 4**: Green Agent Core Logic - Game orchestration and LLM agent integration
- ✅ **Step 5**: Logging and Visualization System - HTML reports, charts, and game replay
- ✅ **Step 6**: A2A + AgentBeats Controller Integration
- ⏳ **Step 7**: Testing and Optimization

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd project

# Install dependencies
pip install -r requirements.txt
```

**Required Python Version**: 3.10 or higher

### 2. Install Stockfish (Optional but Recommended)

Stockfish is used for objective move quality evaluation and ACPL (Average Centipawn Loss) calculation.

**Download**: https://stockfishchess.org/download/

Extract and place in `engines/` directory or add to system `PATH`.

This repo will auto-detect Stockfish in the following order:
1. `STOCKFISH_PATH` / `STOCKFISH_BINARY` environment variable
2. A local binary under `engines/`
3. `stockfish` on `PATH`

### 3. Configure API Keys

For local development you can create `src/api/api.txt` with your LLM API keys (this file is ignored by git):

```
deepseek: YOUR_DEEPSEEK_API_KEY
openai: YOUR_OPENAI_API_KEY
google: YOUR_GOOGLE_API_KEY
```

Recommended (especially for deployment): use environment variables instead:
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`

## 🎛️ AgentBeats Deployment (Green + White)

This repo can be deployed to AgentBeats v2 as **two separate remote agents** (two Cloud Run services), using the same codebase:
- **Green (assessor)**: `AGENT_ROLE=green` (default) → exposes `POST /play`
- **White (participant)**: `AGENT_ROLE=white` → exposes `POST /move`

Both deployments are managed by the AgentBeats controller (`agentbeats run_ctrl`) and must expose an A2A Agent Card at `/.well-known/agent-card.json`.
AgentBeats assessments also send A2A JSON-RPC requests to the **agent base URL** (the `url` field in the agent card), so this repo exposes an A2A JSON-RPC endpoint at `POST /` (required for remote assessments).

### Key Environment Variables

- `AGENT_ROLE`: `green` or `white`
- `CLOUDRUN_HOST`: set to your Cloud Run hostname (without `https://`) so AgentBeats can load agent URLs (avoids `0.0.0.0` URLs)
- `HTTPS_ENABLED`: set to `true` on Cloud Run
- `AGENT_API_KEY` (optional but recommended): if set, requests to `/play` and `/move` require header `X-API-Key`
- `ASSESSMENT_MAX_MOVES` (green, optional): max moves per assessment game (default: `20`)
- `ASSESSMENT_BLACK_AGENT` (green, optional): `greedy` (default) or `random`
- `ASSESSMENT_REMOTE_TIMEOUT` (green, optional): seconds for each remote `/move` call (default: `60`)

### Local: Run Controller

```bash
pip install -r requirements.txt
agentbeats run_ctrl
```

Then access the controller UI at `http://localhost:8010`, and use the proxy URL:
- `GET http://localhost:8010/to_agent/<id>/.well-known/agent-card.json`
- `GET http://localhost:8010/to_agent/<id>/healthz`

### Cloud Run: Deploy Green (Assessor)

```bash
gcloud run deploy chess-green-agent --source . --allow-unauthenticated --port 8010 --region us-central1
gcloud run services update chess-green-agent --region us-central1 \
  --set-env-vars AGENT_ROLE=green \
  --set-env-vars CLOUDRUN_HOST=<your-green-hostname> \
  --set-env-vars HTTPS_ENABLED=true
```

### Cloud Run: Deploy White (Participant)

```bash
gcloud run deploy chess-white-agent --source . --allow-unauthenticated --port 8010 --region us-central1
gcloud run services update chess-white-agent --region us-central1 \
  --set-env-vars AGENT_ROLE=white \
  --set-env-vars CLOUDRUN_HOST=<your-white-hostname> \
  --set-env-vars HTTPS_ENABLED=true
```

Register both controller URLs on AgentBeats v2, then create an assessment selecting:
1) your Green (assessor) agent, and 2) your White (participant) agent.

### 4. Run Tests

```bash
# Test environment
python tests/test_environment.py

# Test evaluation system (requires Stockfish)
python tests/test_evaluation.py

# Test LLM agents
python tests/test_llm_agents.py single

# Complete system test
python tests/test_complete_system.py

# Full LLM vs LLM game
python tests/test_llm_agents.py full

# Manual validation: run 3 example test cases and print evaluation summaries
python tests/validation_examples.py
```

## 🏗️ Project Structure

```
project/
├── docs/                           # Documentation
│   ├── environment_design.md       # Environment design specification
│   ├── METRICS_DESIGN.md          # Evaluation metrics design
│   ├── EVALUATION_SYSTEM.md       # Evaluation system usage guide
│   └── VISUALIZATION_GUIDE.md     # Visualization system guide
├── src/                           # Source code
│   ├── environment/               # Chess game environment
│   │   ├── chess_environment.py   # Core chess environment
│   │   └── models.py              # Data models (Pydantic)
│   ├── evaluation/                # Evaluation system
│   │   ├── metrics.py             # Metrics (ACPL, move quality)
│   │   └── stockfish_evaluator.py # Stockfish engine integration
│   ├── green_agent/               # Green Agent implementation
│   │   ├── chess_green_agent.py   # Main orchestrator
│   │   ├── llm_agents.py          # LLM agent implementations
│   │   ├── sample_agents.py       # Sample agents (Random, Greedy)
│   │   └── agent_interface.py     # Agent interface definition
│   ├── visualization/             # Visualization system
│   │   ├── html_reporter.py       # HTML game reports
│   │   ├── chart_generator.py     # Analytics charts
│   │   ├── game_replay.py         # Interactive game replay
│   │   └── chess_board_renderer.py # Graphical board rendering
│   ├── config/                    # Configuration
│   │   ├── const.py               # Constants and thresholds
│   │   └── api_config.py          # API configuration
│   ├── white_agent/               # White Agent implementation (participant agent)
│   ├── green_service.py           # Green HTTP service (AgentBeats)
│   ├── white_service.py           # White HTTP service (AgentBeats)
│   └── server.py                  # Role-based entrypoint (AGENT_ROLE)
│   └── api/                       # API keys (not in repo)
│       └── api.txt                # API keys file
├── tests/                         # Test suite
│   ├── test_environment.py        # Environment tests
│   ├── test_evaluation.py         # Evaluation system tests
│   ├── test_llm_agents.py         # LLM agent tests
│   ├── test_complete_system.py    # End-to-end system tests
│   └── test_visualization.py      # Visualization tests
├── logs/                          # Game logs (auto-generated)
│   └── */                         # Organized by test run
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🎮 Environment Design

### Available Tools

1. **get_board_state** - Get current board state (FEN, legal moves)
2. **make_move** - Execute a move (UCI or SAN format)
3. **get_legal_moves** - Get all legal moves
4. **get_move_history** - View game history
5. **check_rules** - Query chess rules
6. **analyze_position** - Analyze current position
7. **offer_draw** - Propose a draw
8. **resign** - Resign the game

### Supported Actions

- `QUERY_STATE` - Query game state
- `MAKE_MOVE` - Make a chess move
- `GET_MOVES` - Get legal moves
- `VIEW_HISTORY` - View move history
- `CHECK_RULES` - Query rules
- `ANALYZE` - Analyze position
- `OFFER_DRAW` - Offer draw
- `RESIGN` - Resign game

### Feedback Types

- `move_success` - Move executed successfully
- `move_error` - Move failed (illegal, invalid format)
- `opponent_moved` - Opponent made a move
- `game_over` - Game ended (checkmate, stalemate, draw)
- `check_warning` - King is in check
- `time_warning` - Time running low
- `protocol_violation` - Protocol error

See `docs/environment_design.md` for detailed specifications.

## 📊 Evaluation Metrics

### Core Metrics

1. **ACPL (Average Centipawn Loss)**
   - Gold standard for chess skill measurement
   - Objective and quantifiable
   - Correlates with human ELO ratings
   - **< 10**: Super Grandmaster (2700+ ELO)
   - **10-20**: Grandmaster (2500-2700 ELO)
   - **20-30**: International Master (2400-2500 ELO)
   - **30-50**: Expert (2200-2400 ELO)
   - **50-100**: Advanced (1800-2200 ELO)
   - **100-200**: Intermediate (1400-1800 ELO)
   - **200+**: Beginner (<1400 ELO)

2. **Move Quality Classification**
   - **Best** (0 cp loss) - Engine's top choice
   - **Excellent** (≤10 cp loss) - Strong move
   - **Good** (10-25 cp loss) - Solid move
   - **Inaccuracy** (25-50 cp loss) - Suboptimal
   - **Mistake** (50-100 cp loss) - Poor move
   - **Blunder** (>100 cp loss) - Major error
   - **Catastrophic** (>300 cp loss) - Game-losing

3. **Tactical Statistics**
   - Blunders, mistakes, and inaccuracies count
   - Best and excellent move percentage
   - Tactical opportunity recognition

4. **Phase Performance**
   - **Opening** (moves 1-10): Development and control
   - **Middlegame** (moves 11-30): Strategy and tactics
   - **Endgame** (move 31+): Technique and precision

### Usage Example

```python
from green_agent import ChessGreenAgent, DeepSeekAgent, ChatGPTAgent

# Create Green Agent
green_agent = ChessGreenAgent(
    agent_id="evaluator",
    use_stockfish=True,
    log_dir="logs/games"
)

# Create LLM agents
agent_white = DeepSeekAgent(
    agent_id="deepseek",
    agent_name="DeepSeek Reasoner",
    model="deepseek-reasoner"
)

agent_black = ChatGPTAgent(
    agent_id="chatgpt",
    agent_name="ChatGPT",
    model="gpt-4o-mini"
)

# Run game
results = green_agent.run_game(
    white_agent=agent_white,
    black_agent=agent_black,
    game_id="game_001",
    max_moves=50
)

# Results include:
# - Game outcome (1-0, 0-1, 1/2-1/2)
# - Complete move history
# - ACPL for both players
# - Estimated ELO ratings
# - Move quality breakdown
# - Phase-specific performance
# - HTML report and game replay
```

## 🎨 Visualization System

### Features

1. **HTML Game Reports**
   - Player statistics and metrics
   - Move-by-move analysis
   - Interactive charts
   - Professional formatting

2. **Analytics Charts**
   - ACPL trend over time
   - Move quality distribution
   - Thinking time analysis
   - Phase comparison

3. **Interactive Game Replay**
   - Graphical chess board (Unicode pieces)
   - Move navigation (prev/next/first/last)
   - Move annotations and quality indicators
   - Stockfish evaluation display
   - Responsive design

### Output Files

All generated automatically after each game:
- `logs/{game_id}.json` - Complete game log
- `logs/{game_id}_report.html` - HTML analysis report
- `logs/charts/{game_id}_*.png` - Analytics charts
- `logs/{game_id}_replay.html` - Interactive game replay

See `docs/VISUALIZATION_GUIDE.md` for detailed usage.

## 🤖 Supported LLM Agents

### Implemented Agents

1. **DeepSeek** (`deepseek-reasoner` or `deepseek-chat`)
   - API: https://api.deepseek.com
   - Reasoning model for deep analysis (3-4 min/move)
   - Chat model for faster responses (~30s/move)

2. **ChatGPT** (`gpt-4o-mini`, `gpt-4o`)
   - API: OpenAI
   - Fast and reliable (~10-20s/move)

3. **Google Gemini** (`gemini-pro`)
   - API: Google AI
   - Good balance of speed and quality

### Sample Agents

- **RandomAgent**: Selects random legal moves
- **SimpleGreedyAgent**: Prioritizes captures and checks

### Configuration

**API Settings** (`src/config/api_config.py`):
- `DEFAULT_TIMEOUT`: 180 seconds (3 minutes for reasoning models)
- `DEFAULT_MAX_TOKENS`: 4096 (allows detailed reasoning output)
- `DEFAULT_TEMPERATURE`: 0.3 (focused, deterministic play)

**Model Selection**:
- Use `deepseek-reasoner` for best play quality (slow)
- Use `deepseek-chat` or `gpt-4o-mini` for faster testing
- Customize via agent initialization parameters

## 🧪 Testing

### Test Modes

```bash
# Quick single move test
python tests/test_llm_agents.py single

# LLM vs Random (fast, 30 moves)
python tests/test_llm_agents.py quick

# LLM vs LLM (full game, 50 moves)
python tests/test_llm_agents.py full

# Complete system test (adapts to available APIs)
python tests/test_complete_system.py
```

### Test Coverage

- ✅ Environment operations
- ✅ Agent creation and move generation
- ✅ Green Agent orchestration
- ✅ Stockfish evaluation (if available)
- ✅ Visualization generation
- ✅ Logging system
- ✅ End-to-end LLM game flow

## 📚 Documentation

- **[Environment Design](docs/environment_design.md)** - Detailed environment specification
- **[Metrics Design](docs/METRICS_DESIGN.md)** - Evaluation metrics and thresholds
- **[Evaluation System](docs/EVALUATION_SYSTEM.md)** - Using Stockfish integration
- **[Visualization Guide](docs/VISUALIZATION_GUIDE.md)** - Generating and customizing reports

## 🛠️ Technology Stack

- **Chess Engine**: python-chess (board management)
- **Evaluation Engine**: Stockfish (move analysis)
- **Data Validation**: Pydantic v2
- **LLM APIs**: DeepSeek, OpenAI, Google Gemini
- **Visualization**: Matplotlib, Plotly.js, HTML/CSS/JavaScript
- **Async Support**: aiohttp, asyncio

## 🔧 Configuration

### ACPL Thresholds

Defined in `src/config/const.py`:
- Skill level classification
- Move quality thresholds
- ACPL to ELO interpolation
- Game phase boundaries

### API Configuration

Managed in `src/config/api_config.py`:
- API endpoints and keys
- Model selections
- Timeout settings
- Token limits

## 📝 Logging

All games are automatically logged to `logs/` with:
- Complete move history with UCI and SAN notation
- Board states (FEN) after each move
- LLM reasoning and confidence
- Stockfish evaluation and CP loss
- Time spent per move
- Game result and metrics

## 🚧 Upcoming Features

- [ ] Assessment UI polish for AgentBeats v2
- [ ] Advanced testing and optimization
- [ ] Tournament mode (multiple games, statistical analysis)
- [ ] Custom evaluation profiles
- [ ] Real-time game monitoring dashboard
- [ ] Database integration for historical analysis

## 🤝 Contributing

This is a course project for Berkeley CS194. Contributions and suggestions are welcome!

## 📖 References

- [Game Arena (Google DeepMind)](https://github.com/google-deepmind/game_arena) - Inspiration for design
- [python-chess Documentation](https://python-chess.readthedocs.io/) - Chess engine library
- [Stockfish](https://stockfishchess.org/) - World's strongest chess engine
- Course Materials: `LLM Agent Evaluations & Project Overview.pdf`

## 📄 License

Apache License 2.0

---
