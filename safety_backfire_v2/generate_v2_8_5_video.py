"""
V2.8.5 — Video Generation with Correct Class Mapping & Motion-Aware Semantic Badges

Correctly maps YOLO classes:
  0 -> forklift
  1 -> person

Features:
- Distinguishes MOVING FORKLIFT (speed > 0.25 m/s) from PARKED FORKLIFT (speed <= 0.25 m/s)
- Identifies person driving the moving forklift as OPERATOR ON MOVING FORKLIFT (Cyan)
- Preserves independent pedestrians (Red)
- Displays pose keypoints on real persons
- Actively blocks false ghosts at the Observation Gate with explanations
- Suppresses false operator-vs-parked-forklift interactions
"""
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
from core.observation_gate import ObservationValidity, ObservationIntegrityGate

def generate_v2_8_5_video():
    print("=== Generating V2.8.5 Visual Output (Corrected Class Mapping & Motion Awareness) ===")
    
    video_path = str(ROOT.parent / "test2.mp4")
    model_path = str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    
    artifact_dir = Path("/Users/xah187/.gemini/antigravity-ide/brain/2047d700-61e0-4839-9e14-d00ab00f0e92")
    output_path = str(artifact_dir / "test2_v2_8_5_output.mp4")
    scratch_dir = artifact_dir / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading Models...")
    det_model = YOLO(model_path)
    pose_model = YOLO("yolov8n-pose.pt")
    
    print(f"Detector Class Names: {det_model.names}")
    
    calibrator = load_default_calibrator()
    track_manager = TrackManager(strong_conf_threshold=0.35, max_prediction_frames=5)
    relation_engine = OperatorVehicleRelationEngineV2()
    event_engine = EventEngineV2(max_gap_frames=15)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    
    print(f"\nProcessing {total_frames} frames into {output_path}...")
    start_time = time.time()
    
    frame_idx = 0
    saved_sample_frames = [200, 540, 545, 800, 1140, 1210]
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_idx += 1
        video_time_sec = frame_idx / fps
        
        # A. Detection & Tracking
        res = det_model.track(frame, imgsz=640, conf=0.15, iou=0.70, classes=[0,1], persist=True, tracker="bytetrack.yaml", verbose=False)[0]
        
        all_tracked_for_drawing = []
        if res.boxes.id is not None:
            for b, cls, trk_id, conf in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy(), res.boxes.id.cpu().numpy(), res.boxes.conf.cpu().numpy()):
                box = [int(v) for v in b]
                cx, fy = (box[0] + box[2]) / 2.0, box[3]
                # CRITICAL: Correct class mapping from model.names
                class_name = det_model.names[int(cls)]
                all_tracked_for_drawing.append({
                    "id": int(trk_id), 
                    "class": class_name, 
                    "bbox": box, 
                    "px": (cx, fy),
                    "conf": float(conf)
                })
                
        # B. Pose Estimation for all Person Candidates
        if all_tracked_for_drawing:
            pose_res = pose_model.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
            for p in all_tracked_for_drawing:
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
                
        # C. TrackManager + Multi-Cue ObservationIntegrityGate + Motion Tracking
        persons, forklifts = [], []
        if all_tracked_for_drawing:
            valid_objects = track_manager.process_tracks(frame_idx, video_time_sec, all_tracked_for_drawing, calibrator)
            for obj in valid_objects:
                if obj.get("safety_eligible", False):
                    if obj["class"] == "person":
                        persons.append(obj)
                    else:
                        forklifts.append(obj)
                        
        # D. Relation Classification
        relation_engine.classify_frame(persons, forklifts, frame_idx)
        
        # E. Proximity & Interaction Analysis
        frame_interactions = []
        for p in persons:
            p_rel = relation_engine.get_person_relation(p["id"], -1, frame_idx) or "UNKNOWN"
            p_is_op = (p_rel == "OPERATOR_ON_VEHICLE")
            
            for f in forklifts:
                f_is_moving = f.get("is_moving", False)
                rel = relation_engine.get_person_relation(p["id"], f["id"], frame_idx) or "UNKNOWN"
                
                # Rule: An operator on a moving vehicle passing a parked, empty forklift
                # is normal warehouse traffic, NOT a pedestrian safety incident!
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
        
        # F. VISUAL OVERLAYS RENDERING
        # 1. Header Bar
        cv2.rectangle(frame, (0, 0), (w, 65), (20, 20, 25), -1)
        cv2.putText(frame, "SAFETY BACKFIRE V2.8.5 | OPERATOR & FORKLIFT VERIFICATION", (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame: {frame_idx:04d}/{total_frames} | Time: {video_time_sec:05.2f}s | Active Events: {len(event_engine.active_events)}", 
                    (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 220, 255), 1)

        # 2. Render Objects
        for obj in all_tracked_for_drawing:
            x1, y1, x2, y2 = obj["bbox"]
            t_state = obj.get("track_state", TrackState.OBSERVED)
            validity = obj.get("observation_validity", ObservationValidity.VALID)
            eligible = obj.get("safety_eligible", False)
            speed = obj.get("speed_m_s", 0.0)
            is_moving = obj.get("is_moving", False)
            
            # Stale / expired tracks are dropped cleanly from the view
            if t_state == TrackState.STALE:
                continue
                
            # --- BLOCKED GHOST (REJECTED BY GATE) ---
            if validity == ObservationValidity.INVALID:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (40, 40, 180), 1)
                badge = f"GHOST {obj['class'].upper()} {obj['id']} | BLOCKED"
                cv2.putText(frame, badge, (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (60, 60, 240), 1)
                reason_short = obj.get("reason", "")[:35]
                if reason_short:
                    cv2.putText(frame, reason_short, (x1, min(h - 5, y2 + 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80, 80, 200), 1)
                continue
                
            # --- FORKLIFTS ---
            thickness = 2 if t_state == TrackState.OBSERVED else 1
            if obj["class"] == "forklift":
                if is_moving:
                    fl_color = (0, 255, 0) # Bright Green for Moving Forklift
                    fl_label = f"MOVING FORKLIFT {obj['id']} [{speed:.1f} m/s]"
                else:
                    fl_color = (200, 160, 50) # Slate/Steel Blue for Parked/Static Forklift
                    fl_label = f"PARKED FORKLIFT {obj['id']} [STATIC]"
                    
                cv2.rectangle(frame, (x1, y1), (x2, y2), fl_color, thickness)
                cv2.putText(frame, fl_label, (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, fl_color, thickness)
                
            # --- PERSONS ---
            else:
                p = obj
                rel = relation_engine.get_person_relation(p["id"], -1, frame_idx) or "UNKNOWN"
                
                # Verified operator relation
                is_riding_vehicle = (rel == "OPERATOR_ON_VEHICLE")
                
                active_event = None
                for pair_key, evt in event_engine.active_events.items():
                    if evt.person_id == p["id"]:
                        active_event = evt
                        break
                        
                # Semantic Color & Badge
                if is_riding_vehicle:
                    color = (255, 230, 0) # Cyan for Operator
                    status_label = f"OPERATOR P{p['id']} [MOVING FORKLIFT] ({speed:.1f} m/s)"
                elif rel == "INDEPENDENT_PEDESTRIAN":
                    color = (0, 0, 255) # Red for Pedestrian
                    status_label = f"PEDESTRIAN P{p['id']} [{validity}]"
                else: # UNKNOWN / Standalone
                    color = (0, 215, 255) if validity == "WEAK" else (255, 255, 255)
                    status_label = f"PERSON P{p['id']} [{validity}]"
                    
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                cv2.putText(frame, status_label, (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.52, color, thickness)
                
                # Active Event Sub-badge
                if active_event:
                    e_state = active_event.event_state
                    dist_str = f"{active_event.smoothed_distance_m:.1f}m" if active_event.smoothed_distance_m else ""
                    ttc_str = f"TTC:{active_event.promotion_evidence.get('ttc', 'inf')}s" if active_event.promotion_evidence else ""
                    info_text = f"{e_state} | {dist_str} {ttc_str}"
                    cv2.putText(frame, info_text, (x1, min(h - 8, y2 + 18)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
                    
                # Draw visible pose keypoints (Magenta circles) on the human body
                if p.get("keypoints"):
                    for kpt in p["keypoints"]:
                        if len(kpt) >= 3 and kpt[2] > 0.4:
                            cv2.circle(frame, (int(kpt[0]), int(kpt[1])), 3, (255, 0, 255), -1)

        # Bottom HUD Legend
        cv2.rectangle(frame, (0, h - 30), (w, h), (20, 20, 25), -1)
        legend = "LEGEND: [GREEN: Moving Forklift]  [SLATE: Parked Forklift]  [CYAN: Operator on Moving Forklift]  [RED: Pedestrian]  [BURGUNDY: Blocked Ghost]"
        cv2.putText(frame, legend, (20, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)

        out.write(frame)
        
        # Save sample key frames for direct visual inspection in the IDE
        if frame_idx in saved_sample_frames:
            sample_img_path = scratch_dir / f"v2_8_5_frame_{frame_idx:04d}.jpg"
            cv2.imwrite(str(sample_img_path), frame)
            print(f"Saved sample frame inspection image to: {sample_img_path}")
            
        if frame_idx % 250 == 0 or frame_idx == total_frames:
            elapsed = time.time() - start_time
            fps_proc = frame_idx / elapsed if elapsed > 0 else 0
            print(f"Processed {frame_idx}/{total_frames} frames ({fps_proc:.1f} FPS)...")

    cap.release()
    out.release()
    total_elapsed = time.time() - start_time
    print(f"\nSuccessfully generated V2.8.5 video in {total_elapsed:.1f}s!")
    print(f"Video saved at: {output_path}")

if __name__ == "__main__":
    generate_v2_8_5_video()
