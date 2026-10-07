"""
refusal/engine.py
V3.3 Safe Refusal & Boundary Enforcement Engine.
Converts sensor degradation, non-planarity, camera drift, and ambiguity into safe refusal.
"""

from typing import Dict, Any, List, Optional
from enum import Enum

class RefusalDecision(str, Enum):
    AUTONOMOUS_INTERVENTION_PERMITTED = "AUTONOMOUS_INTERVENTION_PERMITTED"
    ADVISORY_WARNING_ONLY = "ADVISORY_WARNING_ONLY"
    SAFE_REFUSAL_INSUFFICIENT_EVIDENCE = "SAFE_REFUSAL_INSUFFICIENT_EVIDENCE"

class SafeRefusalEngine:
    def __init__(self,
                 pitch_range: tuple = (35.0, 55.0),
                 degraded_pitch_range: tuple = (20.0, 35.0),
                 max_operational_distance_m: float = 8.0,
                 max_advisory_distance_m: float = 10.0,
                 max_latency_ms: float = 50.0,
                 max_degraded_latency_ms: float = 500.0):
        self.pitch_range = pitch_range
        self.degraded_pitch_range = degraded_pitch_range
        self.max_operational_distance_m = max_operational_distance_m
        self.max_advisory_distance_m = max_advisory_distance_m
        self.max_latency_ms = max_latency_ms
        self.max_degraded_latency_ms = max_degraded_latency_ms

        # Refusal audit counters
        self.appropriate_refusals = 0
        self.false_refusals = 0
        self.unsafe_non_refusals = 0
        self.total_evaluations = 0

    def evaluate_telemetry(self,
                           geometry_state: str,
                           camera_pitch_deg: float,
                           distance_m: float,
                           latency_ms: float,
                           illumination_lux: float,
                           identity_ambiguity_score: float = 0.0,
                           odd_tier: str = "NOMINAL_ODD") -> Dict[str, Any]:
        """
        Evaluates operational conditions and outputs safe decision.
        Returns RefusalDecision and comprehensive audit trail.
        """
        self.total_evaluations += 1
        refusal_flags = []
        advisory_flags = []

        # 1. Geometry Check
        if geometry_state == "NON_PLANAR_REFUSAL":
            refusal_flags.append("Floor geometry non-planar: slope > 3.0 deg or excessive homography residual.")
        elif geometry_state == "PLANAR_DEGRADED":
            advisory_flags.append("Floor geometry degraded: mild slope (1.5-3.0 deg).")

        # 2. Camera Pitch Check
        if camera_pitch_deg < self.degraded_pitch_range[0] or camera_pitch_deg > 65.0:
            refusal_flags.append(f"Camera pitch ({camera_pitch_deg:.1f} deg) outside allowable optical envelope.")
        elif self.degraded_pitch_range[0] <= camera_pitch_deg < self.pitch_range[0]:
            advisory_flags.append(f"Camera pitch ({camera_pitch_deg:.1f} deg) shallow (degraded ODD).")

        # 3. Distance Check
        if distance_m > self.max_advisory_distance_m:
            refusal_flags.append(f"Distance ({distance_m:.1f}m) exceeds absolute perception boundary (10.0m).")
        elif distance_m > self.max_operational_distance_m:
            advisory_flags.append(f"Distance ({distance_m:.1f}m) exceeds nominal 8.0m defensive clamping range.")

        # 4. Latency Check
        if latency_ms > self.max_degraded_latency_ms:
            refusal_flags.append(f"Frame processing latency ({latency_ms:.1f}ms) critically degraded.")
        elif latency_ms > self.max_latency_ms:
            advisory_flags.append(f"Frame processing latency ({latency_ms:.1f}ms) above 50.0ms nominal.")

        # 5. Illumination Check
        if illumination_lux < 50.0:
            refusal_flags.append(f"Illumination ({illumination_lux:.1f} lux) below sensor noise threshold.")
        elif illumination_lux < 150.0:
            advisory_flags.append(f"Low ambient illumination ({illumination_lux:.1f} lux).")

        # 6. Ambiguity Check
        if identity_ambiguity_score > 0.75:
            advisory_flags.append(f"High tracking association ambiguity ({identity_ambiguity_score:.2f}).")

        # Determine Final Decision
        if refusal_flags:
            decision = RefusalDecision.SAFE_REFUSAL_INSUFFICIENT_EVIDENCE
            self.appropriate_refusals += 1
        elif advisory_flags or odd_tier in ["DEGRADED_ODD", "MIXED_ODD"]:
            decision = RefusalDecision.ADVISORY_WARNING_ONLY
        else:
            decision = RefusalDecision.AUTONOMOUS_INTERVENTION_PERMITTED

        return {
            "decision": decision.value,
            "refusal_triggered": decision == RefusalDecision.SAFE_REFUSAL_INSUFFICIENT_EVIDENCE,
            "refusal_flags": refusal_flags,
            "advisory_flags": advisory_flags,
            "telemetry": {
                "geometry_state": geometry_state,
                "camera_pitch_deg": camera_pitch_deg,
                "distance_m": distance_m,
                "latency_ms": latency_ms,
                "illumination_lux": illumination_lux,
                "odd_tier": odd_tier
            }
        }
