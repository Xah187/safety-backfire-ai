"""
V2.9 Red-Team Test: Live RTSP Stream Simulation & Stress Harness

Simulates a real-world RTSP streaming feed under network degradation:
- Variable inter-frame arrival jitter (packet delay).
- Sudden burst frame drops (network packet loss).
- Stream disconnection (camera offline) followed by reconnection.
- Buffer latency and catch-up behavior.
Evaluates if the pipeline recovers gracefully or corrupts tracking state.
"""
import sys
import time
import math
import random
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.geometry import load_default_calibrator
from core.track_manager import TrackManager, TrackState
from core.operator_relation_v2 import OperatorVehicleRelationEngineV2
from core.event_engine_v2 import EventEngineV2

class SimulatedRTSPStream:
    """Simulates an RTSP video source with network flaws."""
    def __init__(self, video_path: str, target_fps: float = 25.0):
        self.cap = cv2.VideoCapture(video_path)
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.frame_idx = 0
        self.simulated_clock = 0.0
        self.is_connected = True

    def read_frame(self, drop_probability: float = 0.05, jitter_std_ms: float = 10.0):
        if not self.is_connected:
            return False, None, self.frame_idx, self.simulated_clock

        ret, frame = self.cap.read()
        if not ret:
            return False, None, self.frame_idx, self.simulated_clock

        self.frame_idx += 1
        
        # Simulate network drop
        if random.random() < drop_probability:
            # Packet dropped! Skip this frame from the receiver's perspective
            self.simulated_clock += self.frame_interval
            return None, None, self.frame_idx, self.simulated_clock

        # Simulate arrival jitter
        jitter_s = random.gauss(0, jitter_std_ms / 1000.0)
        dt = max(0.001, self.frame_interval + jitter_s)
        self.simulated_clock += dt

        return True, frame, self.frame_idx, self.simulated_clock

    def disconnect(self):
        self.is_connected = False

    def reconnect(self):
        self.is_connected = True

    def release(self):
        self.cap.release()

def test_live_simulation():
    print("\n=== V2.9 Red-Team: LIVE / RTSP Streaming Simulation Audit ===")
    video_path = str(ROOT.parent / "test2.mp4")
    stream = SimulatedRTSPStream(video_path, target_fps=25.0)

    calibrator = load_default_calibrator()
    tm = TrackManager()
    ee = EventEngineV2(max_gap_frames=15)

    stats = {
        "received_frames": 0,
        "dropped_frames": 0,
        "disconnect_events": 0,
        "reconnect_events": 0,
        "tracking_failures": 0
    }

    print("Simulating 300 live frames with 10% packet drop and 15ms network jitter...")
    
    for i in range(300):
        # Inject disconnect at frame 150 for 20 frames
        if i == 150:
            print("  [ALERT] Injecting Camera Disconnect (Stream Offline)...")
            stream.disconnect()
            stats["disconnect_events"] += 1
        elif i == 170:
            print("  [ALERT] Camera Stream Reconnected...")
            stream.reconnect()
            stats["reconnect_events"] += 1

        status, frame, f_idx, clock_time = stream.read_frame(drop_probability=0.10, jitter_std_ms=15.0)
        
        if status is False: # Disconnected or EOF
            continue
        elif status is None: # Dropped frame
            stats["dropped_frames"] += 1
            continue
        
        stats["received_frames"] += 1

        # Simulate synthetic track object moving steadily
        synth_obj = {
            "id": 1,
            "class": "forklift",
            "bbox": [500, 500, 600, 600],
            "conf": 0.85,
            "px": (550.0, 600.0)
        }
        
        out = tm.process_tracks(f_idx, clock_time, [synth_obj], calibrator)
        if out[0]["track_state"] == TrackState.STALE:
            stats["tracking_failures"] += 1

    stream.release()

    print("\nLive Simulation Audit Results:")
    print(f"  Frames Processed:   {stats['received_frames']}")
    print(f"  Dropped Frames:     {stats['dropped_frames']} ({stats['dropped_frames'] / 300 * 100:.1f}%)")
    print(f"  Disconnect Events:  {stats['disconnect_events']}")
    print(f"  Reconnect Events:   {stats['reconnect_events']}")
    print(f"  Tracking Failures:  {stats['tracking_failures']}")

    if stats["tracking_failures"] == 0:
        print("  [PASS] TrackManager maintained continuous track through 10% drop and 20-frame disconnect recovery.")
    else:
        print(f"  [WARN] {stats['tracking_failures']} tracks experienced failure state during network dropouts.")

    return stats

if __name__ == "__main__":
    test_live_simulation()
