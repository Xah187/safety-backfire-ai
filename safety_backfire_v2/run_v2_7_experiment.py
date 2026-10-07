"""
V2.7 — Real-World Video Experiment (Multi-Cue)

Runs the full pipeline on test2.mp4 using:
1. YOLOv8 for Person/Forklift bounding boxes.
2. YOLOv8-pose for human keypoints (Pose Estimation).
3. OperatorVehicleRelationEngineV2 for robust relationship classification.
4. EventEngine to register valid interactions.

Validates the UNKNOWN != SUPPRESS invariant on real data.
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
from core.event_engine import EventEngine

def run_v2_7():
    print("=== V2.7 Multi-Cue Operator Relation Experiment ===")
    
    video_path = str(ROOT.parent / "test2.mp4")
    model_path = str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    
    # 1. Load Models
    print("Loading Detection Model...")
    det_model = YOLO(model_path)
    print("Loading Pose Model (YOLOv8n-pose)...")
    pose_model = YOLO("yolov8n-pose.pt")
    
    # 2. Load Engines
    calibrator = load_default_calibrator()
    relation_engine = OperatorVehicleRelationEngineV2()
    event_engine = EventEngine(max_gap_frames=15)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\nProcessing {total_frames} frames from test2.mp4...")
    
    stats = {
        "frames": 0,
        "persons": 0,
        "forklifts": 0,
        "operator_classifications": 0,
        "independent_classifications": 0,
        "unknown_classifications": 0,
        "interaction_candidates": 0,
        "suppressed_by_operator": 0
    }
    
    start_time = time.time()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        f_idx = stats["frames"] + 1
        video_time_sec = f_idx / 30.0
        
        # A. Detection & Tracking
        res = det_model.track(frame, imgsz=640, conf=0.15, iou=0.70, classes=[0,1], persist=True, tracker="bytetrack.yaml", verbose=False)[0]
        
        persons = []
        forklifts = []
        
        if res.boxes.id is not None:
            for b, cls, trk_id in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy(), res.boxes.id.cpu().numpy()):
                box = [int(v) for v in b]
                cx = (box[0] + box[2]) / 2.0
                fy = box[3]
                obj = {"id": int(trk_id), "class": "person" if int(cls) == 0 else "forklift", "bbox": box, "px": (cx, fy)}
                if obj["class"] == "person":
                    persons.append(obj)
                else:
                    forklifts.append(obj)
        
        # C. Pose Estimation
        # We only run pose if there are tracked persons
        
        if persons:
            pose_res = pose_model.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
            # Match pose keypoints to tracked persons based on bounding box IoU
            for p in persons:
                p_box = p["bbox"]
                best_iou = 0
                best_kpts = None
                
                # pose_res.boxes contains [x1, y1, x2, y2]
                if pose_res.keypoints is not None and len(pose_res.boxes) > 0:
                    for i, box in enumerate(pose_res.boxes.xyxy.cpu().numpy()):
                        # compute iou
                        ix1, iy1 = max(p_box[0], box[0]), max(p_box[1], box[1])
                        ix2, iy2 = min(p_box[2], box[2]), min(p_box[3], box[3])
                        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                        area1 = (p_box[2]-p_box[0])*(p_box[3]-p_box[1])
                        area2 = (box[2]-box[0])*(box[3]-box[1])
                        iou = inter / float(area1 + area2 - inter) if (area1 + area2 - inter) > 0 else 0
                        
                        if iou > 0.5 and iou > best_iou:
                            best_iou = iou
                            # Ultralytics keypoints are shape (N, 17, 2) or (N, 17, 3)
                            # Convert to standard format [17, 3] with confidences
                            kpts = pose_res.keypoints.data.cpu().numpy()[i]
                            # If no conf, append 1.0
                            if kpts.shape[1] == 2:
                                import numpy as np
                                kpts = np.hstack([kpts, np.ones((17, 1))])
                            best_kpts = kpts.tolist()
                            
                p["keypoints"] = best_kpts
        
        # D. Relation Classification
        relations = relation_engine.classify_frame(persons, forklifts, f_idx)
        
        frame_interactions = []
        for p in persons:
            f_dist_list = []
            
            p_rel = relation_engine.get_person_relation(p["id"], None, f_idx) # Get best relation for this person
            
            for f in forklifts:
                # Get exact relation for this pair
                rel = relation_engine.get_person_relation(p["id"], f["id"], f_idx)
                
                # SAFETY INVARIANT: UNKNOWN != SUPPRESS
                if rel == "OPERATOR_ON_VEHICLE":
                    stats["suppressed_by_operator"] += 1
                    continue
                    
                # If INDEPENDENT or UNKNOWN, proceed to evaluate risk
                # Ground Geometry (Risk Engine)
                p_gp = calibrator.pixel_to_world(p["px"])
                f_gp = calibrator.pixel_to_world(f["px"])
                
                if p_gp is not None and f_gp is not None:
                    dist_m = math.hypot(p_gp[0] - f_gp[0], p_gp[1] - f_gp[1])
                    zone = "SAFE"
                    if dist_m <= 1.5: zone = "DANGER"
                    elif dist_m <= 3.0: zone = "CAUTION"
                    
                    if zone != "SAFE":
                        stats["interaction_candidates"] += 1
                        frame_interactions.append({
                            "person_id": p["id"],
                            "forklift_id": f["id"],
                            "distance_meters": round(dist_m, 2),
                            "zone_status": zone,
                            "approach_speed_px_s": 0.0, # Simplification for this test
                            "relation": rel
                        })
                        
        event_engine.process_frame_interactions(f_idx, video_time_sec, frame_interactions)
        
        # Update stats
        stats["frames"] += 1
        stats["persons"] += len(persons)
        stats["forklifts"] += len(forklifts)
        
        for r in relations:
            if r["relation"] == "OPERATOR_ON_VEHICLE": stats["operator_classifications"] += 1
            elif r["relation"] == "INDEPENDENT_PEDESTRIAN": stats["independent_classifications"] += 1
            elif r["relation"] == "UNKNOWN": stats["unknown_classifications"] += 1

        if f_idx % 100 == 0:
            print(f"Processed {f_idx}/{total_frames} frames...")

    event_engine.close_all_events()
    events = event_engine.get_all_events()
    
    elapsed = time.time() - start_time
    
    print("\n==============================================")
    print("  V2.7 EXPERIMENT RESULTS (test2.mp4)")
    print("==============================================")
    print(f"Frames Processed: {stats['frames']} ({elapsed:.1f} sec)")
    print("\nRelation Classification:")
    print(f"  OPERATOR_ON_VEHICLE:    {stats['operator_classifications']}")
    print(f"  INDEPENDENT_PEDESTRIAN: {stats['independent_classifications']}")
    print(f"  UNKNOWN:                {stats['unknown_classifications']}")
    print("\nEvent Engine Output:")
    print(f"  Interaction Candidates Evaluated: {stats['interaction_candidates']}")
    print(f"  Interactions Suppressed by V2.7:  {stats['suppressed_by_operator']}")
    print(f"  Confirmed Danger/Caution Events:  {len(events)}")
    
    # Save events for inspection
    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "v2_7_events.json", "w") as f:
        json.dump(events, f, indent=2)

if __name__ == "__main__":
    run_v2_7()
