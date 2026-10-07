from pathlib import Path
from ultralytics import YOLO
R=Path(__file__).resolve().parent; video=R/'test.mp4'; model=YOLO(str(R/'runs/forklift_person_yolo26n_v01/weights/best.pt'))
model.predict(source=str(video),imgsz=960,conf=0.35,device='mps',classes=[0,1],save=True,project=str(R/'runs'),name='video_test_v01',exist_ok=True)
print(R/'runs/video_test_v01')
