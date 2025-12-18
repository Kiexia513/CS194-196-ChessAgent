"""
Memory Module
=============

Responsible for maintaining game history and context.
Stores previous moves, opponent patterns, and game state.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MoveRecord:
    """Record of a single move"""

    move_number: int
    side: str  # "white" or "black"
    move_uci: str
    reasoning: Optional[str] = None
    was_capture: bool = False
    was_check: bool = False
    evaluation_feedback: Optional[str] = None  # Feedback from green agent


@dataclass
class GameMemory:
    """Complete memory of a game"""

    game_id: str
    moves: List[MoveRecord] = field(default_factory=list)
    opponent_style: str = "unknown"  # "aggressive", "defensive", "positional", "tactical"
    opening_name: Optional[str] = None
    our_side: str = "white"

    # Statistics
    captures_made: int = 0
    checks_given: int = 0
    mistakes_made: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "total_moves": len(self.moves),
            "our_side": self.our_side,
            "opponent_style": self.opponent_style,
            "opening": self.opening_name,
            "statistics": {
                "captures": self.captures_made,
                "checks": self.checks_given,
                "mistakes": self.mistakes_made,
            },
        }


class MemoryModule:
    """Manages game memory and context for the agent."""

    def __init__(self, short_term_capacity: int = 10):
        self.short_term_capacity = short_term_capacity
        self.current_game: Optional[GameMemory] = None
        self.short_term_memory: deque = deque(maxlen=short_term_capacity)
        self.past_games: List[GameMemory] = []

    def start_new_game(self, game_id: str = "game_001", our_side: str = "white"):
        if self.current_game:
            self.past_games.append(self.current_game)
        self.current_game = GameMemory(game_id=game_id, our_side=our_side)
        self.short_term_memory.clear()

    def record_move(
        self,
        move_number: int,
        side: str,
        move_uci: str,
        reasoning: Optional[str] = None,
        was_capture: bool = False,
        was_check: bool = False,
        evaluation_feedback: Optional[str] = None,
    ):
        record = MoveRecord(
            move_number=move_number,
            side=side,
            move_uci=move_uci,
            reasoning=reasoning,
            was_capture=was_capture,
            was_check=was_check,
            evaluation_feedback=evaluation_feedback,
        )

        if self.current_game:
            self.current_game.moves.append(record)
            if was_capture:
                self.current_game.captures_made += 1
            if was_check:
                self.current_game.checks_given += 1
            if evaluation_feedback and "mistake" in evaluation_feedback.lower():
                self.current_game.mistakes_made += 1

        self.short_term_memory.append(record)

    def get_recent_moves(self, n: Optional[int] = None) -> List[MoveRecord]:
        if n is None:
            return list(self.short_term_memory)
        return list(self.short_term_memory)[-n:]

    def get_move_history_text(self, max_moves: int = 5) -> str:
        recent = self.get_recent_moves(max_moves)
        if not recent:
            return "No previous moves (game start)."

        history_lines = []
        for record in recent:
            line = f"Move {record.move_number} ({record.side}): {record.move_uci}"
            if record.was_capture:
                line += " (capture)"
            if record.was_check:
                line += " (check)"
            history_lines.append(line)

        return "\n".join(history_lines)

    def get_opponent_last_move(self) -> Optional[MoveRecord]:
        if not self.current_game:
            return None
        our_side = self.current_game.our_side
        opponent_side = "black" if our_side == "white" else "white"
        for record in reversed(list(self.short_term_memory)):
            if record.side == opponent_side:
                return record
        return None

    def analyze_opponent_style(self) -> str:
        if not self.current_game or len(self.current_game.moves) < 4:
            return "unknown (too few moves)"

        our_side = self.current_game.our_side
        opponent_side = "black" if our_side == "white" else "white"
        opponent_moves = [m for m in self.current_game.moves if m.side == opponent_side]
        if not opponent_moves:
            return "unknown"

        captures = sum(1 for m in opponent_moves if m.was_capture)
        checks = sum(1 for m in opponent_moves if m.was_check)
        capture_rate = captures / len(opponent_moves)
        check_rate = checks / len(opponent_moves)

        if capture_rate > 0.4 or check_rate > 0.2:
            style = "aggressive"
        elif capture_rate < 0.1:
            style = "positional"
        else:
            style = "balanced"

        self.current_game.opponent_style = style
        return style

    def get_context_for_prompt(self) -> Dict[str, Any]:
        return {
            "move_history": self.get_move_history_text(),
            "opponent_style": self.analyze_opponent_style(),
            "opponent_last_move": (
                self.get_opponent_last_move().move_uci if self.get_opponent_last_move() else None
            ),
        }

    def reset(self):
        self.short_term_memory.clear()
        self.current_game = None

    def get_game_summary(self) -> Dict[str, Any]:
        if not self.current_game:
            return {"status": "no game in progress"}
        return self.current_game.to_dict()

