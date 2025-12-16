"""
Complete System Test Suite
==========================

This test suite provides comprehensive end-to-end testing of the Chess Green Agent
evaluation system. It works with or without Stockfish installed.

Test Coverage:
- Environment initialization and basic operations
- Agent creation and move generation
- Green Agent game orchestration
- Evaluation metrics (if Stockfish available)
- Visualization system
- Logging and reporting

Usage:
    python tests/test_complete_system.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from environment import ChessEnvironment
from environment.models import MoveRequest, MoveFormat
from green_agent import (
    ChessGreenAgent, 
    RandomAgent, 
    SimpleGreedyAgent,
    DeepSeekAgent,
    ChatGPTAgent,
    GoogleAIAgent
)
from evaluation import StockfishEvaluator
from visualization import HTMLReporter, ChartGenerator, GameReplay
from config.api_config import get_api_key, print_api_status


class TestRunner:
    """Complete system test runner"""
    
    def __init__(self):
        self.stockfish_available = False
        self.llm_available = False
        self.available_llm_agents = []
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def check_stockfish(self):
        """Check if Stockfish is available"""
        print("\n" + "="*80)
        print("CHECKING STOCKFISH AVAILABILITY")
        print("="*80)
        
        try:
            evaluator = StockfishEvaluator()
            self.stockfish_available = evaluator.is_available()
            
            if self.stockfish_available:
                print("✓ Stockfish engine is available")
                print("  Move quality evaluation will be performed")
                evaluator.close()
            else:
                print("⚠ Stockfish engine is not available")
                print("  Tests will run without move quality evaluation")
                print("  To install Stockfish, visit: https://stockfishchess.org/download/")
            
            return self.stockfish_available
        except Exception as e:
            print(f"⚠ Error checking Stockfish: {e}")
            print("  Tests will continue without Stockfish")
            return False
    
    def check_llm_apis(self):
        """Check which LLM APIs are available"""
        print("\n" + "="*80)
        print("CHECKING LLM API AVAILABILITY")
        print("="*80)
        
        print_api_status()
        
        # Check each LLM service
        available_services = []
        
        # Check DeepSeek
        deepseek_key = get_api_key("deepseek")
        if deepseek_key:
            available_services.append("DeepSeek")
            try:
                # Use deepseek-chat for faster responses
                agent = DeepSeekAgent(
                    agent_id="test_deepseek",
                    agent_name="Test DeepSeek",
                    model="deepseek-chat"  # Use chat model for faster responses
                )
                self.available_llm_agents.append(("DeepSeek", agent))
                print("✓ DeepSeek API key found and agent created (using deepseek-chat)")
            except Exception as e:
                print(f"⚠ DeepSeek agent creation failed: {e}")
        
        # Check ChatGPT
        openai_key = get_api_key("openai")
        if openai_key:
            available_services.append("ChatGPT")
            try:
                agent = ChatGPTAgent(
                    agent_id="test_chatgpt",
                    agent_name="Test ChatGPT",
                    model="gpt-4o-mini"  # Fast and affordable model
                )
                self.available_llm_agents.append(("ChatGPT", agent))
                print("✓ ChatGPT API key found and agent created (using gpt-4o-mini)")
            except Exception as e:
                print(f"⚠ ChatGPT agent creation failed: {e}")
                print("  Note: Ensure your API key is valid and has model access")
        
        # Check Google AI
        google_key = get_api_key("google")
        if google_key:
            available_services.append("Google AI")
            try:
                agent = GoogleAIAgent(
                    agent_id="test_google",
                    agent_name="Test Google Gemini",
                    model="gemini-pro"
                )
                self.available_llm_agents.append(("Google AI", agent))
                print("✓ Google AI API key found and agent created (using gemini-pro)")
            except Exception as e:
                print(f"⚠ Google AI agent creation failed: {e}")
        
        if available_services:
            self.llm_available = True
            print(f"\n✓ LLM APIs available: {', '.join(available_services)}")
            print(f"  Found {len(self.available_llm_agents)} LLM agent(s) ready to use")
        else:
            print("\n⚠ No LLM API keys found")
            print("  To use LLM agents, set API keys in src/api/api.txt or environment variables")
            print("  Format: deepseek:YOUR_KEY, openai:YOUR_KEY, google:YOUR_KEY")
        
        return self.llm_available
    
    def test_environment(self):
        """Test 1: Chess Environment"""
        print("\n" + "="*80)
        print("TEST 1: CHESS ENVIRONMENT")
        print("="*80)
        
        try:
            # Create environment
            env = ChessEnvironment(game_id="test_env_001")
            print("✓ Environment created successfully")
            
            # Get initial board state
            board_state = env.get_board_state()
            print(f"✓ Initial board state retrieved")
            print(f"  - FEN: {board_state.fen[:50]}...")
            print(f"  - Legal moves: {len(board_state.legal_moves)} available")
            
            # Make a move
            move_req = MoveRequest(move="e2e4", move_format=MoveFormat.UCI, thinking_time=1.5)
            response, feedback = env.make_move(move_req)
            
            if response.status == "success":
                print(f"✓ Move executed successfully: {response.san_notation}")
            else:
                raise Exception(f"Move failed: {response.message}")
            
            # Get legal moves
            legal_moves = env.get_legal_moves()
            print(f"✓ Legal moves retrieved: {legal_moves.count} moves available")
            
            # Get move history
            history = env.get_move_history()
            print(f"✓ Move history retrieved: {history.total_moves} moves recorded")
            
            self.test_results['passed'] += 1
            print("\n✓ TEST 1 PASSED")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Test 1 (Environment): {str(e)}")
            print(f"\n✗ TEST 1 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_agents(self):
        """Test 2: Agent Creation and Move Generation"""
        print("\n" + "="*80)
        print("TEST 2: AGENT CREATION AND MOVE GENERATION")
        print("="*80)
        
        try:
            # Test Random Agent
            random_agent = RandomAgent(
                agent_id="test_random",
                agent_name="Test Random"
            )
            print("✓ RandomAgent created")
            
            # Test SimpleGreedy Agent
            greedy_agent = SimpleGreedyAgent(
                agent_id="test_greedy",
                agent_name="Test Greedy"
            )
            print("✓ SimpleGreedyAgent created")
            
            # Test move generation
            board_state = {
                "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "time_remaining": 600.0,
                "move_number": 1
            }
            
            # Random agent move
            random_response = random_agent.get_move(board_state)
            print(f"✓ RandomAgent generated move: {random_response.move_uci}")
            
            # Greedy agent move
            greedy_response = greedy_agent.get_move(board_state)
            print(f"✓ SimpleGreedyAgent generated move: {greedy_response.move_uci}")
            
            # Test LLM agents if available
            if self.llm_available and len(self.available_llm_agents) > 0:
                print("\n🧪 Testing LLM Agent Single Move Generation...")
                llm_name, llm_agent = self.available_llm_agents[0]
                print(f"  Using: {llm_name}")
                
                try:
                    import time
                    start_time = time.time()
                    llm_response = llm_agent.get_move(board_state)
                    elapsed = time.time() - start_time
                    
                    print(f"✓ {llm_name} generated move: {llm_response.move_uci}")
                    print(f"  Confidence: {llm_response.confidence:.2f}")
                    print(f"  Response time: {elapsed:.2f}s")
                    print(f"  Reasoning: {llm_response.reasoning[:100]}...")
                except Exception as e:
                    print(f"⚠️  {llm_name} move generation failed: {e}")
                    print("  This is OK - continuing with other tests")
            
            self.test_results['passed'] += 1
            print("\n✓ TEST 2 PASSED")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Test 2 (Agents): {str(e)}")
            print(f"\n✗ TEST 2 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_green_agent_llm_flow(self):
        """Test 3: Green Agent with Full LLM Game Flow"""
        print("\n" + "="*80)
        print("TEST 3: GREEN AGENT WITH LLM GAME FLOW")
        print("="*80)
        
        try:
            # Create Green Agent (with or without Stockfish)
            green_agent = ChessGreenAgent(
                agent_id="test_green_agent",
                use_stockfish=self.stockfish_available,
                log_dir="logs/test_complete_system"
            )
            print("✓ GreenAgent created")
            
            # Choose agents based on availability (prioritize LLM vs LLM)
            if self.llm_available and len(self.available_llm_agents) >= 2:
                # Best case: LLM vs LLM
                print("\n🎮 Test Mode: LLM vs LLM (Full realistic game)")
                white_name, white_agent = self.available_llm_agents[0]
                black_name, black_agent = self.available_llm_agents[1]
                
                print(f"  ⚪ White: {white_name}")
                print(f"  ⚫ Black: {black_name}")
                
                # Reset agents for new game
                white_agent.reset()
                black_agent.reset()
                
                max_moves = 20  # Reduced for faster testing with LLMs
                game_id = f"test_llm_{white_name.lower().replace(' ', '_')}_vs_{black_name.lower().replace(' ', '_')}"
                
            elif self.llm_available and len(self.available_llm_agents) >= 1:
                # Good case: LLM vs Simple
                print("\n🎮 Test Mode: LLM vs Simple Agent")
                llm_name, llm_agent = self.available_llm_agents[0]
                llm_agent.reset()
                
                white_agent = llm_agent
                black_agent = SimpleGreedyAgent(
                    agent_id="test_simple",
                    agent_name="Simple Greedy"
                )
                white_name = llm_name
                black_name = "Simple Greedy"
                
                print(f"  ⚪ White: {white_name}")
                print(f"  ⚫ Black: {black_name}")
                
                max_moves = 15  # Reduced for faster testing
                game_id = f"test_llm_vs_simple_{llm_name.lower().replace(' ', '_')}"
                
            else:
                # Fallback: Simple vs Simple (no LLMs available)
                print("\n🎮 Test Mode: Simple vs Simple (No LLM APIs available)")
                print("  ⚠️  To test LLM functionality, add API keys to src/api/api.txt")
                
                white_agent = SimpleGreedyAgent(
                    agent_id="test_white",
                    agent_name="Greedy White"
                )
                black_agent = RandomAgent(
                    agent_id="test_black",
                    agent_name="Random Black"
                )
                white_name = "Greedy White"
                black_name = "Random Black"
                
                print(f"  ⚪ White: {white_name}")
                print(f"  ⚫ Black: {black_name}")
                
                max_moves = 15
                game_id = "test_simple_vs_simple"
            
            # Run the game
            print(f"\n🚀 Starting game (max {max_moves} moves)...")
            if self.llm_available:
                print("  ⏳ This may take several minutes with LLM agents...")
                print("  💡 Each move requires: API call + Stockfish evaluation" if self.stockfish_available else "  💡 Each move requires: API call")
                print("  ⌨️  Press Ctrl+C to interrupt if needed")
            
            results = green_agent.run_game(
                white_agent=white_agent,
                black_agent=black_agent,
                game_id=game_id,
                max_moves=max_moves
            )
            
            # Verify results structure
            assert 'game_id' in results, "Missing game_id in results"
            assert 'result' in results, "Missing result in results"
            assert 'total_moves' in results, "Missing total_moves in results"
            assert 'metrics' in results, "Missing metrics in results"
            
            # Display results
            print("\n" + "="*80)
            print("📊 GAME RESULTS")
            print("="*80)
            print(f"Result: {results['result']}")
            print(f"Total Moves: {results['total_moves']}")
            print(f"Game ID: {results['game_id']}")
            print(f"Log file: logs/test_complete_system/{results['game_id']}.json")
            
            # Display metrics if Stockfish available
            if self.stockfish_available:
                white_metrics = results['metrics']['metrics']['white']
                black_metrics = results['metrics']['metrics']['black']
                
                print(f"\n⚪ {white_name} Performance:")
                print(f"   ACPL: {white_metrics['acpl']:.2f}")
                print(f"   Estimated ELO: {white_metrics['estimated_elo']}")
                print(f"   Skill Level: {white_metrics['skill_level']}")
                print(f"   Best Moves: {white_metrics['best_moves']}")
                print(f"   Good Moves: {white_metrics['good_moves']}")
                print(f"   Inaccuracies: {white_metrics['inaccuracies']}")
                print(f"   Mistakes: {white_metrics['mistakes']}")
                print(f"   Blunders: {white_metrics['blunders']}")
                
                print(f"\n⚫ {black_name} Performance:")
                print(f"   ACPL: {black_metrics['acpl']:.2f}")
                print(f"   Estimated ELO: {black_metrics['estimated_elo']}")
                print(f"   Skill Level: {black_metrics['skill_level']}")
                print(f"   Best Moves: {black_metrics['best_moves']}")
                print(f"   Good Moves: {black_metrics['good_moves']}")
                print(f"   Inaccuracies: {black_metrics['inaccuracies']}")
                print(f"   Mistakes: {black_metrics['mistakes']}")
                print(f"   Blunders: {black_metrics['blunders']}")
            else:
                print("\n⚠️  Move quality metrics not available (Stockfish not installed)")
                print("   Basic game statistics recorded")
            
            # Cleanup
            green_agent.close()
            
            self.test_results['passed'] += 1
            print("\n✓ TEST 3 PASSED")
            return True, results
            
        except KeyboardInterrupt:
            print("\n⚠️  Game interrupted by user")
            self.test_results['skipped'] += 1
            return False, None
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Test 3 (Green Agent LLM Flow): {str(e)}")
            print(f"\n✗ TEST 3 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def test_evaluation_system(self):
        """Test 4: Evaluation System (if Stockfish available)"""
        print("\n" + "="*80)
        print("TEST 4: EVALUATION SYSTEM")
        print("="*80)
        
        if not self.stockfish_available:
            print("⚠ Skipping evaluation test (Stockfish not available)")
            self.test_results['skipped'] += 1
            return True
        
        try:
            from evaluation import MetricsCollector, SingleMovequality
            import chess
            
            # Create evaluator
            evaluator = StockfishEvaluator()
            if not evaluator.is_available():
                raise Exception("Stockfish evaluator not available")
            print("✓ StockfishEvaluator created")
            
            # Create metrics collector
            metrics = MetricsCollector(
                game_id="test_eval_001",
                white_player="Test White",
                black_player="Test Black"
            )
            print("✓ MetricsCollector created")
            
            # Test position evaluation
            board = chess.Board()
            eval_score = evaluator.evaluate_position(board)
            print(f"✓ Position evaluated: {eval_score} centipawns")
            
            # Test move evaluation
            move = chess.Move.from_uci("e2e4")
            eval_info = evaluator.evaluate_move(board, move)
            print(f"✓ Move evaluated: {eval_info.get('centipawn_loss', 'N/A')} cp loss")
            
            # Cleanup
            evaluator.close()
            
            self.test_results['passed'] += 1
            print("\n✓ TEST 4 PASSED")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Test 4 (Evaluation): {str(e)}")
            print(f"\n✗ TEST 4 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_visualization(self, game_results=None):
        """Test 5: Visualization System"""
        print("\n" + "="*80)
        print("TEST 5: VISUALIZATION SYSTEM")
        print("="*80)
        
        try:
            # If no game results provided, create a test game
            if game_results is None:
                print("Creating a test game for visualization...")
                green_agent = ChessGreenAgent(
                    agent_id="test_viz_agent",
                    use_stockfish=self.stockfish_available,
                    log_dir="logs/test_complete_system"
                )
                
                # Use LLM agents if available, otherwise simple agents
                if self.llm_available and len(self.available_llm_agents) >= 1:
                    llm_name, llm_agent = self.available_llm_agents[0]
                    llm_agent.reset()
                    white_agent = llm_agent
                    black_agent = SimpleGreedyAgent(
                        agent_id="viz_simple",
                        agent_name="Viz Simple"
                    )
                else:
                    white_agent = RandomAgent(
                        agent_id="viz_white",
                        agent_name="Viz White"
                    )
                    black_agent = RandomAgent(
                        agent_id="viz_black",
                        agent_name="Viz Black"
                    )
                
                game_results = green_agent.run_game(
                    white_agent=white_agent,
                    black_agent=black_agent,
                    game_id="test_viz_game",
                    max_moves=8
                )
                green_agent.close()
            
            # Test HTML Report
            print("\nTesting HTML report generation...")
            html_reporter = HTMLReporter(output_dir="logs/test_complete_system/reports")
            html_file = html_reporter.generate_game_report(game_results, include_charts=True)
            print(f"✓ HTML report generated: {html_file.name}")
            
            # Test Charts (if matplotlib available)
            try:
                print("\nTesting chart generation...")
                chart_gen = ChartGenerator(output_dir="logs/test_complete_system/charts")
                charts = chart_gen.generate_all_charts(game_results)
                print(f"✓ Charts generated: {len(charts)} files")
                for chart_name in charts.keys():
                    print(f"  - {chart_name}")
            except ImportError:
                print("⚠ Chart generation skipped (matplotlib not installed)")
            except Exception as e:
                print(f"⚠ Chart generation failed: {e}")
            
            # Test Game Replay
            print("\nTesting game replay generation...")
            replay = GameReplay()
            replay_file = replay.generate_replay_html(game_results)
            print(f"✓ Game replay generated: {replay_file.name}")
            
            self.test_results['passed'] += 1
            print("\n✓ TEST 5 PASSED")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Test 5 (Visualization): {str(e)}")
            print(f"\n✗ TEST 5 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_logging(self):
        """Test 6: Logging System"""
        print("\n" + "="*80)
        print("TEST 6: LOGGING SYSTEM")
        print("="*80)
        
        try:
            import json
            from pathlib import Path
            
            # Check if log files exist
            log_dir = Path("logs/test_complete_system")
            log_files = list(log_dir.glob("*.json"))
            
            if log_files:
                print(f"✓ Found {len(log_files)} log file(s)")
                
                # Verify log file structure
                with open(log_files[0], 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                required_keys = ['game_id', 'result', 'total_moves', 'metrics', 'game_log']
                for key in required_keys:
                    if key in log_data:
                        print(f"✓ Log contains '{key}' field")
                    else:
                        raise Exception(f"Missing required key: {key}")
                
                print(f"✓ Log file structure verified")
            else:
                print("⚠ No log files found (this is OK if no games were run)")
            
            self.test_results['passed'] += 1
            print("\n✓ TEST 6 PASSED")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Test 6 (Logging): {str(e)}")
            print(f"\n✗ TEST 6 FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("CHESS GREEN AGENT - COMPLETE SYSTEM TEST SUITE")
        print("="*80)
        print("\nThis test suite will verify all major components of the system.")
        print("Tests will adapt based on available dependencies (Stockfish, matplotlib, etc.)")
        
        # Check dependencies
        self.check_stockfish()
        self.check_llm_apis()
        
        # Run tests
        game_results = None
        
        try:
            # Test 1: Environment
            self.test_environment()
            
            # Test 2: Agents
            self.test_agents()
            
            # Test 3: Green Agent with LLM Flow
            success, game_results = self.test_green_agent_llm_flow()
            
            # Test 4: Evaluation (if Stockfish available)
            self.test_evaluation_system()
            
            # Test 5: Visualization (use game results from Test 3)
            if game_results:
                self.test_visualization(game_results)
            else:
                self.test_visualization()
            
            # Test 6: Logging
            self.test_logging()
            
        except KeyboardInterrupt:
            print("\n\n⚠ Tests interrupted by user")
            return False
        except Exception as e:
            print(f"\n\n✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Print summary
        self.print_summary()
        
        return self.test_results['failed'] == 0
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.test_results['passed'] + self.test_results['failed'] + self.test_results['skipped']}")
        print(f"✓ Passed: {self.test_results['passed']}")
        print(f"✗ Failed: {self.test_results['failed']}")
        print(f"⚠ Skipped: {self.test_results['skipped']}")
        
        if self.test_results['errors']:
            print("\nErrors:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        if self.test_results['failed'] == 0:
            print("\n" + "="*80)
            print("✓ ALL TESTS PASSED!")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("✗ SOME TESTS FAILED")
            print("="*80)
        
        print("\nGenerated Files:")
        print("  - Logs: logs/test_complete_system/")
        print("  - Reports: logs/test_complete_system/reports/")
        print("  - Charts: logs/test_complete_system/charts/")


def main():
    """Main entry point"""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

