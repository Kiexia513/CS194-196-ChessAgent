# limingrui 

# Chess evaluation metrics - ACPL, move quality, tactical analysis

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import statistics
from config import (
    MOVE_QUALITY_THRESHOLDS,
    OPENING_END,
    MIDDLEGAME_END,
    interpolate_elo_from_acpl,
    get_skill_level_by_acpl
)


class SingleMovequalityCategory(Enum):
    # based on the Lichess/Chess.com standard
    BEST = "best"                    # best move (0 cp loss)
    EXCELLENT = "excellent"          # excellent move (≤10 cp loss)
    GOOD = "good"                    # good move (10-20 cp loss)
    INACCURACY = "inaccuracy"        # inaccuracy (20-40 cp loss)
    MISTAKE = "mistake"              # mistake (40-80 cp loss)
    BLUNDER = "blunder"              # blunder (80-150 cp loss)
    CATASTROPHIC = "catastrophic"    # catastrophic blunder (>150 cp loss)
    BOOK = "book"                    # opening book # TODO: write the function to detect the opening book
    NO_EVALUATION = "no_evaluation"  # no evaluation

@dataclass
class SingleMovequality:
    # single move quality evaluation

    move_number: int
    move_san: str
    move_uci: str
    player: str
    
    # Stockfish evaluation
    engine_evaluation: Optional[int] = None # board before the move
    best_move: Optional[str] = None
    best_move_evaluation: Optional[int] = None
    
    # move quality
    centipawn_loss: Optional[int] = None 
    category: SingleMovequalityCategory = SingleMovequalityCategory.GOOD
    
    # tactical information
    is_check: bool = False
    is_checkmate: bool = False
    is_capture: bool = False
    is_castling: bool = False
    is_promotion: bool = False 
    is_tactical: bool = False                   
    
    # time information
    thinking_time: float = 0.0
    time_pressure: bool = False
    
    def calculate_quality(self):
        # calculate the move quality category - using the thresholds in the configuration file
        if self.centipawn_loss is None:
            self.category = SingleMovequalityCategory.NO_EVALUATION
            return
        
        cp_loss = abs(self.centipawn_loss)
        
        # using the thresholds in the configuration file
        if cp_loss == MOVE_QUALITY_THRESHOLDS["best"]:
            self.category = SingleMovequalityCategory.BEST
        elif cp_loss <= MOVE_QUALITY_THRESHOLDS["excellent"]:
            self.category = SingleMovequalityCategory.EXCELLENT
        elif cp_loss <= MOVE_QUALITY_THRESHOLDS["good"]:
            self.category = SingleMovequalityCategory.GOOD
        elif cp_loss <= MOVE_QUALITY_THRESHOLDS["inaccuracy"]:
            self.category = SingleMovequalityCategory.INACCURACY
        elif cp_loss <= MOVE_QUALITY_THRESHOLDS["mistake"]:
            self.category = SingleMovequalityCategory.MISTAKE
        elif cp_loss <= MOVE_QUALITY_THRESHOLDS["blunder"]:
            self.category = SingleMovequalityCategory.BLUNDER
        else:
            self.category = SingleMovequalityCategory.CATASTROPHIC


@dataclass
class PhaseMetrics:
    # metrics for each phase
    phase_name: str                             # opening, middlegame, endgame
    move_count: int = 0                         
    acpl: float = 0.0                           # ACPL of the phase
    best_move_rate: float = 0.0                 # best move rate
    blunder_count: int = 0
    mistake_count: int = 0
    average_time: float = 0.0


