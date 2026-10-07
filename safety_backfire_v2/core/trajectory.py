"""
Phase 5 — Trajectory Reconstruction

Maintains historical trajectories for all tracked entities (Persons/Forklifts) in WORLD coordinates.
Performs spatial smoothing and extracts trajectory-level semantics (displacement, peak velocity, etc.).
"""
import math
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

class TrajectoryPoint:
    def __init__(self, timestamp: float, x_world: float, y_world: float, zone: str = "SAFE"):
        self.timestamp = timestamp
        self.x_world = x_world
        self.y_world = y_world
        self.zone = zone
        self.velocity_m_s: Optional[float] = None
        self.direction_deg: Optional[float] = None

class WorldTrajectory:
    def __init__(self, track_id: int, entity_type: str, smoothing_window: int = 5):
        self.track_id = track_id
        self.entity_type = entity_type
        self.smoothing_window = smoothing_window
        self.points: List[TrajectoryPoint] = []
        
        # Aggregated Metrics
        self.trajectory_length: float = 0.0
        self.displacement: float = 0.0
        self.average_velocity: float = 0.0
        self.peak_velocity: float = 0.0
        self.zone_transitions: int = 0
        
    def add_point(self, timestamp: float, x: float, y: float, zone: str = "SAFE"):
        new_pt = TrajectoryPoint(timestamp, x, y, zone)
        
        if len(self.points) > 0:
            prev_pt = self.points[-1]
            if zone != prev_pt.zone:
                self.zone_transitions += 1
                
            dt = timestamp - prev_pt.timestamp
            if dt > 0:
                dx = x - prev_pt.x_world
                dy = y - prev_pt.y_world
                
                # Apply simple smoothing for velocity by looking back at recent window
                # To prevent tracking jitter from causing massive velocity spikes
                if len(self.points) >= self.smoothing_window:
                    old_pt = self.points[-self.smoothing_window]
                    dt_smooth = timestamp - old_pt.timestamp
                    if dt_smooth > 0:
                        dx_smooth = x - old_pt.x_world
                        dy_smooth = y - old_pt.y_world
                        vx = dx_smooth / dt_smooth
                        vy = dy_smooth / dt_smooth
                    else:
                        vx, vy = dx / dt, dy / dt
                else:
                    vx, vy = dx / dt, dy / dt
                    
                speed = math.hypot(vx, vy)
                direction = math.degrees(math.atan2(vy, vx)) % 360
                
                new_pt.velocity_m_s = round(speed, 2)
                new_pt.direction_deg = round(direction, 1)
                
                self.trajectory_length += math.hypot(dx, dy)
                if speed > self.peak_velocity:
                    self.peak_velocity = speed
                    
        self.points.append(new_pt)
        
        # Update displacement (distance from first to last point)
        if len(self.points) > 1:
            first = self.points[0]
            self.displacement = math.hypot(x - first.x_world, y - first.y_world)
            
    def get_metrics(self) -> Dict[str, Any]:
        valid_vels = [p.velocity_m_s for p in self.points if p.velocity_m_s is not None]
        avg_v = sum(valid_vels) / len(valid_vels) if valid_vels else 0.0
        
        return {
            "track_id": self.track_id,
            "entity_type": self.entity_type,
            "points_count": len(self.points),
            "trajectory_length_m": round(self.trajectory_length, 2),
            "displacement_m": round(self.displacement, 2),
            "average_velocity_m_s": round(avg_v, 2),
            "peak_velocity_m_s": round(self.peak_velocity, 2),
            "zone_transitions": self.zone_transitions
        }

class TrajectoryEngine:
    def __init__(self):
        self.active_trajectories: Dict[int, WorldTrajectory] = {}
        
    def update(self, track_id: int, entity_type: str, timestamp: float, x: float, y: float, zone: str = "SAFE"):
        if track_id not in self.active_trajectories:
            self.active_trajectories[track_id] = WorldTrajectory(track_id, entity_type)
        self.active_trajectories[track_id].add_point(timestamp, x, y, zone)
        
    def get_trajectory(self, track_id: int) -> Optional[WorldTrajectory]:
        return self.active_trajectories.get(track_id)
