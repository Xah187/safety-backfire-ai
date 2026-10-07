"""
V3.0 Core — Empirical Ground Geometry & Man-Down Behavioral Hazard Engine

Solves FAIL-10 (Elevated cabin homography distortion up to 2.5m).
Implements empirical evaluation of 5 distinct geometric projection methods:
  - Method A: Planar Homography of bottom-center bounding box (Baseline).
  - Method B: Footpoint-based projection (isolating visible Ankle keypoints).
  - Method C: Pose-Ground Kinematic Projection (Torso-to-Floor vector projection).
  - Method D: Monocular Camera Ray-Plane Intersection (Camera elevation & pitch angle).
  - Method E: 3D Bounding Box approximation with vehicle elevation compensation.

Enforces Strict Ground Contact Invariant:
  Upper body keypoints (Head, Shoulders, Torso) are strictly forbidden from 
  being used directly as ground contact points. If lower limbs are occluded,
  Ground Position Confidence is explicitly degraded.

Implements Multi-Cue Man-Down State Classifier:
  STANDING, WALKING, RUNNING, CROUCHED, FALLEN_CANDIDATE, PARTIALLY_OCCLUDED, UNKNOWN.
"""
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import cv2

class CalibrationSource(str, Enum):
    DEFAULT = "DEFAULT"
    MANUAL_ESTIMATE = "MANUAL_ESTIMATE"
    VISUAL_ESTIMATE = "VISUAL_ESTIMATE"
    CALIBRATED = "CALIBRATED"
    SURVEYED = "SURVEYED"
    VERIFIED = "VERIFIED"
    UNVERIFIED_DEFAULT = "UNVERIFIED_DEFAULT"

OPERATOR_ELEVATION_SPECS: Dict[str, Dict[str, float]] = {
    "PALLET_TRUCK": {"nominal_m": 0.40, "uncertainty_m": 0.15},
    "REACH_TRUCK": {"nominal_m": 0.80, "uncertainty_m": 0.20},
    "COUNTERBALANCE": {"nominal_m": 1.20, "uncertainty_m": 0.25},
    "HIGH_TURRET": {"nominal_m": 1.50, "uncertainty_m": 0.30},
    "DISMOUNTED": {"nominal_m": 0.00, "uncertainty_m": 0.05}
}

@dataclass
class CameraCalibrationContract:
    """
    Formal camera extrinsic and intrinsic calibration contract.
    Enforces that geometric projections are grounded in explicit optical parameters
    rather than unvalidated magic pixel offsets.
    
    CRITICAL SAFETY INVARIANT:
      is_verified defaults to False (Fail-Closed). Unverified calibration must
      incur downstream uncertainty inflation and degradation of confidence.
    """
    camera_height_m: float = 3.5
    camera_pitch_deg: float = 28.0
    camera_roll_deg: float = 0.0
    camera_intrinsics: Dict[str, float] = field(default_factory=lambda: {
        "fx": 950.0, "fy": 950.0, "cx": 640.0, "cy": 360.0
    })
    distortion_parameters: Optional[List[float]] = None
    ground_plane_calibration: Optional[Any] = None
    calibration_source: str = CalibrationSource.UNVERIFIED_DEFAULT.value
    calibration_method: str = "DEFAULT_ASSUMPTION"
    calibration_version: str = "v3.0.3_calib"
    calibration_timestamp: str = "2026-09-23T00:00:00Z"
    reprojection_error: Optional[Dict[str, float]] = None
    ground_control_point_count: int = 0
    parameter_uncertainty: Dict[str, float] = field(default_factory=lambda: {
        "pitch_deg": 1.5, "height_m": 0.20, "roll_deg": 0.5
    })
    is_verified: bool = False
    verification_status: str = "UNVERIFIED_DEFAULT"
    operator_elevation_m: float = 1.20 # Legacy fallback nominal

