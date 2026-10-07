"""
test_hazard_metric_definitions.py
Verifies distinction between Pooled (Micro) and Unweighted Macro metrics,
and programmatically verifies that REAL_WORLD_VALIDATED count is 6, not 5.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_hazard_metric_definitions():
    haz_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/hazard_metric_audit.json"
    assert haz_file.exists(), "hazard_metric_audit.json missing"
    
    with open(haz_file) as f:
        data = json.load(f)
        
    hazards = data["hazard_list"]
    assert len(hazards) == 12
    
    # Programmatic count of statuses
    real_world_val = sum(1 for h in hazards if h["status"] == "REAL_WORLD_VALIDATED")
    limited_val = sum(1 for h in hazards if h["status"] == "LIMITED_REAL_WORLD_VALIDATION")
    synth_only = sum(1 for h in hazards if h["status"] == "SYNTHETIC_ONLY")
    
    assert real_world_val == 6, f"Expected 6 REAL_WORLD_VALIDATED, got {real_world_val}"
    assert limited_val == 5, f"Expected 5 LIMITED_REAL_WORLD_VALIDATION, got {limited_val}"
    assert synth_only == 1, f"Expected 1 SYNTHETIC_ONLY, got {synth_only}"
    
    # Pooled calculations
    total_tp = sum(h["tp"] for h in hazards)
    total_fp = sum(h["fp"] for h in hazards)
    total_fn = sum(h["fn"] for h in hazards)
    
    assert total_tp == 268
    assert total_fp == 13
    assert total_fn == 18
    
    micro_prec = total_tp / (total_tp + total_fp)
    micro_rec = total_tp / (total_tp + total_fn)
    
    assert abs(micro_prec - 0.9537) < 0.001
    assert abs(micro_rec - 0.9371) < 0.001
    
    # Macro calculations
    macro_prec = sum(h["tp"] / (h["tp"] + h["fp"]) for h in hazards) / len(hazards)
    macro_rec = sum(h["tp"] / (h["tp"] + h["fn"]) for h in hazards) / len(hazards)
    
    assert abs(macro_prec - 0.9480) < 0.001
    assert abs(macro_rec - 0.9288) < 0.001

if __name__ == "__main__":
    test_hazard_metric_definitions()
    print("[PASS] test_hazard_metric_definitions")
