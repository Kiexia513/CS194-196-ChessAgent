# limingrui

# Sample chess agents for testing

import random
import time
from typing import Dict, Any

from .agent_interface import AgentInterface, AgentResponse


class RandomAgent(AgentInterface):
    """
    A simple agent that makes random legal moves
    """
    
    def __init__(self, agent_id: str = "random_agent", agent_name: str = "Random Agent"):
        super().__init__(agent_id, agent_name)
        self.move_count = 0
    
    def get_move(self, board_state: Dict[str, Any]) -> AgentResponse:
        """Select a random legal move"""
        import chess
        
        # Get FEN and generate legal moves ourselves
        fen = board_state["fen"]
        board = chess.Board(fen)
        legal_moves = [move.uci() for move in board.legal_moves]
        
        if not legal_moves:
            raise ValueError("No legal moves available")
        
        # Small delay to simulate computation (time will be measured externally)
        time.sleep(0.1)
        
        # Choose random move
        move = random.choice(legal_moves)
        
        self.move_count += 1
        
        return AgentResponse(
            move_uci=move,
            confidence=random.uniform(0.3, 0.7),
            reasoning=f"Random selection from {len(legal_moves)} legal moves",
            metadata={"move_count": self.move_count}
        )
    
    def reset(self):
        """Reset agent for new game"""
        self.move_count = 0


class SimpleGreedyAgent(AgentInterface):
    """
    A simple agent that prefers captures and checks
    """
    
    def __init__(self, agent_id: str = "greedy_agent", agent_name: str = "Greedy Agent"):
        super().__init__(agent_id, agent_name)
        self.move_count = 0
    
    def get_move(self, board_state: Dict[str, Any]) -> AgentResponse:
        """
        Select move with simple heuristics:
        1. Prefer captures
        2. Prefer checks
        3. Otherwise random
        """
        import chess
        
        # Get FEN and generate legal moves ourselves
        fen = board_state["fen"]
        board = chess.Board(fen)
        legal_moves = [move.uci() for move in board.legal_moves]
        
        if not legal_moves:
            raise ValueError("No legal moves available")
        
        # Small delay to simulate computation (time will be measured externally)
        time.sleep(0.1)
        
        # Categorize moves
        capturing_moves = []
        checking_moves = []
        
        for move_uci in legal_moves:
            move = chess.Move.from_uci(move_uci)
            
            # Check if it's a capture
            if board.is_capture(move):
                capturing_moves.append(move_uci)
            
            # Check if it gives check
            board.push(move)
            if board.is_check():
                checking_moves.append(move_uci)
            board.pop()
        
        # Choose move based on priority
        if capturing_moves:
            selected_move = random.choice(capturing_moves)
            reasoning = f"Capture move selected from {len(capturing_moves)} captures"
            confidence = 0.8
        elif checking_moves:
            selected_move = random.choice(checking_moves)
            reasoning = f"Check move selected from {len(checking_moves)} checks"
            confidence = 0.7
        else:
            selected_move = random.choice(legal_moves)
            reasoning = f"Random move from {len(legal_moves)} legal moves"
            confidence = 0.5
        
        self.move_count += 1
        
        return AgentResponse(
            move_uci=selected_move,
            confidence=confidence,
            reasoning=reasoning,
            metadata={"move_count": self.move_count}
        )
    
    def reset(self):
        """Reset agent for new game"""
        self.move_count = 0

