import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.geometry import compute_metric_distance, GroundPlaneCalibrator

def test_geometry_validation():
    calibrator = GroundPlaneCalibrator()
    
    # 1. Test Valid Points (within [140, 440] x [170, 350] roughly)
    p1_valid = (220.0, 200.0)
    p2_valid = (300.0, 200.0)
    
    res_valid = compute_metric_distance(p1_valid, p2_valid, calibrator)
    assert res_valid["calibration_status"] == "VALID"
    assert res_valid["distance_m"] is not None
    assert res_valid["calibration_confidence"] == 1.0
    
    # 2. Test Invalid Points (Extrapolation)
    p1_invalid = (10.0, 10.0)
    p2_invalid = (50.0, 50.0)
    
    res_invalid = compute_metric_distance(p1_invalid, p2_invalid, calibrator)
    assert res_invalid["calibration_status"] == "EXTRAPOLATED_OUT_OF_BOUNDS"
    assert res_invalid["distance_m"] is None
    assert res_invalid["calibration_confidence"] == 0.0
    
    # 3. Test Mixed
    res_mixed = compute_metric_distance(p1_valid, p2_invalid, calibrator)
    assert res_mixed["calibration_status"] == "EXTRAPOLATED_OUT_OF_BOUNDS"
    assert res_mixed["distance_m"] is None

    print("Geometry tests passed successfully!")

if __name__ == "__main__":
    test_geometry_validation()
