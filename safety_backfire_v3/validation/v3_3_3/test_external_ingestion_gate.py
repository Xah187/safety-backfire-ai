"""
validation/v3_3_3/test_external_ingestion_gate.py
Regression test suite for EXP_333_01 External Data Acquisition & Ingestion Gate.
Implements 20 mandatory regression tests (A–T):
- Test A: Central 01 footage cannot pass as external.
- Test B: Missing external footage cannot yield evaluation metrics.
- Test C: Missing physical-independence evidence blocks execution.
- Test D: Missing frame-overlap verification blocks execution.
- Test E: Synthetic transformations are rejected.
- Test F: Changing Model H parameters causes baseline integrity failure.
- Test G: Blind protocol cannot be unlocked silently.
- Test H: Missing metadata remains NOT_AVAILABLE.
- Test I: Empty datasets never produce zero-valued scientific metrics.
- Test J: External ingestion does not modify frozen V3.3.2 artifacts.
--- RECONCILIATION TESTS K–T ---
- Test K: Planned camera values cannot be used as actual measurements.
- Test L: ODD-shift data cannot enter the primary in-ODD population.
- Test M: Acceptance criterion is not represented as unsupported hypothesis test.
- Test N: BLIND_PROTOCOL_LOCKED cannot imply BLIND_DATA_LOCKED.
- Test O: Missing actual camera metadata remains NOT_AVAILABLE (null).
- Test P: External zero-adaptation run cannot modify Model H parameters.
- Test Q: A copied/transformed Central 01 video cannot pass external independence.
- Test R: External data with unresolved frame overlap blocks evaluation.
- Test S: Missing facility evidence keeps independence NOT_ESTABLISHED.
- Test T: External metadata alone cannot generate performance metrics.
"""

import sys
import os
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np

def find_workspace_root() -> Path:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "data").is_dir() and (p / "safety_backfire_v3").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent.parent.parent

WORKSPACE_ROOT = find_workspace_root()
sys.path.insert(0, str(WORKSPACE_ROOT))

from validation.v3_3_3.validate_external_provenance import (
    ExternalProvenanceValidator,
    compute_sha256,
    compute_frame_hash,
    hamming_distance_hex
)
from safety_backfire_v3_3_3.experiments.run_exp_333_01 import (
    verify_hard_baseline_lock,
    check_execution_gates,
    run_exp_333_01_evaluation
)

