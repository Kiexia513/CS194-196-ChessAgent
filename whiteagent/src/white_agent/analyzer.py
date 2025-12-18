"""
Reasoning Quality Analyzer
==========================

Analyzes and scores the quality of agent reasoning.
Provides interpretability metrics and failure analysis.

Metrics:
- Coherence: Logical flow of reasoning steps
- Completeness: Coverage of relevant factors
- Accuracy: Alignment between reasoning and move choice
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re


@dataclass
class ReasoningAnalysis:
    """Analysis of agent reasoning quality"""
    
    # Scores (0.0 to 1.0)
    coherence_score: float
    completeness_score: float
    accuracy_score: float
    overall_score: float
    
    # Details
    reasoning_steps: List[str]
    identified_factors: List[str]
    missing_factors: List[str]
    
    # Flags
    has_position_analysis: bool
    has_candidate_comparison: bool
    has_clear_conclusion: bool
    
    # Raw data
    raw_reasoning: str
    move_selected: str


@dataclass
class FailureAnalysis:
    """Analysis of a reasoning failure"""
    
    position_id: str
    expected_move: str
    actual_move: str
    
    failure_type: str  # "tactical_miss", "positional_error", "calculation_error", etc.
    root_cause: str
    reasoning_gaps: List[str]
    
    severity: str  # "minor", "moderate", "severe"


class ReasoningAnalyzer:
    """
    Analyzes agent reasoning quality and identifies failures.
    
    Provides:
    - Scoring of reasoning quality
    - Identification of reasoning patterns
    - Failure mode analysis
    - Improvement suggestions
    """
    
    # Expected factors in good chess reasoning
    EXPECTED_FACTORS = {
        "material": ["material", "piece", "pawn", "capture", "trade", "exchange"],
        "position": ["center", "control", "space", "position", "square"],
        "king_safety": ["king", "castle", "safety", "check", "attack"],
        "development": ["develop", "piece activity", "minor piece", "knight", "bishop"],
        "tactics": ["fork", "pin", "skewer", "discovered", "threat", "tactic"],
        "planning": ["plan", "strategy", "idea", "goal", "target"]
    }
    
    # Failure type patterns
    FAILURE_PATTERNS = {
        "tactical_miss": ["missed", "oversight", "didn't see", "failed to notice"],
        "calculation_error": ["miscalculated", "wrong", "error in", "incorrect"],
        "positional_error": ["weak square", "bad structure", "poor position"],
        "time_pressure": ["ran out", "time", "rushed"],
        "knowledge_gap": ["didn't know", "unfamiliar", "unknown"]
    }
    
    def __init__(self):
        self.analysis_history: List[ReasoningAnalysis] = []
        self.failure_history: List[FailureAnalysis] = []
    
    def analyze_reasoning(
        self,
        reasoning: str,
        move_selected: str,
        reasoning_chain: Optional[List[str]] = None,
        position_context: Optional[Dict[str, Any]] = None
    ) -> ReasoningAnalysis:
        """
        Analyze the quality of agent reasoning.
        
        Args:
            reasoning: The reasoning text from the agent
            move_selected: The move that was selected
            reasoning_chain: Optional list of reasoning steps
            position_context: Optional position information
            
        Returns:
            ReasoningAnalysis with scores and details
        """
        # Extract reasoning steps
        if reasoning_chain:
            steps = reasoning_chain
        else:
            steps = self._extract_steps(reasoning)
        
        # Identify factors mentioned
        identified_factors = self._identify_factors(reasoning)
        missing_factors = self._find_missing_factors(identified_factors, position_context)
        
        # Check for key components
        has_position_analysis = self._has_position_analysis(reasoning)
        has_candidate_comparison = self._has_candidate_comparison(reasoning)
        has_clear_conclusion = self._has_clear_conclusion(reasoning, move_selected)
        
        # Calculate scores
        coherence = self._score_coherence(steps)
        completeness = self._score_completeness(identified_factors, position_context)
        accuracy = self._score_accuracy(reasoning, move_selected, has_clear_conclusion)
        
        # Overall score (weighted average)
        overall = 0.4 * coherence + 0.3 * completeness + 0.3 * accuracy
        
        analysis = ReasoningAnalysis(
            coherence_score=coherence,
            completeness_score=completeness,
            accuracy_score=accuracy,
            overall_score=overall,
            reasoning_steps=steps,
            identified_factors=list(identified_factors),
            missing_factors=missing_factors,
            has_position_analysis=has_position_analysis,
            has_candidate_comparison=has_candidate_comparison,
            has_clear_conclusion=has_clear_conclusion,
            raw_reasoning=reasoning,
            move_selected=move_selected
        )
        
        self.analysis_history.append(analysis)
        return analysis
    
    def _extract_steps(self, reasoning: str) -> List[str]:
        """Extract reasoning steps from text"""
        steps = []
        
        # Try numbered steps (1., 2., etc.)
        numbered = re.findall(r'\d+\.\s*([^0-9]+?)(?=\d+\.|$)', reasoning)
        if numbered:
            steps.extend([s.strip() for s in numbered if s.strip()])
        
        # Try bullet points
        bullets = re.findall(r'[-•]\s*([^\n-•]+)', reasoning)
        if bullets:
            steps.extend([s.strip() for s in bullets if s.strip()])
        
        # Try sentence splitting if no structured steps found
        if not steps:
            sentences = reasoning.split('.')
            steps = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return steps[:10]  # Limit to 10 steps
    
    def _identify_factors(self, reasoning: str) -> set:
        """Identify chess factors mentioned in reasoning"""
        reasoning_lower = reasoning.lower()
        identified = set()
        
        for factor, keywords in self.EXPECTED_FACTORS.items():
            for keyword in keywords:
                if keyword in reasoning_lower:
                    identified.add(factor)
                    break
        
        return identified
    
    def _find_missing_factors(
        self, 
        identified: set,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Find important factors that weren't mentioned"""
        missing = []
        
        # Always expected factors
        core_factors = {"material", "position"}
        for factor in core_factors:
            if factor not in identified:
                missing.append(factor)
        
        # Context-dependent factors
        if context:
            if context.get("in_check") and "king_safety" not in identified:
                missing.append("king_safety (critical: in check!)")
            if context.get("captures_available") and "tactics" not in identified:
                missing.append("tactics (captures available)")
        
        return missing
    
    def _has_position_analysis(self, reasoning: str) -> bool:
        """Check if reasoning includes position analysis"""
        position_keywords = ["position", "fen", "board", "pieces", "material", "evaluation"]
        reasoning_lower = reasoning.lower()
        return any(kw in reasoning_lower for kw in position_keywords)
    
    def _has_candidate_comparison(self, reasoning: str) -> bool:
        """Check if reasoning compares candidate moves"""
        comparison_keywords = ["candidate", "option", "alternative", "compare", "better than", "instead of"]
        reasoning_lower = reasoning.lower()
        return any(kw in reasoning_lower for kw in comparison_keywords)
    
    def _has_clear_conclusion(self, reasoning: str, move: str) -> bool:
        """Check if reasoning has a clear conclusion"""
        conclusion_keywords = ["therefore", "so i choose", "best move", "i play", "decision", "selected"]
        reasoning_lower = reasoning.lower()
        
        has_conclusion_word = any(kw in reasoning_lower for kw in conclusion_keywords)
        mentions_move = move.lower() in reasoning_lower
        
        return has_conclusion_word or mentions_move
    
    def _score_coherence(self, steps: List[str]) -> float:
        """Score the logical coherence of reasoning"""
        if not steps:
            return 0.3
        
        score = 0.5  # Base score for having steps
        
        # Bonus for multiple steps
        if len(steps) >= 2:
            score += 0.2
        if len(steps) >= 4:
            score += 0.1
        
        # Check for logical connectors
        connectors = ["because", "therefore", "since", "so", "which", "this"]
        text = " ".join(steps).lower()
        connector_count = sum(1 for c in connectors if c in text)
        score += min(0.2, connector_count * 0.05)
        
        return min(1.0, score)
    
    def _score_completeness(
        self, 
        factors: set,
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Score the completeness of reasoning"""
        if not factors:
            return 0.2
        
        # Base score for having some factors
        score = 0.3
        
        # Score for each factor identified
        score += len(factors) * 0.1
        
        # Bonus for core factors
        if "material" in factors:
            score += 0.1
        if "position" in factors:
            score += 0.1
        if "tactics" in factors:
            score += 0.1
        
        return min(1.0, score)
    
    def _score_accuracy(
        self,
        reasoning: str,
        move: str,
        has_conclusion: bool
    ) -> float:
        """Score alignment between reasoning and move"""
        score = 0.4  # Base score
        
        # Clear conclusion bonus
        if has_conclusion:
            score += 0.3
        
        # Move mentioned in reasoning
        if move.lower() in reasoning.lower():
            score += 0.2
        
        # Confidence mentioned
        if "confidence" in reasoning.lower() or "certain" in reasoning.lower():
            score += 0.1
        
        return min(1.0, score)
    
    def analyze_failure(
        self,
        position_id: str,
        expected_move: str,
        actual_move: str,
        reasoning: str,
        position_context: Optional[Dict[str, Any]] = None
    ) -> FailureAnalysis:
        """
        Analyze a reasoning failure.
        
        Args:
            position_id: Identifier for the position
            expected_move: The expected correct move
            actual_move: The move the agent made
            reasoning: Agent's reasoning
            position_context: Optional position information
            
        Returns:
            FailureAnalysis with root cause identification
        """
        # Identify failure type
        failure_type = self._identify_failure_type(reasoning, expected_move, actual_move)
        
        # Determine root cause
        root_cause = self._determine_root_cause(reasoning, failure_type, position_context)
        
        # Find reasoning gaps
        reasoning_gaps = self._find_reasoning_gaps(reasoning, expected_move, position_context)
        
        # Assess severity
        severity = self._assess_severity(failure_type, position_context)
        
        failure = FailureAnalysis(
            position_id=position_id,
            expected_move=expected_move,
            actual_move=actual_move,
            failure_type=failure_type,
            root_cause=root_cause,
            reasoning_gaps=reasoning_gaps,
            severity=severity
        )
        
        self.failure_history.append(failure)
        return failure
    
    def _identify_failure_type(
        self,
        reasoning: str,
        expected: str,
        actual: str
    ) -> str:
        """Identify the type of failure"""
        reasoning_lower = reasoning.lower()
        
        # Check for pattern matches
        for ftype, patterns in self.FAILURE_PATTERNS.items():
            for pattern in patterns:
                if pattern in reasoning_lower:
                    return ftype
        
        # Infer from move difference
        if expected[2:4] != actual[2:4]:  # Different destination
            return "tactical_miss"
        
        return "unknown"
    
    def _determine_root_cause(
        self,
        reasoning: str,
        failure_type: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Determine the root cause of failure"""
        if failure_type == "tactical_miss":
            return "Failed to identify tactical opportunity or threat"
        elif failure_type == "calculation_error":
            return "Error in move calculation or sequence evaluation"
        elif failure_type == "positional_error":
            return "Misjudged positional factors"
        elif failure_type == "time_pressure":
            return "Insufficient time for proper analysis"
        elif failure_type == "knowledge_gap":
            return "Missing domain knowledge for position type"
        else:
            return "Unable to determine specific root cause"
    
    def _find_reasoning_gaps(
        self,
        reasoning: str,
        expected_move: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Find gaps in the reasoning"""
        gaps = []
        
        reasoning_lower = reasoning.lower()
        
        # Check if expected move was considered
        if expected_move.lower() not in reasoning_lower:
            gaps.append(f"Did not consider the move {expected_move}")
        
        # Check for missing factor analysis
        factors = self._identify_factors(reasoning)
        if "tactics" not in factors:
            gaps.append("No tactical analysis performed")
        if "king_safety" not in factors and context and context.get("in_check"):
            gaps.append("Did not address king safety while in check")
        
        return gaps
    
    def _assess_severity(
        self,
        failure_type: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Assess the severity of the failure"""
        if failure_type == "tactical_miss":
            return "moderate"
        elif failure_type == "calculation_error":
            return "moderate"
        elif failure_type == "positional_error":
            return "minor"
        elif context and context.get("in_check"):
            return "severe"
        else:
            return "minor"
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of all analyses"""
        if not self.analysis_history:
            return {"error": "No analyses performed"}
        
        coherence_scores = [a.coherence_score for a in self.analysis_history]
        completeness_scores = [a.completeness_score for a in self.analysis_history]
        overall_scores = [a.overall_score for a in self.analysis_history]
        
        return {
            "total_analyses": len(self.analysis_history),
            "avg_coherence": sum(coherence_scores) / len(coherence_scores),
            "avg_completeness": sum(completeness_scores) / len(completeness_scores),
            "avg_overall": sum(overall_scores) / len(overall_scores),
            "total_failures": len(self.failure_history),
            "failure_types": self._count_failure_types()
        }
    
    def _count_failure_types(self) -> Dict[str, int]:
        """Count failures by type"""
        counts = {}
        for failure in self.failure_history:
            counts[failure.failure_type] = counts.get(failure.failure_type, 0) + 1
        return counts
    
    def generate_report(self) -> str:
        """Generate a text report of reasoning quality"""
        stats = self.get_summary_statistics()
        
        lines = [
            "=" * 50,
            "REASONING QUALITY REPORT",
            "=" * 50,
            "",
            f"Total Analyses: {stats.get('total_analyses', 0)}",
            f"Average Coherence: {stats.get('avg_coherence', 0):.2f}",
            f"Average Completeness: {stats.get('avg_completeness', 0):.2f}",
            f"Average Overall: {stats.get('avg_overall', 0):.2f}",
            "",
            f"Total Failures: {stats.get('total_failures', 0)}",
            ""
        ]
        
        if stats.get("failure_types"):
            lines.append("Failure Types:")
            for ftype, count in stats["failure_types"].items():
                lines.append(f"  - {ftype}: {count}")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)


