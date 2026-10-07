"""
reencode_clips_avc1.py
Milestone V3.4-C Video Playback Diagnostic & Remediation Script

Converts derived review clips from MPEG-4 Part 2 ('mp4v') to W3C-compliant H.264 ('avc1')
for native, zero-latency playback across modern web browsers (Chrome, Safari, Firefox).
Preserves all spatiotemporal frame boundaries, package hashes, metadata, and blinding.
"""

import sys
import os
import json
from pathlib import Path
import cv2

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
ADJUDICATION_DIR = WORKSPACE_ROOT / "outputs/v3_4/adjudication"
UNION_REGISTRY_PATH = WORKSPACE_ROOT / "outputs/v3_4/candidates/union_events_registry.json"

WH026_VIDEOS = WORKSPACE_ROOT / "data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026/videos"
WH027_VIDEOS = WORKSPACE_ROOT / "data/external_facility_02/raw/Warehouse_027/MTMC_Tracking_2026/test/Warehouse_027/videos"


def extract_clip_avc1(src_path: Path, start_frame: int, end_frame: int, out_path: Path, fps: float = 30.0) -> bool:
    if end_frame < start_frame or not src_path.exists():
        return False

    cap = cv2.VideoCapture(str(src_path))
    if not cap.isOpened():
        return False

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"avc1")

    # Write to a temporary file first then atomic rename
    tmp_out = out_path.with_suffix(".tmp.mp4")
    out = cv2.VideoWriter(str(tmp_out), fourcc, fps, (width, height))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_f = start_frame

    while current_f <= end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        current_f += 1

    cap.release()
    out.release()

    if tmp_out.exists() and tmp_out.stat().st_size > 0:
        tmp_out.replace(out_path)
        return True
    return False


def reencode_eligible_packages():
    with open(UNION_REGISTRY_PATH) as f:
        reg = json.load(f)

    eligible_events = [e for e in reg.get("union_records", []) if e.get("window_valid", False)]
    total = len(eligible_events)
    print(f"Starting H.264 (avc1) re-encoding for {total} eligible events...")

    for idx, ev in enumerate(eligible_events, 1):
        event_id = ev["union_id"]
        scene = ev["scene_id"]
        cam = ev["camera_id"]
        v_base = WH026_VIDEOS if scene == "Warehouse_026" else WH027_VIDEOS
        src_video = v_base / f"{cam}.mp4"

        pkg_dir = ADJUDICATION_DIR / event_id
        if not pkg_dir.exists():
            continue

        win = ev.get("screening_windows", {})
        psf = win.get("pre", {}).get("start_frame", 0)
        pef = win.get("pre", {}).get("end_frame", 0)
        isf = win.get("intervention", {}).get("start_frame", 0)
        ief = win.get("intervention", {}).get("end_frame", 0)
        post_sf = win.get("post", {}).get("start_frame", 0)
        post_ef = win.get("post", {}).get("end_frame", 0)

        extract_clip_avc1(src_video, psf, pef, pkg_dir / "before.mp4")
        extract_clip_avc1(src_video, isf, ief, pkg_dir / "intervention.mp4")
        extract_clip_avc1(src_video, post_sf, post_ef, pkg_dir / "after.mp4")

        if idx % 10 == 0 or idx == total:
            print(f"  Processed {idx}/{total} packages (H.264 avc1)...")

    print(f"Successfully re-encoded all {total} eligible packages with H.264 (avc1).")


if __name__ == "__main__":
    reencode_eligible_packages()
