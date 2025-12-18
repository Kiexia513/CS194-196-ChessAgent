"""
Reasoning Module for White Agent

Generates and analyzes candidate moves using lightweight chess principles.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import chess


@dataclass
class MoveCandidate:
    move_uci: str
    reasoning: str
    category: str  # 'tactical', 'positional', 'defensive', 'developing'
    score: float  # 0.0 to 1.0
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)


@dataclass
class ReasoningResult:
    candidates_analyzed: List[MoveCandidate]
    recommended_move: str
    reasoning_summary: str
    tactical_opportunities: List[str]
    strategic_considerations: List[str]
    reasoning_chain: List[str] = field(default_factory=list)
    confidence: float = 0.7

    @property
    def selected_move(self) -> str:
        return self.recommended_move

    @property
    def final_reasoning(self) -> str:
        return self.reasoning_summary

    @classmethod
    def empty(cls) -> "ReasoningResult":
        return cls(
            candidates_analyzed=[],
            recommended_move="e2e4",
            reasoning_summary="No reasoning available.",
            tactical_opportunities=[],
            strategic_considerations=[],
            reasoning_chain=[],
            confidence=0.05,
        )


class ReasoningModule:
    def __init__(self, max_candidates: int = 10):
        self.max_candidates = max_candidates
        self.board = chess.Board()

    def reason(self, fen: str, legal_moves: List[str], context: Dict[str, Any]) -> ReasoningResult:
        candidates = self.generate_candidate_moves(fen, legal_moves)
        analyzed: List[MoveCandidate] = []
        for move_uci, category in candidates:
            analyzed.append(self.analyze_candidate(move_uci, category, fen))
        analyzed.sort(key=lambda x: x.score, reverse=True)
        recommended = analyzed[0].move_uci if analyzed else (legal_moves[0] if legal_moves else "e2e4")
        return ReasoningResult(
            candidates_analyzed=analyzed,
            recommended_move=recommended,
            reasoning_summary=self._create_summary(analyzed),
            tactical_opportunities=[],
            strategic_considerations=[],
            reasoning_chain=[
                f"Analyzed {len(analyzed)} candidates, recommended {recommended}."
            ],
            confidence=min(0.95, (analyzed[0].score + 0.2) if analyzed else 0.2),
        )

    def generate_candidate_moves(self, fen: str, legal_moves: List[str]) -> List[Tuple[str, str]]:
        self.board.set_fen(fen)
        categorized: Dict[str, List[str]] = {
            "checks": [],
            "captures": [],
            "center_control": [],
            "development": [],
            "king_safety": [],
            "other": [],
        }
        for move_uci in legal_moves:
            try:
                move = chess.Move.from_uci(move_uci)
                self.board.push(move)
                gives_check = self.board.is_check()
                self.board.pop()
                if gives_check:
                    categorized["checks"].append(move_uci)
                elif self.board.is_capture(move):
                    categorized["captures"].append(move_uci)
                elif move.to_square in {chess.D4, chess.D5, chess.E4, chess.E5}:
                    categorized["center_control"].append(move_uci)
                else:
                    categorized["other"].append(move_uci)
            except Exception:
                categorized["other"].append(move_uci)

        candidates: List[Tuple[str, str]] = []
        for move in categorized["checks"][:3]:
            candidates.append((move, "tactical"))
        for move in categorized["center_control"]:
            if len(candidates) < self.max_candidates:
                candidates.append((move, "positional"))
        for move in categorized["captures"][:3]:
            if len(candidates) < self.max_candidates:
                candidates.append((move, "tactical"))
        for move in categorized["other"]:
            if len(candidates) < self.max_candidates:
                candidates.append((move, "positional"))

        return candidates[: self.max_candidates]

    def analyze_candidate(self, move_uci: str, category: str, fen: str) -> MoveCandidate:
        # Light heuristic scoring (placeholder)
        score = 0.5
        pros: List[str] = []
        cons: List[str] = []

        if category == "tactical":
            score += 0.15
            pros.append("Tactical opportunity")
        if category == "positional":
            score += 0.05
            pros.append("Positional improvement")

        reasoning = f"{category} move {move_uci}"
        return MoveCandidate(
            move_uci=move_uci,
            reasoning=reasoning,
            category=category,
            score=max(0.0, min(1.0, score)),
            pros=pros,
            cons=cons,
        )

    def _create_summary(self, analyzed: List[MoveCandidate]) -> str:
        if not analyzed:
            return "No candidates analyzed."
        best = analyzed[0]
        return f"Recommended {best.move_uci} ({best.category}) with score {best.score:.2f}."
