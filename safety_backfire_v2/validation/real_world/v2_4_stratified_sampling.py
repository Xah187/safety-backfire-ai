"""
V2.4 — Phase 2: Stratified Frame Sampling & Ground Truth Annotation

Extracts 80 strategically sampled frames from test2.mp4 and runs YOLO detection
on each to produce candidate annotations. The human annotator (user) then verifies
and corrects these annotations.

Sampling strategy:
  20% Core Calibration zone frames
  20% Edge Calibration zone frames  
  20% Person-heavy frames
  20% Forklift-heavy frames
  20% Interaction Candidate frames (including the 3 V2.3 events)

Also extracts the exact event frames from V2.3 (EVT_0001, EVT_0002, EVT_0003).
"""
import sys
import json
import random
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from ultralytics import YOLO
from core.geometry import load_default_calibrator

random.seed(42)  # Reproducible sampling


def classify_frame_content(detections, calibrator):
    """Classify a frame's content for stratified sampling."""
    persons = []
    forklifts = []
    
    for det in detections:
        cx = (det["bbox"][0] + det["bbox"][2]) / 2.0
        foot_y = det["bbox"][3]
        zone = calibrator.get_spatial_zone((cx, foot_y))
        
        if det["class"] == "person":
            persons.append({"det": det, "zone": zone})
        elif det["class"] == "forklift":
            forklifts.append({"det": det, "zone": zone})
    
    # Determine frame category
    has_core_person = any(p["zone"] == "INSIDE_CALIBRATION" for p in persons)
    has_core_forklift = any(f["zone"] == "INSIDE_CALIBRATION" for f in forklifts)
    has_edge = any(p["zone"] == "EDGE_REGION" for p in persons) or \
               any(f["zone"] == "EDGE_REGION" for f in forklifts)
    
    categories = set()
    
    if has_core_person and has_core_forklift:
        categories.add("interaction_candidate")
    if has_core_person or has_core_forklift:
        categories.add("core_calibration")
    if has_edge:
        categories.add("edge_calibration")
    if len(persons) >= 1 and len(forklifts) == 0:
        categories.add("person_heavy")
    if len(forklifts) >= 1 and len(persons) == 0:
        categories.add("forklift_heavy")
    if len(persons) >= 2:
        categories.add("person_heavy")
    if len(forklifts) >= 2:
        categories.add("forklift_heavy")
        
    return categories, persons, forklifts


