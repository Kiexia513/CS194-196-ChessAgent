"""
Efficiency tracking utilities (optional).
"""

import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class EfficiencyTracker:
    start_ts: float = field(default_factory=time.time)
    llm_calls: int = 0

    def inc_llm(self):
        self.llm_calls += 1

    def snapshot(self) -> Dict[str, float]:
        return {"uptime_s": time.time() - self.start_ts, "llm_calls": float(self.llm_calls)}

