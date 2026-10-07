"""
V2.6.1 — Micro Ground Truth Generator

Generates a tiny semantic GT for a small subset of frames.
Strictly adheres to the rule: "Do not use YOLO -> GT -> visual verification".
Since human bounding-box annotation is unavailable, detection bounding boxes 
are left out or approximated, making Detection Metrics NOT COMPUTABLE.
Focuses strictly on semantic Operator/Pedestrian labels.
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))


def generate_micro_gt():
    # 50 frames with known EPJ operator (Green pallet jack)
    epj_frames = list(range(800, 850)) # 50 consecutive frames for tracking
    
    # 10 frames with parked forklift on the left
    parked_frames = list(range(100, 110))
    
    all_frames = sorted(set(epj_frames + parked_frames))
    
    annotations = []
    
    for f_idx in all_frames:
        objects = []
        
        # We know there is an EPJ operator in 800-850
        if f_idx in epj_frames:
            objects.append({
                "class": "forklift",
                "semantic_id": "green_epj",
                "annotation_type": "SEMANTIC_ONLY" 
                # NO BBOX - Prevents cheating with YOLO
            })
            objects.append({
                "class": "person",
                "semantic_id": "epj_operator",
                "person_relation": "OPERATOR_ON_VEHICLE",
                "annotation_type": "SEMANTIC_ONLY"
            })
            
        # We know there is a parked forklift in 100-110
        if f_idx in parked_frames:
            objects.append({
                "class": "forklift",
                "semantic_id": "parked_left",
                "annotation_type": "SEMANTIC_ONLY"
            })
            
        annotations.append({
            "frame": f_idx,
            "objects": objects
        })
        
    gt_data = {
        "version": "V2.6.1",
        "description": "Micro GT - Semantic Only. No bounding boxes provided to enforce NOT COMPUTABLE on detection metrics.",
        "frames": annotations
    }
    
    out_dir = ROOT / "validation/real_world/annotations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "micro_gt_v2_6_1.json"
    
    with open(out_path, "w") as f:
        json.dump(gt_data, f, indent=2)
        
    print(f"=== V2.6.1 Micro GT Generator ===")
    print(f"Generated Semantic GT for {len(all_frames)} frames.")
    print("Detection Bounding Boxes omitted (Rule: No YOLO bootstrapping).")
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    generate_micro_gt()
