import sys
from pathlib import Path
import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from core.geometry import GroundPlaneCalibrator, compute_metric_distance

def debug_tracking():
    model_path = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
    video_path = ROOT.parent / "safety_backfire_v08/test.mp4"
    
    model = YOLO(str(model_path))
    calibrator = GroundPlaneCalibrator()
    
    frame_idx = 0
    for result in model.track(
        source=str(video_path),
        stream=True, persist=True, tracker="bytetrack.yaml",
        imgsz=960, conf=0.08, iou=0.70, device="cpu", classes=[0, 1], verbose=False
    ):
        frame_idx += 1
        if frame_idx < 180 or frame_idx > 230:
            continue
            
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            continue
            
        ids = boxes.id
        xyxy = boxes.xyxy.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)
        
        persons = []
        forklifts = []
        
        for i, cls_id in enumerate(clss):
            tid = int(ids[i].item()) if ids is not None and ids[i] is not None else None
            box = [int(v) for v in xyxy[i]]
            cx = (box[0] + box[2]) / 2.0
            foot_y = box[3]
            c_name = model.names[int(cls_id)]
            
            world_pt = calibrator.pixel_to_world((cx, foot_y))
            valid = calibrator.is_in_calibrated_region((cx, foot_y))
            
            if c_name == "person":
                persons.append((tid, cx, foot_y, valid))
            else:
                forklifts.append((tid, cx, foot_y, valid))
                
        print(f"Frame {frame_idx}:")
        print(f"  Persons: {persons}")
        print(f"  Forklifts: {forklifts}")
        for p in persons:
            for f in forklifts:
                geo_res = compute_metric_distance((p[1], p[2]), (f[1], f[2]), calibrator)
                print(f"  Pair (P{p[0]}, F{f[0]}): Status: {geo_res['calibration_status']}, Dist px: {geo_res['distance_px']}, Dist m: {geo_res['distance_m']}")

if __name__ == "__main__":
    debug_tracking()
