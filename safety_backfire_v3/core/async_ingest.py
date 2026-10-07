"""
V3.0 Core — Asynchronous Frame Ingest, Contract & Freshness Engine

Implements:
1. Frame Contract with microsecond timestamp provenance.
2. Bounded Queue with real-time backpressure monitoring.
3. Freshness Policy: drops stale frames to prevent cumulative lag in live safety analysis.
"""
import time
import threading
import queue
from typing import Optional, Tuple, Dict, Any
import numpy as np
import cv2

class FramePacket:
    """
    Contract representing an immutable ingested video frame with strict timing provenance.
    """
    def __init__(
        self,
        frame_id: int,
        image: Optional[np.ndarray] = None,
        source_timestamp: float = 0.0,
        capture_timestamp: Optional[float] = None,
        frame: Optional[np.ndarray] = None,
        arrival_timestamp: Optional[float] = None
    ):
        self.frame_id = frame_id
        self.image = image if image is not None else frame
        self.source_timestamp = source_timestamp # Video PTS (e.g. frame_idx / FPS)
        self.capture_timestamp = capture_timestamp if capture_timestamp is not None else time.time() # Wall-clock capture time
        self.arrival_timestamp = arrival_timestamp if arrival_timestamp is not None else time.time()
        self.processing_timestamp: Optional[float] = None
        self.completion_timestamp: Optional[float] = None
        self.drop_reason: Optional[str] = None

    def mark_processing_start(self):
        self.processing_timestamp = time.time()

    def mark_completion(self):
        self.completion_timestamp = time.time()

    def age_ms(self, current_time: Optional[float] = None) -> float:
        now = current_time or time.time()
        return round((now - self.capture_timestamp) * 1000.0, 2)

    def queue_age_ms(self, current_time: Optional[float] = None) -> float:
        now = current_time or time.time()
        return round((now - self.arrival_timestamp) * 1000.0, 2)

    def processing_latency_ms(self) -> Optional[float]:
        if self.processing_timestamp is None or self.completion_timestamp is None:
            return None
        return round((self.completion_timestamp - self.processing_timestamp) * 1000.0, 2)

    def compute_decision_latency_ms(self) -> Optional[float]:
        return self.processing_latency_ms()

    def arrival_to_decision_ms(self) -> Optional[float]:
        if self.completion_timestamp is None:
            return None
        return round((self.completion_timestamp - self.arrival_timestamp) * 1000.0, 2)

    def source_capture_to_decision_ms(self) -> Optional[float]:
        if self.completion_timestamp is None:
            return None
        return round((self.completion_timestamp - self.capture_timestamp) * 1000.0, 2)

    def end_to_end_latency_ms(self) -> Optional[float]:
        return self.source_capture_to_decision_ms()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "source_timestamp": round(self.source_timestamp, 4),
            "capture_timestamp": round(self.capture_timestamp, 4),
            "arrival_timestamp": round(self.arrival_timestamp, 4),
            "processing_timestamp": round(self.processing_timestamp, 4) if self.processing_timestamp else None,
            "completion_timestamp": round(self.completion_timestamp, 4) if self.completion_timestamp else None,
            "source_capture_to_decision_ms": self.source_capture_to_decision_ms(),
            "arrival_to_decision_ms": self.arrival_to_decision_ms(),
            "compute_decision_latency_ms": self.compute_decision_latency_ms(),
            "age_ms": self.age_ms(),
            "processing_latency_ms": self.processing_latency_ms(),
            "end_to_end_latency_ms": self.end_to_end_latency_ms()
        }


class FreshnessPolicy:
    """
    Decides whether a frame is fresh enough to enter safety-critical evaluation.
    In live safety, fresh frames are prioritized over historical completeness.
    """
    def __init__(self, max_allowed_age_ms: float = 150.0, max_age_ms: Optional[float] = None):
        self.max_allowed_age_ms = max_age_ms if max_age_ms is not None else max_allowed_age_ms

    def evaluate(self, packet: FramePacket, current_time: Optional[float] = None) -> Tuple[str, str]:
        age = packet.age_ms(current_time)
        if age > self.max_allowed_age_ms:
            return "DROP", f"Frame age ({age:.1f}ms) exceeds freshness limit ({self.max_allowed_age_ms:.1f}ms)"
        return "PROCESS", "Fresh observation"


