"""
Phase 9 — Evidence Engine Validation

Tests the Evidence Engine against different data quality profiles.
Ensures it outputs HIGH, MODERATE, LOW, and INSUFFICIENT correctly based on data.
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

from core.event_engine import InteractionEvent
from core.evidence import EvidenceEngine

def build_mock_events(count: int, duration_frames: int):
    events = []
    for i in range(count):
        evt = InteractionEvent(f"EVT_{i}", 1, 99, 1, 0.0)
        for f in range(duration_frames):
            evt.update(f, f*0.1, 2.0, 1.0, "CAUTION")
        evt.end()
        events.append(evt)
    return events

def run_evidence_validation():
    passed = True
    errors = []
    
    # 1. Excellent Evidence
    # High event count, long durations, no tracking failures
    events_excellent = build_mock_events(20, 50)
    ev_excellent = EvidenceEngine.evaluate_segment_evidence(events_excellent, total_video_frames=1000, tracking_failures=10)
    
    if ev_excellent["evidence_level"] != "HIGH":
        passed = False
        errors.append(f"Expected HIGH, got {ev_excellent['evidence_level']}")
        
    # 2. Partial Evidence
    # Moderate event count, high tracking failures -> 0.4 penalty -> Confidence 0.6 (MODERATE)
    events_partial = build_mock_events(15, 10) 
    ev_partial = EvidenceEngine.evaluate_segment_evidence(events_partial, total_video_frames=1000, tracking_failures=300)
    
    if ev_partial["evidence_level"] != "MODERATE":
        passed = False
        errors.append(f"Expected MODERATE, got {ev_partial['evidence_level']} ({ev_partial['evidence_confidence']})")
        
    # 3. Poor Evidence
    # Few events, mostly short -> 0.3 penalty
    # high tracking failures -> 0.4 penalty
    # Total penalty 0.7 -> Confidence 0.3 (Wait, 0.4-0.6 is LOW. So I need a penalty of 0.5. How?
    # out_of_bounds_events penalty is 0.1 per event. Let's do 1 out of bounds event + 0.4 tracking failure = 0.5 penalty -> Conf 0.5 (LOW).
    events_poor = build_mock_events(3, 5)
    events_poor[0].min_distance_m = 20.0 # Trigger out of bounds
    ev_poor = EvidenceEngine.evaluate_segment_evidence(events_poor, total_video_frames=1000, tracking_failures=300)
    
    if ev_poor["evidence_level"] != "LOW":
        passed = False
        errors.append(f"Expected LOW, got {ev_poor['evidence_level']} ({ev_poor['evidence_confidence']})")
        
    # 4. Missing Critical Evidence
    # Almost no events (0 events -> 0.4 penalty)
    # Huge tracking failures -> 0.4 penalty
    # Total 0.8 penalty -> Conf 0.2 (INSUFFICIENT)
    events_missing = build_mock_events(0, 0)
    ev_missing = EvidenceEngine.evaluate_segment_evidence(events_missing, total_video_frames=1000, tracking_failures=800)
    
    if ev_missing["evidence_level"] != "INSUFFICIENT":
        passed = False
        errors.append(f"Expected INSUFFICIENT, got {ev_missing['evidence_level']}")
        
    report = {
        "evidence_validation_passed": passed,
        "errors": errors,
        "excellent_score": ev_excellent["evidence_confidence"],
        "partial_score": ev_partial["evidence_confidence"],
        "poor_score": ev_poor["evidence_confidence"],
        "missing_score": ev_missing["evidence_confidence"]
    }
    
    out_dir = ROOT / "validation" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "evidence_validation.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Evidence Validation Passed: {passed}")
    if not passed:
        print(errors)

if __name__ == "__main__":
    run_evidence_validation()
