"""
test_causality_evidence_integrity.py
Verifies causality audit integrity: Difference-in-Differences enforcement,
confounder detection, and suspension of binary attribution when parallel trends fail.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_causality_evidence_integrity():
    caus_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/causality_audit.json"
    assert caus_file.exists(), "causality_audit.json missing"
    
    with open(caus_file) as f:
        data = json.load(f)
        
    assert "Difference-in-Differences" in data["methodology"]
    assert "TEMPORAL_CORRELATION != CAUSAL_EFFECT" in data["axiom"]
    
    scenarios = data["scenarios_audited"]
    assert scenarios["CLEAN_ISOLATION"]["status"] == "ATTRIBUTED_DIRECT_EFFECT"
    assert scenarios["TRAFFIC_SURGE"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert scenarios["SHIFT_CHANGE"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert scenarios["FACILITY_SLOWDOWN"]["status"] == "INSUFFICIENT_EVIDENCE"

if __name__ == "__main__":
    test_causality_evidence_integrity()
    print("[PASS] test_causality_evidence_integrity")
