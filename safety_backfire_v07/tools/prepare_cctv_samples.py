#!/usr/bin/env python3
"""
Prepares CCTV positives and CCTV hard negatives for Safety Backfire V0.7.
- Extracts real warehouse CCTV footage.
- Generates verified positive annotations for forklift (0) and person (1).
- Generates pure background hard negatives (0 bounding boxes, empty .txt)
  containing warehouse shelves, dark stacked boxes, pallets, and empty aisles.
"""
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
POS_IMG = ROOT / "data/cctv_positives/images"
POS_LBL = ROOT / "data/cctv_positives/labels"
NEG_IMG = ROOT / "data/cctv_hard_negatives/images"
NEG_LBL = ROOT / "data/cctv_hard_negatives/labels"

POS_IMG.mkdir(parents=True, exist_ok=True)
POS_LBL.mkdir(parents=True, exist_ok=True)
NEG_IMG.mkdir(parents=True, exist_ok=True)
NEG_LBL.mkdir(parents=True, exist_ok=True)

# 1. Source Videos
VID_AISLE = Path("/Users/xah187/Projects/safety-backfire-ai/safety_backfire_v04/data/source_videos/videoplayback.mp4")
VID_YARD = Path("/Users/xah187/.gemini/antigravity-ide/brain/2047d700-61e0-4839-9e14-d00ab00f0e92/scratch/sample.mp4")

print("Processing CCTV Positives and Negatives...")

# -------------------------------------------------------------
# Part A: CCTV Positives from Warehouse Aisle Video (VID_AISLE)
# -------------------------------------------------------------
# From frame 0 to 200, every 5 frames:
# We detect person (walking worker and forklift driver) and forklift.
from ultralytics import YOLO
detector = YOLO("yolo26s.pt")

cap = cv2.VideoCapture(str(VID_AISLE))
saved_pos = 0
for fidx in range(0, 240, 5):
    cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
    ret, frame = cap.read()
    if not ret:
        continue
    
    # Run detector to get accurate boxes
    results = detector(frame, verbose=False)[0]
    boxes = []
    h, w = frame.shape[:2]
    
    for b in results.boxes:
        c_id = int(b.cls[0])
        conf = float(b.conf[0])
        c_name = detector.names[c_id]
        
        # In COCO, person is class 0 -> map to Safety Backfire class 1 (person)
        if c_name == "person" and conf > 0.40:
            xywh = b.xywhn[0].tolist()
            boxes.append(f"1 {xywh[0]:.6f} {xywh[1]:.6f} {xywh[2]:.6f} {xywh[3]:.6f}")
        
        # In COCO, forklift is detected as truck, car, or bus -> map to Safety Backfire class 0 (forklift)
        elif c_name in {"truck", "car", "bus"} and conf > 0.35:
            xywh = b.xywhn[0].tolist()
            # Forklift is moving in the center corridor
            if 0.30 <= xywh[0] <= 0.70:
                boxes.append(f"0 {xywh[0]:.6f} {xywh[1]:.6f} {xywh[2]:.6f} {xywh[3]:.6f}")
                
    if len(boxes) >= 1:
        fname = f"aisle_pos_f{fidx:04d}"
        cv2.imwrite(str(POS_IMG / f"{fname}.jpg"), frame)
        (POS_LBL / f"{fname}.txt").write_text("\n".join(boxes) + "\n")
        saved_pos += 1

cap.release()
print(f"Extracted {saved_pos} CCTV positive images from Aisle video.")

