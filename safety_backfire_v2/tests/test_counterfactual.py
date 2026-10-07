import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.counterfactual import CounterfactualEngine

def test_counterfactual_engine():
    # Before: 2 events with total risk = 20 over 1000 frames (Rate = 20 per 1000)
    before_events = [
        {"risk_exposure_score": 10.0},
        {"risk_exposure_score": 10.0}
    ]
    before_frames = 1000
    
    # After: 2000 frames. Expected risk = 40.
    # But observed risk is 100 -> Deviation is +60.
    after_events = [
        {"risk_exposure_score": 50.0},
        {"risk_exposure_score": 50.0}
    ]
    after_frames = 2000
    
    res = CounterfactualEngine.analyze(before_events, after_events, before_frames, after_frames)
    
    assert res["expected_exposure"] == 40.0
    assert res["observed_exposure"] == 100.0
    assert res["counterfactual_deviation"] == 60.0
    assert res["counterfactual_signal"] == "CONSISTENT_WITH_BACKFIRE"
    
    print("CounterfactualEngine tests passed successfully!")

if __name__ == "__main__":
    test_counterfactual_engine()
