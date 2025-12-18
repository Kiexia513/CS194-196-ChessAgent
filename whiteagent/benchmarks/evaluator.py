"""
Benchmark Evaluator
===================

Provides tools for comparing multiple agents and
analyzing benchmark results.

Features:
- Multi-agent comparison
- Baseline comparison
- Performance visualization
- Statistical analysis
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .benchmark import ChessBenchmark, BenchmarkResult


@dataclass
class ComparisonResult:
    """Result of comparing multiple agents"""
    agents: List[str]
    benchmark_id: str
    
    # Rankings
    accuracy_ranking: List[tuple]  # [(agent_name, accuracy), ...]
    speed_ranking: List[tuple]  # [(agent_name, avg_time), ...]
    
    # Detailed comparison
    comparison_table: Dict[str, Dict[str, float]]
    
    # Analysis
    best_overall: str
    best_accuracy: str
    fastest: str


class BenchmarkEvaluator:
    """
    Evaluates and compares multiple agents on benchmarks.
    
    Provides tools for:
    - Running benchmarks on multiple agents
    - Comparing agent performance
    - Generating comparison reports
    """
    
    def __init__(self, benchmark: Optional[ChessBenchmark] = None):
        """
        Initialize evaluator.
        
        Args:
            benchmark: ChessBenchmark instance (creates new if None)
        """
        self.benchmark = benchmark or ChessBenchmark()
        self.results: Dict[str, BenchmarkResult] = {}
    
    def evaluate_agent(
        self, 
        agent, 
        categories: Optional[List[str]] = None,
        verbose: bool = True
    ) -> BenchmarkResult:
        """
        Evaluate a single agent and store results.
        
        Args:
            agent: Chess agent to evaluate
            categories: Categories to test
            verbose: Print progress
            
        Returns:
            BenchmarkResult
        """
        result = self.benchmark.evaluate_agent(agent, categories, verbose)
        self.results[agent.agent_id] = result
        return result
    
    def evaluate_multiple(
        self, 
        agents: List[Any],
        categories: Optional[List[str]] = None,
        verbose: bool = True
    ) -> Dict[str, BenchmarkResult]:
        """
        Evaluate multiple agents.
        
        Args:
            agents: List of chess agents
            categories: Categories to test
            verbose: Print progress
            
        Returns:
            Dictionary of agent_id -> BenchmarkResult
        """
        results = {}
        
        for i, agent in enumerate(agents):
            if verbose:
                print(f"\n{'='*60}")
                print(f"Evaluating Agent {i+1}/{len(agents)}: {agent.agent_name}")
                print(f"{'='*60}")
            
            result = self.evaluate_agent(agent, categories, verbose)
            results[agent.agent_id] = result
            
            # Reset agent for next evaluation
            agent.reset()
        
        return results
    
    def compare_agents(
        self, 
        agent_ids: Optional[List[str]] = None
    ) -> ComparisonResult:
        """
        Compare multiple agents' benchmark results.
        
        Args:
            agent_ids: List of agent IDs to compare (None = all evaluated)
            
        Returns:
            ComparisonResult with rankings and analysis
        """
        if agent_ids is None:
            agent_ids = list(self.results.keys())
        
        # Build comparison table
        comparison_table = {}
        accuracy_list = []
        speed_list = []
        
        for agent_id in agent_ids:
            if agent_id not in self.results:
                continue
            
            result = self.results[agent_id]
            
            comparison_table[result.agent_name] = {
                "accuracy": result.accuracy,
                "good_moves": result.good_moves,
                "best_moves": result.best_moves,
                "avg_time": result.avg_thinking_time,
                "avg_confidence": result.avg_confidence,
                "total_positions": result.total_positions
            }
            
            accuracy_list.append((result.agent_name, result.accuracy))
            speed_list.append((result.agent_name, result.avg_thinking_time))
        
        # Sort rankings
        accuracy_ranking = sorted(accuracy_list, key=lambda x: x[1], reverse=True)
        speed_ranking = sorted(speed_list, key=lambda x: x[1])  # Lower is better
        
        # Determine bests
        best_accuracy = accuracy_ranking[0][0] if accuracy_ranking else "N/A"
        fastest = speed_ranking[0][0] if speed_ranking else "N/A"
        
        # Overall best (weighted: 70% accuracy, 30% speed)
        scores = {}
        for name, acc in accuracy_list:
            time_score = 1 - (dict(speed_list)[name] / max(1, max(s[1] for s in speed_list)))
            scores[name] = 0.7 * acc + 0.3 * time_score
        
        best_overall = max(scores.items(), key=lambda x: x[1])[0] if scores else "N/A"
        
        return ComparisonResult(
            agents=[r.agent_name for r in self.results.values() if r.agent_id in agent_ids],
            benchmark_id="chess_benchmark_v1",
            accuracy_ranking=accuracy_ranking,
            speed_ranking=speed_ranking,
            comparison_table=comparison_table,
            best_overall=best_overall,
            best_accuracy=best_accuracy,
            fastest=fastest
        )
    
    def generate_comparison_report(
        self, 
        comparison: ComparisonResult,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a text comparison report.
        
        Args:
            comparison: ComparisonResult to report on
            output_file: Optional file to save report
            
        Returns:
            Report as string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("AGENT COMPARISON REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Agents Compared: {len(comparison.agents)}")
        lines.append(f"Best Overall: {comparison.best_overall}")
        lines.append(f"Best Accuracy: {comparison.best_accuracy}")
        lines.append(f"Fastest: {comparison.fastest}")
        lines.append("")
        
        # Accuracy Ranking
        lines.append("ACCURACY RANKING")
        lines.append("-" * 40)
        for i, (name, acc) in enumerate(comparison.accuracy_ranking, 1):
            lines.append(f"  {i}. {name}: {acc*100:.1f}%")
        lines.append("")
        
        # Speed Ranking
        lines.append("SPEED RANKING (avg time per move)")
        lines.append("-" * 40)
        for i, (name, time) in enumerate(comparison.speed_ranking, 1):
            lines.append(f"  {i}. {name}: {time:.2f}s")
        lines.append("")
        
        # Detailed Table
        lines.append("DETAILED COMPARISON")
        lines.append("-" * 40)
        header = f"{'Agent':<25} {'Accuracy':<12} {'Good/Total':<12} {'Avg Time':<10} {'Confidence':<10}"
        lines.append(header)
        lines.append("-" * len(header))
        
        for name, data in comparison.comparison_table.items():
            lines.append(
                f"{name:<25} {data['accuracy']*100:>6.1f}%     "
                f"{data['good_moves']}/{data['total_positions']:<8} "
                f"{data['avg_time']:>6.2f}s    {data['avg_confidence']:>6.2f}"
            )
        
        lines.append("")
        lines.append("=" * 70)
        
        report = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to: {output_file}")
        
        return report
    
    def print_comparison(self, comparison: ComparisonResult):
        """Print comparison report to console"""
        print(self.generate_comparison_report(comparison))
    
    def get_category_comparison(self, category: str) -> Dict[str, float]:
        """
        Get accuracy comparison for a specific category.
        
        Args:
            category: Category name (e.g., "opening", "tactical")
            
        Returns:
            Dictionary of agent_name -> accuracy for that category
        """
        comparison = {}
        
        for agent_id, result in self.results.items():
            if category in result.category_results:
                comparison[result.agent_name] = result.category_results[category]["accuracy"]
        
        return comparison
    
    def save_all_results(self, output_dir: str = "results"):
        """Save all benchmark results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for agent_id, result in self.results.items():
            self.benchmark.save_results(result, output_dir)
        
        # Save comparison summary
        if len(self.results) > 1:
            comparison = self.compare_agents()
            report_file = output_path / "comparison_report.txt"
            self.generate_comparison_report(comparison, str(report_file))


