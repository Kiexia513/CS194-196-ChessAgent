# Chess Agent Evaluation System

**LLM Agent Evaluations Project for Berkeley CS194 - Unit 3**

A comprehensive evaluation framework for assessing Large Language Model (LLM) agents' chess-playing capabilities using objective metrics and professional chess engine analysis.

## 🎯 Project Overview

This project implements a **two-agent evaluation system**:

- **White Agent**: The agent being tested - an LLM-based chess player with modular architecture
- **Green Agent**: The evaluator - orchestrates games, validates moves, and collects metrics

### Key Features

- 🧠 **Chain-of-Thought (CoT) reasoning** for interpretable decision-making
- 📊 **Objective evaluation** using Stockfish ACPL (Average Centipawn Loss)
- 🎮 **Standardized benchmarks** for consistent agent comparison
- 📈 **Comprehensive analytics** with HTML reports and visualizations
- 🔄 **Multiple LLM support**: DeepSeek, OpenAI, Google Gemini

## 📊 Project Status

- ✅ **Step 1**: Task Selection - Chess Game Evaluation
- ✅ **Step 2**: Environment Design - Tools, actions, and feedback mechanisms
- ✅ **Step 3**: Evaluation Metrics - Stockfish integration and ACPL calculation
- ✅ **Step 4**: Green Agent Core Logic - Game orchestration and LLM agent integration
- ✅ **Step 5**: Logging and Visualization System - HTML reports, charts, and game replay
- ✅ **Step 6**: White Agent Implementation - Modular architecture with CoT reasoning
- ✅ **Step 7**: Benchmark Suite - Standardized testing and baseline comparison

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

Stockfish is used for objective move quality evaluation.

**Download**: https://stockfishchess.org/download/

### 3. Configure API Keys

Create `src/api/api.txt` with your LLM API keys:

```
deepseek: YOUR_DEEPSEEK_API_KEY
openai: YOUR_OPENAI_API_KEY
google: YOUR_GOOGLE_API_KEY
```

### 4. Run Tests

```bash
# Quick benchmark test (recommended first run)
python tests/test_white_agent_benchmark.py --quick

# Full benchmark with all agents
python tests/test_white_agent_benchmark.py --full

# Test reasoning quality
python tests/test_white_agent_benchmark.py --reasoning

# Complete system test
python tests/test_complete_system.py
```

## 🏗️ Project Structure

```
project/
├── src/
│   ├── white_agent/            # White Agent (the agent being tested)
│   │   ├── agent.py            # Main WhiteAgent class with CoT
│   │   ├── perception.py       # Position understanding module
│   │   ├── memory.py           # Game history and context
│   │   ├── reasoning.py        # Structured decision-making
│   │   ├── analyzer.py         # Reasoning quality analysis
│   │   └── efficiency.py       # Performance tracking
│   ├── green_agent/            # Green Agent (evaluator)
│   │   ├── chess_green_agent.py # Game orchestration
│   │   ├── llm_agents.py       # LLM implementations
│   │   ├── sample_agents.py    # Baseline agents
│   │   └── agent_interface.py  # Interface definition
│   ├── environment/            # Chess environment
│   │   ├── chess_environment.py
│   │   └── models.py
│   ├── evaluation/             # Evaluation system
│   │   ├── metrics.py
│   │   └── stockfish_evaluator.py
│   ├── visualization/          # Reporting system
│   │   ├── html_reporter.py
│   │   ├── chart_generator.py
│   │   └── game_replay.py
│   └── config/                 # Configuration
├── benchmarks/                 # Benchmark suite
│   ├── positions.json          # Test positions
│   ├── benchmark.py            # Benchmark runner
│   └── evaluator.py            # Multi-agent comparison
├── tests/                      # Test suite
│   ├── test_white_agent_benchmark.py  # White agent benchmark
│   ├── test_complete_system.py        # End-to-end tests
│   └── test_llm_agents.py             # LLM agent tests
├── results/                    # Benchmark results
└── logs/                       # Game logs
```

