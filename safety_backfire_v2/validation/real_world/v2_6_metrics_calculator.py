"""
V2.6 — Metrics Calculator

Calculates Operator Classification Metrics (Precision, Recall, F1)
and Tracking Metrics (IDF1, ID Switches, Continuity) by comparing
system outputs against the V2.6 Independent Ground Truth.
"""
import sys
import json
import math
import cv2
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

def compute_iou(boxA, boxB):
    # Determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou


def calculate_tracking_metrics(gt_data, video_path):
    """
    Calculate basic tracking metrics for the sequences by running YOLO tracker.
    IDF1 approximation: How consistently does a model track ID map to a GT track ID.
    ID Switches: How many times does a GT ID change its assigned model ID.
    """
    print("\n--- 1. Tracking Metrics ---")
    
    from ultralytics import YOLO
    model = YOLO(str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"))
    
    # Organize GT sequences
    seq_frames = [fr["frame"] for fr in gt_data["frames"] if fr.get("is_consecutive_sequence", False)]
    if not seq_frames:
        print("No consecutive sequences found in GT.")
        return
        
    start_frame = min(seq_frames)
    end_frame = max(seq_frames)
    
    # Organize GT tracks: gt_id -> {frame: bbox}
    gt_tracks = defaultdict(dict)
    for fr in gt_data["frames"]:
        f_idx = fr["frame"]
        if f_idx not in seq_frames: continue
        for obj in fr["objects"]:
            if "bbox" in obj:
                gt_tracks[obj["gt_id"]][f_idx] = obj["bbox"]
                
    print(f"Evaluating tracking on frames {start_frame}-{end_frame}...")
    
    cap = cv2.VideoCapture(video_path)
    
    # Run YOLO Tracker over the range
    mod_tracks = defaultdict(dict) # mod_id -> {frame: bbox}
    
    for f_idx in range(start_frame, end_frame + 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx - 1)
        ret, frame = cap.read()
        if not ret: break
        
        # Run tracking
        res = model.track(frame, persist=True, imgsz=640, conf=0.20, iou=0.70, classes=[0,1], verbose=False)[0]
        
        if res.boxes.id is not None:
            for b, tid in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.id.cpu().numpy()):
                mod_tracks[int(tid)][f_idx] = [int(v) for v in b]
                
    cap.release()
    
    # Calculate ID Switches and IDF1
    total_id_switches = 0
    
    for gt_id, gt_frames in gt_tracks.items():
        mapped_mods = []
        current_mod_id = None
        
        # Sort frames to trace sequentially
        for f_idx in sorted(gt_frames.keys()):
            bbox = gt_frames[f_idx]
            
            # Find highest IoU model ID in this frame
            matched_mod_id = None
            best_iou = 0
            
            for m_id, m_frames in mod_tracks.items():
                if f_idx in m_frames:
                    iou = compute_iou(bbox, m_frames[f_idx])
                    if iou > 0.3 and iou > best_iou:
                        best_iou = iou
                        matched_mod_id = m_id
            
            if matched_mod_id is not None:
                mapped_mods.append(matched_mod_id)
                if current_mod_id is not None and matched_mod_id != current_mod_id:
                    total_id_switches += 1
                current_mod_id = matched_mod_id

        # Calculate IDF1 (Simplified): max contiguous frames with same ID / total frames
        if mapped_mods:
            from collections import Counter
            most_common_id, count = Counter(mapped_mods).most_common(1)[0]
            idf1 = count / len(gt_frames)
        else:
            idf1 = 0.0
            
        print(f"Track {gt_id}:")
        print(f"  Total Frames: {len(gt_frames)}")
        print(f"  Recall (Matched): {len(mapped_mods)} / {len(gt_frames)}")
        print(f"  IDF1 (Dominant ID Consistency): {idf1:.2f}")
        
    print(f"\nTotal ID Switches across all tracks: {total_id_switches}")


