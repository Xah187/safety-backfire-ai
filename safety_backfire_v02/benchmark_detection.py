#!/usr/bin/env python3
"""Benchmark YOLO detection-only configurations on one video.

Run on the user's MacBook Pro M5/24GB after installing Ultralytics.
Outputs one annotated video + CSV/JSON summaries per configuration.
"""
from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

import cv2
from ultralytics import YOLO

VIDEO = Path("test.mp4")
OUT = Path("runs/detection_benchmark")
OUT.mkdir(parents=True, exist_ok=True)

@dataclass
class Config:
    name: str
    model: str
    conf: float
    iou: float
    imgsz: int

CONFIGS = [
    Config("A_yolo26n_640_conf50", "yolo26n.pt", 0.50, 0.70, 640),
    Config("B_yolo26s_960_conf50", "yolo26s.pt", 0.50, 0.70, 960),
    Config("C_yolo26s_1280_conf35", "yolo26s.pt", 0.35, 0.70, 1280),
]


def run(cfg: Config) -> Dict:
    model = YOLO(cfg.model)
    cap = cv2.VideoCapture(str(VIDEO))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {VIDEO}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out_video = OUT / f"{cfg.name}.mp4"
    writer = cv2.VideoWriter(
        str(out_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )

    class_counts: Dict[str, int] = {}
    det_count = 0
    frame_count = 0
    infer_seconds = 0.0
    max_conf: Dict[str, float] = {}

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_count += 1
        t0 = time.perf_counter()
        results = model.predict(
            source=frame,
            conf=cfg.conf,
            iou=cfg.iou,
            imgsz=cfg.imgsz,
            device="mps",
            verbose=False,
        )
        infer_seconds += time.perf_counter() - t0
        result = results[0]
        if result.boxes is not None and len(result.boxes) > 0:
            names = result.names
            boxes = result.boxes
            det_count += len(boxes)
            for cls_id, score in zip(boxes.cls.tolist(), boxes.conf.tolist()):
                label = names[int(cls_id)]
                class_counts[label] = class_counts.get(label, 0) + 1
                max_conf[label] = max(max_conf.get(label, 0.0), float(score))
        annotated = result.plot()
        writer.write(annotated)

    cap.release()
    writer.release()

    elapsed = infer_seconds
    summary = {
        **asdict(cfg),
        "video": str(VIDEO),
        "frames": frame_count,
        "source_fps": fps,
        "resolution": [width, height],
        "total_detections": det_count,
        "detections_per_frame": round(det_count / max(frame_count, 1), 3),
        "inference_seconds": round(elapsed, 3),
        "inference_fps": round(frame_count / max(elapsed, 1e-9), 2),
        "class_counts": class_counts,
        "max_confidence_by_class": {k: round(v, 3) for k, v in max_conf.items()},
        "annotated_video": str(out_video),
    }
    (OUT / f"{cfg.name}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    if not VIDEO.exists():
        raise FileNotFoundError(f"Put {VIDEO} beside this script")
    all_results: List[Dict] = []
    for cfg in CONFIGS:
        print(f"\n=== {cfg.name} ===")
        result = run(cfg)
        all_results.append(result)
        print(json.dumps(result, indent=2))
    (OUT / "summary.json").write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "model", "conf", "imgsz", "frames", "detections", "det/frame", "infer_fps"])
        for r in all_results:
            writer.writerow([r["name"], r["model"], r["conf"], r["imgsz"], r["frames"], r["total_detections"], r["detections_per_frame"], r["inference_fps"]])

if __name__ == "__main__":
    main()
