"""
Reasoning Analyzer (optional utility)

Provides lightweight hooks for analyzing the reasoning chain produced by the WhiteAgent.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ReasoningAnalyzer:
    def summarize(self, reasoning_chain: List[str]) -> Dict[str, Any]:
        return {"steps": len(reasoning_chain), "preview": reasoning_chain[:5]}

