# limingrui

# Chess Green Agent - Orchestrates and evaluates chess games

import time
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from environment import ChessEnvironment, MoveRequest, GameStatus
from evaluation import MetricsCollector, StockfishEvaluator, SingleMovequality
from .agent_interface import AgentInterface, AgentResponse


class ChessGreenAgent:
    def __init__(
        self,
        agent_id: str = "chess_green_agent",
        use_stockfish: bool = True,
        log_dir: Optional[str] = None
    ):
        """
        Initialize the Green Agent

        Args:
            agent_id: unique identifier for this green agent
            use_stockfish: whether to use Stockfish for evaluation
            log_dir: directory to save logs and results
        """
        print("\n=== [Step 1] Initializing Green Agent ===")

        self.agent_id = agent_id
        self.use_stockfish = use_stockfish
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize evaluator if needed
        self.evaluator = StockfishEvaluator() if use_stockfish else None

        # Game history
        self.games_history: List[Dict[str, Any]] = []

        print(f"1.1 Agent ID: {agent_id}")
        print(f"1.2 Log directory: {self.log_dir.resolve()}")

        if use_stockfish and self.evaluator and self.evaluator.is_available():
            print(f"1.3 Stockfish engine: Available")
        else:
            print(f"1.3 Stockfish engine: Not available — evaluation will be limited")
    
    def _evaluate_move_with_stockfish(
        self,
        env,
        move,
        move_uci: str,
        move_count: int,
        current_player: str,
        thinking_time: float
    ) -> Optional[SingleMovequality]:
        """
        Evaluate a move using Stockfish engine
        
        Args:
            env: ChessEnvironment instance
            move: chess.Move object
            move_uci: UCI notation of the move
            move_count: current move number
            current_player: player making the move
            thinking_time: time spent thinking
            
        Returns:
            SingleMovequality object if evaluation successful, None otherwise
        """
        if not self.evaluator or not self.evaluator.is_available():
            return None
        
        try:
            # Get SAN notation before executing move
            move_san_notation = env.board.san(move)
            
            # Evaluate with Stockfish
            eval_result = self.evaluator.evaluate_move(env.board, move)
            
            if eval_result["available"]:
                move_quality = SingleMovequality(
                    move_number=move_count,
                    move_san=move_san_notation,
                    move_uci=move_uci,
                    player=current_player,
                    engine_evaluation=eval_result["eval_after"],
                    best_move=eval_result["best_move"],
                    best_move_evaluation=eval_result["best_eval"],
                    centipawn_loss=eval_result["centipawn_loss"],
                    thinking_time=thinking_time,
                    is_check=env.board.gives_check(move),
                    is_capture=env.board.is_capture(move),
                    is_castling=env.board.is_castling(move)
                )
                move_quality.calculate_quality()
                return move_quality
        except Exception as e:
            print(f"   ⚠️  Stockfish evaluation error: {e}")
        
        return None

    def prepare_environment(self, game_id: str) -> 'ChessEnvironment':
        """
        Prepare the chess environment for a game
        """
        print("\n=== [Step 2] Preparing Game Environment ===")
        print(f"2.1 Target game ID: {game_id}")

        env = ChessEnvironment(game_id=game_id)

        print("2.2 Environment object created successfully")
        print("2.3 Initial board position loaded (starting FEN)")
        print("=== ✅ Environment preparation complete ===\n")

        return env

    def verify_environment(self, env: 'ChessEnvironment') -> bool:
        """
        Verify the environment is in a valid state
        """
        print("\n=== [Step 3] Verifying Environment State ===")
        try:
            board_state = env.get_board_state()

            print("3.1 Environment verification passed")
            print(f"3.2 FEN: {board_state.fen}")
            print(f"3.3 Legal moves available: {len(board_state.legal_moves)}")
            print(f"3.4 Current player to move: {board_state.current_player}")
            print("=== ✅ Environment verification successful ===\n")

            return True
        except Exception as e:
            print("3.1 Environment verification failed")
            print(f"3.2 Error details: {e}")
            print("=== ⚠️ Environment verification aborted ===\n")
            return False

    # TODO: may rewrite the run_game to several sub-functions, e.g. validate_move, evaluate_move, execute_move, etc.
    def run_game(
        self,
        white_agent: AgentInterface,
        black_agent: AgentInterface,
        game_id: Optional[str] = None,
        max_moves: int = 300
    ) -> Dict[str, Any]:
        """
        Run a complete chess game between two agents
        
        Args:
            white_agent: agent playing white
            black_agent: agent playing black
            game_id: unique identifier for the game
            max_moves: maximum number of moves before draw
            
        Returns:
            Dictionary containing game results and metrics
        """
        if game_id is None:
            game_id = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Step 1: Prepare environment
        env = self.prepare_environment(game_id)
        
        # Step 2: Verify environment
        if not self.verify_environment(env):
            return {"error": "Environment verification failed"}
        
        print(f"\n{'='*80}")
        print(f"🎮 STARTING GAME: {game_id}")
        print(f"{'='*80}")
        print(f"⚪ White: {white_agent.agent_name}")
        print(f"⚫ Black: {black_agent.agent_name}")
        print(f"{'='*80}\n")

        # Step 3: Reset agents
        white_agent.reset()
        black_agent.reset()
        
        # Step 4: Initialize metrics collector
        metrics_collector = MetricsCollector(
            game_id=game_id,
            white_player=white_agent.agent_name,
            black_player=black_agent.agent_name
        )
        
        # Step 5: Game loop
        game_log = []
        move_count = 0
        
        while move_count < max_moves:
            move_count += 1
            
            # Get current board state
            board_state = env.get_board_state()
            
            # Check if game is over
            if board_state.is_checkmate:
                print(f"\n🏁 Game Over: Checkmate")
                break
            elif board_state.is_stalemate:
                print(f"\n🏁 Game Over: Stalemate")
                break
            
            # Determine current player
            current_agent = white_agent if env.board.turn else black_agent
            current_player = "white" if env.board.turn else "black"
            
            print(f"\n📍 Move {move_count} - {current_player.upper()}'s turn")
            
            # Get agent's move (LLM must rely on FEN only)
            # Include legal_moves for fallback random selection if LLM fails
            agent_state = {
                "fen": board_state.fen,
                "time_remaining": board_state.time_remaining.get("white" if env.board.turn else "black", 0),
                "move_number": move_count,
                "legal_moves": [move.uci() for move in env.board.legal_moves]  # For random fallback
            }
            
            try:
                # Get move from agent with retry logic for illegal moves, maximum 3 retries
                max_retries = 3
                retry_count = 0

                # initialize the move response, feedback, agent response, and thinking time
                move_response = None
                feedback = None
                agent_response = None
                thinking_time = 0
                
                while retry_count <= max_retries:
                    # Get move from agent, given only the FEN string
                    start_time = time.time()

                    # (e.g. llm_agent.py: get_move(agent_state))
                    agent_response = current_agent.get_move(agent_state)

                    thinking_time_attempt = time.time() - start_time
                    
                    thinking_time += thinking_time_attempt
                    
                    if retry_count > 0:
                        print(f"   Retry {retry_count}: {agent_response.move_uci} (thinking: {thinking_time_attempt:.2f}s)")
                    else:
                        print(f"   Move: {agent_response.move_uci} (thinking: {thinking_time_attempt:.2f}s)")                    

                    # the following are the steps to validate and evaluate the move
                    # First, try to validate and evaluate move with Stockfish (BEFORE executing)
                    move_quality = None
                    
                    try:
                        import chess
                        move = chess.Move.from_uci(agent_response.move_uci)
                        
                        # Check if move is legal (basic validation)
                        if move in env.board.legal_moves:
                            # Evaluate move with Stockfish
                            move_quality = self._evaluate_move_with_stockfish(
                                env, move, agent_response.move_uci, 
                                move_count, current_player, thinking_time
                            )
                            
                            if move_quality:
                                metrics_collector.add_move_evaluation(move_quality)
                                print(f"   Quality: {move_quality.category.value} (CP loss: {move_quality.centipawn_loss})")
                    
                    except Exception as eval_error:
                        print(f"   ⚠️  Evaluation error: {eval_error}")
                    
                    # Display LLM's reasoning
                    if agent_response.reasoning:
                        reasoning_preview = agent_response.reasoning[:500]
                        print(f"   💭 LLM Reasoning: {reasoning_preview}")
                    if agent_response.confidence:
                        print(f"   🎯 Confidence: {agent_response.confidence:.2f}")
                    
                    # Now execute move in environment
                    move_request = MoveRequest(
                        move=agent_response.move_uci,
                        thinking_time=thinking_time
                    )
                    move_response, feedback = env.make_move(move_request)
                    
                    # Check if move was successful
                    if move_response.status == "success":
                        break
                    else:
                        # Illegal or invalid move
                        retry_count += 1
                        if retry_count <= max_retries:
                            print(f"   ⚠️  Illegal move! {move_response.message}")
                            # Update agent state with error feedback for retry
                            # TODO: may distinguish invalid or illegal move
                            agent_state["last_error"] = move_response.message
                            agent_state["illegal_move"] = agent_response.move_uci

                        # Max retries exceeded, use random legal move
                        else:
                            # TODO: use another penalty for max retries exceeded instead of using random move
                            # TODO: really make the agent penalized for max retries exceeded!
                            import random
                            legal_moves_list = list(env.board.legal_moves)
                            random_move = random.choice(legal_moves_list)
                            print(f"   ❌ Max retries exceeded! Using random move: {random_move.uci()}")
                            
                            # Evaluate random move with Stockfish
                            move_quality = self._evaluate_move_with_stockfish(
                                env, random_move, random_move.uci(),
                                move_count, current_player, thinking_time
                            )
                            
                            if move_quality:
                                metrics_collector.add_move_evaluation(move_quality)
                            
                            # Execute random move
                            move_request = MoveRequest(
                                move=random_move.uci(),
                                thinking_time=thinking_time
                            )
                            move_response, feedback = env.make_move(move_request)
                            agent_response.move_uci = random_move.uci()
                            break
                
                # Get updated board state after move
                updated_board_state = env.get_board_state()

                # Display current board position
                print("\n" + env._board_to_ascii())

                # Log move (including ASCII board and LLM reasoning)
                # Save ASCII board as array of lines for better readability in JSON
                board_ascii_lines = env._board_to_ascii().strip().split('\n')
                
                move_log = {
                    "move_number": move_count,
                    "player": current_player,
                    "move_uci": agent_response.move_uci,
                    "move_san": move_response.san_notation,
                    "thinking_time": thinking_time,
                    "time_remaining": updated_board_state.time_remaining.get(current_player, 0),
                    "llm_reasoning": agent_response.reasoning,  # LLM's reasoning
                    "llm_confidence": agent_response.confidence,  # LLM's confidence
                    "move_quality": move_quality.category.value if move_quality else None,
                    "centipawn_loss": move_quality.centipawn_loss if move_quality else None,
                    "fen_after": move_response.new_fen,
                    "board_ascii": board_ascii_lines,
                    "feedback": feedback.message
                }
                game_log.append(move_log)
                
                # Check for game over
                if move_response.is_checkmate:
                    print(f"\n🎉 Checkmate! {current_player.upper()} wins!")
                    break
                
                # Check board state for other game ending conditions
                updated_board_state_check = env.get_board_state()
                if updated_board_state_check.is_stalemate:
                    print(f"\n🤝 Stalemate - Draw!")
                    break
                
            except Exception as e:
                print(f"❌ Error during move {move_count}: {e}")
                game_log.append({
                    "move_number": move_count,
                    "player": current_player,
                    "error": str(e)
                })
                break
        

        # Step 6: Finalize metrics
        board_state = env.get_board_state()
        result = self._determine_result(board_state)
        metrics_collector.finalize(result)
        
        # Step 7: Generate report
        print(f"\n{'='*80}")
        print(metrics_collector.get_summary())
        print(f"{'='*80}\n")
        
        # Step 8: Compile results
        # Save final board as array of lines for better readability in JSON
        final_board_lines = env._board_to_ascii().strip().split('\n')
        
        game_results = {
            "game_id": game_id,
            "white_agent": white_agent.get_info(),
            "black_agent": black_agent.get_info(),
            "result": result,
            "total_moves": move_count,
            "metrics": metrics_collector.get_metrics().to_dict(),
            "game_log": game_log,
            "pgn": env._generate_pgn(),
            "final_fen": board_state.fen,
            "final_board_ascii": final_board_lines,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to history
        self.games_history.append(game_results)
        
        # Save to file
        self._save_game_results(game_results)
        
        return game_results
    
    def _determine_result(self, board_state) -> str:
        """Determine game result from board state"""
        if board_state.is_checkmate:
            return "1-0" if board_state.current_player == "black" else "0-1"
        elif board_state.is_stalemate:
            return "1/2-1/2"
        else:
            return "*"  # Game ongoing or aborted
    
    def _save_game_results(self, game_results: Dict[str, Any]):
        """Save game results to file"""
        filename = f"{game_results['game_id']}.json"
        filepath = self.log_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(game_results, f, indent=2, ensure_ascii=False)
            print(f" Game results saved to: {filepath}")
            
            # Generate visualization reports
            try:
                self._generate_visualizations(game_results)
            except Exception as viz_error:
                print(f" Warning: Failed to generate visualizations: {viz_error}")
        except Exception as e:
            print(f" Failed to save game results: {e}")
    
    def _generate_visualizations(self, game_results: Dict[str, Any]):
        """Generate visualization reports for the game"""
        try:
            # Try relative import first, then absolute
            try:
                from ..visualization import HTMLReporter, ChartGenerator, GameReplay
            except ImportError:
                from visualization import HTMLReporter, ChartGenerator, GameReplay
            
            print("\n Generating visualizations...")
            
            # Generate HTML report
            html_reporter = HTMLReporter(output_dir=str(self.log_dir.parent / "reports"))
            html_file = html_reporter.generate_game_report(game_results, include_charts=True)
            print(f" HTML report saved to: {html_file}")
            
            # Generate charts
            chart_generator = ChartGenerator(output_dir=str(self.log_dir.parent / "charts"))
            charts = chart_generator.generate_all_charts(game_results, game_results['game_id'])
            print(f" Charts saved: {len(charts)} files")
            for chart_name, chart_path in charts.items():
                print(f"   - {chart_name}: {chart_path}")
            
            # Generate game replay
            game_replay = GameReplay()
            replay_file = game_replay.generate_replay_html(
                game_results, 
                output_path=self.log_dir.parent / "reports" / f"{game_results['game_id']}_replay.html"
            )
            print(f" Game replay saved to: {replay_file}")
            
        except ImportError as e:
            print(f" Visualization modules not available: {e}")
            print(" Install matplotlib for chart generation: pip install matplotlib")
    
    def get_agent_summary(self, agent_name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a specific agent across all games
        """
        games_as_white = []
        games_as_black = []
        
        for game in self.games_history:
            if game["white_agent"]["agent_name"] == agent_name:
                games_as_white.append(game)
            elif game["black_agent"]["agent_name"] == agent_name:
                games_as_black.append(game)
        
        total_games = len(games_as_white) + len(games_as_black)
        
        if total_games == 0:
            return {"error": f"No games found for agent: {agent_name}"}
        
        # Calculate statistics
        wins = 0
        draws = 0
        losses = 0
        total_acpl = 0
        
        for game in games_as_white:
            result = game["result"]
            if result == "1-0":
                wins += 1
            elif result == "1/2-1/2":
                draws += 1
            else:
                losses += 1
            total_acpl += game["metrics"]["metrics"]["white"]["acpl"]
        
        for game in games_as_black:
            result = game["result"]
            if result == "0-1":
                wins += 1
            elif result == "1/2-1/2":
                draws += 1
            else:
                losses += 1
            total_acpl += game["metrics"]["metrics"]["black"]["acpl"]
        
        avg_acpl = total_acpl / total_games
        
        return {
            "agent_name": agent_name,
            "total_games": total_games,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "win_rate": wins / total_games,
            "average_acpl": avg_acpl,
            "games_as_white": len(games_as_white),
            "games_as_black": len(games_as_black)
        }
    
    def close(self):
        # close the evaluator
        if self.evaluator:
            self.evaluator.close()
        print("✅ Green Agent closed")

