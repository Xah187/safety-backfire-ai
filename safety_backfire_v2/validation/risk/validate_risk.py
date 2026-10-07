"""
Phase 8 — Risk Engine Validation

Validates the mathematical properties of the RiskEngine.
Ensures monotonicity: Closer, longer, and faster approaches strictly increase risk.
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.risk_engine import RiskEngine
from core.event_engine import InteractionEvent
import math

def run_risk_validation():
    engine = RiskEngine()
    passed = True
    errors = []
    
    # 1. Monotonicity with Distance (Closer = Higher Risk)
    e1 = InteractionEvent("E1", 1, 99, 1, 0.0)
    e1.update(1, 0.0, 1.0, 0.0, "CAUTION")
    e1.end()
    
    e2 = InteractionEvent("E2", 1, 99, 1, 0.0)
    e2.update(1, 0.0, 3.0, 0.0, "CAUTION")
    e2.end()
    
    risk_d1 = engine.calculate_risk_exposure(e1)
    risk_d2 = engine.calculate_risk_exposure(e2)
    
    if not (risk_d1 > risk_d2):
        passed = False
        errors.append(f"Distance monotonicity failed: dist=1.0m ({risk_d1}) vs dist=3.0m ({risk_d2})")
        
    # 2. Monotonicity with Velocity (Faster approach = Higher Risk, below cap)
    e3 = InteractionEvent("E3", 1, 99, 1, 0.0)
    e3.update(1, 0.0, 2.0, 2.0, "CAUTION")
    e3.end()
    
    e4 = InteractionEvent("E4", 1, 99, 1, 0.0)
    e4.update(1, 0.0, 2.0, 0.5, "CAUTION")
    e4.end()
    
    risk_v1 = engine.calculate_risk_exposure(e3)
    risk_v2 = engine.calculate_risk_exposure(e4)
    
    if not (risk_v1 > risk_v2):
        passed = False
        errors.append(f"Velocity monotonicity failed: v=2.0m/s ({risk_v1}) vs v=0.5m/s ({risk_v2})")
        
    # 3. Monotonicity with Duration (Longer = Higher Risk)
    e5 = InteractionEvent("E5", 1, 99, 1, 0.0)
    e5.update(1, 0.0, 2.0, 0.0, "CAUTION")
    e5.update(2, 0.1, 2.0, 0.0, "CAUTION")
    e5.end()
    
    e6 = InteractionEvent("E6", 1, 99, 1, 0.0)
    e6.update(1, 0.0, 2.0, 0.0, "CAUTION")
    e6.update(2, 0.1, 2.0, 0.0, "CAUTION")
    e6.update(3, 0.2, 2.0, 0.0, "CAUTION")
    e6.update(4, 0.3, 2.0, 0.0, "CAUTION")
    e6.end()
    
    risk_t1 = engine.calculate_risk_exposure(e5)
    risk_t2 = engine.calculate_risk_exposure(e6)
    
    if not (risk_t2 > risk_t1):
        passed = False
        errors.append(f"Duration monotonicity failed: 4 frames ({risk_t2}) vs 2 frames ({risk_t1})")
        
    report = {
        "risk_validation_passed": passed,
        "errors": errors
    }
    
    out_dir = ROOT / "validation" / "risk"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "risk_validation.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Risk Validation Passed: {passed}")
    if not passed:
        print(errors)

if __name__ == "__main__":
    run_risk_validation()
