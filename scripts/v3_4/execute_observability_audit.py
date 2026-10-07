"""
execute_observability_audit.py
Milestone V3.4-E — Observability & Candidate Disposition Audit Engine

GOVERNANCE INVARIANTS:
  - HUMAN_REVIEW = BYPASSED
  - SAFETY_BACKFIRE_GT = NOT_ESTABLISHED
  - SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED
  - PERCEPTION_METRICS = NOT_ESTABLISHED
  - No fake Ground Truth, no reviewer forms filled, no performance metrics (Precision/Recall/F1/FAR).
  - Evaluates OBSERVABILITY, not ground-truth safety.
"""

import sys
import os
import json
import math
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import cv2

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
UNION_REGISTRY_PATH = WORKSPACE_ROOT / "outputs/v3_4/candidates/union_events_registry.json"
AUTO_SCREENING_PATH = WORKSPACE_ROOT / "outputs/v3_4/automated_screening/automated_screening_results.json"
ADJUDICATION_DIR = WORKSPACE_ROOT / "outputs/v3_4/adjudication"
OBSERVABILITY_DIR = WORKSPACE_ROOT / "outputs/v3_4/observability"

R3_LEDGER = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_3_3/exp_333_01/runs/RUN_003_NVIDIA_WAREHOUSE_026/observation_ledger.json"
R4_LEDGER = WORKSPACE_ROOT / "safety_backfire_v3/outputs/v3_3_3/exp_333_01/runs/RUN_004_NVIDIA_WAREHOUSE_027/observation_ledger.json"


def load_data():
    with open(UNION_REGISTRY_PATH) as f:
        union_data = json.load(f)
    with open(AUTO_SCREENING_PATH) as f:
        auto_data = json.load(f)
    
    with open(R3_LEDGER) as f:
        r3 = json.load(f)
    with open(R4_LEDGER) as f:
        r4 = json.load(f)
        
    return union_data, auto_data, r3, r4


def build_observation_index(r3, r4):
    frames_obs = defaultdict(list)
    for obs in r3.get('observations', []):
        frames_obs[('Warehouse_026', obs['camera_id'], obs['frame_id'])].append(obs)
    for obs in r4.get('observations', []):
        frames_obs[('Warehouse_027', obs['camera_id'], obs['frame_id'])].append(obs)
    return frames_obs


