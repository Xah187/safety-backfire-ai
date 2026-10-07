#!/usr/bin/env python3
"""
Training Script for Safety Backfire AI V1.0
- Model: yolo26n.pt (transfer learning from base)
- Device: Apple Silicon MPS
- Target: forklift (0) and person (1)
- Dataset: CCTV Domain-Adapted Dataset V1.0 
  Includes original CCTV hard negatives + positives, PLUS the newly extracted
  critical frames (150-250) with motion-tracked person bounding boxes.
- Augmentations: Heavy CCTV augmentations to make the model robust to 
  top-down partial occlusion and rotation.
"""
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DATA_YAML = ROOT / 'data/dataset_v10/data.yaml'

def main():
    print("=== Starting Safety Backfire AI V1.0 Training ===")
    print(f"Dataset config: {DATA_YAML}")
    
    # Load base YOLO model
    # We use YOLOv8n to stay consistent with V0.7, but you could also use 
    # the best.pt from V0.7 if you wanted to fine-tune it further.
    # To demonstrate a clean baseline improvement from the augmentations and
    # the new dataset, we'll train from the base yolo26n (or yolov8n).
    model = YOLO("../yolo26n.pt") 
    
    # Train with Heavy CCTV Augmentations
    results = model.train(
        data=str(DATA_YAML),
        epochs=8,
        imgsz=960,
        device='mps',
        batch=8,
        workers=2,
        patience=15,
        cos_lr=True,
        # -- Heavy CCTV Augmentations --
        degrees=15.0,        # rotation to simulate different camera angles
        perspective=0.001,   # simulate top-down lens distortion
        mosaic=1.0,          # force model to learn partial objects
        mixup=0.2,           # improve robustness against background blending
        project=str(ROOT / 'runs'),
        name='forklift_person_yolov10_v10',
        exist_ok=True,
        verbose=True
    )
    
    best_weights = ROOT / 'runs/forklift_person_yolov10_v10/weights/best.pt'
    print(f"\nTraining completed! Best weights saved at: {best_weights}")

if __name__ == '__main__':
    main()
