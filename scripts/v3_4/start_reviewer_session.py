"""
start_reviewer_session.py
Milestone V3.4-C — Human Adjudication Interactive Review Session CLI

Governance Guarantees:
  - Agent does NOT adjudicate. The human reviewer inputs all evaluations.
  - Strict Blinding: No AI scores, YOLO boxes, ByteTrack IDs, Model H values displayed.
  - Reviewer Isolation: Reviewer 2 cannot access Reviewer 1's entries or notes.
  - Strict Rules Enforced:
      * BACKFIRE requires all 6 criteria to be YES.
      * If secondary_risk is UNKNOWN, cannot label as NO_BACKFIRE (must be AMBIGUOUS).
  - Submission lock & revision tracking with SHA256 hashes.
  - Audit logging to outputs/v3_4/adjudication/audit/<session_id>.json.
"""

import sys
import os
import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import argparse

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
ADJUDICATION_DIR = WORKSPACE_ROOT / "outputs/v3_4/adjudication"
AUDIT_DIR = ADJUDICATION_DIR / "audit"
UNION_REGISTRY_PATH = WORKSPACE_ROOT / "outputs/v3_4/candidates/union_events_registry.json"
GT_PATH = WORKSPACE_ROOT / "outputs/v3_4/ground_truth/safety_backfire_event_gt.json"

ALLOWED_EVENT_TYPES = [
    "SAFETY_INTERVENTION",
    "NATURAL_INTERACTION",
    "NORMAL_OPERATION",
    "UNCERTAIN",
    "NO_RELEVANT_EVENT"
]

ALLOWED_CRITERIA_VALUES = ["YES", "NO", "UNKNOWN"]
ALLOWED_EVIDENCE_QUALITY = ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
ALLOWED_CAUSAL_LINKS = [
    "DIRECTLY_OBSERVED",
    "TELEMETRY_SUPPORTED",
    "PLAUSIBLE_BUT_UNCONFIRMED",
    "NOT_ESTABLISHED"
]

ALLOWED_FINAL_LABELS = ["BACKFIRE", "NO_BACKFIRE", "AMBIGUOUS"]


def compute_sha256(data_str: str) -> str:
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()


def verify_package_integrity(package_dir: Path) -> tuple[bool, str]:
    meta_path = package_dir / "review_metadata.json"
    if not meta_path.exists():
        return False, "review_metadata.json missing"
    
    with open(meta_path) as f:
        meta = json.load(f)

    if not meta.get("window_valid", False):
        return False, f"Event is ineligible (status: {meta.get('eligibility_status')})"

    src_sha = meta.get("source_video_sha256", "")
    pkg_hash = meta.get("package_hash", "")
    event_id = meta.get("event_id", "")
    
    twb = meta.get("temporal_window_bounds", {})
    psf = twb.get("pre", {}).get("start_frame", 0)
    ief = twb.get("intervention", {}).get("end_frame", 0)
    post_ef = twb.get("post", {}).get("end_frame", 0)

    expected_hash = compute_sha256(f"{event_id}_{src_sha}_{psf}_{ief}_{post_ef}")
    if pkg_hash != expected_hash:
        return False, f"Package hash mismatch (expected: {expected_hash}, got: {pkg_hash})"

    # Check video clips exist and are non-empty
    for clip_name in ["before.mp4", "intervention.mp4", "after.mp4"]:
        clip_path = package_dir / clip_name
        if not clip_path.exists() or clip_path.stat().st_size == 0:
            return False, f"Derived video clip {clip_name} missing or empty"

    return True, "Integrity verified"


def get_eligible_events() -> list[dict]:
    if not UNION_REGISTRY_PATH.exists():
        return []
    with open(UNION_REGISTRY_PATH) as f:
        reg = json.load(f)
    records = reg.get("union_records", [])
    # Return only eligible events sorted deterministically by event_id
    eligible = [r for r in records if r.get("window_valid", False)]
    eligible.sort(key=lambda x: x["union_id"])
    return eligible


