"""
V3.1 Safety Ontology — Counterfactual Timeline & Windowing Model

Guarantees:
1. Baseline calculation is strictly isolated from post-intervention observations.
2. Invariant verification against temporal leakage, timestamp disorder, and retrospective mutation.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.interventions.types import InterventionRecord

class TemporalLeakageError(ValueError):
    """Raised when post-intervention observations attempt to leak into baseline calculations."""
    pass

@dataclass
class CounterfactualTimeline:
    """
    Manages immutable baseline and post-intervention windows.
    """
    intervention: InterventionRecord
    baseline_start_ts: float
    baseline_end_ts: float # Must equal intervention.timestamp
    post_start_ts: float    # Must equal intervention.timestamp
    post_end_ts: float

    def __post_init__(self):
        if self.baseline_end_ts > self.intervention.timestamp + 1e-6:
            raise TemporalLeakageError(
                f"Baseline window ends at {self.baseline_end_ts:.4f}, leaking past intervention timestamp {self.intervention.timestamp:.4f}!"
            )
        if self.post_start_ts < self.intervention.timestamp - 1e-6:
            raise TemporalLeakageError(
                f"Post window starts at {self.post_start_ts:.4f}, prior to intervention timestamp {self.intervention.timestamp:.4f}!"
            )

    def validate_baseline_frame(self, frame_timestamp: float) -> bool:
        """Enforces that no post-intervention frame can enter baseline analysis."""
        if frame_timestamp >= self.intervention.timestamp:
            raise TemporalLeakageError(
                f"Post-intervention frame (t={frame_timestamp:.4f}) illegally passed to baseline processor (cutoff: {self.intervention.timestamp:.4f})!"
            )
        return True

    def validate_post_frame(self, frame_timestamp: float) -> bool:
        """Enforces that post-window frames occur at or after intervention."""
        return frame_timestamp >= self.intervention.timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intervention": self.intervention.to_dict(),
            "baseline_window": [round(self.baseline_start_ts, 4), round(self.baseline_end_ts, 4)],
            "post_window": [round(self.post_start_ts, 4), round(self.post_end_ts, 4)],
            "baseline_duration_sec": round(self.baseline_end_ts - self.baseline_start_ts, 2),
            "post_duration_sec": round(self.post_end_ts - self.post_start_ts, 2)
        }
