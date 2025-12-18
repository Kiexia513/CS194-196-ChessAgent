"""
Perception Module
=================

Responsible for understanding the chess board state.
Converts raw FEN and board state into structured, interpretable information.

Follows the self-explanatory principle: provides clear, human-readable
descriptions of the chess position without assuming prior knowledge.
"""

import chess
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PositionAnalysis:
    """Structured analysis of a chess position"""
    
    # Basic info
    fen: str
    side_to_move: str  # "white" or "black"
    move_number: int
    
    # Material
    material_balance: int  # positive = white advantage
    white_pieces: Dict[str, int]  # e.g., {"pawn": 8, "knight": 2, ...}
    black_pieces: Dict[str, int]
    
    # Position features
    center_control: str  # "white", "black", "equal"
    king_safety: Dict[str, str]  # {"white": "safe/exposed/castled", "black": ...}
    piece_activity: Dict[str, str]  # general assessment
    
    # Legal moves
    legal_moves: List[str]
    legal_moves_count: int
    
    # Threats and opportunities
    checks: bool
    captures_available: List[str]
    
    # Visual representation
    board_ascii: str
    position_description: str


class PerceptionModule:
    """
    Analyzes chess positions and provides structured understanding.
    
    This module converts raw chess data into interpretable information
    that can be used by the reasoning module.
    """
    
    # Piece values for material calculation
    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0  # King is invaluable
    }
    
    PIECE_NAMES = {
        chess.PAWN: "pawn",
        chess.KNIGHT: "knight",
        chess.BISHOP: "bishop",
        chess.ROOK: "rook",
        chess.QUEEN: "queen",
        chess.KING: "king"
    }
    
    def __init__(self):
        self.board = chess.Board()
    
    def analyze(self, board_state: Dict[str, Any]) -> PositionAnalysis:
        """
        Analyze a chess position and return structured information.
        
        Args:
            board_state: Dictionary containing FEN and other game info
            
        Returns:
            PositionAnalysis with detailed position information
        """
        fen = board_state.get("fen", chess.STARTING_FEN)
        self.board.set_fen(fen)
        
        # Basic info
        side_to_move = "white" if self.board.turn else "black"
        move_number = board_state.get("move_number", self.board.fullmove_number)
        
        # Material analysis
        white_pieces, black_pieces = self._count_pieces()
        material_balance = self._calculate_material_balance(white_pieces, black_pieces)
        
        # Position analysis
        center_control = self._analyze_center_control()
        king_safety = self._analyze_king_safety()
        piece_activity = self._analyze_piece_activity()
        
        # Legal moves
        legal_moves = [move.uci() for move in self.board.legal_moves]
        
        # Threats
        checks = self.board.is_check()
        captures_available = self._get_captures()
        
        # Visual representation
        board_ascii = self._get_ascii_board()
        position_description = self._generate_position_description(
            side_to_move, move_number, material_balance, checks
        )
        
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
            captures_available=captures_available,
            board_ascii=board_ascii,
            position_description=position_description
        )
    
    def _count_pieces(self) -> tuple:
        """Count pieces for each side"""
        white_pieces = {name: 0 for name in self.PIECE_NAMES.values()}
        black_pieces = {name: 0 for name in self.PIECE_NAMES.values()}
        
        for piece_type in self.PIECE_NAMES.keys():
            white_pieces[self.PIECE_NAMES[piece_type]] = len(
                self.board.pieces(piece_type, chess.WHITE)
            )
            black_pieces[self.PIECE_NAMES[piece_type]] = len(
                self.board.pieces(piece_type, chess.BLACK)
            )
        
        return white_pieces, black_pieces
    
    def _calculate_material_balance(
        self, 
        white_pieces: Dict[str, int], 
        black_pieces: Dict[str, int]
    ) -> int:
        """Calculate material balance (positive = white advantage)"""
        white_material = sum(
            count * self.PIECE_VALUES[piece_type]
            for piece_type, name in self.PIECE_NAMES.items()
            for n, count in [(name, white_pieces.get(name, 0))]
            if n == name
        )
        black_material = sum(
            count * self.PIECE_VALUES[piece_type]
            for piece_type, name in self.PIECE_NAMES.items()
            for n, count in [(name, black_pieces.get(name, 0))]
            if n == name
        )
        
        # Simplified calculation
        white_total = (
            white_pieces["pawn"] * 1 +
            white_pieces["knight"] * 3 +
            white_pieces["bishop"] * 3 +
            white_pieces["rook"] * 5 +
            white_pieces["queen"] * 9
        )
        black_total = (
            black_pieces["pawn"] * 1 +
            black_pieces["knight"] * 3 +
            black_pieces["bishop"] * 3 +
            black_pieces["rook"] * 5 +
            black_pieces["queen"] * 9
        )
        
        return white_total - black_total
    
    def _analyze_center_control(self) -> str:
        """Analyze who controls the center squares"""
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        extended_center = [chess.C3, chess.C4, chess.C5, chess.C6,
                          chess.D3, chess.D6, chess.E3, chess.E6,
                          chess.F3, chess.F4, chess.F5, chess.F6]
        
        white_control = 0
        black_control = 0
        
        for square in center_squares:
            white_attackers = len(self.board.attackers(chess.WHITE, square))
            black_attackers = len(self.board.attackers(chess.BLACK, square))
            white_control += white_attackers
            black_control += black_attackers
        
        if white_control > black_control + 2:
            return "white"
        elif black_control > white_control + 2:
            return "black"
        else:
            return "equal"
    
    def _analyze_king_safety(self) -> Dict[str, str]:
        """Analyze king safety for both sides"""
        safety = {}
        
        for color, name in [(chess.WHITE, "white"), (chess.BLACK, "black")]:
            king_square = self.board.king(color)
            if king_square is None:
                safety[name] = "unknown"
                continue
            
            # Check if castled (king on g1/g8 or c1/c8 area)
            king_file = chess.square_file(king_square)
            king_rank = chess.square_rank(king_square)
            
            if color == chess.WHITE and king_rank == 0:
                if king_file >= 6:  # Kingside castled
                    safety[name] = "castled_kingside"
                elif king_file <= 2:  # Queenside castled
                    safety[name] = "castled_queenside"
                else:
                    safety[name] = "center"
            elif color == chess.BLACK and king_rank == 7:
                if king_file >= 6:
                    safety[name] = "castled_kingside"
                elif king_file <= 2:
                    safety[name] = "castled_queenside"
                else:
                    safety[name] = "center"
            else:
                # King has moved but not to a typical castled position
                safety[name] = "exposed" if king_rank in [3, 4] else "moved"
        
        return safety
    
    def _analyze_piece_activity(self) -> Dict[str, str]:
        """General assessment of piece activity"""
        activity = {}
        
        for color, name in [(chess.WHITE, "white"), (chess.BLACK, "black")]:
            # Count developed pieces (not on starting squares)
            developed = 0
            total_minors = 0
            
            # Knights
            for square in self.board.pieces(chess.KNIGHT, color):
                total_minors += 1
                rank = chess.square_rank(square)
                if (color == chess.WHITE and rank > 0) or (color == chess.BLACK and rank < 7):
                    developed += 1
            
            # Bishops
            for square in self.board.pieces(chess.BISHOP, color):
                total_minors += 1
                rank = chess.square_rank(square)
                if (color == chess.WHITE and rank > 0) or (color == chess.BLACK and rank < 7):
                    developed += 1
            
            if total_minors == 0:
                activity[name] = "endgame"
            elif developed >= total_minors:
                activity[name] = "fully_developed"
            elif developed >= total_minors / 2:
                activity[name] = "partially_developed"
            else:
                activity[name] = "undeveloped"
        
        return activity
    
    def _get_captures(self) -> List[str]:
        """Get all available capture moves"""
        captures = []
        for move in self.board.legal_moves:
            if self.board.is_capture(move):
                captures.append(move.uci())
        return captures
    
    def _get_ascii_board(self) -> str:
        """Get ASCII representation of the board"""
        return str(self.board)
    
    def _generate_position_description(
        self,
        side_to_move: str,
        move_number: int,
        material_balance: int,
        in_check: bool
    ) -> str:
        """Generate a human-readable position description"""
        description_parts = []
        
        # Move info
        description_parts.append(f"Move {move_number}: {side_to_move.capitalize()} to play.")
        
        # Check status
        if in_check:
            description_parts.append(f"{side_to_move.capitalize()} is in CHECK!")
        
        # Material
        if material_balance > 0:
            description_parts.append(f"White is ahead by {material_balance} point(s) of material.")
        elif material_balance < 0:
            description_parts.append(f"Black is ahead by {-material_balance} point(s) of material.")
        else:
            description_parts.append("Material is equal.")
        
        return " ".join(description_parts)
    
    def get_move_description(self, move_uci: str) -> str:
        """Get a human-readable description of a move"""
        try:
            move = chess.Move.from_uci(move_uci)
            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            
            piece = self.board.piece_at(move.from_square)
            piece_name = self.PIECE_NAMES.get(piece.piece_type, "piece") if piece else "piece"
            
            captured = self.board.piece_at(move.to_square)
            
            if captured:
                captured_name = self.PIECE_NAMES.get(captured.piece_type, "piece")
                return f"{piece_name.capitalize()} from {from_square} captures {captured_name} on {to_square}"
            else:
                return f"{piece_name.capitalize()} from {from_square} to {to_square}"
        except:
            return f"Move: {move_uci}"


