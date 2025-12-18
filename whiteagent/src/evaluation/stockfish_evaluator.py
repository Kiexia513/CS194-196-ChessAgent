# limingrui 

# Stockfish chess engine integration for move evaluation

import chess
import chess.engine
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from config import get_stockfish_path, STOCKFISH_DEPTH, STOCKFISH_TIME_LIMIT


class StockfishEvaluator:
    """
    Stockfish engine evaluator
    """
    
    def __init__(
        self,
        depth: Optional[int] = None,
        time_limit: Optional[float] = None
    ):
        """
        initialize Stockfish evaluator
        
        Args:
            depth: analysis depth (default: from config)
            time_limit: time limit for each analysis in seconds (default: from config)
        """
        self.depth = depth if depth is not None else STOCKFISH_DEPTH
        self.time_limit = time_limit if time_limit is not None else STOCKFISH_TIME_LIMIT
        self.engine: Optional[chess.engine.SimpleEngine] = None
        
        # get Stockfish path from config
        self.stockfish_path = get_stockfish_path()
        
        # initialize the engine
        if self.stockfish_path:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
                print(f"1.0 Stockfish engine initialized successfully: {self.stockfish_path}")
            except Exception as e:
                print(f"1.0 Error: Stockfish engine initialization failed: {e}")
                print(f"    Cannot perform move quality evaluation")
        else:
            print("1.0 Error: Stockfish engine not found")
            print("    Please download Stockfish and set the path")
            print("    Download address: https://stockfishchess.org/download/")
    
    
    def is_available(self) -> bool:
        return self.engine is not None
    
    def evaluate_position(self, board: chess.Board) -> Optional[int]:
        """
        evaluate the position
        
        Args:
            board: the chess board object
            
        Returns:
            the evaluation score (in centipawns), from the current player's perspective
            positive value means current player advantage, negative value means disadvantage
            None means the engine is not available
        """
        if not self.is_available():
            return None
        
        try:
            info = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.depth, time=self.time_limit)
            )
            
            score = info["score"].relative
            
            # convert to centipawns
            if score.is_mate():
                # if the game is mate, return a large value
                # TODO: maybe use a more reasonable value instead of 10000
                mate_in = score.mate() # if the current player is mated, mate_in < 0
                return 10000 if mate_in > 0 else -10000
            else:
                return score.score()
        
        except Exception as e:
            print(f" evaluation failed: {e}")
            return None
    
    def get_best_move(self, board: chess.Board) -> Optional[Tuple[str, int]]:
        """
        get the best move to a certain position
        
        Args:
            board: the chess board object
            
        Returns:
            (the best move UCI, the evaluation score) or None
        """
        if not self.is_available():
            return None
        
        try:
            result = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.depth, time=self.time_limit)
            )


            best_move = result["pv"][0] if "pv" in result and result["pv"] else None
            
            if best_move:
                # TODO: maybe use a more reasonable value instead of 10000
                score = result["score"].relative
                score_cp = score.score() if not score.is_mate() else (10000 if score.mate() > 0 else -10000)
                return (best_move.uci(), score_cp)
            
            return None

        except Exception as e:
            print(f" get the best move failed: {e}")
            return None
    
    # main function to evaluate the quality of a move
    def evaluate_move(self, board: chess.Board, move: chess.Move) -> Dict[str, Any]:
        """
        evaluate the quality of a specific move
        
        Args:
            board: the chess board object
            move: the move to evaluate
            
        Returns:
            a dictionary containing the evaluation information
        """
        if not self.is_available():
            return {"available": False, "error": "Stockfish engine not available"}

        # evaluate the position before the move (from the current player's perspective)
        eval_before = self.evaluate_position(board)

        # get the best move and the corresponding evaluation
        best_move_info = self.get_best_move(board)
        best_move_uci = best_move_info[0] if best_move_info else None
        best_eval = best_move_info[1] if best_move_info else None

        # execute the move
        board_after = board.copy()
        board_after.push(move)

        # evaluate the position after the move (from the opponent's perspective)
        eval_after_opponent = self.evaluate_position(board_after)
        eval_after = -eval_after_opponent if eval_after_opponent is not None else None

        # calculate the centipawn loss
        centipawn_loss = None
        if best_eval is not None and eval_after is not None:
            centipawn_loss = best_eval - eval_after
            centipawn_loss = max(0, centipawn_loss)  # loss cannot be negative

        return {
            "available": True,
            "eval_before": eval_before,
            "eval_after": eval_after,
            "best_move": best_move_uci,
            "best_eval": best_eval,
            "centipawn_loss": centipawn_loss,
            "is_best_move": move.uci() == best_move_uci if best_move_uci else False
        }

    
    def close(self):
        if self.engine:
            try:
                self.engine.quit()
                print(" Stockfish engine closed")
            except Exception:
                pass
            finally:
                self.engine = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __del__(self):
        try:
            if self.engine:
                self.close()
        except Exception:
            pass


def download_stockfish_instructions():
    from config import print_stockfish_instructions
    print_stockfish_instructions()

