"""
Chess Benchmark Suite
=====================

Provides standardized test positions and evaluation metrics
for assessing chess agent performance.

Test Categories:
- Opening: Standard opening knowledge
- Tactical: Tactical pattern recognition
- Endgame: Endgame technique
- Defensive: Defensive skills
- Complex: Complex middlegame decisions

Metrics:
- Accuracy: Percentage of "good" moves
- Quality: Average move quality score
- Consistency: Performance stability
- Speed: Average thinking time
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import chess


@dataclass
class TestPosition:
    """A single test position"""
    id: str
    name: str
    fen: str
    description: str
    expected_good_moves: List[str]
    category: str
    difficulty: str
    
    def get_legal_moves(self) -> List[str]:
        """Get all legal moves for this position"""
        board = chess.Board(self.fen)
        return [move.uci() for move in board.legal_moves]


@dataclass
class TestResult:
    """Result from testing a single position"""
    position_id: str
    position_name: str
    category: str
    difficulty: str
    
    agent_move: str
    is_good_move: bool
    is_best_move: bool
    confidence: float
    reasoning: str
    thinking_time: float
    
    expected_moves: List[str]
    legal_moves_count: int


@dataclass
class BenchmarkResult:
    """Complete benchmark results"""
    agent_id: str
    agent_name: str
    timestamp: str
    
    # Overall metrics
    total_positions: int = 0
    good_moves: int = 0
    best_moves: int = 0
    accuracy: float = 0.0
    
    # Category breakdown
    category_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Difficulty breakdown
    difficulty_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Individual results
    test_results: List[TestResult] = field(default_factory=list)
    
    # Efficiency metrics
    total_time: float = 0.0
    avg_thinking_time: float = 0.0
    avg_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp,
            "summary": {
                "total_positions": self.total_positions,
                "good_moves": self.good_moves,
                "best_moves": self.best_moves,
                "accuracy": round(self.accuracy, 4),
                "avg_thinking_time": round(self.avg_thinking_time, 3),
                "avg_confidence": round(self.avg_confidence, 3)
            },
            "by_category": self.category_results,
            "by_difficulty": self.difficulty_results,
            "detailed_results": [
                {
                    "position_id": r.position_id,
                    "position_name": r.position_name,
                    "category": r.category,
                    "difficulty": r.difficulty,
                    "agent_move": r.agent_move,
                    "is_good_move": r.is_good_move,
                    "confidence": r.confidence,
                    "thinking_time": round(r.thinking_time, 3)
                }
                for r in self.test_results
            ]
        }


class ChessBenchmark:
    """
    Chess Benchmark Suite for evaluating agent performance.
    
    Loads standardized test positions and provides methods
    to evaluate agents against them.
    """
    
    def __init__(self, positions_file: Optional[str] = None):
        """
        Initialize benchmark suite.
        
        Args:
            positions_file: Path to JSON file with test positions
        """
        if positions_file is None:
            positions_file = Path(__file__).parent / "positions.json"
        
        self.positions_file = Path(positions_file)
        self.positions: Dict[str, List[TestPosition]] = {}
        
        self._load_positions()
    
    def _load_positions(self):
        """Load test positions from JSON file"""
        if not self.positions_file.exists():
            print(f"Warning: Positions file not found: {self.positions_file}")
            self._create_default_positions()
            return
        
        with open(self.positions_file, 'r') as f:
            data = json.load(f)
        
        for category, positions in data.items():
            self.positions[category] = [
                TestPosition(
                    id=p["id"],
                    name=p["name"],
                    fen=p["fen"],
                    description=p["description"],
                    expected_good_moves=p["expected_good_moves"],
                    category=p["category"],
                    difficulty=p["difficulty"]
                )
                for p in positions
            ]
    
    def _create_default_positions(self):
        """Create minimal default positions if file not found"""
        self.positions = {
            "opening_positions": [
                TestPosition(
                    id="default_001",
                    name="Starting Position",
                    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    description="Initial chess position",
                    expected_good_moves=["e2e4", "d2d4", "g1f3", "c2c4"],
                    category="opening",
                    difficulty="easy"
                )
            ]
        }
    
    def get_all_positions(self) -> List[TestPosition]:
        """Get all test positions"""
        all_positions = []
        for category_positions in self.positions.values():
            all_positions.extend(category_positions)
        return all_positions
    
    def get_positions_by_category(self, category: str) -> List[TestPosition]:
        """Get positions for a specific category"""
        return self.positions.get(category, [])
    
    def get_positions_by_difficulty(self, difficulty: str) -> List[TestPosition]:
        """Get positions by difficulty level"""
        result = []
        for positions in self.positions.values():
            result.extend([p for p in positions if p.difficulty == difficulty])
        return result
    
    def evaluate_agent(
        self, 
        agent,
        categories: Optional[List[str]] = None,
        verbose: bool = True
    ) -> BenchmarkResult:
        """
        Evaluate an agent on the benchmark suite.
        
        Args:
            agent: Chess agent implementing get_move(board_state)
            categories: List of categories to test (None = all)
            verbose: Print progress during evaluation
            
        Returns:
            BenchmarkResult with complete evaluation data
        """
        from datetime import datetime
        
        # Get positions to test
        if categories:
            positions = []
            for cat in categories:
                positions.extend(self.get_positions_by_category(cat))
        else:
            positions = self.get_all_positions()
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"CHESS BENCHMARK EVALUATION")
            print(f"Agent: {agent.agent_name}")
            print(f"Positions: {len(positions)}")
            print(f"{'='*60}\n")
        
        # Initialize result
        result = BenchmarkResult(
            agent_id=agent.agent_id,
            agent_name=agent.agent_name,
            timestamp=datetime.now().isoformat(),
            total_positions=len(positions)
        )
        
        # Category and difficulty tracking
        cat_counts = {}
        diff_counts = {}
        
        total_confidence = 0.0
        total_time = 0.0
        
        # Test each position
        for i, position in enumerate(positions):
            if verbose:
                print(f"[{i+1}/{len(positions)}] Testing: {position.name}")
            
            # Create board state
            board_state = {
                "fen": position.fen,
                "legal_moves": position.get_legal_moves(),
                "move_number": 1,
                "time_remaining": 600.0
            }
            
            # Get agent's move
            start_time = time.time()
            try:
                response = agent.get_move(board_state)
                thinking_time = time.time() - start_time
                
                agent_move = response.move_uci
                confidence = response.confidence or 0.5
                reasoning = response.reasoning or ""
            except Exception as e:
                thinking_time = time.time() - start_time
                agent_move = "error"
                confidence = 0.0
                reasoning = f"Error: {str(e)}"
            
            # Evaluate the move
            is_good = agent_move in position.expected_good_moves
            is_best = agent_move == position.expected_good_moves[0] if position.expected_good_moves else False
            
            # Create test result
            test_result = TestResult(
                position_id=position.id,
                position_name=position.name,
                category=position.category,
                difficulty=position.difficulty,
                agent_move=agent_move,
                is_good_move=is_good,
                is_best_move=is_best,
                confidence=confidence,
                reasoning=reasoning,
                thinking_time=thinking_time,
                expected_moves=position.expected_good_moves,
                legal_moves_count=len(position.get_legal_moves())
            )
            
            result.test_results.append(test_result)
            
            # Update counters
            if is_good:
                result.good_moves += 1
            if is_best:
                result.best_moves += 1
            
            total_confidence += confidence
            total_time += thinking_time
            
            # Category tracking
            if position.category not in cat_counts:
                cat_counts[position.category] = {"total": 0, "good": 0, "time": 0.0}
            cat_counts[position.category]["total"] += 1
            if is_good:
                cat_counts[position.category]["good"] += 1
            cat_counts[position.category]["time"] += thinking_time
            
            # Difficulty tracking
            if position.difficulty not in diff_counts:
                diff_counts[position.difficulty] = {"total": 0, "good": 0}
            diff_counts[position.difficulty]["total"] += 1
            if is_good:
                diff_counts[position.difficulty]["good"] += 1
            
            if verbose:
                status = "✓" if is_good else "✗"
                print(f"   {status} Move: {agent_move} (expected: {position.expected_good_moves[0]})")
                print(f"   Time: {thinking_time:.2f}s, Confidence: {confidence:.2f}")
        
        # Calculate final metrics
        result.accuracy = result.good_moves / max(1, result.total_positions)
        result.total_time = total_time
        result.avg_thinking_time = total_time / max(1, result.total_positions)
        result.avg_confidence = total_confidence / max(1, result.total_positions)
        
        # Category results
        for cat, data in cat_counts.items():
            result.category_results[cat] = {
                "total": data["total"],
                "good": data["good"],
                "accuracy": data["good"] / max(1, data["total"]),
                "avg_time": data["time"] / max(1, data["total"])
            }
        
        # Difficulty results
        for diff, data in diff_counts.items():
            result.difficulty_results[diff] = {
                "total": data["total"],
                "good": data["good"],
                "accuracy": data["good"] / max(1, data["total"])
            }
        
        if verbose:
            self._print_summary(result)
        
        return result
    
    def _print_summary(self, result: BenchmarkResult):
        """Print benchmark summary"""
        print(f"\n{'='*60}")
        print("BENCHMARK RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Agent: {result.agent_name}")
        print(f"Total Positions: {result.total_positions}")
        print(f"Good Moves: {result.good_moves} ({result.accuracy*100:.1f}%)")
        print(f"Best Moves: {result.best_moves}")
        print(f"Avg Thinking Time: {result.avg_thinking_time:.2f}s")
        print(f"Avg Confidence: {result.avg_confidence:.2f}")
        
        print(f"\nBy Category:")
        for cat, data in result.category_results.items():
            print(f"  {cat}: {data['good']}/{data['total']} ({data['accuracy']*100:.1f}%)")
        
        print(f"\nBy Difficulty:")
        for diff, data in result.difficulty_results.items():
            print(f"  {diff}: {data['good']}/{data['total']} ({data['accuracy']*100:.1f}%)")
        
        print(f"{'='*60}\n")
    
    def save_results(self, result: BenchmarkResult, output_dir: str = "results"):
        """Save benchmark results to JSON file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"benchmark_{result.agent_id}_{result.timestamp.replace(':', '-')}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"Results saved to: {filepath}")
        return filepath


