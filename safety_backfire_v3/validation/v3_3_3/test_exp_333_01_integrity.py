"""
validation/v3_3_3/test_exp_333_01_integrity.py
Unit test suite verifying integrity, provenance, and governance gates for EXP_333_01 External Facility Generalization Gate.
"""

import sys
import json
import hashlib
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

def compute_sha256(fp: Path) -> str:
    hasher = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class TestEXP33301Integrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.exp_dir = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01"
        cls.prov_dir = cls.exp_dir / "provenance"
        cls.splits_dir = cls.exp_dir / "splits"
        cls.metrics_dir = cls.exp_dir / "metrics"
        cls.analysis_dir = cls.exp_dir / "analysis"
        cls.reports_dir = cls.exp_dir / "reports"
        cls.release_dir = cls.exp_dir / "release"
        cls.baseline_manifest_path = WORKSPACE_ROOT / "outputs/v3_3_3/baseline/v3_3_2_source_hash_manifest.json"
        cls.release_decision_path = WORKSPACE_ROOT / "outputs/v3_3_3/release_decision.json"

    def test_01_hard_baseline_lock(self):
        """Test 01: Verify V3.3.2 baseline remains 100% frozen with zero hash drift."""
        with open(self.release_decision_path, "r", encoding="utf-8") as f:
            rd = json.load(f)
        self.assertEqual(rd["v3_3_2_reconciled_status"], "V3.3.2_FINAL_RECONCILED")
        self.assertEqual(rd["reconciliation_gate"], "FULL_RECONCILIATION_PASSED")
        self.assertEqual(rd["active_unsupported_claims"], 0)

        with open(self.baseline_manifest_path, "r", encoding="utf-8") as f:
            bm = json.load(f)
        for fpath, meta in bm["files"].items():
            full_p = WORKSPACE_ROOT / fpath
            self.assertTrue(full_p.exists(), f"Protected baseline file missing: {fpath}")
            current_h = compute_sha256(full_p)
            self.assertEqual(current_h, meta["sha256"], f"Baseline hash drift in {fpath}")

        # Verify locked Model H parameters
        mh_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/model_h_lineage.json"
        with open(mh_path, "r", encoding="utf-8") as f:
            mh = json.load(f)
        self.assertEqual(mh["parameters"]["k0"], 2.40)
        self.assertEqual(mh["parameters"]["beta_d"], 0.08)
        self.assertEqual(mh["parameters"]["beta_l"], 0.12)
        self.assertEqual(mh["parameters"]["beta_pitch"], 0.22)
        self.assertEqual(mh["parameters"]["gamma_occ"], {"NONE": 0.0, "PARTIAL": 0.20, "HEAVY": 0.40})

    def test_02_exp_333_01_provenance_manifests(self):
        """Test 02: Verify all 4 provenance manifests exist and enforce NOT_ESTABLISHED independence."""
        prov_files = [
            "external_facility_manifest.json",
            "camera_manifest.json",
            "acquisition_manifest.json",
            "integrity_hash_manifest.json"
        ]
        for pf in prov_files:
            p = self.prov_dir / pf
            self.assertTrue(p.exists(), f"Missing provenance manifest: {pf}")

        with open(self.prov_dir / "external_facility_manifest.json", "r", encoding="utf-8") as f:
            ef = json.load(f)
        if ef.get("raw_video_available", False):
            self.assertTrue(ef["raw_video_available"])
            self.assertIn("DATA_VOLUME_LIMITATION", ef["governance_classification"])
        else:
            self.assertFalse(ef["raw_video_available"])
            self.assertEqual(ef["governance_classification"], "EXTERNAL_FACILITY_INDEPENDENCE = NOT_ESTABLISHED")
        self.assertEqual(ef["limitation_classification"], "DATA_VOLUME_LIMITATION")

    def test_03_zero_adaptation_split_and_blind_quarantine(self):
        """Test 03: Verify split manifest enforces zero-adaptation and blind quarantine is locked."""
        split_p = self.splits_dir / "split_manifest.json"
        blind_m_p = self.splits_dir / "blind_manifest.json"
        blind_h_p = self.splits_dir / "blind_hash.json"
        self.assertTrue(split_p.exists())
        self.assertTrue(blind_m_p.exists())
        self.assertTrue(blind_h_p.exists())

        with open(split_p, "r", encoding="utf-8") as f:
            sm = json.load(f)
        self.assertEqual(sm["zero_adaptation_pipeline"]["parameter_adaptation"], "ZERO_PARAMETER_ADAPTATION")
        self.assertEqual(sm["zero_adaptation_pipeline"]["primary_reported_result"], "ZERO_ADAPTATION_EXTERNAL_OOS")

        with open(blind_m_p, "r", encoding="utf-8") as f:
            bm = json.load(f)
        self.assertTrue(bm["blind_locked"])
        self.assertTrue(bm["quarantine_rules"]["prohibit_threshold_tuning"])

    def test_04_metrics_and_analysis_artifacts_integrity(self):
        """Test 04: Verify all 7 metric files and 4 analysis files exist and reflect NOT_ESTABLISHED."""
        metric_files = [
            "perception_metrics.json", "tracking_metrics.json", "geometry_metrics.json",
            "uncertainty_metrics.json", "policy_metrics.json", "hazard_metrics.json", "event_metrics.json"
        ]
        for mf in metric_files:
            p = self.metrics_dir / mf
            self.assertTrue(p.exists(), f"Missing metric file: {mf}")

        analysis_files = [
            "stratified_analysis.json", "failure_taxonomy.json", "red_team_results.json", "statistical_analysis.json"
        ]
        for af in analysis_files:
            p = self.analysis_dir / af
            self.assertTrue(p.exists(), f"Missing analysis file: {af}")

    def test_05_red_team_stress_scenarios(self):
        """Test 05: Verify all 10 red team stress fixtures are preregistered."""
        with open(self.analysis_dir / "red_team_results.json", "r", encoding="utf-8") as f:
            rt = json.load(f)
        self.assertEqual(len(rt["scenarios"]), 10)
        self.assertEqual(rt["total_red_team_scenarios"], 10)

    def test_06_failure_taxonomy_classification(self):
        """Test 06: Verify failure is classified as DATA_PROVENANCE and not model failure."""
        with open(self.analysis_dir / "failure_taxonomy.json", "r", encoding="utf-8") as f:
            ft = json.load(f)
        self.assertEqual(ft["summary"]["primary_category_breakdown"]["DATA_PROVENANCE"], 1)
        self.assertEqual(ft["summary"]["primary_category_breakdown"]["PERCEPTION"], 0)

    def test_07_report_24_sections(self):
        """Test 07: Verify EXP_333_01_EXTERNAL_FACILITY_REPORT.md contains all 24 numbered sections."""
        report_p = self.reports_dir / "EXP_333_01_EXTERNAL_FACILITY_REPORT.md"
        self.assertTrue(report_p.exists())
        with open(report_p, "r", encoding="utf-8") as f:
            text = f.read()

        for sec_num in range(1, 25):
            expected_header = f"## {sec_num}."
            self.assertIn(expected_header, text, f"Missing section header: {expected_header}")

        self.assertTrue("EXTERNAL_FACILITY_INDEPENDENCE = NOT_ESTABLISHED" in text or "EXTERNAL\\_FACILITY\\_INDEPENDENCE = NOT\\_ESTABLISHED" in text)
        self.assertTrue("V3.3.3 EXP_333_01 STATUS = NOT_ESTABLISHED" in text or "V3.3.3\\ EXP\\_333\\_01\\ STATUS = NOT\\_ESTABLISHED" in text)
        self.assertTrue("V3.3.3 NEXT EXPERIMENT = HOLD" in text or "V3.3.3\\ NEXT\\ EXPERIMENT = HOLD" in text)

    def test_08_release_status_and_hold_gate(self):
        """Test 08: Verify release status is NOT_ESTABLISHED and next experiment is HOLD."""
        rel_p = self.release_dir / "exp_333_01_release_status.json"
        self.assertTrue(rel_p.exists())
        with open(rel_p, "r", encoding="utf-8") as f:
            rs = json.load(f)
        self.assertEqual(rs["experiment_status"], "NOT_ESTABLISHED")
        self.assertEqual(rs["physical_independence"], "NOT_ESTABLISHED")
        self.assertEqual(rs["v3_3_3_next_experiment"], "HOLD")

    def test_09_hash_manifest_completeness(self):
        """Test 09: Verify all 20 artifacts match hashes in exp_333_01_hash_manifest.json."""
        manifest_p = self.release_dir / "exp_333_01_hash_manifest.json"
        self.assertTrue(manifest_p.exists())
        with open(manifest_p, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(len(manifest["artifacts"]), 20)
        for rel_path, meta in manifest["artifacts"].items():
            full_path = self.exp_dir / rel_path
            self.assertTrue(full_path.exists(), f"Missing artifact: {rel_path}")
            current_h = compute_sha256(full_path)
            self.assertEqual(current_h, meta["sha256"], f"Hash drift in artifact: {rel_path}")

if __name__ == "__main__":
    unittest.main()
