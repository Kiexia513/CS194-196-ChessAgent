"""Complete game test - Over 15 moves with detailed logging"""

import sys
import json
from datetime import datetime
sys.path.insert(0, 'src')

from environment.chess_environment import ChessEnvironment
from environment.models import MoveRequest, MoveFormat, Player


def log_separator(title=""):
    """Print separator line"""
    if title:
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    else:
        print("-" * 80)


def log_board_state(env, move_number):
    """Log board state in detail"""
    log_separator(f"Board State After Move {move_number}")
    
    state = env.get_board_state(format_type="all")
    
    print(f"\n[Basic Information]")
    print(f"  Game ID: {state.game_id}")
    print(f"  Move Number: {state.move_number}")
    print(f"  Current Player: {state.current_player}")
    print(f"  FEN: {state.fen}")
    
    print(f"\n[Board]")
    print(state.board_ascii)
    
    print(f"\n[Game Status]")
    print(f"  In Check: {'Yes' if state.is_check else 'No'}")
    print(f"  Checkmate: {'Yes' if state.is_checkmate else 'No'}")
    print(f"  Stalemate: {'Yes' if state.is_stalemate else 'No'}")
    
    print(f"\n[Time Information]")
    print(f"  White Time Remaining: {state.time_remaining['white']:.2f} seconds")
    print(f"  Black Time Remaining: {state.time_remaining['black']:.2f} seconds")
    
    print(f"\n[Legal Moves]")
    print(f"  Legal Moves Count: {len(state.legal_moves)}")
    print(f"  First 10 Legal Moves: {state.legal_moves[:10]}")
    
    print(f"\n[Captured Pieces]")
    print(f"  Captured by White: {state.captured_pieces['by_white']}")
    print(f"  Captured by Black: {state.captured_pieces['by_black']}")


def log_move_details(move_number, move_uci, thinking_time, response, feedback):
    """Log move details"""
    log_separator(f"Move {move_number} Details")
    
    print(f"\n[Move Request]")
    print(f"  UCI: {move_uci}")
    print(f"  Thinking Time: {thinking_time:.2f} seconds")
    
    print(f"\n[Move Response]")
    print(f"  Status: {response.status}")
    
    if response.status == "success":
        print(f"  Executed Move: {response.move_executed}")
        print(f"  SAN Notation: {response.san_notation}")
        print(f"  UCI Notation: {response.uci_notation}")
        print(f"  Time Used: {response.time_used:.2f} seconds")
        print(f"  Piece Moved: {response.piece_moved}")
        print(f"  Captured: {response.captured if response.captured else 'None'}")
        print(f"  In Check: {'Yes' if response.is_check else 'No'}")
        print(f"  Checkmate: {'Yes' if response.is_checkmate else 'No'}")
        print(f"  New FEN: {response.new_fen}")
    else:
        print(f"  Error Type: {response.error_type}")
        print(f"  Error Message: {response.message}")
        print(f"  Error Reason: {response.reason}")
    
    print(f"\n[Environment Feedback]")
    print(f"  Feedback Type: {feedback.feedback_type}")
    print(f"  Feedback Message: {feedback.message}")
    print(f"  Next Action: {feedback.next_action}")


def log_statistics(env):
    """Log statistics"""
    log_separator("Statistics")
    
    print(f"\n[White Statistics]")
    for key, value in env.statistics[Player.WHITE].items():
        print(f"  {key}: {value}")
    
    print(f"\n[Black Statistics]")
    for key, value in env.statistics[Player.BLACK].items():
        print(f"  {key}: {value}")


def log_move_history(env):
    """Log move history"""
    log_separator("Move History")
    
    history = env.get_move_history()
    
    print(f"\n[History Summary]")
    print(f"  Total Moves: {history.total_moves}")
    print(f"  Rounds: {len(history.moves)}")
    print(f"  Opening Name: {history.opening_name if history.opening_name else 'Not Identified'}")
    
    print(f"\n[PGN Notation]")
    print(f"  {history.pgn}")
    
    print(f"\n[Detailed History]")
    for move in history.moves:
        white_info = ""
        black_info = ""
        
        if move.white:
            white_info = f"{move.white.san} ({move.white.time_used:.2f}s)"
        if move.black:
            black_info = f"{move.black.san} ({move.black.time_used:.2f}s)"
        
        print(f"  {move.move_number}. {white_info:20} {black_info}")


def log_position_analysis(env):
    """Log position analysis"""
    log_separator("Position Analysis")
    
    analysis = env.analyze_position(analysis_type="all")
    
    if analysis.material_balance:
        print(f"\n[Material Balance]")
        print(f"  White:")
        for piece, count in analysis.material_balance.white.items():
            print(f"    {piece}: {count}")
        print(f"  Black:")
        for piece, count in analysis.material_balance.black.items():
            print(f"    {piece}: {count}")
        print(f"  Advantage: {analysis.material_balance.advantage}")
    
    if analysis.threats:
        print(f"\n[Threats]")
        for threat in analysis.threats:
            print(f"  - {threat}")
    
    if analysis.opportunities:
        print(f"\n[Opportunities]")
        for opp in analysis.opportunities:
            print(f"  - {opp}")


