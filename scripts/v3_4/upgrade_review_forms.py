"""
upgrade_review_forms.py
Standardizes reviewer forms and adjudication forms across all 51 packages in outputs/v3_4/adjudication
to include structured notes, event type question, submission locks, and revision history tracking.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
ADJUDICATION_DIR = WORKSPACE_ROOT / "outputs/v3_4/adjudication"


def upgrade_package(event_dir):
    event_id = event_dir.name
    r1_file = event_dir / "reviewer_1_form.json"
    r2_file = event_dir / "reviewer_2_form.json"
    adj_file = event_dir / "adjudication_form.json"

    # Default template for reviewer forms
    def make_reviewer_form(slot):
        return {
            "event_id": event_id,
            "reviewer_slot": slot,
            "reviewer_id": None,
            "session_id": None,
            "review_start_timestamp_utc": None,
            "review_completion_timestamp_utc": None,
            "status": "PENDING_HUMAN_REVIEW",
            "observed_event_type": None,  # SAFETY_INTERVENTION, NATURAL_INTERACTION, NORMAL_OPERATION, UNCERTAIN, NO_RELEVANT_EVENT
            "criteria_evaluations": {
                "intervention_visible": None,           # YES / NO / UNKNOWN
                "primary_risk_present": None,           # YES / NO / UNKNOWN
                "primary_risk_reduced": None,           # YES / NO / UNKNOWN
                "secondary_risk_changed": None,         # YES / NO / UNKNOWN
                "causal_mechanism_observed": None,      # YES / NO / UNKNOWN
                "independent_evidence_present": None,   # YES / NO / UNKNOWN
                "evidence_quality": None                # HIGH / MEDIUM / LOW / UNKNOWN
            },
            "causal_link_confidence": None,             # DIRECTLY_OBSERVED / TELEMETRY_SUPPORTED / PLAUSIBLE_BUT_UNCONFIRMED / NOT_ESTABLISHED
            "reviewer_notes": {
                "observations": "",
                "intervention_description": "",
                "primary_zone_description": "",
                "secondary_zone_description": "",
                "reasoning_notes": ""
            },
            "label_decision": None,                     # BACKFIRE / NO_BACKFIRE / AMBIGUOUS
            "submission_locked": False,
            "submission_hash": None,
            "revisions": []
        }

    # Write R1
    with open(r1_file, "w") as f:
        json.dump(make_reviewer_form("REVIEWER_1"), f, indent=2)

    # Write R2 (Completely isolated)
    with open(r2_file, "w") as f:
        json.dump(make_reviewer_form("REVIEWER_2"), f, indent=2)

    # Adjudication form
    adj_form = {
        "event_id": event_id,
        "adjudicator_id": None,
        "session_id": None,
        "decision_timestamp_utc": None,
        "status": "PENDING_HUMAN_REVIEW",
        "reviewer_1_label": None,
        "reviewer_2_label": None,
        "disagreement": False,
        "disagreement_reason": "",
        "adjudicator_label": "PENDING_HUMAN_REVIEW",
        "adjudicator_notes": {
            "disagreement_analysis": "",
            "causal_assessment": "",
            "final_decision_rationale": ""
        },
        "final_evidence_quality": None,
        "final_causal_link": None,
        "submission_locked": False,
        "submission_hash": None,
        "revisions": []
    }
    with open(adj_file, "w") as f:
        json.dump(adj_form, f, indent=2)


def main():
    pkg_dirs = [p for p in ADJUDICATION_DIR.iterdir() if p.is_dir() and p.name != "audit"]
    print(f"Upgrading {len(pkg_dirs)} review packages...")
    for pkg in pkg_dirs:
        upgrade_package(pkg)
    print("All review forms successfully standardized.")


if __name__ == "__main__":
    main()
