"""
run_synthetic_verification.py
Milestone V3.4-H — Synthetic Scenario Generator, State Machine Runner & Invariant Verifier

GOVERNANCE INVARIANTS:
  - Prototype / Sandbox execution only.
  - Model H parameters frozen invariant: k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22.
  - Evaluates SYNTHETIC_LOGIC_VERIFICATION, not real-world dataset ground truth.
"""

import sys
import json
import copy
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts/v3_4_h_sandbox"))

from backfire_state_machine import BackfireStateMachine

OUTPUT_DIR = WORKSPACE_ROOT / "outputs/v3_4_h"


def build_synthetic_scenarios():
    scenarios = [
        # H01: Safe Complete Stop (026_010 analog)
        {
            "event_id": "CASE_H01_SAFE_COMPLETE_STOP",
            "scenario_type": "SAFE_COMPLETE_STOP",
            "description": "Forklift approaches pedestrian at 115px; executes emergency brake to a dead stop (disp 2.5px); zero secondary risk transfer.",
            "primary_interaction": {
                "actor_vehicle_id": "FK_136",
                "actor_pedestrian_id": "PED_148",
                "minimum_separation_px": 115.1,
                "co_occurring_frames": 59,
                "interaction_duration_s": 2.43
            },
            "intervention_signal": {
                "intervention_detected": True,
                "intervention_type": "EMERGENCY_BRAKING",
                "evidence_status": "OBSERVED",
                "timestamp_start_s": 8.03,
                "timestamp_end_s": 10.43
            },
            "telemetry": {
                "brake_applied": True,
                "longitudinal_decel_mps2": 3.8,
                "stop_confirmed": True
            },
            "primary_mitigation": {
                "collision_averted": True,
                "primary_risk_change": "ELIMINATED",
                "evidence_status": "OBSERVED"
            },
            "risk_redirection": {
                "redirection_observed": False,
                "lateral_swerve_m": 0.0
            },
            "secondary_zone": {
                "zone_id": "Wh026_Camera_0002_ADJACENT_RACK",
                "zone_definition_type": "ADJACENT_RACK_AISLE",
                "entry_observable": True,
                "interior_depth_observable": False
            },
            "secondary_risk_pre": {
                "risk_score": 0.10,
                "occupancy_count": 2,
                "evidence_status": "OBSERVED"
            },
            "secondary_risk_post": {
                "risk_score": 0.10,
                "occupancy_count": 2,
                "evidence_status": "OBSERVED"
            },
            "delta_secondary_risk": {
                "delta_value": 0.00,
                "risk_increased": False,
                "evidence_status": "OBSERVED"
            },
            "observability": {
                "primary_zone_status": "FULL",
                "secondary_zone_status": "PARTIAL",
                "secondary_entry_observable": True,
                "secondary_depth_observable": False,
                "post_window_status": "ADEQUATE"
            },
            "temporal_order": {
                "chronological_stages_valid": True
            },
            "causal_link": {
                "causal_chain_status": "UNSUPPORTED",
                "observable_causal_path": "FALSE",
                "latency_to_secondary_onset_s": None
            },
            "confounders": {
                "confounders_present": "NO",
                "causal_isolation_status": "ISOLATED"
            },
            "expected_class": "PRIMARY_NEAR_MISS",
            "oracle_reason": "Vehicle stopped completely without lateral redirection; delta secondary risk is exactly zero."
        },

        # H02: True Synthetic Backfire (Prototypical Backfire)
        {
            "event_id": "CASE_H02_TRUE_SYNTHETIC_BACKFIRE",
            "scenario_type": "PROTOTYPICAL_BACKFIRE_CASCADE",
            "description": "Forklift swerves away from worker in lane into occupied secondary cross-aisle; secondary hazard increases sharply.",
            "primary_interaction": {
                "actor_vehicle_id": "FK_201",
                "actor_pedestrian_id": "PED_202",
                "minimum_separation_px": 180.0,
                "co_occurring_frames": 120,
                "interaction_duration_s": 4.0
            },
            "intervention_signal": {
                "intervention_detected": True,
                "intervention_type": "SWERVE_AVOIDANCE",
                "evidence_status": "OBSERVED",
                "timestamp_start_s": 5.0,
                "timestamp_end_s": 7.0
            },
            "telemetry": {
                "brake_applied": True,
                "steering_angle_deg": 28.5,
                "yaw_rate_deg_s": 14.2
            },
            "primary_mitigation": {
                "collision_averted": True,
                "primary_risk_change": "ELIMINATED",
                "evidence_status": "OBSERVED"
            },
            "risk_redirection": {
                "redirection_observed": True,
                "lateral_swerve_m": 2.4
            },
            "secondary_zone": {
                "zone_id": "Wh027_CROSS_AISLE_B",
                "zone_definition_type": "CALIBRATED_POLYGON",
                "entry_observable": True,
                "interior_depth_observable": True
            },
            "secondary_risk_pre": {
                "risk_score": 0.05,
                "occupancy_count": 1,
                "evidence_status": "OBSERVED"
            },
            "secondary_risk_post": {
                "risk_score": 0.75,
                "occupancy_count": 1,
                "evidence_status": "OBSERVED"
            },
            "delta_secondary_risk": {
                "delta_value": 0.70,
                "risk_increased": True,
                "evidence_status": "OBSERVED"
            },
            "observability": {
                "primary_zone_status": "FULL",
                "secondary_zone_status": "FULL",
                "secondary_entry_observable": True,
                "secondary_depth_observable": True,
                "post_window_status": "ADEQUATE"
            },
            "temporal_order": {
                "chronological_stages_valid": True
            },
            "causal_link": {
                "causal_chain_status": "DIRECTLY_OBSERVED",
                "observable_causal_path": "TRUE",
                "latency_to_secondary_onset_s": 1.1
            },
            "confounders": {
                "confounders_present": "NO",
                "causal_isolation_status": "ISOLATED"
            },
            "expected_class": "BACKFIRE_CANDIDATE",
            "oracle_reason": "Verified unbroken physical chain: avoidance swerve redirected vehicle into fully observable secondary zone where hazard increased."
        },

        # H03: Occluded Secondary Zone
        {
            "event_id": "CASE_H03_OCCLUDED_SECONDARY",
            "scenario_type": "OBSERVABILITY_BOTTLENECK",
            "description": "Evasive maneuver toward rack aisle; aisle depth completely occluded by stacked cargo.",
            "primary_interaction": { "minimum_separation_px": 150.0, "co_occurring_frames": 90 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "SWERVE_AVOIDANCE", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "RACK_AISLE_C", "zone_definition_type": "ADJACENT_RACK_AISLE", "entry_observable": True, "interior_depth_observable": False },
            "secondary_risk_pre": { "risk_score": 0.10, "evidence_status": "PARTIAL" },
            "secondary_risk_post": { "risk_score": 0.60, "evidence_status": "UNAVAILABLE" },
            "delta_secondary_risk": { "delta_value": 0.50, "risk_increased": True, "evidence_status": "UNAVAILABLE" },
            "observability": {
                "primary_zone_status": "FULL",
                "secondary_zone_status": "PARTIAL",
                "secondary_entry_observable": True,
                "secondary_depth_observable": False,
                "post_window_status": "ADEQUATE"
            },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "PARTIALLY_OBSERVED", "observable_causal_path": "TRUE", "latency_to_secondary_onset_s": 1.0 },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Secondary zone interior depth is unobservable; cannot verify whether hazard actually materialized."
        },

        # H04: New Forklift Confounder (027_003 analog)
        {
            "event_id": "CASE_H04_NEW_FORKLIFT_CONFOUNDER",
            "scenario_type": "CONFOUNDER_TURNOVER",
            "description": "Primary vehicle leaves frame; an entirely new forklift arrives in POST and causes secondary hazard.",
            "primary_interaction": { "minimum_separation_px": 230.0, "co_occurring_frames": 140 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "PEDESTRIAN_YIELD", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "SEC_ZONE_D", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.05, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.70, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.65, "risk_increased": True, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": 1.5 },
            "confounders": {
                "confounders_present": "YES",
                "confounder_types": ["NEW_FORKLIFT", "TRACK_HANDOFF"],
                "causal_isolation_status": "FAILED"
            },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Arrival of independent second forklift competitively explains secondary hazard; causal isolation failed."
        },

        # H05: Independent Worker Cluster (027_001 analog)
        {
            "event_id": "CASE_H05_INDEPENDENT_WORKER_CLUSTER",
            "scenario_type": "CONFOUNDER_PEDESTRIAN_CROWD",
            "description": "Shift change crowd enters adjacent aisle independently of vehicle avoidance.",
            "primary_interaction": { "minimum_separation_px": 240.0, "co_occurring_frames": 150 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "EMERGENCY_BRAKING", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": False },
            "secondary_zone": { "zone_id": "SEC_ZONE_E", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.05, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.60, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.55, "risk_increased": True, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": 1.2 },
            "confounders": {
                "confounders_present": "YES",
                "confounder_types": ["INDEPENDENT_WORKER_CLUSTER"],
                "causal_isolation_status": "FAILED"
            },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Independent pedestrian cluster explains secondary density; lack of physical redirection link."
        },

        # H06: Positive Delta but No Temporal Link (Latency > tau_max)
        {
            "event_id": "CASE_H06_POSITIVE_DELTA_LATENCY_VIOLATION",
            "scenario_type": "TEMPORAL_LATENCY_VIOLATION",
            "description": "Secondary hazard manifests 5.5 seconds after intervention (exceeds tau_max = 2.0s).",
            "primary_interaction": { "minimum_separation_px": 170.0, "co_occurring_frames": 110 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "SWERVE_AVOIDANCE", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "SEC_ZONE_F", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.05, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.50, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.45, "risk_increased": True, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "PARTIALLY_OBSERVED", "observable_causal_path": "TRUE", "latency_to_secondary_onset_s": 5.5 },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Propagation latency (5.5s) exceeds maximum causal threshold (2.0s); anti-retroactive attribution rule triggers."
        },

        # H07: Temporal Link but No Physical Path
        {
            "event_id": "CASE_H07_TEMPORAL_LINK_DISCONNECTED_PATH",
            "scenario_type": "DISCONNECTED_PHYSICAL_TRAJECTORY",
            "description": "Secondary risk starts quickly (<2s), but occurs across physical concrete barrier with no connected trajectory.",
            "primary_interaction": { "minimum_separation_px": 160.0, "co_occurring_frames": 100 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "EMERGENCY_BRAKING", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": False },
            "secondary_zone": { "zone_id": "SEC_ZONE_G", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.10, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.60, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.50, "risk_increased": True, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": 0.8 },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Lack of continuous physical path connecting vehicle intervention to secondary exposure."
        },

        # H08: Secondary Delta Zero (Delta_R_sec = 0)
        {
            "event_id": "CASE_H08_SECONDARY_DELTA_ZERO",
            "scenario_type": "ZERO_DELTA_NEAR_MISS",
            "description": "Intervention mitigates primary hazard; secondary risk remains identical before and after.",
            "primary_interaction": { "minimum_separation_px": 190.0, "co_occurring_frames": 105 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "COMBINED_MANEUVER", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": False },
            "secondary_zone": { "zone_id": "SEC_ZONE_H", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.20, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.20, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.00, "risk_increased": False, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": None },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "PRIMARY_NEAR_MISS",
            "oracle_reason": "Delta secondary risk is zero; intervention resolved primary conflict without hazard propagation."
        },

        # H09: Secondary Delta Negative (Delta_R_sec < 0)
        {
            "event_id": "CASE_H09_SECONDARY_DELTA_NEGATIVE",
            "scenario_type": "NEGATIVE_DELTA_NEAR_MISS",
            "description": "Secondary zone clears out during post-window, reducing background risk.",
            "primary_interaction": { "minimum_separation_px": 210.0, "co_occurring_frames": 95 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "EMERGENCY_BRAKING", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": False },
            "secondary_zone": { "zone_id": "SEC_ZONE_I", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.50, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.10, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": -0.40, "risk_increased": False, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": None },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "PRIMARY_NEAR_MISS",
            "oracle_reason": "Secondary risk decreased (Delta_R_sec = -0.40 < 0); gate 3 fails, routing to PRIMARY_NEAR_MISS."
        },

        # H10: Intervention Not Confirmed
        {
            "event_id": "CASE_H10_INTERVENTION_NOT_CONFIRMED",
            "scenario_type": "UNCONFIRMED_INTERVENTION",
            "description": "Close approach in primary corridor, but vehicle maintained constant velocity with no braking or steering action.",
            "primary_interaction": { "minimum_separation_px": 140.0, "co_occurring_frames": 80 },
            "intervention_signal": { "intervention_detected": False, "intervention_type": "NONE", "evidence_status": "NOT_OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": False },
            "secondary_zone": { "zone_id": "SEC_ZONE_J", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.10, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.10, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.00, "risk_increased": False, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": None },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "PRIMARY_NEAR_MISS",
            "oracle_reason": "No safety intervention was confirmed; event remains a primary near miss."
        },

        # H11: Secondary Zone Unknown (HEVT analog)
        {
            "event_id": "CASE_H11_SECONDARY_ZONE_UNKNOWN",
            "scenario_type": "UNDEFINED_SECONDARY_GEOMETRY",
            "description": "Secondary zone geometry is undefined/UNKNOWN in environment calibration.",
            "primary_interaction": { "minimum_separation_px": 200.0, "co_occurring_frames": 100 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "PEDESTRIAN_YIELD", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "UNKNOWN", "zone_definition_type": "UNKNOWN", "entry_observable": False, "interior_depth_observable": False },
            "secondary_risk_pre": { "risk_score": 0.0, "evidence_status": "UNAVAILABLE" },
            "secondary_risk_post": { "risk_score": 0.0, "evidence_status": "UNAVAILABLE" },
            "delta_secondary_risk": { "delta_value": 0.0, "risk_increased": False, "evidence_status": "UNAVAILABLE" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "NONE", "secondary_entry_observable": False, "secondary_depth_observable": False, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": None },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Secondary zone is undefined (UNKNOWN); observability gate fails, prohibiting Backfire candidacy."
        },

        # H12: Partial Observability with Suspected Increase
        {
            "event_id": "CASE_H12_PARTIAL_OBSERVABILITY_SUSPECTED_HAZARD",
            "scenario_type": "PARTIAL_DEPTH_OBSERVABILITY",
            "description": "Secondary entry visible; secondary depth occluded; suspected agent movement behind pallets.",
            "primary_interaction": { "minimum_separation_px": 175.0, "co_occurring_frames": 115 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "SWERVE_AVOIDANCE", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "RACK_LANE_K", "zone_definition_type": "ADJACENT_RACK_AISLE", "entry_observable": True, "interior_depth_observable": False },
            "secondary_risk_pre": { "risk_score": 0.05, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.55, "evidence_status": "PARTIAL" },
            "delta_secondary_risk": { "delta_value": 0.50, "risk_increased": True, "evidence_status": "PARTIAL" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "PARTIAL", "secondary_entry_observable": True, "secondary_depth_observable": False, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "PARTIALLY_OBSERVED", "observable_causal_path": "TRUE", "latency_to_secondary_onset_s": 1.1 },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Secondary depth occluded; gate 2 fails (rule: never convert PARTIAL to NO_SECONDARY_RISK, never award candidate)."
        },

        # H13: Delta Secondary Risk Exactly Zero (Edge Case)
        {
            "event_id": "CASE_H13_EXACT_DELTA_ZERO_EDGE",
            "scenario_type": "EXACT_ZERO_DELTA_EDGE",
            "description": "Secondary risk before = 0.3500, after = 0.3500; delta = 0.0000 exactly.",
            "primary_interaction": { "minimum_separation_px": 165.0, "co_occurring_frames": 100 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "EMERGENCY_BRAKING", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": False },
            "secondary_zone": { "zone_id": "SEC_ZONE_L", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.35, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.35, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.00, "risk_increased": False, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": None },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "PRIMARY_NEAR_MISS",
            "oracle_reason": "Delta_R_sec == 0.0000 exactly fails Gate 3, routing decisively to PRIMARY_NEAR_MISS."
        },

        # H14: Delta Secondary Risk Negligible Noise (+0.005)
        {
            "event_id": "CASE_H14_NEGLIGIBLE_SENSOR_NOISE_DELTA",
            "scenario_type": "NOISE_DELTA_EDGE",
            "description": "Delta secondary risk = +0.005 (within bounding-box tracking jitter noise floor).",
            "primary_interaction": { "minimum_separation_px": 170.0, "co_occurring_frames": 90 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "EMERGENCY_BRAKING", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": False },
            "secondary_zone": { "zone_id": "SEC_ZONE_M", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.10, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.105, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.005, "risk_increased": True, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": 0.5 },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "PRIMARY_NEAR_MISS",
            "oracle_reason": "Delta (+0.005) is below noise threshold (0.010); Gate 3 treats as no significant increase."
        },

        # H15: Confounder Status Unknown
        {
            "event_id": "CASE_H15_CONFOUNDER_STATUS_UNKNOWN",
            "scenario_type": "UNKNOWN_CONFOUNDER_STATE",
            "description": "Camera feed glitched during POST; presence of independent vehicles/workers is unknown.",
            "primary_interaction": { "minimum_separation_px": 180.0, "co_occurring_frames": 110 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "SWERVE_AVOIDANCE", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "SEC_ZONE_N", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.05, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.65, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.60, "risk_increased": True, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "DIRECTLY_OBSERVED", "observable_causal_path": "TRUE", "latency_to_secondary_onset_s": 1.1 },
            "confounders": { "confounders_present": "UNKNOWN", "causal_isolation_status": "UNKNOWN" },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Confounder state is UNKNOWN; Gate 4 cannot verify causal isolation."
        },

        # H16: Temporal Ordering Violated
        {
            "event_id": "CASE_H16_TEMPORAL_ORDERING_VIOLATED",
            "scenario_type": "STAGE_SEQUENCE_INVERSION",
            "description": "Secondary risk increase logged at t=3.0s, prior to intervention at t=5.0s.",
            "primary_interaction": { "minimum_separation_px": 170.0, "co_occurring_frames": 100 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "SWERVE_AVOIDANCE", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "SEC_ZONE_O", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.05, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.70, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.65, "risk_increased": True, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": False },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "TRUE", "latency_to_secondary_onset_s": -2.0 },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Chronological stage ordering violated (secondary hazard preceded intervention)."
        },

        # H17: POST Window Inadequate (< 4 seconds)
        {
            "event_id": "CASE_H17_POST_WINDOW_INADEQUATE",
            "scenario_type": "TRUNCATED_POST_WINDOW",
            "description": "Post window ends 1.8 seconds after intervention due to video stream boundary.",
            "primary_interaction": { "minimum_separation_px": 175.0, "co_occurring_frames": 90 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "SWERVE_AVOIDANCE", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "SEC_ZONE_P", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.05, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.60, "evidence_status": "PARTIAL" },
            "delta_secondary_risk": { "delta_value": 0.55, "risk_increased": True, "evidence_status": "PARTIAL" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "INADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "PARTIALLY_OBSERVED", "observable_causal_path": "TRUE", "latency_to_secondary_onset_s": 1.0 },
            "confounders": { "confounders_present": "NO", "causal_isolation_status": "ISOLATED" },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Post window duration (1.8s) is inadequate; Gate 2 fails."
        },

        # H18: Track Handoff During Propagation
        {
            "event_id": "CASE_H18_TRACK_HANDOFF_DURING_PROPAGATION",
            "scenario_type": "TRACKER_ID_SWAP",
            "description": "Automated tracker swaps vehicle ID at secondary zone threshold, breaking trajectory identity.",
            "primary_interaction": { "minimum_separation_px": 180.0, "co_occurring_frames": 100 },
            "intervention_signal": { "intervention_detected": True, "intervention_type": "SWERVE_AVOIDANCE", "evidence_status": "OBSERVED" },
            "primary_mitigation": { "collision_averted": True, "evidence_status": "OBSERVED" },
            "risk_redirection": { "redirection_observed": True },
            "secondary_zone": { "zone_id": "SEC_ZONE_Q", "zone_definition_type": "CALIBRATED_POLYGON", "entry_observable": True, "interior_depth_observable": True },
            "secondary_risk_pre": { "risk_score": 0.05, "evidence_status": "OBSERVED" },
            "secondary_risk_post": { "risk_score": 0.70, "evidence_status": "OBSERVED" },
            "delta_secondary_risk": { "delta_value": 0.65, "risk_increased": True, "evidence_status": "OBSERVED" },
            "observability": { "primary_zone_status": "FULL", "secondary_zone_status": "FULL", "secondary_entry_observable": True, "secondary_depth_observable": True, "post_window_status": "ADEQUATE" },
            "temporal_order": { "chronological_stages_valid": True },
            "causal_link": { "causal_chain_status": "UNSUPPORTED", "observable_causal_path": "FALSE", "latency_to_secondary_onset_s": 1.2 },
            "confounders": {
                "confounders_present": "YES",
                "confounder_types": ["TRACK_HANDOFF"],
                "causal_isolation_status": "FAILED"
            },
            "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
            "oracle_reason": "Tracker handoff breaks trajectory continuity; Gate 4 fails."
        }
    ]
    return scenarios


def run_synthetic_tests():
    sm = BackfireStateMachine()
    scenarios = build_synthetic_scenarios()

    results = []
    traces = []
    all_passed = True

    print(f"Executing deterministic state machine across {len(scenarios)} synthetic scenarios...")

    for sc in scenarios:
        eid = sc["event_id"]
        exp = sc["expected_class"]
        eval_res = sm.evaluate(sc)
        actual = eval_res["candidate_class"]

        passed = (actual == exp)
        if not passed:
            all_passed = False

        res_record = {
            "event_id": eid,
            "scenario_type": sc["scenario_type"],
            "gate_results": eval_res["gate_results"],
            "actual_candidate_class": actual,
            "expected_candidate_class": exp,
            "logic_verification_match": passed,
            "failure_reasons": eval_res["failure_reasons"]
        }
        results.append(res_record)
        traces.append({
            "event_id": eid,
            "audit_trace": eval_res["audit_trace"]
        })

        status_sym = "[PASS]" if passed else "[FAIL]"
        print(f"  {status_sym} {eid:45s} -> Expected: {exp:28s} | Actual: {actual:28s}")

    assert all_passed, "Some synthetic scenarios did not match oracle label!"
    print(f"\n[SUCCESS] All {len(scenarios)} synthetic test cases passed with 100% exact logical match!")

    # 2. Invariant Property Tests
    print("\nRunning Formal Invariant Property Tests...")
    inv_results = run_invariant_tests(sm, scenarios)

    # 3. Counterfactual Logic Tests on H02
    print("\nRunning Counterfactual Logic Tests on H02...")
    cf_results = run_counterfactual_tests(sm, scenarios)

    # Save outputs
    with open(OUTPUT_DIR / "synthetic_scenarios.json", "w") as f:
        json.dump({"total_scenarios": len(scenarios), "scenarios": scenarios}, f, indent=2)

    with open(OUTPUT_DIR / "synthetic_results.json", "w") as f:
        json.dump({"total_scenarios": len(results), "all_matched": all_passed, "results": results}, f, indent=2)

    with open(OUTPUT_DIR / "backfire_state_machine_trace.json", "w") as f:
        json.dump({"traces": traces}, f, indent=2)

    with open(OUTPUT_DIR / "v3_4_h_invariant_test_results.json", "w") as f:
        json.dump({
            "invariants": inv_results,
            "counterfactuals": cf_results
        }, f, indent=2)

    print(f"[SUCCESS] All artifacts written to {OUTPUT_DIR}")
    return results, inv_results, cf_results


def run_invariant_tests(sm: BackfireStateMachine, scenarios: list) -> dict:
    inv_tests = {}

    # Property 1: If secondary_depth = False, never BACKFIRE_CANDIDATE
    prop1_pass = True
    for sc in scenarios:
        test_sc = copy.deepcopy(sc)
        test_sc["observability"]["secondary_depth_observable"] = False
        res = sm.evaluate(test_sc)
        if res["candidate_class"] == "BACKFIRE_CANDIDATE":
            prop1_pass = False
    inv_tests["PROPERTY_1_DEPTH_OCCLUSION_NEVER_CANDIDATE"] = {
        "passed": prop1_pass,
        "description": "Secondary depth occluded must NEVER result in BACKFIRE_CANDIDATE."
    }

    # Property 2: If Delta_R_sec <= 0, never BACKFIRE_CANDIDATE
    prop2_pass = True
    for sc in scenarios:
        test_sc = copy.deepcopy(sc)
        test_sc["delta_secondary_risk"]["delta_value"] = 0.0
        test_sc["secondary_risk_post"]["risk_score"] = test_sc["secondary_risk_pre"]["risk_score"]
        res = sm.evaluate(test_sc)
        if res["candidate_class"] == "BACKFIRE_CANDIDATE":
            prop2_pass = False
    inv_tests["PROPERTY_2_DELTA_LEQ_ZERO_NEVER_CANDIDATE"] = {
        "passed": prop2_pass,
        "description": "Delta_R_sec <= 0 must NEVER result in BACKFIRE_CANDIDATE."
    }

    # Property 3: If intervention = NOT_OBSERVED, never BACKFIRE_CANDIDATE
    prop3_pass = True
    for sc in scenarios:
        test_sc = copy.deepcopy(sc)
        test_sc["intervention_signal"]["intervention_detected"] = False
        test_sc["intervention_signal"]["evidence_status"] = "NOT_OBSERVED"
        res = sm.evaluate(test_sc)
        if res["candidate_class"] == "BACKFIRE_CANDIDATE":
            prop3_pass = False
    inv_tests["PROPERTY_3_UNCONFIRMED_INTERVENTION_NEVER_CANDIDATE"] = {
        "passed": prop3_pass,
        "description": "Unconfirmed intervention must NEVER result in BACKFIRE_CANDIDATE."
    }

    # Property 4: If causal_isolation = FAILED, never BACKFIRE_CANDIDATE
    prop4_pass = True
    for sc in scenarios:
        test_sc = copy.deepcopy(sc)
        test_sc["confounders"]["confounders_present"] = "YES"
        test_sc["confounders"]["causal_isolation_status"] = "FAILED"
        res = sm.evaluate(test_sc)
        if res["candidate_class"] == "BACKFIRE_CANDIDATE":
            prop4_pass = False
    inv_tests["PROPERTY_4_FAILED_ISOLATION_NEVER_CANDIDATE"] = {
        "passed": prop4_pass,
        "description": "Failed confounder isolation must NEVER result in BACKFIRE_CANDIDATE."
    }

    # Property 5: If temporal latency > 2.0s, never BACKFIRE_CANDIDATE
    prop5_pass = True
    for sc in scenarios:
        test_sc = copy.deepcopy(sc)
        test_sc["causal_link"]["latency_to_secondary_onset_s"] = 2.5
        res = sm.evaluate(test_sc)
        if res["candidate_class"] == "BACKFIRE_CANDIDATE":
            prop5_pass = False
    inv_tests["PROPERTY_5_LATENCY_VIOLATION_NEVER_CANDIDATE"] = {
        "passed": prop5_pass,
        "description": "Latency > 2.0s must NEVER result in BACKFIRE_CANDIDATE."
    }

    # Property 6: If secondary_zone = UNKNOWN, never BACKFIRE_CANDIDATE
    prop6_pass = True
    for sc in scenarios:
        test_sc = copy.deepcopy(sc)
        test_sc["secondary_zone"]["zone_definition_type"] = "UNKNOWN"
        res = sm.evaluate(test_sc)
        if res["candidate_class"] == "BACKFIRE_CANDIDATE":
            prop6_pass = False
    inv_tests["PROPERTY_6_UNDEFINED_ZONE_NEVER_CANDIDATE"] = {
        "passed": prop6_pass,
        "description": "Undefined secondary zone must NEVER result in BACKFIRE_CANDIDATE."
    }

    # Property 7: Varying PRIMARY_INTERACTION_SCORE alone never manufactures secondary risk
    h01 = next(s for s in scenarios if s["event_id"] == "CASE_H01_SAFE_COMPLETE_STOP")
    prop7_pass = True
    for synth_score in [0.60, 0.75, 0.90, 1.00]:
        test_sc = copy.deepcopy(h01)
        test_sc["primary_interaction"]["primary_interaction_score"] = synth_score
        res = sm.evaluate(test_sc)
        if res["candidate_class"] == "BACKFIRE_CANDIDATE":
            prop7_pass = False
    inv_tests["PROPERTY_7_INTERACTION_SCORE_ALONE_NEVER_MANUFACTURES_BACKFIRE"] = {
        "passed": prop7_pass,
        "description": "Elevating Primary Interaction Score to 1.00 on a safe stop must NEVER manufacture BACKFIRE_CANDIDATE."
    }

    # Negative Property Test: Close approach + safe stop -> PRIMARY_NEAR_MISS
    res_h01 = sm.evaluate(h01)
    neg_prop_pass = (res_h01["candidate_class"] == "PRIMARY_NEAR_MISS")
    inv_tests["NEGATIVE_PROPERTY_SAFE_CLOSE_APPROACH_MUST_BE_PRIMARY_NEAR_MISS"] = {
        "passed": neg_prop_pass,
        "description": "High proximity safe stop MUST be classified as PRIMARY_NEAR_MISS."
    }

    all_inv_pass = all(v["passed"] for v in inv_tests.values())
    print(f"Invariant Properties Passed: {sum(1 for v in inv_tests.values() if v['passed'])} / {len(inv_tests)}")
    assert all_inv_pass, "Some invariant property tests failed!"
    return inv_tests


def run_counterfactual_tests(sm: BackfireStateMachine, scenarios: list) -> dict:
    h02 = next(s for s in scenarios if s["event_id"] == "CASE_H02_TRUE_SYNTHETIC_BACKFIRE")
    cf_results = {}

    # CF1: Remove risk redirection from H02
    cf1 = copy.deepcopy(h02)
    cf1["risk_redirection"]["redirection_observed"] = False
    cf1["causal_link"]["observable_causal_path"] = "FALSE"
    res1 = sm.evaluate(cf1)
    cf_results["CF1_REMOVE_REDIRECTION"] = {
        "actual_class": res1["candidate_class"],
        "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
        "passed": (res1["candidate_class"] == "INSUFFICIENT_BACKFIRE_EVIDENCE")
    }

    # CF2: Make secondary depth PARTIAL / occluded on H02
    cf2 = copy.deepcopy(h02)
    cf2["observability"]["secondary_depth_observable"] = False
    cf2["secondary_zone"]["interior_depth_observable"] = False
    res2 = sm.evaluate(cf2)
    cf_results["CF2_OCCLUDE_SECONDARY_DEPTH"] = {
        "actual_class": res2["candidate_class"],
        "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
        "passed": (res2["candidate_class"] == "INSUFFICIENT_BACKFIRE_EVIDENCE")
    }

    # CF3: Add NEW_FORKLIFT confounder on H02
    cf3 = copy.deepcopy(h02)
    cf3["confounders"]["confounders_present"] = "YES"
    cf3["confounders"]["confounder_types"] = ["NEW_FORKLIFT"]
    cf3["confounders"]["causal_isolation_status"] = "FAILED"
    res3 = sm.evaluate(cf3)
    cf_results["CF3_ADD_NEW_FORKLIFT_CONFOUNDER"] = {
        "actual_class": res3["candidate_class"],
        "expected_class": "INSUFFICIENT_BACKFIRE_EVIDENCE",
        "passed": (res3["candidate_class"] == "INSUFFICIENT_BACKFIRE_EVIDENCE")
    }

    all_cf_pass = all(v["passed"] for v in cf_results.values())
    print(f"Counterfactual Tests Passed: {sum(1 for v in cf_results.values() if v['passed'])} / {len(cf_results)}")
    assert all_cf_pass, "Some counterfactual logic tests failed!"
    return cf_results


if __name__ == "__main__":
    run_synthetic_tests()