## 🤖 White Agent Architecture

The White Agent follows **Tau-Bench principles**:
1. **Self-explanatory tasks**: Clear prompts without benchmark-specific knowledge
2. **Agent-friendly formatting**: Structured input/output formats

### Modules

```
WhiteAgent
├── PerceptionModule     # Understands board state
│   ├── Material analysis
│   ├── Center control
│   ├── King safety assessment
│   └── Position description
│
├── MemoryModule         # Maintains context
│   ├── Short-term (recent moves)
│   ├── Long-term (game patterns)
│   └── Opponent style tracking
│
├── ReasoningModule      # Structured decision-making
│   ├── Candidate generation
│   ├── Pros/cons analysis
│   ├── Move scoring
│   └── Selection reasoning
│
└── LLM Interface        # Final decision
    ├── Self-explanatory prompts
    ├── JSON response parsing
    └── Fallback handling
```

### Decision Pipeline

```
Input: Board State (FEN)
    ↓
[1. Perception] Analyze position, count material, assess safety
    ↓
[2. Memory] Retrieve game history, opponent patterns
    ↓
[3. Reasoning] Generate candidates, analyze each, score moves
    ↓
[4. LLM Decision] Chain-of-thought prompt, get final choice
    ↓
Output: Move (UCI) + Confidence + Reasoning
```

## 📊 Benchmark Suite

### Test Categories

| Category | Positions | Description |
|----------|-----------|-------------|
| Opening | 3 | Standard opening knowledge |
| Tactical | 3 | Tactical pattern recognition |
| Endgame | 3 | Endgame technique |
| Defensive | 2 | Defensive skills |
| Complex | 2 | Complex middlegame decisions |

### Evaluation Metrics

1. **Accuracy**: Percentage of "good" moves (expected moves)
2. **ACPL**: Average Centipawn Loss (with Stockfish)
3. **Thinking Time**: Average time per move
4. **Confidence**: Agent's self-reported confidence
5. **Reasoning Quality**: Coherence and completeness scores

### Running Benchmarks

```python
from white_agent import WhiteAgent, AgentConfig
from benchmarks import ChessBenchmark, BenchmarkEvaluator

# Create agent
config = AgentConfig(
    api_provider="deepseek",
    model="deepseek-chat",
    use_chain_of_thought=True
)
agent = WhiteAgent(config=config)

# Run benchmark
benchmark = ChessBenchmark()
result = benchmark.evaluate_agent(agent, verbose=True)

# View results
print(f"Accuracy: {result.accuracy * 100:.1f}%")
print(f"Avg Time: {result.avg_thinking_time:.2f}s")
```

### Baseline Comparison

```bash
# Compare White Agent against baselines
python tests/test_white_agent_benchmark.py --full
```

**Baselines**:
- RandomAgent: Random legal moves
- SimpleGreedyAgent: Captures and checks priority
- LLM Baseline: Basic LLM without CoT

## 📈 Evaluation Metrics

### ACPL (Average Centipawn Loss)

| ACPL Range | Skill Level | ELO Estimate |
|------------|-------------|--------------|
| < 10 | Super Grandmaster | 2700+ |
| 10-20 | Grandmaster | 2500-2700 |
| 20-30 | International Master | 2400-2500 |
| 30-50 | Expert | 2200-2400 |
| 50-100 | Advanced | 1800-2200 |
| 100-200 | Intermediate | 1400-1800 |
| 200+ | Beginner | <1400 |

### Move Quality Classification

- **Best** (0 cp loss) - Engine's top choice
- **Excellent** (≤10 cp) - Strong move
- **Good** (10-25 cp) - Solid move
- **Inaccuracy** (25-50 cp) - Suboptimal
- **Mistake** (50-100 cp) - Poor move
- **Blunder** (>100 cp) - Major error

## 🎨 Visualization

### Generated Outputs

- `results/benchmark/*.json` - Benchmark results
- `results/comparison_report.txt` - Agent comparison
- `logs/{game_id}.json` - Complete game log
- `logs/{game_id}_report.html` - HTML analysis
- `logs/{game_id}_replay.html` - Interactive replay

