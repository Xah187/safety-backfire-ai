"""
test_claim_evidence_traceability.py
Verifies that all major claims in the claim-evidence matrix trace directly to
underlying data, sample sizes, and approved conservative wording.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_claim_evidence_traceability():
    claim_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/claim_evidence_registry.json"
    assert claim_file.exists(), "claim_evidence_registry.json missing"
    
    with open(claim_file) as f:
        data = json.load(f)
        
    matrix = data["matrix"]
    assert len(matrix) >= 4
    
    for item in matrix:
        assert "claim" in item
        assert "evidence" in item
        assert "data_type" in item
        assert "sample_size" in item
        assert "allowed_wording" in item
        assert item["independent"] is True
        assert item["reproducible"] is True

if __name__ == "__main__":
    test_claim_evidence_traceability()
    print("[PASS] test_claim_evidence_traceability")
