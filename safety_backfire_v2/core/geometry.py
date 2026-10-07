"""
Phase 3 — Metric Geometry & Ground Plane  (V2.3 update)

Changes from V2.2:
  - GroundPlaneCalibrator can be loaded from external JSON calibration artifact
  - Removed hardcoded 100px margin from calibration bounds
  - Bounds now use the CONVEX HULL of calibration points (not bbox + margin)
  - Added calibration_margin_px as a separate, configurable safety parameter
    that is NOT used to assert geometric validity — it is informational only
  - Added calibration_confidence_level (INSIDE / EDGE / OUTSIDE)
  - Measurement source is propagated from calibration artifact
"""
import math
import json
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import cv2
import numpy as np


class GroundPlaneCalibrator:
    def __init__(
        self,
        src_pts: Optional[np.ndarray] = None,
        dst_pts: Optional[np.ndarray] = None,
        calibration_artifact: Optional[dict] = None,
        edge_margin_px: float = 30.0,        # informational edge zone (not validity criterion)
    ):
        """
        Initialise calibrator.

        Priority:
          1. calibration_artifact (loaded from config/calibration/*.json)
          2. src_pts / dst_pts (explicit numpy arrays)
          3. Hardcoded V2.1 defaults (fallback — kept for backwards compatibility)

        edge_margin_px: pixels beyond the convex hull to classify as EDGE_REGION.
                        Does NOT extend geometric validity.
        """
        self.measurement_source = "UNKNOWN"
        self.calibration_status = "UNKNOWN"
        self.edge_margin_px = edge_margin_px

        if calibration_artifact is not None:
            # Load from pre-computed artifact
            self.src_pts = np.float32(calibration_artifact["src_pts"])
            self.dst_pts = np.float32(calibration_artifact["dst_pts"])
            H_flat = calibration_artifact["homography"]
            self.H = np.array(H_flat, dtype=np.float64).reshape(3, 3)
            self.measurement_source = calibration_artifact.get("measurement_source", "UNKNOWN")
            self.calibration_status = calibration_artifact.get("calibration_status", "UNKNOWN")
            hull_pts = calibration_artifact.get("calibration_hull_px")
            if hull_pts:
                self.calib_hull = np.array(hull_pts, dtype=np.int32)
            else:
                self.calib_hull = cv2.convexHull(self.src_pts.astype(np.int32)).reshape(-1, 2)

        elif src_pts is not None:
            self.src_pts = np.float32(src_pts)
            self.dst_pts = np.float32(dst_pts)
            self.H, _ = cv2.findHomography(self.src_pts, self.dst_pts)
            self.measurement_source = "EXPLICIT_PARAMETER"
            self.calibration_status = "UNVALIDATED"
            self.calib_hull = cv2.convexHull(self.src_pts.astype(np.int32)).reshape(-1, 2)

        else:
            # V2.1 defaults — kept for backwards compatibility and synthetic tests
            self.src_pts = np.float32([
                [210.0, 180.0], [340.0, 180.0],
                [150.0, 340.0], [430.0, 340.0],
            ])
            self.dst_pts = np.float32([
                [0.0, 6.0], [3.5, 6.0],
                [0.0, 0.0], [3.5, 0.0],
            ])
            self.H, _ = cv2.findHomography(self.src_pts, self.dst_pts)
            self.measurement_source = "HARDCODED_DEFAULT_V2_1"
            self.calibration_status = "UNVALIDATED_DEFAULT"
            self.calib_hull = cv2.convexHull(self.src_pts.astype(np.int32)).reshape(-1, 2)

        self.H_inv = np.linalg.inv(self.H) if self.H is not None else None

        # Legacy bbox bounds — kept so that old code using calib_x_min still compiles
        # but is_in_calibrated_region() now uses hull, not bbox
        if self.src_pts is not None:
            self.calib_x_min = float(np.min(self.src_pts[:, 0]))
            self.calib_x_max = float(np.max(self.src_pts[:, 0]))
            self.calib_y_min = float(np.min(self.src_pts[:, 1]))
            self.calib_y_max = float(np.max(self.src_pts[:, 1]))

    @classmethod
    def from_json(cls, artifact_path: str, edge_margin_px: float = 30.0) -> "GroundPlaneCalibrator":
        """Load calibrator from a JSON calibration artifact file."""
        with open(artifact_path) as f:
            artifact = json.load(f)
        return cls(calibration_artifact=artifact, edge_margin_px=edge_margin_px)

    def pixel_to_world(self, pt: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        if self.H is None:
            return None
        p = np.array([[[pt[0], pt[1]]]], dtype=np.float32)
        w = cv2.perspectiveTransform(p, self.H)
        return float(w[0][0][0]), float(w[0][0][1])

    def get_spatial_zone(self, pt: Tuple[float, float]) -> str:
        """
        Returns spatial zone for a pixel point:
          INSIDE_CALIBRATION — within convex hull of calibration points
          EDGE_REGION        — within edge_margin_px outside hull
          OUTSIDE_CALIBRATION — beyond edge region
        """
        hull_pts = self.calib_hull.reshape((-1, 1, 2)).astype(np.int32)
        dist = cv2.pointPolygonTest(hull_pts, (float(pt[0]), float(pt[1])), True)
        if dist >= 0:
            return "INSIDE_CALIBRATION"
        elif dist >= -self.edge_margin_px:
            return "EDGE_REGION"
        else:
            return "OUTSIDE_CALIBRATION"

    def is_in_calibrated_region(self, pt: Tuple[float, float]) -> bool:
        """
        Returns True only if point is INSIDE the convex hull of calibration points.
        EDGE_REGION and OUTSIDE are both False.
        
        V2.3 change: no longer uses bbox + 100px margin.
                     Uses actual convex hull of src_pts.
        """
        zone = self.get_spatial_zone(pt)
        return zone == "INSIDE_CALIBRATION"

    def compute_world_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> Optional[float]:
        w1 = self.pixel_to_world(p1)
        w2 = self.pixel_to_world(p2)
        if w1 is None or w2 is None:
            return None
        return math.hypot(w2[0] - w1[0], w2[1] - w1[1])


def load_default_calibrator(prefer_v23: bool = True) -> GroundPlaneCalibrator:
    """
    Load calibrator: prefers V2.3 artifact if available, falls back to V2.1 defaults.
    """
    artifact_path = Path(__file__).resolve().parent.parent / "config/calibration/warehouse_test2.json"
    if prefer_v23 and artifact_path.exists():
        cal = GroundPlaneCalibrator.from_json(str(artifact_path))
        return cal
    return GroundPlaneCalibrator()  # V2.1 defaults


# Module-level default — V2.3 will use wider calibration if artifact exists
DEFAULT_CALIBRATOR = load_default_calibrator()


def get_footprint(bbox: List[int]) -> Tuple[float, float]:
    """Computes the ground contact footprint (bottom-center) of a bounding box."""
    x1, y1, x2, y2 = bbox
    return float((x1 + x2) / 2.0), float(y2)


def compute_metric_distance(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    calibrator: GroundPlaneCalibrator = None
) -> Dict[str, Any]:
    """
    Computes distance and returns a structured object indicating calibration status.
    V2.3: uses convex hull containment instead of bbox + 100px margin.
    """
    if calibrator is None:
        calibrator = DEFAULT_CALIBRATOR

    distance_px = math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    zone1 = calibrator.get_spatial_zone(p1)
    zone2 = calibrator.get_spatial_zone(p2)

    p1_valid = zone1 == "INSIDE_CALIBRATION"
    p2_valid = zone2 == "INSIDE_CALIBRATION"

    status = "VALID"
    confidence = 1.0
    distance_m = None

    if not (p1_valid and p2_valid):
        # Determine most informative status
        if zone1 == "OUTSIDE_CALIBRATION" or zone2 == "OUTSIDE_CALIBRATION":
            status = "EXTRAPOLATED_OUT_OF_BOUNDS"
        else:
            status = "EDGE_REGION_LOW_CONFIDENCE"
        confidence = 0.0
    elif calibrator.H is None:
        status = "INVALID_HOMOGRAPHY"
        confidence = 0.0
    else:
        dist = calibrator.compute_world_distance(p1, p2)
        if dist is not None:
            distance_m = round(dist, 3)
        else:
            status = "TRANSFORM_FAILED"
            confidence = 0.0

    return {
        "distance_px": round(distance_px, 1),
        "distance_m": distance_m,
        "calibration_status": status,
        "calibration_confidence": confidence,
        "measurement_source": calibrator.measurement_source,
        "zone_p1": zone1,
        "zone_p2": zone2,
    }
