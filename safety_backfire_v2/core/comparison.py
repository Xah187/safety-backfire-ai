"""
Phase 9 — Before / After Comparison Engine

Compares two segments of data (Before vs After) at the Event-level and Risk-level.
Produces detailed delta metrics (absolute, percentage, direction) for all key factors.
Does NOT independently declare a Backfire; it only computes the mathematical differences.
"""
from typing import Dict, Any, List

def calculate_change(before: float, after: float) -> Dict[str, Any]:
    """Helper to safely calculate absolute and percentage changes."""
    abs_change = after - before
    if before == 0.0:
        if after == 0.0:
            pct_change = 0.0
        else:
            pct_change = float('inf') if after > 0 else float('-inf')
    else:
        pct_change = (abs_change / before) * 100.0
        
    direction = "INCREASE" if abs_change > 0 else ("DECREASE" if abs_change < 0 else "NO_CHANGE")
    
    return {
        "before": round(before, 3),
        "after": round(after, 3),
        "absolute_change": round(abs_change, 3),
        "percentage_change": round(pct_change, 2) if pct_change not in [float('inf'), float('-inf')] else pct_change,
        "direction": direction
    }

class ComparisonEngine:
    
    @staticmethod
    def extract_segment_metrics(events: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extracts aggregated metrics from a list of resolved JSON event dictionaries.
        """
        num_events = len(events)
        if num_events == 0:
            return {
                "min_distance_m": 0.0,
                "median_distance_m": 0.0,
                "total_risk_exposure": 0.0,
                "num_events": 0.0,
                "high_severity_events": 0.0,
                "avg_interaction_duration_sec": 0.0,
                "peak_approach_velocity": 0.0,
                "trajectory_crossings": 0.0
            }
            
        valid_min_dists = [e["min_distance_m"] for e in events if e.get("min_distance_m") is not None]
        valid_med_dists = [e["median_distance_m"] for e in events if e.get("median_distance_m") is not None]
        
        min_dist = min(valid_min_dists) if valid_min_dists else 0.0
        # Average of the median distances for the segment
        avg_median_dist = sum(valid_med_dists)/len(valid_med_dists) if valid_med_dists else 0.0
        
        total_risk = sum([e.get("risk_exposure_score", 0.0) for e in events])
        high_severity = sum([1 for e in events if e.get("severity_level") in ["HIGH", "CRITICAL"]])
        
        durations = [e.get("duration_sec", 0.0) for e in events]
        avg_duration = sum(durations)/len(durations) if durations else 0.0
        
        peak_speeds = [e.get("peak_approach_speed", 0.0) for e in events if e.get("peak_approach_speed") is not None]
        max_peak_speed = max(peak_speeds) if peak_speeds else 0.0
        
        crossings = sum([1 for e in events if e.get("semantic_type") == "CROSSING"])
        
        return {
            "min_distance_m": min_dist,
            "median_distance_m": avg_median_dist,
            "total_risk_exposure": total_risk,
            "num_events": float(num_events),
            "high_severity_events": float(high_severity),
            "avg_interaction_duration_sec": avg_duration,
            "peak_approach_velocity": max_peak_speed,
            "trajectory_crossings": float(crossings)
        }
        
    @staticmethod
    def compare(before_events: List[Dict[str, Any]], after_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compares before and after segments and computes the deltas.
        """
        b_metrics = ComparisonEngine.extract_segment_metrics(before_events)
        a_metrics = ComparisonEngine.extract_segment_metrics(after_events)
        
        comparison = {}
        for key in b_metrics.keys():
            comparison[key] = calculate_change(b_metrics[key], a_metrics[key])
            
        return {
            "metrics": comparison,
            "summary": "Comparison completed. See Phase 13 (Decision Engine) for backfire assessment."
        }
