"""
Phase 10 — Risk Redistribution Engine

Analyzes where the risk moved between the Before and After segments.
Identifies if risk decreased in one area but increased in another, 
a core component of the Safety Backfire effect.
"""
from typing import List, Dict, Any

class RiskRedistributionEngine:
    
    @staticmethod
    def _aggregate_risk_by_zone(events: List[Dict[str, Any]]) -> Dict[str, float]:
        zone_risk = {"DANGER": 0.0, "CAUTION": 0.0, "SAFE": 0.0}
        for event in events:
            zone = event.get("zone", "SAFE")
            risk = event.get("risk_exposure_score", 0.0)
            if zone in zone_risk:
                zone_risk[zone] += risk
            else:
                zone_risk[zone] = risk
        return zone_risk

    @staticmethod
    def analyze_redistribution(before_events: List[Dict[str, Any]], after_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes how risk exposure shifted across zones.
        """
        before_zones = RiskRedistributionEngine._aggregate_risk_by_zone(before_events)
        after_zones = RiskRedistributionEngine._aggregate_risk_by_zone(after_events)
        
        redistribution = {}
        decreased_zones = []
        increased_zones = []
        
        for zone in before_zones.keys():
            b_risk = before_zones.get(zone, 0.0)
            a_risk = after_zones.get(zone, 0.0)
            delta = round(a_risk - b_risk, 2)
            
            redistribution[f"zone_{zone}"] = {
                "before_risk": round(b_risk, 2),
                "after_risk": round(a_risk, 2),
                "risk_delta": delta
            }
            
            if delta < -5.0: # Minimum threshold to consider it a meaningful decrease
                decreased_zones.append(zone)
            elif delta > 5.0: # Minimum threshold to consider it a meaningful increase
                increased_zones.append(zone)
                
        # Risk Displacement (Backfire) Check
        # If risk decreased in one zone but increased in another
        risk_displaced = len(decreased_zones) > 0 and len(increased_zones) > 0
        
        return {
            "redistribution": redistribution,
            "risk_displaced": risk_displaced,
            "decreased_zones": decreased_zones,
            "increased_zones": increased_zones,
            "insight": "Risk was displaced to other zones." if risk_displaced else "No significant spatial risk displacement detected."
        }
