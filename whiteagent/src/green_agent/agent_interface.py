# limingrui

# Agent interface for chess agents being evaluated

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AgentResponse:
    """
    Response from an agent
    
    Note: thinking_time should NOT be provided by the agent.
    It will be calculated by the Green Agent (evaluator) externally.
    """
    move_uci: str  # UCI format move (e.g., "e2e4")
    confidence: Optional[float] = None  # confidence score (0-1)
    reasoning: Optional[str] = None  # reasoning for the move
    metadata: Optional[Dict[str, Any]] = None  # additional metadata


class AgentInterface(ABC):
    """
    Abstract interface for chess agents being evaluated
    
    All participant agents must implement this interface to be evaluated by the Green Agent
    """
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
    
    @abstractmethod
    def get_move(self, board_state: Dict[str, Any]) -> AgentResponse:
        """
        Get the next move from the agent
        
        Args:
            board_state: dictionary containing:
                - fen: FEN string of current position
                - legal_moves: list of legal moves in UCI format
                - move_history: list of previous moves
                - time_remaining: remaining time in seconds
                - move_number: current move number
                
        Returns:
            AgentResponse containing the move and metadata
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset the agent for a new game"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name
        }

