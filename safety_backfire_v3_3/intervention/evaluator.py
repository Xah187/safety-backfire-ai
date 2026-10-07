"""
intervention/evaluator.py
V3.3 Safety Backfire & Intervention Impact Evaluator.
Analyzes pre/post/intervention/control data across diverse physical interventions.
Classifies outcomes into explicit backfire states.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from ..causality.did_engine import DifferenceInDifferencesEngine, CausalStatus

class InterventionOutcome(str, Enum):
    RISK_REDUCED = "RISK_REDUCED"
    PARTIAL_BACKFIRE = "PARTIAL_BACKFIRE"
    NEW_HAZARD_CREATED = "NEW_HAZARD_CREATED"
    RISK_REDISTRIBUTED = "RISK_REDISTRIBUTED"
    NO_DETECTABLE_EFFECT = "NO_DETECTABLE_EFFECT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

@dataclass
class InterventionRecord:
    intervention_id: str
    case_id: str
    control_zone_id: str
    intervention_type: str  # "barrier_installation", "speed_limitation", "route_change", etc.
    pre_primary_risk: float
    post_primary_risk: float
    pre_secondary_risk: float
    post_secondary_risk: float
    control_pre_risk: float
    control_post_risk: float
    new_hazard_detected: bool
    new_hazard_type: Optional[str]
    exogenous_shock: float = 0.0

class SafetyBackfireEvaluator:
    def __init__(self, did_engine: Optional[DifferenceInDifferencesEngine] = None):
        self.did_engine = did_engine or DifferenceInDifferencesEngine()

    def evaluate_intervention(self, record: InterventionRecord) -> Dict[str, Any]:
        """Evaluates intervention outcomes, primary/secondary risk deltas, and causal validity."""
        # 1. Evaluate primary risk DiD
        primary_did = self.did_engine.estimate_effect(
            treated_pre_risk=record.pre_primary_risk,
            treated_post_risk=record.post_primary_risk,
            control_pre_risk=record.control_pre_risk,
            control_post_risk=record.control_post_risk,
            exogenous_traffic_shock=record.exogenous_shock
        )

        delta_primary = record.post_primary_risk - record.pre_primary_risk
        delta_secondary = record.post_secondary_risk - record.pre_secondary_risk

        # 2. Determine Outcome State
        if not primary_did["parallel_trend_valid"]:
            outcome = InterventionOutcome.INSUFFICIENT_EVIDENCE
        elif record.new_hazard_detected:
            outcome = InterventionOutcome.NEW_HAZARD_CREATED
        elif delta_secondary > 0.15 and delta_primary < -0.15:
            outcome = InterventionOutcome.RISK_REDISTRIBUTED
        elif delta_secondary > 0.05 and delta_primary < 0.0:
            outcome = InterventionOutcome.PARTIAL_BACKFIRE
        elif delta_primary < -0.05:
            outcome = InterventionOutcome.RISK_REDUCED
        else:
            outcome = InterventionOutcome.NO_DETECTABLE_EFFECT

        return {
            "intervention_id": record.intervention_id,
            "case_id": record.case_id,
            "control_zone_id": record.control_zone_id,
            "intervention_type": record.intervention_type,
            "outcome_state": outcome.value,
            "delta_primary_risk": round(delta_primary, 4),
            "delta_secondary_risk": round(delta_secondary, 4),
            "new_hazard_created": record.new_hazard_detected,
            "new_hazard_type": record.new_hazard_type,
            "did_analysis": primary_did,
            "causal_status": primary_did["causal_status"]
        }
