"""
safety_backfire_v3_3_3/uncertainty/model_h.py
Canonical frozen implementation of Model H (Pitch-Compensated Anisotropic Condition-Aware Uncertainty Scaling).

Source of Truth: outputs/v3_3_3/reconciliation/model_h_lineage.json
Canonical Formula:
    k_H(d, L, occ, pitch) = k0 + beta_d * max(0.0, d - 4.0)
                               + beta_L * max(0.0, 300.0 - L) / 100.0
                               + beta_pitch * I(pitch < 40.0)
                               + gamma_occ[occ]

Parameters (FROZEN):
    k0 = 2.40
    beta_d = 0.08
    beta_l = 0.12
    beta_pitch = 0.22
    pitch_threshold_deg = 40.0
    gamma_occ = {"NONE": 0.00, "PARTIAL": 0.20, "HEAVY": 0.40}

Missing Input Semantics:
    If any required physical dimension is unavailable (None or NOT_AVAILABLE):
    STATUS = INPUT_INSUFFICIENT
    No substitution of guessed, default, or uncalibrated values is permitted.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

# Canonical frozen parameters
K0: float = 2.40
BETA_D: float = 0.08
BETA_L: float = 0.12
BETA_PITCH: float = 0.22
PITCH_THRESHOLD_DEG: float = 40.0
GAMMA_OCC: Dict[str, float] = {
    "NONE": 0.00,
    "PARTIAL": 0.20,
    "HEAVY": 0.40
}

@dataclass
class ModelHResult:
    status: str  # "SUCCESS" or "INPUT_INSUFFICIENT"
    k_H: Optional[float]
    k0: float
    distance_term: Optional[float]
    illumination_term: Optional[float]
    pitch_term: Optional[float]
    occlusion_term: Optional[float]
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "k_H": self.k_H,
            "k0": self.k0,
            "distance_term": self.distance_term,
            "illumination_term": self.illumination_term,
            "pitch_term": self.pitch_term,
            "occlusion_term": self.occlusion_term,
            "reason": self.reason
        }

def compute_distance_penalty(distance_m: float) -> float:
    """Canonical distance penalty: beta_d * max(0.0, d - 4.0).
    For d <= 4.0m, penalty is exactly 0.0.
    For d > 4.0m, increases with slope beta_d = 0.08.
    """
    if distance_m < 0.0:
        raise ValueError(f"Distance cannot be negative: {distance_m}")
    return BETA_D * max(0.0, float(distance_m) - 4.0)

def compute_illumination_penalty(illumination_lux: float) -> float:
    """Canonical illumination penalty: beta_L * max(0.0, 300.0 - L) / 100.0.
    For L >= 300.0 lux, penalty is exactly 0.0.
    For L < 300.0 lux, penalty increases as lighting dims.
    """
    if illumination_lux < 0.0:
        raise ValueError(f"Illumination lux cannot be negative: {illumination_lux}")
    return BETA_L * (max(0.0, 300.0 - float(illumination_lux)) / 100.0)

def compute_pitch_penalty(camera_pitch_deg: float) -> float:
    """Canonical pitch compensation: beta_pitch * I(pitch < 40.0).
    For pitch >= 40.0 deg, penalty is exactly 0.0.
    For pitch < 40.0 deg, penalty is exactly beta_pitch = 0.22.
    """
    return BETA_PITCH if float(camera_pitch_deg) < PITCH_THRESHOLD_DEG else 0.0

def compute_occlusion_penalty(occlusion_state: str) -> float:
    """Canonical occlusion penalty: gamma_occ[state].
    NONE = 0.00, PARTIAL = 0.20, HEAVY = 0.40.
    """
    if occlusion_state not in GAMMA_OCC:
        raise KeyError(f"Invalid occlusion state: {occlusion_state}. Must be one of {list(GAMMA_OCC.keys())}")
    return GAMMA_OCC[occlusion_state]

def compute_canonical_model_h(
    distance_m: Optional[float],
    illumination_lux: Optional[float],
    camera_pitch_deg: Optional[float],
    occlusion_state: Optional[str]
) -> ModelHResult:
    """Computes exact canonical Model H coverage factor k_H.
    
    Strictly enforces missing input semantics:
    If any variable is None, returns status='INPUT_INSUFFICIENT'.
    Never invents defaults (e.g. no L=0.5, no pitch=0).
    """
    # Check distance
    if distance_m is None:
        return ModelHResult(
            status="INPUT_INSUFFICIENT",
            k_H=None,
            k0=K0,
            distance_term=None,
            illumination_term=None,
            pitch_term=None,
            occlusion_term=None,
            reason="MISSING_DISTANCE_M"
        )

    # Check illumination
    if illumination_lux is None:
        return ModelHResult(
            status="INPUT_INSUFFICIENT",
            k_H=None,
            k0=K0,
            distance_term=compute_distance_penalty(distance_m),
            illumination_term=None,
            pitch_term=None,
            occlusion_term=None,
            reason="MISSING_ILLUMINATION_LUX"
        )

    # Check pitch
    if camera_pitch_deg is None:
        return ModelHResult(
            status="INPUT_INSUFFICIENT",
            k_H=None,
            k0=K0,
            distance_term=compute_distance_penalty(distance_m),
            illumination_term=compute_illumination_penalty(illumination_lux),
            pitch_term=None,
            occlusion_term=None,
            reason="MISSING_CAMERA_PITCH_DEG"
        )

    # Check occlusion
    if occlusion_state is None or occlusion_state not in GAMMA_OCC:
        return ModelHResult(
            status="INPUT_INSUFFICIENT",
            k_H=None,
            k0=K0,
            distance_term=compute_distance_penalty(distance_m),
            illumination_term=compute_illumination_penalty(illumination_lux),
            pitch_term=compute_pitch_penalty(camera_pitch_deg),
            occlusion_term=None,
            reason="MISSING_OR_INVALID_OCCLUSION_STATE"
        )

    d_term = compute_distance_penalty(distance_m)
    l_term = compute_illumination_penalty(illumination_lux)
    p_term = compute_pitch_penalty(camera_pitch_deg)
    o_term = compute_occlusion_penalty(occlusion_state)

    k_total = round(K0 + d_term + l_term + p_term + o_term, 6)

    return ModelHResult(
        status="SUCCESS",
        k_H=k_total,
        k0=K0,
        distance_term=round(d_term, 6),
        illumination_term=round(l_term, 6),
        pitch_term=round(p_term, 6),
        occlusion_term=round(o_term, 6),
        reason=None
    )
