#!/usr/bin/env python3
"""
Safety Backfire AI — V0.9 Comparison Pipeline
Runs the V0.8 risk analysis on two video segments (before/after intervention)
and produces a Safety Backfire comparison report.

Usage:
    python run_v09_comparison.py
    python run_v09_comparison.py --before path/to/before.mp4 --after path/to/after.mp4

When no arguments are given, splits the default test.mp4 at midpoint.
"""
import argparse
import csv
import json
import sys
import cv2
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
V08_ROOT = ROOT.parent / "safety_backfire_v08"
PROJECT_ROOT = ROOT.parent

# core.* → V08 core modules (geometry, trajectory, safety_zones, interaction_engine)
# safety_backfire_v09.core.* → V09 modules (comparison_engine)
sys.path.insert(0, str(PROJECT_ROOT))   # for safety_backfire_v09.*
sys.path.insert(0, str(V08_ROOT))       # for core.* (V08 modules)

from ultralytics import YOLO
from core.geometry import get_footprint
from core.trajectory import TrajectoryTracker
from core.safety_zones import SafetyZoneManager
from core.interaction_engine import InteractionEngine
from safety_backfire_v09.core.comparison_engine import ComparisonEngine

MODEL_PATH = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
DEFAULT_VIDEO = V08_ROOT / "test.mp4"
OUTPUT_DIR = ROOT / "runs/comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONF_THRESH = 0.08
IOU_THRESH  = 0.70
IMGSZ       = 960
DEVICE      = "cpu"
TRACKER     = "bytetrack.yaml"


# ─────────────────────────────────────────────────────────────
# Video segment splitter
# ─────────────────────────────────────────────────────────────
def split_video(video_path: Path, before_path: Path, after_path: Path):
    """Splits a video into two equal halves and writes them to disk."""
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 29.97
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    mid = total // 2

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writers = [
        cv2.VideoWriter(str(before_path), fourcc, fps, (w, h)),
        cv2.VideoWriter(str(after_path),  fourcc, fps, (w, h)),
    ]

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        writers[0 if frame_idx < mid else 1].write(frame)
        frame_idx += 1

    cap.release()
    for wr in writers:
        wr.release()

    print(f"  Split: BEFORE={mid} frames ({mid/fps:.1f}s) | AFTER={total-mid} frames ({(total-mid)/fps:.1f}s)")
    return fps, w, h


