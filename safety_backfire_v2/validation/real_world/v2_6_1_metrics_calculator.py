"""
V2.6.1 — Integrity Metrics Calculator

Calculates metrics strictly based on what is mathematically provable.
Declares NOT COMPUTABLE for metrics lacking human Ground Truth.
"""
import sys
import json
import cv2
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

def main():
    print("=== V2.6.1 Validation Integrity Metrics ===\n")
    
    # 1. Detection Metrics
    print("--- 1. Detection Metrics (Person & Forklift) ---")
    print("  Precision: NOT COMPUTABLE (Requires human-drawn bounding boxes for IoU matching)")
    print("  Recall:    NOT COMPUTABLE (Requires human-drawn bounding boxes for IoU matching)")
    print("  F1-Score:  NOT COMPUTABLE\n")
    
    # 2. Tracking Metrics
    print("--- 2. Tracking Metrics ---")
    print("  IDF1:       NOT COMPUTABLE (Requires contiguous human-drawn track IDs)")
    print("  ID Switch:  NOT COMPUTABLE (YOLO/IoU tracker known to switch on fast occlusion)\n")
    
    # 3. Operator Relation Metrics
    print("--- 3. Operator Relation Metrics (Semantic Computation) ---")
    
    gt_path = ROOT / "validation/real_world/annotations/micro_gt_v2_6_1.json"
    video_path = str(ROOT.parent / "test2.mp4")
    
    with open(gt_path) as f:
        gt_data = json.load(f)
        
    from ultralytics import YOLO
    from core.operator_relation import OperatorVehicleRelationEngine
    
    model = YOLO(str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"))
    relation_engine = OperatorVehicleRelationEngine()
    
    results = {
        "True_OP_Pred_OP": 0,
        "True_OP_Pred_IND": 0,
        "True_OP_Pred_UNK": 0
    }
    
    cap = cv2.VideoCapture(video_path)
    frames_processed = 0
    detected_persons = 0
    
    for fr in gt_data["frames"]:
        f_idx = fr["frame"]
        
        # We only evaluate if there is a known person in GT
        has_person_gt = any(o["class"] == "person" for o in fr["objects"])
        if not has_person_gt:
            continue
            
        frames_processed += 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx - 1)
        ret, frame = cap.read()
        if not ret: continue
        
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
                
        # If YOLO didn't detect the person, it's a detection failure, not a relation failure.
        # We only evaluate Relation Engine on successful detections.
        if not persons:
            continue
            
        detected_persons += len(persons)
        rels = relation_engine.classify_frame(persons, forklifts, f_idx)
        
        for p in persons:
            rel_record = next((r for r in rels if r["person_id"] == p["id"]), None)
            best_pred = rel_record["relation"] if rel_record else "UNKNOWN"
            
            if rel_record and frames_processed < 5:
                ev = rel_record['evidence']
                print(f"Debug [Frame {f_idx}]: Rel={best_pred}, Cont={ev['spatial_containment']:.2f}, ROI={ev['operator_roi_match']:.2f}, Score={ev['weighted_score']:.2f}")
                
            if best_pred == "OPERATOR_ON_VEHICLE": results["True_OP_Pred_OP"] += 1
            elif best_pred == "INDEPENDENT_PEDESTRIAN": results["True_OP_Pred_IND"] += 1
            else: results["True_OP_Pred_UNK"] += 1
            
    cap.release()
    
    tp_op = results["True_OP_Pred_OP"]
    fn_op = results["True_OP_Pred_IND"] + results["True_OP_Pred_UNK"]
    
    op_rec = tp_op / (tp_op + fn_op) if (tp_op + fn_op) > 0 else 0
    
    print("Confusion Matrix (Partial):")
    print(f"  GT Operator -> Pred Operator:   {results['True_OP_Pred_OP']}")
    print(f"  GT Operator -> Pred Pedestrian: {results['True_OP_Pred_IND']}")
    print(f"  GT Operator -> Pred Unknown:    {results['True_OP_Pred_UNK']}")
    print("  GT Pedestrian -> NOT COMPUTABLE (No real independent pedestrians in sample)")
    
    print("\nOperator Metrics:")
    print("  Precision: NOT COMPUTABLE (Requires GT Pedestrians to calculate False Positives)")
    print(f"  Recall:    {op_rec:.3f} (Evaluated on {detected_persons} successful person detections)")
    print("  F1-Score:  NOT COMPUTABLE\n")

if __name__ == "__main__":
    main()