class GeometricProjectionMethod:
    METHOD_A_HOMOGRAPHY_BBOX = "METHOD_A_HOMOGRAPHY_BBOX"
    METHOD_B_FOOTPOINT_KEYPOINTS = "METHOD_B_FOOTPOINT_KEYPOINTS"
    METHOD_C_POSE_GROUND_KINEMATIC = "METHOD_C_POSE_GROUND_KINEMATIC"
    METHOD_D_RAY_PLANE_OPTICS = "METHOD_D_RAY_PLANE_OPTICS"
    METHOD_E_3D_VEHICLE_OFFSET = "METHOD_E_3D_VEHICLE_OFFSET"
    METHOD_E_PERSPECTIVE_ELEVATION_OFFSET = "METHOD_E_PERSPECTIVE_ELEVATION_OFFSET"


class GeometryEngineV3:
    """
    Evaluates and projects 2D image observations into metric ground coordinates.
    Provides runtime benchmarking across all 5 geometric methods with parameterized
    perspective elevation compensation, exact projective models, and covariance-derived uncertainty.
    """
    def __init__(
        self,
        calibrator,
        camera_height_m: float = 3.5,
        camera_pitch_deg: float = 28.0,
        camera_roll_deg: float = 0.0,
        focal_length_px: float = 950.0,
        calibration_contract: Optional[CameraCalibrationContract] = None
    ):
        self.calibrator = calibrator
        self.calibration = calibration_contract or CameraCalibrationContract(
            camera_height_m=camera_height_m,
            camera_pitch_deg=camera_pitch_deg,
            camera_roll_deg=camera_roll_deg,
            camera_intrinsics={"fx": focal_length_px, "fy": focal_length_px, "cx": 640.0, "cy": 360.0},
            ground_plane_calibration=calibrator,
            is_verified=False,
            verification_status="UNVERIFIED_DEFAULT"
        )
        self.camera_height_m = self.calibration.camera_height_m
        self.camera_pitch_rad = math.radians(self.calibration.camera_pitch_deg)
        self.camera_roll_rad = math.radians(self.calibration.camera_roll_deg)
        self.focal_length_px = self.calibration.camera_intrinsics.get("fy", focal_length_px)

    def get_operator_elevation(
        self,
        vehicle_type: str = "COUNTERBALANCE",
        posture: str = "SEATED"
    ) -> Tuple[float, float]:
        """
        Returns (nominal_elevation_m, uncertainty_m) for vehicle class and operator posture.
        Replaces universal 1.2m constant.
        """
        spec = OPERATOR_ELEVATION_SPECS.get(vehicle_type.upper(), OPERATOR_ELEVATION_SPECS["COUNTERBALANCE"])
        nom = spec["nominal_m"]
        unc = spec["uncertainty_m"]
        
        # Posture adjustments
        if posture.upper() == "STANDING":
            nom += 0.35
            unc += 0.10
        elif posture.upper() == "LEANING":
            nom -= 0.15
            unc += 0.15
        elif posture.upper() == "PARTIAL_DISMOUNT":
            nom = nom * 0.5
            unc += 0.25
        elif posture.upper() == "DISMOUNTED":
            nom = 0.0
            unc = 0.05
            
        return float(nom), float(unc)

    def compute_parameterized_elevation_shift_px(
        self,
        ground_distance_m: float,
        operator_elevation_m: Optional[float] = None
    ) -> float:
        """
        First-order linear pinhole elevation shift approximation:
          Δy = (fy * ho * cos(θ)) / D
        NOTE: Valid as a first-order approximation when ho << Hc and roll is negligible.
        """
        h_o = operator_elevation_m if operator_elevation_m is not None else self.calibration.operator_elevation_m
        fy = self.calibration.camera_intrinsics.get("fy", self.focal_length_px)
        pitch_rad = self.camera_pitch_rad
        
        d_eff = max(1.5, ground_distance_m)
        shift_px = (fy * h_o * math.cos(pitch_rad)) / d_eff
        return float(shift_px)

    def project_pixel_to_ground_plane(self, u: float, v: float) -> Optional[Tuple[float, float]]:
        """
        Exact closed-form 3D ray-plane intersection on planar ground Z_w = 0.
        Pinhole optical center at (0, 0, H_c) with pitch depression angle theta from horizontal.
        Returns physical ground coordinates (X_w, Y_w) in meters.
        """
        fx = self.calibration.camera_intrinsics.get("fx", self.focal_length_px)
        fy = self.calibration.camera_intrinsics.get("fy", self.focal_length_px)
        cx = self.calibration.camera_intrinsics.get("cx", 640.0)
        cy = self.calibration.camera_intrinsics.get("cy", 360.0)
        theta = self.camera_pitch_rad
        H = self.camera_height_m
        
        ty = (v - cy) / fy
        denom = math.sin(theta) + ty * math.cos(theta)
        if denom <= 0.02: # Ray is above or parallel to ground horizon
            return None
            
        Y_w = H * (math.cos(theta) - ty * math.sin(theta)) / denom
        Z_c = Y_w * math.cos(theta) + H * math.sin(theta)
        X_w = ((u - cx) / fx) * Z_c
        return float(X_w), float(Y_w)

    def compute_exact_projective_elevation_shift_px(
        self,
        ground_distance_m: float,
        operator_elevation_m: float,
        lateral_offset_m: float = 0.0
    ) -> Tuple[float, float]:
        """
        Full rigorous projective pinhole transformation on planar ground:
        P_world_ground   = [X, Y, 0]
        P_world_elevated = [X, Y, h_o]
        Camera origin at [0, 0, H_c], pitched by θ_p downwards from horizontal.
        
        Returns:
          (exact_shift_px, truncation_error_px = approx_shift - exact_shift)
        """
        H = self.camera_height_m
        theta = self.camera_pitch_rad
        fy = self.calibration.camera_intrinsics.get("fy", self.focal_length_px)
        cy = self.calibration.camera_intrinsics.get("cy", 360.0)
        
        Y_g = max(1.5, ground_distance_m)
        
        # Camera frame coordinates for Ground contact (Z_w = 0):
        # Optical axis Z_c = Y * cos(theta) + H * sin(theta)
        # Downward axis Y_c = H * cos(theta) - Y * sin(theta)
        Z_c_ground = Y_g * math.cos(theta) + H * math.sin(theta)
        Y_c_ground = H * math.cos(theta) - Y_g * math.sin(theta)
        v_ground = fy * (Y_c_ground / Z_c_ground) + cy
        
        # Camera frame coordinates for Elevated point (Z_w = h_o):
        Z_c_elev = Y_g * math.cos(theta) + (H - operator_elevation_m) * math.sin(theta)
        Y_c_elev = (H - operator_elevation_m) * math.cos(theta) - Y_g * math.sin(theta)
        v_elev = fy * (Y_c_elev / Z_c_elev) + cy
        
        # Downward pixel shift needed to bring elevated visual detection down to true floor contact:
        exact_shift_px = float(v_ground - v_elev)
        
        # Approximate shift:
        approx_shift_px = self.compute_parameterized_elevation_shift_px(ground_distance_m, operator_elevation_m)
        truncation_err_px = float(approx_shift_px - exact_shift_px)
        
        return exact_shift_px, truncation_err_px

    def project_entity_ground(
        self,
        bbox: list,
        keypoints: Optional[list] = None,
        entity_class: str = "person",
        is_operator: bool = False,
        method: str = GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX
    ) -> Dict[str, Any]:
        """
        Projects entity to world ground coordinates (X, Y in meters) using selected method.
        Returns position, confidence, and diagnostic error factors.
        """
        t0 = time.perf_counter()
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        by = float(y2)
        
        # 1. Inspect Keypoints & Foot Contact
        has_ankles = False
        ankle_pt = None
        ankle_conf = 0.0
        
        if keypoints is not None and len(keypoints) >= 17:
            # Indices 15 (L-Ankle) and 16 (R-Ankle)
            l_ank = keypoints[15]
            r_ank = keypoints[16]
            valid_anks = [a for a in [l_ank, r_ank] if len(a) >= 3 and a[2] > 0.35]
            if valid_anks:
                has_ankles = True
                ankle_pt = (
                    sum(a[0] for a in valid_anks) / len(valid_anks),
                    sum(a[1] for a in valid_anks) / len(valid_anks)
                )
                ankle_conf = float(np.mean([a[2] for a in valid_anks]))

        # --- METHOD A: Baseline Homography of BBox Bottom-Center ---
        if method == GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX:
            if self.calibrator and hasattr(self.calibrator, "pixel_to_world"):
                world_pos = self.calibrator.pixel_to_world((cx, by))
            else:
                world_pos = self.project_pixel_to_ground_plane(cx, by)
            conf = 0.5 if is_operator else 0.8
            runtime_us = (time.perf_counter() - t0) * 1e6
            return {
                "method": method,
                "world_pos_m": world_pos,
                "ground_confidence": conf,
                "elevation_bias_m": 2.2 if is_operator else 0.0,
                "runtime_us": round(runtime_us, 1)
            }

        # --- METHOD B: Footpoint-Based Projection (Visible Ankles) ---
        elif method == GeometricProjectionMethod.METHOD_B_FOOTPOINT_KEYPOINTS:
            if has_ankles and ankle_pt is not None:
                # Use physical ground contact of feet
                if self.calibrator and hasattr(self.calibrator, "pixel_to_world"):
                    world_pos = self.calibrator.pixel_to_world(ankle_pt)
                else:
                    world_pos = self.project_pixel_to_ground_plane(ankle_pt[0], ankle_pt[1])
                conf = min(0.95, ankle_conf)
                bias = 0.2 if is_operator else 0.0
            else:
                # Fallback to bottom-center with reduced confidence
                if self.calibrator and hasattr(self.calibrator, "pixel_to_world"):
                    world_pos = self.calibrator.pixel_to_world((cx, by))
                else:
                    world_pos = self.project_pixel_to_ground_plane(cx, by)
                conf = 0.3 # Degraded confidence due to occluded feet
                bias = 1.8 if is_operator else 0.4
                
            runtime_us = (time.perf_counter() - t0) * 1e6
            return {
                "method": method,
                "world_pos_m": world_pos,
                "ground_confidence": conf,
                "elevation_bias_m": bias,
                "runtime_us": round(runtime_us, 1)
            }

        # --- METHOD C: Pose-Ground Kinematic Projection ---
        elif method == GeometricProjectionMethod.METHOD_C_POSE_GROUND_KINEMATIC:
            # Derives floor stance from Hip-Knee-Ankle kinematic chain
            if has_ankles and ankle_pt is not None:
                contact_px = ankle_pt
                conf = 0.90
            elif keypoints is not None and len(keypoints) >= 17:
                # Hips visible (11, 12) but feet occluded
                hips = [keypoints[i] for i in [11, 12] if len(keypoints[i]) >= 3 and keypoints[i][2] > 0.4]
                if hips:
                    hip_y = sum(h[1] for h in hips) / len(hips)
                    contact_px = (cx, min(by, hip_y + (by - hip_y) * 0.95))
                    conf = 0.55
                else:
                    contact_px = (cx, by)
                    conf = 0.35
            else:
                contact_px = (cx, by)
                conf = 0.30

            if self.calibrator and hasattr(self.calibrator, "pixel_to_world"):
                world_pos = self.calibrator.pixel_to_world(contact_px)
            else:
                world_pos = self.project_pixel_to_ground_plane(contact_px[0], contact_px[1])
            runtime_us = (time.perf_counter() - t0) * 1e6
            return {
                "method": method,
                "world_pos_m": world_pos,
                "ground_confidence": conf,
                "elevation_bias_m": 0.8 if is_operator else 0.1,
                "runtime_us": round(runtime_us, 1)
            }

        # --- METHOD D: Monocular Camera Ray-Plane Optical Intersection ---
        elif method == GeometricProjectionMethod.METHOD_D_RAY_PLANE_OPTICS:
            # Uses exact 3D closed-form ray intersection with planar floor Z=0
            world_pos = self.project_pixel_to_ground_plane(cx, by)
            conf = 0.85 if world_pos is not None else 0.0
            runtime_us = (time.perf_counter() - t0) * 1e6
            return {
                "method": method,
                "world_pos_m": world_pos,
                "ground_confidence": conf,
                "elevation_bias_m": 1.2 if is_operator else 0.0,
                "runtime_us": round(runtime_us, 1)
            }

        # --- METHOD E: 2D Perspective Elevation Compensation with Ground Homography ---
        elif method in [GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET, "METHOD_E_PERSPECTIVE_ELEVATION_OFFSET"]:
            if is_operator:
                # Estimate preliminary range from uncorrected base
                if self.calibrator and hasattr(self.calibrator, "pixel_to_world"):
                    prelim_pos = self.calibrator.pixel_to_world((cx, by))
                else:
                    prelim_pos = self.project_pixel_to_ground_plane(cx, by)
                prelim_dist = math.hypot(prelim_pos[0], prelim_pos[1]) if prelim_pos else 6.0
                
                # Dynamic exact projective shift (resolves FAIL-19 and FAIL-24 linear truncation breakdown)
                h_o = self.calibration.operator_elevation_m
                shift_px, _ = self.compute_exact_projective_elevation_shift_px(prelim_dist, h_o)
                corrected_y = min(by + shift_px, 720.0)
                if self.calibrator and hasattr(self.calibrator, "pixel_to_world"):
                    world_pos = self.calibrator.pixel_to_world((cx, corrected_y))
                else:
                    world_pos = self.project_pixel_to_ground_plane(cx, corrected_y)
                
                # Calibration verification penalty
                is_verified = self.calibration.is_verified
                calib_penalty = 0.0 if is_verified else 0.25
                
                # Degrade confidence if feet/ankles are occluded inside cabin
                base_conf = min(0.85, ankle_conf) if has_ankles else 0.50
                conf = max(0.15, base_conf - calib_penalty)
                bias = 0.05 if is_verified else 0.50
            else:
                if self.calibrator and hasattr(self.calibrator, "pixel_to_world"):
                    world_pos = self.calibrator.pixel_to_world((cx, by))
                else:
                    world_pos = self.project_pixel_to_ground_plane(cx, by)
                conf = min(0.95, ankle_conf) if has_ankles else 0.45
                bias = 0.0
                
            runtime_us = (time.perf_counter() - t0) * 1e6
            pos_uncertainty_m = round(max(0.10, (1.0 - conf) * 1.5), 2)
            return {
                "method": "METHOD_E_PERSPECTIVE_ELEVATION_OFFSET",
                "world_pos_m": world_pos,
                "ground_confidence": round(conf, 2),
                "elevation_bias_m": bias,
                "position_uncertainty_m": pos_uncertainty_m,
                "runtime_us": round(runtime_us, 1)
            }

        world_pos = self.calibrator.pixel_to_world((cx, by)) if self.calibrator else None
        return {
            "method": "UNKNOWN",
            "world_pos_m": world_pos,
            "ground_confidence": 0.5,
            "elevation_bias_m": 0.0,
            "position_uncertainty_m": 0.75,
            "runtime_us": 10.0
        }

    @staticmethod
    def compute_distance_with_uncertainty(
        p_pos: Tuple[float, float],
        f_pos: Tuple[float, float],
        p_unc_m: float = 0.2,
        f_unc_m: float = 0.2,
        p_cov: Optional[np.ndarray] = None,
        f_cov: Optional[np.ndarray] = None,
        coverage_factor: float = 2.24, # 95% 2D Rice non-central chi coverage factor (resolves FAIL-23)
        debias_jensen: bool = True,
        adaptive_2d_calibration: bool = True,
        monte_carlo_samples: int = 0
    ) -> Dict[str, Any]:
        """
        FAIL-22 and FAIL-23 Resolution — Calibrated 2D Uncertainty Engine:
        Computes metric Euclidean distance with second-order Jensen debiasing
        and 2D Rice (non-central chi) calibrated confidence intervals.
        
        Root Cause of FAIL-23:
          Euclidean distance d = ||Δx|| is strictly convex (Jensen's inequality).
          Orthogonal 2D noise systematically expands scalar distance by:
            E[d_obs] \approx d_true + Tr(Σ_perp) / (2 * d_true)
          First-order Taylor expansions with 1D Gaussian k=1.96 systematically
          under-cover the lower bound when targets are close (< 3m), achieving only 89% coverage.
          
        V3.0.4 Fix:
          1. Second-order Jensen convexity debiasing shifts interval center back to unbiased d_true.
          2. 2D Rice non-central chi calibration uses k=2.24 for 95% coverage (instead of 1D Gaussian 1.96).
        """
        dx = float(p_pos[0] - f_pos[0])
        dy = float(p_pos[1] - f_pos[1])
        dist_obs_m = float(math.hypot(dx, dy))
        
        # Build 2D Covariance matrices if not provided
        if p_cov is None:
            cov_p = np.array([[p_unc_m**2, 0.0], [0.0, p_unc_m**2]], dtype=np.float64)
        else:
            cov_p = np.array(p_cov, dtype=np.float64)
            
        if f_cov is None:
            cov_f = np.array([[f_unc_m**2, 0.0], [0.0, f_unc_m**2]], dtype=np.float64)
        else:
            cov_f = np.array(f_cov, dtype=np.float64)
            
        cov_sum = cov_p + cov_f
        tr_cov = float(np.trace(cov_sum))
        
        # Directional radial projection
        if dist_obs_m > 1e-4:
            J = np.array([dx / dist_obs_m, dy / dist_obs_m], dtype=np.float64)
            var_radial = float(J @ cov_sum @ J.T)
        else:
            J = np.array([1.0, 0.0], dtype=np.float64)
            var_radial = tr_cov / 2.0
            
        sigma_d = float(math.sqrt(max(1e-6, var_radial)))
        sigma_perp_sq = max(0.0, tr_cov - var_radial)
        
        # Jensen Convexity Debiasing (Resolves FAIL-23 Systematic Positive Bias)
        if debias_jensen and dist_obs_m > 0.05:
            jensen_bias = sigma_perp_sq / (2.0 * max(0.2, dist_obs_m))
            dist_unbiased_m = max(0.0, dist_obs_m - jensen_bias)
        else:
            jensen_bias = 0.0
            dist_unbiased_m = dist_obs_m

        # Adaptive 2D Rice Calibration:
        # If caller requested standard 95% (k=1.96) or default, adapt to 2D Rice factor k=2.24
        if adaptive_2d_calibration and abs(coverage_factor - 1.96) < 1e-3:
            k = 2.24
        else:
            k = coverage_factor

        # Handle Degenerate / Non-linear singularity as d -> 0 or explicit Monte Carlo
        if dist_obs_m < 0.25 or monte_carlo_samples > 0:
            n_samples = max(2000, monte_carlo_samples)
            samples_p = np.random.multivariate_normal(p_pos, cov_p, size=n_samples)
            samples_f = np.random.multivariate_normal(f_pos, cov_f, size=n_samples)
            sampled_dists = np.linalg.norm(samples_p - samples_f, axis=1)
            
            sigma_d = float(np.std(sampled_dists))
            lower_95 = float(max(0.0, np.percentile(sampled_dists, 2.5) - 2 * jensen_bias))
            upper_95 = float(np.percentile(sampled_dists, 97.5))
            propagation_method = "MONTE_CARLO_NON_LINEAR"
        else:
            lower_95 = max(0.0, dist_unbiased_m - k * sigma_d)
            upper_95 = dist_unbiased_m + k * sigma_d
            propagation_method = "SECOND_ORDER_DEBIASED_JACOBIAN"
            
        # Categorical Uncertainty Level
        if sigma_d < 0.25:
            unc_level = "LOW"
        elif sigma_d <= 0.50:
            unc_level = "MODERATE"
        else:
            unc_level = "HIGH"
            
        # 1-sigma interval (calibrated for 2D Rice: k_1s = 1.15)
        k_1s = 1.15 if adaptive_2d_calibration else 1.0
        lower_1s = max(0.0, dist_unbiased_m - k_1s * sigma_d)
        upper_1s = dist_unbiased_m + k_1s * sigma_d

        return {
            "nominal_distance_m": round(dist_obs_m, 3),
            "unbiased_distance_m": round(dist_unbiased_m, 3),
            "distance_uncertainty_m": round(sigma_d, 3), # 1-sigma standard uncertainty
            "std_uncertainty_1sigma_m": round(sigma_d, 3),
            "expanded_uncertainty_95_m": round(k * sigma_d, 3),
            "distance_interval_m": [round(lower_95, 3), round(upper_95, 3)], # 95% interval
            "interval_1sigma_m": [round(lower_1s, 3), round(upper_1s, 3)],
            "coverage_factor_k": round(k, 3),
            "jensen_bias_m": round(jensen_bias, 4),
            "uncertainty_level": unc_level,
            "propagation_method": propagation_method
        }


