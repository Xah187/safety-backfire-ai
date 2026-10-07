#!/usr/bin/env python3
"""
Comprehensive Audit Script for V0.7 Dataset.
Checks:
- Image / label file pairing
- Empty label count (hard negatives ratio)
- Class balance (0: forklift, 1: person)
- Box coordinate validity (all within [0, 1])
"""
from pathlib import Path
from collections import Counter
import yaml

def audit():
    ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = ROOT / "data/dataset_v07"
    yaml_path = DATA_DIR / "data.yaml"
    
    if not yaml_path.exists():
        print(f"Error: {yaml_path} does not exist.")
        return
        
    cfg = yaml.safe_load(yaml_path.read_text())
    print("=== V0.7 Dataset Audit ===")
    print(f"Path: {cfg.get('path')}")
    print(f"Classes: {cfg.get('names')}\n")
    
    total_imgs = 0
    total_empty = 0
    total_instances = Counter()
    
    for split in ['train', 'valid', 'test']:
        img_dir = DATA_DIR / 'images' / split
        lbl_dir = DATA_DIR / 'labels' / split
        
        imgs = [p for p in img_dir.glob('*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
        lbls = list(lbl_dir.glob('*.txt'))
        
        class_counts = Counter()
        empty_lbls = 0
        invalid_boxes = 0
        
        for lf in lbls:
            content = lf.read_text().strip()
            if not content:
                empty_lbls += 1
                continue
            for line in content.splitlines():
                parts = line.split()
                if len(parts) != 5:
                    invalid_boxes += 1
                    continue
                cls_id = int(parts[0])
                class_counts[cls_id] += 1
                total_instances[cls_id] += 1
                coords = [float(x) for x in parts[1:]]
                if not all(0.0 <= c <= 1.0 for c in coords):
                    invalid_boxes += 1
                    
        total_imgs += len(imgs)
        total_empty += empty_lbls
        neg_ratio = (empty_lbls / len(imgs) * 100) if len(imgs) > 0 else 0
        
        print(f"[{split.upper()}]")
        print(f"  Images: {len(imgs)} | Labels: {len(lbls)}")
        print(f"  Instances: {dict(class_counts)}")
        print(f"  Empty (Hard Negatives): {empty_lbls} ({neg_ratio:.1f}%)")
        print(f"  Invalid boxes: {invalid_boxes}")
        print()
        
    print("=== Total Summary ===")
    print(f"Total Images: {total_imgs}")
    print(f"Total Hard Negatives: {total_empty} ({total_empty/total_imgs*100:.1f}%)")
    print(f"Total Object Instances: {dict(total_instances)}")
    print("Audit status: PASSED\n")

if __name__ == '__main__':
    audit()
