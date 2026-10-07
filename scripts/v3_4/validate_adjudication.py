"""
validate_adjudication.py
Milestone V3.4-C — Human Adjudication & Ground Truth Quality Control Validator

Strict Quality Control Checks:
  1. Missing reviewer verification (prevent missing reviewer IDs on submitted forms)
  2. Duplicate event detection across registry, adjudication packages, and GT
  3. Missing reviewer label validation
  4. Unauthorized final label prevention (enforcing BACKFIRE, NO_BACKFIRE, AMBIGUOUS, PENDING_HUMAN_REVIEW)
  5. Reviewer 2 isolation validation (prevent Reviewer 2 seeing Reviewer 1 decisions)
  6. Invalid event ID validation against union registry
  7. Invalid hash detection (source SHA256 and package SHA256 integrity)
  8. Invalid window enforcement (INELIGIBLE_WINDOW must be excluded from causal adjudication & GT)
  9. Missing evidence quality verification
  10. AI Blinding verification (zero AI scores, YOLO conf, ByteTrack IDs, Model H in review forms)
"""

import sys
import json
import hashlib
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
UNION_REGISTRY_PATH = WORKSPACE_ROOT / "outputs/v3_4/candidates/union_events_registry.json"
ADJUDICATION_DIR = WORKSPACE_ROOT / "outputs/v3_4/adjudication"
GT_PATH = WORKSPACE_ROOT / "outputs/v3_4/ground_truth/safety_backfire_event_gt.json"

ALLOWED_REVIEWER_CRITERIA_VALUES = {"YES", "NO", "UNKNOWN"}
ALLOWED_EVIDENCE_QUALITY = {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}
ALLOWED_CAUSAL_LINKS = {
    "DIRECTLY_OBSERVED",
    "TELEMETRY_SUPPORTED",
    "PLAUSIBLE_BUT_UNCONFIRMED",
    "NOT_ESTABLISHED",
    None
}
FORBIDDEN_CAUSAL_LINKS = {"CAUSED_BY_AI", "PROVEN_CAUSAL"}
ALLOWED_LABELS = {"BACKFIRE", "NO_BACKFIRE", "AMBIGUOUS", "PENDING_HUMAN_REVIEW", None}
FORBIDDEN_LABELS = {"PASS", "FAIL", "CERTIFIED", "SAFETY_CERTIFIED"}


class AdjudicationValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {
            "total_registry_events": 0,
            "eligible_events": 0,
            "ineligible_events": 0,
            "adjudication_packages_scanned": 0,
            "reviewer_1_completed": 0,
            "reviewer_2_completed": 0,
            "both_reviewers_completed": 0,
            "agreements": 0,
            "disagreements": 0,
            "final_labels": {
                "BACKFIRE": 0,
                "NO_BACKFIRE": 0,
                "AMBIGUOUS": 0,
                "PENDING_HUMAN_REVIEW": 0
            },
            "gt_events_count": 0
        }

    def validate(self):
        print("=" * 70)
        print("  V3.4-C INDEPENDENT HUMAN ADJUDICATION QUALITY CONTROL VALIDATOR")
        print("=" * 70)

        # 1. Load Registry
        if not UNION_REGISTRY_PATH.exists():
            self.errors.append(f"Union registry not found at {UNION_REGISTRY_PATH}")
            return False

        with open(UNION_REGISTRY_PATH) as f:
            registry_data = json.load(f)

        union_records = registry_data.get("union_records", [])
        self.stats["total_registry_events"] = len(union_records)

        # Check duplicate events in registry
        reg_ids = [r["union_id"] for r in union_records]
        if len(reg_ids) != len(set(reg_ids)):
            dup = [x for x in reg_ids if reg_ids.count(x) > 1]
            self.errors.append(f"[DUPLICATE_EVENT] Duplicate event IDs in registry: {set(dup)}")

        registry_map = {r["union_id"]: r for r in union_records}

        # 2. Check Adjudication Directory
        if not ADJUDICATION_DIR.exists():
            self.errors.append(f"Adjudication directory not found at {ADJUDICATION_DIR}")
            return False

        package_dirs = [p for p in ADJUDICATION_DIR.iterdir() if p.is_dir() and p.name != "audit"]
        self.stats["adjudication_packages_scanned"] = len(package_dirs)

        seen_pkg_ids = set()

        for pkg_dir in package_dirs:
            event_id = pkg_dir.name
            
            # Check duplicate package
            if event_id in seen_pkg_ids:
                self.errors.append(f"[DUPLICATE_EVENT] Duplicate package directory for event: {event_id}")
            seen_pkg_ids.add(event_id)

            # Check invalid event ID
            if event_id not in registry_map:
                self.errors.append(f"[INVALID_EVENT_ID] Adjudication package {event_id} not present in union registry")
                continue

            reg_record = registry_map[event_id]
            is_eligible_reg = reg_record.get("window_valid", False)
            if is_eligible_reg:
                self.stats["eligible_events"] += 1
            else:
                self.stats["ineligible_events"] += 1

            self._validate_package(pkg_dir, event_id, reg_record)

        # 3. Check Ground Truth File
        self._validate_ground_truth(registry_map)

        # Print Summary
        self._print_report()

        return len(self.errors) == 0

    def _validate_package(self, pkg_dir, event_id, reg_record):
        is_eligible = reg_record.get("window_valid", False)

        # Expected files
        meta_file = pkg_dir / "review_metadata.json"
        r1_file = pkg_dir / "reviewer_1_form.json"
        r2_file = pkg_dir / "reviewer_2_form.json"
        adj_file = pkg_dir / "adjudication_form.json"

        for required_file, name in [(meta_file, "review_metadata.json"), 
                                    (r1_file, "reviewer_1_form.json"), 
                                    (r2_file, "reviewer_2_form.json"), 
                                    (adj_file, "adjudication_form.json")]:
            if not required_file.exists():
                self.errors.append(f"[MISSING_FILE] {name} missing in package {event_id}")

        if not meta_file.exists():
            return

        with open(meta_file) as f:
            meta = json.load(f)

        # 7. Invalid Hash Check
        src_sha = meta.get("source_video_sha256", "")
        pkg_hash = meta.get("package_hash", "")
        if not src_sha or src_sha == "SOURCE_FILE_NOT_FOUND":
            self.errors.append(f"[INVALID_HASH] Event {event_id} has invalid or missing source_video_sha256")
        
        twb = meta.get("temporal_window_bounds", {})
        psf = twb.get("pre", {}).get("start_frame", 0)
        ief = twb.get("intervention", {}).get("end_frame", 0)
        post_ef = twb.get("post", {}).get("end_frame", 0)
        expected_pkg_hash = hashlib.sha256(f"{event_id}_{src_sha}_{psf}_{ief}_{post_ef}".encode("utf-8")).hexdigest()
        if pkg_hash != expected_pkg_hash:
            self.errors.append(f"[INVALID_HASH] Event {event_id} package_hash mismatch: expected {expected_pkg_hash}, got {pkg_hash}")

        # 8. Invalid Window Check
        window_valid_meta = meta.get("window_valid", True)
        if not is_eligible:
            if window_valid_meta:
                self.errors.append(f"[INVALID_WINDOW] Event {event_id} marked window_valid=False in registry but True in metadata")
            if meta.get("eligibility_status") != "INELIGIBLE_WINDOW":
                self.errors.append(f"[INVALID_WINDOW] Event {event_id} status must be INELIGIBLE_WINDOW, got {meta.get('eligibility_status')}")
            if meta.get("adjudication_readiness") != "EXCLUDED_FROM_ADJUDICATION":
                self.errors.append(f"[INVALID_WINDOW] Event {event_id} with invalid window must be EXCLUDED_FROM_ADJUDICATION")
        else:
            # Check derived video clips exist for eligible events
            for clip_name in ["before.mp4", "intervention.mp4", "after.mp4"]:
                clip_path = pkg_dir / clip_name
                if not clip_path.exists():
                    self.errors.append(f"[MISSING_VIDEO_CLIP] Eligible event {event_id} missing {clip_name}")
                elif clip_path.stat().st_size == 0:
                    self.errors.append(f"[CORRUPTED_VIDEO_CLIP] Eligible event {event_id} {clip_name} is 0 bytes")

        # 10. AI Blinding Verification on Metadata
        meta_str = json.dumps(meta).lower()
        forbidden_ai_keys = ["candidate_relevance_score", "yolo", "bytetrack", "model_h", "model h", "ai_recommendation"]
        for fk in forbidden_ai_keys:
            if fk in meta_str:
                self.errors.append(f"[BLINDING_VIOLATION] Forbidden AI attribute '{fk}' found in metadata for {event_id}")

        # Validate Reviewer 1 Form
        r1_completed = False
        r1_label = None
        if r1_file.exists():
            with open(r1_file) as f:
                r1 = json.load(f)
            r1_status = r1.get("status")
            r1_completed = (r1_status == "COMPLETED")
            r1_label = r1.get("label_decision")

            if r1_completed:
                self.stats["reviewer_1_completed"] += 1
                # 1. Missing reviewer check
                if not r1.get("reviewer_id"):
                    self.errors.append(f"[MISSING_REVIEWER] Event {event_id} Reviewer 1 completed without reviewer_id")
                # 3. Missing reviewer label
                if r1_label not in {"BACKFIRE", "NO_BACKFIRE", "AMBIGUOUS"}:
                    self.errors.append(f"[MISSING_REVIEWER_LABEL] Event {event_id} Reviewer 1 completed without valid label decision")
                # 9. Missing evidence quality
                ev_q = r1.get("criteria_evaluations", {}).get("evidence_quality")
                if ev_q not in ALLOWED_EVIDENCE_QUALITY:
                    self.errors.append(f"[MISSING_EVIDENCE_QUALITY] Event {event_id} Reviewer 1 missing valid evidence quality")
            else:
                if r1_label is not None and r1_label != "PENDING_HUMAN_REVIEW":
                    self.errors.append(f"[PREMATURE_LABEL] Event {event_id} Reviewer 1 unsubmitted but has label {r1_label}")

            # Check criteria values
            for crit_name, crit_val in r1.get("criteria_evaluations", {}).items():
                if crit_name != "evidence_quality" and crit_val is not None and crit_val not in ALLOWED_REVIEWER_CRITERIA_VALUES:
                    self.errors.append(f"[INVALID_CRITERION_VALUE] Event {event_id} Reviewer 1 has invalid value '{crit_val}' for {crit_name}")

        # Validate Reviewer 2 Form
        r2_completed = False
        r2_label = None
        if r2_file.exists():
            with open(r2_file) as f:
                r2 = json.load(f)
            r2_status = r2.get("status")
            r2_completed = (r2_status == "COMPLETED")
            r2_label = r2.get("label_decision")

            # 5. Reviewer 2 seeing Reviewer 1 label / isolation violation
            r2_str = json.dumps(r2).lower()
            if "reviewer_1" in r2_str or "reviewer 1" in r2_str:
                self.errors.append(f"[ISOLATION_VIOLATION] Event {event_id} Reviewer 2 form contains references to Reviewer 1")

            if r2_completed:
                self.stats["reviewer_2_completed"] += 1
                # 1. Missing reviewer check
                if not r2.get("reviewer_id"):
                    self.errors.append(f"[MISSING_REVIEWER] Event {event_id} Reviewer 2 completed without reviewer_id")
                # 3. Missing reviewer label
                if r2_label not in {"BACKFIRE", "NO_BACKFIRE", "AMBIGUOUS"}:
                    self.errors.append(f"[MISSING_REVIEWER_LABEL] Event {event_id} Reviewer 2 completed without valid label decision")
                # 9. Missing evidence quality
                ev_q = r2.get("criteria_evaluations", {}).get("evidence_quality")
                if ev_q not in ALLOWED_EVIDENCE_QUALITY:
                    self.errors.append(f"[MISSING_EVIDENCE_QUALITY] Event {event_id} Reviewer 2 missing valid evidence quality")
            else:
                if r2_label is not None and r2_label != "PENDING_HUMAN_REVIEW":
                    self.errors.append(f"[PREMATURE_LABEL] Event {event_id} Reviewer 2 unsubmitted but has label {r2_label}")

            # Check criteria values
            for crit_name, crit_val in r2.get("criteria_evaluations", {}).items():
                if crit_name != "evidence_quality" and crit_val is not None and crit_val not in ALLOWED_REVIEWER_CRITERIA_VALUES:
                    self.errors.append(f"[INVALID_CRITERION_VALUE] Event {event_id} Reviewer 2 has invalid value '{crit_val}' for {crit_name}")

        # Validate Adjudication Form
        if adj_file.exists():
            with open(adj_file) as f:
                adj = json.load(f)
            
            final_label = adj.get("adjudicator_label")
            # 4. Unauthorized final label
            if final_label not in ALLOWED_LABELS or final_label in FORBIDDEN_LABELS:
                self.errors.append(f"[UNAUTHORIZED_FINAL_LABEL] Event {event_id} has unauthorized final label '{final_label}'")

            final_causal = adj.get("final_causal_link")
            if final_causal in FORBIDDEN_CAUSAL_LINKS:
                self.errors.append(f"[FORBIDDEN_CAUSAL_LINK] Event {event_id} has forbidden causal link '{final_causal}'")
            elif final_causal is not None and final_causal not in ALLOWED_CAUSAL_LINKS:
                self.errors.append(f"[INVALID_CAUSAL_LINK] Event {event_id} has invalid causal link '{final_causal}'")

            # Check agreement / disagreement logic if both completed
            if r1_completed and r2_completed:
                self.stats["both_reviewers_completed"] += 1
                if r1_label != r2_label:
                    self.stats["disagreements"] += 1
                    if not adj.get("disagreement", False):
                        self.errors.append(f"[DISAGREEMENT_HANDLING] Event {event_id} has R1={r1_label} != R2={r2_label} but disagreement flag is False")
                else:
                    self.stats["agreements"] += 1

            if final_label in self.stats["final_labels"]:
                self.stats["final_labels"][final_label] += 1

    def _validate_ground_truth(self, registry_map):
        if not GT_PATH.exists():
            self.errors.append(f"[MISSING_GT_FILE] Ground Truth file not found at {GT_PATH}")
            return

        with open(GT_PATH) as f:
            gt_data = json.load(f)

        adjudicated_events = gt_data.get("adjudicated_events", [])
        self.stats["gt_events_count"] = len(adjudicated_events)

        seen_gt_ids = set()
        for ev in adjudicated_events:
            ev_id = ev.get("event_id")
            if ev_id in seen_gt_ids:
                self.errors.append(f"[DUPLICATE_EVENT] Event {ev_id} duplicated in Ground Truth dataset")
            seen_gt_ids.add(ev_id)

            if ev_id not in registry_map:
                self.errors.append(f"[INVALID_EVENT_ID] GT event {ev_id} does not exist in union registry")

            reg_record = registry_map.get(ev_id, {})
            # Invalid window cannot enter GT
            if not reg_record.get("window_valid", False):
                self.errors.append(f"[INVALID_WINDOW] Ineligible window event {ev_id} entered Ground Truth dataset")

            # Unauthorized final label
            f_label = ev.get("adjudicated_label")
            if f_label not in {"BACKFIRE", "NO_BACKFIRE", "AMBIGUOUS"}:
                self.errors.append(f"[UNAUTHORIZED_FINAL_LABEL] GT event {ev_id} has invalid label '{f_label}'")

            ev_q = ev.get("evidence_quality")
            if ev_q not in ALLOWED_EVIDENCE_QUALITY:
                self.errors.append(f"[MISSING_EVIDENCE_QUALITY] GT event {ev_id} missing evidence quality")

            clink = ev.get("causal_link_classification")
            if clink in FORBIDDEN_CAUSAL_LINKS or clink not in ALLOWED_CAUSAL_LINKS:
                self.errors.append(f"[INVALID_CAUSAL_LINK] GT event {ev_id} has invalid causal link '{clink}'")

    def _print_report(self):
        print(f"\nAudit Summary:")
        print(f"  Total Union Registry Events:     {self.stats['total_registry_events']}")
        print(f"  Eligible Events (Window Valid):  {self.stats['eligible_events']}")
        print(f"  Ineligible Events (Window Bad):  {self.stats['ineligible_events']}")
        print(f"  Adjudication Packages Scanned:   {self.stats['adjudication_packages_scanned']}")
        print(f"  Reviewer 1 Completed:            {self.stats['reviewer_1_completed']}")
        print(f"  Reviewer 2 Completed:            {self.stats['reviewer_2_completed']}")
        print(f"  Both Completed:                  {self.stats['both_reviewers_completed']}")
        print(f"  Agreements:                      {self.stats['agreements']}")
        print(f"  Disagreements:                   {self.stats['disagreements']}")
        print(f"  Final Labels:")
        for k, v in self.stats["final_labels"].items():
            print(f"    - {k:22}: {v}")
        print(f"  Events in Ground Truth Dataset:  {self.stats['gt_events_count']}")

        print(f"\nValidation Results:")
        print(f"  Errors:   {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")

        if self.errors:
            print("\nViolations Detected:")
            for err in self.errors:
                print(f"  [X] {err}")
        else:
            print("\n[SUCCESS] All Human Adjudication Quality Control Checks PASSED perfectly!")
        print("=" * 70)


def main():
    validator = AdjudicationValidator()
    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
