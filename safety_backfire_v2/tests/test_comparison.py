import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.comparison import ComparisonEngine

def test_comparison_engine():
    # Mock data
    before = [
        {"min_distance_m": 2.0, "median_distance_m": 2.5, "risk_exposure_score": 10.0, "severity_level": "MODERATE", "duration_sec": 1.0},
        {"min_distance_m": 1.5, "median_distance_m": 1.8, "risk_exposure_score": 15.0, "severity_level": "HIGH", "duration_sec": 1.5}
    ]
    
    after = [
        {"min_distance_m": 1.0, "median_distance_m": 1.2, "risk_exposure_score": 30.0, "severity_level": "CRITICAL", "duration_sec": 2.0},
        {"min_distance_m": 0.5, "median_distance_m": 0.8, "risk_exposure_score": 50.0, "severity_level": "CRITICAL", "duration_sec": 3.0},
        {"min_distance_m": 2.0, "median_distance_m": 2.5, "risk_exposure_score": 10.0, "severity_level": "LOW", "duration_sec": 1.0}
    ]
    
    comp = ComparisonEngine.compare(before, after)
    metrics = comp["metrics"]
    
    # 1. Total events increased 2 -> 3
    assert metrics["num_events"]["direction"] == "INCREASE"
    assert metrics["num_events"]["absolute_change"] == 1.0
    assert metrics["num_events"]["percentage_change"] == 50.0
    
    # 2. Min distance decreased 1.5 -> 0.5
    assert metrics["min_distance_m"]["direction"] == "DECREASE"
    assert metrics["min_distance_m"]["absolute_change"] == -1.0
    
    # 3. High severity events increased 1 -> 2
    assert metrics["high_severity_events"]["before"] == 1.0
    assert metrics["high_severity_events"]["after"] == 2.0
    
    # 4. Risk exposure increased 25.0 -> 90.0
    assert metrics["total_risk_exposure"]["before"] == 25.0
    assert metrics["total_risk_exposure"]["after"] == 90.0
    
    print("ComparisonEngine tests passed successfully!")

if __name__ == "__main__":
    test_comparison_engine()