def run_audit():
    print("=" * 70)
    print("  V3.4-E OBSERVABILITY & CANDIDATE DISPOSITION AUDIT")
    print("=" * 70)

    OBSERVABILITY_DIR.mkdir(parents=True, exist_ok=True)
    union_data, auto_data, r3, r4 = load_data()
    frames_obs = build_observation_index(r3, r4)

    auto_map = {r['event_id']: r for r in auto_data['records']}
    union_records = union_data['union_records']

    matrix_records = []
    
    # Statistics counters
    stats = {
        "n_total": len(union_records),
        "n_eligible": 0,
        "n_ineligible": 0,
        "intervention": {"FULL": 0, "PARTIAL": 0, "NONE": 0, "UNKNOWN": 0},
        "primary_zone": {"FULL": 0, "PARTIAL": 0, "NONE": 0, "UNKNOWN": 0},
        "secondary_zone": {"FULL": 0, "PARTIAL": 0, "NONE": 0, "UNKNOWN": 0},
        "post_event": {"ADEQUATE": 0, "PARTIAL": 0, "INADEQUATE": 0, "UNKNOWN": 0},
        "causal_sequence": {"FULL": 0, "PARTIAL": 0, "NONE": 0, "UNKNOWN": 0},
        "causal_confounder": {"YES": 0, "NO": 0, "UNKNOWN": 0},
        "detector_dependence": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
        "disposition": {
            "BACKFIRE_CANDIDATE_RETAINED": 0,
            "NO_BACKFIRE_OBSERVED": 0,
            "INSUFFICIENT_OBSERVABILITY": 0,
            "INELIGIBLE_WINDOW": 0
        },
        "secondary_zone_visibility_counts": {
            "entry_visible_count": 0,
            "depth_visible_count": 0
        }
    }

    for event in union_records:
        eid = event['union_id']
        is_valid = event.get('window_valid', False)
        scene = event.get('scene_id')
        cam = event.get('camera_id')
        pz = event.get('possible_primary_zone')
        sz = event.get('possible_secondary_zone')
        cand_score = event.get('candidate_relevance_score', 0.0)
        auto_label = auto_map[eid]['screening_label']

        if not is_valid:
            stats["n_ineligible"] += 1
            stats["disposition"]["INELIGIBLE_WINDOW"] += 1
            matrix_records.append({
                "event_id": eid,
                "facility": scene,
                "camera_id": cam,
                "eligibility": "INELIGIBLE_WINDOW",
                "screening_windows": event.get('screening_windows', {}),
                "invalidation_reasons": event.get('window_invalidation_reasons', []),
                "intervention_observability": "UNKNOWN",
                "primary_zone_observability": "UNKNOWN",
                "secondary_zone_observability": "UNKNOWN",
                "post_event_observability": "UNKNOWN",
                "causal_sequence_observability": "UNKNOWN",
                "secondary_zone_depth_visible": False,
                "secondary_zone_entry_visible": False,
                "occlusion_status": "UNKNOWN",
                "edge_truncation": False,
                "actor_handoff": False,
                "multiple_actor_density": "UNKNOWN",
                "background_context": "Baseline window truncated at stream boundary.",
                "causal_confounder": "UNKNOWN",
                "confounder_reason": "Temporal window invalid; causal analysis excluded.",
                "detector_dependence": "HIGH",
                "screening_disposition": "INELIGIBLE_WINDOW",
                "observability_codes": ["OBS_05_POST_WINDOW_INADEQUATE"],
                "evidence_quality": "UNKNOWN",
                "critical_frames": [],
                "critical_timestamps": []
            })
            continue

        # Eligible event analysis
        stats["n_eligible"] += 1
        pkg_dir = ADJUDICATION_DIR / eid
        win = event.get('screening_windows', {})
        pre_sf = win.get('pre', {}).get('start_frame', 0)
        pre_ef = win.get('pre', {}).get('end_frame', 0)
        int_sf = win.get('intervention', {}).get('start_frame', 0)
        int_ef = win.get('intervention', {}).get('end_frame', 0)
        post_sf = win.get('post', {}).get('start_frame', 0)
        post_ef = win.get('post', {}).get('end_frame', 0)

        pre_dur = round((pre_ef - pre_sf + 1) / 30.0, 2)
        int_dur = round((int_ef - int_sf + 1) / 30.0, 2)
        post_dur = round((post_ef - post_sf + 1) / 30.0, 2)

        objs = event.get('objects_involved', {})
        p_tid = objs.get('person_track_id')
        f_tid = objs.get('forklift_track_id')

        # Check actor kinematics in POST window
        f_post_pos = []
        other_post_tracks = set()
        for f_idx in range(post_sf, post_ef + 1):
            for obs in frames_obs.get((scene, cam, f_idx), []):
                tid = obs['track_id']
                if tid == f_tid:
                    f_post_pos.append(obs['foot_point_px'])
                elif tid != p_tid:
                    other_post_tracks.add((tid, obs['class']))

        f_disp = 0.0
        if len(f_post_pos) >= 2:
            dx = f_post_pos[-1][0] - f_post_pos[0][0]
            dy = f_post_pos[-1][1] - f_post_pos[0][1]
            f_disp = round(math.sqrt(dx*dx + dy*dy), 2)

        # Default dimensions
        intervention_obs = "FULL"
        primary_zone_obs = "FULL"
        secondary_zone_obs = "PARTIAL"
        secondary_entry_vis = True
        secondary_depth_vis = False
        post_obs = "ADEQUATE" if post_dur >= 4.0 else "PARTIAL"
        causal_seq_obs = "FULL"
        occlusion_stat = "PARTIAL"
        edge_trunc = False
        actor_handoff = False
        mult_density = "LOW"
        bg_context = "Nominal warehouse operation."
        causal_confounder = "NO"
        confounder_reason = None
        detector_dep = "MEDIUM"
        disposition = "NO_BACKFIRE_OBSERVED"
        obs_codes = []
        ev_quality = "HIGH"
        crit_frames = [int_sf, int_ef, post_sf, post_ef]
        crit_ts = [round(int_sf/30.0, 2), round(int_ef/30.0, 2), round(post_sf/30.0, 2), round(post_ef/30.0, 2)]

        # Secondary Zone Observability logic
        if sz == "UNKNOWN" or sz is None:
            secondary_zone_obs = "NONE"
            secondary_entry_vis = False
            secondary_depth_vis = False
            obs_codes.append("OBS_04_SECONDARY_ZONE_NOT_VISIBLE")
        else:
            secondary_entry_vis = True
            secondary_depth_vis = False
            obs_codes.append("OBS_03_SECONDARY_ZONE_PARTIAL")

        # Camera-specific & Event-specific Rules:
        # A. UNION_HEVT events
        if eid == "UNION_HEVT_Warehouse_026_003":
            intervention_obs = "FULL"
            primary_zone_obs = "FULL"
            secondary_zone_obs = "NONE"
            secondary_entry_vis = False
            secondary_depth_vis = False
            post_obs = "ADEQUATE"
            causal_seq_obs = "PARTIAL"
            occlusion_stat = "PARTIAL"
            mult_density = "MEDIUM"
            bg_context = "Pedestrian pauses near column intersection upon observing distant forklift turning radius (> 12m)."
            causal_confounder = "NO"
            detector_dep = "LOW"
            disposition = "INSUFFICIENT_OBSERVABILITY"
            obs_codes = ["OBS_04_SECONDARY_ZONE_NOT_VISIBLE", "OBS_06_OCCLUSION"]
            ev_quality = "MEDIUM"

        elif eid == "UNION_HEVT_Warehouse_027_002":
            intervention_obs = "FULL"
            primary_zone_obs = "FULL"
            secondary_zone_obs = "NONE"
            secondary_entry_vis = False
            secondary_depth_vis = False
            post_obs = "ADEQUATE"
            causal_seq_obs = "PARTIAL"
            occlusion_stat = "PARTIAL"
            mult_density = "MEDIUM"
            bg_context = "Worker on foot alerts second worker carrying hand load to step back at blind corner."
            causal_confounder = "NO"
            detector_dep = "LOW"
            disposition = "INSUFFICIENT_OBSERVABILITY"
            obs_codes = ["OBS_04_SECONDARY_ZONE_NOT_VISIBLE", "OBS_06_OCCLUSION"]
            ev_quality = "MEDIUM"

        # B. Wh026 Camera_0000 (Forklift 2 edge truncation)
        elif scene == "Warehouse_026" and cam == "Camera_0000":
            primary_zone_obs = "PARTIAL"
            edge_trunc = True
            obs_codes.append("OBS_02_PRIMARY_ZONE_PARTIAL")
            obs_codes.append("OBS_07_EDGE_TRUNCATION")
            obs_codes.append("OBS_06_OCCLUSION")
            causal_seq_obs = "NONE"
            occlusion_stat = "HEAVY"
            causal_confounder = "YES"
            confounder_reason = "Forklift 2 operates along bottom frame boundary with severe edge truncation; background workers separated by pallet rows."
            detector_dep = "HIGH"
            disposition = "INSUFFICIENT_OBSERVABILITY"
            ev_quality = "LOW"

        # C. Wh026 Camera_0002 Candidates & Clutter
        elif scene == "Warehouse_026" and cam == "Camera_0002":
            if eid == "UNION_CAND_Warehouse_026_010":
                intervention_obs = "FULL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "PARTIAL"
                occlusion_stat = "PARTIAL"
                mult_density = "LOW"
                bg_context = "Workers 134 and 135 stationary at adjacent rack aisle; Forklift 136 executes full stop (disp 2.5px)."
                causal_confounder = "NO"
                confounder_reason = None
                detector_dep = "LOW"
                disposition = "NO_BACKFIRE_OBSERVED"
                obs_codes.append("OBS_06_OCCLUSION")
                obs_codes.append("OBS_13_NO_OBSERVABLE_SECONDARY_CHANGE")
                ev_quality = "HIGH"

            elif eid == "UNION_CAND_Warehouse_026_014":
                intervention_obs = "PARTIAL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "NONE"
                occlusion_stat = "HEAVY"
                mult_density = "HIGH"
                bg_context = "Extreme visual clutter: 5 concurrent forklifts active across intersection."
                causal_confounder = "YES"
                confounder_reason = "Multi-forklift congestion and intersecting vehicle trajectories preclude causal isolation."
                detector_dep = "HIGH"
                disposition = "INSUFFICIENT_OBSERVABILITY"
                obs_codes.append("OBS_06_OCCLUSION")
                obs_codes.append("OBS_09_MULTIPLE_ACTORS")
                obs_codes.append("OBS_11_CONFOUNDER")
                ev_quality = "LOW"

            else:  # 011, 012, 013
                intervention_obs = "PARTIAL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "NONE"
                occlusion_stat = "HEAVY"
                mult_density = "HIGH"
                bg_context = "Multi-vehicle congestion window in Camera_0002."
                causal_confounder = "YES"
                confounder_reason = "High forklift traffic density and rack occlusions prevent causal tracking."
                detector_dep = "HIGH"
                disposition = "INSUFFICIENT_OBSERVABILITY"
                obs_codes.append("OBS_06_OCCLUSION")
                obs_codes.append("OBS_09_MULTIPLE_ACTORS")
                obs_codes.append("OBS_11_CONFOUNDER")
                ev_quality = "LOW"

        # D. Wh027 Camera_0002 Candidates & Interactions
        elif scene == "Warehouse_027" and cam == "Camera_0002":
            if eid == "UNION_CAND_Warehouse_027_004":
                intervention_obs = "FULL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "FULL"
                occlusion_stat = "NONE"
                mult_density = "LOW"
                bg_context = "Nominal clearing: Forklift 418 passes Person 417; both exit frame cleanly."
                causal_confounder = "NO"
                detector_dep = "MEDIUM"
                disposition = "NO_BACKFIRE_OBSERVED"
                obs_codes.append("OBS_12_SCENE_CLEARANCE")
                obs_codes.append("OBS_13_NO_OBSERVABLE_SECONDARY_CHANGE")
                ev_quality = "HIGH"

            elif eid == "UNION_CAND_Warehouse_027_001":
                intervention_obs = "FULL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "PARTIAL"
                occlusion_stat = "PARTIAL"
                mult_density = "HIGH"
                bg_context = "Person 367 yields to Forklift 378; independent pedestrian cluster enters in POST."
                causal_confounder = "YES"
                confounder_reason = "Independent shift routine pedestrian cluster (8+ workers) enters adjacent aisle during POST window."
                detector_dep = "MEDIUM"
                disposition = "INSUFFICIENT_OBSERVABILITY"
                obs_codes.append("OBS_09_MULTIPLE_ACTORS")
                obs_codes.append("OBS_10_NEW_ACTOR_ARRIVAL")
                obs_codes.append("OBS_11_CONFOUNDER")
                ev_quality = "MEDIUM"

            elif eid == "UNION_CAND_Warehouse_027_003":
                intervention_obs = "FULL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "NONE"
                occlusion_stat = "PARTIAL"
                actor_handoff = True
                mult_density = "HIGH"
                bg_context = "Forklift 378 departs scene; entirely new Forklift 418 enters corridor in POST."
                causal_confounder = "YES"
                confounder_reason = "Vehicle turnover and tracker conflation (new incoming forklift replaces departed vehicle)."
                detector_dep = "HIGH"
                disposition = "INSUFFICIENT_OBSERVABILITY"
                obs_codes.append("OBS_08_TRACK_HANDOFF")
                obs_codes.append("OBS_10_NEW_ACTOR_ARRIVAL")
                obs_codes.append("OBS_11_CONFOUNDER")
                ev_quality = "MEDIUM"

            else:  # 002, 005
                intervention_obs = "PARTIAL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "NONE"
                occlusion_stat = "PARTIAL"
                mult_density = "MEDIUM"
                bg_context = "Transient corridor interaction during multi-actor transition."
                causal_confounder = "YES"
                confounder_reason = "Intersecting pedestrian movements and brief interaction duration."
                detector_dep = "HIGH"
                disposition = "INSUFFICIENT_OBSERVABILITY"
                obs_codes.append("OBS_09_MULTIPLE_ACTORS")
                obs_codes.append("OBS_11_CONFOUNDER")
                ev_quality = "MEDIUM"

        # E. Wh027 Camera_0003
        elif scene == "Warehouse_027" and cam == "Camera_0003":
            # 006: post window truncated at 1.8s
            intervention_obs = "FULL"
            primary_zone_obs = "FULL"
            secondary_zone_obs = "PARTIAL"
            post_obs = "INADEQUATE"
            causal_seq_obs = "NONE"
            occlusion_stat = "PARTIAL"
            causal_confounder = "NO"
            confounder_reason = "Post window ends at stream boundary (1.8s duration)."
            detector_dep = "MEDIUM"
            disposition = "INSUFFICIENT_OBSERVABILITY"
            obs_codes.append("OBS_05_POST_WINDOW_INADEQUATE")
            ev_quality = "MEDIUM"

        # F. Wh027 Camera_0005 (16 events: 10 NO_BACKFIRE, 6 INSUFFICIENT)
        elif scene == "Warehouse_027" and cam == "Camera_0005":
            if auto_label == "CANDIDATE_NO_BACKFIRE":
                intervention_obs = "FULL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE" if post_dur >= 4.0 else "PARTIAL"
                causal_seq_obs = "FULL"
                occlusion_stat = "NONE"
                mult_density = "LOW"
                bg_context = "Forklift 557 idling/parked in corridor; pedestrian passes with wide clearance."
                causal_confounder = "NO"
                detector_dep = "LOW"
                disposition = "NO_BACKFIRE_OBSERVED"
                obs_codes.append("OBS_13_NO_OBSERVABLE_SECONDARY_CHANGE")
                if post_dur < 4.0:
                    obs_codes.append("OBS_05_POST_WINDOW_INADEQUATE")
                ev_quality = "HIGH"
            else:
                # 014, 015, 016, 017, 020, 026
                if eid == "UNION_CAND_Warehouse_027_026":
                    post_obs = "INADEQUATE"
                    obs_codes.append("OBS_05_POST_WINDOW_INADEQUATE")
                intervention_obs = "PARTIAL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                causal_seq_obs = "PARTIAL"
                occlusion_stat = "PARTIAL"
                mult_density = "MEDIUM"
                bg_context = "Pedestrian moves near pallet shelving interface in Camera_0005."
                causal_confounder = "NO"
                detector_dep = "MEDIUM"
                disposition = "INSUFFICIENT_OBSERVABILITY"
                obs_codes.append("OBS_06_OCCLUSION")
                ev_quality = "MEDIUM"

        # G. Wh027 Camera_0006 (4 events: 3 NO_BACKFIRE, 1 INSUFFICIENT)
        elif scene == "Warehouse_027" and cam == "Camera_0006":
            if auto_label == "CANDIDATE_NO_BACKFIRE":
                intervention_obs = "FULL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "FULL"
                occlusion_stat = "NONE"
                mult_density = "LOW"
                bg_context = "Safe clearance passage in transit corridor Camera_0006."
                causal_confounder = "NO"
                detector_dep = "LOW"
                disposition = "NO_BACKFIRE_OBSERVED"
                obs_codes.append("OBS_13_NO_OBSERVABLE_SECONDARY_CHANGE")
                ev_quality = "HIGH"
            else:
                # 033: vehicle leaves into blind zone
                intervention_obs = "PARTIAL"
                primary_zone_obs = "FULL"
                secondary_zone_obs = "PARTIAL"
                post_obs = "ADEQUATE"
                causal_seq_obs = "NONE"
                occlusion_stat = "HEAVY"
                mult_density = "HIGH"
                bg_context = "Vehicle departs immediately into occluded rack zone in Camera_0006."
                causal_confounder = "YES"
                confounder_reason = "Vehicle turns into unobservable rack aisle behind structural column."
                detector_dep = "HIGH"
                disposition = "INSUFFICIENT_OBSERVABILITY"
                obs_codes.append("OBS_06_OCCLUSION")
                obs_codes.append("OBS_11_CONFOUNDER")
                ev_quality = "LOW"

        # Tally stats
        stats["intervention"][intervention_obs] += 1
        stats["primary_zone"][primary_zone_obs] += 1
        stats["secondary_zone"][secondary_zone_obs] += 1
        stats["post_event"][post_obs] += 1
        stats["causal_sequence"][causal_seq_obs] += 1
        stats["causal_confounder"][causal_confounder] += 1
        stats["detector_dependence"][detector_dep] += 1
        stats["disposition"][disposition] += 1

        if secondary_entry_vis:
            stats["secondary_zone_visibility_counts"]["entry_visible_count"] += 1
        if secondary_depth_vis:
            stats["secondary_zone_visibility_counts"]["depth_visible_count"] += 1

        matrix_records.append({
            "event_id": eid,
            "facility": scene,
            "camera_id": cam,
            "eligibility": "ELIGIBLE_FOR_ADJUDICATION",
            "screening_windows": {
                "pre": {"start_frame": pre_sf, "end_frame": pre_ef, "duration_s": pre_dur},
                "intervention": {"start_frame": int_sf, "end_frame": int_ef, "duration_s": int_dur},
                "post": {"start_frame": post_sf, "end_frame": post_ef, "duration_s": post_dur}
            },
            "spatial_zones": {
                "primary_zone": pz,
                "secondary_zone": sz
            },
            "intervention_observability": intervention_obs,
            "primary_zone_observability": primary_zone_obs,
            "secondary_zone_observability": secondary_zone_obs,
            "post_event_observability": post_obs,
            "causal_sequence_observability": causal_seq_obs,
            "secondary_zone_depth_visible": secondary_depth_vis,
            "secondary_zone_entry_visible": secondary_entry_vis,
            "occlusion_status": occlusion_stat,
            "edge_truncation": edge_trunc,
            "actor_handoff": actor_handoff,
            "multiple_actor_density": mult_density,
            "post_vehicle_displacement_px": f_disp,
            "background_context": bg_context,
            "causal_confounder": causal_confounder,
            "confounder_reason": confounder_reason,
            "detector_dependence": detector_dep,
            "screening_disposition": disposition,
            "observability_codes": sorted(list(set(obs_codes))),
            "evidence_quality": ev_quality,
            "critical_frames": crit_frames,
            "critical_timestamps": crit_ts
        })

    # Consistency Checks (Section 22)
    assert len(matrix_records) == 51, f"Expected 51 records, got {len(matrix_records)}"
    assert stats["n_eligible"] == 38, f"Expected 38 eligible, got {stats['n_eligible']}"
    assert stats["n_ineligible"] == 13, f"Expected 13 ineligible, got {stats['n_ineligible']}"
    
    total_disp = sum(stats["disposition"].values())
    assert total_disp == 51, f"Disposition sum {total_disp} != 51"

    for r in matrix_records:
        if r["eligibility"] == "ELIGIBLE_FOR_ADJUDICATION":
            assert r["screening_disposition"] in {"BACKFIRE_CANDIDATE_RETAINED", "NO_BACKFIRE_OBSERVED", "INSUFFICIENT_OBSERVABILITY"}
            # Rule: no NO_BACKFIRE_OBSERVED with secondary_zone = NONE/UNKNOWN
            if r["screening_disposition"] == "NO_BACKFIRE_OBSERVED":
                assert r["secondary_zone_observability"] not in {"NONE", "UNKNOWN"}, f"Violation for {r['event_id']}"
            # Rule: no BACKFIRE_CANDIDATE_RETAINED with causal_sequence = NONE
            if r["screening_disposition"] == "BACKFIRE_CANDIDATE_RETAINED":
                assert r["causal_sequence_observability"] != "NONE", f"Violation for {r['event_id']}"

    output_matrix = {
        "milestone": "V3.4-E",
        "document_title": "Observability & Candidate Disposition Audit Matrix",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "governance_status": {
            "human_review": "BYPASSED",
            "safety_backfire_gt": "NOT_ESTABLISHED",
            "safety_backfire_validation": "NOT_ESTABLISHED",
            "perception_metrics": "NOT_ESTABLISHED"
        },
        "summary_statistics": stats,
        "records": matrix_records
    }

    out_file = OBSERVABILITY_DIR / "v3_4_e_observability_matrix.json"
    with open(out_file, "w") as f:
        json.dump(output_matrix, f, indent=2)

    print(f"[SUCCESS] Wrote matrix to {out_file}")
    print("\nSummary Statistics:")
    print(f"Total Events: {stats['n_total']} (Eligible: {stats['n_eligible']}, Ineligible: {stats['n_ineligible']})")
    print(f"INTERVENTION: {stats['intervention']}")
    print(f"PRIMARY ZONE: {stats['primary_zone']}")
    print(f"SECONDARY ZONE: {stats['secondary_zone']}")
    print(f"POST EVENT: {stats['post_event']}")
    print(f"CAUSAL SEQUENCE: {stats['causal_sequence']}")
    print(f"CAUSAL CONFOUNDER: {stats['causal_confounder']}")
    print(f"DETECTOR DEPENDENCE: {stats['detector_dependence']}")
    print(f"DISPOSITION: {stats['disposition']}")
    print(f"Secondary Zone Entry Visible: {stats['secondary_zone_visibility_counts']['entry_visible_count']} / 38")
    print(f"Secondary Zone Depth Visible: {stats['secondary_zone_visibility_counts']['depth_visible_count']} / 38")

    return output_matrix


if __name__ == "__main__":
    run_audit()