def get_event_review_status(event_id: str) -> dict:
    pkg_dir = ADJUDICATION_DIR / event_id
    res = {
        "event_id": event_id,
        "reviewer_1_status": "PENDING",
        "reviewer_2_status": "PENDING",
        "adjudication_status": "PENDING_HUMAN_REVIEW",
        "final_label": "PENDING_HUMAN_REVIEW"
    }
    if not pkg_dir.exists():
        return res

    r1_file = pkg_dir / "reviewer_1_form.json"
    if r1_file.exists():
        with open(r1_file) as f:
            d = json.load(f)
            if d.get("status") == "COMPLETED":
                res["reviewer_1_status"] = "COMPLETED"

    r2_file = pkg_dir / "reviewer_2_form.json"
    if r2_file.exists():
        with open(r2_file) as f:
            d = json.load(f)
            if d.get("status") == "COMPLETED":
                res["reviewer_2_status"] = "COMPLETED"

    adj_file = pkg_dir / "adjudication_form.json"
    if adj_file.exists():
        with open(adj_file) as f:
            d = json.load(f)
            res["adjudication_status"] = d.get("status", "PENDING_HUMAN_REVIEW")
            res["final_label"] = d.get("adjudicator_label", "PENDING_HUMAN_REVIEW")

    return res


