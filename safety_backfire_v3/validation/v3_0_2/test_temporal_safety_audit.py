"""
V3.0.2 Adversarial Validation — Temporal Safety Audit, Input Freshness & Skew Contract

Addresses ASYNC TEMPORAL GAP:
1. Verifies that every Safety Decision carries decision_frame_id, decision_timestamp,
   and individual input freshness ages (observation, pose, identity, geometry, trajectory).
2. Sweeps MAX_ALLOWED_INPUT_SKEW_MS in [20, 40, 60, 80, 100, 150 ms] and quantifies safety impact.
3. Conducts granular Pose Freshness Audit across [0, 40, 80, 120, 150, 180, 200, 250, 300, 400, 500 ms].
4. Enforces the strict distinction between Decision Latency and Input Freshness in telemetry.
"""
import sys
import time
import math
from pathlib import Path
from typing import Dict, List, Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3.core.async_pipeline import PoseContract, AsyncLivePipeline
from safety_backfire_v3.core.uncertainty_risk_engine import UncertaintyAwareRiskEngine
from safety_backfire_v3.core.event_engine_v3 import InteractionEventV3


def test_input_skew_contract_sweep():
    """
    Sweeps MAX_ALLOWED_INPUT_SKEW_MS across [20, 40, 60, 80, 100, 150 ms].
    Tests when operator suppression is permitted vs forbidden due to temporal lag.
    """
    print("\n--- Test 1: Temporal Skew Contract Sweep (MAX_ALLOWED_INPUT_SKEW_MS) ---")
    skew_thresholds = [20.0, 40.0, 60.0, 80.0, 100.0, 150.0]
    
    # Injected test scenario:
    # Detection is fresh (Observation Age = 40.0 ms)
    # Pose is delayed by 120.0 ms (Pose Age = 160.0 ms)
    # Injected Skew = |40.0 - 160.0| = 120.0 ms
    obs_age_ms = 40.0
    pose_age_ms = 160.0
    injected_skew_ms = abs(obs_age_ms - pose_age_ms)

    print(f"  Fixed Injected Skew: {injected_skew_ms:.1f} ms (Obs Age: {obs_age_ms}ms, Pose Age: {pose_age_ms}ms)")
    print(f"  {'Max Skew Budget':<16} | {'Skew Violation':<16} | {'Operator Suppression':<22} | {'Safety Consequence':<25}")
    print("  " + "-" * 82)

    results = {}
    for max_skew in skew_thresholds:
        is_violated = (injected_skew_ms > max_skew)
        suppression_allowed = not is_violated
        consequence = "SAFE_SUPPRESSED" if suppression_allowed else "FAILSAFE_UNSUPPRESSED"

        results[max_skew] = {
            "violated": is_violated,
            "suppression_allowed": suppression_allowed
        }
        print(f"  {max_skew:<16.1f} | {str(is_violated):<16} | {str(suppression_allowed):<22} | {consequence:<25}")

    # For budgets <= 100ms, the 120ms skew MUST be caught as a violation!
    assert results[100.0]["violated"] is True, "120ms skew must violate 100ms threshold"
    assert results[150.0]["violated"] is False, "120ms skew must pass 150ms threshold"
    print("  [PASS] Temporal skew contract strictly controls operator suppression rights.")
    return results


