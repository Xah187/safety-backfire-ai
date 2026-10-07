"""
geometry/classifier.py
V3.3 Ground Geometry & Planarity Classification Module.
Categorizes surface into PLANAR_VALID, PLANAR_DEGRADED, and NON_PLANAR_REFUSAL.
"""

from typing import Dict, Any, List
from enum import Enum

class GeometryState(str, Enum):
    PLANAR_VALID = "PLANAR_VALID"
    PLANAR_DEGRADED = "PLANAR_DEGRADED"
    NON_PLANAR_REFUSAL = "NON_PLANAR_REFUSAL"

class GroundGeometryClassifier:
    def __init__(self,
                 max_planar_slope_deg: float = 1.5,
                 max_degraded_slope_deg: float = 3.0,
                 max_reprojection_residual_m: float = 0.05):
        self.max_planar_slope_deg = max_planar_slope_deg
        self.max_degraded_slope_deg = max_degraded_slope_deg
        self.max_reprojection_residual_m = max_reprojection_residual_m

    def classify_surface(self,
                         slope_deg: float,
                         reprojection_residual_m: float,
                         distance_m: float) -> Dict[str, Any]:
        """
        Classifies local floor geometry and determines safe operational state.
        Slope < 1.5 deg & residual <= 0.05m -> PLANAR_VALID
        Slope 1.5-3.0 deg OR distance 8-10m -> PLANAR_DEGRADED
        Slope > 3.0 deg OR residual > 0.08m -> NON_PLANAR_REFUSAL
        """
        reasons = []

        if slope_deg > self.max_degraded_slope_deg:
            state = GeometryState.NON_PLANAR_REFUSAL
            reasons.append(f"Floor incline ({slope_deg:.1f} deg) exceeds maximum tolerance (3.0 deg) - homography projection invalid.")
        elif reprojection_residual_m > (self.max_reprojection_residual_m * 1.6):
            state = GeometryState.NON_PLANAR_REFUSAL
            reasons.append(f"Homography reprojection residual ({reprojection_residual_m:.3f}m) indicates non-planar surface warping.")
        elif slope_deg > self.max_planar_slope_deg or distance_m > 8.0:
            state = GeometryState.PLANAR_DEGRADED
            if slope_deg > self.max_planar_slope_deg:
                reasons.append(f"Mild slope ({slope_deg:.1f} deg) causes coordinate dilution.")
            if distance_m > 8.0:
                reasons.append(f"Distance ({distance_m:.1f}m) exceeds 8.0m nominal ray boundary.")
        else:
            state = GeometryState.PLANAR_VALID
            reasons.append("Planar concrete within nominal ODD bounds.")

        return {
            "geometry_state": state.value,
            "slope_deg": slope_deg,
            "residual_m": reprojection_residual_m,
            "distance_m": distance_m,
            "autonomous_braking_permitted": state == GeometryState.PLANAR_VALID,
            "reasons": reasons
        }
