import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.output_schema import OutputManager

def test_output_manager():
    out_dir = ROOT / "tests/temp_outputs"
    manager = OutputManager(str(out_dir))
    
    manager.save_events([{"id": 1}])
    
    events_file = out_dir / "events.json"
    assert events_file.exists()
    
    with open(events_file, 'r') as f:
        data = json.load(f)
        
    assert "metadata" in data
    assert data["metadata"]["schema_version"] == "2.0"
    assert data["metadata"]["data_type"] == "InteractionEvents"
    assert data["data"][0]["id"] == 1
    
    # Cleanup
    events_file.unlink()
    out_dir.rmdir()
    
    print("OutputManager tests passed successfully!")

if __name__ == "__main__":
    test_output_manager()
