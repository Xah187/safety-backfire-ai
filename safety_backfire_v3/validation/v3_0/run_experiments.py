"""
V3.0 Core — Controlled Experimental Isolation Runner

Executes Experiments A through F independently against BASELINE_V2_9:
  - Baseline: Frozen V2.9 architecture (Sequential, Raw Tracks, Method A Geometry)
  - Experiment A: Async Live only (Decoupled Pose @ 8 Hz, Raw Tracks, Method A)
  - Experiment B: Identity/ReID only (Sequential, Durable Identity, Method A)
  - Experiment C: Geometry only (Sequential, Raw Tracks, Method E 3D Offset)
  - Experiment D: Async + Identity (Decoupled Pose @ 8 Hz, Durable Identity, Method A)
  - Experiment E: Async + Geometry (Decoupled Pose @ 8 Hz, Raw Tracks, Method E)
  - Experiment F: Full Candidate Architecture (Decoupled Pose @ 8 Hz, Durable Identity, Method E)

Evaluates on identical video inputs:
  - test2.mp4 (Forklift interaction & pedestrian crossings)
  - test.mp4 (Warehouse pedestrian motion)

Outputs complete structured JSON to safety_backfire_v3/outputs/v3_0_experiment_comparison.json
"""
import sys
import time
import json
import math
import platform
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import cv2
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
_V2_PATH = WORKSPACE_ROOT / "safety_backfire_v2"
if str(_V2_PATH) not in sys.path:
    sys.path.insert(0, str(_V2_PATH))

from safety_backfire_v3.core.async_ingest import FramePacket
from safety_backfire_v3.core.async_pipeline import AsyncLivePipeline
from safety_backfire_v3.core.geometry_v3 import GeometricProjectionMethod

