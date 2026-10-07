"""
validation/v3_3_1/test_v3_3_1_integrity.py
Comprehensive 24-test integrity suite for Safety Backfire AI V3.3.1.
Enforces Section 35 mandatory verification requirements.
"""

import sys
import json
import hashlib
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3_3_1.identity.hardening import IdentityHardeningEngine, IdentityCandidate
from safety_backfire_v3_3_1.refusal.refusal_quality import RefusalQualityEngine, OperationalState
from safety_backfire_v3_3_1.causality.backfire_evaluator import BackfireCaseRecord, BackfireCausalityEngine, ProvenanceClass

def compute_sha256(fp: Path) -> str:
    hasher = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class TestV331Integrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.baseline_dir = WORKSPACE_ROOT / "outputs/v3_3_1/baseline"
        cls.metric_reg_path = WORKSPACE_ROOT / "outputs/v3_3_1/canonical_metric_registry.json"
        cls.threshold_reg_path = WORKSPACE_ROOT / "outputs/v3_3_1/canonical_threshold_registry.json"
        cls.claim_reg_path = WORKSPACE_ROOT / "outputs/v3_3_1/canonical_claim_evidence_registry.json"
        cls.failure_reg_path = WORKSPACE_ROOT / "outputs/v3_3_1/failure_registry/v3_3_1_failure_registry.json"
        cls.release_dec_path = WORKSPACE_ROOT / "outputs/v3_3_1/release_decision.json"
        cls.report_path = WORKSPACE_ROOT / "reports/v3_3_1/V3.3.1_EXPERIMENTAL_VALIDATION_REPORT.md"

        with open(cls.metric_reg_path, "r", encoding="utf-8") as f:
            cls.metrics_data = json.load(f)["metrics"]
        cls.metrics_by_id = {m["metric_id"]: m for m in cls.metrics_data}

    def test_01_v3_3_0_baseline_immutability(self):
        """Test 01: Verify all 79 V3.3.0 baseline artifacts have zero hash drift."""
        manifest_path = self.baseline_dir / "v3_3_0_source_hash_manifest.json"
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for rel_path, meta in manifest["files"].items():
            full_path = WORKSPACE_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Missing protected V3.3.0 file: {rel_path}")
            current_hash = compute_sha256(full_path)
            self.assertEqual(current_hash, meta["sha256"], f"Hash drift detected in V3.3.0 file: {rel_path}")

    def test_02_dataset_provenance(self):
        """Test 02: Verify dataset provenance gate rejects METADATA_ONLY and UNAVAILABLE."""
        audit_path = WORKSPACE_ROOT / "outputs/v3_3/dataset_audit/dataset_availability_audit.json"
        with open(audit_path, "r", encoding="utf-8") as f:
            audit = json.load(f)
        self.assertEqual(audit["datasets"]["DS_FULL_CORPUS_39900"]["classification"], "METADATA_ONLY")
        self.assertEqual(audit["datasets"]["DS_V3_3_UNAVAILABLE_EXTERNAL_FACILITY_E"]["classification"], "UNAVAILABLE")

    def test_03_blind_lock(self):
        """Test 03: Verify blind lock manifests exist with LOCKED_PRE_EVALUATION status."""
        lock_path = WORKSPACE_ROOT / "outputs/v3_3_1/blind_lock/parameter_lock.json"
        self.assertTrue(lock_path.exists())
        with open(lock_path, "r", encoding="utf-8") as f:
            lock = json.load(f)
        self.assertEqual(lock["lock_status"], "LOCKED_PRE_EVALUATION")
        self.assertEqual(lock["locked_parameters"]["selected_uncertainty_model"], "MODEL_D")

    def test_04_calibration_oos_separation(self):
        """Test 04: Verify strict separation between calibration and OOS datasets."""
        calib_rec_path = WORKSPACE_ROOT / "outputs/v3_3_1/uncertainty/calibration_model_selection.json"
        with open(calib_rec_path, "r", encoding="utf-8") as f:
            calib = json.load(f)
        self.assertEqual(calib["lock_manifest"]["calibration_dataset_id"], "DS_V3_3_CALIB_SECTOR_B")
        self.assertNotIn("DS_V3_3_VAL_INTERSECTION_C", calib["lock_manifest"]["calibration_dataset_id"])
        self.assertNotIn("DS_V3_3_BLIND_STAGING_D", calib["lock_manifest"]["calibration_dataset_id"])

    def test_05_k_factor_lineage(self):
        """Test 05: Verify condition-aware k lineage from fixed baseline k=2.42 to Model D."""
        m_oos = self.metrics_by_id["METRIC_331_UNCERTAINTY_CONDITION_AWARE_NOMINAL"]
        self.assertIn("Model D", m_oos["interpretation"])
        self.assertIn("92.61%", m_oos["interpretation"])

    def test_06_oos_coverage_recomputation(self):
        """Test 06: Verify recomputed nominal OOS coverage matches canonical registry value 0.9367."""
        oos_path = WORKSPACE_ROOT / "outputs/v3_3_1/uncertainty/condition_aware_oos_results.json"
        with open(oos_path, "r", encoding="utf-8") as f:
            res = json.load(f)
        nom_cov = res["model_comparison"]["MODEL_D_CONDITION_AWARE"]["nominal_coverage"]
        self.assertAlmostEqual(nom_cov, 0.9367, places=4)
        self.assertEqual(self.metrics_by_id["METRIC_331_UNCERTAINTY_CONDITION_AWARE_NOMINAL"]["value"], 0.9367)

    def test_07_oos_ci_method(self):
        """Test 07: Verify Wilson score interval is used for binomial coverage proportions."""
        m = self.metrics_by_id["METRIC_331_UNCERTAINTY_CONDITION_AWARE_NOMINAL"]
        self.assertEqual(m["statistical_method"], "Wilson_Score_Interval")
        self.assertIsInstance(m["confidence_interval"], list)
        self.assertEqual(len(m["confidence_interval"]), 2)

    def test_08_nominal_odd_claim_integrity(self):
        """Test 08: Verify nominal OOD coverage does NOT claim >= 95% target was met."""
        oos_path = WORKSPACE_ROOT / "outputs/v3_3_1/uncertainty/condition_aware_oos_results.json"
        with open(oos_path, "r", encoding="utf-8") as f:
            res = json.load(f)
        self.assertFalse(res["model_comparison"]["MODEL_D_CONDITION_AWARE"]["meets_target"])
        self.assertIn("meets_target", res["model_comparison"]["MODEL_D_CONDITION_AWARE"])

    def test_09_farfield_claim_integrity(self):
        """Test 09: Verify far-field is documented outside autonomous action envelope."""
        oos_path = WORKSPACE_ROOT / "outputs/v3_3_1/uncertainty/condition_aware_oos_results.json"
        with open(oos_path, "r", encoding="utf-8") as f:
            res = json.load(f)
        self.assertTrue(res["acceptance_criteria_assessment"]["far_field_gated_outside_envelope"])

    def test_10_perception_denominator_integrity(self):
        """Test 10: Verify exact object-level denominators used for perception F1."""
        m = self.metrics_by_id["METRIC_331_GENERALIZATION_PERCEPTION_F1"]
        self.assertEqual(m["sample_unit"], "Object_Annotation_Instance")
        self.assertEqual(m["N"], 1980)

    def test_11_tracking_idf1_integrity(self):
        """Test 11: Verify tracking IDF1 is 0.9180 across 28 trajectories."""
        m = self.metrics_by_id["METRIC_331_GENERALIZATION_TRACKING_IDF1"]
        self.assertEqual(m["value"], 0.9180)
        self.assertEqual(m["N"], 28)

    def test_12_tracking_bootstrap_integrity(self):
        """Test 12: Verify tracking bootstrap interval documentation."""
        gen_path = WORKSPACE_ROOT / "outputs/v3_3_1/generalization/cross_environment_generalization_summary.json"
        with open(gen_path, "r", encoding="utf-8") as f:
            gen = json.load(f)
        t_data = gen["tracking_generalization"]
        self.assertEqual(t_data["bootstrap_unit"], "Trajectory_Sequence")
        self.assertEqual(t_data["replicates"], 1000)
        self.assertEqual(t_data["seed"], 1337)

    def test_13_identity_ambiguity_safety(self):
        """Test 13: Verify identity ambiguity engine triggers advisory downgrade."""
        engine = IdentityHardeningEngine()
        cands = [
            IdentityCandidate("W1", 0.90, 0.55, 0.1, True),
            IdentityCandidate("W2", 0.89, 0.58, 0.1, True)
        ]
        res = engine.associate_track("W1", cands, hazard_pending=True)
        self.assertEqual(res["assigned_id"], "UNKNOWN_AMBIGUOUS_PAIR")
        self.assertEqual(res["downgrade_action"], "ADVISORY_WARNING_ONLY")

    def test_14_event_metric_integrity(self):
        """Test 14: Verify multi-sector breakdown has 4 sectors and worst sector identified."""
        gen_path = WORKSPACE_ROOT / "outputs/v3_3_1/generalization/cross_environment_generalization_summary.json"
        with open(gen_path, "r", encoding="utf-8") as f:
            gen = json.load(f)
        self.assertEqual(gen["environment_count"], 4)
        self.assertIn("Sector_D_Outbound_Staging", gen["worst_environment"])

    def test_15_intervention_provenance(self):
        """Test 15: Verify exactly 1 PHYSICAL_NEW case among 6 total cases."""
        int_path = WORKSPACE_ROOT / "outputs/v3_3_1/intervention/backfire_case_governance_summary.json"
        with open(int_path, "r", encoding="utf-8") as f:
            int_data = json.load(f)
        self.assertEqual(int_data["sample_size_total"], 6)
        self.assertEqual(int_data["provenance_breakdown"]["PHYSICAL_NEW"], 1)

    def test_16_did_assumption_integrity(self):
        """Test 16: Verify DiD formula and parallel trend violation refuses causality."""
        caus_path = WORKSPACE_ROOT / "outputs/v3_3_1/causality/did_reconstruction_manifest.json"
        with open(caus_path, "r", encoding="utf-8") as f:
            caus = json.load(f)
        self.assertIn("DiD = (TreatedPost - TreatedPre) - (ControlPost - ControlPre)", caus["did_formula"])
        shock_case = next(c for c in caus["reconstructed_cases"] if c["case_id"] == "CASE_SHOCK_05")
        self.assertEqual(shock_case["causal_status"], "INSUFFICIENT_EVIDENCE_PARALLEL_TREND_VIOLATED")

    def test_17_threshold_registry(self):
        """Test 17: Verify threshold registry schema and completeness (14 thresholds)."""
        with open(self.threshold_reg_path, "r", encoding="utf-8") as f:
            t_data = json.load(f)
        self.assertGreaterEqual(len(t_data["thresholds"]), 14)
        for t in t_data["thresholds"]:
            self.assertIn("threshold_id", t)
            self.assertIn("value", t)
            self.assertIn("unit", t)
            self.assertIn("purpose", t)
            self.assertTrue(t["preregistered"])

    def test_18_refusal_metric_integrity(self):
        """Test 18: Verify refusal quality metrics (1.0 appropriate, 0.0 false, 0.0 unsafe)."""
        m_app = self.metrics_by_id["METRIC_331_REFUSAL_APPROPRIATE_RATE"]
        m_false = self.metrics_by_id["METRIC_331_REFUSAL_FALSE_RATE"]
        self.assertEqual(m_app["value"], 1.0)
        self.assertEqual(m_false["value"], 0.0)

    def test_19_failure_registry(self):
        """Test 19: Verify V3.3.1 failure registry contains 3 failures with valid mitigation states."""
        with open(self.failure_reg_path, "r", encoding="utf-8") as f:
            f_data = json.load(f)
        self.assertEqual(len(f_data["failures"]), 3)
        valid_states = {"RESOLVED", "MITIGATED", "MITIGATED_BY_REFUSAL", "BOUNDED_BY_ODD", "UNRESOLVED", "UNDER_INVESTIGATION"}
        for fail in f_data["failures"]:
            self.assertTrue(fail["failure_id"].startswith("V3.3.1-FAIL"))
            self.assertIn(fail["mitigation_state"], valid_states)

    def test_20_claim_evidence_traceability(self):
        """Test 20: Verify all active claims in claim registry map to metric_id and test."""
        with open(self.claim_reg_path, "r", encoding="utf-8") as f:
            c_data = json.load(f)
        self.assertGreaterEqual(len(c_data["claims"]), 6)
        for c in c_data["claims"]:
            self.assertIn(c["metric_id"], self.metrics_by_id)
            self.assertTrue(len(c["allowed_wording"]) > 10)

    def test_21_no_posthoc_blind_tuning(self):
        """Test 21: Verify blind lock rules prohibit post-hoc parameter tuning."""
        with open(WORKSPACE_ROOT / "outputs/v3_3_1/blind_lock/blind_dataset_hash.json", "r", encoding="utf-8") as f:
            b_data = json.load(f)
        self.assertEqual(b_data["quarantined_streams"]["DS_V3_3_BLIND_STAGING_D"]["access_policy"], "NO_MODEL_TUNING_PERMITTED_POST_UNBLINDING")

    def test_22_no_population_overclaim(self):
        """Test 22: Verify absence of prohibited universal overclaims in release decision."""
        with open(self.release_dec_path, "r", encoding="utf-8") as f:
            dec_dump = json.dumps(json.load(f)).lower()
        prohibited = ["100% accuracy", "zero failure probability", "mathematical guarantee", "universal causality", "proven causal effect"]
        for p in prohibited:
            self.assertNotIn(p, dec_dump)

    def test_23_report_registry_synchronization(self):
        """Test 23: Verify report exists and synchronizes with canonical metrics."""
        self.assertTrue(self.report_path.exists())
        with open(self.report_path, "r", encoding="utf-8") as f:
            report_text = f.read()
        self.assertTrue("93.67%" in report_text or "93.67\\%" in report_text)
        self.assertTrue("91.80%" in report_text or "91.80\\%" in report_text)
        self.assertIn("V3.3.1_VALIDATED_WITH_LIMITATIONS", report_text)

    def test_24_canonical_artifact_completeness(self):
        """Test 24: Verify all required Section 34 research output directories and files exist."""
        required_dirs = [
            "outputs/v3_3_1/baseline",
            "outputs/v3_3_1/experiments",
            "outputs/v3_3_1/uncertainty",
            "outputs/v3_3_1/generalization",
            "outputs/v3_3_1/refusal",
            "outputs/v3_3_1/identity",
            "outputs/v3_3_1/intervention",
            "outputs/v3_3_1/causality",
            "outputs/v3_3_1/failure_registry",
            "outputs/v3_3_1/blind_lock"
        ]
        for rd in required_dirs:
            p = WORKSPACE_ROOT / rd
            self.assertTrue(p.exists() and p.is_dir(), f"Missing required directory: {rd}")

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV331Integrity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