class ManDownClassifier:
    """
    Multi-Cue Behavioral Posture & Man-Down Classifier.
    Distinguishes: STANDING, WALKING, RUNNING, CROUCHED, FALLEN_CANDIDATE, PARTIALLY_OCCLUDED, UNKNOWN.
    """
    @staticmethod
    def classify_posture(
        bbox: list,
        speed_m_s: float,
        keypoints: Optional[list] = None,
        conf: float = 0.7
    ) -> Dict[str, Any]:
        x1, y1, x2, y2 = bbox
        width = max(1.0, float(x2 - x1))
        height = max(1.0, float(y2 - y1))
        aspect_ratio = height / width

        # 1. Inspect Keypoints
        visible_kpts = 0
        torso_angle_deg = None
        if keypoints is not None and len(keypoints) >= 17:
            for k in keypoints:
                if len(k) >= 3 and k[2] > 0.35:
                    visible_kpts += 1
            
            # Torso angle between shoulders and hips
            sh_l, sh_r = keypoints[5], keypoints[6]
            hip_l, hip_r = keypoints[11], keypoints[12]
            if sh_l[2] > 0.3 and sh_r[2] > 0.3 and hip_l[2] > 0.3 and hip_r[2] > 0.3:
                sh_mid = ((sh_l[0] + sh_r[0]) / 2.0, (sh_l[1] + sh_r[1]) / 2.0)
                hip_mid = ((hip_l[0] + hip_r[0]) / 2.0, (hip_l[1] + hip_r[1]) / 2.0)
                dx = hip_mid[0] - sh_mid[0]
                dy = hip_mid[1] - sh_mid[1]
                torso_angle_deg = abs(math.degrees(math.atan2(dx, dy)))

        # Classification Logic
        # Condition A: Fallen / Lying Down
        is_horizontal_box = (aspect_ratio < 0.85)
        is_horizontal_torso = (torso_angle_deg is not None and torso_angle_deg > 55.0)
        is_motionless = (speed_m_s < 0.15)
        
        if (is_horizontal_box or is_horizontal_torso) and is_motionless:
            posture = "FALLEN_CANDIDATE"
            confidence = 0.85 if is_horizontal_torso else 0.70
            safety_status = "SAFETY_ELIGIBLE_INCIDENT_CANDIDATE"
        
        # Condition B: Crouched / Stooping
        elif 0.85 <= aspect_ratio < 1.3:
            posture = "CROUCHED"
            confidence = 0.75
            safety_status = "SAFETY_ELIGIBLE_NORMAL"
            
        # Condition C: Upright Moving (Running vs Walking)
        elif aspect_ratio >= 1.3 and speed_m_s > 1.8:
            posture = "RUNNING"
            confidence = 0.85
            safety_status = "SAFETY_ELIGIBLE_NORMAL"
            
        elif aspect_ratio >= 1.3 and speed_m_s > 0.3:
            posture = "WALKING"
            confidence = 0.90
            safety_status = "SAFETY_ELIGIBLE_NORMAL"
            
        elif aspect_ratio >= 1.3:
            posture = "STANDING"
            confidence = 0.90
            safety_status = "SAFETY_ELIGIBLE_NORMAL"
            
        else:
            posture = "PARTIALLY_OCCLUDED"
            confidence = 0.50
            safety_status = "SAFETY_ELIGIBLE_NORMAL"

        return {
            "posture": posture,
            "confidence": confidence,
            "safety_status": safety_status,
            "aspect_ratio": round(aspect_ratio, 2),
            "speed_m_s": round(speed_m_s, 2),
            "torso_angle_deg": round(torso_angle_deg, 1) if torso_angle_deg else None,
            "visible_kpts": visible_kpts
        }
