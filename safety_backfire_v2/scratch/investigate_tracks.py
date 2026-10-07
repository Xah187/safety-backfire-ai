import sys
import cv2
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from ultralytics import YOLO

def investigate_tracks():
    print("=== Ghost Track Investigation (P89 & P18) ===")
    video_path = str(ROOT.parent.parent / "test2.mp4")
    model_path = str(ROOT.parent.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt")
    
    det_model = YOLO(model_path)
    cap = cv2.VideoCapture(video_path)
    
    frame_idx = 0
    p89_log = []
    p18_log = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        frame_idx += 1
        
        res = det_model.track(frame, imgsz=640, conf=0.15, iou=0.70, classes=[0,1], persist=True, tracker="bytetrack.yaml", verbose=False)[0]
        
        if res.boxes.id is not None:
            for b, cls, trk_id, conf in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy(), res.boxes.id.cpu().numpy(), res.boxes.conf.cpu().numpy()):
                tid = int(trk_id)
                if tid == 89 and (1050 <= frame_idx <= 1160):
                    p89_log.append({"frame": frame_idx, "conf": float(conf), "box": b.tolist(), "cls": int(cls)})
                if tid == 18 and (500 <= frame_idx <= 650):
                    p18_log.append({"frame": frame_idx, "conf": float(conf), "box": b.tolist(), "cls": int(cls)})
                    
    cap.release()
    
    print("\n--- P18 Log ---")
    for log in p18_log:
        print(f"Frame {log['frame']} | Conf {log['conf']:.3f} | Box {log['box']}")
        
    print("\n--- P89 Log ---")
    for log in p89_log:
        print(f"Frame {log['frame']} | Conf {log['conf']:.3f} | Box {log['box']}")

if __name__ == "__main__":
    investigate_tracks()