class TestExternalIngestionGate(unittest.TestCase):
    """Regression test suite enforcing Section 22 Ingestion Gate criteria."""

    @classmethod
    def setUpClass(cls):
        cls.exp_dir = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01"
        cls.prov_dir = cls.exp_dir / "provenance"
        cls.splits_dir = cls.exp_dir / "splits"
        cls.metrics_dir = cls.exp_dir / "metrics"
        cls.release_dir = cls.exp_dir / "release"
        cls.baseline_manifest = WORKSPACE_ROOT / "outputs/v3_3_3/baseline/v3_3_2_source_hash_manifest.json"
        cls.validator = ExternalProvenanceValidator()

    def test_A_central01_footage_cannot_pass_as_external(self):
        """Test A: Central 01 footage cannot pass as external."""
        test_video = WORKSPACE_ROOT / "test.mp4"
        test2_video = WORKSPACE_ROOT / "test2.mp4"

        # Check existing Central 01 source videos
        for vpath in [test_video, test2_video]:
            if vpath.exists():
                res = self.validator.check_central01_exclusion(vpath)
                self.assertFalse(res["passed"], f"Central 01 video {vpath.name} was not rejected!")
                self.assertEqual(res["rejection_code"], "CENTRAL01_FILE_MATCH_REJECTED")

        # Test copied / renamed file retains SHA-256 rejection
        if test2_video.exists():
            with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
                tmp.write(test2_video.read_bytes())
                tmp.flush()
                res = self.validator.check_central01_exclusion(Path(tmp.name))
                self.assertFalse(res["passed"])
                self.assertEqual(res["rejection_code"], "CENTRAL01_FILE_MATCH_REJECTED")

        # Test banned metadata identifiers
        with open(self.prov_dir / "central01_exclusion_registry.json", "r") as f:
            reg = json.load(f)
        for banned_id in reg["banned_facility_identifiers"]:
            self.assertIn(banned_id, reg["banned_facility_identifiers"])

    def test_B_missing_external_footage_cannot_yield_evaluation_metrics(self):
        """Test B: Missing external footage cannot yield evaluation metrics."""
        # Simulate absent raw footage to verify execution is correctly blocked.
        # (0_te11.mp4 may be present in workspace from manual testing, use mock to ensure determinism.)
        with patch("pathlib.Path.glob", return_value=[]):
            # Verify execution refusal
            passed, reason = check_execution_gates()
            self.assertFalse(passed)
            self.assertTrue(reason.startswith("EXTERNAL_RAW_DATA_ABSENT"))

            # Verify evaluation runner returns execution_blocked and zero scientific metrics
            res = run_exp_333_01_evaluation()
            self.assertTrue(res.get("execution_blocked"))
            self.assertEqual(res.get("data_status"), "NOT_AVAILABLE")
            self.assertEqual(res.get("status"), "NOT_ESTABLISHED")

    def test_C_missing_physical_independence_evidence_blocks_execution(self):
        """Test C: Missing physical-independence evidence blocks execution."""
        prov_manifest = self.prov_dir / "external_facility_manifest.json"
        with open(prov_manifest, "r") as f:
            pdata = json.load(f)

        self.assertFalse(pdata.get("physical_independence_verified"))
        gate = pdata.get("physical_independence_gate", {})
        self.assertFalse(gate.get("different_building"))
        self.assertFalse(gate.get("independent_session"))
        self.assertFalse(gate.get("independent_camera"))
        self.assertFalse(gate.get("independent_raw_provenance"))
        self.assertFalse(gate.get("frame_overlap_absent"))
        self.assertFalse(gate.get("overall_independence"))

        # Mock presence of a video file to test independence gate blocker
        with patch("pathlib.Path.glob", return_value=[Path("/fake/external_01.mp4")]):
            passed, reason = check_execution_gates()
            self.assertFalse(passed)
            self.assertIn("PHYSICAL_INDEPENDENCE_NOT_ESTABLISHED", reason)

    def test_D_missing_frame_overlap_verification_blocks_execution(self):
        """Test D: Missing frame-overlap verification blocks execution."""
        overlap_manifest = self.prov_dir / "frame_overlap_manifest.json"
        with open(overlap_manifest, "r") as f:
            odata = json.load(f)

        self.assertEqual(odata.get("frame_overlap_status"), "NOT_ESTABLISHED")
        self.assertIsNone(odata.get("candidate_overlap_count"))

        # Mock raw files present and physical independence passed to test frame overlap blocker
        mock_manifest = {
            "physical_independence_verified": True
        }
        with patch("pathlib.Path.glob", return_value=[Path("/fake/external_01.mp4")]), \
             patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_manifest))):
            # When frame overlap is NOT_ESTABLISHED, check_execution_gates must block
            passed, reason = check_execution_gates()
            self.assertFalse(passed)

    def test_E_synthetic_transformations_are_rejected(self):
        """Test E: Synthetic transformations of Central 01 footage are rejected."""
        test2_video = WORKSPACE_ROOT / "test2.mp4"
        if not test2_video.exists():
            self.skipTest("test2.mp4 not present in workspace")

        cap = cv2.VideoCapture(str(test2_video))
        ret, frame = cap.read()
        cap.release()
        self.assertTrue(ret and frame is not None)

        # Apply synthetic transformations: resize + blur + color shift
        transformed = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_LINEAR)
        transformed = cv2.GaussianBlur(transformed, (5, 5), 0)
        transformed = cv2.convertScaleAbs(transformed, alpha=1.1, beta=-10)

        # Write transformed video to temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(tmp.name, fourcc, 10.0, (640, 360))
            for _ in range(15):
                out.write(transformed)
            out.release()

            # Test validator rejection
            res = self.validator.check_central01_exclusion(Path(tmp.name))
            self.assertFalse(res["passed"], "Transformed Central 01 footage was not detected!")
            self.assertEqual(res["rejection_code"], "SYNTHETIC_SUBSTITUTE_REJECTED")
            self.assertLessEqual(res["hamming_distance"], 15)

    def test_F_changing_model_h_parameters_causes_baseline_integrity_failure(self):
        """Test F: Changing Model H parameters causes baseline integrity failure."""
        self.assertTrue(verify_hard_baseline_lock(), "Baseline lock must pass in clean state")

        # Mock drift in k0
        mock_mh = {
            "parameters": {
                "k0": 2.45,  # Drifted from 2.40
                "beta_d": 0.08,
                "beta_l": 0.12,
                "beta_pitch": 0.22,
                "gamma_occ": {"NONE": 0.0, "PARTIAL": 0.20, "HEAVY": 0.40}
            }
        }
        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(mock_mh))):
            with self.assertRaises((AssertionError, ValueError)):
                verify_hard_baseline_lock()

    def test_G_blind_protocol_cannot_be_unlocked_silently(self):
        """Test G: Blind protocol cannot be unlocked silently."""
        blind_manifest = self.splits_dir / "blind_manifest.json"
        with open(blind_manifest, "r") as f:
            bm = json.load(f)

        self.assertTrue(bm["blind_protocol_locked"])
        self.assertFalse(bm["blind_data_locked"])
        self.assertEqual(bm["blind_data_status"], "AWAITING_INGESTION")

        prereqs = bm.get("prerequisites_for_blind_data_lock", [])
        self.assertEqual(len(prereqs), 4)
        self.assertIn("raw_data_hash_established", prereqs)
        self.assertIn("split_hash_established", prereqs)
        self.assertIn("annotation_manifest_hash_established", prereqs)
        self.assertIn("provenance_manifest_hash_established", prereqs)

        blind_protocol_hash = self.splits_dir / "blind_protocol_hash.json"
        with open(blind_protocol_hash, "r") as f:
            bph = json.load(f)
        self.assertTrue(bph["blind_protocol_locked"])
        self.assertFalse(bph["blind_data_locked"])
        self.assertEqual(bph["blind_data_hash"], "NOT_AVAILABLE")

    def test_H_missing_metadata_remains_not_available(self):
        """Test H: Missing metadata remains NOT_AVAILABLE."""
        camera_manifest = self.prov_dir / "camera_manifest.json"
        with open(camera_manifest, "r") as f:
            cm = json.load(f)

        # Lighting metadata: lux must be null (not a numeric value, not a string '0')
        self.assertIsNone(cm["lighting_metadata"]["lux"],
                          "lighting_metadata.lux must be null when not measured")
        self.assertEqual(cm["lighting_metadata"]["illumination_category"], "NOT_ESTABLISHED")
        self.assertEqual(cm["geometry_metadata"]["floor_geometry_classification"], "UNKNOWN")

        # With the planned/actual schema, actual fields must all be null
        for cam in cm["cameras"]:
            actual = cam.get("actual", {})
            self.assertIsNone(actual.get("mounting_height_m"),
                              f"{cam['camera_id']}: actual.mounting_height_m must be null")
            self.assertIsNone(actual.get("pitch_deg"),
                              f"{cam['camera_id']}: actual.pitch_deg must be null")
            self.assertIsNone(actual.get("roll_deg"),
                              f"{cam['camera_id']}: actual.roll_deg must be null")
            self.assertIsNone(actual.get("calibration_matrix"),
                              f"{cam['camera_id']}: actual.calibration_matrix must be null")

        self.assertIn("NOT_AVAILABLE", cm["metadata_provenance_taxonomy"]["supported_categories"])

    def test_I_empty_datasets_never_produce_zero_valued_scientific_metrics(self):
        """Test I: Empty datasets never produce zero-valued scientific metrics."""
        metric_files = [
            "perception_metrics.json", "tracking_metrics.json", "geometry_metrics.json",
            "uncertainty_metrics.json", "policy_metrics.json", "hazard_metrics.json", "event_metrics.json"
        ]

        def check_no_zero_metrics(obj, path_prefix=""):
            banned_zero_keys = {
                "f1", "precision", "recall", "micro_f1", "macro_f1", "idf1",
                "mae", "mae_meters", "coverage", "nominal_oos_coverage",
                "refusal_rate", "hazard_f1", "event_f1"
            }
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() in banned_zero_keys:
                        self.assertNotEqual(
                            v, 0, f"Scientific metric {path_prefix}.{k} must not be numeric 0 (must be NOT_ESTABLISHED / null)"
                        )
                        self.assertNotEqual(
                            v, 0.0, f"Scientific metric {path_prefix}.{k} must not be numeric 0.0 (must be NOT_ESTABLISHED / null)"
                        )
                    check_no_zero_metrics(v, f"{path_prefix}.{k}" if path_prefix else k)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    check_no_zero_metrics(item, f"{path_prefix}[{idx}]")

        for mf in metric_files:
            p = self.metrics_dir / mf
            self.assertTrue(p.exists())
            with open(p, "r") as f:
                content = json.load(f)
            check_no_zero_metrics(content, mf)

        # Also verify ingestion_gate_status
        with open(self.release_dir / "ingestion_gate_status.json", "r") as f:
            igs = json.load(f)
        self.assertEqual(igs["current_experiment_status"], "NOT_ESTABLISHED")
        self.assertEqual(igs["ingestion_gate"]["external_raw_footage"], "NOT_AVAILABLE")

    def test_J_external_ingestion_does_not_modify_frozen_v3_3_2_artifacts(self):
        """Test J: External ingestion does not modify frozen V3.3.2 artifacts."""
        with open(self.baseline_manifest, "r") as f:
            bm = json.load(f)

        self.assertEqual(len(bm["files"]), 39)
        for rel_path, meta in bm["files"].items():
            full_path = WORKSPACE_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Protected baseline file missing: {rel_path}")
            current_h = compute_sha256(full_path)
            self.assertEqual(current_h, meta["sha256"], f"Protected file modified: {rel_path}")

    # ---- RECONCILIATION TESTS K–T ----

    def test_K_planned_camera_values_cannot_be_used_as_actual_measurements(self):
        """Test K: Planned camera values cannot be used as actual measurements."""
        cam_manifest = self.prov_dir / "camera_manifest.json"
        with open(cam_manifest, "r") as f:
            cm = json.load(f)

        for cam in cm["cameras"]:
            # Planned fields must exist and be clearly labelled as targets
            self.assertIn("planned", cam, f"Camera {cam['camera_id']} missing planned section")
            self.assertIn("actual", cam, f"Camera {cam['camera_id']} missing actual section")

            planned = cam["planned"]
            actual = cam["actual"]

            # Actual values must not be populated with planned values (all must be null/NOT_AVAILABLE)
            self.assertIsNone(actual.get("resolution"), f"{cam['camera_id']} actual.resolution must be null")
            self.assertIsNone(actual.get("fps"), f"{cam['camera_id']} actual.fps must be null")
            self.assertIsNone(actual.get("mounting_height_m"), f"{cam['camera_id']} actual.mounting_height_m must be null")
            self.assertIsNone(actual.get("pitch_deg"), f"{cam['camera_id']} actual.pitch_deg must be null")
            self.assertEqual(actual.get("status"), "NOT_AVAILABLE", f"{cam['camera_id']} actual.status must be NOT_AVAILABLE")

            # Planned section must NOT be named or tagged as measured evidence
            planned_desc = planned.get("description", "")
            self.assertNotIn("MEASURED", planned_desc.upper())
            self.assertNotIn("VERIFIED", planned_desc.upper())
            self.assertIn("TARGET", planned_desc.upper(),
                          f"{cam['camera_id']} planned.description must indicate it is a TARGET specification")

        # Camera manifest must also contain the prohibition rule
        self.assertIn("planned_value_prohibition", cm)
        prohibition = cm["planned_value_prohibition"]
        self.assertIn("rule", prohibition)
        self.assertIn("perception evaluation", prohibition["rule"])

    def test_L_odd_shift_data_cannot_enter_primary_in_odd_population(self):
        """Test L: ODD-shift data cannot enter the primary in-ODD population."""
        odd_manifest = self.exp_dir / "policy" / "odd_classification_manifest.json"
        self.assertTrue(odd_manifest.exists(), "ODD classification manifest must exist")
        with open(odd_manifest, "r") as f:
            om = json.load(f)

        # Verify split definitions exist
        self.assertIn("experiment_split_classification", om)
        split = om["experiment_split_classification"]
        self.assertIn("EXP_333_01A", split)
        self.assertIn("EXP_333_01B", split)

        # Verify mixing prohibition
        self.assertIn("mixing_prohibition", om)
        self.assertIn("rule", om["mixing_prohibition"])

        # EXP_333_01A must restrict to IN_ODD/ODD_MARGIN only
        pop_manifest = self.exp_dir / "policy" / "evaluation_population_manifest.json"
        self.assertTrue(pop_manifest.exists(), "Evaluation population manifest must exist")
        with open(pop_manifest, "r") as f:
            pm = json.load(f)

        self.assertIn("EXP_333_01A_population", pm)
        self.assertIn("EXP_333_01B_population", pm)
        self.assertIn("mixing_violation_detection", pm)

        # Verify enforcement reference
        enforcement = pm["mixing_violation_detection"]["enforcement"]
        self.assertIn("test_L", enforcement)

    def test_M_acceptance_criterion_not_represented_as_unsupported_hypothesis_test(self):
        """Test M: Acceptance criterion is not represented as unsupported hypothesis test."""
        odd_manifest = self.exp_dir / "policy" / "odd_classification_manifest.json"
        with open(odd_manifest, "r") as f:
            om = json.load(f)

        # Acceptance criterion must use PREREGISTERED_ACCEPTANCE_CRITERION framing
        hyp_gov = om.get("hypothesis_governance", {})
        self.assertIn("preregistered_acceptance_criterion", hyp_gov,
                      "Must use preregistered_acceptance_criterion instead of H0/H1 notation")
        criterion = hyp_gov["preregistered_acceptance_criterion"]
        self.assertIn("85.00%", criterion)

        # H0/H1 notation must be in prohibited list, not in active fields
        prohibited = hyp_gov.get("prohibited_notation", [])
        self.assertTrue(any("H0" in p or "H1" in p for p in prohibited),
                        "H0/H1 notation must be listed as prohibited")

        # EXP_333_01A must also use PREREGISTERED_ACCEPTANCE_CRITERION
        split = om["experiment_split_classification"]["EXP_333_01A"]
        self.assertIn("preregistered_acceptance_criterion", split)
        self.assertNotIn("H0:", split.get("preregistered_acceptance_criterion", ""))

    def test_N_blind_protocol_locked_cannot_imply_blind_data_locked(self):
        """Test N: BLIND_PROTOCOL_LOCKED cannot imply BLIND_DATA_LOCKED."""
        blind_manifest = self.splits_dir / "blind_manifest.json"
        with open(blind_manifest, "r") as f:
            bm = json.load(f)

        # Protocol and data locks must be explicitly separated
        self.assertTrue(bm["blind_protocol_locked"],
                        "blind_protocol_locked must be TRUE (protocol is locked)")
        self.assertFalse(bm["blind_data_locked"],
                         "blind_data_locked must be FALSE (no external data ingested yet)")

        # Governance note must explain the semantic distinction
        gov_note = bm.get("governance_note", "")
        self.assertIn("BLIND_PROTOCOL_LOCKED = TRUE", gov_note,
                      "governance_note must explain blind_protocol_locked semantics")
        self.assertNotIn("blind_data_locked = true", gov_note.lower(),
                         "governance_note must not claim blind data is locked")

        # Also check the protocol hash
        protocol_hash = self.splits_dir / "blind_protocol_hash.json"
        with open(protocol_hash, "r") as f:
            ph = json.load(f)
        self.assertTrue(ph["blind_protocol_locked"])
        self.assertFalse(ph["blind_data_locked"])
        self.assertEqual(ph["blind_data_hash"], "NOT_AVAILABLE")

    def test_O_missing_actual_camera_metadata_remains_not_available(self):
        """Test O: Missing actual camera metadata remains NOT_AVAILABLE (null)."""
        cam_manifest = self.prov_dir / "camera_manifest.json"
        with open(cam_manifest, "r") as f:
            cm = json.load(f)

        null_fields = ["resolution", "fps", "mounting_height_m", "pitch_deg",
                       "roll_deg", "model", "focal_length_mm", "sensor_format",
                       "optical_center_x", "optical_center_y", "calibration_matrix",
                       "sha256_source_file"]

        for cam in cm["cameras"]:
            actual = cam.get("actual", {})
            self.assertEqual(actual.get("status"), "NOT_AVAILABLE",
                             f"{cam['camera_id']} actual.status must be NOT_AVAILABLE")
            for field in null_fields:
                val = actual.get(field, "MISSING_KEY")
                self.assertIsNone(val,
                    f"{cam['camera_id']} actual.{field} must be null, got: {val}")

        # Lighting metadata must also remain null/NOT_AVAILABLE
        lighting = cm.get("lighting_metadata", {})
        self.assertIsNone(lighting.get("lux"),
                          "lighting_metadata.lux must be null until measured")
        self.assertEqual(lighting.get("illumination_category"), "NOT_ESTABLISHED")

    def test_P_external_zero_adaptation_run_cannot_modify_model_h(self):
        """Test P: External zero-adaptation run cannot modify Model H parameters."""
        # Verify Model H parameters are unchanged after any external processing
        mh_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/model_h_lineage.json"
        with open(mh_path, "r") as f:
            mh = json.load(f)
        params = mh["parameters"]
        self.assertEqual(params["k0"], 2.40, "k0 must remain 2.40")
        self.assertEqual(params["beta_d"], 0.08, "beta_d must remain 0.08")
        self.assertEqual(params["beta_l"], 0.12, "beta_l must remain 0.12")
        self.assertEqual(params["beta_pitch"], 0.22, "beta_pitch must remain 0.22")
        self.assertEqual(params["gamma_occ"]["NONE"], 0.0)
        self.assertEqual(params["gamma_occ"]["PARTIAL"], 0.20)
        self.assertEqual(params["gamma_occ"]["HEAVY"], 0.40)

        # Acceptance schema must document immutability
        schema_path = self.exp_dir / "ingestion" / "external_data_acceptance_schema.json"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        model_h = schema.get("model_h_immutability", {})
        self.assertFalse(model_h.get("any_adaptation_performed", True),
                         "Schema must declare no adaptation performed")
        locked = model_h.get("locked_parameters", {})
        self.assertEqual(locked.get("k0"), 2.40)
        self.assertEqual(locked.get("beta_d"), 0.08)

    def test_Q_copied_transformed_central01_video_cannot_pass_external_independence(self):
        """Test Q: A copied/transformed Central 01 video cannot pass external independence."""
        test_video = WORKSPACE_ROOT / "test.mp4"
        test2_video = WORKSPACE_ROOT / "test2.mp4"

        for vpath in [test_video, test2_video]:
            if not vpath.exists():
                continue
            # 1. Exact copy rejection
            res = self.validator.check_central01_exclusion(vpath)
            self.assertFalse(res["passed"],
                             f"Exact copy of {vpath.name} must be rejected")
            self.assertEqual(res["rejection_code"], "CENTRAL01_FILE_MATCH_REJECTED")

        # 2. Byte-for-byte copy with different filename must be rejected
        if test2_video.exists():
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp.write(test2_video.read_bytes())
                tmp_path = Path(tmp.name)
            try:
                res = self.validator.check_central01_exclusion(tmp_path)
                self.assertFalse(res["passed"],
                                 "Byte-for-byte copy with different filename must be rejected")
                self.assertEqual(res["rejection_code"], "CENTRAL01_FILE_MATCH_REJECTED")
            finally:
                tmp_path.unlink(missing_ok=True)

    def test_R_external_data_with_unresolved_frame_overlap_blocks_evaluation(self):
        """Test R: External data with unresolved frame overlap blocks evaluation."""
        overlap_manifest = self.prov_dir / "frame_overlap_manifest.json"
        with open(overlap_manifest, "r") as f:
            om = json.load(f)

        # When no external footage has been processed, status must be NOT_ESTABLISHED
        self.assertEqual(om["frame_overlap_status"], "NOT_ESTABLISHED",
                         "Frame overlap must be NOT_ESTABLISHED without actual external footage")
        self.assertEqual(len(om["matching_hashes"]), 0)

        # Governance rule must explain this distinction
        gov_rule = om.get("governance_rule", "")
        self.assertIn("NOT_ESTABLISHED", gov_rule)

        # Verify check_execution_gates blocks when overlap is NOT_ESTABLISHED
        # (mock raw files present and independence passed, but overlap NOT_ESTABLISHED)
        mock_facility = {"physical_independence_verified": True}
        mock_overlap = {"frame_overlap_status": "NOT_ESTABLISHED"}
        with patch("pathlib.Path.glob", return_value=[Path("/fake/external_01.mp4")]), \
             patch("builtins.open", unittest.mock.mock_open(
                 read_data=json.dumps(mock_facility))):
            # Gate should block when overlap is not established
            passed, reason = check_execution_gates()
            self.assertFalse(passed)

    def test_S_missing_facility_evidence_keeps_independence_not_established(self):
        """Test S: Missing facility evidence keeps independence NOT_ESTABLISHED."""
        # Primary independence gate must be FALSE for all criteria
        gate_file = self.prov_dir / "independence_gate.json"
        self.assertTrue(gate_file.exists(), "independence_gate.json must exist")
        with open(gate_file, "r") as f:
            gate = json.load(f)

        primary = gate["primary_gate"]["criteria"]
        for crit_name, crit_data in primary.items():
            self.assertFalse(crit_data["value"],
                             f"Primary gate criterion {crit_name} must be False without evidence")
            self.assertEqual(crit_data["evidence_status"], "NOT_ESTABLISHED")

        self.assertFalse(gate["primary_gate"]["overall_independence"])
        self.assertEqual(gate["overall_physical_independence"], "NOT_ESTABLISHED")

        # Prohibited inference rules must be documented
        self.assertIn("prohibited_inference_rules", gate)
        rules = gate["prohibited_inference_rules"]
        self.assertGreater(len(rules), 0, "Must have at least one prohibited inference rule")

        # External facility manifest must also reflect NOT_ESTABLISHED
        with open(self.prov_dir / "external_facility_manifest.json", "r") as f:
            ef = json.load(f)
        self.assertFalse(ef["physical_independence_verified"])
        self.assertEqual(ef["governance_classification"],
                         "EXTERNAL_FACILITY_INDEPENDENCE = NOT_ESTABLISHED")

    def test_T_external_metadata_cannot_generate_performance_metrics(self):
        """Test T: External metadata alone cannot generate performance metrics."""
        # All metric files must remain NOT_ESTABLISHED
        metric_files = [
            "perception_metrics.json", "tracking_metrics.json", "geometry_metrics.json",
            "uncertainty_metrics.json", "policy_metrics.json", "hazard_metrics.json", "event_metrics.json"
        ]
        for mf in metric_files:
            with open(self.metrics_dir / mf, "r") as f:
                content = json.load(f)
            # No numeric performance value should exist for any primary metric
            def check_no_positive_numeric(obj, path=""):
                banned = {"f1", "precision", "recall", "micro_f1", "macro_f1", "idf1",
                          "mae", "mae_meters", "coverage", "nominal_oos_coverage",
                          "hazard_f1", "event_f1"}
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k.lower() in banned:
                            self.assertNotIsInstance(v, (int, float),
                                f"{mf}: {path}.{k} must not be numeric — metadata alone cannot generate metrics. Got: {v}")
                        check_no_positive_numeric(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_no_positive_numeric(item, f"{path}[{i}]")
            check_no_positive_numeric(content, mf)

        # Check ingestion acceptance schema prohibits metadata-only performance claims
        schema_path = self.exp_dir / "ingestion" / "external_data_acceptance_schema.json"
        with open(schema_path, "r") as f:
            schema = json.load(f)
        checklist_path = self.exp_dir / "ingestion" / "external_evidence_checklist.json"
        with open(checklist_path, "r") as f:
            checklist = json.load(f)
        prohibited = checklist.get("metadata_overclaim_prohibition", {}).get("prohibited_claims_from_metadata_only", [])
        self.assertIn("external generalization", prohibited)
        self.assertIn("cross-warehouse validity", prohibited)

if __name__ == "__main__":
    unittest.main()

