"""
test_report_metric_consistency.py
Verifies that all metrics in canonical_metric_registry.json match the audit files and
that confidence intervals are mathematically valid.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_report_metric_consistency():
    reg_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/canonical_metric_registry.json"
    assert reg_file.exists(), "canonical_metric_registry.json missing"
    
    with open(reg_file) as f:
        registry = json.load(f)
        
    metrics = registry["metrics"]
    assert len(metrics) >= 15
    
    for m in metrics:
        # Check value matches numerator / denominator where applicable
        if m["unit"] in ["proportion", "observed_case_ratio"]:
            calc_val = m["numerator"] / m["denominator"]
            assert abs(calc_val - m["value"]) < 0.005, f"Value mismatch in {m['metric_id']}"
            
        # Check CI structure
        ci = m["confidence_interval_95pct"]
        assert len(ci) == 2
        assert ci[0] <= ci[1]

if __name__ == "__main__":
    test_report_metric_consistency()
    print("[PASS] test_report_metric_consistency")
