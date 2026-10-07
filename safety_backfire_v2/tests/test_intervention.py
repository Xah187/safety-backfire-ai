import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.intervention import Intervention, InterventionExperiment

def test_intervention():
    intervention = Intervention("INT_01", "PHYSICAL_BARRIER", "DANGER", "Added a guardrail")
    
    experiment = InterventionExperiment("EXP_01", intervention, [{"id": 1}], [{"id": 2}, {"id": 3}])
    
    meta = experiment.get_metadata()
    assert meta["experiment_id"] == "EXP_01"
    assert meta["intervention"]["type"] == "PHYSICAL_BARRIER"
    assert meta["data_summary"]["before_events_count"] == 1
    assert meta["data_summary"]["after_events_count"] == 2
    
    print("Intervention tests passed successfully!")

if __name__ == "__main__":
    test_intervention()
