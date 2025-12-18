"""
Play Chess with White Agent - Detailed Module Output
=====================================================

Shows the complete decision-making process of White Agent:
1. Perception Module analysis
2. Memory Module context
3. Reasoning Module candidates
4. LLM final decision
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from white_agent import WhiteAgent
from white_agent.agent import AgentConfig
from green_agent import ChessGreenAgent, SimpleGreedyAgent, DeepSeekAgent
from config.api_config import get_api_key
from evaluation import StockfishEvaluator
import chess


def print_module_outputs(white_agent, board_state, move_number):
    """Print detailed output from each White Agent module"""
    
    print(f"\n{'='*80}")
    print(f"WHITE AGENT - Move {move_number} - DETAILED DECISION PROCESS")
    print(f"{'='*80}")
    
    # Show current board
    board = chess.Board(board_state["fen"])
    print(f"\nCurrent Board:")
    print(board)
    print(f"\nFEN: {board_state['fen']}")
    
    # 1. PERCEPTION MODULE
    print(f"\n{'-'*80}")
    print("[1] PERCEPTION MODULE - Position Analysis")
    print(f"{'-'*80}")
    
    analysis = white_agent.perception.analyze(board_state)
    
    print(f"\n[Basic Info]:")
    print(f"   Side to move: {analysis.side_to_move.upper()}")
    print(f"   Move number: {analysis.move_number}")
    print(f"   Legal moves: {analysis.legal_moves_count}")
    
    print(f"\n[Material Balance]:")
    if analysis.material_balance > 0:
        print(f"   White advantage: +{analysis.material_balance}")
    elif analysis.material_balance < 0:
        print(f"   Black advantage: {analysis.material_balance}")
    else:
        print(f"   Equal material")
    
    print(f"   White pieces: {dict(analysis.white_pieces)}")
    print(f"   Black pieces: {dict(analysis.black_pieces)}")
    
    print(f"\n[Position Features]:")
    print(f"   Center control: {analysis.center_control}")
    print(f"   King safety (White): {analysis.king_safety['white']}")
    print(f"   King safety (Black): {analysis.king_safety['black']}")
    
    print(f"\n[Tactical Situation]:")
    print(f"   In check: {'Yes' if analysis.checks else 'No'}")
    print(f"   Captures available: {len(analysis.captures_available)}")
    if analysis.captures_available:
        print(f"   Capture moves: {', '.join(analysis.captures_available[:5])}")
    
    print(f"\n[Position Description]:")
    print(f"   {analysis.position_description}")
    
    # 2. MEMORY MODULE
    print(f"\n{'-'*80}")
    print("[2] MEMORY MODULE - Game Context")
    print(f"{'-'*80}")
    
    memory_context = white_agent.memory.get_context_for_prompt()
    
    print(f"\n[Game History]:")
    game_stats = memory_context.get('game_statistics', {})
    total_moves = game_stats.get('total_moves', 0)
    print(f"   Total moves: {total_moves}")
    
    # Get recent moves directly from memory
    recent_moves = white_agent.memory.get_recent_moves(5)
    if recent_moves and len(recent_moves) > 0:
        print(f"   Recent moves:")
        for move_record in recent_moves[-3:]:  # Last 3 moves
            print(f"      Move {move_record.move_number}: {move_record.move_uci} ({move_record.side})")
    else:
        print(f"   No moves yet (opening position)")
    
    print(f"\n[Game Statistics]:")
    print(f"   Captures made: {game_stats.get('our_captures', 0)}")
    print(f"   Checks given: {game_stats.get('our_checks', 0)}")
    
    opening = memory_context.get('opening', 'Unknown')
    print(f"\n[Opening Recognition]:")
    print(f"   Detected opening: {opening}")
    
    opponent_style = memory_context.get('opponent_style', 'unknown')
    if opponent_style != 'unknown':
        print(f"\n[Opponent Analysis]:")
        print(f"   Playing style: {opponent_style}")
    
    # 3. REASONING MODULE
    print(f"\n{'-'*80}")
    print("[3] REASONING MODULE - Candidate Generation & Analysis")
    print(f"{'-'*80}")
    
    candidates = white_agent.reasoning.generate_candidate_moves(
        board_state["fen"],
        analysis.legal_moves
    )
    
    print(f"\n[Generated {len(candidates)} candidate moves]:")
    
    # Analyze top candidates
    top_candidates = []
    board_for_moves = chess.Board(board_state["fen"])
    
    for i, (move_uci, category) in enumerate(candidates[:5]):  # Top 5
        # Get move description from chess library
        move = chess.Move.from_uci(move_uci)
        piece = board_for_moves.piece_at(move.from_square)
        piece_name = piece.symbol().upper() if piece else "?"
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)
        
        move_description = f"{piece_name} from {from_sq} to {to_sq}"
        
        # Check if capture
        if board_for_moves.is_capture(move):
            captured = board_for_moves.piece_at(move.to_square)
            if captured:
                move_description += f" (captures {captured.symbol()})"
        
        # Simple scoring
        score = 0.8 if category == "captures" else 0.6 if category == "checks" else 0.5
        
        print(f"\n   Candidate {i+1}: {move_uci} [{category.upper()}]")
        print(f"      Description: {move_description}")
        print(f"      Estimated score: {score:.2f}")
        
        top_candidates.append({
            "move": move_uci,
            "category": category,
            "description": move_description,
            "score": score
        })
    
    print(f"\n[All legal moves]: {len(analysis.legal_moves)} options")
    print(f"   {', '.join(analysis.legal_moves[:15])}{'...' if len(analysis.legal_moves) > 15 else ''}")
    
    # 4. LLM DECISION
    print(f"\n{'-'*80}")
    print("[4] LLM DECISION - Chain-of-Thought Reasoning")
    print(f"{'-'*80}")
    
    print(f"\n[Prompt sent to LLM includes]:")
    print(f"   - Position analysis (material, safety, center)")
    print(f"   - Game context (opening, history, opponent style)")
    print(f"   - Top {len(top_candidates)} analyzed candidates with pros/cons")
    print(f"   - All {len(analysis.legal_moves)} legal moves for free choice")
    
    print(f"\n[LLM will perform Chain-of-Thought reasoning]:")
    print(f"   Step 1: Evaluate position (who's better?)")
    print(f"   Step 2: Identify critical factors")
    print(f"   Step 3: Consider candidate moves")
    print(f"   Step 4: Choose best move")
    print(f"   Step 5: Output with confidence")
    
    print(f"\n{'-'*80}")
    print("[Calling LLM API...]")
    print(f"{'-'*80}")


def play_detailed_game(max_moves=10):
    """Play a game with detailed module output"""
    
    import time as time_module
    
    print("\n" + "="*80)
    print("WHITE AGENT (Modular) vs LLM BASELINE (Direct)")
    print("="*80)
    print("\nThis demo compares:")
    print("  White: Modular approach (Perception + Memory + Reasoning + LLM)")
    print("  Black: Direct LLM baseline (FEN + simple prompt)")
    print("="*80)
    
    # Check API
    deepseek_key = get_api_key("deepseek")
    if not deepseek_key:
        print("\n[ERROR] No DeepSeek API key found!")
        print("   Add to src/api/api.txt: deepseek:your_key")
        return
    
    print("[OK] API key found\n")
    
    # Create White Agent
    print("Creating White Agent...")
    config = AgentConfig(
        api_provider="deepseek",
        model="deepseek-chat",
        use_chain_of_thought=True,
        max_candidates=10,
        temperature=0.3
    )
    
    white_agent = WhiteAgent(
        agent_id="white_detailed",
        agent_name="White Agent (Detailed)",
        config=config
    )
    print(f"[OK] {white_agent.agent_name} created")
    
    # Initialize memory for new game
    import time as time_mod
    game_id = f"detailed_demo_{int(time_mod.time())}"
    white_agent.memory.start_new_game(game_id=game_id, our_side="white")
    print(f"[OK] Memory initialized for game: {game_id}")
    
    # Create LLM opponent (direct LLM baseline for comparison)
    print("Creating opponent (LLM Baseline - DeepSeek)...")
    black_agent = DeepSeekAgent(
        agent_id="black_llm",
        agent_name="LLM Baseline (Direct DeepSeek)",
        model="deepseek-chat"
    )
    print(f"[OK] {black_agent.agent_name} created")
    print("   Note: This is direct LLM call WITHOUT modular processing")
    
    # Create game orchestrator
    print("\nInitializing game...")
    green_agent = ChessGreenAgent()
    
    # Initialize Stockfish evaluator
    print("Initializing Stockfish evaluator...")
    try:
        evaluator = StockfishEvaluator()
        print(f"[OK] Stockfish initialized: {evaluator.stockfish_path}")
        use_stockfish = True
    except Exception as e:
        print(f"[WARNING] Stockfish not available: {e}")
        print("   Continuing without evaluation...")
        use_stockfish = False
    
    # Manual game loop for detailed output - standard starting position
    board = chess.Board()  # This creates standard starting position
    print(f"\nStarting position FEN: {board.fen()}")
    print(f"Legal moves in starting position: {len(list(board.legal_moves))}")
    move_count = 0
    
    # Track evaluations and centipawn loss
    evaluations = []
    previous_eval = None  # Track previous position evaluation
    
    print(f"\n{'='*80}")
    print("GAME START")
    print(f"{'='*80}")
    
    while move_count < max_moves and not board.is_game_over():
        move_count += 1
        
        # Determine current player
        is_white = board.turn
        current_agent = white_agent if is_white else black_agent
        player_name = "WHITE" if is_white else "BLACK"
        
        # Prepare board state
        board_state = {
            "fen": board.fen(),
            "legal_moves": [m.uci() for m in board.legal_moves],
            "move_number": move_count,
            "time_remaining": 300.0
        }
        
        # Show detailed output for White Agent
        if is_white:
            print_module_outputs(white_agent, board_state, move_count)
        else:
            print(f"\n{'='*80}")
            print(f"BLACK (LLM Baseline) - Move {move_count}")
            print(f"{'='*80}")
            print(f"\nDirect LLM call - NO modular processing")
            print(f"FEN: {board_state['fen']}")
            print(f"Legal moves: {len(board_state['legal_moves'])}")
            print(f"\nLLM receives only: FEN + basic prompt")
            print(f"(No Perception, Memory, or Reasoning modules)")
        
        # Evaluate position BEFORE move
        eval_before = None
        if use_stockfish:
            try:
                eval_before = evaluator.evaluate_position(board)
            except:
                pass
        
        # Get move with retry logic for illegal moves
        import time
        import random
        
        max_retries = 3
        retry_count = 0
        move_uci = None
        confidence = 0.5
        reasoning = ""
        thinking_time = 0
        
        while retry_count <= max_retries:
            start_time = time.time()
            
            try:
                response = current_agent.get_move(board_state)
                thinking_time_attempt = time.time() - start_time
                thinking_time += thinking_time_attempt
                
                move_uci = response.move_uci
                confidence = response.confidence or 0.5
                reasoning = response.reasoning or ""
                
                if retry_count > 0:
                    print(f"\n   [Retry {retry_count}]: {move_uci} (thinking: {thinking_time_attempt:.2f}s)")
                else:
                    print(f"\n{'-'*80}")
                    print(f"[FINAL DECISION]")
                    print(f"{'-'*80}")
                    print(f"Move: {move_uci}")
                    print(f"Confidence: {confidence:.2f}")
                    print(f"Thinking time: {thinking_time_attempt:.2f}s")
                
                if reasoning and retry_count == 0:
                    print(f"\n[{'White Agent' if is_white else 'LLM Baseline'} Reasoning]:")
                    reasoning_preview = reasoning[:300] + "..." if len(reasoning) > 300 else reasoning
                    print(f"   {reasoning_preview}")
                
                # Check if move is legal
                move = chess.Move.from_uci(move_uci)
                if move in board.legal_moves:
                    break  # Legal move, exit retry loop
                else:
                    # Illegal move, retry
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"\n   [WARNING] Illegal move: {move_uci}")
                        print(f"   Asking agent to retry...")
                        # Add error feedback for retry
                        board_state["last_error"] = f"Move {move_uci} is not legal in this position"
                        board_state["illegal_move"] = move_uci
                    else:
                        # Max retries exceeded, use random legal move
                        legal_moves_list = list(board.legal_moves)
                        random_move = random.choice(legal_moves_list)
                        move_uci = random_move.uci()
                        print(f"\n   [ERROR] Max retries ({max_retries}) exceeded!")
                        print(f"   Using random legal move: {move_uci}")
                        confidence = 0.1
                        reasoning = f"Random fallback after {max_retries} illegal moves"
                        break
                        
            except Exception as e:
                print(f"\n   [ERROR] Agent error: {e}")
                retry_count += 1
                if retry_count > max_retries:
                    # Fallback to random move
                    legal_moves_list = list(board.legal_moves)
                    random_move = random.choice(legal_moves_list)
                    move_uci = random_move.uci()
                    confidence = 0.1
                    reasoning = f"Random fallback after error: {str(e)[:50]}"
                    print(f"   Using random legal move: {move_uci}")
                    break
        
        try:
            # Execute the validated move
            move = chess.Move.from_uci(move_uci)
            if move in board.legal_moves:
                # Check if capture or check
                was_capture = board.is_capture(move)
                board.push(move)
                was_check = board.is_check()
                
                print(f"\n[OK] Move executed successfully")
                
                # If black just moved, record to White Agent's memory as opponent move
                if not is_white:
                    white_agent.memory.record_move(
                        move_number=move_count,
                        side="black",
                        move_uci=move_uci,
                        reasoning=reasoning if reasoning else None,
                        was_capture=was_capture,
                        was_check=was_check
                    )
                    print(f"   -> Recorded opponent move to White Agent memory")
                
                # Evaluate position AFTER move and calculate centipawn loss
                if use_stockfish and eval_before is not None:
                    try:
                        eval_after_raw = evaluator.evaluate_position(board)
                        
                        if eval_after_raw is None:
                            print(f"\n[WARNING] Stockfish evaluation returned None")
                        else:
                            # IMPORTANT: Stockfish returns evaluation from CURRENT player's perspective
                            # After a move, the perspective changes!
                            # eval_before: from mover's perspective (positive = good for mover)
                            # eval_after: from opponent's perspective (positive = good for opponent)
                            #
                            # To calculate CP loss correctly:
                            # We need to compare from the same perspective (the mover's)
                            # Since eval_after is from opponent's view, negate it to get mover's view
                            #
                            # CP Loss = eval_before - (-eval_after) = eval_before + eval_after
                            # If the move was good: eval_after (opponent's view) is negative, so loss is 0 or negative
                            # If the move was bad: eval_after (opponent's view) is positive, so loss is positive
                            
                            # Calculate: how much did the position worsen from mover's perspective?
                            # Good move: eval_before + eval_after < 0 (opponent is unhappy)
                            # Bad move: eval_before + eval_after > 0 (opponent is happy)
                            cp_loss = max(0, eval_before + eval_after_raw)
                            
                            # Convert eval_after to white's perspective for display
                            if is_white:
                                eval_after = -eval_after_raw  # Negate since it's from black's view
                            else:
                                eval_after = eval_after_raw  # Already from white's view
                            
                            # Format score (from white's perspective)
                            if eval_after > 0:
                                score_str = f"+{eval_after/100:.2f}"
                            else:
                                score_str = f"{eval_after/100:.2f}"
                            
                            # Also show eval_before from white's perspective
                            if is_white:
                                eval_before_white = eval_before
                            else:
                                eval_before_white = -eval_before
                            
                            evaluations.append({
                                "move_number": move_count,
                                "side": player_name.lower(),
                                "move": move_uci,
                                "eval_before": eval_before_white,
                                "eval_after": eval_after,
                                "cp_loss": cp_loss,
                                "score_str": score_str
                            })
                            
                            print(f"\n[STOCKFISH EVALUATION]")
                            print(f"   Position before: {eval_before_white/100:+.2f} (white's view)")
                            print(f"   Position after: {score_str} (white's view)")
                            print(f"   Centipawn loss: {cp_loss} cp")
                            
                            # Classify move quality
                            if cp_loss == 0:
                                quality = "Best move"
                            elif cp_loss < 10:
                                quality = "Excellent"
                            elif cp_loss < 25:
                                quality = "Good"
                            elif cp_loss < 50:
                                quality = "Inaccuracy"
                            elif cp_loss < 100:
                                quality = "Mistake"
                            elif cp_loss < 300:
                                quality = "Blunder"
                            else:
                                quality = "Catastrophic blunder"
                            
                            print(f"   Move quality: {quality}")
                    except Exception as eval_error:
                        print(f"\n[WARNING] Evaluation failed: {eval_error}")
            else:
                # This shouldn't happen after retry logic, but just in case
                print(f"\n[CRITICAL ERROR] Move still illegal after retries: {move_uci}")
                # Use random move as last resort
                legal_moves_list = list(board.legal_moves)
                if legal_moves_list:
                    random_move = random.choice(legal_moves_list)
                    board.push(random_move)
                    print(f"   Used random move: {random_move.uci()}")
                else:
                    print(f"   No legal moves available - game should be over")
                    break
                
        except Exception as e:
            print(f"\n[ERROR]: {e}")
            import traceback
            traceback.print_exc()
            # Try to continue with random move
            try:
                legal_moves_list = list(board.legal_moves)
                if legal_moves_list:
                    random_move = random.choice(legal_moves_list)
                    board.push(random_move)
                    print(f"   Recovery: used random move {random_move.uci()}")
                else:
                    break
            except:
                break
        
        # Short summary
        print(f"\n{'-'*80}")
        print("Board after move:")
        print(board)
        print(f"{'-'*80}")
    
    # Game end
    print(f"\n{'='*80}")
    print("GAME ENDED")
    print(f"{'='*80}")
    print(f"Total moves: {move_count}")
    print(f"Result: {board.result()}")
    
    if board.is_checkmate():
        print("[GAME END] Checkmate!")
    elif board.is_stalemate():
        print("[GAME END] Stalemate!")
    elif move_count >= max_moves:
        print(f"[GAME END] Max moves ({max_moves}) reached")
    
    # Show evaluation summary with ACPL
    if use_stockfish and len(evaluations) > 0:
        print(f"\n{'='*80}")
        print("EVALUATION SUMMARY - Centipawn Loss Analysis")
        print(f"{'='*80}")
        print(f"\n{'Move':<6} {'Side':<10} {'Move':<10} {'CP Loss':<10} {'Quality':<20}")
        print("-" * 70)
        
        for ev in evaluations:
            cp_loss = ev['cp_loss']
            
            # Classify move quality
            if cp_loss == 0:
                quality = "Best"
            elif cp_loss < 10:
                quality = "Excellent"
            elif cp_loss < 25:
                quality = "Good"
            elif cp_loss < 50:
                quality = "Inaccuracy"
            elif cp_loss < 100:
                quality = "Mistake"
            elif cp_loss < 300:
                quality = "Blunder"
            else:
                quality = "Catastrophic"
            
            print(f"{ev['move_number']:<6} {ev['side']:<10} {ev['move']:<10} {cp_loss:<10} {quality:<20}")
        
        # Calculate ACPL (Average Centipawn Loss)
        white_losses = [e['cp_loss'] for e in evaluations if e['side'] == 'white']
        black_losses = [e['cp_loss'] for e in evaluations if e['side'] == 'black']
        
        print(f"\n{'='*70}")
        print("ACPL (Average Centipawn Loss)")
        print("-" * 70)
        
        if white_losses:
            acpl_white = sum(white_losses) / len(white_losses)
            print(f"White Agent (Modular):  {acpl_white:.1f} ACPL")
            
            # Estimate skill level
            if acpl_white < 10:
                skill = "Super Grandmaster (2700+)"
            elif acpl_white < 20:
                skill = "Grandmaster (2500-2700)"
            elif acpl_white < 30:
                skill = "International Master (2400-2500)"
            elif acpl_white < 50:
                skill = "FIDE Master (2300-2400)"
            elif acpl_white < 100:
                skill = "Expert (2000-2300)"
            elif acpl_white < 200:
                skill = "Intermediate (1500-2000)"
            else:
                skill = "Beginner (<1500)"
            print(f"   Estimated skill: {skill}")
        
        if black_losses:
            acpl_black = sum(black_losses) / len(black_losses)
            print(f"\nLLM Baseline (Direct):  {acpl_black:.1f} ACPL")
            
            # Estimate skill level
            if acpl_black < 10:
                skill = "Super Grandmaster (2700+)"
            elif acpl_black < 20:
                skill = "Grandmaster (2500-2700)"
            elif acpl_black < 30:
                skill = "International Master (2400-2500)"
            elif acpl_black < 50:
                skill = "FIDE Master (2300-2400)"
            elif acpl_black < 100:
                skill = "Expert (2000-2300)"
            elif acpl_black < 200:
                skill = "Intermediate (1500-2000)"
            else:
                skill = "Beginner (<1500)"
            print(f"   Estimated skill: {skill}")
        
        # Show winner
        if white_losses and black_losses:
            if acpl_white < acpl_black:
                diff = acpl_black - acpl_white
                print(f"\n*** White Agent played better by {diff:.1f} ACPL ***")
            elif acpl_black < acpl_white:
                diff = acpl_white - acpl_black
                print(f"\n*** LLM Baseline played better by {diff:.1f} ACPL ***")
            else:
                print(f"\n*** Both agents played equally well ***")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--moves", type=int, default=6, 
                       help="Number of moves to play (default: 6)")
    
    args = parser.parse_args()
    
    play_detailed_game(max_moves=args.moves)

