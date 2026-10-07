"""
Phase 2 — Risk Exposure Engine

Calculates a multi-factor risk exposure score for InteractionEvents.
Uses configurable weights to prevent arbitrary hardcoding of safety heuristics.
"""
import yaml
import math
from pathlib import Path
from typing import Dict, Any

from core.event_engine import InteractionEvent

class RiskEngine:
    def __init__(self, config_path: str = None):
        if config_path is None:
            ROOT = Path(__file__).resolve().parent.parent
            config_path = ROOT / "config/risk_weights.yaml"
            
        with open(config_path, 'r') as f:
            self.weights = yaml.safe_load(f)
            
    def calculate_risk_exposure(self, event: InteractionEvent) -> float:
        """
        Calculates a continuous risk exposure score based on distance, duration,
        and kinematics. Higher score = higher risk.
        """
        # 1. Distance Risk
        # We invert distance: smaller distance yields exponentially higher risk
        min_dist = getattr(event, "min_distance_m", None)
        min_dist = min_dist if min_dist is not None else 10.0
        median_dist = getattr(event, "median_distance_m", None)
        median_dist = median_dist if median_dist is not None else 10.0
        
        scale = self.weights['distance']['exponential_scale']
        # e.g., if min_dist is 0.5m, risk = 40 * exp(-1.5 * 0.5) = 18.9
        dist_risk = (self.weights['distance']['min_distance_weight'] * math.exp(-scale * min_dist)) + \
                    (self.weights['distance']['median_distance_weight'] * math.exp(-scale * median_dist))
                    
        # 2. Duration Risk
        # Time spent interacting inherently increases risk exposure
        duration = getattr(event, "duration_sec", 0.0)
        # Determine time in caution/danger by inspecting the event zones list
        # We assume uniform frame distribution for simplicity
        zones = getattr(event, "zones", [])
        total_frames = len(zones)
        if total_frames > 0:
            caution_ratio = sum(1 for z in zones if z == "CAUTION") / total_frames
            danger_ratio = sum(1 for z in zones if z == "DANGER") / total_frames
        else:
            caution_ratio, danger_ratio = 0.0, 0.0
            
        time_in_caution = duration * caution_ratio
        time_in_danger = duration * danger_ratio
        
        duration_risk = (duration * self.weights['duration']['base_weight']) + \
                        (time_in_caution * self.weights['duration']['base_weight'] * self.weights['duration']['caution_zone_multiplier']) + \
                        (time_in_danger * self.weights['duration']['base_weight'] * self.weights['duration']['danger_zone_multiplier'])
                        
        # 3. Kinematic Risk (Approach velocity)
        peak_speed = getattr(event, "peak_approach_speed", 0.0)
        peak_speed = peak_speed if peak_speed is not None else 0.0
        raw_kinematic_risk = peak_speed * self.weights['kinematics']['peak_approach_speed_weight']
        kinematic_risk = min(raw_kinematic_risk, self.weights['kinematics']['max_velocity_contribution'])
        
        total_exposure = dist_risk + duration_risk + kinematic_risk
        return round(total_exposure, 2)
