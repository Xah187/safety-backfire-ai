#!/usr/bin/env python3
"""
Training Script for Safety Backfire AI V0.7
- Model: yolo26n.pt
- Device: Apple Silicon MPS
- Target: forklift (0) and person (1)
- Dataset: CCTV Domain-Adapted Dataset V0.7 (15.3% hard negatives)
"""
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DATA_YAML = ROOT / 'data/dataset_v07/data.yaml'

def main():
    print("=== Starting Safety Backfire AI V0.7 Training ===")
    print(f"Dataset config: {DATA_YAML}")
    
    # Load base YOLO model
    model = YOLO("yolo26n.pt")
    
    # Train
    results = model.train(
        data=str(DATA_YAML),
        epochs=60,
        imgsz=960,
        device='mps',
        batch=8,
        workers=2,
        patience=15,
        cos_lr=True,
        project=str(ROOT / 'runs'),
        name='forklift_person_yolo26n_v07',
        exist_ok=True
    )
    
    best_weights = ROOT / 'runs/forklift_person_yolo26n_v07/weights/best.pt'
    print(f"\nTraining completed! Best weights saved at: {best_weights}")

if __name__ == '__main__':
    main()
