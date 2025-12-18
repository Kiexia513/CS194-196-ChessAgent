"""
Reasoning Module for White Agent

This module generates and analyzes candidate moves using chess principles.
It provides structured reasoning for the LLM to make better decisions.
"""

import chess
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class MoveCandidate:
    """Represents an analyzed candidate move"""
    move_uci: str
    move_description: str
    category: str  # 'tactical', 'positional', 'defensive', 'developing'
    score: float  # 0.0 to 1.0
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)


@dataclass 
class ReasoningResult:
    """Result of reasoning process"""
    candidates_analyzed: List[MoveCandidate]
    recommended_move: str
    reasoning_summary: str
    tactical_opportunities: List[str]
    strategic_considerations: List[str]
    reasoning_chain: List[str] = field(default_factory=list)  # Step-by-step reasoning
    confidence: float = 0.7  # Default confidence score
    
    @property
    def selected_move(self) -> str:
        """Alias for recommended_move (for compatibility)"""
        return self.recommended_move
    
    @property
    def final_reasoning(self) -> str:
        """Alias for reasoning_summary (for compatibility)"""
        return self.reasoning_summary


class ReasoningModule:
    """
    Generates and analyzes candidate moves.
    
    This module:
    1. Categorizes legal moves (tactical, positional, etc.)
    2. Scores each candidate based on chess principles
    3. Provides structured reasoning for LLM consumption
    """
    
    def __init__(self, max_candidates: int = 10):
        """
        Initialize reasoning module.
        
        Args:
            max_candidates: Maximum number of candidate moves to analyze
        """
        self.max_candidates = max_candidates
        self.board = chess.Board()
    
    def reason(
        self, 
        fen: str, 
        legal_moves: List[str],
        context: Dict[str, Any]
    ) -> ReasoningResult:
        """
        Main reasoning entry point.
        
        Args:
            fen: Current position FEN
            legal_moves: List of legal moves in UCI format
            context: Memory context from previous moves
            
        Returns:
            ReasoningResult with analyzed candidates
        """
        # Generate candidates with categories
        candidates = self.generate_candidate_moves(fen, legal_moves)
        
        # Analyze each candidate
        analyzed = []
        for move_uci, category in candidates:
            candidate = self.analyze_candidate(move_uci, category, fen)
            analyzed.append(candidate)
        
        # Sort by score
        analyzed.sort(key=lambda x: x.score, reverse=True)
        
        # Generate tactical and strategic observations
        tactical = self._identify_tactical_opportunities(fen)
        strategic = self._identify_strategic_considerations(fen, context)
        
        # Recommend best move
        recommended = analyzed[0].move_uci if analyzed else legal_moves[0]
        
        # Build reasoning chain (step-by-step)
        reasoning_chain = []
        reasoning_chain.append(f"Step 1: Analyzed {len(candidates)} candidate moves")
        if tactical:
            reasoning_chain.append(f"Step 2: Found tactical opportunities: {', '.join(tactical[:2])}")
        if strategic:
            reasoning_chain.append(f"Step 3: Strategic considerations: {', '.join(strategic[:2])}")
        if analyzed:
            best = analyzed[0]
            reasoning_chain.append(f"Step 4: Best candidate is {best.move_uci} (score: {best.score:.2f})")
            if best.pros:
                reasoning_chain.append(f"Step 5: Reasoning: {', '.join(best.pros)}")
        
        # Calculate confidence based on analysis
        confidence = 0.5
        if analyzed:
            best_score = analyzed[0].score
            confidence = min(0.95, best_score + 0.2)  # Base on best move score
            if tactical:
                confidence = min(0.95, confidence + 0.1)  # Bonus for tactical opportunities
        
        return ReasoningResult(
            candidates_analyzed=analyzed,
            recommended_move=recommended,
            reasoning_summary=self._create_summary(analyzed, tactical, strategic),
            tactical_opportunities=tactical,
            strategic_considerations=strategic,
            reasoning_chain=reasoning_chain,
            confidence=confidence
        )
    
    def generate_candidate_moves(
        self, 
        fen: str, 
        legal_moves: List[str]
    ) -> List[Tuple[str, str]]:
        """
        Generate top candidate moves with categories.
        
        Args:
            fen: Current position FEN
            legal_moves: List of legal moves in UCI format
            
        Returns:
            List of (move_uci, category) tuples
        """
        self.board.set_fen(fen)
        
        candidates = []
        
        # Categorize all legal moves
        categorized = {
            "checks": [],
            "captures": [],
            "center_control": [],
            "development": [],
            "king_safety": [],
            "other": []
        }
        
        for move_uci in legal_moves:
            try:
                move = chess.Move.from_uci(move_uci)
                
                # Check if it gives check
                self.board.push(move)
                gives_check = self.board.is_check()
                self.board.pop()
                
                # Check for tactical threats (attacks on weak squares)
                is_tactical_threat = self._is_tactical_threat(move)
                
                if gives_check:
                    categorized["checks"].append(move_uci)
                elif is_tactical_threat:
                    # HIGH PRIORITY: Tactical threats (attacks f7/f2, knight forks, etc.)
                    categorized["checks"].append(move_uci)  # Put with checks for high priority
                elif self.board.is_capture(move):
                    categorized["captures"].append(move_uci)
                elif self._is_center_move(move):
                    categorized["center_control"].append(move_uci)
                elif self._is_development_move(move):
                    categorized["development"].append(move_uci)
                elif self._is_castling(move):
                    categorized["king_safety"].append(move_uci)
                else:
                    categorized["other"].append(move_uci)
            except:
                categorized["other"].append(move_uci)
        
        # Select candidates from each category
        # IMPORTANT: Include more candidates to not miss good moves
        priority_order = ["checks", "captures", "center_control", "development", "king_safety", "other"]
        
        # IMPROVED: Balance tactical and positional moves
        # First priority: checks (almost always worth considering)
        for move in categorized["checks"][:3]:  # Max 3 checks
            candidates.append((move, "tactical"))
        
        # Second priority: center control and development (key for openings)
        for move in categorized["center_control"]:
            if len(candidates) < self.max_candidates:
                candidates.append((move, "positional"))
        
        for move in categorized["development"]:
            if len(candidates) < self.max_candidates:
                candidates.append((move, "developing"))
        
        # Third priority: king safety (castling)
        for move in categorized["king_safety"]:
            if len(candidates) < self.max_candidates:
                candidates.append((move, "defensive"))
        
        # Fourth priority: captures
        for move in categorized["captures"][:3]:  # Max 3 captures
            if len(candidates) < self.max_candidates:
                candidates.append((move, "tactical"))
        
        # Fill remaining with "other" moves
        for move in categorized["other"]:
            if len(candidates) < self.max_candidates:
                candidates.append((move, "positional"))
        
        return candidates[:self.max_candidates]
    
    def _is_center_move(self, move: chess.Move) -> bool:
        """Check if move targets center squares"""
        center_squares = {chess.D4, chess.D5, chess.E4, chess.E5}
        return move.to_square in center_squares
    
    def _is_development_move(self, move: chess.Move) -> bool:
        """Check if move develops a piece"""
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            from_rank = chess.square_rank(move.from_square)
            # First rank for white, eighth for black
            if (piece.color == chess.WHITE and from_rank == 0) or \
               (piece.color == chess.BLACK and from_rank == 7):
                return True
        
        # Also consider pawn moves that open diagonals
        if piece and piece.piece_type == chess.PAWN:
            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)
            if to_file in [3, 4]:  # d and e files
                if (piece.color == chess.WHITE and to_rank in [2, 3]) or \
                   (piece.color == chess.BLACK and to_rank in [4, 5]):
                    return True
        
        return False
    
    def _is_castling(self, move: chess.Move) -> bool:
        """Check if move is castling"""
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.KING:
            file_diff = abs(chess.square_file(move.from_square) - chess.square_file(move.to_square))
            return file_diff == 2
        return False
    
    def _is_tactical_threat(self, move: chess.Move) -> bool:
        """
        Check if move creates a tactical threat.
        
        Detects:
        - Knight attacks on f7/f2 (classic weak squares)
        - Knight on g5 (threatens Nxf7 fork)
        - Bishop attacks on weak diagonals
        """
        piece = self.board.piece_at(move.from_square)
        if not piece:
            return False
        
        to_square = move.to_square
        
        # Check for knight attacks on weak squares
        if piece.piece_type == chess.KNIGHT:
            # Knight on g5 attacks f7 (classic Italian Game tactic)
            if to_square == chess.G5:
                return True
            # Knight on g4 attacks f2
            if to_square == chess.G4:
                return True
            
            # Check if knight will attack f7 or f2
            self.board.push(move)
            knight_attacks = self.board.attacks(to_square)
            attacks_weak = chess.F7 in knight_attacks or chess.F2 in knight_attacks
            self.board.pop()
            
            if attacks_weak:
                return True
        
        # Check for bishop on attacking diagonal
        if piece.piece_type == chess.BISHOP:
            # Bishop on c4 or b5 targets f7
            if to_square in [chess.C4, chess.B5]:
                return True
        
        return False
    
    def analyze_candidate(
        self, 
        move_uci: str, 
        category: str,
        fen: str
    ) -> MoveCandidate:
        """
        Analyze a single candidate move.
        
        Args:
            move_uci: Move in UCI format
            category: Move category
            fen: Current position FEN
            
        Returns:
            MoveCandidate with analysis
        """
        self.board.set_fen(fen)
        
        try:
            move = chess.Move.from_uci(move_uci)
        except:
            return MoveCandidate(
                move_uci=move_uci,
                move_description="Invalid move",
                category=category,
                score=0.0
            )
        
        # Generate move description
        piece = self.board.piece_at(move.from_square)
        piece_name = chess.piece_name(piece.piece_type).capitalize() if piece else "Piece"
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)
        
        is_capture = self.board.is_capture(move)
        captured = self.board.piece_at(move.to_square)
        
        if is_capture and captured:
            desc = f"{piece_name} takes {chess.piece_name(captured.piece_type)} on {to_sq}"
        else:
            desc = f"{piece_name} to {to_sq}"
        
        # Score the move
        score = self._score_move(move, category)
        
        # Generate pros and cons
        pros, cons = self._evaluate_pros_cons(move, category)
        
        return MoveCandidate(
            move_uci=move_uci,
            move_description=desc,
            category=category,
            score=score,
            pros=pros,
            cons=cons
        )
    
    def _score_move(self, move: chess.Move, category: str) -> float:
        """Score a move from 0.0 to 1.0"""
        score = 0.5  # Base score
        
        # Category bonuses
        category_scores = {
            "tactical": 0.3,
            "positional": 0.2,
            "developing": 0.2,
            "defensive": 0.1
        }
        score += category_scores.get(category, 0.0)
        
        # Check bonus
        self.board.push(move)
        if self.board.is_check():
            score += 0.2
        self.board.pop()
        
        # Capture bonus based on piece value
        if self.board.is_capture(move):
            captured = self.board.piece_at(move.to_square)
            if captured:
                piece_values = {
                    chess.PAWN: 0.05,
                    chess.KNIGHT: 0.15,
                    chess.BISHOP: 0.15,
                    chess.ROOK: 0.25,
                    chess.QUEEN: 0.45
                }
                score += piece_values.get(captured.piece_type, 0.0)
        
        # Center control bonus
        if move.to_square in {chess.D4, chess.D5, chess.E4, chess.E5}:
            score += 0.1
        
        return min(1.0, score)
    
    def _evaluate_pros_cons(
        self, 
        move: chess.Move, 
        category: str
    ) -> Tuple[List[str], List[str]]:
        """Generate pros and cons for a move"""
        pros = []
        cons = []
        
        # Check-related
        self.board.push(move)
        if self.board.is_check():
            pros.append("Gives check")
        if self.board.is_checkmate():
            pros.append("CHECKMATE!")
        self.board.pop()
        
        # Capture
        if self.board.is_capture(move):
            captured = self.board.piece_at(move.to_square)
            if captured:
                pros.append(f"Captures {chess.piece_name(captured.piece_type)}")
        
        # Center control
        if move.to_square in {chess.D4, chess.D5, chess.E4, chess.E5}:
            pros.append("Controls center")
        
        # Development
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            from_rank = chess.square_rank(move.from_square)
            if (piece.color == chess.WHITE and from_rank == 0) or \
               (piece.color == chess.BLACK and from_rank == 7):
                pros.append("Develops piece")
        
        # Castling
        if self._is_castling(move):
            pros.append("Secures king safety")
        
        # Category-specific
        if category == "tactical":
            pros.append("Tactical opportunity")
        
        return pros, cons
    
    def _identify_tactical_opportunities(self, fen: str) -> List[str]:
        """Identify tactical opportunities in the position"""
        self.board.set_fen(fen)
        opportunities = []
        
        # Check for checks
        for move in self.board.legal_moves:
            self.board.push(move)
            if self.board.is_check():
                opportunities.append(f"{move.uci()} gives check")
            self.board.pop()
        
        # Check for captures
        for move in self.board.legal_moves:
            if self.board.is_capture(move):
                captured = self.board.piece_at(move.to_square)
                if captured and captured.piece_type in [chess.QUEEN, chess.ROOK]:
                    opportunities.append(f"{move.uci()} captures major piece")
        
        return opportunities[:5]  # Limit to top 5
    
    def _identify_strategic_considerations(
        self, 
        fen: str, 
        context: Dict[str, Any]
    ) -> List[str]:
        """Identify strategic considerations"""
        self.board.set_fen(fen)
        considerations = []
        
        # Opening considerations
        move_num = context.get('game_statistics', {}).get('total_moves', 0)
        if move_num < 10:
            considerations.append("Opening phase - prioritize development and center control")
            
            # Check if castled
            if not self.board.has_castling_rights(self.board.turn):
                considerations.append("Consider castling for king safety")
        
        # Piece activity
        undeveloped = 0
        back_rank = 0 if self.board.turn == chess.WHITE else 7
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece and piece.color == self.board.turn:
                if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                    if chess.square_rank(sq) == back_rank:
                        undeveloped += 1
        
        if undeveloped > 0:
            considerations.append(f"Develop {undeveloped} minor piece(s)")
        
        return considerations
    
    def _create_summary(
        self, 
        analyzed: List[MoveCandidate],
        tactical: List[str],
        strategic: List[str]
    ) -> str:
        """Create a reasoning summary"""
        if not analyzed:
            return "No moves analyzed"
        
        best = analyzed[0]
        summary = f"Best candidate: {best.move_uci} ({best.move_description})"
        
        if best.pros:
            summary += f". Pros: {', '.join(best.pros)}"
        
        if tactical:
            summary += f". Tactical notes: {tactical[0]}"
        
        return summary

