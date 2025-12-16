"""Test LLM Agents - DeepSeek and ChatGPT"""

import sys
sys.path.insert(0, 'src')

from green_agent import ChessGreenAgent, DeepSeekAgent, ChatGPTAgent, GoogleAIAgent, RandomAgent


def test_chatgpt_vs_google():
    """Test DeepSeek vs ChatGPT"""
    print("\n" + "="*80)
    print("🤖 LLM Chess Match: DeepSeek vs ChatGPT")
    print("="*80)
    
    # Create Green Agent
    green_agent = ChessGreenAgent(
        agent_id="llm_evaluator",
        use_stockfish=True,
        log_dir="logs/llm_games"
    )
    
    # Create LLM agents - using deepseek-reasoner for deep reasoning
    deepseek_agent = DeepSeekAgent(
        agent_id="deepseek_1",
        agent_name="DeepSeek Reasoner",
        model="deepseek-reasoner",  # Use reasoning model
        temperature=0.3
    )
    
    chatgpt_agent = ChatGPTAgent(
        agent_id="chatgpt_1",
        agent_name="ChatGPT",
        model="gpt-4o-mini",
        temperature=0.3
    )
    
    # Run game
    print("\n🎮 Starting LLM vs LLM game...")
    print(f"⚪ White: {deepseek_agent.agent_name} (deepseek-reasoner)")
    print(f"⚫ Black: {chatgpt_agent.agent_name}")

    try:
        results = green_agent.run_game(
            white_agent=deepseek_agent,
            black_agent=chatgpt_agent,
            game_id="deepseek_vs_chatgpt_001",
            max_moves=50  # Limit to 50 moves to control cost
        )
        
        # Display results
        print("\n" + "="*80)
        print("📊 MATCH RESULTS")
        print("="*80)
        print(f"Result: {results['result']}")
        print(f"Total Moves: {results['total_moves']}")
        print(f"\n⚪ Google Gemini:")
        print(f"   ACPL: {results['metrics']['metrics']['white']['acpl']:.2f}")
        print(f"   ELO: {results['metrics']['metrics']['white']['estimated_elo']}")
        print(f"   Level: {results['metrics']['metrics']['white']['skill_level']}")
        print(f"   Blunders: {results['metrics']['metrics']['white']['blunders']}")
        print(f"   Mistakes: {results['metrics']['metrics']['white']['mistakes']}")
        
        print(f"\n⚫ ChatGPT:")
        print(f"   ACPL: {results['metrics']['metrics']['black']['acpl']:.2f}")
        print(f"   ELO: {results['metrics']['metrics']['black']['estimated_elo']}")
        print(f"   Level: {results['metrics']['metrics']['black']['skill_level']}")
        print(f"   Blunders: {results['metrics']['metrics']['black']['blunders']}")
        print(f"   Mistakes: {results['metrics']['metrics']['black']['mistakes']}")
        
        print("\n✅ LLM game completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Game interrupted by user")
    except Exception as e:
        print(f"\n❌ Game failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        green_agent.close()


def test_deepseek_vs_chatgpt():
    """Test DeepSeek vs ChatGPT"""
    print("\n" + "="*80)
    print("🤖 LLM Chess Match: DeepSeek Reasoner vs ChatGPT")
    print("="*80)
    
    # Create Green Agent
    green_agent = ChessGreenAgent(
        agent_id="llm_evaluator",
        use_stockfish=True,
        log_dir="logs/llm_games"
    )
    
    # Create LLM agents - using deepseek-reasoner
    deepseek_agent = DeepSeekAgent(
        agent_id="deepseek_1",
        agent_name="DeepSeek Reasoner",
        model="deepseek-reasoner",  # Use reasoning model
        temperature=0.3
    )
    
    chatgpt_agent = ChatGPTAgent(
        agent_id="chatgpt_1",
        agent_name="ChatGPT",
        model="gpt-4o-mini",
        temperature=0.3
    )
    
    # Run game
    print("\n🎮 Starting LLM vs LLM game...")
    print(f"⚪ White: {deepseek_agent.agent_name} (deepseek-reasoner)")
    print(f"⚫ Black: {chatgpt_agent.agent_name}")
    
    try:
        results = green_agent.run_game(
            white_agent=deepseek_agent,
            black_agent=chatgpt_agent,
            game_id="deepseek_vs_chatgpt_001",
            max_moves=50  # Limit to 50 moves to control cost
        )
        
        # Display results
        print("\n" + "="*80)
        print("📊 MATCH RESULTS")
        print("="*80)
        print(f"Result: {results['result']}")
        print(f"Total Moves: {results['total_moves']}")
        print(f"\n⚪ Google Gemini:")
        print(f"   ACPL: {results['metrics']['metrics']['white']['acpl']:.2f}")
        print(f"   ELO: {results['metrics']['metrics']['white']['estimated_elo']}")
        print(f"   Level: {results['metrics']['metrics']['white']['skill_level']}")
        print(f"   Blunders: {results['metrics']['metrics']['white']['blunders']}")
        print(f"   Mistakes: {results['metrics']['metrics']['white']['mistakes']}")
        
        print(f"\n⚫ ChatGPT:")
        print(f"   ACPL: {results['metrics']['metrics']['black']['acpl']:.2f}")
        print(f"   ELO: {results['metrics']['metrics']['black']['estimated_elo']}")
        print(f"   Level: {results['metrics']['metrics']['black']['skill_level']}")
        print(f"   Blunders: {results['metrics']['metrics']['black']['blunders']}")
        print(f"   Mistakes: {results['metrics']['metrics']['black']['mistakes']}")
        
        print("\n✅ LLM game completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Game interrupted by user")
    except Exception as e:
        print(f"\n❌ Game failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        green_agent.close()


def test_llm_vs_random():
    """Test LLM vs Random Agent (faster and cheaper)"""
    print("\n" + "="*80)
    print("🤖 Quick Test: DeepSeek vs Random Agent")
    print("="*80)
    
    # Create Green Agent
    green_agent = ChessGreenAgent(
        agent_id="quick_test",
        use_stockfish=True,
        log_dir="logs/quick_test"
    )
    
    # Create agents - using deepseek-reasoner model
    llm_agent = DeepSeekAgent(
        agent_id="deepseek_test",
        agent_name="DeepSeek Reasoner Test",
        model="deepseek-reasoner",
        temperature=0.7
    )
    
    random_agent = RandomAgent(
        agent_id="random_test",
        agent_name="Random Test"
    )
    
    print(f"\n⚪ White: {llm_agent.agent_name}")
    print(f"⚫ Black: {random_agent.agent_name}")
    
    try:
        results = green_agent.run_game(
            white_agent=llm_agent,
            black_agent=random_agent,
            game_id="llm_vs_random_001",
            max_moves=30  # Quick test with 30 moves
        )
        
        print(f"\n✅ Test completed!")
        print(f"Result: {results['result']}")
        print(f"DeepSeek Reasoner ACPL: {results['metrics']['metrics']['white']['acpl']:.2f}")
        print(f"DeepSeek Reasoner ELO: {results['metrics']['metrics']['white']['estimated_elo']}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        green_agent.close()


def test_llm_single_move():
    """Test LLM agent single move"""
    print("\n" + "="*80)
    print("🧪 Testing LLM Agent Single Move")
    print("="*80)
    
    # Create DeepSeek agent - using deepseek-reasoner for deep thinking
    agent = DeepSeekAgent(
        agent_id="test_agent",
        agent_name="Test DeepSeek",
        model="deepseek-reasoner"  # Use reasoning model for deeper thinking
    )
    
    # Test initial position
    board_state = {
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "legal_moves": ["e2e4", "e2e3", "d2d4", "d2d3", "g1f3", "b1c3"],
        "move_history": [],
        "time_remaining": 600.0,
        "move_number": 1
    }
    
    print("\nRequesting move from DeepSeek (deepseek-reasoner model)...")
    print("⏳ Note: Reasoning model may take 1-3 minutes to think deeply...")
    try:
        import time
        start_time = time.time()
        response = agent.get_move(board_state)
        thinking_time = time.time() - start_time
        
        print(f"\n✅ Move received:")
        print(f"   Move: {response.move_uci}")
        print(f"   Thinking Time: {thinking_time:.2f}s")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Reasoning: {response.reasoning[:200]}...")  # Show first 200 characters
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║          LLM Chess Agents Test Suite                              ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    import sys
    
    if len(sys.argv) > 1:
        test_mode = sys.argv[1]
    else:
        print("\nAvailable tests:")
        print("  1. single      - Test single move (fastest)")
        print("  2. quick       - DeepSeek vs Random (30 moves)")
        print("  3. full        - DeepSeek vs ChatGPT (50 moves)")
        print("\nUsage: python test_llm_agents.py [single|quick|full]")
        test_mode = input("\nSelect test (or press Enter for 'single'): ").strip() or "single"
    
    print(f"\n🚀 Running test mode: {test_mode}")
    
    if test_mode == "single":
        test_llm_single_move()
    elif test_mode == "quick":
        test_llm_vs_random()
    elif test_mode == "full" or test_mode == "gpt_google":
        # gpt_google also points to DeepSeek vs ChatGPT test
        test_chatgpt_vs_google()
    else:
        print(f"❌ Unknown test mode: {test_mode}")
        print("Available modes: single, quick, full")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("✅ Test completed!")
    print("="*80)