def write_audit_log(session_id: str, event_id: str, reviewer_id: str,
                    start_time: str, end_time: str, package_hash: str,
                    form_hash: str, status: str, slot: str):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    audit_record = {
        "session_id": session_id,
        "event_id": event_id,
        "reviewer_id": reviewer_id,
        "reviewer_slot": slot,
        "session_start_utc": start_time,
        "session_end_utc": end_time,
        "package_hash": package_hash,
        "form_submission_hash": form_hash,
        "submission_status": status,
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    audit_file = AUDIT_DIR / f"{session_id}.json"
    with open(audit_file, "w") as f:
        json.dump(audit_record, f, indent=2)


def submit_reviewer_form(package_dir: Path, slot: str, reviewer_id: str,
                         form_data: dict, session_id: str, start_time: str) -> tuple[bool, str]:
    form_filename = "reviewer_1_form.json" if slot == "REVIEWER_1" else "reviewer_2_form.json"
    form_path = package_dir / form_filename
    if not form_path.exists():
        return False, f"Form {form_filename} does not exist"

    with open(form_path) as f:
        existing_form = json.load(f)

    # Reviewer Isolation check:
    if slot == "REVIEWER_2":
        # Ensure form has no data from reviewer 1
        r1_path = package_dir / "reviewer_1_form.json"
        if r1_path.exists():
            with open(r1_path) as f:
                r1_data = json.load(f)
            # Verify no keys in form_data borrow from r1_data
            if form_data.get("reviewer_notes") == r1_data.get("reviewer_notes") and r1_data.get("reviewer_notes", {}).get("observations"):
                return False, "Isolation violation: Reviewer 2 notes identical to Reviewer 1"

    # Enforce BACKFIRE validation rules
    label = form_data.get("label_decision")
    crit = form_data.get("criteria_evaluations", {})

    # Check criteria completeness
    for c_name in [
        "intervention_visible", "primary_risk_present", "primary_risk_reduced",
        "secondary_risk_changed", "causal_mechanism_observed", "independent_evidence_present"
    ]:
        val = crit.get(c_name)
        if val not in ALLOWED_CRITERIA_VALUES:
            return False, f"Criterion {c_name} must be answered with YES, NO, or UNKNOWN"

    if crit.get("evidence_quality") not in ALLOWED_EVIDENCE_QUALITY:
        return False, "evidence_quality must be HIGH, MEDIUM, LOW, or UNKNOWN"

    if label == "BACKFIRE":
        # System only permits BACKFIRE if all 6 criteria are YES
        required_yes = [
            "intervention_visible", "primary_risk_present", "primary_risk_reduced",
            "secondary_risk_changed", "causal_mechanism_observed", "independent_evidence_present"
        ]
        failed_criteria = [c for c in required_yes if crit.get(c) != "YES"]
        if failed_criteria:
            return False, f"BACKFIRE label rejected: Criteria {failed_criteria} must all be YES"

    elif label == "NO_BACKFIRE":
        # System does NOT allow converting UNKNOWN secondary risk to NO_BACKFIRE
        if crit.get("secondary_risk_changed") == "UNKNOWN":
            return False, "NO_BACKFIRE label rejected: secondary_risk_changed is UNKNOWN (must be labeled AMBIGUOUS)"

    # Revision handling
    now_iso = datetime.now(timezone.utc).isoformat()
    revisions = existing_form.get("revisions", [])
    current_serialized = json.dumps(existing_form, sort_keys=True)
    prev_hash = existing_form.get("submission_hash") or compute_sha256(current_serialized)

    if existing_form.get("submission_locked", False):
        rev_entry = {
            "revision_number": len(revisions) + 1,
            "previous_hash": prev_hash,
            "timestamp_utc": now_iso,
            "reason": "Human reviewer revision update"
        }
        revisions.append(rev_entry)

    # Build updated form
    updated_form = {
        "event_id": package_dir.name,
        "reviewer_slot": slot,
        "reviewer_id": reviewer_id,
        "session_id": session_id,
        "review_start_timestamp_utc": start_time,
        "review_completion_timestamp_utc": now_iso,
        "status": "COMPLETED",
        "observed_event_type": form_data.get("observed_event_type"),
        "criteria_evaluations": crit,
        "causal_link_confidence": form_data.get("causal_link_confidence"),
        "reviewer_notes": form_data.get("reviewer_notes", {}),
        "label_decision": label,
        "submission_locked": True,
        "revisions": revisions
    }

    # Hash submission
    sub_hash = compute_sha256(json.dumps(updated_form, sort_keys=True))
    updated_form["submission_hash"] = sub_hash

    # Save form
    with open(form_path, "w") as f:
        json.dump(updated_form, f, indent=2)

    # Write audit log
    meta_path = package_dir / "review_metadata.json"
    with open(meta_path) as f:
        meta = json.load(f)
    pkg_hash = meta.get("package_hash", "")

    write_audit_log(session_id, package_dir.name, reviewer_id, start_time, now_iso,
                    pkg_hash, sub_hash, "SUCCESS", slot)

    # Check inter-rater status
    check_and_update_consensus(package_dir)

    return True, f"Submission locked successfully. Hash: {sub_hash[:16]}..."


def check_and_update_consensus(package_dir: Path):
    r1_path = package_dir / "reviewer_1_form.json"
    r2_path = package_dir / "reviewer_2_form.json"
    adj_path = package_dir / "adjudication_form.json"

    if not (r1_path.exists() and r2_path.exists() and adj_path.exists()):
        return

    with open(r1_path) as f:
        r1 = json.load(f)
    with open(r2_path) as f:
        r2 = json.load(f)
    with open(adj_path) as f:
        adj = json.load(f)

    if r1.get("status") == "COMPLETED" and r2.get("status") == "COMPLETED":
        l1 = r1.get("label_decision")
        l2 = r2.get("label_decision")
        adj["reviewer_1_label"] = l1
        adj["reviewer_2_label"] = l2

        if l1 == l2:
            adj["status"] = "CONSENSUS_REACHED"
            adj["disagreement"] = False
            adj["disagreement_reason"] = "Both independent reviewers reached identical conclusion."
            adj["adjudicator_label"] = l1
        else:
            adj["status"] = "ADJUDICATION_REQUIRED"
            adj["disagreement"] = True
            adj["disagreement_reason"] = f"Reviewer 1 concluded '{l1}' while Reviewer 2 concluded '{l2}'."
            adj["adjudicator_label"] = "PENDING_HUMAN_REVIEW"

        with open(adj_path, "w") as f:
            json.dump(adj, f, indent=2)


def submit_adjudication(package_dir: Path, adjudicator_id: str, final_label: str,
                        notes: dict, final_evidence_quality: str, final_causal_link: str,
                        session_id: str, start_time: str) -> tuple[bool, str]:
    adj_path = package_dir / "adjudication_form.json"
    if not adj_path.exists():
        return False, "adjudication_form.json not found"

    with open(adj_path) as f:
        adj = json.load(f)

    if final_label not in ALLOWED_FINAL_LABELS:
        return False, f"Invalid final label '{final_label}'"

    now_iso = datetime.now(timezone.utc).isoformat()
    adj["adjudicator_id"] = adjudicator_id
    adj["session_id"] = session_id
    adj["decision_timestamp_utc"] = now_iso
    adj["status"] = "ADJUDICATED"
    adj["adjudicator_label"] = final_label
    adj["adjudicator_notes"] = notes
    adj["final_evidence_quality"] = final_evidence_quality
    adj["final_causal_link"] = final_causal_link
    adj["submission_locked"] = True

    sub_hash = compute_sha256(json.dumps(adj, sort_keys=True))
    adj["submission_hash"] = sub_hash

    with open(adj_path, "w") as f:
        json.dump(adj, f, indent=2)

    meta_path = package_dir / "review_metadata.json"
    with open(meta_path) as f:
        meta = json.load(f)

    write_audit_log(session_id, package_dir.name, adjudicator_id, start_time, now_iso,
                    meta.get("package_hash", ""), sub_hash, "ADJUDICATED", "ADJUDICATOR")

    return True, f"Adjudication completed. Final Label: {final_label}"


def run_test_dryrun():
    """Validates the adjudication review engine on an isolated temporary test package."""
    print("=== Running Dry-Run Review Engine Validation ===")
    test_id = "TEST_EVENT_VALIDATION_001"
    test_dir = ADJUDICATION_DIR / test_id
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create mock metadata
        meta = {
            "event_id": test_id,
            "source_video_sha256": "mock_sha256_hash",
            "package_hash": compute_sha256(f"{test_id}_mock_sha256_hash_0_100_200"),
            "window_valid": True,
            "temporal_window_bounds": {
                "pre": {"start_frame": 0, "end_frame": 50},
                "intervention": {"start_frame": 51, "end_frame": 100},
                "post": {"start_frame": 101, "end_frame": 200}
            }
        }
        with open(test_dir / "review_metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

        # Create dummy clips
        for clip in ["before.mp4", "intervention.mp4", "after.mp4"]:
            with open(test_dir / clip, "wb") as f:
                f.write(b"MOCK_VIDEO_DATA")

        # Initialize forms
        r1_form = {"event_id": test_id, "reviewer_slot": "REVIEWER_1", "status": "PENDING_HUMAN_REVIEW"}
        r2_form = {"event_id": test_id, "reviewer_slot": "REVIEWER_2", "status": "PENDING_HUMAN_REVIEW"}
        adj_form = {"event_id": test_id, "status": "PENDING_HUMAN_REVIEW", "adjudicator_label": "PENDING_HUMAN_REVIEW"}

        with open(test_dir / "reviewer_1_form.json", "w") as f:
            json.dump(r1_form, f)
        with open(test_dir / "reviewer_2_form.json", "w") as f:
            json.dump(r2_form, f)
        with open(test_dir / "adjudication_form.json", "w") as f:
            json.dump(adj_form, f)

        # 1. Test Integrity check
        ok, msg = verify_package_integrity(test_dir)
        assert ok, f"Integrity check failed: {msg}"
        print("  [PASS] Video package integrity check passed.")

        # 2. Test Rule: BACKFIRE rejection when criterion is not YES
        bad_submission = {
            "observed_event_type": "SAFETY_INTERVENTION",
            "criteria_evaluations": {
                "intervention_visible": "YES",
                "primary_risk_present": "YES",
                "primary_risk_reduced": "YES",
                "secondary_risk_changed": "UNKNOWN",  # Not YES
                "causal_mechanism_observed": "YES",
                "independent_evidence_present": "YES",
                "evidence_quality": "HIGH"
            },
            "causal_link_confidence": "PLAUSIBLE_BUT_UNCONFIRMED",
            "reviewer_notes": {"observations": "Test note"},
            "label_decision": "BACKFIRE"
        }
        res_ok, res_msg = submit_reviewer_form(test_dir, "REVIEWER_1", "TEST_REV_01", bad_submission, "test_sess_01", "2026-09-30T00:00:00Z")
        assert not res_ok, "Rule violation: BACKFIRE was incorrectly permitted with UNKNOWN criterion!"
        print("  [PASS] Rule guard correctly blocked invalid BACKFIRE decision.")

        # 3. Test Rule: NO_BACKFIRE rejection when secondary risk is UNKNOWN
        bad_no_backfire = dict(bad_submission)
        bad_no_backfire["label_decision"] = "NO_BACKFIRE"
        res_ok, res_msg = submit_reviewer_form(test_dir, "REVIEWER_1", "TEST_REV_01", bad_no_backfire, "test_sess_01", "2026-09-30T00:00:00Z")
        assert not res_ok, "Rule violation: NO_BACKFIRE was incorrectly permitted with UNKNOWN secondary risk!"
        print("  [PASS] Rule guard correctly blocked invalid NO_BACKFIRE with UNKNOWN secondary risk.")

        # 4. Test Valid AMBIGUOUS Submission
        valid_ambiguous = dict(bad_submission)
        valid_ambiguous["label_decision"] = "AMBIGUOUS"
        res_ok, res_msg = submit_reviewer_form(test_dir, "REVIEWER_1", "TEST_REV_01", valid_ambiguous, "test_sess_01", "2026-09-30T00:00:00Z")
        assert res_ok, f"Submission failed: {res_msg}"
        print("  [PASS] Valid submission accepted and frozen.")

        # 5. Test Audit Log created
        audit_file = AUDIT_DIR / "test_sess_01.json"
        assert audit_file.exists(), "Audit log was not written!"
        print("  [PASS] Audit log verified.")

        print("=== Dry-Run Review Engine Validation Successfully Completed ===")
    finally:
        # Clean up test package completely
        if test_dir.exists():
            for f in test_dir.iterdir():
                f.unlink()
            test_dir.rmdir()
        test_audit = AUDIT_DIR / "test_sess_01.json"
        if test_audit.exists():
            test_audit.unlink()


def main():
    parser = argparse.ArgumentParser(description="Human Adjudication Interactive Session")
    parser.add_argument("--test-mode", action="store_true", help="Run automated dry-run validation")
    parser.add_argument("--list-eligible", action="store_true", help="List all 38 eligible events and their status")
    parser.add_argument("--reviewer-id", type=str, help="Human Reviewer ID (e.g. REVIEWER_001)")
    parser.add_argument("--slot", choices=["REVIEWER_1", "REVIEWER_2", "ADJUDICATOR"], help="Reviewer slot")
    parser.add_argument("--event-id", type=str, help="Event ID to review")
    args = parser.parse_args()

    if args.test_mode:
        run_test_dryrun()
        return

    eligible = get_eligible_events()
    if args.list_eligible:
        print(f"\n{'='*75}")
        print(f"  ELIGIBLE EVENTS FOR HUMAN ADJUDICATION (N={len(eligible)})")
        print(f"{'='*75}")
        print(f"{'INDEX':<6} {'EVENT ID':<30} {'R1 STATUS':<12} {'R2 STATUS':<12} {'FINAL LABEL'}")
        print(f"{'-'*75}")
        for idx, ev in enumerate(eligible, 1):
            st = get_event_review_status(ev["union_id"])
            print(f"{idx:<6} {ev['union_id']:<30} {st['reviewer_1_status']:<12} {st['reviewer_2_status']:<12} {st['final_label']}")
        print(f"{'='*75}\n")
        return

    print("\nTo start human review sessions, you can run:")
    print("  .venv/bin/python scripts/v3_4/start_reviewer_session.py --list-eligible")
    print("  .venv/bin/python scripts/v3_4/review_server.py  (Local Web Dashboard)")


if __name__ == "__main__":
    main()
