"""Test chess environment"""

import sys
sys.path.insert(0, 'src')

from environment.chess_environment import ChessEnvironment
from environment.models import MoveRequest, MoveFormat


def test_basic_game():
    """Test basic game flow"""
    print("=" * 60)
    print("Test Chess Environment")
    print("=" * 60)
    
    # Create environment
    env = ChessEnvironment(game_id="test_001")
    print("\n✅ Environment created successfully")
    
    # Test 1: Get initial board state
    print("\n[Test 1] Get board state")
    board_state = env.get_board_state(format_type="all")
    print(f"  - Game ID: {board_state.game_id}")
    print(f"  - Current player: {board_state.current_player}")
    print(f"  - FEN: {board_state.fen}")
    print(f"  - Legal moves count: {len(board_state.legal_moves)}")
    print(f"  - First 5 legal moves: {board_state.legal_moves[:5]}")
    print("\nBoard:")
    print(board_state.board_ascii)
    
    # Test 2: Execute move
    print("\n[Test 2] Execute move - e2e4")
    move_req = MoveRequest(move="e2e4", move_format=MoveFormat.UCI, thinking_time=2.5)
    response, feedback = env.make_move(move_req)
    print(f"  - Status: {response.status}")
    print(f"  - Move: {response.uci_notation} ({response.san_notation})")
    print(f"  - Thinking time: {response.time_used:.1f}s")
    print(f"  - White time remaining: {env.time_remaining['white']:.1f}s")
    print(f"  - New FEN: {response.new_fen}")
    print(f"  - Feedback: {feedback.message}")
    
    # Test 3: Get legal moves
    print("\n[Test 3] Get black's legal moves")
    legal_moves = env.get_legal_moves()
    print(f"  - Legal moves count: {legal_moves.count}")
    print(f"  - First 5:")
    for move in legal_moves.moves[:5]:
        print(f"    * {move.uci} ({move.san}) - {move.piece}")
    
    # Test 4: Move again
    print("\n[Test 4] Black moves - e7e5")
    move_req = MoveRequest(move="e7e5", move_format=MoveFormat.UCI, thinking_time=3.2)
    response, feedback = env.make_move(move_req)
    print(f"  - Status: {response.status}")
    print(f"  - Move: {response.san_notation}")
    print(f"  - Thinking time: {response.time_used:.1f}s")
    print(f"  - Black time remaining: {env.time_remaining['black']:.1f}s")
    
    # Test 5: View history
    print("\n[Test 5] View move history")
    history = env.get_move_history()
    print(f"  - Total moves: {history.total_moves}")
    print(f"  - PGN: {history.pgn}")
    
    # Test 6: Analyze position
    print("\n[Test 6] Analyze position")
    analysis = env.analyze_position(analysis_type="material")
    if analysis.material_balance:
        print(f"  - White: {analysis.material_balance.white}")
        print(f"  - Black: {analysis.material_balance.black}")
        print(f"  - Advantage: {analysis.material_balance.advantage}")
    
    # Test 7: Query rules
    print("\n[Test 7] Query castling rules")
    rule = env.check_rules("castling")
    print(f"  - Rule: {rule.rule}")
    print(f"  - Description: {rule.description}")
    print(f"  - Conditions:")
    for cond in rule.conditions:
        print(f"    * {cond}")
    
    # Test 8: Test illegal move
    print("\n[Test 8] Test illegal move - e2e5")
    move_req = MoveRequest(move="e2e5", move_format=MoveFormat.UCI, thinking_time=1.0)
    response, feedback = env.make_move(move_req)
    print(f"  - Status: {response.status}")
    print(f"  - Error type: {response.error_type}")
    print(f"  - Message: {response.message}")
    print(f"  - Suggestion: {response.suggestion}")
    print(f"  - Note: Illegal moves do not consume time")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


def test_complete_game():
    """Test complete game"""
    print("\n\n" + "=" * 60)
    print("Scholar's Mate Demo")
    print("=" * 60)
    
    env = ChessEnvironment(game_id="scholars_mate")
    
    # Scholar's Mate game (with simulated thinking time)
    moves = [
        ("e2e4", "e4", 1.5),
        ("e7e5", "e5", 2.3),
        ("f1c4", "Bc4", 3.0),
        ("b8c6", "Nc6", 2.8),
        ("d1h5", "Qh5", 4.2),
        ("g8f6", "Nf6", 5.1),
        ("h5f7", "Qxf7#", 2.0)  # Checkmate!
    ]
    
    for i, (uci, san, thinking_time) in enumerate(moves):
        print(f"\nMove {i+1}: {san} (thinking {thinking_time}s)")
        move_req = MoveRequest(move=uci, move_format=MoveFormat.UCI, thinking_time=thinking_time)
        response, feedback = env.make_move(move_req)
        
        print(f"  Status: {response.status}")
        if response.is_checkmate:
            print("  🎉 Checkmate! Game over!")
            break
        elif response.is_check:
            print("  ⚠️  Check!")
    
    # Display final board
    final_state = env.get_board_state(format_type="ascii")
    print("\nFinal board:")
    print(final_state.board_ascii)
    
    # Display complete game notation
    history = env.get_move_history()
    print(f"\nComplete game notation: {history.pgn}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_basic_game()
    test_complete_game()
