"""
Phase 15 — Versioned Output Schema

Standardizes the JSON outputs of the Safety Backfire Engine to prevent random
ad-hoc formats across different scripts.
"""
import json
from pathlib import Path
from typing import Dict, Any

SCHEMA_VERSION = "2.0"
ENGINE_VERSION = "1.0.0"

class OutputManager:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _wrap_with_schema(self, data_type: str, payload: Any) -> Dict[str, Any]:
        return {
            "metadata": {
                "schema_version": SCHEMA_VERSION,
                "engine_version": ENGINE_VERSION,
                "data_type": data_type
            },
            "data": payload
        }
        
    def _write_json(self, filename: str, data_type: str, payload: Any):
        wrapped = self._wrap_with_schema(data_type, payload)
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(wrapped, f, indent=2)
            
    def save_events(self, events: Any):
        self._write_json("events.json", "InteractionEvents", events)
        
    def save_trajectories(self, trajectories: Any):
        self._write_json("trajectories.json", "WorldTrajectories", trajectories)
        
    def save_risk_analysis(self, risk_data: Any):
        self._write_json("risk_analysis.json", "RiskExposure", risk_data)
        
    def save_comparison(self, comparison_data: Any):
        self._write_json("comparison.json", "BeforeAfterComparison", comparison_data)
        
    def save_evidence(self, evidence_data: Any):
        self._write_json("evidence.json", "EvidenceQuality", evidence_data)
        
    def save_backfire_assessment(self, assessment_data: Any):
        self._write_json("backfire_assessment.json", "SafetyBackfireAssessment", assessment_data)
