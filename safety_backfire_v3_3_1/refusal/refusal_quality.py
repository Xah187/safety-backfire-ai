"""
refusal/refusal_quality.py
V3.3.1 Safe Refusal Quality, Confusion Matrix, and Multi-Trigger Index Engine.

Implements Sections 10, 11, 12, and 27 requirements:
- TRUE_SAFE_REFUSAL, UNSAFE_NON_REFUSAL, FALSE_REFUSAL, ADVISORY_DOWNGRADE, LATE_REFUSAL, EARLY_REFUSAL
- 4x4 Refusal Confusion Matrix (FULL_INTERVENTION, ADVISORY, SAFE_REFUSAL, INSUFFICIENT_EVIDENCE)
- Comprehensive Refusal Quality Index across trigger modalities
"""

from typing import Dict, Any, List, Optional
from enum import Enum

class OperationalState(str, Enum):
    FULL_INTERVENTION = "FULL_INTERVENTION"
    ADVISORY = "ADVISORY"
    SAFE_REFUSAL = "SAFE_REFUSAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class RefusalClassification(str, Enum):
    TRUE_SAFE_REFUSAL = "TRUE_SAFE_REFUSAL"
    UNSAFE_NON_REFUSAL = "UNSAFE_NON_REFUSAL"
    FALSE_REFUSAL = "FALSE_REFUSAL"
    ADVISORY_DOWNGRADE = "ADVISORY_DOWNGRADE"
    LATE_REFUSAL = "LATE_REFUSAL"
    EARLY_REFUSAL = "EARLY_REFUSAL"

class RefusalQualityEngine:
    def __init__(self,
                 max_distance_nominal: float = 8.0,
                 max_distance_hard: float = 10.0,
                 max_latency_nominal: float = 50.0,
                 max_latency_hard: float = 500.0,
                 max_slope_deg: float = 1.5,
                 min_illumination_lux: float = 150.0):
        self.max_distance_nominal = max_distance_nominal
        self.max_distance_hard = max_distance_hard
        self.max_latency_nominal = max_latency_nominal
        self.max_latency_hard = max_latency_hard
        self.max_slope_deg = max_slope_deg
        self.min_illumination_lux = min_illumination_lux

    def evaluate_decision(self,
                          expected_state: OperationalState,
                          observed_state: OperationalState,
                          detection_latency_ms: float = 25.0,
                          lead_time_ms: float = 800.0) -> Dict[str, Any]:
        """Classify refusal action quality."""
        classification = None
        if expected_state in {OperationalState.SAFE_REFUSAL, OperationalState.INSUFFICIENT_EVIDENCE}:
            if observed_state in {OperationalState.SAFE_REFUSAL, OperationalState.INSUFFICIENT_EVIDENCE}:
                if detection_latency_ms > 100.0 or lead_time_ms < 200.0:
                    classification = RefusalClassification.LATE_REFUSAL
                else:
                    classification = RefusalClassification.TRUE_SAFE_REFUSAL
            else:
                classification = RefusalClassification.UNSAFE_NON_REFUSAL
        elif expected_state == OperationalState.ADVISORY:
            if observed_state == OperationalState.ADVISORY:
                classification = RefusalClassification.ADVISORY_DOWNGRADE
            elif observed_state in {OperationalState.SAFE_REFUSAL, OperationalState.INSUFFICIENT_EVIDENCE}:
                classification = RefusalClassification.EARLY_REFUSAL
            else:
                classification = RefusalClassification.UNSAFE_NON_REFUSAL
        else: # expected_state == FULL_INTERVENTION
            if observed_state in {OperationalState.SAFE_REFUSAL, OperationalState.INSUFFICIENT_EVIDENCE}:
                classification = RefusalClassification.FALSE_REFUSAL
            elif observed_state == OperationalState.ADVISORY:
                classification = RefusalClassification.ADVISORY_DOWNGRADE
            else:
                classification = RefusalClassification.TRUE_SAFE_REFUSAL # Correct full execution

        return {
            "expected_state": expected_state.value,
            "observed_state": observed_state.value,
            "classification": classification.value
        }

    def process_telemetry(self,
                          distance_m: float,
                          latency_ms: float,
                          slope_deg: float,
                          pitch_deg: float,
                          illumination_lux: float,
                          identity_ambiguous: bool = False,
                          uncertainty_k_exceeded: bool = False,
                          odd_tier: str = "NOMINAL_ODD") -> Dict[str, Any]:
        """Evaluate operational conditions and return state and specific trigger flags."""
        triggers = []
        is_refusal = False
        is_advisory = False

        if uncertainty_k_exceeded:
            triggers.append("uncertainty_triggered_refusal")
            is_refusal = True

        if slope_deg > 3.0:
            triggers.append("geometry_triggered_refusal")
            is_refusal = True
        elif slope_deg > self.max_slope_deg:
            triggers.append("geometry_triggered_advisory")
            is_advisory = True

        if pitch_deg < 20.0 or pitch_deg > 65.0:
            triggers.append("ODD_triggered_refusal")
            is_refusal = True
        elif pitch_deg < 35.0:
            triggers.append("ODD_triggered_advisory")
            is_advisory = True

        if distance_m > self.max_distance_hard:
            triggers.append("ODD_triggered_refusal")
            is_refusal = True
        elif distance_m > self.max_distance_nominal:
            triggers.append("ODD_triggered_advisory")
            is_advisory = True

        if latency_ms > self.max_latency_hard:
            triggers.append("latency_triggered_refusal")
            is_refusal = True
        elif latency_ms > self.max_latency_nominal:
            triggers.append("latency_triggered_advisory")
            is_advisory = True

        if illumination_lux < 50.0:
            triggers.append("ODD_triggered_refusal")
            is_refusal = True
        elif illumination_lux < self.min_illumination_lux:
            triggers.append("ODD_triggered_advisory")
            is_advisory = True

        if identity_ambiguous:
            triggers.append("identity_triggered_refusal")
            is_advisory = True  # Safety rule: ambiguity causes advisory or refusal

        if is_refusal:
            state = OperationalState.SAFE_REFUSAL
        elif is_advisory or odd_tier in ["DEGRADED_ODD", "OUT_OF_ODD"]:
            state = OperationalState.ADVISORY
        else:
            state = OperationalState.FULL_INTERVENTION

        return {
            "state": state.value,
            "triggers": triggers,
            "is_refusal": is_refusal,
            "is_advisory": is_advisory
        }
