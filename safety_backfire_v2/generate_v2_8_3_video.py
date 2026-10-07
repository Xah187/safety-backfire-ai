import sys
import cv2
import time
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from ultralytics import YOLO
from core.geometry import load_default_calibrator
from core.operator_relation_v2 import OperatorVehicleRelationEngineV2
from core.event_engine_v2 import EventEngineV2
from core.track_manager import TrackManager, TrackState

def generate_video():
    print("=== Generating V2.8.3 Visual Output ===")
    
    video_path = str(ROOT.parent / "test2.mp4")
    model_path = str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    
    # OUTPUT PATH (Saving directly to artifacts folder for easy viewing)
    artifact_dir = Path("/Users/xah187/.gemini/antigravity-ide/brain/2047d700-61e0-4839-9e14-d00ab00f0e92")
    output_path = str(artifact_dir / "test2_v2_8_3_output.mp4")
    
    print("Loading Models...")
    det_model = YOLO(model_path)
    pose_model = YOLO("yolov8n-pose.pt")
    
    calibrator = load_default_calibrator()
    track_manager = TrackManager(strong_conf_threshold=0.35, max_prediction_frames=5)
    relation_engine = OperatorVehicleRelationEngineV2()
    event_engine = EventEngineV2(max_gap_frames=15)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    
    print(f"\nProcessing {total_frames} frames into {output_path}...")
    
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        frame_idx += 1
        video_time_sec = frame_idx / fps
        
        # A. Detection & Tracking
        res = det_model.track(frame, imgsz=640, conf=0.15, iou=0.70, classes=[0,1], persist=True, tracker="bytetrack.yaml", verbose=False)[0]
        
        persons, forklifts = [], []
        all_tracked_for_drawing = []
        
        if res.boxes.id is not None:
            all_objects = []
            for b, cls, trk_id, conf in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy(), res.boxes.id.cpu().numpy(), res.boxes.conf.cpu().numpy()):
                box = [int(v) for v in b]
                cx, fy = (box[0] + box[2]) / 2.0, box[3]
                all_objects.append({
                    "id": int(trk_id), 
                    "class": "person" if int(cls) == 0 else "forklift", 
                    "bbox": box, 
                    "px": (cx, fy),
                    "conf": float(conf)
                })
            
            # Pass through TrackManager
            valid_objects = track_manager.process_tracks(frame_idx, video_time_sec, all_objects, calibrator)
            for obj in valid_objects:
                persons.append(obj) if obj["class"] == "person" else forklifts.append(obj)
                
            # Keep stale objects only for drawing (grayed out)
            all_tracked_for_drawing = all_objects
        
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
                                kpts = np.hstack([kpts, np.ones((17, 1))])
                            best_kpts = kpts.tolist()
                p["keypoints"] = best_kpts
        
        # C. Relation Classification
        relation_engine.classify_frame(persons, forklifts, frame_idx)
        
        # D. Interaction Generation
        frame_interactions = []
        for p in persons:
            for f in forklifts:
                rel = relation_engine.get_person_relation(p["id"], f["id"], frame_idx)
                if not rel: rel = "UNKNOWN"
                
                p_gp = calibrator.pixel_to_world(p["px"])
                f_gp = calibrator.pixel_to_world(f["px"])
                
                if p_gp is not None and f_gp is not None:
                    dist_m = math.hypot(p_gp[0] - f_gp[0], p_gp[1] - f_gp[1])
                    zone = "SAFE"
                    if dist_m <= 1.5: zone = "DANGER"
                    elif dist_m <= 3.0: zone = "CAUTION"
                    
                    if zone != "SAFE" or rel == "OPERATOR_ON_VEHICLE":
                        frame_interactions.append({
                            "person_id": p["id"],
                            "forklift_id": f["id"],
                            "distance_meters": dist_m,
                            "zone_status": zone,
                            "relation": rel
                        })
                        
        event_engine.process_frame_interactions(frame_idx, video_time_sec, frame_interactions)
        
        # E. VISUALIZATION
        
        # Draw ALL tracked objects (including STALE) for debugging
        for obj in all_tracked_for_drawing:
            x1, y1, x2, y2 = obj["bbox"]
            t_state = obj.get("track_state", TrackState.OBSERVED)
            
            if t_state == TrackState.STALE:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (100, 100, 100), 1)
                cv2.putText(frame, f"STALE {obj['id']}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
                continue
                
            # Thickness based on prediction
            thickness = 2 if t_state == TrackState.OBSERVED else 1
            
            if obj["class"] == "forklift":
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), thickness)
                cv2.putText(frame, f"FL {obj['id']} {t_state[:3]}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), thickness)
            else:
                p = obj
                rel = relation_engine.get_person_relation(p["id"], -1, frame_idx)
                active_event = None
                for pair_key, evt in event_engine.active_events.items():
                    if evt.person_id == p["id"]:
                        active_event = evt
                        break
                        
                color = (255, 255, 255) # Default White (UNKNOWN)
                label = f"P{p['id']} UNKNOWN {t_state[:3]}"
                
                if active_event:
                    if active_event.relation_state == "OPERATOR_ON_VEHICLE":
                        color = (255, 255, 0) # Cyan for operator
                        label = f"P{p['id']} OPERATOR {t_state[:3]}"
                    elif active_event.relation_state == "INDEPENDENT_PEDESTRIAN":
                        color = (0, 0, 255) # Red for pedestrian
                        label = f"P{p['id']} PEDESTRIAN {t_state[:3]}"
                        
                    e_state = active_event.event_state
                    a_state = active_event.alert_state
                    dist_str = f"{active_event.smoothed_distance_m:.1f}m" if active_event.smoothed_distance_m else ""
                    ttc_str = f"TTC:{active_event.promotion_evidence.get('ttc', 'N/A')}s" if active_event.promotion_evidence else ""
                    
                    info = f"{e_state} | {a_state} | {dist_str} | {ttc_str}"
                    cv2.putText(frame, info, (x1, y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, thickness)
                
                # Draw Pose
                if p.get("keypoints"):
                    for kpt in p["keypoints"]:
                        if kpt[2] > 0.5:
                            cv2.circle(frame, (int(kpt[0]), int(kpt[1])), 3, (255, 0, 255), -1)

        # Write frame info
        cv2.putText(frame, f"V2.8.3 Track Integrity | Frame: {frame_idx}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        
        out.write(frame)
        
        if frame_idx % 200 == 0:
            print(f"Rendered {frame_idx}/{total_frames} frames...")

    cap.release()
    out.release()
    print(f"\nDone! Video saved to: {output_path}")

if __name__ == "__main__":
    generate_video()
