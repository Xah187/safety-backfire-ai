import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.event_engine import InteractionEvent
from core.semantics import SemanticClassifier

def test_semantic_classifier():
    # 1. Test POTENTIAL_NEAR_MISS
    evt_nm = InteractionEvent("EVT_NM", 1, 99, 1, 0.0)
    evt_nm.update(1, 0.0, 3.0, 1.0, "CAUTION")
    evt_nm.update(2, 0.1, 1.0, 2.5, "DANGER")
    evt_nm.end()
    assert SemanticClassifier.classify(evt_nm) == "POTENTIAL_NEAR_MISS"
    
    # 2. Test CROSSING
    evt_cross = InteractionEvent("EVT_CR", 1, 99, 1, 0.0)
    evt_cross.update(1, 0.0, 4.0, 1.0, "SAFE")
    evt_cross.update(2, 0.1, 2.0, 1.5, "CAUTION")
    evt_cross.update(3, 0.2, 5.0, 0.5, "SAFE")
    evt_cross.end()
    assert SemanticClassifier.classify(evt_cross) == "CROSSING"
    
    # 3. Test STATIONARY_PROXIMITY
    evt_stat = InteractionEvent("EVT_ST", 1, 99, 1, 0.0)
    evt_stat.update(1, 0.0, 2.0, 0.1, "CAUTION")
    evt_stat.update(2, 0.1, 2.1, 0.2, "CAUTION")
    evt_stat.end()
    assert SemanticClassifier.classify(evt_stat) == "STATIONARY_PROXIMITY"
    
    print("SemanticClassifier tests passed successfully!")

if __name__ == "__main__":
    test_semantic_classifier()
