"""
V2.3 — Phase 2: Calibration Visualizer

Draws the current calibration polygon, calibration bounds,
and footpoint distribution on reference frames.
Produces reports/v2_3_calibration_overlay.jpg
"""
import sys
import json
import cv2
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))


def draw_calibration_overlay(frame: np.ndarray, config: dict, detection_feet: list = None) -> np.ndarray:
    """
    Draws calibration polygon, bounds box, and optionally all detected footpoints.
    Color legend:
      Yellow polygon  = src_pts (calibration quad)
      Orange rect     = calibration_bounds (bbox + old 100px margin)
      Green dot       = footpoint INSIDE calibration (new hull)
      Red dot         = footpoint OUTSIDE calibration
      Cyan grid       = world-space grid projected back to image
    """
    vis = frame.copy()
    h, w = vis.shape[:2]

    src_pts = np.array(config["src_pts"], dtype=np.float32)
    dst_pts = np.array(config["dst_pts"], dtype=np.float32)
    H = np.array(config["homography"], dtype=np.float64).reshape(3, 3)
    H_inv = np.linalg.inv(H)

    # ── 1. Old calibration bounds box (bbox + 100px margin) ──────────────
    margin_old = 100
    old_xmin = int(np.min(src_pts[:,0]) - margin_old)
    old_xmax = int(np.max(src_pts[:,0]) + margin_old)
    old_ymin = int(np.min(src_pts[:,1]) - margin_old)
    old_ymax = int(np.max(src_pts[:,1]) + margin_old)
    cv2.rectangle(vis, (old_xmin, old_ymin), (old_xmax, old_ymax),
                  (0, 140, 255), 2)  # orange
    cv2.putText(vis, "OLD bounds (+100px)", (old_xmin+4, old_ymin+20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 140, 255), 2)

    # ── 2. src_pts polygon (yellow) ──────────────────────────────────────
    pts_i = src_pts.astype(np.int32).reshape((-1,1,2))
    cv2.polylines(vis, [pts_i], True, (0, 255, 255), 3)
    for i, pt in enumerate(src_pts):
        cv2.circle(vis, (int(pt[0]), int(pt[1])), 8, (0,255,255), -1)
        cv2.putText(vis, f"P{i}({int(pt[0])},{int(pt[1])})",
                    (int(pt[0])+6, int(pt[1])-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0,255,255), 1)

    # ── 3. New calibration hull (from config, if present) ─────────────────
    new_hull = config.get("calibration_hull_px")
    if new_hull:
        hull_pts = np.array(new_hull, dtype=np.int32).reshape((-1,1,2))
        cv2.polylines(vis, [hull_pts], True, (0,255,0), 3)
        cv2.putText(vis, "NEW calib hull", (new_hull[0][0]+4, new_hull[0][1]-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,0), 2)

    # ── 4. Footpoints (inside=green, outside=red) ─────────────────────────
    if detection_feet:
        # Use convex hull of new src_pts for containment test
        new_src = np.array(config.get("src_pts_new", config["src_pts"]), dtype=np.float32)
        for fx, fy, cls_id in detection_feet[:500]:  # sample max 500 to keep vis clean
            # point-in-convex-hull test
            dist = cv2.pointPolygonTest(new_src.reshape((-1,1,2)).astype(np.int32),
                                        (int(fx), int(fy)), False)
            color = (0,255,0) if dist >= 0 else (0,0,255)
            cv2.circle(vis, (int(fx), int(fy)), 3, color, -1)

    # ── 5. World-space grid projected back ────────────────────────────────
    world_w = config.get("world_width_m", 3.5)
    world_h = config.get("world_height_m", 6.0)
    for gx in np.arange(0, world_w+0.5, 1.0):
        for gy in np.arange(0, world_h+0.5, 1.0):
            wp = np.array([[[float(gx), float(gy)]]], dtype=np.float32)
            img_pt = cv2.perspectiveTransform(wp, H_inv)
            ix, iy = int(img_pt[0,0,0]), int(img_pt[0,0,1])
            if 0 <= ix < w and 0 <= iy < h:
                cv2.circle(vis, (ix, iy), 4, (255,200,0), -1)
                cv2.putText(vis, f"({gx:.0f},{gy:.0f})", (ix+3, iy-3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255,200,0), 1)

    # ── Legend ────────────────────────────────────────────────────────────
    legend = [
        ((0,255,255), "src_pts (original calib)"),
        ((0,140,255), "OLD bounds (+100px margin)"),
        ((0,255,0),   "NEW calib hull / inside foot"),
        ((0,0,255),   "Outside calibration foot"),
        ((255,200,0), "World grid (projected)"),
    ]
    for i, (col, label) in enumerate(legend):
        y = h - 20 - i*22
        cv2.rectangle(vis, (10, y-14), (28, y+2), col, -1)
        cv2.putText(vis, label, (34, y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, col, 1)

    return vis


def run(video_path: Path, config_path: Path, out_path: Path):
    # Load current calibration config
    with open(config_path) as f:
        config = json.load(f)

    # Load detection feet if available
    feet_path = ROOT / "reports/v23_detection_extent.json"
    feet = []
    if feet_path.exists():
        with open(feet_path) as f:
            data = json.load(f)
            feet = data.get("feet", [])

    # Extract multiple reference frames
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    for fn, suffix in [(50, "early"), (200, "interaction"), (400, "mid"), (600, "late")]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, fn)
        ret, frame = cap.read()
        if not ret:
            continue
        vis = draw_calibration_overlay(frame, config, feet)
        fp = out_path.parent / f"v2_3_calibration_overlay_f{fn:04d}_{suffix}.jpg"
        cv2.imwrite(str(fp), vis)
        print(f"  Saved: {fp.name}")

    cap.release()
    # Also save the primary overlay (frame 200 = interaction zone)
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 200)
    ret, frame = cap.read()
    cap.release()
    if ret:
        vis = draw_calibration_overlay(frame, config, feet)
        cv2.imwrite(str(out_path), vis)
        print(f"\nPrimary overlay saved: {out_path}")


if __name__ == "__main__":
    video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "test2.mp4"
    config_path = ROOT / "config/calibration/warehouse_test2.json"
    out_path = ROOT / "reports/v2_3_calibration_overlay.jpg"

    if not config_path.exists():
        print(f"ERROR: {config_path} not found. Run compute_new_calibration.py first.")
        sys.exit(1)

    print("=== V2.3 Calibration Visualizer ===")
    run(video_path, config_path, out_path)
