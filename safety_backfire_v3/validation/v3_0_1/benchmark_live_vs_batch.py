"""
V3.0.1 Validation — Corrected Benchmark Methodology: Batch vs Sustained Live

Separates:
1. BATCH BENCHMARK (Unconstrained offline throughput)
2. SUSTAINED LIVE BENCHMARK (Throttled real-time streaming at 25.0 FPS source rate)

Outputs structured comparison JSON to safety_backfire_v3/outputs/v3_0_1/benchmark_live_vs_batch.json
"""
import sys
import time
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional
import cv2
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
_V2_PATH = WORKSPACE_ROOT / "safety_backfire_v2"
if str(_V2_PATH) not in sys.path:
    sys.path.insert(0, str(_V2_PATH))

from safety_backfire_v3.core.async_ingest import FramePacket, BoundedFrameQueue, FreshnessPolicy
from safety_backfire_v3.core.async_pipeline import AsyncLivePipeline
from safety_backfire_v3.core.geometry_v3 import GeometricProjectionMethod

DET_WEIGHTS = str(WORKSPACE_ROOT / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
POSE_WEIGHTS = str(WORKSPACE_ROOT / "safety_backfire_v2/yolov8n-pose.pt")
VIDEO_PATH = str(WORKSPACE_ROOT / "test2.mp4")


def run_batch_benchmark(n_frames: int = 150) -> Dict[str, Any]:
    print("\n=======================================================")
    print(f"   EXECUTING BATCH BENCHMARK ({n_frames} frames, unconstrained)")
    print("=======================================================")
    
    # 1. Baseline V2.9 Sequential Mode
    cap = cv2.VideoCapture(VIDEO_PATH)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 550)
    
    pipe_baseline = AsyncLivePipeline(
        detector_weights=DET_WEIGHTS, pose_weights=POSE_WEIGHTS,
        pose_target_hz=25.0, pose_mode="sequential_continuous",
        enable_identity_reid=False, geometry_method=GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX
    )
    
    t0_base = time.time()
    for i in range(n_frames):
        ret, frame = cap.read()
        if not ret: break
        pkt = FramePacket(frame_id=550+i, frame=frame, source_timestamp=(550+i)*0.04)
        pipe_baseline.process_frame_packet(pkt)
    t_base_total = time.time() - t0_base
    base_fps = n_frames / t_base_total
    cap.release()
    
    # 2. V3.0 Candidate Architecture (Exp F)
    cap = cv2.VideoCapture(VIDEO_PATH)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 550)
    
    pipe_v3 = AsyncLivePipeline(
        detector_weights=DET_WEIGHTS, pose_weights=POSE_WEIGHTS,
        pose_target_hz=8.0, pose_mode="async_decoupled",
        enable_identity_reid=True, geometry_method=GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET
    )
    pipe_v3.start()
    
    t0_v3 = time.time()
    for i in range(n_frames):
        ret, frame = cap.read()
        if not ret: break
        pkt = FramePacket(frame_id=550+i, frame=frame, source_timestamp=(550+i)*0.04)
        pipe_v3.process_frame_packet(pkt)
    t_v3_total = time.time() - t0_v3
    v3_fps = n_frames / t_v3_total
    pipe_v3.stop()
    cap.release()
    
    batch_summary = {
        "benchmark_type": "BATCH_UNCONSTRAINED",
        "frames_evaluated": n_frames,
        "baseline_v2_9": {
            "total_time_s": round(t_base_total, 2),
            "throughput_fps": round(base_fps, 2),
            "detection_p50_ms": pipe_baseline.get_latency_percentiles()["detection_ms"]["P50"],
            "pose_p50_ms": pipe_baseline.get_latency_percentiles()["pose_worker_ms"]["P50"]
        },
        "v3_0_core": {
            "total_time_s": round(t_v3_total, 2),
            "throughput_fps": round(v3_fps, 2),
            "detection_p50_ms": pipe_v3.get_latency_percentiles()["detection_ms"]["P50"],
            "pose_p50_ms": pipe_v3.get_latency_percentiles()["pose_worker_ms"]["P50"]
        }
    }
    print(f"  Batch Throughput: Baseline V2.9 = {base_fps:.1f} FPS, V3.0 Core = {v3_fps:.1f} FPS")
    return batch_summary


