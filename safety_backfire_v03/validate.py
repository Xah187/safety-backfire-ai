from pathlib import Path
from ultralytics import YOLO
R=Path(__file__).resolve().parent; model=YOLO(str(R/'runs/forklift_person_yolo26n_v01/weights/best.pt')); model.val(data=str(R/'dataset/yolo/data.yaml'),imgsz=640,device='mps',split='test')
