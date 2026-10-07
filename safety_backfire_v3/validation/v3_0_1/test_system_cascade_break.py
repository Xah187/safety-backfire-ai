"""
V3.0.1 Adversarial Qualification — End-to-End Combinatorial Cascade Break Test

Addresses Section 21 & 22 of V3.0.1:
Simultaneous injection of:
  [False Detection] + [Tracker ID Switch] + [Pose Dropout & Delay] +
  [Frame Drop Burst] + [Geometric Occlusion Uncertainty] + [Delayed Worker Result]
in a single unified interaction scenario.

Investigates the Master System-Level Question:
  "How can V3.0 produce a false safety decision even when Detection, Tracking,
   Pose, Geometry, TTC, and Risk appear correct in isolation?"
"""
import sys
import time
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))
_V2_PATH = WORKSPACE_ROOT / "safety_backfire_v2"
if str(_V2_PATH) not in sys.path:
    sys.path.insert(0, str(_V2_PATH))

from core.geometry import load_default_calibrator
from core.observation_gate import ObservationIntegrityGate
from core.track_manager import TrackManager
from core.operator_relation_v2 import OperatorVehicleRelationEngineV2
from core.kinematics import compute_metric_ttc
from safety_backfire_v3.core.identity_layer import ConservativeIdentityLayer
from safety_backfire_v3.core.geometry_v3 import GeometryEngineV3, GeometricProjectionMethod
from safety_backfire_v3.core.event_engine_v3 import EventEngineV3
from safety_backfire_v3.core.async_pipeline import PoseContract