### Game Replay Features

- Graphical chess board (Unicode pieces)
- Move navigation controls
- Quality indicators per move
- Stockfish evaluation display

## 🧪 Testing

### Test Commands

```bash
# Quick single move test
python tests/test_llm_agents.py single

# White Agent benchmark (quick)
python tests/test_white_agent_benchmark.py --quick

# White Agent benchmark (full)
python tests/test_white_agent_benchmark.py --full

# Reasoning quality test
python tests/test_white_agent_benchmark.py --reasoning

# Complete system test
python tests/test_complete_system.py
```

### Test Coverage

- ✅ White Agent modules (perception, memory, reasoning)
- ✅ Benchmark suite execution
- ✅ Baseline agent comparison
- ✅ Reasoning quality analysis
- ✅ Efficiency tracking
- ✅ Environment operations
- ✅ Stockfish evaluation
- ✅ Visualization generation

## 🔧 Configuration

### Agent Configuration

```python
from white_agent import AgentConfig

config = AgentConfig(
    api_provider="deepseek",      # "deepseek", "openai", "google"
    model="deepseek-chat",        # Model name
    temperature=0.3,              # Randomness (0-1)
    max_tokens=2048,              # Max response length
    timeout=60,                   # API timeout (seconds)
    use_chain_of_thought=True,    # Enable CoT reasoning
    max_candidates=5,             # Candidates to analyze
    short_term_memory_size=10,    # Recent moves to remember
    use_random_fallback=True      # Use random on failure
)
```

### Supported Models

| Provider | Models | Notes |
|----------|--------|-------|
| DeepSeek | `deepseek-chat`, `deepseek-reasoner` | Reasoner is slower but higher quality |
| OpenAI | `gpt-4o-mini`, `gpt-4o` | Fast and reliable |
| Google | `gemini-pro` | Good balance |

## 📚 Assignment Questions Coverage

### Q6: Abstract
The White Agent is tested on **chess move selection tasks** across various position types (opening, tactical, endgame, defensive, complex).

### Q7.1: Agent Framework Design
- **Architecture**: Modular (Perception → Memory → Reasoning → LLM)
- **Decision Pipeline**: Board state → Position analysis → Candidate generation → CoT reasoning → Move selection
- **Modules**: Perception, Memory, Reasoning, Efficiency Tracker, Reasoning Analyzer

### Q7.2: Data & Evaluation Design
- **Tasks**: 13 standardized test positions across 5 categories
- **Metrics**: Accuracy, ACPL, thinking time, confidence, reasoning quality
- **Prompts**: Self-explanatory format with multiple-choice candidates

### Q8.1: Performance vs Baselines
- Compared against: RandomAgent, SimpleGreedyAgent, Basic LLM
- Key improvements: CoT reasoning, structured analysis, candidate comparison

### Q8.2: Generalizability
- Tested across different position types (opening, tactical, endgame)
- Tested with different difficulty levels (easy, medium, hard)

### Q8.3: Reasoning Quality
- ReasoningAnalyzer module scores coherence, completeness, accuracy
- Example trajectories captured in benchmark results

### Q8.4: Efficiency
- EfficiencyTracker monitors time, tokens, API calls
- Efficiency score calculation based on target metrics

### Q8.5: Bias/Overfitting Checks
- Agent has no benchmark-specific knowledge
- Uses general chess reasoning, not memorized positions

### Q8.6: Reusability & Documentation
- Modular architecture with clear interfaces
- Comprehensive README and code documentation
- Runnable examples and test scripts

## 📖 References

- [Tau-Bench Principles](https://github.com/agentbeats/agentify-example-tau-bench) - Agent design inspiration
- [python-chess](https://python-chess.readthedocs.io/) - Chess library
- [Stockfish](https://stockfishchess.org/) - Evaluation engine

## 📄 License

Apache License 2.0

---

**Berkeley CS194 - LLM Agent Evaluations**
