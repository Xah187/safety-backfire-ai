#!/usr/bin/env python3
"""
Extracts critical frames from test.mp4 and auto-labels them for V1.0.
Uses YOLO to detect the forklift, and Background Subtraction (MOG2) to find
the moving person next to the forklift (since YOLO misses the person here).
"""
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
VIDEO_PATH = ROOT.parent / "safety_backfire_v08/test.mp4"
MODEL_PATH = ROOT.parent / "yolo26s.pt"

OUT_IMG_DIR = ROOT / "data/dataset_v10/images/train"
OUT_LBL_DIR = ROOT / "data/dataset_v10/labels/train"

OUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
OUT_LBL_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("Loading YOLO model...")
    model = YOLO(str(MODEL_PATH))
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    
    fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
    
    saved = 0
    frame_idx = 0
    
    print("Pre-training background subtractor...")
    while frame_idx < 150:
        ret, frame = cap.read()
        if not ret: break
        fgbg.apply(frame)
        frame_idx += 1

    print("Extracting critical frames (150-250)...")
    while frame_idx <= 250:
        ret, frame = cap.read()
        if not ret: break
            
        fgmask = fgbg.apply(frame)
        
        if frame_idx % 2 == 0:
            h, w = frame.shape[:2]
            results = model(frame, verbose=False)[0]
            forklift_box = None
            forklift_xywh = None
            
            for b in results.boxes:
                c_name = model.names[int(b.cls[0])]
                conf = float(b.conf[0])
                if c_name in ["car", "truck", "bus", "forklift"] and conf > 0.3:
                    forklift_xywh = b.xywhn[0].tolist()
                    xyxy = b.xyxy[0].tolist()
                    forklift_box = [int(v) for v in xyxy]
                    break
            
            person_xywh = None
            if forklift_box is not None:
                fx1, fy1, fx2, fy2 = forklift_box
                pad = 15
                fgmask[max(0, fy1-pad):min(h, fy2+pad), max(0, fx1-pad):min(w, fx2+pad)] = 0
                
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_DILATE, kernel, iterations=2)
                
                contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                best_person = None
                max_area = 0
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if 300 < area < 5000:
                        x, y, cw, ch = cv2.boundingRect(cnt)
                        fcx, fcy = (fx1+fx2)/2, (fy1+fy2)/2
                        pcx, pcy = x + cw/2, y + ch/2
                        dist = np.hypot(fcx - pcx, fcy - pcy)
                        if dist < 300 and area > max_area:
                            max_area = area
                            best_person = (x, y, cw, ch)
                
                if best_person is not None:
                    px, py, pw, ph = best_person
                    pxc, pyc = (px + pw/2) / w, (py + ph/2) / h
                    pnw, pnh = pw / w, ph / h
                    person_xywh = [pxc, pyc, pnw, pnh]
            
            if forklift_xywh is not None:
                boxes_str = [f"0 {forklift_xywh[0]:.6f} {forklift_xywh[1]:.6f} {forklift_xywh[2]:.6f} {forklift_xywh[3]:.6f}"]
                if person_xywh is not None:
                    boxes_str.append(f"1 {person_xywh[0]:.6f} {person_xywh[1]:.6f} {person_xywh[2]:.6f} {person_xywh[3]:.6f}")
                
                fname = f"test_critical_f{frame_idx:04d}"
                cv2.imwrite(str(OUT_IMG_DIR / f"{fname}.jpg"), frame)
                (OUT_LBL_DIR / f"{fname}.txt").write_text("\n".join(boxes_str) + "\n")
                saved += 1
                
        frame_idx += 1
        
    cap.release()
    print(f"Saved {saved} critical frames to V1.0 dataset.")

if __name__ == "__main__":
    main()
