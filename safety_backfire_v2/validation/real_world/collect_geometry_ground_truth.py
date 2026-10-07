"""
Phase 2 — Real-World Geometry Ground Truth Collection Tool

This tool has TWO modes:
1. TEMPLATE mode: Extracts frames and generates a JSON template for manual annotation
2. VALIDATE mode: Reads filled ground_truth_geometry.json and computes error metrics

Since no physical measurements are available for the current test videos,
this tool generates the template and clearly marks all distances as NULL.
Physical measurements MUST be provided by a human with access to the filming location.
"""
import sys
import json
import cv2
import math
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.geometry import GroundPlaneCalibrator


def extract_template_frames(video_path: Path, output_dir: Path):
    """
    Suggests strategic frames for geometry ground truth annotation.
    Covers: foreground, midground, background, left, center, right, near-boundary.
    """
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    print(f"Video: {video_path.name}, Frames: {total_frames}, FPS: {fps}")

    # Choose 8 representative frames spread through the video
    sample_positions = [0.05, 0.15, 0.30, 0.45, 0.60, 0.75, 0.88, 0.95]
    selected_frames = [int(p * total_frames) for p in sample_positions]

    output_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for frame_num in selected_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            continue
        fname = f"gt_geometry_frame_{frame_num:05d}.jpg"
        cv2.imwrite(str(output_dir / fname), frame)
        saved.append({"frame": frame_num, "file": fname})
        print(f"  Saved frame {frame_num} → {fname}")

    cap.release()
    return saved


def generate_ground_truth_template(video_path: Path, output_dir: Path):
    """
    Generates a JSON template for ground truth geometry annotation.
    All physical_distance_m fields are NULL — must be filled by a human.
    """
    frames = extract_template_frames(video_path, output_dir)

    # Template measurement points covering all required zones
    # pixel coordinates are PLACEHOLDER suggestions — must be adjusted by annotator
    template = {
        "metadata": {
            "video": str(video_path.name),
            "physical_ground_truth_available": False,
            "physical_ground_truth_note": (
                "All physical_distance_m values are NULL. "
                "These MUST be filled with actual physical measurements from the filming location. "
                "Without this data, geometry distance validation CANNOT be performed."
            ),
            "annotation_instructions": [
                "For each measurement pair, identify two points in the video frame",
                "Measure the actual physical distance between those points in the real world",
                "Enter the real-world distance in physical_distance_m",
                "The system will compute estimated_distance_m using the homography",
                "Comparison yields absolute_error_m and relative_error_percent"
            ]
        },
        "calibration_points": [
            {
                "id": "fg_center_A",
                "zone": "foreground_center",
                "description": "Two points in the near foreground, center of frame",
                "pixel_A": [None, None],
                "pixel_B": [None, None],
                "physical_distance_m": None,
                "status": "NEEDS_ANNOTATION"
            },
            {
                "id": "fg_left_B",
                "zone": "foreground_left",
                "description": "Two points in near foreground, left side",
                "pixel_A": [None, None],
                "pixel_B": [None, None],
                "physical_distance_m": None,
                "status": "NEEDS_ANNOTATION"
            },
            {
                "id": "fg_right_C",
                "zone": "foreground_right",
                "description": "Two points in near foreground, right side",
                "pixel_A": [None, None],
                "pixel_B": [None, None],
                "physical_distance_m": None,
                "status": "NEEDS_ANNOTATION"
            },
            {
                "id": "mid_center_D",
                "zone": "midground_center",
                "description": "Two points in midground, center",
                "pixel_A": [None, None],
                "pixel_B": [None, None],
                "physical_distance_m": None,
                "status": "NEEDS_ANNOTATION"
            },
            {
                "id": "mid_left_E",
                "zone": "midground_left",
                "description": "Two points in midground, left side",
                "pixel_A": [None, None],
                "pixel_B": [None, None],
                "physical_distance_m": None,
                "status": "NEEDS_ANNOTATION"
            },
            {
                "id": "mid_right_F",
                "zone": "midground_right",
                "description": "Two points in midground, right side",
                "pixel_A": [None, None],
                "pixel_B": [None, None],
                "physical_distance_m": None,
                "status": "NEEDS_ANNOTATION"
            },
            {
                "id": "bg_center_G",
                "zone": "background_center",
                "description": "Two points in background",
                "pixel_A": [None, None],
                "pixel_B": [None, None],
                "physical_distance_m": None,
                "status": "NEEDS_ANNOTATION"
            },
            {
                "id": "boundary_H",
                "zone": "near_calibration_boundary",
                "description": "Two points near the edge of calibrated zone",
                "pixel_A": [None, None],
                "pixel_B": [None, None],
                "physical_distance_m": None,
                "status": "NEEDS_ANNOTATION"
            }
        ],
        "reference_frames": frames
    }

    out_path = output_dir / "ground_truth_geometry.json"
    with open(out_path, "w") as f:
        json.dump(template, f, indent=2)
    print(f"\nTemplate saved to: {out_path}")
    print("⚠️  All physical_distance_m values are NULL — physical measurements required.")
    return template


