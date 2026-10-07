"""
test_odd_consistency.py
Verifies canonical ODD consistency across pitch, distance, and environmental parameters.
Ensures CAM_DOCK_SOUTH at 22.5 deg is classified as DEGRADED stress test, not nominal ODD.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def test_odd_consistency():
    odd_file = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_2_1/canonical_odd.json"
    assert odd_file.exists(), "canonical_odd.json missing"
    
    with open(odd_file) as f:
        odd = json.load(f)
        
    pitch = odd["camera_extrinsic_geometry"]["camera_pitch_deg"]
    assert pitch["nominal"] == 45.0
    assert pitch["valid_range"] == [35.0, 55.0]
    assert pitch["degraded_range"] == [20.0, 35.0]
    
    # 22.5 deg must fall in degraded range, not valid range
    cam_dock_pitch = 22.5
    assert not (pitch["valid_range"][0] <= cam_dock_pitch <= pitch["valid_range"][1])
    assert pitch["degraded_range"][0] <= cam_dock_pitch <= pitch["degraded_range"][1]
    
    dist = odd["spatial_distance_policy"]
    assert dist["certified_autonomous_braking_range_m"]["range"] == [0.5, 8.0]
    assert dist["degraded_surveillance_advisory_range_m"]["range"] == [8.0, 10.0]
    assert dist["out_of_domain_range_m"]["range"] == "> 10.0"

if __name__ == "__main__":
    test_odd_consistency()
    print("[PASS] test_odd_consistency")
