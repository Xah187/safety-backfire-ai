"""
Safety Zones module for Safety Backfire AI V0.8.
Defines dynamic safety halos around forklifts and pedestrian safety envelopes.
"""
import math
from typing import Tuple, List, Dict

class SafetyZoneManager:
    def __init__(
        self,
        base_caution_radius: float = 75.0,  # ~2.5 - 3.0 meters
        base_danger_radius: float = 42.0,   # ~1.2 - 1.5 meters
        velocity_extension_factor: float = 0.35, # Seconds of forward projection
    ):
        self.base_caution_radius = base_caution_radius
        self.base_danger_radius = base_danger_radius
        self.velocity_extension_factor = velocity_extension_factor

    def compute_forklift_halos(
        self,
        footprint: Tuple[float, float],
        velocity: Tuple[float, float, float]
    ) -> Dict[str, Tuple[Tuple[int, int], Tuple[int, int], float]]:
        """
        Computes the dynamic caution and danger zone parameters (center, axes, angle).
        Returns:
            {
                'danger': ((center_x, center_y), (axis_x, axis_y), angle_deg),
                'caution': ((center_x, center_y), (axis_x, axis_y), angle_deg)
            }
        """
        fx, fy = footprint
        vx, vy, speed = velocity

        # Project zone forward along movement direction
        forward_shift = min(speed * self.velocity_extension_factor, 45.0)
        heading = math.atan2(vy, vx) if speed > 5.0 else 0.0
        angle_deg = math.degrees(heading)

        # Center shifted forward
        center_x = int(fx + forward_shift * 0.5 * math.cos(heading))
        center_y = int(fy + forward_shift * 0.5 * math.sin(heading))

        # Elongate along direction of motion
        danger_major = int(self.base_danger_radius + forward_shift * 0.5)
        danger_minor = int(self.base_danger_radius * 0.85)

        caution_major = int(self.base_caution_radius + forward_shift * 0.75)
        caution_minor = int(self.base_caution_radius * 0.85)

        return {
            "danger": ((center_x, center_y), (danger_major, danger_minor), angle_deg),
            "caution": ((center_x, center_y), (caution_major, caution_minor), angle_deg),
        }

    def evaluate_point_in_zone(
        self,
        point: Tuple[float, float],
        footprint: Tuple[float, float],
        velocity: Tuple[float, float, float]
    ) -> str:
        """
        Evaluates whether a point (pedestrian footprint) is in 'DANGER', 'CAUTION', or 'SAFE'.
        """
        halos = self.compute_forklift_halos(footprint, velocity)
        px, py = point

        # Check Danger Ellipse
        for zone_name in ["danger", "caution"]:
            (cx, cy), (rx, ry), angle_deg = halos[zone_name]
            rad = math.radians(-angle_deg)
            # Rotate point relative to ellipse center
            dx = px - cx
            dy = py - cy
            rx_rot = dx * math.cos(rad) - dy * math.sin(rad)
            ry_rot = dx * math.sin(rad) + dy * math.cos(rad)
            
            # Standard ellipse inclusion: (x/rx)^2 + (y/ry)^2 <= 1
            if (rx_rot / max(rx, 1.0)) ** 2 + (ry_rot / max(ry, 1.0)) ** 2 <= 1.0:
                return "DANGER" if zone_name == "danger" else "CAUTION"

        return "SAFE"
