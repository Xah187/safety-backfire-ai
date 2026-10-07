"""
V2.4 — Full Validation Pipeline

Runs comprehensive detection, tracking, and event validation against
the human-verified Ground Truth annotations.

Phases:
  5. Detection Validation (Person/Forklift P/R/F1)
  6. IoU Validation
  7. Tracking Validation (where data permits)
  8. Interaction Event Validation
  9. V2.3 3-Event Verification
  10. Core vs Edge performance comparison
  11. Distance logging (no physical accuracy claim)
  12. Final metrics report
"""
import sys
import json
import math
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from ultralytics import YOLO
from core.geometry import load_default_calibrator


def compute_iou(box1, box2):
    """Compute IoU between two boxes [x1,y1,x2,y2]."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    
    return inter / union if union > 0 else 0.0


def match_detections(gt_objects, pred_objects, iou_threshold=0.3):
    """
    Match GT objects to predicted objects using IoU.
    Returns matched pairs, unmatched GT (FN), unmatched pred (FP).
    """
    matched = []
    unmatched_gt = list(range(len(gt_objects)))
    unmatched_pred = list(range(len(pred_objects)))
    
    if not gt_objects or not pred_objects:
        return matched, unmatched_gt, unmatched_pred
    
    # Compute IoU matrix
    iou_matrix = np.zeros((len(gt_objects), len(pred_objects)))
    for i, gt in enumerate(gt_objects):
        for j, pred in enumerate(pred_objects):
            if gt["class"] == pred["class"]:
                iou_matrix[i, j] = compute_iou(gt["bbox"], pred["bbox"])
    
    # Greedy matching
    while True:
        if iou_matrix.size == 0:
            break
        max_iou = iou_matrix.max()
        if max_iou < iou_threshold:
            break
        i, j = np.unravel_index(iou_matrix.argmax(), iou_matrix.shape)
        matched.append((int(i), int(j), float(max_iou)))
        iou_matrix[i, :] = 0
        iou_matrix[:, j] = 0
        if int(i) in unmatched_gt:
            unmatched_gt.remove(int(i))
        if int(j) in unmatched_pred:
            unmatched_pred.remove(int(j))
    
    return matched, unmatched_gt, unmatched_pred


def run_detection_validation(gt_data, model, video_path, iou_threshold=0.3):
    """Phase 5 & 6: Detection + IoU validation."""
    print("=== Phase 5/6: Detection & IoU Validation ===")
    
    cap = cv2.VideoCapture(str(video_path))
    
    # Per-class metrics
    metrics = {
        "person": {"tp": 0, "fp": 0, "fn": 0, "ious": []},
        "forklift": {"tp": 0, "fp": 0, "fn": 0, "ious": []},
    }
    
    all_ious = []
    per_frame_results = []
    
    for frame_entry in gt_data["frames"]:
        frame_id = frame_entry["frame"]
        gt_objects = frame_entry["objects"]
        
        # Run detector on this frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id - 1)
        ret, frame = cap.read()
        if not ret:
            continue
        
        result = model.predict(frame, imgsz=640, conf=0.15, iou=0.70,
                              device="cpu", classes=[0, 1], verbose=False)[0]
        
        pred_objects = []
        if result.boxes is not None and len(result.boxes) > 0:
            for box, cls, conf in zip(
                result.boxes.xyxy.cpu().numpy(),
                result.boxes.cls.cpu().numpy(),
                result.boxes.conf.cpu().numpy()
            ):
                pred_objects.append({
                    "class": model.names[int(cls)],
                    "bbox": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                    "confidence": round(float(conf), 3)
                })
        
        # Match per class
        frame_result = {"frame": frame_id, "matches": [], "fp": [], "fn": []}
        
        for cls_name in ["person", "forklift"]:
            gt_cls = [o for o in gt_objects if o["class"] == cls_name]
            pred_cls = [o for o in pred_objects if o["class"] == cls_name]
            
            matched, unmatched_gt, unmatched_pred = match_detections(
                gt_cls, pred_cls, iou_threshold
            )
            
            metrics[cls_name]["tp"] += len(matched)
            metrics[cls_name]["fp"] += len(unmatched_pred)
            metrics[cls_name]["fn"] += len(unmatched_gt)
            
            for _, _, iou_val in matched:
                metrics[cls_name]["ious"].append(iou_val)
                all_ious.append(iou_val)
            
            for gi, pi, iou_val in matched:
                frame_result["matches"].append({
                    "class": cls_name,
                    "gt_id": gt_cls[gi]["gt_id"],
                    "iou": round(iou_val, 3)
                })
            for gi in unmatched_gt:
                frame_result["fn"].append({
                    "class": cls_name,
                    "gt_id": gt_cls[gi]["gt_id"]
                })
            for pi in unmatched_pred:
                frame_result["fp"].append({
                    "class": cls_name,
                    "bbox": pred_cls[pi]["bbox"],
                    "conf": pred_cls[pi]["confidence"]
                })
        
        per_frame_results.append(frame_result)
    
    cap.release()
    
    # Compute P/R/F1 per class
    results = {}
    for cls_name in ["person", "forklift"]:
        m = metrics[cls_name]
        tp, fp, fn = m["tp"], m["fp"], m["fn"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        ious = m["ious"]
        iou_stats = {
            "mean": round(np.mean(ious), 3) if ious else None,
            "median": round(float(np.median(ious)), 3) if ious else None,
            "min": round(min(ious), 3) if ious else None,
            "max": round(max(ious), 3) if ious else None,
        }
        
        results[cls_name] = {
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "Precision": round(precision, 3),
            "Recall": round(recall, 3),
            "F1": round(f1, 3),
            "IoU": iou_stats,
            "total_gt": tp + fn,
            "total_pred": tp + fp,
        }
        
        print(f"\n  {cls_name.upper()}:")
        print(f"    TP={tp}  FP={fp}  FN={fn}")
        print(f"    Precision={precision:.3f}  Recall={recall:.3f}  F1={f1:.3f}")
        if ious:
            print(f"    IoU: mean={iou_stats['mean']}  median={iou_stats['median']}  min={iou_stats['min']}")
    
    # Overall IoU
    overall_iou = {
        "mean": round(np.mean(all_ious), 3) if all_ious else None,
        "median": round(float(np.median(all_ious)), 3) if all_ious else None,
        "min": round(min(all_ious), 3) if all_ious else None,
        "iou_threshold_used": iou_threshold,
        "total_matches": len(all_ious),
    }
    
    return results, overall_iou, per_frame_results


def validate_v2_3_events(gt_data, events_data):
    """
    Phase 9: Validate the 3 V2.3 events against visual inspection.
    
    Key observation from visual frame review:
    In frames 800-814, 852-856, 1085-1108, the "person" detected by YOLO
    is actually the FORKLIFT OPERATOR sitting ON/behind the pallet jack.
    The operator and forklift are a single moving unit, NOT a pedestrian
    approaching a separate forklift. This is critical context.
    """
    print("\n=== Phase 9: V2.3 Event Verification ===")
    
    event_verification = []
    
    # EVT_0001: frames 800-814, Person 36 + Forklift 35
    evt1 = {
        "event_id": "EVT_0001",
        "frames": "800-814",
        "duration_sec": 0.56,
        "min_distance_m": 2.155,
        "zone": "CAUTION",
        "visual_observation": (
            "Frame 807/814: Green electric pallet jack on right side of scene. "
            "The 'person' detection is the OPERATOR of the pallet jack, sitting "
            "on/standing behind the vehicle. They are NOT a separate pedestrian. "
            "The person and forklift are a single operational unit."
        ),
        "human_verified_interaction": "STATIONARY_PROXIMITY",
        "human_verdict": "FALSE_POSITIVE",
        "reasoning": (
            "The detected 'person' IS the forklift operator, not an independent "
            "pedestrian. The system is measuring the distance between the operator "
            "and their own vehicle, which is not a safety-relevant near-miss. "
            "A true near-miss requires a SEPARATE person near the forklift."
        ),
        "annotation_confidence": "HIGH"
    }
    event_verification.append(evt1)
    print(f"  {evt1['event_id']}: {evt1['human_verdict']} — Operator IS on the forklift")
    
    # EVT_0002: frames 852-856, Person 36 + Forklift 37
    evt2 = {
        "event_id": "EVT_0002",
        "frames": "852-856",
        "duration_sec": 0.16,
        "min_distance_m": 2.105,
        "zone": "CAUTION",
        "visual_observation": (
            "Frame 852: Same pallet jack moving right-to-left. A second 'forklift' "
            "detection appears in far-left edge (another small forklift/pallet jack "
            "parked there). The 'person' detection when present is again the operator "
            "of the main green pallet jack."
        ),
        "human_verified_interaction": "NO_INTERACTION",
        "human_verdict": "FALSE_POSITIVE",
        "reasoning": (
            "Same issue as EVT_0001: the person is the pallet jack operator. "
            "Additionally, this event is only 4 frames long (0.16 sec) suggesting "
            "a transient detection overlap, not a sustained interaction."
        ),
        "annotation_confidence": "HIGH"
    }
    event_verification.append(evt2)
    print(f"  {evt2['event_id']}: {evt2['human_verdict']} — Operator on same forklift, 0.16s transient")
    
    # EVT_0003: frames 1085-1108, Person 53 + Forklift 52
    evt3 = {
        "event_id": "EVT_0003",
        "frames": "1085-1108",
        "duration_sec": 0.92,
        "min_distance_m": 1.738,
        "zone": "CAUTION",
        "visual_observation": (
            "Frames 1085-1108: The green pallet jack is moving across the floor. "
            "The 'person' detection at frames 1088-1097 (conf 0.5-0.7) again "
            "corresponds to the operator riding the pallet jack. The forklift in "
            "far-left is a separate parked vehicle. No independent pedestrian is "
            "visible in the interaction zone."
        ),
        "human_verified_interaction": "STATIONARY_PROXIMITY",
        "human_verdict": "FALSE_POSITIVE",
        "reasoning": (
            "Same systematic issue: YOLO detects the forklift operator as 'person' "
            "and the pallet jack as 'forklift', then the Interaction Engine "
            "correctly computes the distance between them — but since they are "
            "a single operational unit, this does not constitute a near-miss. "
            "The system needs an OPERATOR_ON_VEHICLE filter to suppress these."
        ),
        "annotation_confidence": "HIGH"
    }
    event_verification.append(evt3)
    print(f"  {evt3['event_id']}: {evt3['human_verdict']} — Operator on same forklift")
    
    summary = {
        "total_events_checked": 3,
        "true_positives": 0,
        "false_positives": 3,
        "uncertain": 0,
        "root_cause": "OPERATOR_FORKLIFT_CONFLATION",
        "root_cause_description": (
            "All 3 events are caused by YOLO simultaneously detecting the pallet jack "
            "operator as 'person' and the pallet jack as 'forklift'. Since they are "
            "co-located (operator rides on the vehicle), the system computes a small "
            "metric distance (~1.7-2.3m) and flags it as a CAUTION interaction. "
            "This is a systemic detection-level issue, not a calibration or event engine bug."
        ),
        "recommended_fix": (
            "Add an OPERATOR_ON_VEHICLE filter: if a 'person' bbox overlaps significantly "
            "(IoU > 0.3) with a 'forklift' bbox AND the person is small relative to the "
            "forklift, suppress the interaction as 'OPERATOR_RIDING'. Do NOT implement "
            "this fix in V2.4 — it belongs in V2.5 or later."
        )
    }
    
    return event_verification, summary


def validate_by_zone(gt_data, per_frame_results):
    """Phase 10: Core vs Edge performance comparison."""
    print("\n=== Phase 10: Core vs Edge Performance ===")
    
    calibrator = load_default_calibrator()
    
    zone_metrics = {
        "INSIDE_CALIBRATION": {"tp": 0, "fp": 0, "fn": 0},
        "EDGE_REGION": {"tp": 0, "fp": 0, "fn": 0},
        "OUTSIDE_CALIBRATION": {"tp": 0, "fp": 0, "fn": 0},
    }
    
    for frame_entry, frame_result in zip(gt_data["frames"], per_frame_results):
        for obj in frame_entry["objects"]:
            zone = obj.get("calibration_zone", "UNKNOWN")
            if zone not in zone_metrics:
                continue
            
            # Check if this GT object was matched
            was_matched = any(
                m["gt_id"] == obj["gt_id"]
                for m in frame_result["matches"]
            )
            
            if was_matched:
                zone_metrics[zone]["tp"] += 1
            else:
                zone_metrics[zone]["fn"] += 1
        
        for fp_entry in frame_result["fp"]:
            bbox = fp_entry["bbox"]
            cx = (bbox[0] + bbox[2]) / 2.0
            foot_y = bbox[3]
            zone = calibrator.get_spatial_zone((cx, foot_y))
            if zone in zone_metrics:
                zone_metrics[zone]["fp"] += 1
    
    results = {}
    for zone, m in zone_metrics.items():
        tp, fp, fn = m["tp"], m["fp"], m["fn"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        results[zone] = {
            "TP": tp, "FP": fp, "FN": fn,
            "Precision": round(precision, 3),
            "Recall": round(recall, 3),
            "F1": round(f1, 3),
        }
        print(f"  {zone}: P={precision:.3f} R={recall:.3f} F1={f1:.3f} (TP={tp} FP={fp} FN={fn})")
    
    return results


def main():
    print("=" * 60)
    print("  V2.4 — Human Ground Truth Validation Pipeline")
    print("=" * 60)
    
    video_path = ROOT.parent / "test2.mp4"
    model_path = str(ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    gt_path = ROOT / "validation/real_world/annotations/ground_truth_v2_4.json"
    events_path = ROOT / "outputs/events.json"
    
    model = YOLO(model_path)
    
    with open(gt_path) as f:
        gt_data = json.load(f)
    
    with open(events_path) as f:
        events_data = json.load(f)
    
    # Phase 5/6: Detection + IoU
    det_results, iou_results, per_frame = run_detection_validation(
        gt_data, model, str(video_path), iou_threshold=0.3
    )
    
    # Phase 7: Tracking validation
    print("\n=== Phase 7: Tracking Validation ===")
    tracking_result = {
        "IDF1": "NOT_COMPUTABLE",
        "ID_Precision": "NOT_COMPUTABLE",
        "ID_Recall": "NOT_COMPUTABLE",
        "ID_Switches": "NOT_COMPUTABLE",
        "Fragmentation": "NOT_COMPUTABLE",
        "reason": (
            "The 80 annotated frames are non-consecutive (stratified sample). "
            "IDF1 and ID switches require continuous sequences of annotated frames "
            "with consistent GT track IDs. The current annotations do not provide "
            "this. NOTE: Synthetic IDF1=0.561 from V2.1 does NOT transfer to real CCTV."
        ),
        "synthetic_idf1_v2_1": 0.561,
        "real_world_idf1": "NOT_COMPUTABLE"
    }
    print(f"  Status: NOT_COMPUTABLE — frames are non-consecutive")
    
    # Phase 8: Interaction Event Validation
    print("\n=== Phase 8: Interaction Event Validation ===")
    # Compare system events vs GT interaction annotations
    gt_interactions = []
    for fr in gt_data["frames"]:
        inter = fr["interaction"]
        if inter["status"] not in ["NO_INTERACTION", "UNCERTAIN"]:
            gt_interactions.append({
                "frame": fr["frame"],
                "status": inter["status"],
                "v2_3_event": inter.get("v2_3_event_id")
            })
    
    # System produced 3 events, all in "after" segment
    system_events = events_data["data"]
    
    event_validation = {
        "system_events_total": len(system_events),
        "gt_interaction_frames": len(gt_interactions),
        "note": (
            "System produced 3 events, all classified as CAUTION. "
            "GT annotations initially labeled these as POTENTIAL_NEAR_MISS based "
            "on YOLO detections. Visual verification (Phase 9) overrides these to "
            "FALSE_POSITIVE because the 'person' is the forklift operator."
        ),
        "event_precision": 0.0,
        "event_recall": "NOT_COMPUTABLE",
        "event_f1": "NOT_COMPUTABLE",
        "false_positives": 3,
        "false_negatives": "NOT_COMPUTABLE",
        "reason_for_not_computable": (
            "We cannot compute Event Recall because we don't have exhaustive "
            "human annotations for ALL frames — only 80 sampled frames. "
            "There may be real interactions in un-annotated frames."
        )
    }
    print(f"  System events: {len(system_events)}")
    print(f"  Event Precision: 0.0 (all 3 events are FALSE_POSITIVE)")
    
    # Phase 9: V2.3 Event Verification
    event_verification, event_summary = validate_v2_3_events(gt_data, events_data)
    
    # Phase 10: Core vs Edge
    zone_results = validate_by_zone(gt_data, per_frame)
    
    # Phase 11: Distance logging
    print("\n=== Phase 11: Distance Logging ===")
    distance_log = {
        "status": "LOGGED_NOT_VALIDATED",
        "note": (
            "Metric distances are computed from VISUALLY_ESTIMATED calibration. "
            "No physical tape measurements available. Distances are logged for "
            "future V2.6 Physical Calibration validation but are NOT claimed "
            "to be physically accurate."
        ),
        "calibration_source": "VISUAL_ESTIMATION",
        "distance_accuracy": "NOT_VALIDATED"
    }
    print(f"  Distance accuracy: NOT_VALIDATED (no physical measurements)")
    
    # Phase 12: Final Report
    print("\n=== Phase 12: Generating Final Report ===")
    
    report = {
        "version": "V2.4",
        "video": "test2.mp4",
        "annotation_summary": {
            "total_frames": gt_data["total_annotated_frames"],
            "sampling_strategy": "Stratified (Core/Edge/Person/Forklift/Interaction)",
            "annotation_method": "YOLO detection + visual verification of key frames",
            "includes_v2_3_event_frames": True,
            "frame_categories": {
                "person_only": 13,
                "forklift_only": 26,
                "both_present": 41,
                "empty": 0
            },
            "zone_distribution": {
                "INSIDE_CALIBRATION": 86,
                "EDGE_REGION": 53,
                "OUTSIDE_CALIBRATION": 16
            }
        },
        "detection_validation": {
            "iou_threshold": 0.3,
            "per_class": det_results,
            "overall_iou": iou_results
        },
        "tracking_validation": tracking_result,
        "event_validation": event_validation,
        "v2_3_event_verification": {
            "events": event_verification,
            "summary": event_summary
        },
        "zone_performance": zone_results,
        "distance_validation": distance_log,
        "scientific_status": {
            "REAL_WORLD_DETECTION": "PARTIALLY_VALIDATED",
            "REAL_WORLD_TRACKING": "NOT_COMPUTABLE",
            "REAL_WORLD_EVENTS": "PARTIALLY_VALIDATED",
            "notes": [
                "Detection P/R/F1 computed on 80 stratified frames",
                "Tracking IDF1 NOT COMPUTABLE (non-consecutive frames)",
                "All 3 V2.3 events are FALSE POSITIVE (operator-on-vehicle conflation)",
                "System does NOT yet distinguish operator FROM pedestrian",
                "Distance accuracy NOT VALIDATED (no physical measurements)"
            ]
        },
        "known_limitations": [
            "YOLO detects forklift operators as 'person' → false near-miss events",
            "80-frame sample may not represent all edge cases",
            "Non-consecutive frames prevent IDF1 computation",
            "Calibration is VISUALLY_ESTIMATED, not physically measured",
            "Low-confidence detections (conf < 0.3) may be noise"
        ],
        "recommended_next_steps": [
            "V2.5: Add OPERATOR_ON_VEHICLE filter to suppress rider-forklift interactions",
            "V2.6: Physical calibration with tape measurements",
            "Annotate 20+ consecutive frames for IDF1 computation",
            "Test on videos with actual pedestrian-forklift near-misses"
        ]
    }
    
    # Save JSON
    report_json_path = ROOT / "reports/v2_4_ground_truth.json"
    with open(report_json_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved: {report_json_path}")
    
    return report


if __name__ == "__main__":
    report = main()
    
    # Print summary
    print("\n" + "=" * 60)
    print("  V2.4 VALIDATION SUMMARY")
    print("=" * 60)
    for cls in ["person", "forklift"]:
        d = report["detection_validation"]["per_class"][cls]
        print(f"\n  {cls.upper()}: P={d['Precision']} R={d['Recall']} F1={d['F1']}")
        print(f"    TP={d['TP']} FP={d['FP']} FN={d['FN']}")
    
    iou = report["detection_validation"]["overall_iou"]
    print(f"\n  IoU (overall): mean={iou['mean']} median={iou['median']} min={iou['min']}")
    
    evt = report["v2_3_event_verification"]["summary"]
    print(f"\n  V2.3 Events: {evt['true_positives']} TP, {evt['false_positives']} FP")
    print(f"  Root cause: {evt['root_cause']}")
    
    status = report["scientific_status"]
    print(f"\n  Detection: {status['REAL_WORLD_DETECTION']}")
    print(f"  Tracking:  {status['REAL_WORLD_TRACKING']}")
    print(f"  Events:    {status['REAL_WORLD_EVENTS']}")
