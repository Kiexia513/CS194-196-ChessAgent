"""
Perception Module
=================

Responsible for understanding the chess board state.
Converts raw FEN and board state into structured, interpretable information.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import chess


@dataclass
class PositionAnalysis:
    fen: str
    side_to_move: str  # "white" or "black"
    move_number: int

    material_balance: int
    white_pieces: Dict[str, int]
    black_pieces: Dict[str, int]

    center_control: str
    king_safety: Dict[str, str]
    piece_activity: Dict[str, str]

    legal_moves: List[str]
    legal_moves_count: int

    checks: bool
    captures_available: List[str]

    board_ascii: str
    position_description: str


class PerceptionModule:
    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,
    }

    PIECE_NAMES = {
        chess.PAWN: "pawn",
        chess.KNIGHT: "knight",
        chess.BISHOP: "bishop",
        chess.ROOK: "rook",
        chess.QUEEN: "queen",
        chess.KING: "king",
    }

    def __init__(self):
        self.board = chess.Board()

    def analyze(self, board_state: Dict[str, Any]) -> PositionAnalysis:
        fen = board_state.get("fen") or chess.STARTING_FEN
        self.board.set_fen(fen)
        side_to_move = "white" if self.board.turn == chess.WHITE else "black"
        move_number = board_state.get("move_number", self.board.fullmove_number)

        legal_moves = board_state.get("legal_moves")
        if not legal_moves:
            legal_moves = [m.uci() for m in self.board.legal_moves]

        white_pieces, black_pieces, material_balance = self._compute_material()
        center_control = self._assess_center_control()
        king_safety = self._assess_king_safety()
        piece_activity = self._assess_piece_activity()

        checks = self.board.is_check()
        captures = self._captures_available()

        board_ascii = str(self.board)
        description = f"{side_to_move} to move. Material balance (white-black): {material_balance}."

        return PositionAnalysis(
            fen=fen,
            side_to_move=side_to_move,
            move_number=move_number,
            material_balance=material_balance,
            white_pieces=white_pieces,
            black_pieces=black_pieces,
            center_control=center_control,
            king_safety=king_safety,
            piece_activity=piece_activity,
            legal_moves=legal_moves,
            legal_moves_count=len(legal_moves),
            checks=checks,
            captures_available=captures,
            board_ascii=board_ascii,
            position_description=description,
        )

    def _compute_material(self):
        white_pieces: Dict[str, int] = {}
        black_pieces: Dict[str, int] = {}
        white_score = 0
        black_score = 0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece:
                continue
            name = self.PIECE_NAMES[piece.piece_type]
            if piece.color == chess.WHITE:
                white_pieces[name] = white_pieces.get(name, 0) + 1
                white_score += self.PIECE_VALUES[piece.piece_type]
            else:
                black_pieces[name] = black_pieces.get(name, 0) + 1
                black_score += self.PIECE_VALUES[piece.piece_type]
        return white_pieces, black_pieces, white_score - black_score

    def _assess_center_control(self) -> str:
        center = [chess.D4, chess.D5, chess.E4, chess.E5]
        white_attacks = 0
        black_attacks = 0
        for sq in center:
            white_attacks += len(self.board.attackers(chess.WHITE, sq))
            black_attacks += len(self.board.attackers(chess.BLACK, sq))
        if white_attacks > black_attacks:
            return "white"
        if black_attacks > white_attacks:
            return "black"
        return "equal"

    def _assess_king_safety(self) -> Dict[str, str]:
        def _king_status(color: chess.Color) -> str:
            king_sq = self.board.king(color)
            if king_sq is None:
                return "unknown"
            file_ = chess.square_file(king_sq)
            if color == chess.WHITE and file_ in (6, 2):
                return "castled"
            if color == chess.BLACK and file_ in (6, 2):
                return "castled"
            return "uncastled"

        return {"white": _king_status(chess.WHITE), "black": _king_status(chess.BLACK)}

    def _assess_piece_activity(self) -> Dict[str, str]:
        # Lightweight placeholder: real evaluation is in reasoning module
        return {"white": "unknown", "black": "unknown"}

    def _captures_available(self) -> List[str]:
        captures: List[str] = []
        for move in self.board.legal_moves:
            if self.board.is_capture(move):
                captures.append(move.uci())
        return captures

