import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.event_engine import InteractionEvent
from core.risk_engine import RiskEngine

def test_risk_engine():
    engine = RiskEngine()
    
    # Create a mock high-risk event
    evt1 = InteractionEvent("EVT_1", 1, 99, 1, 0.0)
    evt1.update(1, 0.0, 0.5, 20.0, "DANGER")
    evt1.update(2, 0.1, 0.4, 15.0, "DANGER")
    evt1.update(3, 0.2, 0.6, 5.0, "CAUTION")
    evt1.end()
    
    score1 = engine.calculate_risk_exposure(evt1)
    
    # Create a mock low-risk event
    evt2 = InteractionEvent("EVT_2", 2, 99, 1, 0.0)
    evt2.update(1, 0.0, 4.0, 2.0, "SAFE")
    evt2.update(2, 0.1, 4.2, 1.0, "SAFE")
    evt2.end()
    
    score2 = engine.calculate_risk_exposure(evt2)
    
    print(f"High risk score: {score1}")
    print(f"Low risk score: {score2}")
    
    assert score1 > score2, "High risk event should have a higher score than low risk event"
    assert score1 > 0, "Score should be positive"
    
    print("RiskEngine tests passed successfully!")

if __name__ == "__main__":
    test_risk_engine()
