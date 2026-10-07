"""
V2.8 — Real-World Video Experiment (Uncertainty-Aware Policy)

Runs the full pipeline on test2.mp4 using:
1. YOLOv8 for Person/Forklift bounding boxes.
2. YOLOv8-pose for human keypoints (Pose Estimation).
3. OperatorVehicleRelationEngineV2 for relationship classification.
4. EventEngineV2 to manage uncertainty via the Safety Matrix.
"""
import sys
import json
import cv2
import time
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from ultralytics import YOLO
from core.geometry import load_default_calibrator
from core.operator_relation_v2 import OperatorVehicleRelationEngineV2
from core.event_engine_v2 import EventEngineV2

def run_v2_8():
    print("=== V2.8 Uncertainty-Aware Safety Policy Experiment ===")
    
    video_path = str(ROOT.parent / "test2.mp4")
    model_path = str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    
    print("Loading Models...")
    det_model = YOLO(model_path)
    pose_model = YOLO("yolov8n-pose.pt")
    
    calibrator = load_default_calibrator()
    relation_engine = OperatorVehicleRelationEngineV2()
    event_engine = EventEngineV2(max_gap_frames=15)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\nProcessing {total_frames} frames from test2.mp4...")
    
    stats = {
        "frames": 0,
        "interaction_candidates_evaluated": 0,
    }
    
    start_time = time.time()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        f_idx = stats["frames"] + 1
        video_time_sec = f_idx / 30.0
        
        # A. Detection & Tracking
        res = det_model.track(frame, imgsz=640, conf=0.15, iou=0.70, classes=[0,1], persist=True, tracker="bytetrack.yaml", verbose=False)[0]
        
        persons, forklifts = [], []
        if res.boxes.id is not None:
            for b, cls, trk_id in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy(), res.boxes.id.cpu().numpy()):
                box = [int(v) for v in b]
                cx, fy = (box[0] + box[2]) / 2.0, box[3]
                obj = {"id": int(trk_id), "class": "person" if int(cls) == 0 else "forklift", "bbox": box, "px": (cx, fy)}
                persons.append(obj) if obj["class"] == "person" else forklifts.append(obj)
        
        # B. Pose Estimation
        if persons:
            pose_res = pose_model.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
            for p in persons:
                p_box = p["bbox"]
                best_iou, best_kpts = 0, None
                if pose_res.keypoints is not None and len(pose_res.boxes) > 0:
                    for i, box in enumerate(pose_res.boxes.xyxy.cpu().numpy()):
                        ix1, iy1 = max(p_box[0], box[0]), max(p_box[1], box[1])
                        ix2, iy2 = min(p_box[2], box[2]), min(p_box[3], box[3])
                        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                        area1, area2 = (p_box[2]-p_box[0])*(p_box[3]-p_box[1]), (box[2]-box[0])*(box[3]-box[1])
                        iou = inter / float(area1 + area2 - inter) if (area1 + area2 - inter) > 0 else 0
                        if iou > 0.5 and iou > best_iou:
                            best_iou = iou
                            kpts = pose_res.keypoints.data.cpu().numpy()[i]
                            if kpts.shape[1] == 2:
                                import numpy as np
                                kpts = np.hstack([kpts, np.ones((17, 1))])
                            best_kpts = kpts.tolist()
                p["keypoints"] = best_kpts
        
        # C. Relation Classification
        relation_engine.classify_frame(persons, forklifts, f_idx)
        
        # D. Interaction Generation
        frame_interactions = []
        for p in persons:
            for f in forklifts:
                rel = relation_engine.get_person_relation(p["id"], f["id"], f_idx)
                if not rel: rel = "UNKNOWN"
                
                # We do NOT drop OPERATOR_ON_VEHICLE here. We send it to EventEngineV2
                # to properly classify it as SUPPRESSED_OPERATOR_EVENT.
                
                p_gp = calibrator.pixel_to_world(p["px"])
                f_gp = calibrator.pixel_to_world(f["px"])
                
                if p_gp is not None and f_gp is not None:
                    dist_m = math.hypot(p_gp[0] - f_gp[0], p_gp[1] - f_gp[1])
                    zone = "SAFE"
                    if dist_m <= 1.5: zone = "DANGER"
                    elif dist_m <= 3.0: zone = "CAUTION"
                    
                    if zone != "SAFE" or rel == "OPERATOR_ON_VEHICLE":
                        # We send even SAFE operators to ensure the engine tracks them
                        stats["interaction_candidates_evaluated"] += 1
                        frame_interactions.append({
                            "person_id": p["id"],
                            "forklift_id": f["id"],
                            "distance_meters": round(dist_m, 2),
                            "zone_status": zone,
                            "relation": rel
                        })
                        
        event_engine.process_frame_interactions(f_idx, video_time_sec, frame_interactions)
        stats["frames"] += 1
        
        if f_idx % 200 == 0:
            print(f"Processed {f_idx}/{total_frames} frames...")

    event_engine.close_all_events()
    events = event_engine.get_all_events()
    elapsed = time.time() - start_time
    
    # Analyze Final States
    states = {"CONFIRMED_EVENT": 0, "CANDIDATE_EVENT": 0, "SUPPRESSED_OPERATOR_EVENT": 0, "INSUFFICIENT_EVIDENCE": 0}
    for e in events:
        if e["event_state"] in states:
            states[e["event_state"]] += 1
    
    print("\n==============================================")
    print("  V2.8 UNCERTAINTY EXPERIMENT RESULTS (test2.mp4)")
    print("==============================================")
    print(f"Frames Processed: {stats['frames']} ({elapsed:.1f} sec)")
    print("\nFinal Event States:")
    print(f"  CONFIRMED_EVENT (Real Danger Alerts): {states['CONFIRMED_EVENT']}")
    print(f"  CANDIDATE_EVENT (Needs Human Review): {states['CANDIDATE_EVENT']}")
    print(f"  INSUFFICIENT_EVIDENCE (Dismissed):    {states['INSUFFICIENT_EVIDENCE']}")
    print(f"  SUPPRESSED_OPERATOR_EVENT (Safe):     {states['SUPPRESSED_OPERATOR_EVENT']}")
    print(f"\nTotal Tracked Interactions: {len(events)}")
    
    # Output Confirmed Events for Audit
    print("\nConfirmed Danger/Caution Events:")
    for e in events:
        if e["event_state"] == "CONFIRMED_EVENT":
            print(f"  {e['event_id']}: Frames {e['start_frame']}-{e['end_frame']} | Zone: {e['zone']} | Reason: {e['reason']}")
    
    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "v2_8_events.json", "w") as f:
        json.dump(events, f, indent=2)

if __name__ == "__main__":
    run_v2_8()
