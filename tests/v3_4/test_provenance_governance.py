"""
tests/v3_4/test_provenance_governance.py
Governance and integrity unit tests for V3.4 provenance enforcement.

Validates that the provenance gate strictly rejects prohibited claims and enforces
NVIDIA PhysicalAI-SmartSpaces official documentation rules.
"""

import sys
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.v3_4.provenance_gate import (
    ProvenanceClass,
    validate_provenance_record,
    evaluate_gate,
)

class TestProvenanceGovernance(unittest.TestCase):

    def setUp(self):
        self.valid_wh026_record = {
            "dataset_name": "nvidia/PhysicalAI-SmartSpaces",
            "scene_id": "Warehouse_026",
            "provenance_class": "REAL_WORLD_TEST_CAPTURE",
            "authoritative_source": "NVIDIA Corporation",
            "source_url": "https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces",
            "acquisition_record": "data/external_facility/raw/Warehouse_026/nvidia_warehouse_026_provenance.json",
            "hash": "83ed232a2f5fe3031807ed19020e1a44fe386e89b68f9bea621797f1552c9cda",
            "gt_status": "WITHHELD_FOR_TEST_SCENES",
            "calibration_status": "DATASET_PROVIDED",
            "capture_type": "PHYSICAL_VIDEO_CAPTURE",
            "lux_telemetry_status": "NOT_AVAILABLE",
            "lux_value": None
        }

        self.valid_wh027_record = {
            "dataset_name": "nvidia/PhysicalAI-SmartSpaces",
            "scene_id": "Warehouse_027",
            "provenance_class": "REAL_WORLD_TEST_CAPTURE",
            "authoritative_source": "NVIDIA Corporation",
            "source_url": "https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces",
            "acquisition_record": "data/external_facility_02/metadata/warehouse_027_provenance.json",
            "hash": "abe39e20560a581e18ec0e72fc10cba7ff0f09a9dbd4ff51a44c5b3641b5b82a",
            "gt_status": "WITHHELD_FOR_TEST_SCENES",
            "calibration_status": "DATASET_PROVIDED",
            "capture_type": "PHYSICAL_VIDEO_CAPTURE",
            "lux_telemetry_status": "NOT_AVAILABLE",
            "lux_value": None
        }

    def test_01_canonical_wh026_wh027_pass(self):
        """Rule Verification: WH026 and WH027 pass when correctly classified as REAL_WORLD_TEST_CAPTURE."""
        p26, err26 = validate_provenance_record(self.valid_wh026_record)
        self.assertTrue(p26, f"Valid WH026 record failed: {err26}")

        p27, err27 = validate_provenance_record(self.valid_wh027_record)
        self.assertTrue(p27, f"Valid WH027 record failed: {err27}")

    def test_02_fail_if_wh026_classified_as_synthetic(self):
        """Rule 1: Gate must fail if Warehouse_026 is classified as SYNTHETIC."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["provenance_class"] = "SYNTHETIC"
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed with WH026 as SYNTHETIC")
        self.assertTrue(any("REAL_WORLD test capture" in e for e in errors))

    def test_03_fail_if_wh027_classified_as_synthetic(self):
        """Rule 2: Gate must fail if Warehouse_027 is classified as SYNTHETIC."""
        bad_rec = dict(self.valid_wh027_record)
        bad_rec["provenance_class"] = "SYNTHETIC"
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed with WH027 as SYNTHETIC")
        self.assertTrue(any("REAL_WORLD test capture" in e for e in errors))

    def test_04_fail_if_dataset_level_synthetic_inherited_blindly(self):
        """Rule 3: Gate must fail if dataset-level synthetic label is inherited blindly by scenes."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["blind_dataset_synthetic_inheritance"] = True
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed with blind synthetic inheritance")
        self.assertTrue(any("Dataset-level synthetic label cannot be applied blindly" in e for e in errors))

    def test_05_fail_if_calibration_labeled_physically_surveyed_without_evidence(self):
        """Rule 4: Gate must fail if calibration is claimed as physically surveyed without audit record."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["calibration_status"] = "PHYSICALLY_SURVEYED"
        bad_rec["survey_audit_record"] = None
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed with unverified physical survey claim")
        self.assertTrue(any("physically surveyed without independent survey audit" in e for e in errors))

    def test_06_fail_if_missing_lux_converted_to_zero(self):
        """Rule 5: Gate must fail if missing lux telemetry is converted to zero."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["lux_telemetry_status"] = "NOT_AVAILABLE"
        bad_rec["lux_value"] = 0
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed when missing lux was converted to 0")
        self.assertTrue(any("missing lux telemetry must not be converted to 0" in e for e in errors))

    def test_07_fail_if_detector_output_labeled_gt(self):
        """Rule 6: Gate must fail if detector outputs are labeled or used as Ground Truth."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["gt_source"] = "YOLOv8_MODEL_PREDICTIONS"
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed when YOLO was labeled as Ground Truth")
        self.assertTrue(any("detector output" in e for e in errors))

    def test_08_fail_if_industry_wide_claim_inferred_from_two_scenes(self):
        """Rule 7: Gate must fail if industry-wide claims are inferred from two test scenes."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["inferred_industry_wide_claim"] = True
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed with unwarranted industry-wide claim")
        self.assertTrue(any("Industry-wide warehouse claims cannot be inferred" in e for e in errors))

    def test_09_fail_if_old_incorrect_report_becomes_authoritative(self):
        """Rule 8: Gate must fail if old uncorrected report is designated as authoritative."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["authoritative_report_version"] = "V3_3_3_UNRESOLVED_OLD"
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed with old uncorrected report as authority")
        self.assertTrue(any("Old uncorrected report cannot serve as the authoritative baseline" in e for e in errors))

    def test_10_fail_if_unknown_provenance_proceeds_as_real_world(self):
        """Rule 9: Gate must fail if provenance is UNKNOWN but evaluation proceeds as REAL_WORLD."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["provenance_class"] = "UNKNOWN"
        bad_rec["evaluation_mode"] = "REAL_WORLD"
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed with UNKNOWN evaluated as REAL_WORLD")
        self.assertTrue(any("provenance is UNKNOWN but evaluation is attempting to proceed as REAL_WORLD" in e for e in errors))

    def test_11_fail_if_source_url_missing(self):
        """Rule 10: Gate must fail if provenance source URL is missing or invalid."""
        bad_rec = dict(self.valid_wh026_record)
        bad_rec["source_url"] = ""
        passed, errors = validate_provenance_record(bad_rec)
        self.assertFalse(passed, "Gate unexpectedly passed with missing source_url")
        self.assertTrue(any("source_url" in e for e in errors))

    def test_12_central_registry_gate_evaluation(self):
        """Verify that the official repository provenance registry passes all gate checks."""
        registry_path = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01/provenance/provenance_registry.json"
        self.assertTrue(registry_path.exists(), "Central provenance_registry.json does not exist")
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = []
        for s_id, s_info in data["scenes"].items():
            rec = dict(s_info)
            rec.setdefault("authoritative_source", "NVIDIA Corporation")
            rec.setdefault("acquisition_record", "data/external_facility/")
            rec.setdefault("hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
            rec.setdefault("gt_status", s_info.get("ground_truth_status", "WITHHELD"))
            rec.setdefault("calibration_status", s_info.get("calibration_status", "DATASET_PROVIDED"))
            rec.setdefault("capture_type", s_info.get("physical_capture_status", "PHYSICAL_VIDEO_CAPTURE"))
            records.append(rec)

        res = evaluate_gate(records)
        self.assertEqual(res["gate_status"], "PASS", f"Central registry failed gate evaluation: {res}")
        self.assertEqual(res["total_passed"], 3)
        self.assertEqual(res["total_failed"], 0)

if __name__ == "__main__":
    unittest.main()
