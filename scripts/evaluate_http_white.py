"""
Evaluate a White agent exposed as an HTTP API using the Green agent orchestrator.

Usage (example):
  python scripts/evaluate_http_white.py --white-url http://localhost:8002 --max-moves 20

If your white agent is behind an AgentBeats controller proxy, pass:
  --white-url https://<controller>/to_agent/<id>
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "src"))

    from green_agent import ChessGreenAgent, RandomAgent, SimpleGreedyAgent
    from http_white_agent import HTTPWhiteAgent

    parser = argparse.ArgumentParser()
    parser.add_argument("--white-url", required=True, help="Base URL of white HTTP agent")
    parser.add_argument("--max-moves", type=int, default=30)
    parser.add_argument(
        "--black",
        choices=["greedy", "random"],
        default="greedy",
        help="Baseline opponent used as black",
    )
    parser.add_argument("--use-stockfish", action="store_true")
    parser.add_argument("--white-api-key", default=os.getenv("AGENT_API_KEY"))
    args = parser.parse_args()

    white = HTTPWhiteAgent(
        base_url=args.white_url,
        agent_id="white_http",
        agent_name="WhiteHTTP",
        timeout_s=60.0,
        api_key=args.white_api_key,
    )

    black = (
        RandomAgent(agent_id="random_black", agent_name="Random")
        if args.black == "random"
        else SimpleGreedyAgent(agent_id="greedy_black", agent_name="SimpleGreedy")
    )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    green = ChessGreenAgent(
        agent_id=f"eval_{run_id}",
        use_stockfish=args.use_stockfish,
        log_dir="logs/http_eval",
    )
    try:
        results = green.run_game(
            white_agent=white,
            black_agent=black,
            game_id=f"http_eval_{run_id}",
            max_moves=args.max_moves,
        )
    finally:
        green.close()

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

