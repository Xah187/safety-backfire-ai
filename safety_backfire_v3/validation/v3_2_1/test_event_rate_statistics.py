"""
test_event_rate_statistics.py
Verifies exact Poisson rate confidence intervals for false alarms and missed events,
preventing invalid application of binomial Wilson score intervals to count rates.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_event_rate_statistics():
    event_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/event_metric_audit.json"
    assert event_file.exists(), "event_metric_audit.json missing"
    
    with open(event_file) as f:
        data = json.load(f)
        
    full = data["full_corpus_23min"]
    assert full["duration_hours"] == 0.3833
    assert full["ground_truth_events_N"] == 50
    assert full["true_positives"] == 47
    assert full["false_positives"] == 3
    assert full["false_negatives"] == 3
    
    # 3 / 0.3833 hours = 7.8267 -> 7.83 events/hr
    assert abs(full["false_events_per_hour"] - 7.83) < 0.05
    assert abs(full["missed_events_per_hour"] - 7.83) < 0.05
    
    # Exact Poisson 95% CI check
    ci = full["false_events_per_hour_poisson_ci"]
    assert abs(ci[0] - 1.614) < 0.05
    assert abs(ci[1] - 22.868) < 0.05
    
    blind = data["blind_test_11min"]
    assert blind["duration_hours"] == 0.1833
    assert blind["ground_truth_events_N"] == 16
    assert blind["false_positives"] == 1
    assert abs(blind["false_events_per_hour"] - 5.45) < 0.05
    
    b_ci = blind["false_events_per_hour_poisson_ci"]
    assert abs(b_ci[0] - 0.138) < 0.05
    assert abs(b_ci[1] - 30.388) < 0.05

if __name__ == "__main__":
    test_event_rate_statistics()
    print("[PASS] test_event_rate_statistics")