def run_live_benchmark(n_frames: int = 150, target_stream_fps: float = 25.0) -> Dict[str, Any]:
    print("\n=======================================================")
    print(f"   EXECUTING SUSTAINED LIVE BENCHMARK ({n_frames} frames @ {target_stream_fps} FPS stream rate)")
    print("=======================================================")
    
    stream_dt = 1.0 / target_stream_fps
    
    # 1. Baseline V2.9 under Live Real-Time Ingest
    cap = cv2.VideoCapture(VIDEO_PATH)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 550)
    
    pipe_baseline = AsyncLivePipeline(
        detector_weights=DET_WEIGHTS, pose_weights=POSE_WEIGHTS,
        pose_target_hz=25.0, pose_mode="sequential_continuous",
        enable_identity_reid=False, geometry_method=GeometricProjectionMethod.METHOD_A_HOMOGRAPHY_BBOX,
        max_allowed_frame_age_ms=150.0
    )
    
    latencies_base = []
    dropped_base = 0
    t_start_base = time.time()
    
    for i in range(n_frames):
        ret, frame = cap.read()
        if not ret: break
        t_cap = t_start_base + (i * stream_dt)
        # Sleep until frame arrival time
        now = time.time()
        if now < t_cap:
            time.sleep(t_cap - now)
            
        pkt = FramePacket(frame_id=550+i, frame=frame, source_timestamp=(550+i)*stream_dt, capture_timestamp=t_cap)
        res = pipe_baseline.process_frame_packet(pkt)
        if res is None:
            dropped_base += 1
        else:
            e2e = pkt.end_to_end_latency_ms()
            if e2e is not None:
                latencies_base.append(e2e)
                
    t_total_base = time.time() - t_start_base
    cap.release()
    
    # 2. V3.0 Core under Live Real-Time Ingest
    cap = cv2.VideoCapture(VIDEO_PATH)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 550)
    
    pipe_v3 = AsyncLivePipeline(
        detector_weights=DET_WEIGHTS, pose_weights=POSE_WEIGHTS,
        pose_target_hz=8.0, pose_mode="async_decoupled",
        enable_identity_reid=True, geometry_method=GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET,
        max_allowed_frame_age_ms=150.0
    )
    pipe_v3.start()
    
    latencies_v3 = []
    dropped_v3 = 0
    t_start_v3 = time.time()
    
    for i in range(n_frames):
        ret, frame = cap.read()
        if not ret: break
        t_cap = t_start_v3 + (i * stream_dt)
        now = time.time()
        if now < t_cap:
            time.sleep(t_cap - now)
            
        pkt = FramePacket(frame_id=550+i, frame=frame, source_timestamp=(550+i)*stream_dt, capture_timestamp=t_cap)
        res = pipe_v3.process_frame_packet(pkt)
        if res is None:
            dropped_v3 += 1
        else:
            e2e = pkt.end_to_end_latency_ms()
            if e2e is not None:
                latencies_v3.append(e2e)
                
    t_total_v3 = time.time() - t_start_v3
    pipe_v3.stop()
    cap.release()
    
    live_summary = {
        "benchmark_type": "SUSTAINED_LIVE_STREAMING",
        "stream_fps": target_stream_fps,
        "frames_evaluated": n_frames,
        "baseline_v2_9": {
            "processed_frames": len(latencies_base),
            "dropped_frames": dropped_base,
            "drop_rate_pct": round((dropped_base / max(1, n_frames)) * 100.0, 1),
            "p50_e2e_ms": round(float(np.percentile(latencies_base, 50)), 2) if latencies_base else None,
            "p95_e2e_ms": round(float(np.percentile(latencies_base, 95)), 2) if latencies_base else None,
            "p99_e2e_ms": round(float(np.percentile(latencies_base, 99)), 2) if latencies_base else None
        },
        "v3_0_core": {
            "processed_frames": len(latencies_v3),
            "dropped_frames": dropped_v3,
            "drop_rate_pct": round((dropped_v3 / max(1, n_frames)) * 100.0, 1),
            "p50_e2e_ms": round(float(np.percentile(latencies_v3, 50)), 2) if latencies_v3 else None,
            "p95_e2e_ms": round(float(np.percentile(latencies_v3, 95)), 2) if latencies_v3 else None,
            "p99_e2e_ms": round(float(np.percentile(latencies_v3, 99)), 2) if latencies_v3 else None
        }
    }
    
    print(f"  Live Baseline V2.9: Processed={len(latencies_base)}, Dropped={dropped_base}, P50 Latency={live_summary['baseline_v2_9']['p50_e2e_ms']}ms")
    print(f"  Live V3.0 Core:     Processed={len(latencies_v3)}, Dropped={dropped_v3}, P50 Latency={live_summary['v3_0_core']['p50_e2e_ms']}ms")
    return live_summary


def run_benchmark_comparison():
    batch_res = run_batch_benchmark(n_frames=120)
    live_res = run_live_benchmark(n_frames=120, target_stream_fps=25.0)
    
    full_output = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "video": "test2.mp4 (frames 550-670)",
            "methodology_note": "Batch throughput represents unthrottled disk reading; Live throughput represents throttled 25 FPS stream with freshness gate."
        },
        "batch_benchmark": batch_res,
        "live_benchmark": live_res
    }
    
    out_dir = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_0_1"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "benchmark_live_vs_batch.json"
    
    with open(out_path, "w") as f:
        json.dump(full_output, f, indent=2)
        
    print(f"\nSaved corrected benchmark report to: {out_path}")
    return full_output

if __name__ == "__main__":
    run_benchmark_comparison()
