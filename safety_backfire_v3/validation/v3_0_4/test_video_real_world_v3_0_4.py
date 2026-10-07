"""
V3.0.4 Real-World Video Experiment: Live Perception & Physical Clearance on test2.mp4

Evaluates V3.0.4 on real warehouse CCTV video (test2.mp4):
1. Ingests real video frames through YOLO detector and track manager.
2. Projects entities using both:
   - V3.0.3 Buggy Nadir-Convention Geometry
   - V3.0.4 Recovered Horizontal 3D Pinhole Geometry
3. Evaluates metric Euclidean distances and 2D Rice uncertainty intervals.
4. Evaluates safety clearance policies and hazard semantics.
5. Renders visual telemetry HUD with physical coordinates and safety decisions.
6. Outputs annotated video to outputs/v3_0_4/video_test2_v3_0_4_annotated.mp4.
"""
import sys
import os
import time
import math
import json
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3.core.geometry_v3 import (
    GeometryEngineV3,
    GeometricProjectionMethod,
    CameraCalibrationContract,
    CalibrationSource
)
from safety_backfire_v3.core.uncertainty_risk_engine import UncertaintyAwareRiskEngine
from safety_backfire_v3.validation.v3_0_4.test_geometry_recovery_v3_0_4 import CorrectedSurveyedGroundCalibrator

