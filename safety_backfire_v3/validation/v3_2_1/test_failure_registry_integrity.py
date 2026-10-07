"""
test_failure_registry_integrity.py
Verifies failure registry lineage and arithmetic reconciliation:
49 confirmed failures (42 resolved + 7 boundaries) + 6 unreproduced candidates = 55 total IDs.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_failure_registry_integrity():
    reg_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/failure_registry_audit.json"
    assert reg_file.exists(), "failure_registry_audit.json missing"
    
    with open(reg_file) as f:
        data = json.load(f)
        
    assert data["total_cataloged_ids"] == 55
    assert data["confirmed_failures_count"] == 49
    assert data["resolved_failures_count"] == 42
    assert data["documented_boundaries_count"] == 7
    assert data["unreproduced_candidates_count"] == 6
    assert data["open_critical_defects_count"] == 0
    
    # Mathematical identity check
    assert data["confirmed_failures_count"] == data["resolved_failures_count"] + data["documented_boundaries_count"]
    assert data["total_cataloged_ids"] == data["confirmed_failures_count"] + data["unreproduced_candidates_count"]
    
    assert len(data["documented_physical_boundaries"]) == 7

if __name__ == "__main__":
    test_failure_registry_integrity()
    print("[PASS] test_failure_registry_integrity")
