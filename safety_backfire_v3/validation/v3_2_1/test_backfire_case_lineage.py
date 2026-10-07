"""
test_backfire_case_lineage.py
Verifies backfire case study lineage: 2 real intervention cases evaluated,
sample accuracy 2/2 (100%), and verifies the population claim prohibition.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_backfire_case_lineage():
    bf_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/backfire_case_audit.json"
    assert bf_file.exists(), "backfire_case_audit.json missing"
    
    with open(bf_file) as f:
        data = json.load(f)
        
    assert data["evaluated_cases_count"] == 2
    cases = data["cases"]
    assert len(cases) == 2
    
    c1 = cases[0]
    assert c1["case_id"] == "CASE_01_PHYSICAL_BARRIER"
    assert c1["intended_hazard_reduced"] is True
    assert "BLOCKED_EGRESS_HAZARD" in c1["unintended_secondary_hazards"][0]
    assert c1["classification"] == "NEW_HAZARD_CREATED / PARTIAL_BACKFIRE"
    assert c1["classification_correct"] is True
    
    c2 = cases[1]
    assert c2["case_id"] == "CASE_02_SPEED_LIMIT_GOVERNOR"
    assert c2["intended_hazard_reduced"] is True
    assert len(c2["unintended_secondary_hazards"]) == 0
    assert c2["classification"] == "RISK_REDUCED / GENUINE_SAFETY_GAIN"
    assert c2["classification_correct"] is True
    
    assert "population" in data["population_claim_prohibition"].lower()

if __name__ == "__main__":
    test_backfire_case_lineage()
    print("[PASS] test_backfire_case_lineage")