# ─────────────────────────────────────────────────────────────
# Core pipeline (re-used from V0.8, self-contained here)
# ─────────────────────────────────────────────────────────────
def run_pipeline(model: YOLO, video_path: Path, label: str) -> dict:
    """
    Runs the V0.8 risk pipeline on a single video and returns
    the pre_intervention_baseline dict.
    """
    print(f"\n[{label}] Processing: {video_path.name}")

    cap = cv2.VideoCapture(str(video_path))
    fps   = cap.get(cv2.CAP_PROP_FPS) or 29.97
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    trajectory_tracker = TrajectoryTracker(window_size=5, max_history=60)
    zone_manager       = SafetyZoneManager()
    engine             = InteractionEngine(zone_manager=zone_manager)
    track_class: dict  = {}
    frame_idx = 0

    for result in model.track(
        source=str(video_path),
        stream=True, persist=True, tracker=TRACKER,
        imgsz=IMGSZ, conf=CONF_THRESH, iou=IOU_THRESH,
        device=DEVICE, classes=[0, 1], verbose=False,
    ):
        frame_idx += 1
        time_sec = round((frame_idx - 1) / fps, 3)

        anon_persons_frame:   dict = {}
        anon_forklifts_frame: dict = {}

        boxes = result.boxes
        if boxes is not None and len(boxes):
            ids  = boxes.id
            xyxy = boxes.xyxy.cpu().numpy()
            clss = boxes.cls.cpu().numpy().astype(int)

            forklift_boxes = [xyxy[k] for k, c in enumerate(clss)
                              if model.names[int(c)] == "forklift"]

            for i, cls_id in enumerate(clss):
                c_name = model.names[int(cls_id)]
                box    = [int(v) for v in xyxy[i]]

                # Cabin suppression: upper 55% of forklift box only
                if c_name == "person" and len(forklift_boxes) > 0:
                    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
                    suppressed = False
                    for fb in forklift_boxes:
                        cab_bot = fb[1] + (fb[3] - fb[1]) * 0.55
                        if fb[0] <= cx <= fb[2] and fb[1] <= cy <= cab_bot:
                            suppressed = True
                            break
                    if suppressed:
                        continue

                foot = get_footprint(box)
                if ids is not None and ids[i] is not None:
                    tid = int(ids[i].item())
                    track_class[tid] = c_name
                    trajectory_tracker.update(tid, frame_idx, time_sec, foot)
                else:
                    sid = frame_idx * 1000 + i
                    (anon_persons_frame if c_name == "person" else anon_forklifts_frame)[sid] = foot

        # Resolve active entities
        active_persons:   dict = {}
        active_forklifts: dict = {}
        for tid, c_name in track_class.items():
            if trajectory_tracker.is_active(tid, frame_idx, max_age=25):
                pos = trajectory_tracker.get_smoothed_position(tid)
                if pos:
                    (active_persons if c_name == "person" else active_forklifts)[tid] = pos

        active_persons.update(anon_persons_frame)
        active_forklifts.update(anon_forklifts_frame)

        forklift_velocities: dict = {}
        person_velocities:   dict = {}
        for f_id, foot in active_forklifts.items():
            forklift_velocities[f_id] = trajectory_tracker.get_velocity(f_id)
        for p_id in active_persons:
            person_velocities[p_id] = trajectory_tracker.get_velocity(p_id)

        engine.process_frame(
            frame_idx=frame_idx, time_sec=time_sec,
            persons=active_persons, forklifts=active_forklifts,
            forklift_velocities=forklift_velocities,
            person_velocities=person_velocities,
        )

    summary = engine.get_baseline_summary(total_video_frames=frame_idx)
    baseline = summary["pre_intervention_baseline"]
    print(f"  → min_dist={baseline['min_passing_distance_meters']}m  "
          f"warnings={baseline['total_proximity_warnings']}  "
          f"near_miss={baseline['total_near_miss_incidents']}  "
          f"risk_time={baseline['percent_time_in_risk_zones']}%")
    return baseline


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Safety Backfire V0.9 Comparison")
    parser.add_argument("--before", type=Path, default=None, help="Path to pre-intervention video")
    parser.add_argument("--after",  type=Path, default=None, help="Path to post-intervention video")
    parser.add_argument("--before-label", default="Pre-Intervention",  help="Label for BEFORE segment")
    parser.add_argument("--after-label",  default="Post-Intervention", help="Label for AFTER segment")
    args = parser.parse_args()

    print("=== Safety Backfire AI V0.9 — Comparison Pipeline ===")
    print(f"Model: {MODEL_PATH}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    # ── Video preparation ──
    if args.before is None or args.after is None:
        print(f"\nNo before/after videos provided. Splitting {DEFAULT_VIDEO.name} at midpoint.")
        before_path = OUTPUT_DIR / "segment_before.mp4"
        after_path  = OUTPUT_DIR / "segment_after.mp4"
        split_video(DEFAULT_VIDEO, before_path, after_path)
        before_label = "Segment A (Frames 1-213, 7.1s)"
        after_label  = "Segment B (Frames 214-426, 7.1s)"
    else:
        before_path  = args.before
        after_path   = args.after
        before_label = args.before_label
        after_label  = args.after_label

    if not before_path.exists():
        raise FileNotFoundError(f"Before video not found: {before_path}")
    if not after_path.exists():
        raise FileNotFoundError(f"After video not found: {after_path}")

    # ── Load model (shared across both runs) ──
    model = YOLO(str(MODEL_PATH))

    # ── Run pipeline on each segment ──
    before_baseline = run_pipeline(model, before_path, before_label)
    after_baseline  = run_pipeline(model, after_path,  after_label)

    # ── Compare ──
    comp = ComparisonEngine()
    report = comp.compare(before_baseline, after_baseline,
                          before_label=before_label, after_label=after_label)

    # ── Save outputs ──
    report_path = OUTPUT_DIR / "safety_backfire_comparison.json"
    report_path.write_text(json.dumps(report, indent=2))

    before_path_out = OUTPUT_DIR / "before_baseline.json"
    after_path_out  = OUTPUT_DIR / "after_baseline.json"
    before_path_out.write_text(json.dumps(before_baseline, indent=2))
    after_path_out.write_text(json.dumps(after_baseline, indent=2))

    # ── Print report ──
    print("\n")
    print(comp.format_report(report))
    print(f"\nOutputs saved to: {OUTPUT_DIR}/")
    print(f"  → safety_backfire_comparison.json")
    print(f"  → before_baseline.json")
    print(f"  → after_baseline.json")


if __name__ == "__main__":
    main()
