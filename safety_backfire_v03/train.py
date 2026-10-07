from pathlib import Path
from ultralytics import YOLO
R=Path(__file__).resolve().parent; data=R/'dataset/yolo/data.yaml'
model=YOLO('yolo26n.pt')
model.train(data=str(data),epochs=50,imgsz=640,device='mps',batch=8,workers=2,patience=15,freeze=10,project=str(R/'runs'),name='forklift_person_yolo26n_v01',exist_ok=True)
print(R/'runs/forklift_person_yolo26n_v01/weights/best.pt')
