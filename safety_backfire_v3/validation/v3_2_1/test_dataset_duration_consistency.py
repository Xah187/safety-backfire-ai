"""
test_dataset_duration_consistency.py
Verifies that dataset duration numbers are mathematically consistent and that unsupported
2.5-hour claims are rejected in favor of empirical durations.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_dataset_duration_consistency():
    audit_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/dataset_duration_audit.json"
    assert audit_file.exists(), "dataset_duration_audit.json missing"
    
    with open(audit_file) as f:
        data = json.load(f)
        
    raw = data["physical_raw_video_on_disk"]
    assert raw["total_physical_frames"] == 1672
    assert abs(raw["total_physical_sec"] - 64.05) < 0.1
    
    corpus = data["annotated_validation_corpus"]
    assert corpus["total_duration_sec"] == 1380.0
    assert corpus["total_duration_min"] == 23.0
    assert abs(corpus["total_duration_hours"] - (23.0 / 60.0)) < 0.001
    assert corpus["blind_test_duration_min"] == 11.0
    assert abs(corpus["blind_test_duration_hours"] - (11.0 / 60.0)) < 0.001

if __name__ == "__main__":
    test_dataset_duration_consistency()
    print("[PASS] test_dataset_duration_consistency")