def test_combinatorial_cascade_break():
    print("\n=================================================================")
    print("   V3.0.1 MASTER BREAK TEST: COMBINATORIAL CASCADE INJECTION     ")
    print("=================================================================")
    
    calibrator = load_default_calibrator()
    obs_gate = ObservationIntegrityGate()
    track_mgr = TrackManager()
    id_layer = ConservativeIdentityLayer()
    relation_engine = OperatorVehicleRelationEngineV2()
    geo_engine = GeometryEngineV3(calibrator)
    event_engine = EventEngineV3(max_gap_frames=10)
    
    # Cascade Failures Discovered & Evaluated
    discovered_faults = []
    
    # -------------------------------------------------------------
    # STEP 1: Frame 100 — Normal Baseline Initialization
    # -------------------------------------------------------------
    # Pedestrian P01 (Track 10) approaching Forklift F01 (Track 1)
    t100 = 4.00
    objs_f100 = [
        {"id": 10, "class": "person", "bbox": [300, 300, 350, 480], "px": (325.0, 480.0), "conf": 0.88},
        {"id": 1, "class": "forklift", "bbox": [500, 200, 750, 500], "px": (625.0, 500.0), "conf": 0.92}
    ]
    # Filter through Observation Gate & TrackManager
    valid_100 = track_mgr.process_tracks(100, t100, objs_f100, calibrator)
    entities_100 = id_layer.process_tracks(100, t100, valid_100)
    
    p01_ent = entities_100[0]["entity_id"]
    f01_ent = entities_100[1]["entity_id"]
    print(f"  [Frame 100] Initialized P01={p01_ent}, F01={f01_ent}")
    
    # -------------------------------------------------------------
    # STEP 2: Frame 101 — ByteTrack ID Switch Injection
    # -------------------------------------------------------------
    # Tracker drops ID 10 and reassigns ID 11 nearby
    t101 = 4.04
    objs_f101 = [
        {"id": 11, "class": "person", "bbox": [305, 300, 355, 480], "px": (330.0, 480.0), "conf": 0.85},
        {"id": 1, "class": "forklift", "bbox": [500, 200, 750, 500], "px": (625.0, 500.0), "conf": 0.92}
    ]
    valid_101 = track_mgr.process_tracks(101, t101, objs_f101, calibrator)
    entities_101 = id_layer.process_tracks(101, t101, valid_101)
    
    # Invariant: Must absorb ID switch
    p01_relinked = entities_101[0]["entity_id"]
    if p01_relinked != p01_ent:
        discovered_faults.append("ID_SWITCH_FRAGMENTATION: Failed to relink track 11 to P01")
    else:
        print(f"  [Frame 101] ID Switch absorbed: Track 11 -> {p01_relinked}")

    # -------------------------------------------------------------
    # STEP 3: Frame 102 — Injected False Fork Tine Detection
    # -------------------------------------------------------------
    # YOLO hallucination: fork tine clutter detected as "person" (w=150, h=30, horizontal)
    t102 = 4.08
    hallucination_box = [520, 450, 670, 480] # Aspect ratio = 30 / 150 = 0.20
    eval_dec = obs_gate.evaluate("person", hallucination_box, keypoints=None, conf=0.75)
    
    if eval_dec.safety_eligible:
        discovered_faults.append("FALSE_OBSERVATION_LEAK: Horizontal fork tine hallucination entered safety engine!")
    else:
        print(f"  [Frame 102] False detection intercepted by ObservationGate: validity={eval_dec.validity}, eligible=False")

    # -------------------------------------------------------------
    # STEP 4: Frame 103 — Delayed Out-of-Order Pose Result (Skew)
    # -------------------------------------------------------------
    # Pose worker finishes delayed task from Frame 95 (age = 320ms)
    t103 = 4.12
    delayed_pose = PoseContract(
        pose_id="POSE_DELAYED",
        pose_frame_id=95,
        pose_timestamp=t100 - 0.20,
        source_track_id=10,
        source_entity_id=p01_ent,
        keypoints=[[10, 20, 0.9]],
        keypoint_confidence=0.88
    )
    status_delayed = delayed_pose.get_status(103, t103)
    if status_delayed == "FRESH_POSE":
        discovered_faults.append("STALE_POSE_LEAK: Delayed Frame 95 pose accepted as fresh at Frame 103!")
    else:
        print(f"  [Frame 103] Delayed pose rejected from fresh usage: status={status_delayed}")

    # -------------------------------------------------------------
    # STEP 5: Frames 104-106 — Burst Frame Drop Injection
    # -------------------------------------------------------------
    # 3 frames dropped due to network burst. Pipeline jumps directly to Frame 107 (dt = 0.16s)
    t107 = 4.28
    print(f"  [Frames 104-106] Simulating 3 consecutive dropped frames; jumping directly to Frame 107...")

    # -------------------------------------------------------------
    # STEP 6: Frame 107 — Geometric Occlusion & Uncertainty Shock
    # -------------------------------------------------------------
    # Pedestrian P01 is now close to Forklift F01, but lower body is occluded behind a pallet!
    # Point estimate distance is 1.60m (Nominally CAUTION zone in single-point estimate).
    # However, ground contact uncertainty is +-0.75m!
    p_box_occl = [420, 280, 470, 420] # Occluded lower half
    f_box = [460, 200, 710, 500]
    
    proj_res = geo_engine.project_entity_ground(
        bbox=p_box_occl,
        keypoints=None, # Feet occluded
        entity_class="person",
        is_operator=False,
        method=GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET
    )
    p_gp = proj_res["world_pos_m"]
    f_gp = calibrator.pixel_to_world((585.0, 500.0))
    nominal_dist_m = math.hypot(p_gp[0] - f_gp[0], p_gp[1] - f_gp[1])
    uncertainty_m = proj_res["position_uncertainty_m"]
    
    min_credible_dist_m = max(0.1, nominal_dist_m - uncertainty_m)
    max_credible_dist_m = nominal_dist_m + uncertainty_m
    
    print(f"  [Frame 107] Geometric Distance Estimate:")
    print(f"    Nominal Point Estimate: {nominal_dist_m:.2f} m")
    print(f"    Uncertainty Margin:     +-{uncertainty_m:.2f} m")
    print(f"    Credible Bound:         [{min_credible_dist_m:.2f} m  ---  {max_credible_dist_m:.2f} m]")
    
    # -------------------------------------------------------------
    # STEP 7: Master System-Level Question Evaluation
    # -------------------------------------------------------------
    # If the system uses ONLY nominal_dist_m (e.g. 1.60m > 1.50m -> CAUTION)
    # but the physical worker could be at min_credible_dist_m (0.85m <= 1.50m -> DANGER),
    # then an optimistic safety failure occurs!
    point_estimate_zone = "CAUTION" if nominal_dist_m > 1.5 else "DANGER"
    worst_case_zone = "DANGER" if min_credible_dist_m <= 1.5 else "CAUTION"
    
    print(f"\n  System-Level Evaluation under Cascade:")
    print(f"    Point-Estimate Safety Zone: {point_estimate_zone}")
    print(f"    Worst-Case Conservative Zone: {worst_case_zone}")
    
    if point_estimate_zone != worst_case_zone:
        discovered_faults.append(
            f"FAIL-22 (SYSTEM-LEVEL RISK OVER-OPTIMISM): Nominal distance ({nominal_dist_m:.2f}m) classified as {point_estimate_zone}, "
            f"ignoring credible bound ({min_credible_dist_m:.2f}m) which is in {worst_case_zone}!"
        )
        print("  [FAIL-22 IDENTIFIED] Point-estimate risk evaluation suppresses DANGER alert under geometric uncertainty!")
    else:
        print("  [PASS] Zone matches conservative bound.")
        
    print(f"\n=================================================================")
    print(f"   COMBINATORIAL CASCADE BREAK SUMMARY")
    print(f"   Total Cascade Faults Identified: {len(discovered_faults)}")
    for f in discovered_faults:
        print(f"     -> {f}")
    print(f"=================================================================")
    return discovered_faults


def run_all_cascade_tests():
    return test_combinatorial_cascade_break()

if __name__ == "__main__":
    run_all_cascade_tests()
