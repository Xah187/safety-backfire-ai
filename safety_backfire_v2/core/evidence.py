"""
Phase 8 — Evidence Engine

Evaluates the overall quality and reliability of the data before allowing a verdict.
Outputs evidence_confidence, evidence_level, and explicit limitations.
"""
from typing import List, Dict, Any
from core.event_engine import InteractionEvent

class EvidenceEngine:
    
    @staticmethod
    def evaluate_segment_evidence(
        events: List[InteractionEvent], 
        total_video_frames: int, 
        tracking_failures: int = 0
    ) -> Dict[str, Any]:
        """
        Evaluates the quality of evidence for a specific video segment.
        """
        limitations = []
        confidence_penalties = 0.0
        
        # 1. Total events check
        if len(events) == 0:
            limitations.append("No interaction events observed. Analysis relies on zero-event baseline.")
            confidence_penalties += 0.4
            
        # 2. Track continuity & fragmentation
        short_events = [e for e in events if e.duration_sec < 0.2]
        if len(events) > 0 and (len(short_events) / len(events)) > 0.5:
            limitations.append("High track fragmentation: Over 50% of events lasted less than 0.2 seconds.")
            confidence_penalties += 0.3
            
        # 3. Calibration Quality
        # Check how many events relied heavily on fallback ID extrapolation or poor TTC
        # For this phase, we look at the raw distances (are they extremely small or large?)
        out_of_bounds_events = [e for e in events if e.min_distance_m is None or e.min_distance_m > 15.0]
        if out_of_bounds_events:
            limitations.append(f"{len(out_of_bounds_events)} events occurred outside calibrated homography bounds.")
            confidence_penalties += (len(out_of_bounds_events) * 0.1)
            
        # 4. Tracking Failures
        if total_video_frames > 0:
            failure_rate = tracking_failures / total_video_frames
            if failure_rate > 0.2:
                limitations.append(f"High tracking failure rate ({failure_rate:.1%} of frames lacked detections).")
                confidence_penalties += 0.4
                
        # Calculate final confidence
        evidence_confidence = round(max(0.0, 1.0 - confidence_penalties), 2)
        
        # Assign Level
        if evidence_confidence >= 0.8:
            level = "HIGH"
        elif evidence_confidence >= 0.6:
            level = "MODERATE"
        elif evidence_confidence >= 0.4:
            level = "LOW"
        else:
            level = "INSUFFICIENT"
            limitations.append("CRITICAL: Evidence is insufficient to support any causal or comparative claims.")
            
        if not limitations:
            limitations.append("None detected. Data appears robust.")
            
        return {
            "evidence_confidence": evidence_confidence,
            "evidence_level": level,
            "limitations": limitations
        }
