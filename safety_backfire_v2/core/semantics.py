"""
Phase 6 — Interaction Semantics

Classifies interactions into discrete behavioral semantics rather than relying purely on distance.
Categories:
- STATIONARY_PROXIMITY
- DIVERGING
- CROSSING
- APPROACHING
- POTENTIAL_NEAR_MISS
- PROXIMITY (fallback)
"""
from core.event_engine import InteractionEvent

class SemanticClassifier:
    
    @staticmethod
    def classify(event: InteractionEvent) -> str:
        """
        Assigns a semantic label to the interaction event based on its temporal properties.
        """
        if len(event.distances_m) < 2:
            return "PROXIMITY"
            
        start_dist = event.distances_m[0]
        end_dist = event.distances_m[-1]
        dist_delta = end_dist - start_dist
        
        peak_speed = event.peak_approach_speed if event.peak_approach_speed is not None else 0.0
        min_dist = event.min_distance_m if event.min_distance_m is not None else 10.0
        
        # 1. STATIONARY_PROXIMITY
        # Objects stay near each other but neither is approaching fast
        if abs(dist_delta) < 0.5 and peak_speed < 0.5:
            return "STATIONARY_PROXIMITY"
            
        # 2. POTENTIAL_NEAR_MISS
        # Distance closed significantly, high peak speed, very close minimum distance, danger zone
        if dist_delta < -1.0 and peak_speed > 2.0 and min_dist < 1.5 and event.dominant_zone == "DANGER":
            return "POTENTIAL_NEAR_MISS"
            
        # 3. DIVERGING
        # Overall distance increased significantly
        if dist_delta > 1.0:
            return "DIVERGING"
            
        # 4. CROSSING
        # Distance decreased then increased (U-shape in distance graph)
        # We check if min_distance happened somewhere in the middle, and it ended up further away
        if min_dist < start_dist - 0.5 and end_dist > min_dist + 0.5:
            return "CROSSING"
            
        # 5. APPROACHING
        # Distance simply decreased steadily without hitting near miss criteria
        if dist_delta < -0.5:
            return "APPROACHING"
            
        # Fallback
        return "PROXIMITY"
