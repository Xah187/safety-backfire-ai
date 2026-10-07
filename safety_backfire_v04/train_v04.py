from pathlib import Path
from ultralytics import YOLO
R=Path(__file__).resolve().parent; data=R/'data/v04/data.yaml'
model=YOLO('yolo26n.pt')
model.train(data=str(data), epochs=70, imgsz=960, device='mps', batch=8, workers=2, patience=20, freeze=8, cos_lr=True, project=str(R/'runs'), name='forklift_person_yolo26n_v04', exist_ok=True)
print(R/'runs/forklift_person_yolo26n_v04/weights/best.pt')