def compute_geometry_metrics(gt_file: Path):
    """
    Reads a filled ground_truth_geometry.json and computes error metrics.
    Skips any entry where physical_distance_m is null.
    """
    with open(gt_file) as f:
        data = json.load(f)

    calibrator = GroundPlaneCalibrator()
    results = []
    computable = 0

    for point in data["calibration_points"]:
        if point["physical_distance_m"] is None or point["pixel_A"][0] is None:
            results.append({
                "id": point["id"],
                "zone": point["zone"],
                "ground_truth_m": None,
                "estimated_m": None,
                "absolute_error_m": None,
                "relative_error_percent": None,
                "status": "NOT_COMPUTABLE — physical_distance_m not provided"
            })
            continue

        pA = tuple(point["pixel_A"])
        pB = tuple(point["pixel_B"])
        gt_dist = point["physical_distance_m"]

        wA = calibrator.pixel_to_world(pA)
        wB = calibrator.pixel_to_world(pB)

        if wA is None or wB is None:
            results.append({
                "id": point["id"],
                "zone": point["zone"],
                "ground_truth_m": gt_dist,
                "estimated_m": None,
                "absolute_error_m": None,
                "relative_error_percent": None,
                "status": "NOT_COMPUTABLE — pixel outside calibration bounds"
            })
            continue

        est_dist = math.hypot(wB[0] - wA[0], wB[1] - wA[1])
        abs_err = abs(est_dist - gt_dist)
        rel_err = (abs_err / gt_dist * 100) if gt_dist > 0 else None

        results.append({
            "id": point["id"],
            "zone": point["zone"],
            "ground_truth_m": round(gt_dist, 3),
            "estimated_m": round(est_dist, 3),
            "absolute_error_m": round(abs_err, 3),
            "relative_error_percent": round(rel_err, 2) if rel_err is not None else None,
            "status": "COMPUTED"
        })
        computable += 1

    # Aggregate metrics (only over computable entries)
    valid = [r for r in results if r["status"] == "COMPUTED"]
    if valid:
        errors = [r["absolute_error_m"] for r in valid]
        rel_errors = [r["relative_error_percent"] for r in valid if r["relative_error_percent"] is not None]
        mae = sum(errors) / len(errors)
        rmse = math.sqrt(sum(e**2 for e in errors) / len(errors))
        median_ae = sorted(errors)[len(errors)//2]
        max_ae = max(errors)
        mean_rel = sum(rel_errors) / len(rel_errors) if rel_errors else None
        max_rel = max(rel_errors) if rel_errors else None
    else:
        mae = rmse = median_ae = max_ae = mean_rel = max_rel = None

    report = {
        "physical_ground_truth_available": computable > 0,
        "total_measurement_points": len(results),
        "computable_points": computable,
        "not_computable_points": len(results) - computable,
        "aggregate_metrics": {
            "MAE_m": round(mae, 4) if mae is not None else None,
            "RMSE_m": round(rmse, 4) if rmse is not None else None,
            "Median_AE_m": round(median_ae, 4) if median_ae is not None else None,
            "Max_AE_m": round(max_ae, 4) if max_ae is not None else None,
            "Mean_Relative_Error_pct": round(mean_rel, 2) if mean_rel is not None else None,
            "Max_Relative_Error_pct": round(max_rel, 2) if max_rel is not None else None,
        },
        "per_point_results": results
    }

    if computable == 0:
        report["calibration_classification"] = "UNVALIDATED"
        report["classification_reason"] = "No physical measurements provided. Cannot assess real-world distance accuracy."
    else:
        # Classify based on thresholds from config/validation_thresholds.yaml
        if mae <= 0.30:
            report["calibration_classification"] = "VALIDATED"
        elif mae <= 0.60:
            report["calibration_classification"] = "PARTIALLY_VALIDATED"
        elif mae <= 1.00:
            report["calibration_classification"] = "POORLY_VALIDATED"
        else:
            report["calibration_classification"] = "UNVALIDATED"
        report["classification_threshold_type"] = "PROJECT_VALIDATION_THRESHOLD"

    return report


if __name__ == "__main__":
    video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "test2.mp4"
    out_dir = ROOT / "validation/real_world"

    print("=== Geometry Ground Truth Tool ===")

    gt_file = out_dir / "ground_truth_geometry.json"
    if gt_file.exists():
        print("Found existing ground_truth_geometry.json — computing metrics...")
        report = compute_geometry_metrics(gt_file)
    else:
        print("Generating template (no physical measurements available)...")
        generate_ground_truth_template(video_path, out_dir)
        report = compute_geometry_metrics(out_dir / "ground_truth_geometry.json")

    out_report = out_dir / "geometry_validation_report.json"
    with open(out_report, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nClassification: {report['calibration_classification']}")
    print(f"Computable points: {report['computable_points']}/{report['total_measurement_points']}")
    print(f"Report saved to: {out_report}")
