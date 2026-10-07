"""
Phase 4 — Metric TTC & Kinematics

Calculates true physical world velocity (m/s) and Metric Time-To-Collision (TTC).
Replaces the image-space TTC proxy with a calibrated physical model.
Avoids substituting '99.90' for undefined TTC, using explicit 'UNDEFINED' statuses instead.
"""
import math
from typing import Tuple, Dict, Any, Optional

def calculate_world_velocity(
    p_current: Tuple[float, float],
    p_previous: Tuple[float, float],
    time_delta_sec: float,
    max_physical_speed: float = 10.0
) -> Tuple[float, float, float]:
    """
    Calculates velocity vector (vx, vy) and magnitude in world coordinates (m/s).
    Points must be in ground-plane world coordinates (meters).
    Clamps unphysical velocity spikes (e.g. caused by tracker ID swaps).
    """
    if time_delta_sec <= 0:
        return 0.0, 0.0, 0.0
        
    vx = (p_current[0] - p_previous[0]) / time_delta_sec
    vy = (p_current[1] - p_previous[1]) / time_delta_sec
    speed = math.hypot(vx, vy)
    
    if speed > max_physical_speed:
        scale = max_physical_speed / speed
        vx *= scale
        vy *= scale
        speed = max_physical_speed
        
    return vx, vy, speed

def compute_metric_ttc(
    person_pos_m: Tuple[float, float],
    forklift_pos_m: Tuple[float, float],
    person_vel_m_s: Tuple[float, float],
    forklift_vel_m_s: Tuple[float, float],
    distance_m: float,
    collision_radius_m: float = 1.8
) -> Dict[str, Any]:
    """
    Computes true metric Time-To-Collision (TTC) with Closest Point of Approach (CPA) filter.
    Prevents safe orthogonal crossing movements from triggering false collision alerts.
    """
    rx = person_pos_m[0] - forklift_pos_m[0]
    ry = person_pos_m[1] - forklift_pos_m[1]
    
    if distance_m > 1e-3:
        r_hat_x = rx / distance_m
        r_hat_y = ry / distance_m
    else:
        r_hat_x, r_hat_y = 0.0, 0.0
        
    v_rel_x = forklift_vel_m_s[0] - person_vel_m_s[0]
    v_rel_y = forklift_vel_m_s[1] - person_vel_m_s[1]
    
    # Approach velocity: rate at which range is decreasing
    raw_v_closing = v_rel_x * r_hat_x + v_rel_y * r_hat_y
    v_approach = max(0.0, raw_v_closing)
    
    # 2D Closest Point of Approach (CPA) / Miss-Distance Calculation
    # r(t) = r0 - v_rel * t  (vector from forklift to person)
    v_rel_sq = v_rel_x**2 + v_rel_y**2
    
    ttc_sec = None
    ttc_status = "UNDEFINED"
    miss_distance = distance_m
    
    if v_approach <= 0.1 or distance_m <= 0.1:
        ttc_status = "NO_APPROACH"
    elif v_rel_sq > 1e-4:
        # Time to closest point of approach:
        # t_cpa minimizes ||r0 - v_rel * t||^2 -> t_cpa = (r0 . v_rel) / ||v_rel||^2
        t_cpa = (rx * v_rel_x + ry * v_rel_y) / v_rel_sq
        
        if t_cpa > 0:
            cpa_x = rx - v_rel_x * t_cpa
            cpa_y = ry - v_rel_y * t_cpa
            miss_distance = math.hypot(cpa_x, cpa_y)
            
            # Only declare an active collision course if the miss distance is within collision radius!
            if miss_distance <= collision_radius_m:
                ttc_sec = round(t_cpa, 2)
                ttc_status = "VALID"
            else:
                ttc_status = "CROSSING_CLEARED"
        else:
            ttc_status = "NO_APPROACH"
    else:
        ttc_status = "NO_APPROACH"
    
    return {
        "relative_velocity_m_s": round(v_approach, 2),
        "miss_distance_m": round(miss_distance, 2),
        "ttc_sec": ttc_sec,
        "ttc_status": ttc_status
    }
