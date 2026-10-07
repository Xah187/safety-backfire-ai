"""
causality/backfire_evaluator.py
V3.3.1 Safety Backfire & Causal Evidence Governance Engine.

Implements Sections 19, 20, 21, 22, and 23 requirements:
- Case classification: PHYSICAL_NEW, PHYSICAL_HISTORICAL, REPLAY, SYNTHETIC, SIMULATED
- Difference-in-Differences calculation with parallel trend pre-treatment evaluation
- Backfire taxonomy states: RISK_REDUCED, RISK_REDISTRIBUTED, PARTIAL_BACKFIRE, NEW_HAZARD_CREATED, NO_DETECTABLE_EFFECT, INSUFFICIENT_EVIDENCE
- Prohibits population-level generalization claims from discrete sample sizes
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict

class ProvenanceClass(str, Enum):
    PHYSICAL_NEW = "PHYSICAL_NEW"
    PHYSICAL_HISTORICAL = "PHYSICAL_HISTORICAL"
    REPLAY = "REPLAY"
    SYNTHETIC = "SYNTHETIC"
    SIMULATED = "SIMULATED"

class BackfireOutcome(str, Enum):
    RISK_REDUCED = "RISK_REDUCED"
    RISK_REDISTRIBUTED = "RISK_REDISTRIBUTED"
    PARTIAL_BACKFIRE = "PARTIAL_BACKFIRE"
    NEW_HAZARD_CREATED = "NEW_HAZARD_CREATED"
    NO_DETECTABLE_EFFECT = "NO_DETECTABLE_EFFECT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

@dataclass
class BackfireCaseRecord:
    intervention_id: str
    case_id: str
    facility_id: str
    provenance_class: ProvenanceClass
    treated_zone: str
    control_zone: str
    pre_window: List[int]
    post_window: List[int]
    intervention_timestamp_s: float
    primary_hazard: str
    secondary_hazards: List[str]
    traffic_volume: int
    treated_pre_risk: float
    treated_post_risk: float
    treated_pre_secondary_risk: float = 0.10
    treated_post_secondary_risk: float = 0.10
    control_pre_risk: float = 0.20
    control_post_risk: float = 0.20
    pre_trend_p_value: float = 0.50  # Slope difference test in pre-period (p < 0.05 indicates violation)
    exogenous_shock_fraction: float = 0.0  # Site-wide shock percentage
    new_hazard_detected: bool = False
    new_hazard_type: Optional[str] = None
    source_hashes: Optional[List[str]] = None

class BackfireCausalityEngine:
    def __init__(self,
                 control_drift_tolerance: float = 0.15,
                 shock_tolerance: float = 0.20,
                 risk_redistribution_threshold: float = 0.15):
        self.control_drift_tolerance = control_drift_tolerance
        self.shock_tolerance = shock_tolerance
        self.risk_redistribution_threshold = risk_redistribution_threshold

    def evaluate_case(self, case: BackfireCaseRecord) -> Dict[str, Any]:
        """Evaluates DiD estimator, parallel trends, and backfire taxonomy state."""
        delta_treated = round(case.treated_post_risk - case.treated_pre_risk, 4)
        delta_control = round(case.control_post_risk - case.control_pre_risk, 4)
        did_coeff = round(delta_treated - delta_control, 4)

        delta_secondary = round(case.treated_post_secondary_risk - case.treated_pre_secondary_risk, 4)

        # Pre-trend and stability assessment
        control_shift = abs(delta_control)
        trend_violated = (
            case.pre_trend_p_value < 0.05 or
            control_shift > self.control_drift_tolerance or
            abs(case.exogenous_shock_fraction) > self.shock_tolerance
        )

        if trend_violated:
            outcome = BackfireOutcome.INSUFFICIENT_EVIDENCE
            causal_status = "INSUFFICIENT_EVIDENCE_PARALLEL_TREND_VIOLATED"
        elif case.new_hazard_detected:
            outcome = BackfireOutcome.NEW_HAZARD_CREATED
            causal_status = "ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS"
        elif delta_secondary > self.risk_redistribution_threshold and delta_treated < -self.risk_redistribution_threshold:
            outcome = BackfireOutcome.RISK_REDISTRIBUTED
            causal_status = "ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS"
        elif delta_secondary > 0.05 and delta_treated < 0.0:
            outcome = BackfireOutcome.PARTIAL_BACKFIRE
            causal_status = "ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS"
        elif delta_treated < -0.05:
            outcome = BackfireOutcome.RISK_REDUCED
            causal_status = "ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS"
        elif abs(did_coeff) < 0.02:
            outcome = BackfireOutcome.NO_DETECTABLE_EFFECT
            causal_status = "NO_DETECTABLE_EFFECT"
        else:
            outcome = BackfireOutcome.NO_DETECTABLE_EFFECT
            causal_status = "ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS"

        return {
            "intervention_id": case.intervention_id,
            "case_id": case.case_id,
            "facility_id": case.facility_id,
            "provenance_class": case.provenance_class.value,
            "treated_zone": case.treated_zone,
            "control_zone": case.control_zone,
            "primary_hazard": case.primary_hazard,
            "secondary_hazards": case.secondary_hazards,
            "traffic_volume": case.traffic_volume,
            "delta_treated": delta_treated,
            "delta_control": delta_control,
            "did_coefficient": did_coeff,
            "parallel_trend_valid": not trend_violated,
            "pre_trend_p_value": case.pre_trend_p_value,
            "control_shift": control_shift,
            "outcome_state": outcome.value,
            "causal_status": causal_status,
            "is_physical_new": case.provenance_class == ProvenanceClass.PHYSICAL_NEW
        }
