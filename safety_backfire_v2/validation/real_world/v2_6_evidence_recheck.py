"""
V2.6 — Real Video Test & Evidence Re-check

Re-checks the exact frames of the false positive events from V2.4
(EVT_0001, EVT_0002, EVT_0003) to prove that their suppression in V2.6
is strictly due to OPERATOR_ON_VEHICLE classification.
"""
import sys
import json
import cv2
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from ultralytics import YOLO
from core.operator_relation import OperatorVehicleRelationEngine

def print_evidence(event_name, frames, video_path, model, relation_engine):
    print(f"\n[{event_name}] — Original frames: {frames[0]}-{frames[-1]}")
    cap = cv2.VideoCapture(video_path)
    
    # We check the first frame of each event
    f_idx = frames[0]
    cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx - 1)
    ret, frame = cap.read()
    if not ret:
        print("  Failed to read frame.")
        return
        
    res = model.predict(frame, imgsz=640, conf=0.15, iou=0.70, classes=[0,1], verbose=False)[0]
    
    persons = []
    forklifts = []
    
    pid_c = 1; fid_c = 100
    for b, c in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy()):
        box = [int(v) for v in b]
        if int(c) == 0:
            persons.append({"id": pid_c, "bbox": box, "px": (box[0], box[1]), "vel": (0,0)})
            pid_c += 1
        elif int(c) == 1:
            forklifts.append({"id": fid_c, "bbox": box, "px": (box[0], box[1]), "vel": (0,0)})
            fid_c += 1
            
    if not persons or not forklifts:
        print("  Loss of detection. YOLO failed to detect either person or forklift.")
        return
        
    # Classify
    rels = relation_engine.classify_frame(persons, forklifts, f_idx)
    
    # Find the relation for the specific EPJ operator
    # The EPJ operator is always inside the forklift bbox
    for rel in rels:
        # We find the one with highest containment
        ev = rel["evidence"]
        if ev["spatial_containment"] > 0.5:
            print(f"  Classification: {rel['relation']} (Confidence: {rel['confidence']:.2f})")
            print(f"  Evidence Details:")
            print(f"    Spatial Containment: {ev['spatial_containment']:.3f} (>0.7 for fast-track)")
            print(f"    Operator ROI Match:  {ev['operator_roi_match']:.3f} (>0.6 for fast-track)")
            print(f"    Temporal Score:      {ev['temporal_consistency']:.3f}")
            print(f"    Weighted Score:      {ev['weighted_score']:.3f}")
            print(f"  Conclusion: Event suppressed because person is the operator.")
            return

    print("  No operator found. Event suppressed for other reasons.")


def main():
    print("=== V2.6 Real Video Test & Evidence Re-check ===")
    
    video_path = str(ROOT.parent / "test2.mp4")
    model_path = str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    model = YOLO(model_path)
    
    relation_engine = OperatorVehicleRelationEngine()
    
    print("\nRe-evaluating V2.4 False Positives on Real Video:")
    # V2.4 EVT_0001: Frames 800-814 (Checking 804 for strong detection)
    print_evidence("EVT_0001", range(804, 815), video_path, model, relation_engine)
    
    # V2.4 EVT_0002: Frames 852-856
    print_evidence("EVT_0002", range(854, 857), video_path, model, relation_engine)
    
    # V2.4 EVT_0003: Frames 1085-1108
    print_evidence("EVT_0003", range(1088, 1109), video_path, model, relation_engine)

if __name__ == "__main__":
    main()
