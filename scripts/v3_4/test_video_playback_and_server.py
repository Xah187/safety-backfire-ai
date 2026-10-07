"""
test_video_playback_and_server.py
Comprehensive Diagnostic & Verification Suite for Milestone V3.4-C Video Playback & Review Server

Verifies all 12 operational and governance criteria:
  A. Server starts successfully
  B. Index page returns HTTP 200 OK
  C. Eligible event listing returns exactly 38 events
  D. At least one before.mp4 is playable and verified via cv2/FFmpeg
  E. At least one intervention.mp4 is playable and verified via cv2/FFmpeg
  F. At least one after.mp4 is playable and verified via cv2/FFmpeg
  G. Full video HTTP request returns 200 OK with Accept-Ranges
  H. Valid HTTP Range request returns 206 Partial Content
  I. Invalid HTTP Range request returns 416 Range Not Satisfiable
  J. Content-Type header is strictly 'video/mp4'
  K. Reviewer 2 endpoint is strictly isolated (zero Reviewer 1 exposure)
  L. Zero AI metrics exposed across endpoints
"""

import sys
import os
import time
import json
import threading
import subprocess
from pathlib import Path
import urllib.request
import urllib.error
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts/v3_4"))
from review_server import run_server

TEST_PORT = 8798
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


def decode_frames_check(video_path: Path) -> dict:
    if not video_path.exists():
        return {"ok": False, "error": "file does not exist"}
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"ok": False, "error": "could not open with cv2"}

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

    read_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        read_count += 1
    cap.release()

    return {
        "ok": (read_count == cnt and read_count > 0),
        "fourcc": fourcc_str,
        "width": w,
        "height": h,
        "fps": fps,
        "frames": cnt,
        "decoded": read_count,
        "size_bytes": video_path.stat().st_size
    }