DET_WEIGHTS = str(WORKSPACE_ROOT / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
POSE_WEIGHTS = str(WORKSPACE_ROOT / "safety_backfire_v2/yolov8n-pose.pt")

def run_pipeline_experiment(
    exp_name: str,
    video_path: str,
    max_frames: int = 300,
    start_frame: int = 500,
    pose_mode: str = "async_decoupled",
    pose_target_hz: float = 8.0,
    enable_identity_reid: bool = True,
    geometry_method: str = GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET
) -> Dict[str, Any]:
    print(f"\n=======================================================")
    print(f"   RUNNING: {exp_name}")
    print(f"   Pose Mode: {pose_mode} ({pose_target_hz}Hz), ReID: {enable_identity_reid}, Geo: {geometry_method}")
    print(f"=======================================================")
    
    cap = cv2.VideoCapture(video_path)
    total_vid_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    
    pipeline = AsyncLivePipeline(
        detector_weights=DET_WEIGHTS,
        pose_weights=POSE_WEIGHTS,
        pose_target_hz=pose_target_hz,
        pose_mode=pose_mode,
        enable_identity_reid=enable_identity_reid,
        geometry_method=geometry_method,
        max_queue_size=10,
        max_allowed_frame_age_ms=250.0
    )
    
    if pose_mode == "async_decoupled":
        pipeline.start()

    # Seek to start_frame if requested
    if start_frame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
    processed_count = 0
    start_wall_time = time.time()
    current_frame_id = start_frame
    
    frames_to_process = min(max_frames, total_vid_frames - start_frame)
    
    while processed_count < frames_to_process:
        ret, frame = cap.read()
        if not ret:
            break
            
        current_frame_id += 1
        t_src = current_frame_id / video_fps
        t_cap = start_wall_time + (processed_count / video_fps)
        
        packet = FramePacket(
            frame_id=current_frame_id,
            frame=frame,
            source_timestamp=t_src,
            capture_timestamp=t_cap
        )
        
        pipeline.process_frame_packet(packet)
        processed_count += 1
        if processed_count % 50 == 0:
            print(f"    [{exp_name}] Processed {processed_count}/{frames_to_process} frames...")
            
    cap.release()
    total_time_s = time.time() - start_wall_time
    effective_fps = processed_count / total_time_s if total_time_s > 0 else 0.0
    
    if pose_mode == "async_decoupled":
        pipeline.stop()
    else:
        pipeline.event_engine.close_all_events()

    # Telemetry and Statistics
    percentiles = pipeline.get_latency_percentiles()
    events = pipeline.event_engine.get_all_events()
    confirmed_events = pipeline.event_engine.get_confirmed_events()
    
    # Calculate track fragmentation (number of track IDs per durable entity)
    lineage_lengths = []
    for ent in pipeline.identity_layer.entities.values():
        lineage_lengths.append(len(ent.track_id_lineage))
    mean_lineage = float(np.mean(lineage_lengths)) if lineage_lengths else 1.0
    max_lineage = int(np.max(lineage_lengths)) if lineage_lengths else 1
    
    min_dist = None
    for ev in events:
        if ev.get("min_distance_m") is not None:
            if min_dist is None or ev["min_distance_m"] < min_dist:
                min_dist = ev["min_distance_m"]

    result = {
        "experiment": exp_name,
        "frames_evaluated": processed_count,
        "total_time_s": round(total_time_s, 2),
        "overall_fps": round(effective_fps, 2),
        "percentiles_ms": percentiles,
        "pose_mode": pose_mode,
        "pose_target_hz": pose_target_hz,
        "enable_identity_reid": enable_identity_reid,
        "geometry_method": geometry_method,
        "total_entities_spawned": len(pipeline.identity_layer.entities),
        "total_events_recorded": len(events),
        "confirmed_events_count": len(confirmed_events),
        "mean_track_lineage_per_entity": round(mean_lineage, 2),
        "max_track_lineage_per_entity": max_lineage,
        "min_encounter_distance_m": round(min_dist, 3) if min_dist else None,
        "events_summary": [
            {
                "event_id": ev["event_id"],
                "person_entity_id": ev.get("person_entity_id"),
                "forklift_entity_id": ev.get("forklift_entity_id"),
                "duration_sec": ev.get("duration_sec"),
                "min_distance_m": ev.get("min_distance_m"),
                "event_state": ev.get("event_state"),
                "track_pair_lineage": ev.get("track_pair_lineage")
            }
            for ev in events
        ]
    }
    
    print(f"  --> COMPLETED {exp_name}: {effective_fps:.1f} FPS, {len(events)} events, P50 E2E: {percentiles['end_to_end_ms']['P50']}ms")
    return result


def run_full_experimental_matrix():
    print("=================================================================")
    print("   V3.0 CORE: EXECUTING FULL EXPERIMENTAL MATRIX (A THROUGH F)   ")
    print("=================================================================")
    
    video2 = str(WORKSPACE_ROOT / "test2.mp4")
    # Evaluate across a dense 250-frame window (frames 550 to 800) containing the critical
    # pedestrian crossing, forklift close encounters, and ByteTrack ID switches.
    start_f = 550
    eval_frames = 250
    
    experiments_plan = [
        # Baseline V2.9
        {
            "name": "BASELINE_V2_9",
            "pose_mode": "sequential_continuous",
            "pose_target_hz": 25.0,
            "enable_identity_reid": False,
            "geometry_method": GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX
        },
        # Experiment A: Async only
        {
            "name": "EXPERIMENT_A_ASYNC_ONLY",
            "pose_mode": "async_decoupled",
            "pose_target_hz": 8.0,
            "enable_identity_reid": False,
            "geometry_method": GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX
        },
        # Experiment B: Identity only
        {
            "name": "EXPERIMENT_B_IDENTITY_ONLY",
            "pose_mode": "sequential_continuous",
            "pose_target_hz": 25.0,
            "enable_identity_reid": True,
            "geometry_method": GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX
        },
        # Experiment C: Geometry only
        {
            "name": "EXPERIMENT_C_GEOMETRY_ONLY",
            "pose_mode": "sequential_continuous",
            "pose_target_hz": 25.0,
            "enable_identity_reid": False,
            "geometry_method": GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET
        },
        # Experiment D: Async + Identity
        {
            "name": "EXPERIMENT_D_ASYNC_IDENTITY",
            "pose_mode": "async_decoupled",
            "pose_target_hz": 8.0,
            "enable_identity_reid": True,
            "geometry_method": GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX
        },
        # Experiment E: Async + Geometry
        {
            "name": "EXPERIMENT_E_ASYNC_GEOMETRY",
            "pose_mode": "async_decoupled",
            "pose_target_hz": 8.0,
            "enable_identity_reid": False,
            "geometry_method": GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET
        },
        # Experiment F: Full Candidate Architecture
        {
            "name": "EXPERIMENT_F_FULL_CANDIDATE",
            "pose_mode": "async_decoupled",
            "pose_target_hz": 8.0,
            "enable_identity_reid": True,
            "geometry_method": GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET
        }
    ]
    
    all_results = {}
    
    for plan in experiments_plan:
        res = run_pipeline_experiment(
            exp_name=plan["name"],
            video_path=video2,
            max_frames=eval_frames,
            start_frame=start_f,
            pose_mode=plan["pose_mode"],
            pose_target_hz=plan["pose_target_hz"],
            enable_identity_reid=plan["enable_identity_reid"],
            geometry_method=plan["geometry_method"]
        )
        all_results[plan["name"]] = res
        
    # Write summary snapshot
    out_dir = WORKSPACE_ROOT / "safety_backfire_v3/outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "v3_0_experiment_comparison.json"
    
    snapshot_payload = {
        "metadata": {
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "video_source": "test2.mp4 (frames 550-800)",
            "total_frames_evaluated_per_exp": eval_frames,
            "python_version": sys.version.split()[0],
            "os": f"{platform.system()} {platform.release()} ({platform.machine()})"
        },
        "experiments": all_results
    }
    
    with open(out_path, "w") as f:
        json.dump(snapshot_payload, f, indent=2)
        
    print(f"\nSuccessfully executed all 7 experimental conditions!")
    print(f"Results saved to: {out_path}")
    return snapshot_payload

if __name__ == "__main__":
    run_full_experimental_matrix()