def test_italian_game():
    """Test Italian Game - Over 15 moves"""
    
    log_separator("Italian Game Complete Game Test")
    print(f"\nTest Start Time: {datetime.now()}")
    print(f"Game Type: Italian Game (Giuoco Piano)")
    print(f"Expected Moves: 20 moves")
    
    # Create environment
    env = ChessEnvironment(
        game_id="italian_game_001",
        time_per_side=600.0,  # 10 minutes per side
        time_per_move=60.0     # Maximum 1 minute per move
    )
    
    print(f"\nEnvironment Configuration:")
    print(f"  Game ID: {env.game_id}")
    print(f"  Time Per Side: {env.time_per_side} seconds")
    print(f"  Time Per Move: {env.time_per_move} seconds")
    
    # Italian Game opening sequence (20 moves, entering middlegame)
    # This is a classic Italian Game variation
    moves = [
        # Opening phase (moves 1-5)
        ("e2e4", "White opens - King's pawn two squares", 3.5),
        ("e7e5", "Black responds - King's pawn two squares", 2.8),
        ("g1f3", "White - Knight attacks e5", 4.2),
        ("b8c6", "Black - Queen's knight defends e5", 3.1),
        ("f1c4", "White - Italian Game! Bishop targets f7 weakness", 5.0),
        
        # Continued development (moves 6-10)
        ("f8c5", "Black - Symmetrical response", 4.5),
        ("c2c3", "White - Prepares d4 breakthrough", 6.3),
        ("g8f6", "Black - Knight attacks e4", 3.8),
        ("d2d3", "White - Solidifies center", 5.1),
        ("d7d6", "Black - Consolidates e5", 4.0),
        
        # Castling and middlegame preparation (moves 11-15)
        ("e1g1", "White - Kingside castling (O-O)", 2.5),
        ("e8g8", "Black - Kingside castling (O-O)", 2.3),
        ("b1d2", "White - Queen's knight development", 5.5),
        ("a7a6", "Black - Prevents Nb5", 3.9),
        ("h2h3", "White - Prevents Ng4", 4.2),
        
        # Middlegame battle begins (moves 16-20)
        ("h7h6", "Black - Creates escape square for king", 4.7),
        ("f1e1", "White - Rook controls e-file", 6.1),
        ("c6e7", "Black - Knight repositioning, preparing ...Ng6", 5.3),
        ("d3d4", "White - Center breakthrough!", 7.2),
        ("e5d4", "Black - Captures pawn", 4.8),
    ]
    
    print(f"\nPreparing to execute {len(moves)} moves...")
    log_separator()
    
    # Log initial state
    log_board_state(env, 0)
    
    # Execute each move
    for i, (move_uci, comment, thinking_time) in enumerate(moves, 1):
        print(f"\n\n")
        log_separator(f">>> Move {i}: {comment} <<<")
        
        # Execute move
        move_req = MoveRequest(
            move=move_uci, 
            move_format=MoveFormat.UCI,
            thinking_time=thinking_time
        )
        response, feedback = env.make_move(move_req)
        
        # Log move details
        log_move_details(i, move_uci, thinking_time, response, feedback)
        
        # Log board state every 5 moves
        if i % 5 == 0 or i == len(moves):
            log_board_state(env, i)
        
        # Check if game ended
        if response.status == "success" and response.is_checkmate:
            print(f"\n🎉 Game ended at move {i}! Checkmate!")
            break
    
    # Final statistics
    print(f"\n\n")
    log_statistics(env)
    log_move_history(env)
    log_position_analysis(env)
    
    # Final board state
    log_board_state(env, len(moves))
    
    # Game summary
    log_separator("Game Summary")
    print(f"\nTest End Time: {datetime.now()}")
    print(f"Total Moves: {len(env.move_history)}")
    print(f"Game Status: {env.game_status}")
    print(f"\nWhite Total Time: {env.statistics[Player.WHITE]['time_used']:.2f} seconds")
    print(f"Black Total Time: {env.statistics[Player.BLACK]['time_used']:.2f} seconds")
    print(f"\nWhite Time Remaining: {env.time_remaining[Player.WHITE]:.2f} seconds")
    print(f"Black Time Remaining: {env.time_remaining[Player.BLACK]:.2f} seconds")
    
    print(f"\n✅ Test completed! Executed {len(env.move_history)} moves")
    log_separator()


def export_game_log(env, filename="game_log.json"):
    """Export game log as JSON"""
    log_separator(f"Exporting game log to {filename}")
    
    game_data = {
        "game_id": env.game_id,
        "game_status": env.game_status.value,
        "total_moves": len(env.move_history),
        "start_time": env.start_time,
        "statistics": {
            "white": env.statistics[Player.WHITE],
            "black": env.statistics[Player.BLACK]
        },
        "time_remaining": {
            "white": env.time_remaining[Player.WHITE],
            "black": env.time_remaining[Player.BLACK]
        },
        "move_history": env.move_history,
        "final_fen": env.board.fen(),
        "pgn": env.get_move_history().pgn
    }
    
    # Convert datetime to string
    for move in game_data["move_history"]:
        if "timestamp" in move:
            move["timestamp"] = move["timestamp"].isoformat()
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(game_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Game log exported to: {filename}")
    print(f"File size: {len(json.dumps(game_data))} bytes")


if __name__ == "__main__":
    print("=" * 80)
    print("  Complete Chess Game Test - Detailed Logging Version")
    print("=" * 80)
    
    # Run test
    test_italian_game()
    
    print("\n" + "=" * 80)
    print("  All tests completed")
    print("=" * 80)
