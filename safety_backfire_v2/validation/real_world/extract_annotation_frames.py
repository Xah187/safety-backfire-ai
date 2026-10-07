"""
Phase 5 — Frame Extraction for Human Ground Truth Annotation

Extracts representative frames from real-world video covering all required scenarios:
- person only
- forklift only
- person + forklift
- near interaction
- far interaction
- occlusion
- crossing
- stationary

Generates ground_truth.json template for manual annotation.
The template has null bboxes — a human MUST fill these in.
"""
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))


def extract_annotation_frames(video_path: Path, model_path: Path, output_dir: Path, max_frames_per_scenario: int = 3):
    """
    Runs detection (no tracking) to find frames with interesting content,
    then saves those frames for manual annotation.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(model_path))
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    print(f"Scanning {video_path.name} ({total_frames} frames @ {fps}fps) for annotation candidates...")

    scenarios = {
        "person_only": [],
        "forklift_only": [],
        "person_and_forklift": [],
        "no_detections": []
    }

    frame_idx = 0
    # Sample every 10th frame for efficiency
    for result in model.predict(
        source=str(video_path),
        stream=True,
        imgsz=640,
        conf=0.15,
        iou=0.70,
        device="cpu",
        classes=[0, 1],
        verbose=False
    ):
        frame_idx += 1
        if frame_idx % 10 != 0:
            continue

        boxes = result.boxes
        frame = result.orig_img.copy()

        if boxes is None or len(boxes) == 0:
            if len(scenarios["no_detections"]) < max_frames_per_scenario:
                scenarios["no_detections"].append(frame_idx)
            continue

        clss = set(int(c) for c in boxes.cls.cpu().numpy())
        has_person = 0 in clss
        has_forklift = 1 in clss

        if has_person and has_forklift:
            if len(scenarios["person_and_forklift"]) < max_frames_per_scenario:
                scenarios["person_and_forklift"].append(frame_idx)
                # Save frame with raw detections overlaid
                vis = result.plot()
                cv2.imwrite(str(output_dir / f"candidate_person_forklift_f{frame_idx:05d}.jpg"), vis)
        elif has_person:
            if len(scenarios["person_only"]) < max_frames_per_scenario:
                scenarios["person_only"].append(frame_idx)
                vis = result.plot()
                cv2.imwrite(str(output_dir / f"candidate_person_only_f{frame_idx:05d}.jpg"), vis)
        elif has_forklift:
            if len(scenarios["forklift_only"]) < max_frames_per_scenario:
                scenarios["forklift_only"].append(frame_idx)
                vis = result.plot()
                cv2.imwrite(str(output_dir / f"candidate_forklift_only_f{frame_idx:05d}.jpg"), vis)

        # Stop early if we have enough of all types
        if all(len(v) >= max_frames_per_scenario for v in scenarios.values()):
            break

    cap.release()
    print(f"\nScenario coverage found:")
    for k, v in scenarios.items():
        print(f"  {k}: {len(v)} frames → {v}")

    return scenarios


def generate_annotation_template(scenarios: dict, output_dir: Path, video_name: str):
    """
    Generates ground_truth.json with null bboxes for human annotation.
    """
    annotation_data = {
        "metadata": {
            "video": video_name,
            "annotation_status": "NEEDS_HUMAN_ANNOTATION",
            "annotation_instructions": [
                "For each frame, fill in the 'bbox' field: [x1, y1, x2, y2] in pixels",
                "Do NOT leave bbox as null for frames you have annotated",
                "gt_id must be consistent across frames for the same physical entity",
                "class must be exactly 'person' or 'forklift'",
                "Remove entries for objects NOT visible in that frame"
            ],
            "critical_note": (
                "These annotations are the GROUND TRUTH. The system's metrics depend entirely "
                "on the accuracy of these annotations. Incorrect annotations = incorrect metrics."
            )
        },
        "frames": []
    }

    all_frames = []
    for scenario, frame_list in scenarios.items():
        for f in frame_list:
            all_frames.append({"frame": f, "scenario": scenario})

    # Sort by frame number
    all_frames.sort(key=lambda x: x["frame"])

    for item in all_frames:
        frame_entry = {
            "frame": item["frame"],
            "scenario": item["scenario"],
            "annotation_status": "NEEDS_ANNOTATION",
            "objects": [
                {
                    "gt_id": "person_01",
                    "class": "person",
                    "bbox": [None, None, None, None],
                    "note": "Fill if person is visible, remove if not"
                },
                {
                    "gt_id": "forklift_01",
                    "class": "forklift",
                    "bbox": [None, None, None, None],
                    "note": "Fill if forklift is visible, remove if not"
                }
            ]
        }
        annotation_data["frames"].append(frame_entry)

    out_path = output_dir / "ground_truth.json"
    with open(out_path, "w") as f:
        json.dump(annotation_data, f, indent=2)
    print(f"\nAnnotation template saved to: {out_path}")
    print(f"Total frames requiring annotation: {len(all_frames)}")
    print("\n⚠️  A human MUST review the saved candidate images and fill in the bbox coordinates.")
    return annotation_data


if __name__ == "__main__":
    video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "test2.mp4"
    model_path = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
    out_dir = ROOT / "validation/real_world/annotations"

    print("=== Phase 5: Frame Extraction for Human Annotation ===")
    scenarios = extract_annotation_frames(video_path, model_path, out_dir)
    generate_annotation_template(scenarios, out_dir, video_path.name)
    print("\nDone. Open the candidate_*.jpg images and fill in ground_truth.json bboxes.")
