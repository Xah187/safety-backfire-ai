#!/usr/bin/env python3
import pandas as pd
import cv2
import os
import numpy as np

# إعداد المجلدات
output_dir = "failure_gallery"
forklift_dir = os.path.join(output_dir, "forklift_ranked")
person_dir = os.path.join(output_dir, "person_tracks")
os.makedirs(forklift_dir, exist_ok=True)
os.makedirs(person_dir, exist_ok=True)

try:
    # قراءة البيانات
    df = pd.read_csv('tracking_events.csv')
    video_path = 'test.mp4'

    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        exit()

    # تحليل مسارات الرافعات الشوكية (البحث عن الإيجابيات الخاطئة)
    forklift_tracks = df[df['class'] == 'forklift'].groupby('track_id').agg(
        num_frames=('frame', 'count'),
        start_frame=('frame', 'min'),
        end_frame=('frame', 'max'),
        avg_conf=('confidence', 'mean'),
        x1_std=('x1', 'std'),
        y1_std=('y1', 'std')
    ).reset_index()

    # تصفية المسارات المشبوهة (أكثر من 20 إطار وحركة قليلة)
    # ملاحظة: تم تعديل معيار الحركة لتضمين المسارات التي تم تحديدها سابقًا مثل ID 2 و 20
    suspicious_forklifts = forklift_tracks[
        (forklift_tracks['num_frames'] > 20) &
        (forklift_tracks['x1_std'].fillna(0) < 10) & 
        (forklift_tracks['y1_std'].fillna(0) < 10)
    ].sort_values('num_frames', ascending=False)
    
    # تحليل مسارات الأشخاص
    person_tracks = df[df['class'] == 'person'].groupby('track_id').agg(
        num_frames=('frame', 'count'),
        start_frame=('frame', 'min'),
        end_frame=('frame', 'max')
    ).reset_index()

    cap = cv2.VideoCapture(video_path)
    annotations = []

    def extract_frames(track_id, start, end, obj_class, out_dir):
        # استخراج 3 إطارات (بداية، منتصف، نهاية)
        frames_to_extract = [start, start + (end - start) // 2, end]
        for frame_num in frames_to_extract:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if ret:
                # رسم مربع الإحاطة إذا كان متاحًا
                track_data = df[(df['track_id'] == track_id) & (df['frame'] == frame_num)]
                if not track_data.empty:
                    row = track_data.iloc[0]
                    x1, y1, x2, y2 = int(row['x1']), int(row['y1']), int(row['x2']), int(row['y2'])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                filename = f"{obj_class}_track_{int(track_id)}_frame_{int(frame_num)}.jpg"
                filepath = os.path.join(out_dir, filename)
                cv2.imwrite(filepath, frame)
                annotations.append({"filename": filename, "track_id": track_id, "class": obj_class, "human_label": ""})
                print(f"Saved: {filepath}")

    print("Extracting Suspicious Forklift Frames...")
    for index, row in suspicious_forklifts.iterrows():
        extract_frames(row['track_id'], row['start_frame'], row['end_frame'], 'forklift', forklift_dir)

    print("\nExtracting Person Track Frames...")
    for index, row in person_tracks.iterrows():
        extract_frames(row['track_id'], row['start_frame'], row['end_frame'], 'person', person_dir)

    cap.release()

    # حفظ ملف المراجعة
    if annotations:
        anno_df = pd.DataFrame(annotations)
        anno_csv_path = os.path.join(output_dir, "annotation_review.csv")
        anno_df.to_csv(anno_csv_path, index=False)
        print(f"\n✅ Created annotation file: {anno_csv_path}")
    else:
        print("\nNo frames were extracted.")

except Exception as e:
    print(f"An error occurred: {e}")
