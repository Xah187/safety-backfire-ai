import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.redistribution import RiskRedistributionEngine

def test_redistribution_engine():
    before = [
        {"zone": "DANGER", "risk_exposure_score": 50.0},
        {"zone": "CAUTION", "risk_exposure_score": 10.0}
    ]
    
    after = [
        {"zone": "DANGER", "risk_exposure_score": 10.0}, # Dropped significantly
        {"zone": "CAUTION", "risk_exposure_score": 40.0} # Increased significantly
    ]
    
    res = RiskRedistributionEngine.analyze_redistribution(before, after)
    
    assert res["risk_displaced"] is True
    assert "DANGER" in res["decreased_zones"]
    assert "CAUTION" in res["increased_zones"]
    
    assert res["redistribution"]["zone_DANGER"]["risk_delta"] == -40.0
    assert res["redistribution"]["zone_CAUTION"]["risk_delta"] == 30.0
    
    print("RiskRedistributionEngine tests passed successfully!")

if __name__ == "__main__":
    test_redistribution_engine()
