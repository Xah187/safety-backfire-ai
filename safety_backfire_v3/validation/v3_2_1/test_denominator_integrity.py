"""
test_denominator_integrity.py
Verifies that entity-frame instances (3450) and physical frames (1672) denominators
are properly separated and not confused in ID switch rates.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_denominator_integrity():
    reg_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/canonical_metric_registry.json"
    assert reg_file.exists(), "canonical_metric_registry.json missing"
    
    with open(reg_file) as f:
        registry = json.load(f)
        
    metrics = {m["metric_id"]: m for m in registry["metrics"]}
    
    # 1. Check ID switch rate per instances
    m_inst = metrics["IDENTITY_SWITCH_RATE_INSTANCES"]
    assert m_inst["numerator"] == 7
    assert m_inst["denominator"] == 3450
    assert abs(m_inst["value"] - 2.03) < 0.01
    assert "entity_frame_instances" in m_inst["unit"]
    
    # 2. Check ID switch rate per frames
    m_frame = metrics["IDENTITY_SWITCH_RATE_FRAMES"]
    assert m_frame["numerator"] == 7
    assert m_frame["denominator"] == 1672
    assert abs(m_frame["value"] - 4.19) < 0.01
    assert "physical_frames" in m_frame["unit"]

if __name__ == "__main__":
    test_denominator_integrity()
    print("[PASS] test_denominator_integrity")
