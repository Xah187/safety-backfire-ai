#!/usr/bin/env python3
"""
Builds the unified V0.7 dataset by merging:
1. Clean base YOLO dataset (V0.3 base)
2. CCTV-specific positive instances (workers and forklifts in surveillance view)
3. CCTV-specific hard negatives (pure background images with empty .txt)
"""
from pathlib import Path
import shutil, random, yaml

def copy_split(src_img, src_lbl, dst_img, dst_lbl, prefix):
    n = 0
    for ip in sorted(Path(src_img).glob('*')):
        if ip.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
            continue
        lp = Path(src_lbl) / (ip.stem + '.txt')
        if not lp.exists():
            continue
        name = f"{prefix}_{ip.name}"
        shutil.copy2(ip, Path(dst_img) / name)
        shutil.copy2(lp, Path(dst_lbl) / (Path(name).stem + '.txt'))
        n += 1
    return n

def main():
    ROOT = Path(__file__).resolve().parent.parent
    BASE = ROOT / "data/base_yolo"
    POS = ROOT / "data/cctv_positives"
    NEG = ROOT / "data/cctv_hard_negatives"
    OUT = ROOT / "data/dataset_v07"
    
    random.seed(42)
    
    # 1. Clean output directory
    if OUT.exists():
        shutil.rmtree(OUT)
        
    for split in ['train', 'valid', 'test']:
        (OUT / 'images' / split).mkdir(parents=True, exist_ok=True)
        (OUT / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
    # 2. Copy base dataset
    for split in ['train', 'valid', 'test']:
        n = copy_split(BASE / 'images' / split, BASE / 'labels' / split,
                       OUT / 'images' / split, OUT / 'labels' / split, 'base')
        print(f"Base {split}: copied {n} images")
        
    # 3. Add CCTV positives (85% train, 15% valid)
    pos_files = [p for p in (POS / 'images').glob('*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
    random.shuffle(pos_files)
    n_pos_val = max(1, round(len(pos_files) * 0.15))
    val_pos_set = set(pos_files[:n_pos_val])
    
    for ip in pos_files:
        lp = POS / 'labels' / (ip.stem + '.txt')
        if not lp.exists():
            continue
        split = 'valid' if ip in val_pos_set else 'train'
        name = f"cctv_pos_{ip.name}"
        shutil.copy2(ip, OUT / 'images' / split / name)
        shutil.copy2(lp, OUT / 'labels' / split / (Path(name).stem + '.txt'))
    print(f"CCTV Positives: {len(pos_files) - n_pos_val} to train, {n_pos_val} to valid")
    
    # 4. Add CCTV hard negatives (85% train, 15% valid)
    neg_files = [p for p in (NEG / 'images').glob('*') if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
    random.shuffle(neg_files)
    n_neg_val = max(1, round(len(neg_files) * 0.15))
    val_neg_set = set(neg_files[:n_neg_val])
    
    for ip in neg_files:
        lp = NEG / 'labels' / (ip.stem + '.txt')
        if not lp.exists():
            continue
        split = 'valid' if ip in val_neg_set else 'train'
        name = f"cctv_neg_{ip.name}"
        shutil.copy2(ip, OUT / 'images' / split / name)
        shutil.copy2(lp, OUT / 'labels' / split / (Path(name).stem + '.txt'))
    print(f"CCTV Hard Negatives: {len(neg_files) - n_neg_val} to train, {n_neg_val} to valid")
    
    # 5. Create data.yaml
    data_yaml = {
        'path': str(OUT.resolve()),
        'train': 'images/train',
        'val': 'images/valid',
        'test': 'images/test',
        'names': {
            0: 'forklift',
            1: 'person'
        }
    }
    (OUT / 'data.yaml').write_text(yaml.safe_dump(data_yaml, sort_keys=False))
    print(f"Dataset V0.7 built successfully at: {OUT / 'data.yaml'}")

if __name__ == '__main__':
    main()
