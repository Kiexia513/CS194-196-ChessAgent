"""
White Agent Benchmark Test
==========================

Comprehensive benchmark test for the White Agent.
Compares against baseline agents and generates performance reports.

Usage:
    python tests/test_white_agent_benchmark.py

Test Coverage:
- Opening positions
- Tactical positions  
- Endgame positions
- Defensive positions
- Complex positions

Agents Tested:
- WhiteAgent (main agent with CoT)
- RandomAgent (baseline)
- SimpleGreedyAgent (baseline)
- Basic LLM Agent (baseline without CoT)
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent))

from white_agent import WhiteAgent
from white_agent.agent import AgentConfig
from green_agent import RandomAgent, SimpleGreedyAgent, DeepSeekAgent
from benchmarks import ChessBenchmark, BenchmarkEvaluator
from config.api_config import get_api_key, print_api_status


def create_agents():
    """Create all agents for benchmark comparison"""
    agents = []
    
    # 1. Baseline: Random Agent
    print("Creating RandomAgent (baseline)...")
    random_agent = RandomAgent(
        agent_id="baseline_random",
        agent_name="Random Baseline"
    )
    agents.append(random_agent)
    
    # 2. Baseline: Simple Greedy Agent
    print("Creating SimpleGreedyAgent (baseline)...")
    greedy_agent = SimpleGreedyAgent(
        agent_id="baseline_greedy",
        agent_name="Greedy Baseline"
    )
    agents.append(greedy_agent)
    
    # 3. Check if LLM APIs are available
    deepseek_key = get_api_key("deepseek")
    
    if deepseek_key:
        # Basic LLM Agent (without CoT - using existing DeepSeekAgent)
        print("Creating DeepSeekAgent (LLM baseline)...")
        llm_baseline = DeepSeekAgent(
            agent_id="baseline_llm",
            agent_name="LLM Baseline (DeepSeek)",
            model="deepseek-chat"
        )
        agents.append(llm_baseline)
        
        # White Agent with CoT
        print("Creating WhiteAgent (main agent with CoT)...")
        config = AgentConfig(
            api_provider="deepseek",
            model="deepseek-chat",
            use_chain_of_thought=True,
            max_candidates=10,  # Increased to include more good moves
            timeout=60
        )
        white_agent = WhiteAgent(
            agent_id="white_agent_cot",
            agent_name="White Agent (CoT)",
            config=config
        )
        agents.append(white_agent)
        
        # White Agent without CoT (for ablation) - still uses reasoning module
        print("Creating WhiteAgent (no CoT - ablation)...")
        config_no_cot = AgentConfig(
            api_provider="deepseek",
            model="deepseek-chat",
            use_chain_of_thought=False,
            max_candidates=10  # Increased
        )
        white_agent_no_cot = WhiteAgent(
            agent_id="white_agent_no_cot",
            agent_name="White Agent (No CoT)",
            config=config_no_cot
        )
        agents.append(white_agent_no_cot)
    else:
        print("\n⚠️  No DeepSeek API key found")
        print("   Only testing baseline agents")
        print("   To test LLM agents, add API key to src/api/api.txt")
    
    return agents


def run_benchmark():
    """Run full benchmark suite"""
    print("\n" + "=" * 70)
    print("WHITE AGENT BENCHMARK TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check API status
    print("\n--- API Status ---")
    print_api_status()
    
    # Create agents
    print("\n--- Creating Agents ---")
    agents = create_agents()
    print(f"Total agents: {len(agents)}")
    
    # Create benchmark and evaluator
    print("\n--- Loading Benchmark ---")
    benchmark = ChessBenchmark()
    evaluator = BenchmarkEvaluator(benchmark)
    
    positions = benchmark.get_all_positions()
    print(f"Total test positions: {len(positions)}")
    
    # Show position categories
    categories = {}
    for pos in positions:
        categories[pos.category] = categories.get(pos.category, 0) + 1
    print("Categories:", dict(categories))
    
    # Run evaluation
    print("\n" + "=" * 70)
    print("RUNNING BENCHMARK EVALUATION")
    print("=" * 70)
    
    results = evaluator.evaluate_multiple(agents, verbose=True)
    
    # Compare agents
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    
    comparison = evaluator.compare_agents()
    evaluator.print_comparison(comparison)
    
    # Save results
    print("\n--- Saving Results ---")
    output_dir = "results/benchmark"
    evaluator.save_all_results(output_dir)
    print(f"Results saved to: {output_dir}/")
    
    # Print key findings
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)
    
    print(f"\n🏆 Best Overall: {comparison.best_overall}")
    print(f"🎯 Best Accuracy: {comparison.best_accuracy}")
    print(f"⚡ Fastest: {comparison.fastest}")
    
    # Improvement analysis
    if len(results) >= 2:
        baseline_accuracy = results.get("baseline_random", results[list(results.keys())[0]]).accuracy
        
        print("\n📊 Improvement over Random Baseline:")
        for agent_id, result in results.items():
            if agent_id != "baseline_random":
                improvement = (result.accuracy - baseline_accuracy) * 100
                print(f"   {result.agent_name}: +{improvement:.1f}%")
    
    return results


def run_quick_test():
    """Run a quick test with fewer positions"""
    print("\n" + "=" * 70)
    print("WHITE AGENT QUICK TEST")
    print("=" * 70)
    
    # Create just one agent for quick testing
    deepseek_key = get_api_key("deepseek")
    
    if deepseek_key:
        config = AgentConfig(
            api_provider="deepseek",
            model="deepseek-chat",
            use_chain_of_thought=True,
            max_candidates=3,
            timeout=30
        )
        agent = WhiteAgent(
            agent_id="white_agent_test",
            agent_name="White Agent Test",
            config=config
        )
    else:
        print("No API key, using RandomAgent")
        agent = RandomAgent(agent_id="test", agent_name="Test Agent")
    
    # Test on just opening positions
    benchmark = ChessBenchmark()
    result = benchmark.evaluate_agent(
        agent, 
        categories=["opening_positions"],
        verbose=True
    )
    
    print("\n--- Quick Test Results ---")
    print(f"Agent: {result.agent_name}")
    print(f"Accuracy: {result.accuracy * 100:.1f}%")
    print(f"Avg Time: {result.avg_thinking_time:.2f}s")
    
    return result


def test_reasoning_quality():
    """Test and display reasoning quality"""
    print("\n" + "=" * 70)
    print("REASONING QUALITY TEST")
    print("=" * 70)
    
    deepseek_key = get_api_key("deepseek")
    
    if not deepseek_key:
        print("⚠️  No API key available, skipping reasoning test")
        return
    
    # Create white agent
    config = AgentConfig(
        api_provider="deepseek",
        model="deepseek-chat",
        use_chain_of_thought=True,
        max_candidates=5
    )
    agent = WhiteAgent(
        agent_id="reasoning_test",
        agent_name="Reasoning Test Agent",
        config=config
    )
    
    # Test positions
    test_positions = [
        {
            "name": "Opening Decision",
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "description": "Starting position - test opening reasoning"
        },
        {
            "name": "Tactical Position",
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
            "description": "Italian Game - test tactical awareness"
        }
    ]
    
    print("\nTesting reasoning quality on sample positions...\n")
    
    for pos in test_positions:
        print(f"Position: {pos['name']}")
        print(f"Description: {pos['description']}")
        print("-" * 50)
        
        import chess
        board = chess.Board(pos["fen"])
        legal_moves = [m.uci() for m in board.legal_moves]
        
        board_state = {
            "fen": pos["fen"],
            "legal_moves": legal_moves,
            "move_number": 1
        }
        
        response = agent.get_move(board_state)
        
        print(f"Move: {response.move_uci}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Reasoning: {response.reasoning}")
        
        if response.metadata and "reasoning_chain" in response.metadata:
            print("\nReasoning Chain:")
            for step in response.metadata["reasoning_chain"]:
                print(f"  {step}")
        
        print("\n" + "=" * 50 + "\n")
        
        # Reset for next position
        agent.reset()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="White Agent Benchmark Test")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    parser.add_argument("--reasoning", action="store_true", help="Test reasoning quality")
    parser.add_argument("--full", action="store_true", help="Run full benchmark")
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_test()
    elif args.reasoning:
        test_reasoning_quality()
    elif args.full:
        run_benchmark()
    else:
        # Default: run quick test
        print("Running quick test (use --full for complete benchmark)")
        run_quick_test()


if __name__ == "__main__":
    main()