@dataclass
class GameMetrics:
    # a data type to store the metrics for the whole game

    game_id: str
    white_player: str
    black_player: str
    result: Optional[str] = None                 # "1-0", "0-1", "1/2-1/2"
    
    # main metrics
    white_acpl: float = 0.0                      # white's ACPL during whole game
    black_acpl: float = 0.0                      # black's ACPL during whole game
    
    # move quality statistics
    white_move_quality: Dict[str, int] = field(default_factory=dict)
    black_move_quality: Dict[str, int] = field(default_factory=dict)
    
    # tactical statistics
    # TODO: write the function to detect the tactical moves
    white_tactical_moves: int = 0
    black_tactical_moves: int = 0
    white_blunders: int = 0
    black_blunders: int = 0
    white_mistakes: int = 0
    black_mistakes: int = 0
    
    # phase performance
    white_opening: Optional[PhaseMetrics] = None
    white_middlegame: Optional[PhaseMetrics] = None
    white_endgame: Optional[PhaseMetrics] = None
    black_opening: Optional[PhaseMetrics] = None
    black_middlegame: Optional[PhaseMetrics] = None
    black_endgame: Optional[PhaseMetrics] = None
    
    # time management
    white_total_time: float = 0.0
    black_total_time: float = 0.0
    white_time_pressure_moves: int = 0
    black_time_pressure_moves: int = 0
    
    # raw data for whole game
    move_evaluations: List[SingleMovequality] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        # convert to dictionary format

        def _derived_counts(move_quality: Dict[str, int]) -> Dict[str, Any]:
            best = move_quality.get(SingleMovequalityCategory.BEST.value, 0)
            excellent = move_quality.get(SingleMovequalityCategory.EXCELLENT.value, 0)
            good = move_quality.get(SingleMovequalityCategory.GOOD.value, 0)
            inaccuracy = move_quality.get(SingleMovequalityCategory.INACCURACY.value, 0)
            mistake = move_quality.get(SingleMovequalityCategory.MISTAKE.value, 0)
            blunder = move_quality.get(SingleMovequalityCategory.BLUNDER.value, 0)
            catastrophic = move_quality.get(SingleMovequalityCategory.CATASTROPHIC.value, 0)
            no_eval = move_quality.get(SingleMovequalityCategory.NO_EVALUATION.value, 0)

            evaluated_moves = max(0, sum(move_quality.values()) - no_eval)
            best_rate = (best / evaluated_moves) if evaluated_moves else 0.0

            return {
                "best_moves": best,
                # Many UIs treat Excellent+Good as "good moves"
                "good_moves": excellent + good,
                "inaccuracies": inaccuracy,
                "mistakes": mistake,
                # Treat catastrophic blunders as blunders for summary display
                "blunders": blunder + catastrophic,
                "evaluated_moves": evaluated_moves,
                "best_move_rate": round(best_rate, 3),
            }

        # calculate ELO estimation
        white_elo = interpolate_elo_from_acpl(self.white_acpl)
        black_elo = interpolate_elo_from_acpl(self.black_acpl)
        white_level = get_skill_level_by_acpl(self.white_acpl)
        black_level = get_skill_level_by_acpl(self.black_acpl)
        
        return {
            "game_id": self.game_id,
            "white_player": self.white_player,
            "black_player": self.black_player,
            "result": self.result,
            "metrics": {
                "white": {
                    "acpl": round(self.white_acpl, 2),
                    "estimated_elo": white_elo,
                    "skill_level": white_level,
                    "blunders": self.white_blunders,
                    "mistakes": self.white_mistakes,
                    "tactical_moves": self.white_tactical_moves,
                    "total_time": round(self.white_total_time, 2),
                    **_derived_counts(self.white_move_quality),
                    "move_quality": self.white_move_quality,
                },
                "black": {
                    "acpl": round(self.black_acpl, 2),
                    "estimated_elo": black_elo,
                    "skill_level": black_level,
                    "blunders": self.black_blunders,
                    "mistakes": self.black_mistakes,
                    "tactical_moves": self.black_tactical_moves,
                    "total_time": round(self.black_total_time, 2),
                    **_derived_counts(self.black_move_quality),
                    "move_quality": self.black_move_quality,
                }
            }
        }