class BoundedFrameQueue:
    """
    Thread-safe bounded queue with active backpressure management.
    Prevents unbounded memory growth when ingestion rate > processing rate.
    """
    def __init__(self, max_size: int = 5, freshness_policy: Optional[FreshnessPolicy] = None, max_age_ms: Optional[float] = None):
        self.max_size = max_size
        if freshness_policy:
            self.policy = freshness_policy
        elif max_age_ms is not None:
            self.policy = FreshnessPolicy(max_allowed_age_ms=max_age_ms)
        else:
            self.policy = FreshnessPolicy()
        self._queue = queue.Queue(maxsize=max_size)
        self._lock = threading.Lock()
        
        # Telemetry
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.total_dropped_overflow = 0
        self.total_dropped_stale = 0

    def put(self, packet: FramePacket) -> bool:
        """
        Attempts to enqueue a frame. If queue is full or packet is stale, applies backpressure.
        """
        with self._lock:
            # Check freshness first
            decision, reason = self.policy.evaluate(packet)
            if decision == "DROP":
                packet.drop_reason = reason
                self.total_dropped_stale += 1
                return False

            if self._queue.full():
                # Backpressure overflow: discard oldest stale frame to make room for fresh frame
                try:
                    evicted: FramePacket = self._queue.get_nowait()
                    evicted.drop_reason = "Evicted due to queue overflow (Backpressure)"
                    self.total_dropped_overflow += 1
                except queue.Empty:
                    pass

            try:
                self._queue.put_nowait(packet)
                self.total_enqueued += 1
                return True
            except queue.Full:
                self.total_dropped_overflow += 1
                return False

    def get(self, timeout: float = 0.1) -> Optional[FramePacket]:
        """
        Retrieves next frame for processing. Returns None if empty within timeout.
        """
        try:
            packet = self._queue.get(timeout=timeout)
            with self._lock:
                self.total_dequeued += 1
            return packet
        except queue.Empty:
            return None

    def qsize(self) -> int:
        return self._queue.qsize()

    def push(self, packet: FramePacket) -> bool:
        return self.put(packet)

    def pop(self, timeout: float = 0.1) -> Optional[FramePacket]:
        return self.get(timeout=timeout)

    def empty(self) -> bool:
        return self._queue.empty()

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            drop_count = self.total_dropped_overflow + self.total_dropped_stale
            return {
                "queue_size": self._queue.qsize(),
                "queue_max": self.max_size,
                "max_size": self.max_size,
                "drop_count": drop_count,
                "total_enqueued": self.total_enqueued,
                "total_dequeued": self.total_dequeued,
                "total_dropped_overflow": self.total_dropped_overflow,
                "total_dropped_stale": self.total_dropped_stale,
                "drop_rate_pct": round(
                    (drop_count / max(1, self.total_enqueued + self.total_dropped_stale)) * 100.0,
                    2
                )
            }


class AsyncFrameIngest:
    """
    Dedicated worker thread simulating or reading an RTSP stream/video file,
    injecting microsecond timestamps and feeding the bounded queue.
    """
    def __init__(
        self,
        video_source: str,
        frame_queue: BoundedFrameQueue,
        target_fps: float = 25.0,
        simulate_realtime: bool = True
    ):
        self.video_source = str(video_source)
        self.frame_queue = frame_queue
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.simulate_realtime = simulate_realtime
        
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.frames_read = 0

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _worker_loop(self):
        cap = cv2.VideoCapture(self.video_source)
        if not cap.isOpened():
            print(f"ERROR: Cannot open video source {self.video_source}")
            self.running = False
            return

        source_fps = cap.get(cv2.CAP_PROP_FPS) or self.target_fps
        interval = 1.0 / source_fps
        
        start_wall_time = time.time()

        while self.running and cap.isOpened():
            t_loop_start = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            self.frames_read += 1
            src_time = self.frames_read / source_fps
            capture_time = time.time()

            packet = FramePacket(
                frame_id=self.frames_read,
                image=frame,
                source_timestamp=src_time,
                capture_timestamp=capture_time
            )

            self.frame_queue.put(packet)

            if self.simulate_realtime:
                # Regulate ingestion to mirror real-time camera FPS
                elapsed = time.time() - t_loop_start
                sleep_time = interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        cap.release()
        self.running = False
