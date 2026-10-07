from pathlib import Path
from collections import defaultdict, Counter
import json
import csv
import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "runs/forklift_person_yolo26n_v04/weights/best.pt"
VIDEO_PATH = ROOT / "test.mp4"

OUTPUT_DIR = ROOT / "runs" / "v05_tracking_stress_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "tracking_events.csv"
SUMMARY_PATH = OUTPUT_DIR / "tracking_summary.json"
OUTPUT_VIDEO = OUTPUT_DIR / "tracked.mp4"

CONF = 0.25
IOU = 0.70
IMGSZ = 960
DEVICE = "mps"
TRACKER = "bytetrack.yaml"

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

# For each frame, keep the strongest track id per class.
# This is NOT a formal ID-switch metric; it is only a diagnostic.
previous_ids = {}

rows = []

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
                track_seen_frames[track_id] += 1
                track_conf_sum[track_id] += conf
                track_first_frame.setdefault(track_id, frames)
                track_last_frame[track_id] = frames
                track_class[track_id] = name
                current_ids.setdefault(name, []).append(track_id)

            x1, y1, x2, y2 = map(int, xyxy[i])

            # Use simple OpenCV annotation so IDs are visually obvious.
            label = name
            if track_id is not None:
                label += f" ID:{track_id}"
            label += f" {conf:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            rows.append({
                "frame": frames,
                "time_sec": round((frames - 1) / fps, 3),
                "class": name,
                "track_id": "" if track_id is None else track_id,
                "confidence": round(conf, 4),
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            })

    if frame_has_det:
        frames_with_detections += 1
    if frame_has_id:
        frames_with_ids += 1

    # Diagnostic proxy: if a class has an existing tracked ID and
    # a completely different set suddenly becomes dominant, record it.
    for cls_name, ids_now in current_ids.items():
        dominant_now = max(ids_now, key=lambda tid: track_seen_frames[tid])
        if cls_name in previous_ids and previous_ids[cls_name] != dominant_now:
            id_switch_proxy += 1
        previous_ids[cls_name] = dominant_now

    cv2.putText(
        frame,
        f"Frame: {frames}  Tracks: {0 if boxes is None or boxes.id is None else len(boxes.id)}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    writer.write(frame)

writer.release()
cap.release()

track_lengths = Counter(track_seen_frames)
summary = {
    "model": str(MODEL_PATH),
    "video": str(VIDEO_PATH),
    "frames": frames,
    "fps": fps,
    "resolution": [width, height],
    "total_detections": detections,
    "frames_with_detections": frames_with_detections,
    "frames_with_ids": frames_with_ids,
    "id_coverage_ratio": round(frames_with_ids / frames, 4) if frames else 0.0,
    "class_counts": dict(class_counts),
    "unique_track_ids": len(track_seen_frames),
    "tracks_by_class": dict(Counter(track_class.values())),
    "track_length_stats": {
        "max_frames": max(track_lengths.values()) if track_lengths else 0,
        "median_frames": (
            sorted(track_lengths.values())[len(track_lengths)//2]
            if track_lengths else 0
        ),
        "mean_frames": (
            sum(track_lengths.values()) / len(track_lengths)
            if track_lengths else 0.0
        ),
    },
    "id_switch_proxy_count": id_switch_proxy,
    "notes": [
        "id_switch_proxy_count is diagnostic only, not a formal ID-switch metric.",
        "This run uses model.track() with ByteTrack; the previous V0.4 stress test used model.predict().",
        "Do not treat confidence alone as tracking quality."
    ],
}

with CSV_PATH.open("w", newline="") as f:
    fieldnames = ["frame", "time_sec", "class", "track_id", "confidence",
                  "x1", "y1", "x2", "y2"]
    writer_csv = csv.DictWriter(f, fieldnames=fieldnames)
    writer_csv.writeheader()
    writer_csv.writerows(rows)

SUMMARY_PATH.write_text(json.dumps(summary, indent=2))

print("Tracking benchmark complete.")
print(f"Tracked video: {OUTPUT_VIDEO}")
print(f"Events CSV:    {CSV_PATH}")
print(f"Summary JSON:  {SUMMARY_PATH}")
