"""
V2.8.4 — Forensic Investigation of False Detections
Investigates P18, P22, P89, P93, P108 to determine the source of each detection.
Outputs raw YOLO detection + pose evidence for each suspect track.
"""
import sys
import cv2
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from ultralytics import YOLO

def investigate():
    video_path = str(ROOT.parent / "test2.mp4")
    model_path = str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    
    det_model = YOLO(model_path)
    pose_model = YOLO("yolov8n-pose.pt")
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Targets: (track_id, frame_range)
    targets = {
        18:  (540, 600),
        22:  (540, 600),
        89:  (1120, 1150),
        93:  (950, 1010),
        108: (1200, 1244),
    }
    
    findings = {t: [] for t in targets}
    frame_idx = 0

    print("Processing... (full video needed to maintain track IDs)")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        if frame_idx % 200 == 0:
            print(f"  Frame {frame_idx}/{total}")

        # Check if this frame is in any target range
        in_range = any(lo <= frame_idx <= hi for lo, hi in targets.values())
        
        res = det_model.track(frame, imgsz=640, conf=0.15, iou=0.70, 
                              classes=[0,1], persist=True, 
                              tracker="bytetrack.yaml", verbose=False)[0]
        
        if not in_range or res.boxes.id is None:
            continue
        
        # Run pose on this frame
        pose_res = pose_model.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
        
        for b, cls, trk_id, conf in zip(
            res.boxes.xyxy.cpu().numpy(),
            res.boxes.cls.cpu().numpy(),
            res.boxes.id.cpu().numpy(),
            res.boxes.conf.cpu().numpy()
        ):
            tid = int(trk_id)
            lo, hi = targets.get(tid, (0, 0))
            if lo <= frame_idx <= hi and int(cls) == 0:  # person class only
                box = b.tolist()
                
                # Check pose evidence for this bbox
                best_visible_kpts = 0
                best_conf_kpts = []
                if pose_res.keypoints is not None and len(pose_res.boxes) > 0:
                    for i, pbox in enumerate(pose_res.boxes.xyxy.cpu().numpy()):
                        ix1 = max(box[0], pbox[0]); iy1 = max(box[1], pbox[1])
                        ix2 = min(box[2], pbox[2]); iy2 = min(box[3], pbox[3])
                        inter = max(0, ix2-ix1) * max(0, iy2-iy1)
                        area1 = (box[2]-box[0]) * (box[3]-box[1])
                        area2 = (pbox[2]-pbox[0]) * (pbox[3]-pbox[1])
                        iou = inter / max(1, area1+area2-inter)
                        if iou > 0.4:
                            kpts = pose_res.keypoints.data.cpu().numpy()[i]
                            visible = int((kpts[:, 2] > 0.5).sum()) if kpts.shape[1] == 3 else 0
                            if visible > best_visible_kpts:
                                best_visible_kpts = visible
                                best_conf_kpts = [round(float(kpts[k,2]), 2) for k in range(min(6, kpts.shape[0]))]
                
                w = box[2]-box[0]; h = box[3]-box[1]
                aspect = h/max(1, w)
                area = w*h
                
                findings[tid].append({
                    "frame": frame_idx,
                    "conf": round(float(conf), 3),
                    "box": [round(v,1) for v in box],
                    "width": round(w,1),
                    "height": round(h,1),
                    "aspect_ratio": round(aspect, 2),
                    "area_px": round(area),
                    "pose_visible_kpts": best_visible_kpts,
                    "pose_kpt_conf_head_to_hip": best_conf_kpts,
                })

    cap.release()
    
    # Summary report
    print("\n" + "="*60)
    print("FORENSIC INVESTIGATION RESULTS")
    print("="*60)
    for tid, entries in findings.items():
        if not entries:
            print(f"\nP{tid}: NOT OBSERVED in target frames (may have different ID this run)")
            continue
        print(f"\nP{tid} ({len(entries)} frames observed):")
        for e in entries[::max(1, len(entries)//5)]:  # Print every ~5th
            print(f"  Frame {e['frame']}: conf={e['conf']} | "
                  f"size={e['width']:.0f}x{e['height']:.0f} | "
                  f"aspect={e['aspect_ratio']} | "
                  f"pose_kpts={e['pose_visible_kpts']}/17 | "
                  f"head-hip_conf={e['pose_kpt_conf_head_to_hip']}")

    # Save JSON
    out_path = Path("/Users/xah187/.gemini/antigravity-ide/brain/2047d700-61e0-4839-9e14-d00ab00f0e92/scratch/v2_8_4_forensic.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(findings, f, indent=2)
    print(f"\nFull data saved to: {out_path}")

if __name__ == "__main__":
    investigate()