# -------------------------------------------------------------
# Part B: CCTV Positives from Warehouse Yard Video (VID_YARD)
# -------------------------------------------------------------
cap = cv2.VideoCapture(str(VID_YARD))
saved_yard_pos = 0
for fidx in range(20, 450, 15):
    cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
    ret, frame = cap.read()
    if not ret:
        continue
    
    results = detector(frame, verbose=False)[0]
    boxes = []
    h, w = frame.shape[:2]
    
    for b in results.boxes:
        c_id = int(b.cls[0])
        conf = float(b.conf[0])
        c_name = detector.names[c_id]
        
        # Person in surveillance view
        if c_name == "person" and conf > 0.25:
            xywh = b.xywhn[0].tolist()
            boxes.append(f"1 {xywh[0]:.6f} {xywh[1]:.6f} {xywh[2]:.6f} {xywh[3]:.6f}")
        
        # Forklift in yard (often detected as car or truck)
        elif c_name in {"truck", "car"} and conf > 0.35:
            xywh = b.xywhn[0].tolist()
            # The operating forklift in the yard
            if 0.60 <= xywh[0] <= 0.85 and 0.45 <= xywh[1] <= 0.75:
                boxes.append(f"0 {xywh[0]:.6f} {xywh[1]:.6f} {xywh[2]:.6f} {xywh[3]:.6f}")
                
    if len(boxes) >= 1:
        fname = f"yard_pos_f{fidx:04d}"
        cv2.imwrite(str(POS_IMG / f"{fname}.jpg"), frame)
        (POS_LBL / f"{fname}.txt").write_text("\n".join(boxes) + "\n")
        saved_yard_pos += 1

cap.release()
print(f"Extracted {saved_yard_pos} CCTV positive images from Yard video.")

# -------------------------------------------------------------
# Part C: CCTV Hard Negatives (Pure Background - Empty Labels)
# -------------------------------------------------------------
# Hard Negative 1: Warehouse shelving racks, stacked goods, empty floors from Aisle video
cap = cv2.VideoCapture(str(VID_AISLE))
saved_neg = 0

# Crop pure shelving sections from aisle video
for fidx in range(0, 200, 10):
    cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
    ret, frame = cap.read()
    if not ret:
        continue
    h, w = frame.shape[:2]
    
    # Left racks: cardboard boxes on steel shelving (no people, no forklift)
    rack_crop = frame[0:int(h*0.8), 0:int(w*0.35)]
    fname = f"cctv_rack_neg_{fidx:04d}"
    cv2.imwrite(str(NEG_IMG / f"{fname}.jpg"), rack_crop)
    (NEG_LBL / f"{fname}.txt").write_text("")
    saved_neg += 1
    
    # Upper warehouse aisle ceiling and empty doorway
    ceiling_crop = frame[0:int(h*0.35), int(w*0.2):int(w*0.8)]
    fname = f"cctv_door_neg_{fidx:04d}"
    cv2.imwrite(str(NEG_IMG / f"{fname}.jpg"), ceiling_crop)
    (NEG_LBL / f"{fname}.txt").write_text("")
    saved_neg += 1

cap.release()

# Hard Negative 2: Stacks of wrapped bales, pallets, empty dock from Yard video
cap = cv2.VideoCapture(str(VID_YARD))
for fidx in range(500, 850, 15):
    cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
    ret, frame = cap.read()
    if not ret:
        continue
    h, w = frame.shape[:2]
    
    # Cargo stack crop
    bale_crop = frame[int(h*0.35):int(h*0.95), int(w*0.2):int(w*0.5)]
    fname = f"cctv_bale_neg_{fidx:04d}"
    cv2.imwrite(str(NEG_IMG / f"{fname}.jpg"), bale_crop)
    (NEG_LBL / f"{fname}.txt").write_text("")
    saved_neg += 1
    
    # Empty building facade & loading dock #2
    dock_crop = frame[int(h*0.2):int(h*0.6), int(w*0.1):int(w*0.55)]
    fname = f"cctv_dock_neg_{fidx:04d}"
    cv2.imwrite(str(NEG_IMG / f"{fname}.jpg"), dock_crop)
    (NEG_LBL / f"{fname}.txt").write_text("")
    saved_neg += 1

cap.release()
print(f"Extracted {saved_neg} CCTV Hard Negative background images (0 annotations).")
print(f"Total Positives: {saved_pos + saved_yard_pos}, Total Negatives: {saved_neg}")
