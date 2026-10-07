"""
Geometry module for Safety Backfire AI V0.8.
Handles:
- Ground footprint projection (bottom-center of bounding boxes).
- Euclidean distance calculation on the ground plane.
- Perspective compensation for high-angle warehouse CCTV cameras.
"""
import math
from typing import Tuple, List, Optional
import cv2
import numpy as np

class GroundPlaneCalibrator:
    """
    Planar Homography Calibrator for Warehouse Floor CCTV.
    Maps 2D pixel coordinates (u, v) on the camera image plane to
    physical world ground coordinates (X, Y) in meters.

    Calibrated on the warehouse driving aisle concrete slab geometry:
    - Image points (src):
      Top-left (far aisle): (210, 180)
      Top-right (far aisle): (340, 180)
      Bottom-left (near foreground): (150, 340)
      Bottom-right (near foreground): (430, 340)
    - World points (dst):
      Standard driving aisle width = 3.5 meters
      Slab length = 6.0 meters
      Top-left: (0.0, 6.0)
      Top-right: (3.5, 6.0)
      Bottom-left: (0.0, 0.0)
      Bottom-right: (3.5, 0.0)
    """
    def __init__(
        self,
        src_pts: Optional[np.ndarray] = None,
        dst_pts: Optional[np.ndarray] = None,
    ):
        if src_pts is None:
            self.src_pts = np.float32([
                [210.0, 180.0],
                [340.0, 180.0],
                [150.0, 340.0],
                [430.0, 340.0],
            ])
        else:
            self.src_pts = np.float32(src_pts)

        if dst_pts is None:
            self.dst_pts = np.float32([
                [0.0, 6.0],
                [3.5, 6.0],
                [0.0, 0.0],
                [3.5, 0.0],
            ])
        else:
            self.dst_pts = np.float32(dst_pts)

        self.H, _ = cv2.findHomography(self.src_pts, self.dst_pts)
        self.H_inv = np.linalg.inv(self.H) if self.H is not None else None

    def pixel_to_world(self, pt: Tuple[float, float]) -> Tuple[float, float]:
        """Maps an image pixel point (x, y) to world ground coordinates (X, Y) in meters."""
        p = np.array([[[pt[0], pt[1]]]], dtype=np.float32)
        w = cv2.perspectiveTransform(p, self.H)
        return float(w[0][0][0]), float(w[0][0][1])

    def world_to_pixel(self, pt: Tuple[float, float]) -> Tuple[float, float]:
        """Maps world ground coordinates (X, Y) in meters back to image pixel (x, y)."""
        if self.H_inv is None:
            return pt
        p = np.array([[[pt[0], pt[1]]]], dtype=np.float32)
        px = cv2.perspectiveTransform(p, self.H_inv)
        return float(px[0][0][0]), float(px[0][0][1])

    def compute_world_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Computes Euclidean planar distance in meters between two pixel footprints."""
        w1 = self.pixel_to_world(p1)
        w2 = self.pixel_to_world(p2)
        dist = math.hypot(w2[0] - w1[0], w2[1] - w1[1])
        return round(dist, 2)

# Global default calibrator instance
DEFAULT_CALIBRATOR = GroundPlaneCalibrator()

# Bounding box of the calibrated region (with a small margin)
_CALIB_X_MIN = 130.0  # src_pts min x - margin
_CALIB_X_MAX = 450.0  # src_pts max x + margin
_CALIB_Y_MIN = 160.0  # src_pts min y - margin
_CALIB_Y_MAX = 360.0  # src_pts max y + margin

def _is_in_calibrated_region(pt: Tuple[float, float]) -> bool:
    """Returns True if pixel point is within the valid homography calibration zone."""
    return (_CALIB_X_MIN <= pt[0] <= _CALIB_X_MAX and
            _CALIB_Y_MIN <= pt[1] <= _CALIB_Y_MAX)

def get_footprint(bbox: List[int]) -> Tuple[float, float]:
    """
    Computes the ground contact footprint (bottom-center) of a bounding box.
    bbox format: [x1, y1, x2, y2]
    """
    x1, y1, x2, y2 = bbox
    foot_x = float((x1 + x2) / 2.0)
    foot_y = float(y2)
    return (foot_x, foot_y)

def compute_euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Computes Euclidean distance in pixels between two ground points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def estimate_metric_distance(
    px_dist: float,
    y_avg: float,
    p1: Optional[Tuple[float, float]] = None,
    p2: Optional[Tuple[float, float]] = None,
    img_height: int = 360,
) -> float:
    """
    Approximates physical distance in meters.
    If footprint points p1 and p2 are provided AND both lie within the calibrated
    homography region, computes exact planar distance via 4-point Homography.
    Otherwise, uses the calibrated perspective scaling formula to avoid extrapolation.
    """
    if p1 is not None and p2 is not None:
        if _is_in_calibrated_region(p1) and _is_in_calibrated_region(p2):
            return DEFAULT_CALIBRATOR.compute_world_distance(p1, p2)
        # Fallback: use the midpoint y for perspective scaling
        y_avg = (p1[1] + p2[1]) / 2.0

    normalized_y = max(0.1, min(1.0, y_avg / float(img_height)))
    px_per_meter = 18.0 + 26.0 * normalized_y
    meters = px_dist / px_per_meter
    return round(meters, 2)

