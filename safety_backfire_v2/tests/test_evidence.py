import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.event_engine import InteractionEvent
from core.evidence import EvidenceEngine

def test_evidence_engine():
    engine = EvidenceEngine()
    
    # 1. Test robust data
    evt_good = InteractionEvent("EVT_1", 1, 99, 1, 0.0)
    for i in range(20):
        evt_good.update(i, i*0.1, 2.0, 1.0, "SAFE")
    evt_good.end()
    
    res_good = engine.evaluate_segment_evidence([evt_good], total_video_frames=100, tracking_failures=5)
    assert res_good["evidence_level"] == "HIGH"
    assert res_good["evidence_confidence"] == 1.0
    
    # 2. Test poor data (fragmentation + out of bounds)
    evt_frag = InteractionEvent("EVT_2", 2, 99, 1, 0.0)
    evt_frag.update(1, 0.0, 20.0, 1.0, "SAFE") # out of bounds distance
    evt_frag.end()
    
    res_poor = engine.evaluate_segment_evidence([evt_frag], total_video_frames=100, tracking_failures=30)
    # Penalties: fragmentation (0.3) + out of bounds (0.1) + failure rate (0.4) = 0.8 penalty -> 0.2 conf
    assert res_poor["evidence_level"] == "INSUFFICIENT"
    assert res_poor["evidence_confidence"] <= 0.3
    
    print("EvidenceEngine tests passed successfully!")

if __name__ == "__main__":
    test_evidence_engine()
