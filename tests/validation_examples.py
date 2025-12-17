"""
Validation examples for the Chess Green Agent evaluation outputs.

Runs three small, deterministic-ish test cases and prints the Green Agent's
evaluation summary for each case.

Usage:
  python tests/validation_examples.py
"""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from green_agent import ChessGreenAgent, RandomAgent, SimpleGreedyAgent
from green_agent.agent_interface import AgentInterface, AgentResponse


class AlwaysIllegalAgent(AgentInterface):
    """An agent that intentionally returns an illegal move to test validation/retry logic."""

    def __init__(self, agent_id: str = "illegal_agent", agent_name: str = "Always Illegal Agent"):
        super().__init__(agent_id, agent_name)

    def get_move(self, board_state):
        # "e2e5" is illegal from the initial position and is illegal in most positions.
        return AgentResponse(
            move_uci="e2e5",
            confidence=0.99,
            reasoning="Intentional illegal move for validation testing (expected to trigger retries).",
            metadata={"intentional": True},
        )

    def reset(self):
        return


def _print_metrics(results: dict):
    white = results["metrics"]["metrics"]["white"]
    black = results["metrics"]["metrics"]["black"]

    def fmt_side(label: str, m: dict) -> str:
        return (
            f"{label}: ACPL={m['acpl']:.2f}, ELO={m['estimated_elo']}, "
            f"best={m.get('best_moves', 0)}, good={m.get('good_moves', 0)}, "
            f"inacc={m.get('inaccuracies', 0)}, mistakes={m.get('mistakes', 0)}, "
            f"blunders={m.get('blunders', 0)}"
        )

    illegal_feedbacks = sum(
        1 for step in results.get("game_log", []) if "Illegal move detected" in (step.get("feedback") or "")
    )

    print(f"Game ID: {results['game_id']}")
    print(f"Result: {results['result']}  |  Total moves: {results['total_moves']}")
    print(fmt_side(f"WHITE ({results['white_agent']['agent_name']})", white))
    print(fmt_side(f"BLACK ({results['black_agent']['agent_name']})", black))
    print(f"Illegal-move feedback count (from logs): {illegal_feedbacks}")
    print(f"Saved log: {Path('logs/validation').joinpath(results['game_id'] + '.json')}")


def main():
    print("=" * 80)
    print("CHESS GREEN AGENT - VALIDATION EXAMPLES")
    print("=" * 80)

    green_agent = ChessGreenAgent(
        agent_id="validation_agent",
        use_stockfish=True,
        log_dir="logs/validation",
    )

    cases = [
        (
            "case_01_greedy_vs_random",
            SimpleGreedyAgent(agent_id="greedy", agent_name="Greedy"),
            RandomAgent(agent_id="random", agent_name="Random"),
            30,
        ),
        (
            "case_02_random_vs_random",
            RandomAgent(agent_id="random_w", agent_name="Random (W)"),
            RandomAgent(agent_id="random_b", agent_name="Random (B)"),
            20,
        ),
        (
            "case_03_illegal_vs_random",
            AlwaysIllegalAgent(agent_id="illegal", agent_name="AlwaysIllegal"),
            RandomAgent(agent_id="random", agent_name="Random"),
            10,
        ),
    ]

    for game_id, white, black, max_moves in cases:
        print("\n" + "-" * 80)
        print(f"Running: {game_id} (max_moves={max_moves})")
        print("-" * 80)
        results = green_agent.run_game(white_agent=white, black_agent=black, game_id=game_id, max_moves=max_moves)
        _print_metrics(results)

    green_agent.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

