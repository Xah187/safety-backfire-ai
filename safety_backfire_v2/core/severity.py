"""
Phase 7 — Risk Event Severity

Calculates an overall severity score and level for an interaction event.
Outputs: severity_score (0-100), severity_level (LOW, MODERATE, HIGH, CRITICAL), evidence_confidence
Note: These classifications are internal system labels, not official industrial safety certifications.
"""
from typing import Dict, Any, Optional
from core.event_engine import InteractionEvent
from core.semantics import SemanticClassifier

class SeverityEngine:
    
    @staticmethod
    def calculate_severity(event: InteractionEvent) -> Dict[str, Any]:
        """
        Evaluates the severity of a fully resolved InteractionEvent.
        """
        min_dist = event.min_distance_m if event.min_distance_m is not None else 10.0
        peak_speed = event.peak_approach_speed if event.peak_approach_speed is not None else 0.0
        duration = event.duration_sec
        semantic_type = SemanticClassifier.classify(event)
        
        # 1. Base Score from Distance (0 to 60 points)
        # Closer than 1.0m gets max points, scales down to 0 at 4.0m
        if min_dist < 1.0:
            dist_score = 60.0
        elif min_dist > 4.0:
            dist_score = 0.0
        else:
            dist_score = 60.0 * (1.0 - ((min_dist - 1.0) / 3.0))
            
        # 2. Kinematic Boost (0 to 25 points)
        # Speeds above 2.0 m/s get max points
        speed_score = min(25.0, (peak_speed / 2.0) * 25.0)
        
        # 3. Duration & Zone Boost (0 to 15 points)
        duration_score = min(10.0, (duration / 5.0) * 10.0)
        zone_boost = 5.0 if event.dominant_zone == "DANGER" else 0.0
        
        # 4. Semantic Modifiers
        semantic_multiplier = 1.0
        if semantic_type == "POTENTIAL_NEAR_MISS":
            semantic_multiplier = 1.2
        elif semantic_type == "CROSSING" and min_dist < 2.0:
            semantic_multiplier = 1.1
        elif semantic_type == "DIVERGING":
            semantic_multiplier = 0.8
            
        # Final calculation
        raw_score = (dist_score + speed_score + duration_score + zone_boost) * semantic_multiplier
        severity_score = round(min(100.0, max(0.0, raw_score)), 1)
        
        # Level assignment
        if severity_score >= 80.0:
            level = "CRITICAL"
        elif severity_score >= 50.0:
            level = "HIGH"
        elif severity_score >= 25.0:
            level = "MODERATE"
        else:
            level = "LOW"
            
        # Evidence Confidence (Placeholder for Phase 8, but we estimate based on points count)
        # If the event only has 2 points (e.g. tracking failed immediately), confidence is low.
        pts = len(event.distances_m)
        if pts < 3:
            evidence_conf = 0.3
        elif pts < 10:
            evidence_conf = 0.7
        else:
            evidence_conf = 0.95
            
        return {
            "severity_score": severity_score,
            "severity_level": level,
            "evidence_confidence": evidence_conf,
            "disclaimer": "Internal system classification only. Not an official safety certification."
        }
