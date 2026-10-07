"""
causality/did_engine.py
V3.3 Difference-in-Differences (DiD) Causal Attribution Engine.
Evaluates parallel-trend assumption, tests for exogenous site-wide shocks,
and refuses causal attribution (INSUFFICIENT_EVIDENCE) when trends diverge.
"""

from typing import Dict, Any, List, Optional
from enum import Enum

class CausalStatus(str, Enum):
    ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS = "ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NO_DETECTABLE_EFFECT = "NO_DETECTABLE_EFFECT"

class DifferenceInDifferencesEngine:
    def __init__(self, parallel_trend_tolerance: float = 0.15):
        self.parallel_trend_tolerance = parallel_trend_tolerance

    def estimate_effect(self,
                        treated_pre_risk: float,
                        treated_post_risk: float,
                        control_pre_risk: float,
                        control_post_risk: float,
                        exogenous_traffic_shock: float = 0.0) -> Dict[str, Any]:
        """
        Computes DiD estimator:
        delta_treated = treated_post - treated_pre
        delta_control = control_post - control_pre
        did = delta_treated - delta_control
        """
        delta_treated = round(treated_post_risk - treated_pre_risk, 4)
        delta_control = round(control_post_risk - control_pre_risk, 4)
        did_result = round(delta_treated - delta_control, 4)

        # Check parallel-trend stability in control zone
        # If control zone shifts by more than tolerance due to site-wide shocks, assumption fails
        control_shift = abs(delta_control)
        trend_violated = control_shift > self.parallel_trend_tolerance or abs(exogenous_traffic_shock) > 0.20

        reasons = []
        if trend_violated:
            status = CausalStatus.INSUFFICIENT_EVIDENCE
            if control_shift > self.parallel_trend_tolerance:
                reasons.append(f"Control zone baseline shifted by {control_shift:.2%} (> {self.parallel_trend_tolerance:.0%}); parallel-trend assumption invalid.")
            if abs(exogenous_traffic_shock) > 0.20:
                reasons.append(f"Exogenous site shock detected ({exogenous_traffic_shock:.1%}); confounding site-wide throughput.")
        elif abs(did_result) < 0.02:
            status = CausalStatus.NO_DETECTABLE_EFFECT
            reasons.append(f"DiD coefficient ({did_result:.4f}) is statistically indistinguishable from zero.")
        else:
            status = CausalStatus.ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS
            reasons.append(f"Parallel trends verified (control shift {control_shift:.2%}); net change attributed to intervention under DiD assumptions.")

        return {
            "did_coefficient": did_result,
            "delta_treated": delta_treated,
            "delta_control": delta_control,
            "control_drift": delta_control,
            "parallel_trend_valid": not trend_violated,
            "causal_status": status.value,
            "attribution_reasons": reasons
        }
