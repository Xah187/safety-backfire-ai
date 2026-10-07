#!/usr/bin/env python3
"""
Main Execution Pipeline for Safety Backfire AI V0.8.
Integrates:
1. V0.7 Domain-Adapted YOLO Detector + ByteTrack Tracker
2. Ground-plane footprint projection
3. Kinematic trajectory smoothing & velocity estimation
4. Dynamic safety halo generation
5. Pairwise proximity matrix & near-miss detection
6. Production HUD rendering & Baseline Risk logging
"""
from pathlib import Path
import csv
import json
import cv2
from ultralytics import YOLO

from core.geometry import get_footprint
from core.trajectory import TrajectoryTracker
from core.safety_zones import SafetyZoneManager
from core.interaction_engine import InteractionEngine
from visualization.risk_overlay import RiskOverlay

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
VIDEO_PATH = ROOT / "test.mp4"
OUTPUT_DIR = ROOT / "runs/risk_benchmark"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_VIDEO_PATH = OUTPUT_DIR / "spatial_risk_video.mp4"
EVENTS_CSV_PATH = OUTPUT_DIR / "interaction_events.csv"
SUMMARY_JSON_PATH = OUTPUT_DIR / "risk_baseline_summary.json"

CONF_THRESH = 0.08
IOU_THRESH = 0.70
IMGSZ = 960
DEVICE = "cpu"
TRACKER = "bytetrack.yaml"

