"""
test_long_duration_label_integrity.py
Verifies that the 60-minute 108,000-frame stability test is explicitly labeled as
a SYNTHETIC & REPLAY ENDURANCE TEST, preventing misleading terminology inflation.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_long_duration_label_integrity():
    claim_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/claim_evidence_registry.json"
    assert claim_file.exists(), "claim_evidence_registry.json missing"
    
    with open(claim_file) as f:
        data = json.load(f)
        
    mem_claim = next(c for c in data["matrix"] if "memory" in c["claim"].lower())
    assert "synthetic" in mem_claim["data_type"].lower()
    assert "endurance" in mem_claim["data_type"].lower()
    assert "synthetic" in mem_claim["allowed_wording"].lower()

if __name__ == "__main__":
    test_long_duration_label_integrity()
    print("[PASS] test_long_duration_label_integrity")