class MetricsCollector:
    """
    metrics collector for the whole game
    """
    
    def __init__(self, game_id: str, white_player: str = "White", black_player: str = "Black"):
        self.metrics = GameMetrics(
            game_id=game_id,
            white_player=white_player,
            black_player=black_player
        )
        
        # initialize the move quality count
        for category in SingleMovequalityCategory:
            self.metrics.white_move_quality[category.value] = 0
            self.metrics.black_move_quality[category.value] = 0
    
    def add_move_evaluation(self, move_quality: SingleMovequality):
        # add single move evaluation
        self.metrics.move_evaluations.append(move_quality)
        
        # update the move quality statistics
        if move_quality.player == "white":
            self.metrics.white_move_quality[move_quality.category.value] += 1
            if move_quality.category in (SingleMovequalityCategory.BLUNDER, SingleMovequalityCategory.CATASTROPHIC):
                self.metrics.white_blunders += 1
            elif move_quality.category == SingleMovequalityCategory.MISTAKE:
                self.metrics.white_mistakes += 1
            if move_quality.is_tactical:
                self.metrics.white_tactical_moves += 1
            self.metrics.white_total_time += move_quality.thinking_time
        else:
            self.metrics.black_move_quality[move_quality.category.value] += 1
            if move_quality.category in (SingleMovequalityCategory.BLUNDER, SingleMovequalityCategory.CATASTROPHIC):
                self.metrics.black_blunders += 1
            elif move_quality.category == SingleMovequalityCategory.MISTAKE:
                self.metrics.black_mistakes += 1
            if move_quality.is_tactical:
                self.metrics.black_tactical_moves += 1
            self.metrics.black_total_time += move_quality.thinking_time
    
    def calculate_acpl(self):
        # calculate the ACPL of both players
        white_losses = []
        black_losses = []
        
        for move_eval in self.metrics.move_evaluations:
            if move_eval.centipawn_loss is not None:
                if move_eval.player == "white":
                    white_losses.append(abs(move_eval.centipawn_loss))
                else:
                    black_losses.append(abs(move_eval.centipawn_loss))
        
        self.metrics.white_acpl = statistics.mean(white_losses) if white_losses else 0.0
        self.metrics.black_acpl = statistics.mean(black_losses) if black_losses else 0.0
    
    def calculate_phase_metrics(self):
        # calculate the metrics for each phase - using the boundaries in the configuration file

        opening_end = OPENING_END
        middlegame_end = MIDDLEGAME_END
        
        white_opening_moves = []
        white_middlegame_moves = []
        white_endgame_moves = []
        black_opening_moves = []
        black_middlegame_moves = []
        black_endgame_moves = []
        
        for move_eval in self.metrics.move_evaluations:
            move_num = move_eval.move_number
            
            # assign to the phase
            if move_num <= opening_end * 2:
                if move_eval.player == "white":
                    white_opening_moves.append(move_eval)
                else:
                    black_opening_moves.append(move_eval)
            elif move_num <= middlegame_end * 2:
                if move_eval.player == "white":
                    white_middlegame_moves.append(move_eval)
                else:
                    black_middlegame_moves.append(move_eval)
            else:
                if move_eval.player == "white":
                    white_endgame_moves.append(move_eval)
                else:
                    black_endgame_moves.append(move_eval)
        
        # calculate the metrics for each phase
        self.metrics.white_opening = self._calculate_phase_stats("opening", white_opening_moves)
        self.metrics.white_middlegame = self._calculate_phase_stats("middlegame", white_middlegame_moves)
        self.metrics.white_endgame = self._calculate_phase_stats("endgame", white_endgame_moves)
        self.metrics.black_opening = self._calculate_phase_stats("opening", black_opening_moves)
        self.metrics.black_middlegame = self._calculate_phase_stats("middlegame", black_middlegame_moves)
        self.metrics.black_endgame = self._calculate_phase_stats("endgame", black_endgame_moves)
    
    def _calculate_phase_stats(self, phase_name: str, moves: List[SingleMovequality]) -> PhaseMetrics:
        # calculate the statistics for a single phase
        if not moves:
            return PhaseMetrics(phase_name=phase_name)
        
        cp_losses = [abs(m.centipawn_loss) for m in moves if m.centipawn_loss is not None]
        acpl = statistics.mean(cp_losses) if cp_losses else 0.0
        
        best_moves = sum(1 for m in moves if m.category == SingleMovequalityCategory.BEST)
        best_move_rate = best_moves / len(moves) if moves else 0.0
        
        blunders = sum(1 for m in moves if m.category == SingleMovequalityCategory.BLUNDER)
        mistakes = sum(1 for m in moves if m.category == SingleMovequalityCategory.MISTAKE)
        
        times = [m.thinking_time for m in moves]
        avg_time = statistics.mean(times) if times else 0.0
        
        return PhaseMetrics(
            phase_name=phase_name,
            move_count=len(moves),
            acpl=acpl,
            best_move_rate=best_move_rate,
            blunder_count=blunders,
            mistake_count=mistakes,
            average_time=avg_time
        )
    
    def finalize(self, result: str):
        # finalize the metrics collection, calculate all the statistics
        self.metrics.result = result
        self.calculate_acpl()
        self.calculate_phase_metrics()
    
    def get_metrics(self) -> GameMetrics:
        # get the complete metrics
        return self.metrics
    
    def get_summary(self) -> str:
        # get the summary of the metrics - including ELO estimation

        white_elo = interpolate_elo_from_acpl(self.metrics.white_acpl)
        black_elo = interpolate_elo_from_acpl(self.metrics.black_acpl)
        white_level = get_skill_level_by_acpl(self.metrics.white_acpl)
        black_level = get_skill_level_by_acpl(self.metrics.black_acpl)
        
        summary = f"""
🏆 CHESS GAME ASSESSMENT REPORT 🏆

Game ID: {self.metrics.game_id}
Result:  {self.metrics.result or 'N/A'}
Total Moves: {len(self.metrics.move_evaluations)}

⚪ WHITE PLAYER: {self.metrics.white_player}
   ACPL: {self.metrics.white_acpl:6.2f}  |  ELO: {white_elo:4d}
   Level: {white_level}
   Mistakes: {self.metrics.white_mistakes:2d}  |  Blunders: {self.metrics.white_blunders:2d}
   Tactical Moves: {self.metrics.white_tactical_moves:2d}  |  Time: {self.metrics.white_total_time:6.1f}s

⚫ BLACK PLAYER: {self.metrics.black_player}
   ACPL: {self.metrics.black_acpl:6.2f}  |  ELO: {black_elo:4d}
   Level: {black_level}
   Mistakes: {self.metrics.black_mistakes:2d}  |  Blunders: {self.metrics.black_blunders:2d}
   Tactical Moves: {self.metrics.black_tactical_moves:2d}  |  Time: {self.metrics.black_total_time:6.1f}s
"""
        return summary
