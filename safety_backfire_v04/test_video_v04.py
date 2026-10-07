from pathlib import Path
from ultralytics import YOLO
R=Path(__file__).resolve().parent
model=YOLO('runs/forklift_person_yolo26n_v04/weights/best.pt')
model.predict(source=str(R/'test.mp4'), imgsz=960, conf=0.25, iou=0.7, device='mps', classes=[0,1], save=True, project=str(R/'runs'), name='v04_stress_test', exist_ok=True)
print('Stress-test output:',R/'runs/v04_stress_test')