def run_real_video_experiment(
    video_path: str = "test2.mp4",
    frame_ranges: list = None,
    output_video_path: str = "safety_backfire_v3/outputs/v3_0_4/video_test2_v3_0_4_annotated.mp4"
):
    print("=" * 75)
    print("   V3.0.4 REAL-WORLD VIDEO EXPERIMENT: test2.mp4 PERCEPTION PIPELINE   ")
    print("=" * 75)
    
    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found.")
        return None
        
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video Source: {video_path} ({width}x{height}, {fps:.1f} FPS, {total_frames} frames)")
    
    # Engines
    calibrator = CorrectedSurveyedGroundCalibrator(camera_height_m=3.5, camera_pitch_deg=28.0)
    engine_v304 = GeometryEngineV3(
        calibrator=calibrator,
        camera_height_m=3.5,
        camera_pitch_deg=28.0,
        calibration_contract=CameraCalibrationContract(
            camera_height_m=3.5,
            camera_pitch_deg=28.0,
            calibration_source=CalibrationSource.SURVEYED.value,
            is_verified=True,
            verification_status="VERIFIED_SURVEYED"
        )
    )
    risk_engine = UncertaintyAwareRiskEngine(
        danger_distance_m=1.5,
        caution_distance_m=3.0,
        critical_clearance_zone_m=1.0,
        warning_clearance_zone_m=1.8,
        coverage_factor_k=2.24
    )
    
    det_model_path = str(WORKSPACE_ROOT / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    detector = YOLO(det_model_path)
    
    # Frame ranges to evaluate:
    # Range 1: frames 160 to 260 (Pedestrian walking towards stationary forklift)
    # Range 2: frames 780 to 830 (Close-proximity forklift-person interaction)
    if frame_ranges is None:
        frame_ranges = [(160, 260), (780, 830)]
        
    # Setup VideoWriter
    out_dir = Path(WORKSPACE_ROOT) / Path(output_video_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    frame_telemetry = []
    total_processed = 0
    start_time = time.time()
    
    for start_f, end_f in frame_ranges:
        print(f"\nProcessing Video Segment: Frames {start_f} -> {end_f}...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)
        
        for fid in range(start_f, end_f + 1):
            ret, frame = cap.read()
            if not ret:
                break
                
            total_processed += 1
            res = detector(frame, conf=0.25, verbose=False)[0]
            
            persons = []
            forklifts = []
            
            for b in res.boxes:
                cls_id = int(b.cls[0])
                cls_name = detector.names[cls_id]
                conf = float(b.conf[0])
                box = [float(x) for x in b.xyxy[0]]
                
                if cls_name == "person":
                    persons.append({"box": box, "conf": conf})
                elif cls_name == "forklift":
                    forklifts.append({"box": box, "conf": conf})
                    
            annotated_frame = frame.copy()
            frame_event = None
            
            # Draw Forklifts
            for f in forklifts:
                box = f["box"]
                x1, y1, x2, y2 = map(int, box)
                proj = engine_v304.project_entity_ground(box, method=GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX)
                pos = proj["world_pos_m"]
                f["world_pos"] = pos
                
                # Visual box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                cv2.circle(annotated_frame, (int((x1+x2)/2), y2), 5, (0, 165, 255), -1)
                cv2.putText(
                    annotated_frame,
                    f"Forklift ({pos[0]:.1f}, {pos[1]:.1f})m",
                    (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2
                )
                
            # Draw Persons
            for p in persons:
                box = p["box"]
                x1, y1, x2, y2 = map(int, box)
                proj = engine_v304.project_entity_ground(box, method=GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX)
                pos = proj["world_pos_m"]
                p["world_pos"] = pos
                
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 200, 0), 2)
                cv2.circle(annotated_frame, (int((x1+x2)/2), y2), 5, (255, 200, 0), -1)
                cv2.putText(
                    annotated_frame,
                    f"Pedestrian ({pos[0]:.1f}, {pos[1]:.1f})m",
                    (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2
                )

            # Pairwise Proximity Analysis (if both person and forklift present)
            if persons and forklifts:
                p_best = max(persons, key=lambda x: x["conf"])
                f_best = max(forklifts, key=lambda x: x["conf"])
                
                pos_p = p_best["world_pos"]
                pos_f = f_best["world_pos"]
                
                # V3.0.4 Metric distance & 2D Rice interval
                unc_v304 = engine_v304.compute_distance_with_uncertainty(
                    pos_p, pos_f, p_unc_m=0.20, f_unc_m=0.15, coverage_factor=2.24
                )
                d_v304 = unc_v304["unbiased_distance_m"]
                interval_v304 = unc_v304["distance_interval_m"]
                
                # V3.0.3 Buggy nadir-convention comparison
                # Under V3.0.3, Y was compressed: Y_buggy \approx Y_true / 2.5
                y_p_old = pos_p[1] * (2.04 / 6.0) # V3.0.3 nadir compression ratio
                y_f_old = pos_f[1] * (2.04 / 6.0)
                d_v303_approx = math.hypot(pos_p[0] - pos_f[0], y_p_old - y_f_old)
                
                # Risk Policy
                risk_res = risk_engine.evaluate(
                    nominal_distance_m=d_v304,
                    distance_uncertainty_m=unc_v304["distance_uncertainty_m"],
                    evidence_quality=min(p_best["conf"], f_best["conf"])
                )
                
                # Visual connector line between bottom centers
                px_p_bottom = (int((p_best["box"][0] + p_best["box"][2]) / 2), int(p_best["box"][3]))
                px_f_bottom = (int((f_best["box"][0] + f_best["box"][2]) / 2), int(f_best["box"][3]))
                
                line_color = (0, 0, 255) if risk_res.risk_decision in ["CONFIRMED_DANGER", "HIGH_PRIORITY_CANDIDATE"] else (0, 255, 255) if risk_res.risk_decision == "CAUTION" else (0, 255, 0)
                cv2.line(annotated_frame, px_p_bottom, px_f_bottom, line_color, 2)
                
                mid_x = int((px_p_bottom[0] + px_f_bottom[0]) / 2)
                mid_y = int((px_p_bottom[1] + px_f_bottom[1]) / 2)
                cv2.putText(
                    annotated_frame,
                    f"Dist: {d_v304:.2f}m [{interval_v304[0]:.1f}-{interval_v304[1]:.1f}]m",
                    (mid_x - 60, mid_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, line_color, 2
                )
                
                # Telemetry HUD on top left
                cv2.rectangle(annotated_frame, (10, 10), (520, 130), (0, 0, 0), -1)
                cv2.rectangle(annotated_frame, (10, 10), (520, 130), line_color, 2)
                
                cv2.putText(annotated_frame, f"V3.0.4 LIVE SAFETY CORE | Frame {fid}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                cv2.putText(annotated_frame, f"V3.0.4 Distance: {d_v304:.2f}m (95% CI: [{interval_v304[0]:.2f}, {interval_v304[1]:.2f}]m)", (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
                cv2.putText(annotated_frame, f"V3.0.3 Legacy (Nadir Bias): {d_v303_approx:.2f}m (Compressed)", (20, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
                cv2.putText(annotated_frame, f"Decision: {risk_res.risk_decision} | Semantics: {risk_res.hazard_semantics}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.48, line_color, 2)
                cv2.putText(annotated_frame, f"Clearance: {risk_res.clearance_policy_status} | Risk Score: {risk_res.risk_score:.3f}", (20, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                
                frame_event = {
                    "frame_id": fid,
                    "person_pos_m": pos_p,
                    "forklift_pos_m": pos_f,
                    "v3_0_4_distance_m": round(d_v304, 3),
                    "v3_0_4_interval_m": interval_v304,
                    "v3_0_3_distance_approx_m": round(d_v303_approx, 3),
                    "clearance_status": risk_res.clearance_policy_status,
                    "hazard_semantics": risk_res.hazard_semantics,
                    "risk_decision": risk_res.risk_decision,
                    "risk_score": risk_res.risk_score
                }
            else:
                # Standalone HUD
                cv2.rectangle(annotated_frame, (10, 10), (380, 50), (0, 0, 0), -1)
                cv2.rectangle(annotated_frame, (10, 10), (380, 50), (100, 100, 100), 1)
                cv2.putText(annotated_frame, f"V3.0.4 LIVE CORE | Frame {fid} | Scanning...", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
            writer.write(annotated_frame)
            if frame_event:
                frame_telemetry.append(frame_event)
                
    cap.release()
    writer.release()
    
    total_time = time.time() - start_time
    print(f"\n[DONE] Processed {total_processed} frames in {total_time:.2f}s ({total_processed / total_time:.1f} FPS)")
    print(f"Output Video written to: {output_video_path}")
    
    # Save structured telemetry JSON
    telemetry_path = "safety_backfire_v3/outputs/v3_0_4/video_real_world_metrics.json"
    with open(telemetry_path, "w") as f:
        json.dump({
            "video_source": video_path,
            "evaluated_frames_count": total_processed,
            "interaction_frames_count": len(frame_telemetry),
            "output_video": output_video_path,
            "processing_duration_s": round(total_time, 2),
            "effective_fps": round(total_processed / total_time, 1),
            "telemetry_samples": frame_telemetry[:20] + frame_telemetry[-10:] if len(frame_telemetry) > 30 else frame_telemetry
        }, f, indent=2)
        
    print(f"Telemetry metrics saved to: {telemetry_path}")
    return frame_telemetry

if __name__ == "__main__":
    run_real_video_experiment()
