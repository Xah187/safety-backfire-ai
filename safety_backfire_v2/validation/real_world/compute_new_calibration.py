"""
V2.3 — Phase 3/4/5: Compute New Wide-Coverage Homography

Since no physical measurements are available, this tool:
1. Uses the actual detection footpoint extent from V2.3 scan
2. Defines 8 visually-estimated calibration points covering the full floor
3. Computes a new homography from these wider points
4. Documents measurement_source as "VISUAL_ESTIMATION" (NOT physically validated)
5. Computes reprojection error
6. Saves calibration artifact to config/calibration/warehouse_test2.json

CRITICAL SCIENTIFIC NOTE:
  This calibration is VISUALLY_ESTIMATED, NOT PHYSICALLY_MEASURED.
  Metric distances computed from it are approximate only.
  The calibration_status = "VISUALLY_ESTIMATED_NOT_VALIDATED"
  until physical measurements are provided.
"""
import sys
import json
import math
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))


# ═══════════════════════════════════════════════════════════════════════════
# DATA ENTRY: Calibration Points
#
# From the V2.2/V2.3 footpoint scan of test2.mp4:
#   Video size: 1274 x 720 px
#   Detections span: X=[28,1246]  Y=[217,720]
#
# The scene is a warehouse/factory floor with a clear aisle.
# We place 8 calibration points covering the full visible floor area.
#
# Point selection strategy (Phase 4 — Point Distribution):
#   Using the visible floor area from frame analysis.
#   The floor appears as a perspective-foreshortened rectangle.
#   We estimate pixel coordinates from visual inspection of reference frames.
#
# World coordinate assignment:
#   Origin (0,0) = bottom-left of the visible floor area
#   X-axis = left-right (width)
#   Y-axis = near-far (depth, 0=foreground, increases into scene)
#
# MEASUREMENT_SOURCE: VISUAL_ESTIMATION
#   These world_x, world_y values are ESTIMATES based on:
#   - Typical warehouse aisle width (3-6m)
#   - Forklift dimensions (~2.5m wide body)
#   - Relative pixel positions scaled to assumed floor dimensions
#   NOT verified with tape measure or surveying equipment.
# ═══════════════════════════════════════════════════════════════════════════

# Scene analysis from frames:
# - Frame 200 (interaction zone): Person visible at ~x=753, y=248 (this was OUTSIDE old calibration)
# - The floor extends from y≈220 (far background) to y=720 (bottom of frame)
# - Horizontal span: x≈0 to x≈1274

# Estimated floor width: ~8m (typical warehouse aisle for forklift)
# Estimated floor depth: ~10m (depth of scene)
ASSUMED_FLOOR_WIDTH_M = 8.0
ASSUMED_FLOOR_DEPTH_M = 10.0

# 8 calibration points — wide coverage across the full visible floor
# Format: (pixel_x, pixel_y, world_x_m, world_y_m, zone_label)
RAW_CALIBRATION_POINTS = [
    # Foreground row (near camera, y_pixel ≈ 680-720)
    (120,  700, 0.0, 0.0, "foreground_left"),
    (640,  700, 4.0, 0.0, "foreground_center"),
    (1150, 700, 8.0, 0.0, "foreground_right"),

    # Mid-foreground row (y_pixel ≈ 530-570)
    (100,  550, 0.5, 3.0, "mid_left"),
    (637,  550, 4.0, 3.0, "mid_center"),
    (1170, 550, 7.5, 3.0, "mid_right"),

    # Background row (y_pixel ≈ 300-350)
    (200,  320, 1.5, 7.0, "background_left"),
    (750,  300, 4.5, 7.5, "background_center"),
    (1100, 320, 7.0, 7.0, "background_right"),

    # Far background (y_pixel ≈ 220-250) — where person was detected at y=248
    (400,  240, 3.0, 9.5, "far_background_left"),
    (760,  235, 4.5, 10.0,"far_background_center"),
]


