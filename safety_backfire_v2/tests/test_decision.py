import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.decision import DecisionEngine

def test_decision_engine():
    # Mock inputs simulating a strong Backfire effect
    evidence = {
        "evidence_level": "HIGH",
        "evidence_confidence": 0.95,
        "limitations": []
    }
    
    comparison = {
        "total_risk_exposure": {"absolute_change": 50.0, "percentage_change": 100.0},
        "high_severity_events": {"absolute_change": 2.0}
    }
    
    redistribution = {
        "risk_displaced": True,
        "decreased_zones": ["DANGER"],
        "increased_zones": ["CAUTION"]
    }
    
    counterfactual = {
        "counterfactual_signal": "CONSISTENT_WITH_BACKFIRE",
        "counterfactual_deviation": 40.0
    }
    
    verdict = DecisionEngine.assess(evidence, comparison, redistribution, counterfactual)
    
    assert verdict["signal"] == "SAFETY_BACKFIRE"
    assert verdict["strength"] == 1.0
    assert verdict["confidence"] == 0.95
    assert len(verdict["reasoning"]) == 4
    
    # Test Insufficient Evidence
    poor_evidence = {
        "evidence_level": "INSUFFICIENT",
        "evidence_confidence": 0.2,
        "limitations": ["Too much fragmentation"]
    }
    
    poor_verdict = DecisionEngine.assess(poor_evidence, comparison, redistribution, counterfactual)
    assert poor_verdict["signal"] == "INSUFFICIENT_EVIDENCE"
    
    print("DecisionEngine tests passed successfully!")

if __name__ == "__main__":
    test_decision_engine()
