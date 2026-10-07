"""
Phase 16 — Real-World Failure Taxonomy

Runs the pipeline on real video and builds a structured failure taxonomy.
Identifies and categorizes actual failures observed during processing.
"""
import sys
import json
import cv2
from pathlib import Path
from ultralytics import YOLO
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.geometry import GroundPlaneCalibrator, compute_metric_distance
from core.event_engine import EventEngine
from core.trajectory import TrajectoryEngine
from core.kinematics import compute_metric_ttc


FAILURE_TYPES = {
    "PERSON_MISSED": "Person present in scene but not detected",
    "FORKLIFT_MISCLASSIFIED": "Forklift detected as wrong class or missed",
    "TRACK_FRAGMENTATION": "Track split into multiple IDs for same physical object",
    "ID_SWITCH": "Wrong ID assigned to an already-tracked object",
    "GEOMETRY_ERROR": "Footpoint outside calibrated homography region",
    "CALIBRATION_ERROR": "Calibration bounds rejected a valid interaction",
    "EVENT_FALSE_POSITIVE": "System generated event where no human interaction occurred",
    "EVENT_FALSE_NEGATIVE": "Human interaction missed by the system",
    "TTC_UNAVAILABLE": "TTC could not be computed (NO_APPROACH or UNDEFINED)",
    "ZONE_MISCLASSIFICATION": "Object detected in wrong danger zone"
}


def run_failure_taxonomy(video_path: Path, model_path: Path):
    """Scan real video and collect observable failure signatures."""
    model = YOLO(str(model_path))
    calibrator = GroundPlaneCalibrator()
    trajectory_engine = TrajectoryEngine()
    event_engine = EventEngine()

    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()

    failures = defaultdict(list)  # failure_type → list of frame_indices
    frame_idx = 0
    prev_ids = {}  # track_id → class_name history for ID switch detection

    for result in model.track(
        source=str(video_path),
        stream=True,
        persist=True,
        tracker="bytetrack.yaml",
        imgsz=640,
        conf=0.15,
        iou=0.70,
        device="cpu",
        classes=[0, 1],
        verbose=False
    ):
        frame_idx += 1
        timestamp = frame_idx / fps
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            event_engine.process_frame_interactions(frame_idx, timestamp, [])
            continue

        ids = boxes.id
        xyxy = boxes.xyxy.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)
        confs = boxes.conf.cpu().numpy()

        persons, forklifts = [], []
        current_ids = {}

        for i, cls_id in enumerate(clss):
            tid = int(ids[i].item()) if ids is not None and ids[i] is not None else None
            if tid is None:
                continue

            c_name = model.names[int(cls_id)]
            box = [int(v) for v in xyxy[i]]
            cx = (box[0] + box[2]) / 2.0
            foot_y = box[3]

            # Check ID switch: same track_id switching class
            if tid in prev_ids and prev_ids[tid] != c_name:
                failures["ID_SWITCH"].append({
                    "frame": frame_idx,
                    "track_id": tid,
                    "prev_class": prev_ids[tid],
                    "new_class": c_name
                })

            current_ids[tid] = c_name

            # Geometry check
            world_pt = calibrator.pixel_to_world((cx, foot_y))
            in_bounds = calibrator.is_in_calibrated_region((cx, foot_y))

            if not in_bounds:
                failures["GEOMETRY_ERROR"].append({
                    "frame": frame_idx,
                    "class": c_name,
                    "track_id": tid,
                    "pixel": [round(cx), round(foot_y)]
                })
                continue

            if world_pt is None:
                continue

            import math as _math
            trajectory_engine.update(tid, c_name, timestamp, world_pt[0], world_pt[1], "SAFE")
            traj = trajectory_engine.get_trajectory(tid)
            vel = (0.0, 0.0)
            if traj and traj.points and traj.points[-1].velocity_m_s is not None:
                speed = traj.points[-1].velocity_m_s
                dir_rad = traj.points[-1].direction_deg * (_math.pi / 180.0)
                vel = (speed * _math.cos(dir_rad), speed * _math.sin(dir_rad))

            entity = {"id": tid, "pos": world_pt, "vel": vel}
            if c_name == "person":
                persons.append(entity)
            elif c_name == "forklift":
                forklifts.append(entity)

        prev_ids = current_ids

        frame_interactions = []
        for p in persons:
            for f in forklifts:
                geo = compute_metric_distance(p["pos"], f["pos"], calibrator)
                if geo["calibration_status"] != "VALID":
                    failures["CALIBRATION_ERROR"].append({
                        "frame": frame_idx,
                        "person_id": p["id"],
                        "forklift_id": f["id"],
                        "status": geo["calibration_status"]
                    })
                    continue

                dist_m = geo["distance_m"]
                ttc = compute_metric_ttc(p["pos"], f["pos"], p["vel"], f["vel"], dist_m)

                if ttc["ttc_status"] in ["UNDEFINED", "NO_APPROACH"]:
                    failures["TTC_UNAVAILABLE"].append({
                        "frame": frame_idx,
                        "ttc_status": ttc["ttc_status"],
                        "distance_m": dist_m
                    })

                zone = "DANGER" if dist_m < 1.5 else ("CAUTION" if dist_m < 3.0 else "SAFE")
                frame_interactions.append({
                    "person_id": p["id"],
                    "forklift_id": f["id"],
                    "distance_meters": dist_m,
                    "approach_speed_px_s": ttc["relative_velocity_m_s"],
                    "zone_status": zone,
                    "risk_exposure_score": 0.0
                })

        event_engine.process_frame_interactions(frame_idx, timestamp, frame_interactions)

    event_engine.close_all_events()

    # Check for track fragmentation (multiple IDs for what appears to be same entity)
    events = event_engine.historical_events
    short_events = [e for e in events if e.duration_sec < 0.5]
    for e in short_events:
        failures["TRACK_FRAGMENTATION"].append({
            "event_id": e.event_id,
            "person_id": e.person_id,
            "forklift_id": e.forklift_id,
            "duration_sec": e.duration_sec
        })

    # Build taxonomy table
    taxonomy = []
    for failure_type, instances in failures.items():
        count = len(instances)
        if count == 0:
            continue

        # Severity classification
        if failure_type in ["PERSON_MISSED", "EVENT_FALSE_NEGATIVE"]:
            severity = "HIGH"
        elif failure_type in ["TRACK_FRAGMENTATION", "ID_SWITCH", "GEOMETRY_ERROR"]:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Example frames
        example_frames = []
        for inst in instances[:3]:
            if isinstance(inst, dict):
                example_frames.append(inst.get("frame", "N/A"))
            else:
                example_frames.append(inst)

        taxonomy.append({
            "failure_type": failure_type,
            "description": FAILURE_TYPES.get(failure_type, "Unknown"),
            "count": count,
            "severity": severity,
            "example_frames": example_frames,
            "root_cause": _get_root_cause(failure_type),
            "recommended_action": _get_recommended_action(failure_type),
            "instances_sample": instances[:5]
        })

    taxonomy.sort(key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["severity"]])

    result = {
        "phase": "Failure Taxonomy (Phase 16)",
        "video": str(video_path.name),
        "total_frames_analyzed": total_frames,
        "total_failure_types_observed": len(taxonomy),
        "failure_taxonomy": taxonomy,
        "note": (
            "EVENT_FALSE_POSITIVE and EVENT_FALSE_NEGATIVE cannot be computed without "
            "human-annotated ground truth. These remain NOT_COMPUTABLE."
        )
    }

    return result


