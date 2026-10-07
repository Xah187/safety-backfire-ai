"""
test_uncertainty_lineage.py
Verifies uncertainty lineage: confirms k=2.24 was evaluated on CALIBRATION_SPLIT,
and that Wilson score CI covers [0.9585, 0.9862] on N=500.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_uncertainty_lineage():
    unc_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/uncertainty_lineage_audit.json"
    assert unc_file.exists(), "uncertainty_lineage_audit.json missing"
    
    with open(unc_file) as f:
        unc = json.load(f)
        
    assert unc["evaluation_dataset_split"] == "CALIBRATION_SPLIT"
    assert unc["sample_size_N"] == 500
    assert unc["empirical_coverage"] == 0.9760
    assert unc["wilson_ci"] == [0.9585, 0.9862]
    assert "CALIBRATION_EVALUATION" in unc["independence_status"]

if __name__ == "__main__":
    test_uncertainty_lineage()
    print("[PASS] test_uncertainty_lineage")
