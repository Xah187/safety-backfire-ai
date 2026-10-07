"""
V2.9 — Improved Benchmark Runner
Executes the exact same benchmark on test2.mp4 using the improved P0/P1 core code.
Outputs v2_9_improved_snapshot.json for direct comparative analysis against baseline.
"""
import sys
import json
import time
import math
import platform
import hashlib
from pathlib import Path
import cv2
import numpy as np
import torch
import ultralytics
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.geometry import load_default_calibrator
from core.operator_relation_v2 import OperatorVehicleRelationEngineV2
from core.event_engine_v2 import EventEngineV2
from core.track_manager import TrackManager, TrackState
from core.observation_gate import ObservationValidity, ObservationIntegrityGate

def get_file_hash(path: Path) -> str:
    if not path.exists():
        return "NOT_FOUND"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def run_improved():
    print("=================================================================")
    print("   V2.9 SYSTEM FORENSICS: EXECUTING IMPROVED BENCHMARK           ")
    print("=================================================================")

    video_path = ROOT.parent / "test2.mp4"
    if not video_path.exists():
        video_path = ROOT / "test2.mp4"
    det_model_path = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
    pose_model_path = ROOT / "yolov8n-pose.pt"
    calib_path = ROOT / "config/calibration/warehouse_test2.json"

    meta = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "os": platform.platform(),
        "machine": platform.machine(),
        "python_version": sys.version,
        "torch_version": torch.__version__,
        "mps_available": torch.backends.mps.is_available(),
        "ultralytics_version": ultralytics.__version__,
        "detector_path": str(det_model_path),
        "detector_sha256": get_file_hash(det_model_path),
        "pose_path": str(pose_model_path),
        "pose_sha256": get_file_hash(pose_model_path),
        "calibration_path": str(calib_path),
        "calibration_sha256": get_file_hash(calib_path),
        "video_path": str(video_path),
        "video_sha256": get_file_hash(video_path)
    }

    det_model = YOLO(str(det_model_path))
    pose_model = YOLO(str(pose_model_path))
    calibrator = load_default_calibrator()
    track_manager = TrackManager(strong_conf_threshold=0.35, max_prediction_frames=5)
    relation_engine = OperatorVehicleRelationEngineV2()
    event_engine = EventEngineV2(max_gap_frames=15)

    meta["detector_classes"] = det_model.names
    meta["pose_classes"] = pose_model.names

    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    meta["video_properties"] = {"frames": total_frames, "fps": fps, "width": w, "height": h}

    perf = {
        "decode_time_s": 0.0,
        "detect_time_s": 0.0,
        "pose_time_s": 0.0,
        "track_manager_time_s": 0.0,
        "relation_time_s": 0.0,
        "proximity_event_time_s": 0.0,
        "total_pipeline_time_s": 0.0
    }

    counts = {
        "raw_detections": {"forklift": 0, "person": 0},
        "observation_gate": {"VALID": 0, "WEAK": 0, "INVALID": 0},
        "safety_eligible": {"true": 0, "false": 0},
        "track_states": {"OBSERVED": 0, "PREDICTED": 0, "STALE": 0},
        "motion_states": {"MOVING": 0, "PARKED": 0},
        "relations": {"OPERATOR_ON_VEHICLE": 0, "INDEPENDENT_PEDESTRIAN": 0, "UNKNOWN": 0},
        "raw_tracks_seen": set(),
        "safety_tracks_seen": set()
    }

    frame_idx = 0
    start_total = time.time()

    print(f"\nProcessing {total_frames} frames with improved pipeline...")

    while cap.isOpened():
        t0 = time.time()
        ret, frame = cap.read()
        t1 = time.time()
        perf["decode_time_s"] += (t1 - t0)

        if not ret:
            break

        frame_idx += 1
        video_time_sec = frame_idx / fps

        # A. Detection & Tracking
        t_det0 = time.time()
        res = det_model.track(frame, imgsz=640, conf=0.15, iou=0.70, classes=[0,1], persist=True, tracker="bytetrack.yaml", verbose=False)[0]
        t_det1 = time.time()
        perf["detect_time_s"] += (t_det1 - t_det0)

        all_tracked = []
        if res.boxes.id is not None:
            for b, cls, trk_id, conf in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy(), res.boxes.id.cpu().numpy(), res.boxes.conf.cpu().numpy()):
                box = [int(v) for v in b]
                cx, fy = (box[0] + box[2]) / 2.0, float(box[3])
                class_name = det_model.names[int(cls)]
                trk_id = int(trk_id)
                counts["raw_detections"][class_name] = counts["raw_detections"].get(class_name, 0) + 1
                counts["raw_tracks_seen"].add(trk_id)
                all_tracked.append({
                    "id": trk_id,
                    "class": class_name,
                    "bbox": box,
                    "px": (cx, fy),
                    "conf": float(conf)
                })

        # B. Pose Estimation
        t_pose0 = time.time()
        if all_tracked:
            pose_res = pose_model.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
            for p in all_tracked:
                if p["class"] != "person":
                    continue
                p_box = p["bbox"]
                best_iou, best_kpts = 0, None
                if pose_res.keypoints is not None and len(pose_res.boxes) > 0:
                    for i, box in enumerate(pose_res.boxes.xyxy.cpu().numpy()):
                        ix1, iy1 = max(p_box[0], box[0]), max(p_box[1], box[1])
                        ix2, iy2 = min(p_box[2], box[2]), min(p_box[3], box[3])
                        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                        area1 = (p_box[2] - p_box[0]) * (p_box[3] - p_box[1])
                        area2 = (box[2] - box[0]) * (box[3] - box[1])
                        iou = inter / float(area1 + area2 - inter) if (area1 + area2 - inter) > 0 else 0
                        if iou > 0.3 and iou > best_iou:
                            best_iou = iou
                            kpts = pose_res.keypoints.data.cpu().numpy()[i]
                            if kpts.shape[1] == 2:
                                kpts = np.hstack([kpts, np.ones((17, 1))])
                            best_kpts = kpts.tolist()
                p["keypoints"] = best_kpts
        t_pose1 = time.time()
        perf["pose_time_s"] += (t_pose1 - t_pose0)

        # C. TrackManager + Observation Gate
        t_tm0 = time.time()
        persons, forklifts = [], []
        if all_tracked:
            valid_objects = track_manager.process_tracks(frame_idx, video_time_sec, all_tracked, calibrator)
            for obj in valid_objects:
                val = str(obj.get("observation_validity", "VALID"))
                counts["observation_gate"][val] = counts["observation_gate"].get(val, 0) + 1
                elig = obj.get("safety_eligible", False)
                if elig:
                    counts["safety_eligible"]["true"] += 1
                    counts["safety_tracks_seen"].add(obj["id"])
                else:
                    counts["safety_eligible"]["false"] += 1

                t_st = obj.get("track_state", "OBSERVED")
                counts["track_states"][t_st] = counts["track_states"].get(t_st, 0) + 1

                m_st = obj.get("motion_state", "PARKED")
                counts["motion_states"][m_st] = counts["motion_states"].get(m_st, 0) + 1

                if elig:
                    if obj["class"] == "person":
                        persons.append(obj)
                    else:
                        forklifts.append(obj)
        t_tm1 = time.time()
        perf["track_manager_time_s"] += (t_tm1 - t_tm0)

        # D. Relation Classification (Fixed Multi-Vehicle Loop)
        t_rel0 = time.time()
        frame_rels = relation_engine.classify_frame(persons, forklifts, frame_idx)
        for r in frame_rels:
            rel_name = r.get("relation", "UNKNOWN")
            counts["relations"][rel_name] = counts["relations"].get(rel_name, 0) + 1
        t_rel1 = time.time()
        perf["relation_time_s"] += (t_rel1 - t_rel0)

        # E. Proximity & Event Generation (Fixed Operator Logic)
        t_ev0 = time.time()
        frame_interactions = []
        for p in persons:
            # Verified relation from relation engine (no blind speed > 0.8 shortcut)
            p_rel = relation_engine.get_person_relation(p["id"], None, frame_idx) or "UNKNOWN"
            p_is_op = (p_rel == "OPERATOR_ON_VEHICLE")

            for f in forklifts:
                f_is_moving = f.get("is_moving", False)
                rel = relation_engine.get_person_relation(p["id"], f["id"], frame_idx) or "UNKNOWN"

                # If person is verified operator on a moving vehicle passing a parked vehicle
                if p_is_op and not f_is_moving:
                    continue

                p_gp = calibrator.pixel_to_world(p["px"])
                f_gp = calibrator.pixel_to_world(f["px"])

                if p_gp is not None and f_gp is not None:
                    dist_m = math.hypot(p_gp[0] - f_gp[0], p_gp[1] - f_gp[1])
                    zone = "SAFE"
                    if dist_m <= 1.5:
                        zone = "DANGER"
                    elif dist_m <= 3.0:
                        zone = "CAUTION"

                    if zone != "SAFE" or rel == "OPERATOR_ON_VEHICLE":
                        frame_interactions.append({
                            "person_id": p["id"],
                            "forklift_id": f["id"],
                            "distance_meters": dist_m,
                            "zone_status": zone,
                            "relation": rel
                        })

        event_engine.process_frame_interactions(frame_idx, video_time_sec, frame_interactions)
        t_ev1 = time.time()
        perf["proximity_event_time_s"] += (t_ev1 - t_ev0)

        if frame_idx % 200 == 0:
            print(f"  Frame {frame_idx}/{total_frames} (Elapsed: {time.time() - start_total:.1f}s)")

    cap.release()
    event_engine.close_all_events()

    total_pipeline_time = time.time() - start_total
    perf["total_pipeline_time_s"] = round(total_pipeline_time, 2)
    perf["overall_fps"] = round(frame_idx / total_pipeline_time, 2) if total_pipeline_time > 0 else 0
    perf["decode_fps"] = round(frame_idx / perf["decode_time_s"], 2) if perf["decode_time_s"] > 0 else 0
    perf["detect_fps"] = round(frame_idx / perf["detect_time_s"], 2) if perf["detect_time_s"] > 0 else 0
    perf["pose_fps"] = round(frame_idx / perf["pose_time_s"], 2) if perf["pose_time_s"] > 0 else 0

    all_events = event_engine.get_all_events()

    event_summary = {
        "total_events": len(all_events),
        "by_state": {},
        "by_zone": {},
        "by_relation": {},
        "by_alert_state": {},
        "events_details": all_events
    }

    for ev in all_events:
        st = ev.get("event_state", "UNKNOWN")
        event_summary["by_state"][st] = event_summary["by_state"].get(st, 0) + 1
        zn = ev.get("zone", "UNKNOWN")
        event_summary["by_zone"][zn] = event_summary["by_zone"].get(zn, 0) + 1
        rl = ev.get("relation_state", "UNKNOWN")
        event_summary["by_relation"][rl] = event_summary["by_relation"].get(rl, 0) + 1
        al = ev.get("alert_state", "UNKNOWN")
        event_summary["by_alert_state"][al] = event_summary["by_alert_state"].get(al, 0) + 1

    counts["unique_raw_tracks"] = len(counts["raw_tracks_seen"])
    counts["unique_safety_tracks"] = len(counts["safety_tracks_seen"])
    del counts["raw_tracks_seen"]
    del counts["safety_tracks_seen"]

    snapshot = {
        "metadata": meta,
        "performance": perf,
        "counts": counts,
        "event_summary": event_summary
    }

    out_dir = ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "v2_9_improved_snapshot.json"
    with open(out_file, "w") as f:
        json.dump(snapshot, f, indent=2)

    print("\n=================================================================")
    print("   IMPROVED BENCHMARK COMPLETE                                   ")
    print(f"   Saved to: {out_file}                                         ")
    print(f"   Total Frames: {frame_idx}, Pipeline FPS: {perf['overall_fps']}")
    print(f"   Total Events: {event_summary['total_events']}")
    print(f"   Event States: {event_summary['by_state']}")
    print(f"   Alert States: {event_summary['by_alert_state']}")
    print("=================================================================")

if __name__ == "__main__":
    run_improved()
