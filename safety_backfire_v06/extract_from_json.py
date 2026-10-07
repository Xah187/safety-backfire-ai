import cv2
import json
import os
import pandas as pd

output_dir = "failure_gallery"
forklift_dir = os.path.join(output_dir, "forklift_ranked")
person_dir = os.path.join(output_dir, "person_tracks")
os.makedirs(forklift_dir, exist_ok=True)
os.makedirs(person_dir, exist_ok=True)

with open('track_stats.json', 'r') as f:
    stats = json.load(f)

cap = cv2.VideoCapture('test.mp4')
annotations = []

for track in stats:
    t_id = track['track_id']
    cls = track['class']
    first = track['first_frame']
    last = track['last_frame']
    
    # تحديد الأخطاء بناءً على نسبة الحركة القليلة (كما رأينا في المسار 2 و 20)
    if cls == 'forklift' and track['frames'] > 20 and track['displacement_px'] < 10:
        out_dir = forklift_dir
    elif cls == 'person':
        out_dir = person_dir
    else:
        continue
        
    frames_to_extract = [first, first + (last - first) // 2, last]
    cx, cy = int(track['start_center'][0]), int(track['start_center'][1])
    
    for fnum in frames_to_extract:
        cap.set(cv2.CAP_PROP_POS_FRAMES, fnum)
        ret, frame = cap.read()
        if ret:
            # رسم دائرة حمراء حول الخطأ
            cv2.circle(frame, (cx, cy), 50, (0, 0, 255), 3)
            cv2.putText(frame, f"Track {t_id}", (cx-50, cy-60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            filename = f"{cls}_track_{t_id}_frame_{fnum}.jpg"
            filepath = os.path.join(out_dir, filename)
            cv2.imwrite(filepath, frame)
            annotations.append({"filename": filename, "track_id": t_id, "class": cls, "human_label": ""})
            print(f"Saved: {filepath}")

cap.release()
if annotations:
    pd.DataFrame(annotations).to_csv(os.path.join(output_dir, "annotation_review.csv"), index=False)
    print("تم إنشاء الصور بنجاح!")