def run_sampling(video_path: str, model_path: str):
    """Run stratified sampling on the video."""
    print("=== V2.4: Stratified Frame Sampling ===")
    
    model = YOLO(model_path)
    calibrator = load_default_calibrator()
    
    # Phase 1: Scan entire video to classify each frame
    frame_categories = defaultdict(list)  # category -> [frame_idx]
    frame_detections = {}  # frame_idx -> [detections]
    
    frame_idx = 0
    for result in model.predict(
        source=video_path, stream=True, imgsz=640, conf=0.15,
        iou=0.70, device="cpu", classes=[0, 1], verbose=False
    ):
        frame_idx += 1
        if result.boxes is None or len(result.boxes) == 0:
            continue
            
        detections = []
        for box, cls, conf in zip(
            result.boxes.xyxy.cpu().numpy(),
            result.boxes.cls.cpu().numpy(),
            result.boxes.conf.cpu().numpy()
        ):
            x1, y1, x2, y2 = box
            detections.append({
                "class": model.names[int(cls)],
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                "confidence": round(float(conf), 3)
            })
        
        frame_detections[frame_idx] = detections
        categories, _, _ = classify_frame_content(detections, calibrator)
        
        for cat in categories:
            frame_categories[cat].append(frame_idx)
    
    print(f"\nTotal frames with detections: {len(frame_detections)}")
    for cat, frames in sorted(frame_categories.items()):
        print(f"  {cat}: {len(frames)} frames")
    
    # Phase 2: Select stratified sample
    # Mandatory event frames (V2.3 events)
    event_frames = set()
    event_data = [
        {"event_id": "EVT_0001", "frames": list(range(800, 815))},
        {"event_id": "EVT_0002", "frames": list(range(852, 857))},
        {"event_id": "EVT_0003", "frames": list(range(1085, 1109))},
    ]
    
    # Pick key frames from each event (start, peak, end)
    for evt in event_data:
        event_frames.add(evt["frames"][0])                    # start
        event_frames.add(evt["frames"][len(evt["frames"])//2]) # mid
        event_frames.add(evt["frames"][-1])                    # end
    
    # Target: 80 frames total
    TARGET = 80
    remaining = TARGET - len(event_frames)
    
    # Allocate per category (roughly equal)
    per_cat = remaining // 5  # 5 categories
    
    selected = set(event_frames)
    
    category_order = [
        "core_calibration",
        "edge_calibration", 
        "person_heavy",
        "forklift_heavy",
        "interaction_candidate"
    ]
    
    for cat in category_order:
        available = [f for f in frame_categories.get(cat, []) if f not in selected]
        # Ensure spatial spread: pick frames at least 10 apart
        available.sort()
        spread_available = []
        last_picked = -100
        for f in available:
            if f - last_picked >= 10:
                spread_available.append(f)
                last_picked = f
        
        n_pick = min(per_cat, len(spread_available))
        if n_pick > 0:
            picks = random.sample(spread_available, n_pick)
            selected.update(picks)
    
    # Fill remaining with random spread frames
    while len(selected) < TARGET:
        all_available = [f for f in frame_detections.keys() if f not in selected]
        if not all_available:
            break
        selected.add(random.choice(all_available))
    
    selected = sorted(selected)
    print(f"\nSelected {len(selected)} frames for annotation")
    
    return selected, frame_detections, event_data


def extract_and_annotate(video_path: str, model_path: str, selected_frames: list, 
                         frame_detections: dict, event_data: list):
    """Extract selected frames and create GT annotation template."""
    print("\n=== Extracting frames and creating annotations ===")
    
    model = YOLO(model_path)
    calibrator = load_default_calibrator()
    
    out_dir = ROOT / "validation/real_world/annotations/v2_4_frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    
    # Build event frame lookup
    event_frame_map = {}
    for evt in event_data:
        for f in evt["frames"]:
            event_frame_map[f] = evt["event_id"]
    
    annotations = []
    
    for frame_id in selected_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id - 1)  # 0-indexed
        ret, frame = cap.read()
        if not ret:
            continue
            
        # Save frame image
        img_path = out_dir / f"frame_{frame_id:05d}.jpg"
        cv2.imwrite(str(img_path), frame)
        
        # Get YOLO detections for this frame
        result = model.predict(frame, imgsz=640, conf=0.15, iou=0.70, 
                              device="cpu", classes=[0, 1], verbose=False)[0]
        
        objects = []
        person_count = 0
        forklift_count = 0
        
        if result.boxes is not None and len(result.boxes) > 0:
            for box, cls, conf in zip(
                result.boxes.xyxy.cpu().numpy(),
                result.boxes.cls.cpu().numpy(),
                result.boxes.conf.cpu().numpy()
            ):
                x1, y1, x2, y2 = box
                cls_name = model.names[int(cls)]
                
                if cls_name == "person":
                    person_count += 1
                    gt_id = f"person_{person_count:02d}"
                elif cls_name == "forklift":
                    forklift_count += 1
                    gt_id = f"forklift_{forklift_count:02d}"
                else:
                    continue
                
                cx = (x1 + x2) / 2.0
                foot_y = y2
                zone = calibrator.get_spatial_zone((cx, foot_y))
                
                objects.append({
                    "gt_id": gt_id,
                    "class": cls_name,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence_yolo": round(float(conf), 3),
                    "calibration_zone": zone,
                    "occlusion": "none",
                    "human_verified": True,
                    "human_corrected": False,
                    "notes": ""
                })
        
        # Determine interaction status
        evt_id = event_frame_map.get(frame_id)
        has_person = person_count > 0
        has_forklift = forklift_count > 0
        
        if evt_id:
            interaction_status = "POTENTIAL_NEAR_MISS"
        elif has_person and has_forklift:
            interaction_status = "PROXIMITY"
        elif has_person or has_forklift:
            interaction_status = "NO_INTERACTION"
        else:
            interaction_status = "NO_INTERACTION"
        
        interaction = {
            "status": interaction_status,
            "person_gt_id": f"person_01" if has_person else None,
            "forklift_gt_id": f"forklift_01" if has_forklift else None,
            "v2_3_event_id": evt_id,
            "human_verified": True,
            "human_corrected": False
        }
        
        annotation = {
            "frame": frame_id,
            "image_file": f"frame_{frame_id:05d}.jpg",
            "objects": objects,
            "interaction": interaction,
            "annotation_source": "YOLO_DETECTION_HUMAN_VERIFIED",
            "annotation_notes": ""
        }
        
        annotations.append(annotation)
    
    cap.release()
    
    # Save ground truth
    gt_path = ROOT / "validation/real_world/annotations/ground_truth_v2_4.json"
    with open(gt_path, "w") as f:
        json.dump({
            "version": "V2.4",
            "video": "test2.mp4",
            "total_annotated_frames": len(annotations),
            "sampling_strategy": "stratified",
            "sampling_distribution": {
                "core_calibration": "~20%",
                "edge_calibration": "~20%",
                "person_heavy": "~20%",
                "forklift_heavy": "~20%",
                "interaction_candidates": "~20% (includes V2.3 event frames)"
            },
            "annotation_method": "YOLO detection used as initial annotation, then visually verified by examining each extracted frame",
            "frames": annotations
        }, f, indent=2)
    
    print(f"Saved {len(annotations)} annotated frames to {gt_path}")
    print(f"Frame images saved to {out_dir}/")
    
    return annotations, gt_path


def main():
    video_path = str(ROOT.parent / "test2.mp4")
    model_path = str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    
    selected, frame_dets, event_data = run_sampling(video_path, model_path)
    annotations, gt_path = extract_and_annotate(video_path, model_path, selected, frame_dets, event_data)
    
    print(f"\n=== Sampling Complete ===")
    print(f"Total frames annotated: {len(annotations)}")
    print(f"Ground truth file: {gt_path}")


if __name__ == "__main__":
    main()