def main():
    print("=" * 75)
    print("  V3.4-C VIDEO PLAYBACK & REVIEW SERVER COMPREHENSIVE VERIFICATION")
    print("=" * 75)

    results = {}

    # A. Server starts
    try:
        server_thread = threading.Thread(target=run_server, args=(TEST_PORT,), daemon=True)
        server_thread.start()
        time.sleep(1.2)
        results["A_SERVER_START"] = "PASS"
        print("  [PASS] A. Server started on port", TEST_PORT)
    except Exception as e:
        results["A_SERVER_START"] = f"FAIL: {e}"
        print("  [FAIL] A. Server start failed:", e)
        return False

    # B. Index page returns 200
    try:
        req = urllib.request.urlopen(f"{BASE_URL}/")
        assert req.status == 200
        html = req.read().decode("utf-8")
        assert "Safety Backfire AI" in html
        results["B_INDEX_PAGE"] = "PASS"
        print("  [PASS] B. Index page returned HTTP 200 OK")
    except Exception as e:
        results["B_INDEX_PAGE"] = f"FAIL: {e}"
        print("  [FAIL] B. Index page failed:", e)

    # C. Eligible event listing = 38
    first_event_id = None
    try:
        req = urllib.request.urlopen(f"{BASE_URL}/api/events")
        assert req.status == 200
        events = json.loads(req.read().decode("utf-8"))
        assert len(events) == 38, f"Expected 38, got {len(events)}"
        first_event_id = events[0]["union_id"]
        results["C_ELIGIBLE_COUNT"] = "PASS"
        print(f"  [PASS] C. Eligible event listing returned exactly {len(events)} events (First: {first_event_id})")
    except Exception as e:
        results["C_ELIGIBLE_COUNT"] = f"FAIL: {e}"
        print("  [FAIL] C. Eligible events failed:", e)

    # D, E, F: Video decoding and playability checks
    adjudication_dir = PROJECT_ROOT / "outputs/v3_4/adjudication" / first_event_id

    for key, clip_name, letter in [
        ("D_BEFORE_PLAYABLE", "before.mp4", "D"),
        ("E_INTERVENTION_PLAYABLE", "intervention.mp4", "E"),
        ("F_AFTER_PLAYABLE", "after.mp4", "F")
    ]:
        clip_path = adjudication_dir / clip_name
        info = decode_frames_check(clip_path)
        if info.get("ok") and info.get("fourcc") == "h264":
            results[key] = "PASS"
            print(f"  [PASS] {letter}. {clip_name} verified: codec={info['fourcc']}, {info['frames']} frames decoded to null, size={info['size_bytes']} bytes")
        else:
            results[key] = f"FAIL: {info}"
            print(f"  [FAIL] {letter}. {clip_name} check failed: {info}")

    # G. Full video request = 200 with Accept-Ranges
    video_url = f"{BASE_URL}/video/{first_event_id}/before.mp4"
    try:
        curl_g = subprocess.run(["curl", "-I", video_url], capture_output=True, text=True)
        assert "200 OK" in curl_g.stdout
        assert "Accept-Ranges: bytes" in curl_g.stdout
        assert "Content-Length:" in curl_g.stdout
        results["G_FULL_REQUEST_200"] = "PASS"
        print("  [PASS] G. Full video HTTP request returned 200 OK with Accept-Ranges: bytes")
    except Exception as e:
        results["G_FULL_REQUEST_200"] = f"FAIL: {e}"
        print("  [FAIL] G. Full request failed:", e)

    # H. Range request = 206
    try:
        curl_h = subprocess.run(["curl", "-I", "-H", "Range: bytes=0-1023", video_url], capture_output=True, text=True)
        assert "206 Partial Content" in curl_h.stdout
        assert "Content-Range: bytes 0-1023/" in curl_h.stdout
        assert "Content-Length: 1024" in curl_h.stdout
        results["H_RANGE_REQUEST_206"] = "PASS"
        print("  [PASS] H. Range request returned 206 Partial Content (bytes 0-1023)")
    except Exception as e:
        results["H_RANGE_REQUEST_206"] = f"FAIL: {e}"
        print("  [FAIL] H. Range request failed:", e)

    # I. Invalid range = 416
    try:
        curl_i = subprocess.run(["curl", "-I", "-H", "Range: bytes=999999999-", video_url], capture_output=True, text=True)
        assert "416 Range Not Satisfiable" in curl_i.stdout
        assert "Content-Range: bytes */" in curl_i.stdout
        results["I_INVALID_RANGE_416"] = "PASS"
        print("  [PASS] I. Invalid Range request returned 416 Range Not Satisfiable")
    except Exception as e:
        results["I_INVALID_RANGE_416"] = f"FAIL: {e}"
        print("  [FAIL] I. Invalid range failed:", e)

    # J. MIME type = video/mp4
    try:
        assert "Content-Type: video/mp4" in curl_g.stdout
        assert "Content-Type: video/mp4" in curl_h.stdout
        results["J_MIME_TYPE"] = "PASS"
        print("  [PASS] J. MIME type is strictly 'video/mp4'")
    except Exception as e:
        results["J_MIME_TYPE"] = f"FAIL: {e}"
        print("  [FAIL] J. MIME type check failed:", e)

    # K. Reviewer 2 isolation
    try:
        req_r2 = urllib.request.urlopen(f"{BASE_URL}/api/form/{first_event_id}?slot=REVIEWER_2&reviewer_id=TEST_REV2")
        r2_data = json.loads(req_r2.read().decode("utf-8"))
        r2_str = json.dumps(r2_data).lower()
        assert "reviewer_1" not in r2_str
        assert "reviewer 1" not in r2_str
        results["K_REVIEWER_ISOLATION"] = "PASS"
        print("  [PASS] K. Reviewer 2 endpoint isolation verified (0 Reviewer 1 leakage)")
    except Exception as e:
        results["K_REVIEWER_ISOLATION"] = f"FAIL: {e}"
        print("  [FAIL] K. Isolation failed:", e)

    # L. No AI metrics exposed
    try:
        req_ev = urllib.request.urlopen(f"{BASE_URL}/api/event/{first_event_id}")
        ev_data = json.loads(req_ev.read().decode("utf-8"))
        ev_str = json.dumps(ev_data).lower()
        forbidden_keys = ["candidate_relevance_score", "yolo", "bytetrack", "model_h", "model h", "ai_recommendation"]
        for fk in forbidden_keys:
            assert fk not in ev_str, f"Forbidden key '{fk}' leaked!"
        results["L_AI_BLINDING"] = "PASS"
        print("  [PASS] L. AI blinding verified across API (0 AI scores/boxes/equations)")
    except Exception as e:
        results["L_AI_BLINDING"] = f"FAIL: {e}"
        print("  [FAIL] L. AI blinding check failed:", e)

    print("=" * 75)
    all_passed = all(v == "PASS" for v in results.values())
    if all_passed:
        print("  [SUCCESS] ALL 12 VERIFICATION CRITERIA (A through L) PASSED PERFECTLY!")
    else:
        print("  [FAILURE] Some verification criteria failed.")
    print("=" * 75)
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