def compute_homography_robust(points: list):
    """
    Compute homography from multiple calibration points.
    If > 4 points available, uses RANSAC for robustness.
    Returns H, inlier_mask, reprojection_errors.
    """
    src = np.float32([[p[0], p[1]] for p in points])
    dst = np.float32([[p[2], p[3]] for p in points])

    if len(points) >= 8:
        H, mask = cv2.findHomography(src, dst, cv2.RANSAC, ransacReprojThreshold=0.5)
    elif len(points) >= 4:
        H, mask = cv2.findHomography(src, dst, 0)
        mask = np.ones(len(points), dtype=np.uint8).reshape(-1,1)
    else:
        return None, None, None

    return H, mask, src, dst


def compute_reprojection_errors(H, src_pts, dst_pts_gt):
    """
    For each control point, project src → world and compare to gt world coords.
    Returns per-point errors and aggregate metrics.
    """
    errors = []
    for i in range(len(src_pts)):
        px, py = src_pts[i]
        p = np.array([[[float(px), float(py)]]], dtype=np.float32)
        w = cv2.perspectiveTransform(p, H)
        wx, wy = float(w[0,0,0]), float(w[0,0,1])
        gx, gy = float(dst_pts_gt[i,0]), float(dst_pts_gt[i,1])
        err = math.hypot(wx - gx, wy - gy)
        errors.append({
            "point_id": i,
            "pixel": [round(px,1), round(py,1)],
            "estimated_world": [round(wx,3), round(wy,3)],
            "gt_world": [round(gx,3), round(gy,3)],
            "error_m": round(err, 4)
        })

    errs = [e["error_m"] for e in errors]
    mae = sum(errs)/len(errs)
    rmse = math.sqrt(sum(e**2 for e in errs)/len(errs))
    median_e = sorted(errs)[len(errs)//2]
    max_e = max(errs)

    return errors, {
        "MAE_m": round(mae, 4),
        "RMSE_m": round(rmse, 4),
        "Median_AE_m": round(median_e, 4),
        "Max_AE_m": round(max_e, 4),
        "n_points": len(errs)
    }


def compute_calibration_hull(src_pts_array: np.ndarray):
    """Compute convex hull of calibration points — this defines the CALIBRATED region."""
    pts_int = src_pts_array.astype(np.int32)
    hull = cv2.convexHull(pts_int)
    return hull.reshape(-1, 2).tolist()


def classify_coverage(feet_data: list, hull_pts: list, src_pts: list):
    """
    For each detection footpoint, classify as:
      INSIDE_CALIBRATION  — within convex hull of calibration points
      EDGE_REGION         — within 50px buffer outside hull
      OUTSIDE_CALIBRATION — beyond edge region
    """
    hull = np.array(hull_pts, dtype=np.int32).reshape((-1,1,2))

    inside = edge = outside = 0
    for fx, fy, cls_id in feet_data:
        dist = cv2.pointPolygonTest(hull, (float(fx), float(fy)), True)
        if dist >= 0:
            inside += 1
        elif dist >= -50:  # within 50px of hull boundary
            edge += 1
        else:
            outside += 1

    total = len(feet_data)
    return {
        "total_detections": total,
        "inside_calibration": inside,
        "edge_region": edge,
        "outside_calibration": outside,
        "inside_pct": round(inside/total*100, 1) if total > 0 else 0,
        "edge_pct": round(edge/total*100, 1) if total > 0 else 0,
        "outside_pct": round(outside/total*100, 1) if total > 0 else 0,
    }


def main():
    print("=== V2.3: Computing New Wide-Coverage Homography ===")
    print(f"\nCalibration points: {len(RAW_CALIBRATION_POINTS)}")
    print(f"Measurement source: VISUAL_ESTIMATION (NOT physically measured)")
    print(f"Assumed floor: {ASSUMED_FLOOR_WIDTH_M}m × {ASSUMED_FLOOR_DEPTH_M}m")

    H, mask, src, dst = compute_homography_robust(RAW_CALIBRATION_POINTS)

    if H is None:
        print("ERROR: Could not compute homography")
        return

    print(f"\nHomography computed (RANSAC with {len(RAW_CALIBRATION_POINTS)} points)")
    if mask is not None:
        inliers = int(mask.sum())
        print(f"RANSAC inliers: {inliers}/{len(RAW_CALIBRATION_POINTS)}")

    # Reprojection errors (this is internal consistency, NOT physical accuracy)
    errors, agg = compute_reprojection_errors(H, src, dst)
    print(f"\nReprojection Error (internal consistency only):")
    print(f"  MAE:    {agg['MAE_m']}m")
    print(f"  RMSE:   {agg['RMSE_m']}m")
    print(f"  Median: {agg['Median_AE_m']}m")
    print(f"  Max:    {agg['Max_AE_m']}m")
    print("  NOTE: These errors measure internal consistency, NOT physical accuracy.")

    # Calibration hull
    hull = compute_calibration_hull(src)
    print(f"\nCalibration convex hull: {len(hull)} vertices")

    # Load detection feet for coverage analysis (optional)
    feet_data = []
    feet_path = ROOT / "reports/v23_detection_extent.json"
    try:
        if feet_path.exists():
            with open(feet_path) as f:
                ext = json.load(f)
            coverage = {"note": "Coverage will be computed by run_spatial_audit.py"}
    except Exception:
        coverage = {"note": "Detection extent file unavailable"}

    # Build calibration artifact
    artifact = {
        "camera_id": "test2_cam_01",
        "source_video": "test2.mp4",
        "video_resolution_px": [1274, 720],
        "created_at": datetime.now().isoformat(),
        "measurement_source": "VISUAL_ESTIMATION",
        "physical_measurements_available": False,
        "calibration_status": "VISUALLY_ESTIMATED_NOT_VALIDATED",
        "calibration_warning": (
            "World coordinates are ESTIMATES based on visual inspection and "
            "assumed floor dimensions. Metric distances have UNKNOWN real-world accuracy. "
            "Physical tape measurements required for VALIDATED status."
        ),
        "assumed_floor_dimensions_m": {
            "width": ASSUMED_FLOOR_WIDTH_M,
            "depth": ASSUMED_FLOOR_DEPTH_M,
            "basis": "Assumed from typical warehouse/industrial floor dimensions"
        },
        "calibration_points": [
            {
                "id": i,
                "pixel": [p[0], p[1]],
                "world_m": [p[2], p[3]],
                "zone_label": p[4],
                "measurement_source": "VISUAL_ESTIMATION"
            }
            for i, p in enumerate(RAW_CALIBRATION_POINTS)
        ],
        "homography": H.flatten().tolist(),
        "homography_method": "RANSAC (cv2.findHomography)" if len(RAW_CALIBRATION_POINTS) >= 8 else "DLT",
        "n_calibration_points": len(RAW_CALIBRATION_POINTS),
        "src_pts": src.tolist(),
        "dst_pts": dst.tolist(),
        "calibration_hull_px": hull,
        "world_width_m": ASSUMED_FLOOR_WIDTH_M,
        "world_height_m": ASSUMED_FLOOR_DEPTH_M,
        "reprojection_error": {
            "description": (
                "Internal consistency error — measures how well H maps "
                "calibration pixels back to their estimated world coords. "
                "Does NOT measure real-world physical accuracy."
            ),
            "metrics": agg,
            "per_point": errors
        },
        "previous_calibration": {
            "src_pts": [[210.0, 180.0], [340.0, 180.0], [150.0, 340.0], [430.0, 340.0]],
            "dst_pts": [[0.0, 6.0], [3.5, 6.0], [0.0, 0.0], [3.5, 0.0]],
            "n_points": 4,
            "bounds_method": "bbox + 100px hardcoded margin",
            "geometry_error_instances_v2_2": 969,
            "geometry_error_rate_v2_2_pct": 77.8
        }
    }

    out_path = ROOT / "config/calibration/warehouse_test2.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)): return int(obj)
            if isinstance(obj, (np.floating, np.float32, np.float64)): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            return super().default(obj)
    
    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2, cls=NpEncoder)
    print(f"\nCalibration artifact saved: {out_path}")
    return artifact


if __name__ == "__main__":
    main()
