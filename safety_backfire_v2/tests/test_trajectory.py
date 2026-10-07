import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.trajectory import TrajectoryEngine

def test_trajectory_engine():
    engine = TrajectoryEngine()
    
    # Simulate a person walking in a straight line
    engine.update(1, "person", 0.0, 0.0, 0.0, "SAFE")
    engine.update(1, "person", 0.1, 0.1, 0.0, "SAFE")
    engine.update(1, "person", 0.2, 0.2, 0.0, "CAUTION")
    engine.update(1, "person", 0.3, 0.3, 0.0, "CAUTION")
    engine.update(1, "person", 0.4, 0.4, 0.0, "DANGER")
    
    traj = engine.get_trajectory(1)
    metrics = traj.get_metrics()
    
    # Assertions
    assert metrics["points_count"] == 5
    assert metrics["zone_transitions"] == 2 # SAFE->CAUTION, CAUTION->DANGER
    assert metrics["trajectory_length_m"] == 0.4
    assert metrics["displacement_m"] == 0.4
    assert metrics["average_velocity_m_s"] == 1.0 # 0.1m / 0.1s
    
    print("Trajectory tests passed successfully!")

if __name__ == "__main__":
    test_trajectory_engine()
