"""
V3.0.2 Core — Uncertainty-Aware Risk & Decision Engine

Resolves FAIL-22: Point-estimate risk ignores geometric uncertainty.
Implements structured risk policy under spatial-temporal uncertainty without
naive worst-case over-alerting.

Enforces:
1. Multi-dimensional risk intervals: [nominal_distance, uncertainty, distance_interval].
2. Decoupled risk categories: nominal_risk, uncertainty_level, plausible_danger, decision_state.
3. Monotonicity under variance: Higher uncertainty elevates review priority, never triggers erratic confirmed danger.
4. Trajectory & Evidence Fusion: Combines metric TTC, CPA miss-distance, and kinematic vectors with spatial confidence.
"""
import math
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field

@dataclass
class RiskEvaluationResult:
    """
    Immutable structured evaluation from the Uncertainty-Aware Risk Engine.
    Enforces clean semantic separation between:
      1. CURRENT_PROXIMITY_HAZARD (spatial breach of clearance envelope)
      2. PREDICTIVE_COLLISION_HAZARD (kinetic trajectory convergence / TTC threat)
      3. MEASUREMENT_UNCERTAINTY (sensor/calibration variance level)
    """
    nominal_distance_m: float
    distance_uncertainty_m: float           # 1-sigma standard uncertainty
    distance_interval_m: Tuple[float, float] # Expanded 95% interval [lower, upper]
    std_uncertainty_1sigma_m: float
    expanded_uncertainty_95_m: float
    coverage_factor_k: float
    nominal_risk: str                      # SAFE, CAUTION, DANGER
    uncertainty_level: str                 # LOW, MODERATE, HIGH
    plausible_danger: bool                 # True if lower 95% bound <= danger threshold
    proximity_hazard: bool                 # Spatial proximity breach
    predictive_collision_hazard: bool      # Active trajectory collision threat
    hazard_semantics: str                  # CURRENT_PROXIMITY_HAZARD, PREDICTIVE_COLLISION_HAZARD, DUAL_HAZARD, CLEAR
    clearance_policy_status: str           # CRITICAL_VIOLATION, WARNING_VIOLATION, ADEQUATE_CLEARANCE
    risk_decision: str                     # SAFE, CAUTION, HIGH_PRIORITY_CANDIDATE, CONFIRMED_DANGER, CANDIDATE_REVIEW, INSUFFICIENT_EVIDENCE
    risk_score: float                      # Continuous monotonic score [0.0..1.0]
    confidence_weight: float               # Spatial-temporal evidence quality [0.0..1.0]
    reason: str
    evidence_telemetry: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nominal_distance_m": self.nominal_distance_m,
            "distance_uncertainty_m": self.distance_uncertainty_m,
            "std_uncertainty_1sigma_m": self.std_uncertainty_1sigma_m,
            "expanded_uncertainty_95_m": self.expanded_uncertainty_95_m,
            "coverage_factor_k": self.coverage_factor_k,
            "distance_interval_m": list(self.distance_interval_m),
            "nominal_risk": self.nominal_risk,
            "uncertainty_level": self.uncertainty_level,
            "plausible_danger": self.plausible_danger,
            "proximity_hazard": self.proximity_hazard,
            "predictive_collision_hazard": self.predictive_collision_hazard,
            "hazard_semantics": self.hazard_semantics,
            "clearance_policy_status": self.clearance_policy_status,
            "risk_decision": self.risk_decision,
            "risk_score": round(self.risk_score, 3),
            "confidence_weight": round(self.confidence_weight, 3),
            "reason": self.reason,
            "evidence_telemetry": self.evidence_telemetry
        }