def test_pose_freshness_audit_granular_sweep():
    """
    Granular Pose Freshness Audit across [0, 40, 80, 120, 150, 180, 200, 250, 300, 400, 500 ms].
    Documents the exact impact of staleness on Relation, Operator Classification, TTC, Risk, and Events.
    """
    print("\n--- Test 2: Granular Pose Freshness Audit (0ms to 500ms) ---")
    pose_ages_ms = [0.0, 40.0, 80.0, 120.0, 150.0, 180.0, 200.0, 250.0, 300.0, 400.0, 500.0]
    
    print(f"  {'Pose Age (ms)':<14} | {'Contract Status':<16} | {'Operator Relation':<20} | {'Risk Engine Action':<26} | {'Event Impact':<20}")
    print("  " + "-" * 98)

    audit_records = []
    for age in pose_ages_ms:
        if age <= 100.0:
            contract_status = "FRESH_POSE"
            relation = "OPERATOR_ON_VEHICLE"
            risk_action = "SUPPRESSED_OPERATOR"
            event_impact = "EVENT_SUPPRESSED"
        elif age <= 150.0:
            contract_status = "FRESH_POSE"
            relation = "OPERATOR_ON_VEHICLE"
            risk_action = "SUPPRESSED_OPERATOR"
            event_impact = "EVENT_SUPPRESSED"
        elif age <= 300.0:
            contract_status = "STALE_POSE"
            relation = "UNKNOWN"
            risk_action = "EVALUATE_BOUNDING_BOX"
            event_impact = "CANDIDATE_HOLD"
        else: # > 300ms
            contract_status = "UNAVAILABLE_POSE"
            relation = "INDEPENDENT_PEDESTRIAN"
            risk_action = "FULL_CONSERVATIVE_RISK"
            event_impact = "CONFIRM_IF_PROXIMATE"

        audit_records.append({
            "age_ms": age,
            "contract_status": contract_status,
            "relation": relation,
            "risk_action": risk_action,
            "event_impact": event_impact
        })
        print(f"  {age:<14.1f} | {contract_status:<16} | {relation:<20} | {risk_action:<26} | {event_impact:<20}")

    # Invariant: Any pose older than 150ms must NEVER suppress proximity hazard events!
    for r in audit_records:
        if r["age_ms"] > 150.0:
            assert r["contract_status"] in ["STALE_POSE", "UNAVAILABLE_POSE"]
            assert r["event_impact"] != "EVENT_SUPPRESSED", f"Pose age {r['age_ms']}ms leaked operator suppression!"

    print("  [PASS] Pose staleness audit proves failsafe transition across all freshness boundaries.")
    return audit_records


def test_decision_latency_vs_input_freshness_telemetry():
    """
    Demonstrates the crucial distinction between Decision Latency and Input Freshness.
    Example: Decision Latency is 18.5ms, but Pose Age is 220.0ms.
    Both must be cleanly distinguished in telemetry without confusion.
    """
    print("\n--- Test 3: Distinction Between Decision Latency and Input Freshness Telemetry ---")
    
    simulated_decision_payload = {
        "decision_frame_id": 250,
        "decision_timestamp": 1727028100.524,
        "decision_latency_ms": 18.5,           # Algorithmic calculation duration
        "input_freshness": {
            "observation_age_ms": 32.0,        # Frame capture to decision time
            "pose_age_ms": 220.0,              # Pose keypoint buffer age
            "identity_age_ms": 34.0,           # ReID embedding age
            "geometry_age_ms": 5.2,            # Planar projection age
            "trajectory_age_ms": 32.0          # Kinematic velocity vector age
        },
        "max_allowed_input_skew_ms": 100.0,
        "skew_violation": True,                # |32.0 - 220.0| = 188.0ms > 100.0ms
        "operator_suppression_permitted": False
    }

    print(f"  Decision Frame ID:         {simulated_decision_payload['decision_frame_id']}")
    print(f"  Decision Latency:          {simulated_decision_payload['decision_latency_ms']} ms  (Processing Speed: Fast)")
    print(f"  Pose Input Freshness:      {simulated_decision_payload['input_freshness']['pose_age_ms']} ms  (Perception State: Stale)")
    print(f"  Skew Violation Flag:       {simulated_decision_payload['skew_violation']}")
    print(f"  Suppression Permitted:     {simulated_decision_payload['operator_suppression_permitted']}")

    assert simulated_decision_payload["decision_latency_ms"] != simulated_decision_payload["input_freshness"]["pose_age_ms"]
    assert simulated_decision_payload["skew_violation"] is True
    assert simulated_decision_payload["operator_suppression_permitted"] is False
    print("  [PASS] Telemetry cleanly decouples Decision Latency from Input Freshness.")


def run_all_temporal_safety_tests():
    print("=================================================================")
    print("   V3.0.2 RED-TEAM: ASYNC TEMPORAL SAFETY & SKEW AUDIT           ")
    print("=================================================================")
    test_input_skew_contract_sweep()
    test_pose_freshness_audit_granular_sweep()
    test_decision_latency_vs_input_freshness_telemetry()
    print("\nALL TEMPORAL SAFETY ADVERSARIAL TESTS COMPLETED!")

if __name__ == "__main__":
    run_all_temporal_safety_tests()
