"""
Phase 2 — Synthetic Controlled Scenarios

Generates synthetic scenarios with mathematically exact inputs and asserts the expected output from the V2 Engine.
"""
import sys
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.event_engine import InteractionEvent
from core.semantics import SemanticClassifier
from core.decision import DecisionEngine

def test_scenario_b_proximity():
    """Scenario B: Person enters proximity but doesn't approach fast."""
    evt = InteractionEvent("EVT_B", 1, 99, 1, 0.0)
    for i in range(10):
        # Distance stays around 2.0m, peak speed is very low
        evt.update(i, i*0.1, 2.0 + (i*0.01), 0.1, "CAUTION")
    evt.end()
    sem = SemanticClassifier.classify(evt)
    assert sem in ["STATIONARY_PROXIMITY", "PROXIMITY"], f"Expected PROXIMITY-like, got {sem}"
    return "Scenario B Passed: PROXIMITY"

def test_scenario_c_approaching():
    """Scenario C: Person and Forklift approaching fast."""
    evt = InteractionEvent("EVT_C", 1, 99, 1, 0.0)
    # Distance closes from 5.0m to 1.5m, high closing speed
    evt.update(1, 0.0, 5.0, 0.0, "SAFE")
    evt.update(2, 0.1, 3.0, 20.0, "CAUTION")
    evt.update(3, 0.2, 1.5, 15.0, "DANGER")
    evt.end()
    sem = SemanticClassifier.classify(evt)
    assert sem in ["POTENTIAL_NEAR_MISS", "APPROACHING"], f"Expected APPROACHING or NEAR MISS, got {sem}"
    # In semantics logic, dist_delta = -3.5, peak_speed = 20.0, min_dist = 1.5 -> POTENTIAL_NEAR_MISS
    return "Scenario C Passed: APPROACHING / NEAR MISS"

def test_scenario_d_crossing():
    """Scenario D: Person crosses Forklift path."""
    evt = InteractionEvent("EVT_D", 1, 99, 1, 0.0)
    # Distance decreases then increases (U-shape)
    evt.update(1, 0.0, 4.0, 1.0, "SAFE")
    evt.update(2, 0.1, 1.8, 1.0, "CAUTION")
    evt.update(3, 0.2, 4.2, 1.0, "SAFE")
    evt.end()
    sem = SemanticClassifier.classify(evt)
    assert sem == "CROSSING", f"Expected CROSSING, got {sem}"
    return "Scenario D Passed: CROSSING"

def test_scenario_e_backfire():
    """Scenario E: Intervention reduces Zone A but increases Zone B."""
    evidence = {"evidence_level": "HIGH", "evidence_confidence": 0.95, "limitations": []}
    
    # Risk exposure increased overall, severity increased slightly
    comparison = {
        "total_risk_exposure": {"absolute_change": 20.0, "percentage_change": 50.0},
        "high_severity_events": {"absolute_change": 1.0}
    }
    
    # Redistribution shows it decreased in DANGER but spiked in CAUTION
    redistribution = {
        "risk_displaced": True,
        "decreased_zones": ["DANGER"],
        "increased_zones": ["CAUTION"],
        "redistribution": {
            "zone_DANGER": {"risk_delta": -15.0},
            "zone_CAUTION": {"risk_delta": +35.0}
        }
    }
    
    counterfactual = {
        "counterfactual_signal": "CONSISTENT_WITH_BACKFIRE",
        "counterfactual_deviation": 18.0
    }
    
    verdict = DecisionEngine.assess(evidence, comparison, redistribution, counterfactual)
    assert verdict["signal"] == "SAFETY_BACKFIRE", f"Expected SAFETY_BACKFIRE, got {verdict['signal']}"
    return "Scenario E Passed: CONSISTENT_WITH_BACKFIRE"

def test_scenario_f_improvement():
    """Scenario F: Intervention truly reduces risk."""
    evidence = {"evidence_level": "HIGH", "evidence_confidence": 0.95, "limitations": []}
    
    # Risk exposure decreased
    comparison = {
        "total_risk_exposure": {"absolute_change": -30.0, "percentage_change": -60.0},
        "high_severity_events": {"absolute_change": -2.0}
    }
    
    redistribution = {
        "risk_displaced": False,
        "decreased_zones": ["DANGER", "CAUTION"],
        "increased_zones": [],
        "redistribution": {}
    }
    
    counterfactual = {
        "counterfactual_signal": "CONSISTENT_WITH_IMPROVEMENT",
        "counterfactual_deviation": -25.0
    }
    
    verdict = DecisionEngine.assess(evidence, comparison, redistribution, counterfactual)
    assert verdict["signal"] == "RISK_IMPROVEMENT", f"Expected RISK_IMPROVEMENT, got {verdict['signal']}"
    return "Scenario F Passed: RISK_IMPROVEMENT"

def test_scenario_g_insufficient():
    """Scenario G: Detection coverage insufficient."""
    evidence = {"evidence_level": "INSUFFICIENT", "evidence_confidence": 0.20, "limitations": ["Too many tracking gaps"]}
    comparison = {"total_risk_exposure": {"absolute_change": -30.0, "percentage_change": -60.0}, "high_severity_events": {"absolute_change": 0.0}}
    redistribution = {"risk_displaced": False}
    counterfactual = {"counterfactual_signal": "CONSISTENT_WITH_IMPROVEMENT"}
    
    verdict = DecisionEngine.assess(evidence, comparison, redistribution, counterfactual)
    assert verdict["signal"] == "INSUFFICIENT_EVIDENCE", f"Expected INSUFFICIENT_EVIDENCE, got {verdict['signal']}"
    return "Scenario G Passed: INSUFFICIENT_EVIDENCE"

def run_all_scenarios():
    results = [
        test_scenario_b_proximity(),
        test_scenario_c_approaching(),
        test_scenario_d_crossing(),
        test_scenario_e_backfire(),
        test_scenario_f_improvement(),
        test_scenario_g_insufficient()
    ]
    for res in results:
        print(res)
    print("\nPhase 2 Scenarios Completed Successfully!")

if __name__ == "__main__":
    run_all_scenarios()