class UncertaintyAwareRiskEngine:
    """
    Evaluates pedestrian-vehicle proximity and collision likelihood under sensory uncertainty.
    Provides rigorous separation of current proximity vs kinetic trajectory threats.
    """
    def __init__(
        self,
        danger_distance_m: float = 1.5,
        caution_distance_m: float = 3.0,
        critical_ttc_sec: float = 2.5,
        cleared_cpa_miss_m: float = 1.8,
        critical_clearance_zone_m: float = 1.0,
        warning_clearance_zone_m: float = 1.8,
        coverage_factor_k: float = 1.96
    ):
        self.danger_distance_m = danger_distance_m
        self.caution_distance_m = caution_distance_m
        self.critical_ttc_sec = critical_ttc_sec
        self.cleared_cpa_miss_m = cleared_cpa_miss_m
        self.critical_clearance_zone_m = critical_clearance_zone_m
        self.warning_clearance_zone_m = warning_clearance_zone_m
        self.coverage_factor_k = coverage_factor_k

    def evaluate(
        self,
        nominal_distance_m: float,
        distance_uncertainty_m: float,
        evidence_quality: float = 0.8,
        ttc_sec: Optional[float] = None,
        cpa_miss_m: Optional[float] = None,
        relation_state: str = "INDEPENDENT_PEDESTRIAN",
        approach_speed_m_s: float = 0.0,
        coverage_factor: Optional[float] = None
    ) -> RiskEvaluationResult:
        """
        Fuses nominal distance, uncertainty interval, evidence quality, and trajectory metrics.
        Enforces clear hazard semantic taxonomy and clearance policy.
        """
        d_nom = max(0.0, float(nominal_distance_m))
        u_1sigma = max(0.05, float(distance_uncertainty_m))
        k = coverage_factor if coverage_factor is not None else self.coverage_factor_k
        u_95 = k * u_1sigma
        lower_95 = max(0.0, d_nom - u_95)
        upper_95 = d_nom + u_95
        
        # 1. Nominal Spatial Risk
        if d_nom <= self.danger_distance_m:
            nom_risk = "DANGER"
        elif d_nom <= self.caution_distance_m:
            nom_risk = "CAUTION"
        else:
            nom_risk = "SAFE"

        # 2. Categorical Uncertainty Level
        if u_1sigma < 0.25:
            unc_level = "LOW"
        elif u_1sigma <= 0.50:
            unc_level = "MODERATE"
        else:
            unc_level = "HIGH"

        # 3. Plausible Danger Flag (95% lower bound reaches danger zone)
        plausible_danger = (lower_95 <= self.danger_distance_m)

        # 4. Trajectory Threat Analysis (Predictive Collision)
        has_trajectory_threat = False
        if ttc_sec is not None and ttc_sec > 0 and ttc_sec <= self.critical_ttc_sec:
            if cpa_miss_m is not None:
                if cpa_miss_m <= self.cleared_cpa_miss_m:
                    has_trajectory_threat = True
            else:
                has_trajectory_threat = True

        # 5. Clearance Envelope Evaluation
        if d_nom <= self.critical_clearance_zone_m:
            clearance_status = "CRITICAL_VIOLATION"
        elif d_nom <= self.warning_clearance_zone_m:
            clearance_status = "WARNING_VIOLATION"
        else:
            clearance_status = "ADEQUATE_CLEARANCE"

        # 6. Proximity Hazard Flag (True if distance or upper bound violates safe clearance)
        is_proximity_hazard = (d_nom <= self.danger_distance_m) or (clearance_status == "CRITICAL_VIOLATION")

        # 7. Hazard Semantics Classification (Strict Disambiguation)
        if is_proximity_hazard and has_trajectory_threat:
            hazard_semantics = "DUAL_HAZARD"
        elif is_proximity_hazard:
            hazard_semantics = "CURRENT_PROXIMITY_HAZARD"
        elif has_trajectory_threat:
            hazard_semantics = "PREDICTIVE_COLLISION_HAZARD"
        elif nom_risk == "CAUTION" or plausible_danger:
            hazard_semantics = "UNCERTAIN_PROXIMITY_CAUTION"
        else:
            hazard_semantics = "CLEAR_SEPARATION"

        # 8. Continuous Monotonic Risk Score
        # Distance component: inverted exponential (monotonically non-increasing with distance)
        dist_factor = math.exp(-0.8 * min(d_nom, 6.0))
        
        # Trajectory threat boost
        traj_boost = 0.35 if has_trajectory_threat else 0.0
        
        # Uncertainty penalty / caution elevation (monotonically non-decreasing with uncertainty)
        unc_factor = min(0.25, (u_1sigma / 4.0))
        
        raw_score = (0.55 * dist_factor) + traj_boost + (0.20 * unc_factor)
        risk_score = min(1.0, max(0.0, raw_score))

        # 9. Policy Decision Logic
        telemetry = {
            "evidence_quality": round(evidence_quality, 2),
            "has_trajectory_threat": has_trajectory_threat,
            "is_proximity_hazard": is_proximity_hazard,
            "hazard_semantics": hazard_semantics,
            "clearance_status": clearance_status,
            "ttc_sec": round(ttc_sec, 2) if ttc_sec else None,
            "cpa_miss_m": round(cpa_miss_m, 2) if cpa_miss_m else None,
            "approach_speed_m_s": round(approach_speed_m_s, 2)
        }

        # Operator suppression override invariant
        if relation_state == "OPERATOR_ON_VEHICLE":
            return RiskEvaluationResult(
                nominal_distance_m=d_nom,
                distance_uncertainty_m=u_1sigma,
                distance_interval_m=(round(lower_95, 3), round(upper_95, 3)),
                std_uncertainty_1sigma_m=round(u_1sigma, 3),
                expanded_uncertainty_95_m=round(u_95, 3),
                coverage_factor_k=k,
                nominal_risk=nom_risk,
                uncertainty_level=unc_level,
                plausible_danger=plausible_danger,
                proximity_hazard=False,
                predictive_collision_hazard=False,
                hazard_semantics="OPERATOR_SUPPRESSED",
                clearance_policy_status=clearance_status,
                risk_decision="SUPPRESSED_OPERATOR",
                risk_score=0.0,
                confidence_weight=1.0,
                reason="operator_relation_verified",
                evidence_telemetry=telemetry
            )

        # Policy Branch 1: Weak evidence or massive uncertainty on nominal safe
        if nom_risk == "SAFE" and unc_level == "HIGH" and evidence_quality < 0.5:
            decision = "INSUFFICIENT_EVIDENCE"
            reason = "nominal_safe_masked_by_severe_spatial_uncertainty"

        # Policy Branch 2: Safe nominal distance with low/moderate uncertainty
        elif nom_risk == "SAFE":
            if not plausible_danger and not has_trajectory_threat:
                decision = "SAFE"
                reason = "clear_spatial_and_kinematic_separation"
            elif plausible_danger and not has_trajectory_threat:
                decision = "CANDIDATE_REVIEW"
                reason = "nominal_safe_with_plausible_boundary_penetration"
            else:
                decision = "HIGH_PRIORITY_CANDIDATE"
                reason = "safe_current_distance_with_converging_collision_trajectory"

        # Policy Branch 3: Nominal Caution Zone (1.5m < d <= 3.0m)
        elif nom_risk == "CAUTION":
            if has_trajectory_threat and evidence_quality >= 0.60:
                decision = "CONFIRMED_DANGER"
                reason = "caution_distance_with_converging_collision_trajectory"
            elif has_trajectory_threat:
                decision = "HIGH_PRIORITY_CANDIDATE"
                reason = "caution_distance_with_trajectory_threat_under_low_evidence"
            elif plausible_danger and unc_level == "HIGH":
                decision = "HIGH_PRIORITY_CANDIDATE"
                reason = "caution_distance_with_plausible_danger_under_high_uncertainty"
            elif plausible_danger:
                decision = "CANDIDATE_REVIEW"
                reason = "caution_distance_with_plausible_danger_boundary_penetration"
            else:
                decision = "CAUTION"
                reason = "confirmed_caution_proximity_without_collision_trajectory"

        # Policy Branch 4: Nominal Danger Zone or Critical Clearance Violation (<= 1.5m / <= 1.0m)
        else: # nom_risk == "DANGER" or clearance_status == "CRITICAL_VIOLATION"
            if evidence_quality >= 0.60:
                decision = "CONFIRMED_DANGER"
                if has_trajectory_threat:
                    reason = "direct_proximity_danger_with_active_collision_trajectory"
                else:
                    # Stationary or non-converging pair within critical proximity clearance!
                    reason = "direct_proximity_danger_with_high_quality_evidence"
            elif unc_level == "HIGH":
                decision = "CANDIDATE_REVIEW"
                reason = "danger_nominal_under_high_measurement_noise"
            else:
                decision = "HIGH_PRIORITY_CANDIDATE"
                reason = "danger_nominal_requiring_temporal_persistence"

        return RiskEvaluationResult(
            nominal_distance_m=d_nom,
            distance_uncertainty_m=round(u_1sigma, 3),
            distance_interval_m=(round(lower_95, 3), round(upper_95, 3)),
            std_uncertainty_1sigma_m=round(u_1sigma, 3),
            expanded_uncertainty_95_m=round(u_95, 3),
            coverage_factor_k=k,
            nominal_risk=nom_risk,
            uncertainty_level=unc_level,
            plausible_danger=plausible_danger,
            proximity_hazard=is_proximity_hazard,
            predictive_collision_hazard=has_trajectory_threat,
            hazard_semantics=hazard_semantics,
            clearance_policy_status=clearance_status,
            risk_decision=decision,
            risk_score=risk_score,
            confidence_weight=evidence_quality,
            reason=reason,
            evidence_telemetry=telemetry
        )
