"""
Trajectory module for Safety Backfire AI V0.8.
Maintains footprint history, performs temporal smoothing, and computes
kinematic velocity and heading vectors.
"""
import math
from collections import defaultdict, deque
from typing import Dict, Tuple, List, Optional

class TrajectoryTracker:
    def __init__(self, window_size: int = 5, max_history: int = 60):
        self.window_size = window_size
        self.max_history = max_history
        # track_id -> deque of (frame_idx, time_sec, (foot_x, foot_y))
        self.history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=self.max_history))

    def update(self, track_id: int, frame_idx: int, time_sec: float, footprint: Tuple[float, float]):
        """Records a new footprint location for the track."""
        self.history[track_id].append((frame_idx, time_sec, footprint))

    def get_smoothed_position(self, track_id: int) -> Optional[Tuple[float, float]]:
        """Returns moving-average smoothed ground position over recent window."""
        hist = self.history[track_id]
        if not hist:
            return None
        recent = list(hist)[-self.window_size:]
        avg_x = sum(p[2][0] for p in recent) / len(recent)
        avg_y = sum(p[2][1] for p in recent) / len(recent)
        return (avg_x, avg_y)

    def get_velocity(self, track_id: int) -> Tuple[float, float, float]:
        """
        Computes velocity vector (vx, vy in px/sec) and scalar speed (px/sec).
        Returns: (vx, vy, speed)
        """
        hist = self.history[track_id]
        if len(hist) < 2:
            return (0.0, 0.0, 0.0)
        
        # Use smoothed points across the window for stable velocity
        recent = list(hist)[-min(len(hist), self.window_size):]
        p_first = recent[0]
        p_last = recent[-1]
        
        dt = p_last[1] - p_first[1]
        if dt <= 1e-4:
            return (0.0, 0.0, 0.0)
            
        dx = p_last[2][0] - p_first[2][0]
        dy = p_last[2][1] - p_first[2][1]
        
        vx = dx / dt
        vy = dy / dt
        speed = math.hypot(vx, vy)
        return (vx, vy, speed)

    def get_heading(self, track_id: int) -> Optional[float]:
        """Returns heading angle in radians (0 = right, pi/2 = down), or None if static."""
        vx, vy, speed = self.get_velocity(track_id)
        if speed < 5.0: # Filter out jitter noise when stationary
            return None
        return math.atan2(vy, vx)

    def get_recent_path(self, track_id: int, num_points: int = 15) -> List[Tuple[float, float]]:
        """Returns recent ground points for drawing trail paths."""
        hist = self.history[track_id]
        return [p[2] for p in list(hist)[-num_points:]]

    def get_last_seen_frame(self, track_id: int) -> int:
        """Returns the frame index when this track was last observed."""
        hist = self.history[track_id]
        return hist[-1][0] if hist else 0

    def is_active(self, track_id: int, current_frame: int, max_age: int = 25) -> bool:
        """Returns True if the track was observed within the last max_age frames."""
        hist = self.history[track_id]
        if not hist:
            return False
        return (current_frame - hist[-1][0]) <= max_age

