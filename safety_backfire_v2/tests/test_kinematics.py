import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.kinematics import calculate_world_velocity, compute_metric_ttc

def test_metric_ttc():
    # Object 1 (Person) at (1.0, 1.0) moving slightly
    p_pos = (1.0, 1.0)
    p_vel = (0.0, 0.0)
    
    # Object 2 (Forklift) at (4.0, 1.0) moving towards person at 1 m/s
    f_pos = (4.0, 1.0)
    f_vel = (-1.0, 0.0)
    
    dist_m = 3.0
    
    ttc_res = compute_metric_ttc(p_pos, f_pos, p_vel, f_vel, dist_m)
    
    assert ttc_res["ttc_status"] == "VALID"
    assert ttc_res["relative_velocity_m_s"] == 1.0
    assert ttc_res["ttc_sec"] == 3.0
    
    # Test diverging objects
    f_vel_div = (1.0, 0.0) # moving away
    ttc_res_div = compute_metric_ttc(p_pos, f_pos, p_vel, f_vel_div, dist_m)
    
    assert ttc_res_div["ttc_status"] == "NO_APPROACH"
    assert ttc_res_div["ttc_sec"] is None
    
    print("Kinematics TTC tests passed successfully!")

if __name__ == "__main__":
    test_metric_ttc()