def _get_root_cause(failure_type):
    causes = {
        "TRACK_FRAGMENTATION": "ByteTrack loses the track during occlusion or low confidence frames, re-assigns new ID",
        "ID_SWITCH": "IoU-based re-identification fails when objects are spatially close or overlap",
        "GEOMETRY_ERROR": "Object footpoint falls outside hardcoded calibration bounds + 100px margin",
        "CALIBRATION_ERROR": "Homography projection produces invalid result outside calibrated region",
        "TTC_UNAVAILABLE": "Objects moving apart (NO_APPROACH) or stationary — physically correct behavior",
        "PERSON_MISSED": "YOLO confidence below threshold, severe occlusion, or person outside camera FOV",
        "FORKLIFT_MISCLASSIFIED": "Similar visual appearance to other objects, or partial occlusion"
    }
    return causes.get(failure_type, "Unknown — requires manual investigation")


def _get_recommended_action(failure_type):
    actions = {
        "TRACK_FRAGMENTATION": "Increase max_gap_frames or use appearance-based Re-ID model",
        "ID_SWITCH": "Tune ByteTrack parameters or add appearance embeddings",
        "GEOMETRY_ERROR": "Re-calibrate homography with wider coverage or use multi-camera setup",
        "CALIBRATION_ERROR": "Physically verify calibration points and remeasure dst_pts",
        "TTC_UNAVAILABLE": "No action required — system correctly reports non-approaching objects as NO_APPROACH",
        "PERSON_MISSED": "Lower confidence threshold (risk: more FP) or improve model with more training data",
        "FORKLIFT_MISCLASSIFIED": "Add more forklift training samples in ambiguous poses"
    }
    return actions.get(failure_type, "Manual investigation required")


if __name__ == "__main__":
    video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "test2.mp4"
    model_path = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"

    print("=== Phase 16: Real-World Failure Taxonomy ===")
    result = run_failure_taxonomy(video_path, model_path)

    out_path = ROOT / "reports/v2_2_failure_taxonomy.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nFailure types observed: {result['total_failure_types_observed']}")
    for item in result["failure_taxonomy"]:
        print(f"  [{item['severity']}] {item['failure_type']}: {item['count']} instances")
    print(f"\nSaved to: {out_path}")
