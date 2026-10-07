from pathlib import Path
from collections import defaultdict, Counter
import json
import csv
import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "runs/forklift_person_yolo26n_v07/weights/best.pt"
VIDEO_PATH = ROOT / "test.mp4"

OUTPUT_DIR = ROOT / "runs" / "benchmark_v07"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "tracking_events.csv"
SUMMARY_PATH = OUTPUT_DIR / "tracking_summary.json"
OUTPUT_VIDEO = OUTPUT_DIR / "tracked.mp4"

CONF = 0.20
IOU = 0.70
IMGSZ = 960
DEVICE = "cpu"
TRACKER = "bytetrack.yaml"

def run_benchmark():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"Video not found: {VIDEO_PATH}")

    model = YOLO(str(MODEL_PATH))

    cap = cv2.VideoCapture(str(VIDEO_PATH))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(
        str(OUTPUT_VIDEO),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    track_seen_frames = Counter()
    track_first_frame = {}
    track_last_frame = {}
    track_class = {}
    track_conf_sum = Counter()

    class_counts = Counter()
    frames = 0
    detections = 0
    frames_with_detections = 0
    frames_with_ids = 0
    id_switch_proxy = 0
    previous_ids = {}

    rows = []

    # Diagnostics for phantom forklift at (x~279, y~135)
    phantom_detections = 0

    print("Running ByteTrack benchmark on test.mp4...")
    for result in model.track(
        source=str(VIDEO_PATH),
        stream=True,
        persist=True,
        tracker=TRACKER,
        imgsz=IMGSZ,
        conf=CONF,
        iou=IOU,
        device=DEVICE,
        classes=[0, 1],
        verbose=False,
    ):
        frames += 1
        frame = result.orig_img.copy()

        frame_has_det = False
        frame_has_id = False
        current_ids = {}

        boxes = result.boxes
        if boxes is not None and len(boxes):
            frame_has_det = True
            detections += len(boxes)

            ids = boxes.id
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            clss = boxes.cls.cpu().numpy().astype(int)

            for i, cls_id in enumerate(clss):
                conf = float(confs[i])
                name = model.names[int(cls_id)]
                class_counts[name] += 1

                track_id = None
                if ids is not None:
                    track_id = int(ids[i].item())
                    frame_has_id = True
                    current_ids[name] = track_id

                    track_seen_frames[track_id] += 1
                    track_conf_sum[track_id] += conf
                    track_last_frame[track_id] = frames
                    track_class[track_id] = name
                    if track_id not in track_first_frame:
                        track_first_frame[track_id] = frames

                x1, y1, x2, y2 = [int(v) for v in xyxy[i]]
                time_sec = round((frames - 1) / fps, 3)

                # Check if this detection is the phantom forklift
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                if name == "forklift" and (240 <= cx <= 320) and (100 <= cy <= 170):
                    phantom_detections += 1

                rows.append({
                    "frame": frames,
                    "time_sec": time_sec,
                    "class": name,
                    "track_id": "" if track_id is None else track_id,
                    "confidence": round(conf, 4),
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                })

                color = (0, 165, 255) if name == "forklift" else (255, 100, 0)
                label = f"{name} {conf:.2f}"
                if track_id is not None:
                    label = f"ID:{track_id} {label}"

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    label,
                    (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

        if frame_has_det:
            frames_with_detections += 1
        if frame_has_id:
            frames_with_ids += 1

        for c, tid in current_ids.items():
            if c in previous_ids and previous_ids[c] != tid:
                id_switch_proxy += 1
        previous_ids.update(current_ids)

        writer.write(frame)

    cap.release()
    writer.release()

    with CSV_PATH.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "frame",
                "time_sec",
                "class",
                "track_id",
                "confidence",
                "x1",
                "y1",
                "x2",
                "y2",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    track_lengths = list(track_seen_frames.values())
    tracks_by_class = Counter(track_class.values())

    summary = {
        "model": str(MODEL_PATH),
        "video": str(VIDEO_PATH),
        "frames": frames,
        "fps": fps,
        "resolution": [width, height],
        "total_detections": detections,
        "frames_with_detections": frames_with_detections,
        "frames_with_ids": frames_with_ids,
        "id_coverage_ratio": round(frames_with_ids / max(frames, 1), 4),
        "class_counts": dict(class_counts),
        "unique_track_ids": len(track_seen_frames),
        "tracks_by_class": dict(tracks_by_class),
        "track_length_stats": {
            "max_frames": max(track_lengths) if track_lengths else 0,
            "median_frames": float(np.median(track_lengths)) if track_lengths else 0,
            "mean_frames": float(np.mean(track_lengths)) if track_lengths else 0,
        },
        "phantom_forklift_frames": phantom_detections,
        "id_switch_proxy_count": id_switch_proxy,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"\nBenchmark completed! Output saved to: {OUTPUT_DIR}")

if __name__ == '__main__':
    run_benchmark()
