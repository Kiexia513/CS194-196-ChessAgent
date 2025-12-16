"""Test Green Agent - Game orchestration and evaluation"""

import sys
sys.path.insert(0, 'src')

from green_agent import ChessGreenAgent, RandomAgent, SimpleGreedyAgent


def test_green_agent_basic():
    """Test Green Agent basic functionality"""
    print("\n" + "="*80)
    print("Test Green Agent - Basic Functionality")
    print("="*80)
    
    # Create Green Agent
    green_agent = ChessGreenAgent(
        agent_id="test_green_agent",
        use_stockfish=True,
        log_dir="logs/test_games"
    )
    
    # Create test agents
    white_agent = SimpleGreedyAgent(
        agent_id="greedy_1",
        agent_name="Greedy Player"
    )
    
    black_agent = RandomAgent(
        agent_id="random_1",
        agent_name="Random Player"
    )
    
    # Run a game
    print("\n🎮 Running a test game...")
    results = green_agent.run_game(
        white_agent=white_agent,
        black_agent=black_agent,
        game_id="test_game_001",
        max_moves=40  # Limit to 40 moves to speed up testing
    )
    
    # Display result summary
    print("\n📊 GAME RESULTS SUMMARY:")
    print(f"   Game ID: {results['game_id']}")
    print(f"   Result: {results['result']}")
    print(f"   Total Moves: {results['total_moves']}")
    print(f"   White ACPL: {results['metrics']['metrics']['white']['acpl']}")
    print(f"   Black ACPL: {results['metrics']['metrics']['black']['acpl']}")
    print(f"   White ELO: {results['metrics']['metrics']['white']['estimated_elo']}")
    print(f"   Black ELO: {results['metrics']['metrics']['black']['estimated_elo']}")
    
    # Cleanup
    green_agent.close()
    
    print("\n✅ Basic Green Agent test completed!")


def test_green_agent_multiple_games():
    """Test Green Agent - Multiple games"""
    print("\n" + "="*80)
    print("Test Green Agent - Multiple Games Statistics")
    print("="*80)
    
    # Create Green Agent
    green_agent = ChessGreenAgent(
        agent_id="multi_game_agent",
        use_stockfish=False,  # Disable Stockfish to speed up testing
        log_dir="logs/multi_games"
    )
    
    # Create test agents
    agent_a = RandomAgent(agent_id="agent_a", agent_name="Agent A")
    agent_b = RandomAgent(agent_id="agent_b", agent_name="Agent B")
    
    # Run multiple games
    num_games = 3
    print(f"\n🎮 Running {num_games} test games...")
    
    for i in range(num_games):
        print(f"\n{'─'*80}")
        print(f"Game {i+1}/{num_games}")
        print(f"{'─'*80}")
        
        # Alternate white/black sides
        if i % 2 == 0:
            white, black = agent_a, agent_b
        else:
            white, black = agent_b, agent_a
        
        results = green_agent.run_game(
            white_agent=white,
            black_agent=black,
            game_id=f"multi_game_{i+1:03d}",
            max_moves=30
        )
        
        print(f"   Result: {results['result']} ({results['total_moves']} moves)")
    
    # Get agent statistics
    print("\n" + "="*80)
    print("📊 AGENT STATISTICS")
    print("="*80)
    
    for agent_name in ["Agent A", "Agent B"]:
        summary = green_agent.get_agent_summary(agent_name)
        if "error" not in summary:
            print(f"\n{agent_name}:")
            print(f"   Total Games: {summary['total_games']}")
            print(f"   Wins: {summary['wins']}")
            print(f"   Draws: {summary['draws']}")
            print(f"   Losses: {summary['losses']}")
            print(f"   Win Rate: {summary['win_rate']:.1%}")
    
    # Cleanup
    green_agent.close()
    
    print("\n✅ Multiple games test completed!")


def test_green_agent_short_game():
    """Test Green Agent - Quick game (no Stockfish)"""
    print("\n" + "="*80)
    print("Test Green Agent - Quick Game")
    print("="*80)
    
    # Create Green Agent (without Stockfish for speed)
    green_agent = ChessGreenAgent(
        agent_id="fast_green_agent",
        use_stockfish=False,
        log_dir="logs/fast_games"
    )
    
    # Create test agents
    white_agent = RandomAgent(agent_id="fast_white", agent_name="Fast White")
    black_agent = RandomAgent(agent_id="fast_black", agent_name="Fast Black")
    
    # Run quick game
    print("\n🎮 Running a fast game (no Stockfish evaluation)...")
    results = green_agent.run_game(
        white_agent=white_agent,
        black_agent=black_agent,
        game_id="fast_game_001",
        max_moves=20
    )
    
    print(f"\n✅ Fast game completed in {results['total_moves']} moves")
    print(f"   Result: {results['result']}")
    
    # Cleanup
    green_agent.close()


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║          Chess Green Agent Test Suite                             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Run tests
    try:
        # Test 1: Quick game (no Stockfish)
        test_green_agent_short_game()
        
        # Test 2: Basic functionality (with Stockfish)
        # test_green_agent_basic()
        
        # Test 3: Multiple games
        # test_green_agent_multiple_games()
        
        print("\n" + "="*80)
        print("✅ All tests completed successfully!")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
