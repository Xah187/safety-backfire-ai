import sys
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from core.geometry import GroundPlaneCalibrator, compute_metric_distance
from core.kinematics import compute_metric_ttc
from core.event_engine import EventEngine
from core.trajectory import TrajectoryEngine
from core.risk_engine import RiskEngine

def render_video():
    print("=== Generating Annotated V2.1 Video ===")
    
    model_path = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
    video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "safety_backfire_v08/test.mp4"
    
    out_name = video_path.stem + "_v2_1_annotated.mp4"
    output_path = ROOT / out_name
    
    model = YOLO(str(model_path))
    cap = cv2.VideoCapture(str(video_path))
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    calibrator = GroundPlaneCalibrator()
    trajectory_engine = TrajectoryEngine()
    event_engine = EventEngine()
    
    # Ground plane visualization points (the unwarped src polygon)
    src_pts = np.array(calibrator.src_pts, np.int32)
    src_pts = src_pts.reshape((-1, 1, 2))
    
    frame_idx = 0
    tracking_failures = 0
    
    for result in model.track(
        source=str(video_path),
        stream=True,
        persist=True,
        tracker="bytetrack.yaml",
        imgsz=960,
        conf=0.08,
        iou=0.70,
        device="cpu",
        classes=[0, 1],
        verbose=False
    ):
        frame_idx += 1
        timestamp = frame_idx / fps
        frame = result.orig_img.copy()
        boxes = result.boxes
        
        # 1. Draw Calibrated Ground Plane Zone
        cv2.polylines(frame, [src_pts], True, (255, 255, 0), 2)
        cv2.putText(frame, "Calibrated Ground Plane", (int(calibrator.src_pts[0][0]), int(calibrator.src_pts[0][1]) - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        global_status = "NO_DETECTIONS"
        global_color = (100, 100, 100)
        
        if boxes is None or len(boxes) == 0:
            tracking_failures += 1
            event_engine.process_frame_interactions(frame_idx, timestamp, [])
            global_status = "TRACKING_LOST / NO_DETECTIONS"
            global_color = (0, 0, 255) # Red for lost
        else:
            global_status = "SAFE"
            global_color = (0, 255, 0)
            
            ids = boxes.id
            xyxy = boxes.xyxy.cpu().numpy()
            clss = boxes.cls.cpu().numpy().astype(int)
            
            persons = []
            forklifts = []
            
            # Process detections
            for i, cls_id in enumerate(clss):
                tid = int(ids[i].item()) if ids is not None and ids[i] is not None else None
                if tid is None: continue
                
                box = [int(v) for v in xyxy[i]]
                c_name = model.names[int(cls_id)]
                
                cx = (box[0] + box[2]) / 2.0
                foot_y = box[3]
                
                # Draw standard bbox
                color = (255, 150, 0) if c_name == "forklift" else (0, 200, 255)
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(frame, f"{c_name} ID:{tid}", (box[0], box[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Plot ground point
                cv2.circle(frame, (int(cx), int(foot_y)), 5, (0, 0, 255), -1)
                
                # Map to world
                world_pt = calibrator.pixel_to_world((cx, foot_y))
                
                if world_pt is None: 
                    cv2.putText(frame, "OUT_OF_BOUNDS", (box[0], box[3]+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    continue
                    
                # Update trajectory to get velocity
                trajectory_engine.update(tid, c_name, timestamp, world_pt[0], world_pt[1], "SAFE")
                traj = trajectory_engine.get_trajectory(tid)
                
                vel = (0.0, 0.0)
                if traj and traj.points and traj.points[-1].velocity_m_s is not None:
                    speed = traj.points[-1].velocity_m_s
                    dir_rad = traj.points[-1].direction_deg * (3.14159/180.0)
                    import math
                    vel = (speed * math.cos(dir_rad), speed * math.sin(dir_rad))
                    
                entity = {"id": tid, "box": box, "cx": cx, "cy": foot_y, "pos": world_pt, "vel": vel, "c_name": c_name}
                
                if c_name == "person":
                    persons.append(entity)
                elif c_name == "forklift":
                    forklifts.append(entity)
                    
            # Interactions
            frame_interactions = []
            
            for p in persons:
                for f in forklifts:
                    geo_res = compute_metric_distance(p["pos"], f["pos"], calibrator)
                    if geo_res["calibration_status"] != "VALID": continue
                    
                    dist_m = geo_res["distance_m"]
                    ttc_res = compute_metric_ttc(p["pos"], f["pos"], p["vel"], f["vel"], dist_m)
                    
                    if dist_m < 1.5:
                        zone = "DANGER"
                        global_status = "POTENTIAL_NEAR_MISS"
                        global_color = (0, 0, 255) # Red
                    elif dist_m < 3.0:
                        zone = "CAUTION"
                        if global_status != "POTENTIAL_NEAR_MISS":
                            global_status = "PROXIMITY_CAUTION"
                            global_color = (0, 165, 255) # Orange
                    else:
                        zone = "SAFE"
                        
                    # Risk score is calculated per-event in V2, not per-frame
                    risk_score = 0.0
                    
                    # Draw Line between them
                    cv2.line(frame, (int(p["cx"]), int(p["cy"])), (int(f["cx"]), int(f["cy"])), (255, 255, 255), 2)
                    
                    # Draw Metric Info
                    mid_x = int((p["cx"] + f["cx"]) / 2)
                    mid_y = int((p["cy"] + f["cy"]) / 2)
                    
                    ttc_str = f"TTC: {ttc_res['ttc_sec']}s" if ttc_res['ttc_sec'] is not None else "TTC: NULL"
                    dist_str = f"Dist: {dist_m:.2f}m"
                    
                    # Text shadow for visibility
                    cv2.putText(frame, dist_str, (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 4)
                    cv2.putText(frame, dist_str, (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
                    
                    cv2.putText(frame, ttc_str, (mid_x, mid_y+25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 4)
                    cv2.putText(frame, ttc_str, (mid_x, mid_y+25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
                    
                    frame_interactions.append({
                        "person_id": p["id"],
                        "forklift_id": f["id"],
                        "distance_meters": dist_m,
                        "approach_speed_px_s": ttc_res["relative_velocity_m_s"],
                        "zone_status": zone,
                        "risk_exposure_score": risk_score
                    })
                    
            event_engine.process_frame_interactions(frame_idx, timestamp, frame_interactions)
            
        # Draw Global Engine Status Panel
        cv2.rectangle(frame, (10, 10), (550, 100), (0,0,0), -1)
        cv2.putText(frame, "V2.1 Engine Live Metrics", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        cv2.putText(frame, f"Frame: {frame_idx}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
        
        # In frames 190-230, detection drops out. The engine should reflect INSUFFICIENT_EVIDENCE locally.
        if global_status == "TRACKING_LOST / NO_DETECTIONS":
            cv2.putText(frame, f"Status: {global_status}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        else:
            cv2.putText(frame, f"Status: {global_status}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, global_color, 2)
            
        out.write(frame)
        
    cap.release()
    out.release()
    print(f"Video saved to {output_path}")

if __name__ == "__main__":
    render_video()
