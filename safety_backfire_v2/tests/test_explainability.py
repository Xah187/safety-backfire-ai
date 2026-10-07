import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.explainability import ExplainabilityLayer

def test_explainability_layer():
    verdict = {
        "signal": "SAFETY_BACKFIRE",
        "evidence_level": "HIGH",
        "confidence": 0.85,
        "reasoning": ["Risk exposure increased", "Risk displaced"]
    }
    
    comparison = {
        "total_risk_exposure": {"before": 10.0, "after": 50.0, "direction": "INCREASE", "percentage_change": 400.0},
        "high_severity_events": {"before": 0, "after": 2, "direction": "INCREASE", "absolute_change": 2}
    }
    
    redistribution = {
        "risk_displaced": True,
        "decreased_zones": ["DANGER"],
        "increased_zones": ["CAUTION"],
        "redistribution": {
            "zone_DANGER": {"risk_delta": -10.0},
            "zone_CAUTION": {"risk_delta": +50.0}
        }
    }
    
    before_events = []
    after_events = [
        {"event_id": "EVT_001", "start_frame": 100, "end_frame": 150, "zone": "CAUTION", "severity_level": "HIGH", "risk_exposure_score": 25.0},
        {"event_id": "EVT_002", "start_frame": 200, "end_frame": 250, "zone": "CAUTION", "severity_level": "HIGH", "risk_exposure_score": 25.0}
    ]
    
    explanation = ExplainabilityLayer.generate_explanation(verdict, comparison, redistribution, before_events, after_events)
    
    assert "consistent with the Safety Backfire effect" in explanation["summary"]
    assert len(explanation["key_changes"]) == 2
    assert len(explanation["supporting_events"]) == 2
    assert explanation["supporting_events"][0]["event_id"] == "EVT_001" or explanation["supporting_events"][0]["event_id"] == "EVT_002"
    assert len(explanation["risk_redistribution"]) == 2
    
    print("ExplainabilityLayer tests passed successfully!")

if __name__ == "__main__":
    test_explainability_layer()
