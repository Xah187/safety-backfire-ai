import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.event_engine import InteractionEvent
from core.severity import SeverityEngine

def test_severity_engine():
    # 1. Critical Event
    evt_crit = InteractionEvent("EVT_1", 1, 99, 1, 0.0)
    for i in range(15):
        evt_crit.update(i, i*0.1, 0.5, 3.0, "DANGER")
    evt_crit.end()
    
    res_crit = SeverityEngine.calculate_severity(evt_crit)
    assert res_crit["severity_level"] == "CRITICAL"
    assert res_crit["evidence_confidence"] == 0.95
    
    # 2. Low Event
    evt_low = InteractionEvent("EVT_2", 2, 99, 1, 0.0)
    evt_low.update(1, 0.0, 5.0, 0.1, "SAFE")
    evt_low.update(2, 0.1, 5.1, 0.1, "SAFE")
    evt_low.end()
    
    res_low = SeverityEngine.calculate_severity(evt_low)
    assert res_low["severity_level"] == "LOW"
    assert res_low["evidence_confidence"] == 0.3
    
    print("SeverityEngine tests passed successfully!")

if __name__ == "__main__":
    test_severity_engine()
