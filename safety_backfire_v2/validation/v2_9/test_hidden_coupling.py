"""
V2.9 Red-Team Test: Hidden Coupling & Magic Numbers Catalog

Scans and verifies all hard-coded magic numbers, duplicate constants, 
and unvalidated thresholds across safety-critical decision paths.
"""
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))

MAGIC_NUMBERS = [
    {
        "constant": "0.35",
        "location": "core/track_manager.py:15",
        "purpose": "strong_conf_threshold distinguishing OBSERVED from PREDICTED",
        "impact_if_changed": "Raising to 0.5 drops real occluded persons; lowering to 0.2 admits false ghosts.",
        "validated": False
    },
    {
        "constant": "0.25 m/s",
        "location": "core/track_manager.py:153",
        "purpose": "Threshold separating MOVING from PARKED/STATIC entity",
        "impact_if_changed": "Affects whether forklift-person proximity is suppressed as parked interaction.",
        "validated": False
    },
    {
        "constant": "0.8 m/s",
        "location": "generate_v2_8_5_video.py:138",
        "purpose": "Operator speed heuristic (speed > 0.8 => operator on vehicle)",
        "impact_if_changed": "Pedestrians walking > 0.8 m/s falsely suppressed as operators.",
        "validated": False
    },
    {
        "constant": "8.0 m/s",
        "location": "core/track_manager.py:15",
        "purpose": "max_drift_speed_m_s for track teleportation detection",
        "impact_if_changed": "Jumps below 8 m/s (28.8 km/h) accepted as valid physical motion.",
        "validated": False
    },
    {
        "constant": "5 frames",
        "location": "core/track_manager.py:15",
        "purpose": "max_prediction_frames before track transitions from PREDICTED to STALE",
        "impact_if_changed": "Directly controls ghost track persistence duration (0.2s at 25 FPS).",
        "validated": False
    },
    {
        "constant": "15 frames",
        "location": "core/event_engine_v2.py:208",
        "purpose": "max_gap_frames before closing an active event",
        "impact_if_changed": "Occlusions > 0.6s fragment continuous safety events into separate events.",
        "validated": False
    },
    {
        "constant": "3.0 seconds",
        "location": "core/event_engine_v2.py:140",
        "purpose": "TTC threshold to promote UNKNOWN candidate to CONFIRMED_EVENT",
        "impact_if_changed": "Controls escalation sensitivity of ambiguous interactions.",
        "validated": False
    },
    {
        "constant": "1.0 - 4.5",
        "location": "core/observation_gate.py:44-45",
        "purpose": "Human aspect ratio bounds (height / width)",
        "impact_if_changed": "Aspect < 1.0 discards fallen/crouching workers as non-human.",
        "validated": False
    },
    {
        "constant": "1.5m / 3.0m",
        "location": "generate_v2_8_5_video.py:155-157",
        "purpose": "DANGER and CAUTION proximity zones",
        "impact_if_changed": "Arbitrary warehouse distance thresholds hardcoded directly into rendering script.",
        "validated": False
    }
]

def test_hidden_coupling():
    print("\n=== V2.9 Red-Team: Hidden Coupling & Magic Numbers Catalog ===")
    print(f"Total Safety-Critical Magic Numbers Identified: {len(MAGIC_NUMBERS)}")
    print("-----------------------------------------------------------------")
    for item in MAGIC_NUMBERS:
        print(f"Constant: {item['constant']:<12} | Location: {item['location']}")
        print(f"  Purpose:  {item['purpose']}")
        print(f"  Impact:   {item['impact_if_changed']}")
        print(f"  Validated: {item['validated']}")
        print("-----------------------------------------------------------------")
    
    # Check for hardcoded distance thresholds in video scripts instead of config
    scripts = ["generate_v2_8_2_video.py", "generate_v2_8_3_video.py", "generate_v2_8_4_video.py", "generate_v2_8_5_video.py"]
    hardcoded_zones = []
    for sc in scripts:
        p = ROOT / sc
        if p.exists():
            content = p.read_text()
            if "1.5" in content and "3.0" in content and "dist_m <= 1.5" in content:
                hardcoded_zones.append(sc)

    print(f"\nScripts with hardcoded zone boundaries (1.5m/3.0m) bypassing config:")
    for sc in hardcoded_zones:
        print(f"  * {sc}")

    return MAGIC_NUMBERS

if __name__ == "__main__":
    test_hidden_coupling()
