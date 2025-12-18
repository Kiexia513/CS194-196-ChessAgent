"""
Efficiency Tracker
==================

Tracks and analyzes agent efficiency metrics.
Monitors token usage, timing, and resource consumption.

Metrics:
- Time per move
- Token usage per move
- API call efficiency
- Overall computational cost
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class MoveMetrics:
    """Metrics for a single move"""
    move_number: int
    thinking_time: float
    tokens_used: int  # Estimated
    api_calls: int
    candidates_analyzed: int
    
    # Derived
    time_per_candidate: float = 0.0
    
    def __post_init__(self):
        if self.candidates_analyzed > 0:
            self.time_per_candidate = self.thinking_time / self.candidates_analyzed


@dataclass
class GameEfficiency:
    """Efficiency metrics for a complete game"""
    game_id: str
    total_moves: int = 0
    total_time: float = 0.0
    total_tokens: int = 0
    total_api_calls: int = 0
    
    # Averages
    avg_time_per_move: float = 0.0
    avg_tokens_per_move: float = 0.0
    
    # Move-by-move metrics
    move_metrics: List[MoveMetrics] = field(default_factory=list)
    
    def calculate_averages(self):
        """Calculate average metrics"""
        if self.total_moves > 0:
            self.avg_time_per_move = self.total_time / self.total_moves
            self.avg_tokens_per_move = self.total_tokens / self.total_moves


class EfficiencyTracker:
    """
    Tracks agent efficiency throughout games.
    
    Provides:
    - Real-time efficiency monitoring
    - Historical efficiency analysis
    - Cost estimation
    - Performance optimization insights
    """
    
    # Token estimation constants (approximate)
    TOKENS_PER_CHAR = 0.25  # Rough estimate for English text
    BASE_PROMPT_TOKENS = 500  # Base prompt overhead
    
    def __init__(self, track_history: bool = True):
        """
        Initialize efficiency tracker.
        
        Args:
            track_history: Whether to keep historical data
        """
        self.track_history = track_history
        self.current_game: Optional[GameEfficiency] = None
        self.game_history: List[GameEfficiency] = []
        
        # Real-time tracking
        self.move_start_time: Optional[float] = None
        self.current_move_tokens: int = 0
        self.current_move_api_calls: int = 0
    
    def start_game(self, game_id: str = "game"):
        """Start tracking a new game"""
        if self.current_game and self.track_history:
            self.game_history.append(self.current_game)
        
        self.current_game = GameEfficiency(game_id=game_id)
    
    def start_move(self):
        """Start timing a move"""
        self.move_start_time = time.time()
        self.current_move_tokens = 0
        self.current_move_api_calls = 0
    
    def record_api_call(self, prompt_length: int, response_length: int):
        """
        Record an API call.
        
        Args:
            prompt_length: Length of prompt in characters
            response_length: Length of response in characters
        """
        # Estimate tokens
        prompt_tokens = int(prompt_length * self.TOKENS_PER_CHAR) + self.BASE_PROMPT_TOKENS
        response_tokens = int(response_length * self.TOKENS_PER_CHAR)
        
        self.current_move_tokens += prompt_tokens + response_tokens
        self.current_move_api_calls += 1
    
    def end_move(self, candidates_analyzed: int = 1) -> MoveMetrics:
        """
        End timing a move and record metrics.
        
        Args:
            candidates_analyzed: Number of candidates the agent analyzed
            
        Returns:
            MoveMetrics for this move
        """
        if self.move_start_time is None:
            thinking_time = 0.0
        else:
            thinking_time = time.time() - self.move_start_time
        
        if self.current_game is None:
            self.start_game()
        
        move_number = self.current_game.total_moves + 1
        
        metrics = MoveMetrics(
            move_number=move_number,
            thinking_time=thinking_time,
            tokens_used=self.current_move_tokens,
            api_calls=self.current_move_api_calls,
            candidates_analyzed=candidates_analyzed
        )
        
        # Update game totals
        self.current_game.total_moves += 1
        self.current_game.total_time += thinking_time
        self.current_game.total_tokens += self.current_move_tokens
        self.current_game.total_api_calls += self.current_move_api_calls
        self.current_game.move_metrics.append(metrics)
        self.current_game.calculate_averages()
        
        # Reset move tracking
        self.move_start_time = None
        self.current_move_tokens = 0
        self.current_move_api_calls = 0
        
        return metrics
    
    def get_current_game_stats(self) -> Dict[str, Any]:
        """Get statistics for current game"""
        if self.current_game is None:
            return {"error": "No game in progress"}
        
        return {
            "game_id": self.current_game.game_id,
            "total_moves": self.current_game.total_moves,
            "total_time": round(self.current_game.total_time, 2),
            "total_tokens": self.current_game.total_tokens,
            "total_api_calls": self.current_game.total_api_calls,
            "avg_time_per_move": round(self.current_game.avg_time_per_move, 2),
            "avg_tokens_per_move": round(self.current_game.avg_tokens_per_move, 0),
            "estimated_cost": self._estimate_cost(self.current_game.total_tokens)
        }
    
    def _estimate_cost(self, tokens: int) -> str:
        """
        Estimate API cost based on token usage.
        
        Note: This is a rough estimate. Actual costs vary by provider.
        """
        # Rough pricing (USD per 1M tokens)
        # DeepSeek: ~$0.14 input, ~$0.28 output (averaged to ~$0.21)
        # GPT-4o-mini: ~$0.15 input, ~$0.60 output (averaged to ~$0.375)
        
        cost_per_million = 0.25  # Average estimate
        cost = (tokens / 1_000_000) * cost_per_million
        
        if cost < 0.01:
            return f"< $0.01"
        else:
            return f"~${cost:.3f}"
    
    def get_historical_stats(self) -> Dict[str, Any]:
        """Get statistics across all games"""
        if not self.game_history and not self.current_game:
            return {"error": "No games recorded"}
        
        all_games = list(self.game_history)
        if self.current_game:
            all_games.append(self.current_game)
        
        total_moves = sum(g.total_moves for g in all_games)
        total_time = sum(g.total_time for g in all_games)
        total_tokens = sum(g.total_tokens for g in all_games)
        
        return {
            "total_games": len(all_games),
            "total_moves": total_moves,
            "total_time": round(total_time, 2),
            "total_tokens": total_tokens,
            "overall_avg_time": round(total_time / max(1, total_moves), 2),
            "overall_avg_tokens": round(total_tokens / max(1, total_moves), 0),
            "total_estimated_cost": self._estimate_cost(total_tokens)
        }
    
    def get_time_trend(self) -> List[float]:
        """Get trend of thinking times for current game"""
        if self.current_game is None:
            return []
        
        return [m.thinking_time for m in self.current_game.move_metrics]
    
    def identify_slow_moves(self, threshold: float = 10.0) -> List[MoveMetrics]:
        """
        Identify moves that took longer than threshold.
        
        Args:
            threshold: Time threshold in seconds
            
        Returns:
            List of slow MoveMetrics
        """
        if self.current_game is None:
            return []
        
        return [m for m in self.current_game.move_metrics if m.thinking_time > threshold]
    
    def get_efficiency_score(self) -> float:
        """
        Calculate an overall efficiency score (0-1).
        
        Higher is better (faster with fewer resources).
        """
        if self.current_game is None or self.current_game.total_moves == 0:
            return 0.5
        
        # Target metrics (adjust based on your requirements)
        target_time = 5.0  # 5 seconds per move
        target_tokens = 1000  # 1000 tokens per move
        
        # Calculate scores (inverse - lower actual = higher score)
        time_score = min(1.0, target_time / max(0.1, self.current_game.avg_time_per_move))
        token_score = min(1.0, target_tokens / max(1, self.current_game.avg_tokens_per_move))
        
        # Weighted average
        return 0.6 * time_score + 0.4 * token_score
    
    def generate_report(self) -> str:
        """Generate efficiency report"""
        stats = self.get_current_game_stats()
        historical = self.get_historical_stats()
        
        lines = [
            "=" * 50,
            "EFFICIENCY REPORT",
            "=" * 50,
            "",
            "Current Game:",
            f"  Moves: {stats.get('total_moves', 0)}",
            f"  Total Time: {stats.get('total_time', 0)}s",
            f"  Avg Time/Move: {stats.get('avg_time_per_move', 0)}s",
            f"  Total Tokens: {stats.get('total_tokens', 0)}",
            f"  Avg Tokens/Move: {stats.get('avg_tokens_per_move', 0)}",
            f"  API Calls: {stats.get('total_api_calls', 0)}",
            f"  Estimated Cost: {stats.get('estimated_cost', 'N/A')}",
            "",
            "Historical:",
            f"  Total Games: {historical.get('total_games', 0)}",
            f"  Total Moves: {historical.get('total_moves', 0)}",
            f"  Overall Avg Time: {historical.get('overall_avg_time', 0)}s",
            f"  Total Estimated Cost: {historical.get('total_estimated_cost', 'N/A')}",
            "",
            f"Efficiency Score: {self.get_efficiency_score():.2f}",
            "=" * 50
        ]
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset all tracking data"""
        self.current_game = None
        self.game_history = []
        self.move_start_time = None


