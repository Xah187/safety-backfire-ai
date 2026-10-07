"""
safety_backfire_v3_3_2/refusal/action_gating.py
Uncertainty-Aware Action Gating Engine.
Enforces Section 5, Section 6, and Section 7 requirements.
Separates PHYSICAL_ODD from EVIDENCE_CONFIDENCE.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ObservationContext:
    distance_m: float
    uncertainty_width_m: float
    camera_pitch_deg: float
    floor_slope_deg: float
    geometry_residual_m: float
    tracking_confidence: float
    identity_state: str  # "CONFIRMED_UNIQUE", "UNKNOWN_AMBIGUOUS_PAIR", "UNKNOWN"
    latency_ms: float
    illumination_lux: float
    hazard_confidence: float

@dataclass
class GatingDecision:
    allowed_action: str  # "FULL_AUTONOMOUS_ACTION", "ADVISORY_ONLY", "SAFE_REFUSAL"
    confidence_state: str  # "UNCERTAINTY_CONFIDENT", "UNCERTAINTY_DEGRADED", "UNCERTAINTY_INSUFFICIENT"
    reason_code: str
    required_confidence: float
    is_physical_odd_nominal: bool
    is_evidence_confident: bool

class UncertaintyActionGatingEngine:
    def __init__(self):
        # Locked Pre-Registered Thresholds
        self.MAX_NOMINAL_DISTANCE_M = 8.0
        self.MIN_NOMINAL_DISTANCE_M = 0.5
        self.MAX_CONFIDENT_INTERVAL_WIDTH_M = 0.25
        self.MAX_DEGRADED_INTERVAL_WIDTH_M = 0.40
        self.MIN_CAMERA_PITCH_DEG = 20.0
        self.MAX_FLOOR_SLOPE_DEG = 3.0
        self.MAX_GEOMETRY_RESIDUAL_M = 0.025
        self.MIN_TRACKING_CONFIDENCE = 0.85
        self.MAX_LATENCY_MS = 500.0
        self.MIN_NOMINAL_ILLUMINATION_LUX = 250.0
        self.MIN_SAFE_ILLUMINATION_LUX = 50.0
        self.MIN_HAZARD_CONFIDENCE = 0.80

    def evaluate_action_gate(self, ctx: ObservationContext) -> GatingDecision:
        # Step 1: Check Physical ODD Boundaries
        is_physical_nominal = (
            self.MIN_NOMINAL_DISTANCE_M <= ctx.distance_m <= self.MAX_NOMINAL_DISTANCE_M
            and ctx.camera_pitch_deg >= self.MIN_CAMERA_PITCH_DEG
            and ctx.floor_slope_deg <= self.MAX_FLOOR_SLOPE_DEG
            and ctx.illumination_lux >= self.MIN_SAFE_ILLUMINATION_LUX
            and ctx.latency_ms <= self.MAX_LATENCY_MS
        )

        # Step 2: Check for Hard Boundary Refusals (SAFE_REFUSAL)
        if ctx.distance_m > self.MAX_NOMINAL_DISTANCE_M:
            return GatingDecision(
                allowed_action="SAFE_REFUSAL",
                confidence_state="UNCERTAINTY_INSUFFICIENT",
                reason_code="FARFIELD_DISTANCE_EXCEEDED",
                required_confidence=0.95,
                is_physical_odd_nominal=False,
                is_evidence_confident=False
            )
        if ctx.camera_pitch_deg < self.MIN_CAMERA_PITCH_DEG:
            return GatingDecision(
                allowed_action="SAFE_REFUSAL",
                confidence_state="UNCERTAINTY_INSUFFICIENT",
                reason_code="CAMERA_PITCH_VIOLATION",
                required_confidence=0.95,
                is_physical_odd_nominal=False,
                is_evidence_confident=False
            )
        if ctx.floor_slope_deg > self.MAX_FLOOR_SLOPE_DEG:
            return GatingDecision(
                allowed_action="SAFE_REFUSAL",
                confidence_state="UNCERTAINTY_INSUFFICIENT",
                reason_code="FLOOR_SLOPE_VIOLATION",
                required_confidence=0.95,
                is_physical_odd_nominal=False,
                is_evidence_confident=False
            )
        if ctx.illumination_lux < self.MIN_SAFE_ILLUMINATION_LUX:
            return GatingDecision(
                allowed_action="SAFE_REFUSAL",
                confidence_state="UNCERTAINTY_INSUFFICIENT",
                reason_code="CRITICAL_LOW_ILLUMINATION",
                required_confidence=0.95,
                is_physical_odd_nominal=False,
                is_evidence_confident=False
            )
        if ctx.latency_ms > self.MAX_LATENCY_MS:
            return GatingDecision(
                allowed_action="SAFE_REFUSAL",
                confidence_state="UNCERTAINTY_INSUFFICIENT",
                reason_code="PIPELINE_LATENCY_EXCEEDED",
                required_confidence=0.95,
                is_physical_odd_nominal=False,
                is_evidence_confident=False
            )
        if ctx.uncertainty_width_m > self.MAX_DEGRADED_INTERVAL_WIDTH_M:
            return GatingDecision(
                allowed_action="SAFE_REFUSAL",
                confidence_state="UNCERTAINTY_INSUFFICIENT",
                reason_code="SPATIAL_UNCERTAINTY_TOO_HIGH",
                required_confidence=0.95,
                is_physical_odd_nominal=is_physical_nominal,
                is_evidence_confident=False
            )

        # Step 3: Check Evidence Confidence inside Nominal Physical ODD
        # Can we grant FULL_AUTONOMOUS_ACTION?
        evidence_confident = (
            ctx.uncertainty_width_m <= self.MAX_CONFIDENT_INTERVAL_WIDTH_M
            and ctx.geometry_residual_m <= self.MAX_GEOMETRY_RESIDUAL_M
            and ctx.tracking_confidence >= self.MIN_TRACKING_CONFIDENCE
            and ctx.identity_state == "CONFIRMED_UNIQUE"
            and ctx.illumination_lux >= self.MIN_NOMINAL_ILLUMINATION_LUX
            and ctx.hazard_confidence >= self.MIN_HAZARD_CONFIDENCE
        )

        if evidence_confident:
            return GatingDecision(
                allowed_action="FULL_AUTONOMOUS_ACTION",
                confidence_state="UNCERTAINTY_CONFIDENT",
                reason_code="NOMINAL_HIGH_CONFIDENCE",
                required_confidence=0.95,
                is_physical_odd_nominal=True,
                is_evidence_confident=True
            )

        # Step 4: Physical ODD is nominal, but Evidence is Degraded -> ADVISORY_ONLY
        degraded_reasons = []
        if ctx.identity_state in ("UNKNOWN_AMBIGUOUS_PAIR", "UNKNOWN"):
            degraded_reasons.append("IDENTITY_AMBIGUITY_ADVISORY")
        if ctx.illumination_lux < self.MIN_NOMINAL_ILLUMINATION_LUX:
            degraded_reasons.append("DEGRADED_ILLUMINATION_ADVISORY")
        if ctx.uncertainty_width_m > self.MAX_CONFIDENT_INTERVAL_WIDTH_M:
            degraded_reasons.append("SPATIAL_UNCERTAINTY_ELEVATED")
        if ctx.tracking_confidence < self.MIN_TRACKING_CONFIDENCE:
            degraded_reasons.append("TRACKING_QUALITY_DEGRADED")
        if ctx.geometry_residual_m > self.MAX_GEOMETRY_RESIDUAL_M:
            degraded_reasons.append("GEOMETRY_RESIDUAL_ELEVATED")

        primary_reason = degraded_reasons[0] if degraded_reasons else "DEGRADED_EVIDENCE_ADVISORY"

        return GatingDecision(
            allowed_action="ADVISORY_ONLY",
            confidence_state="UNCERTAINTY_DEGRADED",
            reason_code=primary_reason,
            required_confidence=0.85,
            is_physical_odd_nominal=True,
            is_evidence_confident=False
        )
