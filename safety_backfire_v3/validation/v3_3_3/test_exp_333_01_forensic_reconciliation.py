"""
validation/v3_3_3/test_exp_333_01_forensic_reconciliation.py
Integrity and regression test suite for EXP_333_01 forensic reconciliation and audit artifacts.
"""
import unittest
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

class TestEXP33301ForensicReconciliation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.exp_dir = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01"
        cls.analysis_dir = cls.exp_dir / "analysis"
        cls.reports_dir = cls.exp_dir / "reports"

        cls.obs_path = cls.analysis_dir / "observation_level_audit.json"
        cls.mh_path = cls.analysis_dir / "model_h_runtime_audit.json"
        cls.odd_path = cls.analysis_dir / "odd_classification_audit.json"
        cls.recon_path = cls.analysis_dir / "forensic_reconciliation.json"
        cls.report_path = cls.reports_dir / "EXP_333_01_ZERO_ADAPTATION_RECONCILED.md"

    def test_01_artifacts_exist(self):
        """Test 01: Verify all 5 required forensic reconciliation artifacts exist."""
        self.assertTrue(self.obs_path.exists(), "Missing observation_level_audit.json")
        self.assertTrue(self.mh_path.exists(), "Missing model_h_runtime_audit.json")
        self.assertTrue(self.odd_path.exists(), "Missing odd_classification_audit.json")
        self.assertTrue(self.recon_path.exists(), "Missing forensic_reconciliation.json")
        self.assertTrue(self.report_path.exists(), "Missing EXP_333_01_ZERO_ADAPTATION_RECONCILED.md")

    def test_02_observation_ledger_reconciliation(self):
        """Test 02: Verify observation ledger counts, strata sum, and units definitions."""
        with open(self.obs_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["total_frames_processed"], 173)
        self.assertEqual(data["total_detection_instances"], 251)
        self.assertEqual(data["by_class"]["forklift"], 238)
        self.assertEqual(data["by_class"]["person"], 13)

        strata = data["distance_strata"]
        self.assertEqual(strata["near_lt_4m"], 43)
        self.assertEqual(strata["mid_4_to_8m"], 201)
        self.assertEqual(strata["far_gt_8m"], 7)
        self.assertEqual(strata["sum_check"], 251)

        # Check units definition
        units = data["units_definition"]
        for required_unit in ["DETECTION_INSTANCE", "TRACK_INSTANCE", "FRAME_OBSERVATION", "UNIQUE_OBJECT", "TRAJECTORY"]:
            self.assertIn(required_unit, units)

        # Check ledger rows
        ledger = data["observation_ledger"]
        self.assertEqual(len(ledger), 251)
        first_row = ledger[0]
        for col in ["observation_id", "frame_id", "track_id", "class", "distance_m", "odd_group", "k", "occlusion"]:
            self.assertIn(col, first_row)

    def test_03_model_h_runtime_audit(self):
        """Test 03: Verify Model H runtime audit classification and term mismatches."""
        with open(self.mh_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["audit_classification"], "MODEL_H_BASELINE_INTEGRITY_FAILURE")
        mismatches = data["structural_mismatch_audit"]
        mismatch_terms = {m["term"]: m["status"] for m in mismatches}
        self.assertEqual(mismatch_terms["distance_scaling"], "MISMATCH")
        self.assertEqual(mismatch_terms["illumination_compensation"], "MISMATCH")
        self.assertEqual(mismatch_terms["camera_pitch_compensation"], "MISMATCH")

    def test_04_odd_classification_audit(self):
        """Test 04: Verify 9 ODD dimensions and overall UNKNOWN status."""
        with open(self.odd_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dims = data["dimensions_audit"]
        required_dims = [
            "camera_height_status", "pitch_status", "range_status", "floor_geometry_status",
            "illumination_status", "speed_status", "latency_status", "uncertainty_width_status",
            "identity_status"
        ]
        for rd in required_dims:
            self.assertIn(rd, dims)
            self.assertIn(dims[rd]["status"], ["IN_ODD", "OUT_OF_ODD", "UNKNOWN"])

        self.assertEqual(data["overall_odd_classification"], "UNKNOWN")

    def test_05_forensic_reconciliation_verdicts(self):
        """Test 05: Verify executive verdicts, 3 critical discrepancies, and final decision table."""
        with open(self.recon_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dec = data["final_decision_table"]
        self.assertEqual(dec["Baseline"], "PASS")
        self.assertEqual(dec["Runtime Model H"], "MISMATCH")
        self.assertEqual(dec["Observation ledger"], "CONSISTENT")
        self.assertEqual(dec["K-value reconciliation"], "FAIL")
        self.assertEqual(dec["Detection-count reconciliation"], "PASS")
        self.assertEqual(dec["ODD classification"], "UNKNOWN")
        self.assertEqual(dec["Ground truth"], "NOT_AVAILABLE")
        self.assertEqual(dec["Perception F1 gate"], "NOT_ESTABLISHED")
        self.assertEqual(dec["Zero-adaptation execution"], "COMPLETED_WITH_LIMITATIONS")
        self.assertEqual(dec["Cross-warehouse generalization"], "NOT_ESTABLISHED")
        self.assertEqual(dec["Critical discrepancies"], 3)
        self.assertEqual(dec["Model optimization performed"], "NO")
        self.assertEqual(dec["Next action"], "ACQUIRE_LONGER_EXTERNAL_DATASET")

if __name__ == "__main__":
    unittest.main()
