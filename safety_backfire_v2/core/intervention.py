"""
Phase 11 — Intervention-aware Analysis

Ties the Before Segment and After Segment to a specific, well-defined physical or policy Intervention.
Prevents the comparison engine from assuming that temporal difference alone equals causality.
"""
from typing import Dict, Any, List

class Intervention:
    def __init__(self, intervention_id: str, type: str, zone: str, description: str, timestamp: str = "UNKNOWN"):
        self.intervention_id = intervention_id
        self.type = type  # e.g. "PHYSICAL_BARRIER", "POLICY_CHANGE", "WARNING_LIGHT"
        self.zone = zone
        self.description = description
        self.timestamp = timestamp
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "type": self.type,
            "zone": self.zone,
            "description": self.description,
            "timestamp": self.timestamp
        }

class InterventionExperiment:
    def __init__(
        self, 
        experiment_id: str, 
        intervention: Intervention, 
        before_segment_events: List[Dict[str, Any]], 
        after_segment_events: List[Dict[str, Any]]
    ):
        self.experiment_id = experiment_id
        self.intervention = intervention
        self.before_segment_events = before_segment_events
        self.after_segment_events = after_segment_events
        
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "intervention": self.intervention.to_dict(),
            "data_summary": {
                "before_events_count": len(self.before_segment_events),
                "after_events_count": len(self.after_segment_events)
            },
            "disclaimer": "Analysis is locked to this specific intervention. Causality is not assumed by temporal difference alone."
        }