def calculate_classification_metrics(gt_data, video_path):
    """
    Run YOLO + Relation Engine on the GT frames to build the Confusion Matrix.
    """
    print("\n--- 2. Operator Classification Metrics ---")
    
    from ultralytics import YOLO
    from core.operator_relation import OperatorVehicleRelationEngine
    
    model = YOLO(str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"))
    relation_engine = OperatorVehicleRelationEngine()
    cap = cv2.VideoCapture(video_path)
    
    # Confusion Matrix
    # [True OPERATOR, True INDEPENDENT] vs [Pred OPERATOR, Pred INDEPENDENT, Pred UNKNOWN]
    results = {
        "True_OP_Pred_OP": 0,
        "True_OP_Pred_IND": 0,
        "True_OP_Pred_UNK": 0,
        "True_IND_Pred_OP": 0,
        "True_IND_Pred_IND": 0,
        "True_IND_Pred_UNK": 0,
    }
    
    # We only care about persons in GT
    for fr in gt_data["frames"]:
        f_idx = fr["frame"]
        
        # Get GT persons
        gt_persons = [o for o in fr["objects"] if o["class"] == "person"]
        if not gt_persons:
            continue
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx - 1)
        ret, frame = cap.read()
        if not ret: continue
        
        # Run YOLO
        res = model.predict(frame, imgsz=640, conf=0.20, iou=0.70, classes=[0,1], verbose=False)[0]
        
        det_persons = []
        det_forklifts = []
        
        # Track IDs are fake just for the engine
        pid_counter = 1
        fid_counter = 100
        
        for b, c in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy()):
            box = [int(v) for v in b]
            if int(c) == 0:
                det_persons.append({"id": pid_counter, "bbox": box, "px": (box[0], box[1])})
                pid_counter += 1
            else:
                det_forklifts.append({"id": fid_counter, "bbox": box, "px": (box[0], box[1])})
                fid_counter += 1
                
        # Classify
        preds = relation_engine.classify_frame(det_persons, det_forklifts, f_idx)
        
        # Match GT persons to Detections
        for gt_p in gt_persons:
            gt_rel = gt_p.get("person_relation", "INDEPENDENT_PEDESTRIAN")
            
            # Find best matching detection by IoU
            best_iou = 0
            best_pred = "UNKNOWN"
            
            for dp in det_persons:
                iou = compute_iou(gt_p["bbox"], dp["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    # Find what relation engine said for this person
                    rel_record = next((r for r in preds if r["person_id"] == dp["id"]), None)
                    if rel_record:
                        best_pred = rel_record["relation"]
            
            if best_iou < 0.3:
                continue # Missed detection, don't count towards classification confusion matrix
                
            # Update matrix
            if gt_rel == "OPERATOR_ON_VEHICLE":
                if best_pred == "OPERATOR_ON_VEHICLE": results["True_OP_Pred_OP"] += 1
                elif best_pred == "INDEPENDENT_PEDESTRIAN": results["True_OP_Pred_IND"] += 1
                else: results["True_OP_Pred_UNK"] += 1
            else:
                if best_pred == "OPERATOR_ON_VEHICLE": results["True_IND_Pred_OP"] += 1
                elif best_pred == "INDEPENDENT_PEDESTRIAN": results["True_IND_Pred_IND"] += 1
                else: results["True_IND_Pred_UNK"] += 1
                
    cap.release()
    
    # Calculate Precision, Recall, F1 for Operator
    tp_op = results["True_OP_Pred_OP"]
    fp_op = results["True_IND_Pred_OP"]
    fn_op = results["True_OP_Pred_IND"] + results["True_OP_Pred_UNK"]
    
    op_prec = tp_op / (tp_op + fp_op) if (tp_op + fp_op) > 0 else 0
    op_rec = tp_op / (tp_op + fn_op) if (tp_op + fn_op) > 0 else 0
    op_f1 = 2 * (op_prec * op_rec) / (op_prec + op_rec) if (op_prec + op_rec) > 0 else 0
    
    print("\nConfusion Matrix:")
    for k, v in results.items():
        print(f"  {k}: {v}")
        
    print("\nOperator Metrics:")
    print(f"  Precision: {op_prec:.3f}")
    print(f"  Recall:    {op_rec:.3f}")
    print(f"  F1-Score:  {op_f1:.3f}")
    

def main():
    print("=== V2.6 Metrics Calculator ===")
    
    gt_path = ROOT / "validation/real_world/annotations/independent_gt_v2_6.json"
    traj_path = ROOT / "outputs/trajectories.json"
    video_path = str(ROOT.parent / "test2.mp4")
    
    with open(gt_path) as f:
        gt_data = json.load(f)
        
    calculate_tracking_metrics(gt_data, video_path)
    calculate_classification_metrics(gt_data, video_path)


if __name__ == "__main__":
    main()
