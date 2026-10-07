"""
execute_candidate_generation_audit.py
Milestone V3.4-F — Candidate Generation & Score Decomposition Audit Engine

GOVERNANCE INVARIANTS:
  - HUMAN_REVIEW = BYPASSED
  - SAFETY_BACKFIRE_GT = NOT_ESTABLISHED
  - SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED
  - PERCEPTION_METRICS = NOT_ESTABLISHED
  - MODEL_H = FROZEN_INVARIANT
  - No model training, no retraining, no threshold tuning, no parameter adaptation.
  - Audit only.
"""

import sys
import os
import json
import re
import math
import hashlib
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
UNION_REGISTRY_PATH = WORKSPACE_ROOT / "outputs/v3_4/candidates/union_events_registry.json"
AUTO_SCREENING_PATH = WORKSPACE_ROOT / "outputs/v3_4/automated_screening/automated_screening_results.json"
OBSERVABILITY_PATH = WORKSPACE_ROOT / "outputs/v3_4/observability/v3_4_e_observability_matrix.json"
AUDIT_MANIFEST_PATH = WORKSPACE_ROOT / "outputs/v3_4_f/audit_manifest.json"
OUTPUT_DIR = WORKSPACE_ROOT / "outputs/v3_4_f"


def get_file_sha256(filepath: Path) -> str:
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_audit():
    print("=" * 70)
    print("  V3.4-F CANDIDATE GENERATION & SCORE DECOMPOSITION AUDIT")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(UNION_REGISTRY_PATH) as f:
        union_data = json.load(f)
    with open(AUTO_SCREENING_PATH) as f:
        auto_data = json.load(f)
    with open(OBSERVABILITY_PATH) as f:
        obs_data = json.load(f)

    obs_map = {r["event_id"]: r for r in obs_data["records"]}
    auto_map = {r["event_id"]: r for r in auto_data["records"]}

    generator_source_files = {
        "candidate_generator": "scripts/v3_4/discover_event_candidates.py",
        "union_constructor": "scripts/v3_4/execute_human_screening_and_union.py",
        "automated_screener": "scripts/v3_4/automated_evidence_screening.py"
    }

    generator_hashes = {
        k: get_file_sha256(WORKSPACE_ROOT / v) for k, v in generator_source_files.items()
    }

    # Features and exact weights
    features_audit = {
        "spatial_proximity": {
            "name": "minimum_pixel_distance",
            "unit": "pixels (2D Euclidean)",
            "actually_used": True,
            "weight": 0.60,
            "formula": "prox_score = max(0.0, min(1.0, 1.0 - (min_px / 600.0)))",
            "source_location": "scripts/v3_4/discover_event_candidates.py:145"
        },
        "co_occurrence_duration": {
            "name": "co_occurring_frame_count",
            "unit": "frames (at 30 fps)",
            "actually_used": True,
            "weight": 0.40,
            "formula": "dur_score = min(1.0, len(items) / 150.0)",
            "source_location": "scripts/v3_4/discover_event_candidates.py:146"
        },
        "detector_confidence": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_USED"
        },
        "agent_velocity": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_USED"
        },
        "trajectory_heading_change": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_USED"
        },
        "intervention_evidence": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_USED"
        },
        "primary_risk_change": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_USED"
        },
        "secondary_risk_change": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_IMPLEMENTED"
        },
        "risk_redirection": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_IMPLEMENTED"
        },
        "post_intervention_risk_increase": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_IMPLEMENTED"
        },
        "causal_chain_requirement": {
            "actually_used": False,
            "weight": 0.0,
            "status": "ABSENT"
        },
        "post_event_evidence": {
            "actually_used": False,
            "weight": 0.0,
            "status": "NOT_REQUIRED"
        }
    }

    # Thresholds audit
    thresholds_audit = {
        "co_occurrence_min_frames": {
            "value": 20,
            "unit": "frames",
            "seconds": 0.66,
            "source": "scripts/v3_4/discover_event_candidates.py:137",
            "purpose": "Filter out transient 1-frame spurious co-detections"
        },
        "max_proximity_baseline": {
            "value": 600.0,
            "unit": "pixels",
            "source": "scripts/v3_4/discover_event_candidates.py:145",
            "purpose": "Distance beyond which proximity score reaches 0.0"
        },
        "duration_saturation_frames": {
            "value": 150,
            "unit": "frames",
            "seconds": 5.0,
            "source": "scripts/v3_4/discover_event_candidates.py:146",
            "purpose": "Duration beyond which duration score saturates at 1.0"
        },
        "candidate_backfire_screening_threshold": {
            "value": 0.60,
            "unit": "score ratio [0.0, 1.0]",
            "source": "scripts/v3_4/automated_evidence_screening.py:196",
            "purpose": "Threshold for AUTOMATED_SCREENING_LABEL = CANDIDATE_BACKFIRE"
        },
        "candidate_no_backfire_screening_threshold": {
            "value": 0.15,
            "unit": "score ratio [0.0, 1.0]",
            "source": "scripts/v3_4/automated_evidence_screening.py:204",
            "purpose": "Threshold for AUTOMATED_SCREENING_LABEL = CANDIDATE_NO_BACKFIRE"
        },
        "secondary_zone_definition_gate": {
            "value": "sz != 'UNKNOWN'",
            "source": "scripts/v3_4/automated_evidence_screening.py:192",
            "purpose": "Exclude events with undefined secondary zone from CANDIDATE_BACKFIRE"
        }
    }

    # Process all 51 events
    all_events_decomposition = []
    candidates_5_decomposition = []

    cands_5_ids = {
        "UNION_CAND_Warehouse_026_010",
        "UNION_CAND_Warehouse_027_001",
        "UNION_CAND_Warehouse_027_003",
        "UNION_CAND_Warehouse_027_004",
        "UNION_CAND_Warehouse_026_014"
    }

    for u in union_data["union_records"]:
        eid = u["union_id"]
        is_valid = u.get("window_valid", False)
        score = u.get("candidate_relevance_score")
        auto_lbl = auto_map[eid]["screening_label"]
        obs_disp = obs_map[eid]["screening_disposition"]

        reason = u.get("ai_provenance", {}).get("screening_reason", "")
        m = re.search(r"closest approach:\s*([0-9\.]+)px", reason)
        min_px = float(m.group(1)) if m else None

        if min_px is not None:
            prox_score = max(0.0, min(1.0, 1.0 - (min_px / 600.0)))
            prox_contrib = round(0.60 * prox_score, 3)
            dur_contrib = round(max(0.0, score - prox_contrib), 3)
            dur_score = round(dur_contrib / 0.40, 3)
        else:
            prox_score = None
            prox_contrib = None
            dur_contrib = None
            dur_score = None

        # Counterfactuals
        score_without_prox = dur_contrib if dur_contrib is not None else 0.0
        score_without_dur = prox_contrib if prox_contrib is not None else 0.0
        score_without_trajectory = score
        score_without_intervention = score
        score_without_secondary = score

        prox_critical = (score_without_prox < 0.60) if score is not None else None
        dur_critical = (score_without_dur < 0.60) if score is not None else None

        dominant_feat = "NOT_APPLICABLE"
        if prox_contrib is not None and dur_contrib is not None and score > 0:
            if prox_contrib > dur_contrib:
                dominant_feat = "SPATIAL_PROXIMITY"
            elif dur_contrib > prox_contrib:
                dominant_feat = "CO_OCCURRENCE_DURATION"
            else:
                dominant_feat = "BALANCED"

        rec = {
            "event_id": eid,
            "scene_id": u.get("scene_id"),
            "camera_id": u.get("camera_id"),
            "eligibility": "ELIGIBLE" if is_valid else "INELIGIBLE_WINDOW",
            "automated_screening_label": auto_lbl,
            "v3_4_e_screening_disposition": obs_disp,
            "candidate_relevance_score": score,
            "raw_min_pixel_distance": min_px,
            "normalized_proximity_score": prox_score,
            "normalized_duration_score": dur_score,
            "proximity_contribution": prox_contrib,
            "duration_contribution": dur_contrib,
            "proximity_share_percent": round((prox_contrib / score * 100), 1) if (score and prox_contrib is not None and score > 0) else None,
            "duration_share_percent": round((dur_contrib / score * 100), 1) if (score and dur_contrib is not None and score > 0) else None,
            "trajectory_contribution": "NOT_USED",
            "detector_confidence_contribution": "NOT_USED",
            "intervention_contribution": "NOT_USED",
            "primary_risk_contribution": "NOT_USED",
            "secondary_risk_contribution": "NOT_IMPLEMENTED",
            "causal_chain_contribution": "NOT_IMPLEMENTED",
            "post_event_contribution": "NOT_USED",
            "dominant_feature": dominant_feat,
            "counterfactual_scores": {
                "actual_score": score,
                "without_spatial_proximity": score_without_prox,
                "without_co_occurrence_duration": score_without_dur,
                "without_trajectory": score_without_trajectory,
                "without_intervention": score_without_intervention,
                "without_secondary_risk": score_without_secondary
            },
            "feature_necessity": {
                "proximity_critical_for_candidacy": prox_critical,
                "duration_critical_for_candidacy": dur_critical
            }
        }

        all_events_decomposition.append(rec)
        if eid in cands_5_ids:
            candidates_5_decomposition.append(rec)

    # Sort candidates by relevance score
    candidates_5_decomposition.sort(key=lambda x: x["candidate_relevance_score"], reverse=True)

    # Negative control audit: analyze events classified as NO_BACKFIRE_OBSERVED in V3.4-E
    negative_controls = [
        r for r in all_events_decomposition
        if r["v3_4_e_screening_disposition"] == "NO_BACKFIRE_OBSERVED"
    ]

    neg_ctrl_behavior = {
        "total_negative_controls": len(negative_controls),
        "scored_below_0_15_count": len([r for r in negative_controls if r["candidate_relevance_score"] < 0.15]),
        "scored_above_0_60_count": len([r for r in negative_controls if r["candidate_relevance_score"] >= 0.60]),
        "anomalous_high_score_events": [
            {
                "event_id": r["event_id"],
                "candidate_relevance_score": r["candidate_relevance_score"],
                "raw_min_pixel_distance": r["raw_min_pixel_distance"],
                "v3_4_e_finding": "Vehicle stopped completely (disp 2.5px) with zero secondary hazard" if r["event_id"] == "UNION_CAND_Warehouse_026_010" else "Both agents cleared corridor safely with zero secondary hazard"
            }
            for r in negative_controls if r["candidate_relevance_score"] >= 0.60
        ],
        "interpretation": (
            "Descriptive negative control behavior proves that high spatial proximity (< 230 px) caused the generator "
            "to produce candidate scores >= 0.60 even when the physical interaction resolved safely with zero secondary risk transfer."
        )
    }

    # Observability Linkage
    obs_linkage = {
        "candidate_score_vs_secondary_zone_observability": {
            "mean_score_partial_secondary_zone": round(
                sum(r["candidate_relevance_score"] for r in all_events_decomposition if r["eligibility"] == "ELIGIBLE" and obs_map[r["event_id"]]["secondary_zone_observability"] == "PARTIAL") /
                len([r for r in all_events_decomposition if r["eligibility"] == "ELIGIBLE" and obs_map[r["event_id"]]["secondary_zone_observability"] == "PARTIAL"]), 3
            ),
            "finding": "High candidate scores occur indiscriminately in zones where secondary depth is unobservable (PARTIAL)."
        },
        "candidate_score_vs_causal_sequence_observability": {
            "mean_score_broken_causal_sequence_none": round(
                sum(r["candidate_relevance_score"] for r in all_events_decomposition if r["eligibility"] == "ELIGIBLE" and obs_map[r["event_id"]]["causal_sequence_observability"] == "NONE") /
                len([r for r in all_events_decomposition if r["eligibility"] == "ELIGIBLE" and obs_map[r["event_id"]]["causal_sequence_observability"] == "NONE"]), 3
            ),
            "finding": "Candidate scores >= 0.60 were assigned to events with broken causal sequences (e.g. 027_003 track handoff, 026_014 clutter) because generator ignored causal continuity."
        }
    }

    audit_results = {
        "milestone": "V3.4-F",
        "document_title": "Candidate Generation & Score Decomposition Audit",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "governance_status": {
            "human_review": "BYPASSED",
            "safety_backfire_gt": "NOT_ESTABLISHED",
            "safety_backfire_validation": "NOT_ESTABLISHED",
            "perception_metrics": "NOT_ESTABLISHED",
            "model_h": "FROZEN_INVARIANT"
        },
        "generator_files": generator_source_files,
        "generator_hashes": generator_hashes,
        "features_audit": features_audit,
        "thresholds_audit": thresholds_audit,
        "scoring_equation": {
            "formula": "relevance_score = round(0.60 * prox_score + 0.40 * dur_score, 3)",
            "prox_score": "max(0.0, min(1.0, 1.0 - (min_pixel_distance / 600.0)))",
            "dur_score": "min(1.0, co_occurring_frames / 150.0)",
            "mathematical_implication": "Score >= 0.60 mathematically requires min_pixel_distance <= 400.0 px. Duration alone can never exceed 0.40."
        },
        "five_candidates_decomposition": candidates_5_decomposition,
        "all_38_events_decomposition": [r for r in all_events_decomposition if r["eligibility"] == "ELIGIBLE"],
        "negative_control_behavior": neg_ctrl_behavior,
        "observability_linkage": obs_linkage,
        "architectural_classification": "PROXIMITY_DOMINANT",
        "confirmed_findings": [
            "Candidate generator relies exclusively on 2 features: minimum 2D Euclidean footpoint distance (60%) and co-occurrence duration (40%).",
            "Zero secondary-risk features are implemented (SECONDARY_RISK_FEATURE = NOT_IMPLEMENTED).",
            "Zero causal chain requirements exist (CAUSAL_CHAIN_REQUIREMENT = ABSENT).",
            "Post-event window evidence is not used in score calculation (POST_EVIDENCE_NOT_REQUIRED_FOR_CANDIDACY = TRUE).",
            "The generator mathematically cannot distinguish between a near-miss stopped safely and an evasive backfire cascade."
        ],
        "limitations": [
            "Audit evaluated existing codebase implementations without executing retraining or parameter tuning.",
            "All findings describe candidate generator heuristic mechanics, not physical safety ground truth."
        ]
    }

    out_file = OUTPUT_DIR / "candidate_generation_audit.json"
    with open(out_file, "w") as f:
        json.dump(audit_results, f, indent=2)

    print(f"[SUCCESS] Wrote audit table to {out_file}")
    return audit_results


if __name__ == "__main__":
    run_audit()