def main():
    print("=== Starting Safety Backfire AI V0.8 Pipeline ===")
    print(f"Model: {MODEL_PATH}")
    print(f"Video: {VIDEO_PATH}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"Video not found: {VIDEO_PATH}")

    model = YOLO(str(MODEL_PATH))
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    fps = cap.get(cv2.CAP_PROP_FPS) or 29.97
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    writer = cv2.VideoWriter(
        str(OUT_VIDEO_PATH),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    trajectory_tracker = TrajectoryTracker(window_size=5, max_history=60)
    zone_manager = SafetyZoneManager()
    interaction_engine = InteractionEngine(zone_manager=zone_manager)
    overlay_renderer = RiskOverlay(width=width, height=height)
    track_class: dict = {}  # confirmed ByteTrack track_id -> class_name only

    frame_idx = 0
    print(f"Processing {total_frames} frames with ByteTrack + Spatial Risk Engine...")

    for result in model.track(
        source=str(VIDEO_PATH),
        stream=True,
        persist=True,
        tracker=TRACKER,
        imgsz=IMGSZ,
        conf=CONF_THRESH,
        iou=IOU_THRESH,
        device=DEVICE,
        classes=[0, 1],
        verbose=False,
    ):
        frame_idx += 1
        time_sec = round((frame_idx - 1) / fps, 3)
        orig_frame = result.orig_img.copy()

        boxes = result.boxes

        # Anonymous detections (no ByteTrack ID) for THIS frame only — no persistence
        anon_persons_frame: dict = {}
        anon_forklifts_frame: dict = {}

        if boxes is not None and len(boxes):
            ids = boxes.id
            xyxy = boxes.xyxy.cpu().numpy()
            clss = boxes.cls.cpu().numpy().astype(int)

            # Identify forklift boxes in current frame to prevent operator-cabin false person tracks
            forklift_boxes = [xyxy[k] for k, c in enumerate(clss) if model.names[int(c)] == "forklift"]

            for i, cls_id in enumerate(clss):
                c_name = model.names[int(cls_id)]
                box = [int(v) for v in xyxy[i]]

                # Suppress false person detections inside the OPERATOR CABIN ONLY.
                # Check: person center inside the upper 55% of the forklift box.
                # The lower 45% (chassis/wheels area) is where pedestrians can legitimately
                # stand adjacent to the forklift — we must NOT suppress those.
                if c_name == "person" and len(forklift_boxes) > 0:
                    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
                    cabin_suppressed = False
                    for fb in forklift_boxes:
                        cabin_bottom = fb[1] + (fb[3] - fb[1]) * 0.55  # upper 55% = cabin
                        if fb[0] <= cx <= fb[2] and fb[1] <= cy <= cabin_bottom:
                            cabin_suppressed = True
                            break
                    if cabin_suppressed:
                        continue

                foot = get_footprint(box)

                if ids is not None and ids[i] is not None:
                    # Confirmed ByteTrack ID: full trajectory + velocity via persistence buffer
                    track_id = int(ids[i].item())
                    track_class[track_id] = c_name
                    trajectory_tracker.update(track_id, frame_idx, time_sec, foot)
                else:
                    # Anonymous detection: in-frame position only, no persistence.
                    # We do NOT add to track_class or trajectory_tracker to prevent
                    # the synthetic ID from lingering across frames via max_age.
                    synth_id = frame_idx * 1000 + i
                    if c_name == "person":
                        anon_persons_frame[synth_id] = foot
                    else:
                        anon_forklifts_frame[synth_id] = foot

                # Draw standard detection bbox
                bbox_color = (255, 100, 0) if c_name == "person" else (0, 165, 255)
                cv2.rectangle(orig_frame, (box[0], box[1]), (box[2], box[3]), bbox_color, 1)

        # Resolve active entities using track persistence buffer (max_age=25 frames ~ 0.83s)
        # Only CONFIRMED ByteTrack tracks benefit from persistence carryover.
        active_persons: dict = {}
        active_forklifts: dict = {}
        for tid, c_name in track_class.items():
            if trajectory_tracker.is_active(tid, frame_idx, max_age=25):
                smoothed_foot = trajectory_tracker.get_smoothed_position(tid)
                if smoothed_foot is not None:
                    if c_name == "person":
                        active_persons[tid] = smoothed_foot
                    elif c_name == "forklift":
                        active_forklifts[tid] = smoothed_foot

        # Merge anonymous in-frame detections (no persistence, no velocity history)
        active_persons.update(anon_persons_frame)
        active_forklifts.update(anon_forklifts_frame)

        # Compute kinematics and dynamic halos
        forklift_velocities = {}
        person_velocities = {}
        forklift_halos = {}
        trails = {}

        for f_id, foot in active_forklifts.items():
            vel = trajectory_tracker.get_velocity(f_id)
            forklift_velocities[f_id] = vel
            forklift_halos[f_id] = zone_manager.compute_forklift_halos(foot, vel)
            trails[f_id] = trajectory_tracker.get_recent_path(f_id)

        for p_id in active_persons:
            p_vel = trajectory_tracker.get_velocity(p_id)
            person_velocities[p_id] = p_vel
            trails[p_id] = trajectory_tracker.get_recent_path(p_id)

        # Process spatial interactions & near-miss detection
        active_interactions = interaction_engine.process_frame(
            frame_idx=frame_idx,
            time_sec=time_sec,
            persons=active_persons,
            forklifts=active_forklifts,
            forklift_velocities=forklift_velocities,
            person_velocities=person_velocities,
        )

        # Render rich overlay
        rendered_frame = overlay_renderer.render(
            frame=orig_frame,
            frame_idx=frame_idx,
            time_sec=time_sec,
            persons=active_persons,
            forklifts=active_forklifts,
            halos=forklift_halos,
            trails=trails,
            interactions=active_interactions,
        )

        writer.write(rendered_frame)

    writer.release()

    # Save interaction events CSV
    events = interaction_engine.recorded_events
    if events:
        with EVENTS_CSV_PATH.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(events[0].keys()))
            w.writeheader()
            w.writerows(events)
        print(f"Logged {len(events)} interaction event records to: {EVENTS_CSV_PATH}")
    else:
        EVENTS_CSV_PATH.write_text("No hazard events detected.\n")

    # Save baseline summary JSON
    summary = interaction_engine.get_baseline_summary(total_video_frames=frame_idx)
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, indent=2))

    print("\n=== Pre-Intervention Risk Baseline Summary ===")
    print(json.dumps(summary, indent=2))
    print(f"\nSpatial Risk Video saved to: {OUT_VIDEO_PATH}")

if __name__ == '__main__':
    main()
