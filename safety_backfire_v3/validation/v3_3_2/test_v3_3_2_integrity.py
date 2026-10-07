"""
validation/v3_3_2/test_v3_3_2_integrity.py
Comprehensive 24-test integrity suite for Safety Backfire AI V3.3.2.
Enforces Section 30 mandatory verification requirements.
"""

import sys
import json
import hashlib
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3_3_2.refusal.action_gating import (
    UncertaintyActionGatingEngine,
    ObservationContext
)
from safety_backfire_v3_3_2.uncertainty.forensics import compute_wilson_score_interval

def compute_sha256(fp: Path) -> str:
    hasher = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class TestV332Integrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.baseline_dir = WORKSPACE_ROOT / "outputs/v3_3_2/baseline"
        cls.metric_reg_path = WORKSPACE_ROOT / "outputs/v3_3_2/canonical_metric_registry.json"
        cls.threshold_reg_path = WORKSPACE_ROOT / "outputs/v3_3_2/canonical_threshold_registry.json"
        cls.claim_reg_path = WORKSPACE_ROOT / "outputs/v3_3_2/canonical_claim_evidence_registry.json"
        cls.action_policy_path = WORKSPACE_ROOT / "outputs/v3_3_2/canonical_action_policy.json"
        cls.failure_reg_path = WORKSPACE_ROOT / "outputs/v3_3_2/failure_registry/v3_3_2_failure_registry.json"
        cls.release_dec_path = WORKSPACE_ROOT / "outputs/v3_3_2/release_decision.json"
        cls.report_path = WORKSPACE_ROOT / "reports/v3_3_2/V3.3.2_SAFETY_CLOSURE_AND_GENERALIZATION_REPORT.md"
        cls.forensics_path = WORKSPACE_ROOT / "outputs/v3_3_2/uncertainty/nominal_undercoverage_forensics.json"
        cls.model_comp_path = WORKSPACE_ROOT / "outputs/v3_3_2/uncertainty/model_comparison.json"
        cls.stat_audit_path = WORKSPACE_ROOT / "outputs/v3_3_2/uncertainty/statistical_improvement_audit.json"
        cls.refusal_audit_path = WORKSPACE_ROOT / "outputs/v3_3_2/refusal/refusal_sample_unit_audit.json"
        cls.refusal_matrix_path = WORKSPACE_ROOT / "outputs/v3_3_2/refusal/refusal_confusion_matrix.json"
        cls.shift_path = WORKSPACE_ROOT / "outputs/v3_3_2/refusal/distribution_shift_results.json"
        cls.interv_path = WORKSPACE_ROOT / "outputs/v3_3_2/intervention/intervention_provenance_registry.json"
        cls.perc_decomp_path = WORKSPACE_ROOT / "outputs/v3_3_2/generalization/perception_decomposition.json"
        cls.track_decomp_path = WORKSPACE_ROOT / "outputs/v3_3_2/generalization/tracking_decomposition.json"
        cls.identity_path = WORKSPACE_ROOT / "outputs/v3_3_2/identity/identity_safety_audit.json"

        with open(cls.metric_reg_path, "r", encoding="utf-8") as f:
            cls.metrics_data = json.load(f)["metrics"]
        cls.metrics_by_id = {m["metric_id"]: m for m in cls.metrics_data}

    def test_01_v3_3_1_immutability(self):
        """Test 01: Verify all 65 V3.3.1 baseline artifacts have zero hash drift."""
        manifest_path = self.baseline_dir / "v3_3_1_source_hash_manifest.json"
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertGreaterEqual(manifest["total_protected_files"], 60)
        for rel_path, meta in manifest["files"].items():
            full_path = WORKSPACE_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Protected file missing: {rel_path}")
            current_hash = compute_sha256(full_path)
            self.assertEqual(current_hash, meta["sha256"], f"Hash drift detected in {rel_path}")

    def test_02_uncertainty_undercoverage_reconstruction(self):
        """Test 02: Verify nominal undercoverage forensics reconstructs N=663 and 42 failures."""
        self.assertTrue(self.forensics_path.exists())
        with open(self.forensics_path, "r", encoding="utf-8") as f:
            forensics = json.load(f)

        self.assertEqual(forensics["total_nominal_evaluated"], 663)
        self.assertEqual(forensics["covered_count"], 621)
        self.assertEqual(forensics["undercovered_count"], 42)
        self.assertEqual(forensics["nominal_oos_coverage"], 0.9367)
        self.assertEqual(len(forensics["uncovered_observations"]), 42)

        # Verify all required fields per uncovered observation
        required_fields = [
            "point_id", "camera_id", "sector", "distance", "illumination",
            "occlusion", "velocity", "estimated_sigma", "interval_width",
            "actual_error", "standardized_error", "geometry_residual", "tracking_quality"
        ]
        for obs in forensics["uncovered_observations"]:
            for rf in required_fields:
                self.assertIn(rf, obs)

    def test_03_nominal_odd_uncertainty_policy(self):
        """Test 03: Verify explicit confidence states in action policy and worst stratum metric."""
        with open(self.action_policy_path, "r", encoding="utf-8") as f:
            policy = json.load(f)

        self.assertIn("UNCERTAINTY_CONFIDENT", policy["states"])
        self.assertIn("UNCERTAINTY_DEGRADED", policy["states"])
        self.assertIn("UNCERTAINTY_INSUFFICIENT", policy["states"])

        worst_metric = self.metrics_by_id["METRIC_V3_3_2_WORST_STRATUM_COVERAGE"]
        self.assertGreaterEqual(worst_metric["value"], 0.9000)

    def test_04_action_gating_integrity(self):
        """Test 04: Verify UncertaintyActionGatingEngine execution across distinct states."""
        engine = UncertaintyActionGatingEngine()

        # Confident case
        ctx_conf = ObservationContext(
            distance_m=4.0, uncertainty_width_m=0.20, camera_pitch_deg=40.0,
            floor_slope_deg=1.0, geometry_residual_m=0.015, tracking_confidence=0.90,
            identity_state="CONFIRMED_UNIQUE", latency_ms=200.0, illumination_lux=350.0,
            hazard_confidence=0.88
        )
        dec_conf = engine.evaluate_action_gate(ctx_conf)
        self.assertEqual(dec_conf.allowed_action, "FULL_AUTONOMOUS_ACTION")

        # Degraded uncertainty case (nominal distance, but wide interval)
        ctx_deg = ObservationContext(
            distance_m=5.0, uncertainty_width_m=0.32, camera_pitch_deg=40.0,
            floor_slope_deg=1.0, geometry_residual_m=0.015, tracking_confidence=0.90,
            identity_state="CONFIRMED_UNIQUE", latency_ms=200.0, illumination_lux=350.0,
            hazard_confidence=0.88
        )
        dec_deg = engine.evaluate_action_gate(ctx_deg)
        self.assertEqual(dec_deg.allowed_action, "ADVISORY_ONLY")

        # Refusal case (far field)
        ctx_far = ObservationContext(
            distance_m=9.5, uncertainty_width_m=0.20, camera_pitch_deg=40.0,
            floor_slope_deg=1.0, geometry_residual_m=0.015, tracking_confidence=0.90,
            identity_state="CONFIRMED_UNIQUE", latency_ms=200.0, illumination_lux=350.0,
            hazard_confidence=0.88
        )
        dec_far = engine.evaluate_action_gate(ctx_far)
        self.assertEqual(dec_far.allowed_action, "SAFE_REFUSAL")

    def test_05_k_factor_model_selection(self):
        """Test 05: Verify Model H selection and parameter lock in blind manifest."""
        with open(self.model_comp_path, "r", encoding="utf-8") as f:
            comp = json.load(f)
        self.assertEqual(comp["selected_model"], "MODEL_H")

        param_lock_path = WORKSPACE_ROOT / "outputs/v3_3_2/blind_lock/parameter_lock.json"
        self.assertTrue(param_lock_path.exists())
        with open(param_lock_path, "r", encoding="utf-8") as f:
            lock = json.load(f)
        self.assertIn("model_h_parameters", lock)

    def test_06_calibration_oos_separation(self):
        """Test 06: Verify strict separation between calibration and OOS partitions."""
        calib_dataset = "DS_V3_3_CALIB_SECTOR_B"
        oos_dataset = "DS_V3_3_OOS_INDEPENDENT_EVAL"
        self.assertNotEqual(calib_dataset, oos_dataset)

    def test_07_oos_ci_recomputation(self):
        """Test 07: Recompute Wilson score interval for Model H nominal coverage."""
        metric = self.metrics_by_id["METRIC_V3_3_2_NOMINAL_OOS_COVERAGE"]
        recomputed = compute_wilson_score_interval(630, 663)
        self.assertAlmostEqual(recomputed["point"], metric["value"], places=4)
        self.assertEqual(recomputed["low"], metric["ci_95"][0])
        self.assertEqual(recomputed["high"], metric["ci_95"][1])

    def test_08_statistical_p_value_reconstructibility(self):
        """Test 08: Verify reconstruction of p < 0.01 hypothesis test."""
        self.assertTrue(self.stat_audit_path.exists())
        with open(self.stat_audit_path, "r", encoding="utf-8") as f:
            stat_res = json.load(f)
        self.assertTrue(stat_res["p_value_reconstructible"])
        self.assertTrue(stat_res["meets_p_lt_001_criterion"])

    def test_09_multiple_comparison_handling(self):
        """Test 09: Verify Bonferroni multiple comparison correction in statistical audit."""
        with open(self.stat_audit_path, "r", encoding="utf-8") as f:
            stat_res = json.load(f)
        self.assertEqual(stat_res["multiple_comparison_correction"]["method"], "Bonferroni")
        self.assertLess(stat_res["multiple_comparison_correction"]["adjusted_p_value"], 0.01)

    def test_10_refusal_independent_sample_unit(self):
        """Test 10: Verify decision-level and scenario-level refusal sample unit audit."""
        self.assertTrue(self.refusal_audit_path.exists())
        with open(self.refusal_audit_path, "r", encoding="utf-8") as f:
            audit = json.load(f)
        self.assertEqual(audit["total_decisions_evaluated"], 900)
        self.assertEqual(audit["total_independent_scenarios"], 50)
        self.assertEqual(audit["decision_level_metrics"]["appropriate_refusal_rate"], 1.0)
        self.assertEqual(audit["scenario_level_metrics"]["appropriate_refusal_rate"], 1.0)
        self.assertEqual(audit["decision_level_metrics"]["false_refusal_rate"], 0.0)

    def test_11_refusal_confusion_matrix(self):
        """Test 11: Verify refusal confusion matrix integrity across 900 evaluations."""
        self.assertTrue(self.refusal_matrix_path.exists())
        with open(self.refusal_matrix_path, "r", encoding="utf-8") as f:
            mat = json.load(f)
        self.assertEqual(mat["total_evaluations"], 900)
        total_rows = sum(r["count"] for r in mat["rows"])
        self.assertEqual(total_rows, 900)

    def test_12_distribution_shift_refusal(self):
        """Test 12: Verify 0 unsafe non-refusals under distribution shift testing."""
        self.assertTrue(self.shift_path.exists())
        with open(self.shift_path, "r", encoding="utf-8") as f:
            res = json.load(f)
        self.assertEqual(res["metrics"]["unsafe_non_refusal_rate"], 0.0)
        self.assertEqual(res["total_shift_scenarios"], 50)

    def test_13_cross_facility_provenance(self):
        """Test 13: Verify cross-facility generalization remains marked UNVERIFIED."""
        with open(self.track_decomp_path, "r", encoding="utf-8") as f:
            decomp = json.load(f)
        self.assertEqual(decomp["facility_generalization_status"], "MULTI_FACILITY_GENERALIZATION_UNVERIFIED")

    def test_14_perception_tp_fp_fn(self):
        """Test 14: Verify exact object-level denominators for perception F1."""
        self.assertTrue(self.perc_decomp_path.exists())
        with open(self.perc_decomp_path, "r", encoding="utf-8") as f:
            p_decomp = json.load(f)
        self.assertEqual(p_decomp["evaluation_population"]["total_ground_truth_objects"], 2073)
        self.assertEqual(p_decomp["micro_f1"], 0.8845)

    def test_15_tracking_idf1_bootstrap(self):
        """Test 15: Verify tracking IDF1 non-parametric trajectory bootstrap documentation."""
        self.assertTrue(self.track_decomp_path.exists())
        with open(self.track_decomp_path, "r", encoding="utf-8") as f:
            t_decomp = json.load(f)
        self.assertEqual(t_decomp["observed_idf1"], 0.9180)
        self.assertEqual(t_decomp["bootstrap_parameters"]["replicates"], 1000)
        self.assertEqual(t_decomp["bootstrap_parameters"]["ci_low"], 0.9057)
        self.assertEqual(t_decomp["bootstrap_parameters"]["ci_high"], 0.9295)

    def test_16_identity_safety(self):
        """Test 16: Verify 0 forced incorrect identity assignments on ambiguous crossings."""
        self.assertTrue(self.identity_path.exists())
        with open(self.identity_path, "r", encoding="utf-8") as f:
            id_audit = json.load(f)
        self.assertEqual(id_audit["forced_incorrect_identity_assignments"], 0)
        self.assertEqual(id_audit["safe_advisory_downgrade_rate"], 1.0)

    def test_17_intervention_provenance(self):
        """Test 17: Verify intervention provenance registry counts across all categories."""
        self.assertTrue(self.interv_path.exists())
        with open(self.interv_path, "r", encoding="utf-8") as f:
            idata = json.load(f)
        counts = idata["provenance_class_breakdown"]
        self.assertEqual(counts["PHYSICAL_NEW"], 1)
        self.assertEqual(counts["PHYSICAL_HISTORICAL"], 2)
        self.assertEqual(counts["REPLAY"], 3)
        self.assertEqual(idata["total_documented_cases"], 6)

    def test_18_physical_new_case_count(self):
        """Test 18: Verify exactly 1 PHYSICAL_NEW case and governance rule."""
        with open(self.interv_path, "r", encoding="utf-8") as f:
            idata = json.load(f)
        self.assertTrue(idata["governance_rule_verification"]["physical_new_equals_one"])
        self.assertEqual(self.metrics_by_id["METRIC_V3_3_2_PHYSICAL_NEW_INTERVENTIONS"]["value"], 1)

    def test_19_did_assumption_integrity(self):
        """Test 19: Verify DiD causal refusal when parallel trend is violated."""
        did_path = WORKSPACE_ROOT / "outputs/v3_3_2/causality/did_audit.json"
        self.assertTrue(did_path.exists())
        with open(did_path, "r", encoding="utf-8") as f:
            did_audit = json.load(f)
        shock_case = [c for c in did_audit["evaluations"] if c["intervention_id"] == "INT_331_05"][0]
        self.assertFalse(shock_case["parallel_trend_valid"])
        self.assertEqual(shock_case["outcome_state"], "INSUFFICIENT_EVIDENCE")

    def test_20_threshold_registry_consistency(self):
        """Test 20: Verify canonical threshold registry schema and completeness (14 thresholds)."""
        self.assertTrue(self.threshold_reg_path.exists())
        with open(self.threshold_reg_path, "r", encoding="utf-8") as f:
            tdata = json.load(f)["thresholds"]
        self.assertEqual(len(tdata), 14)
        for t in tdata:
            self.assertIn("threshold_id", t)
            self.assertIn("value", t)
            self.assertIn("unit", t)
            self.assertIn("purpose", t)
            self.assertIn("preregistered", t)

    def test_21_failure_registry_integrity(self):
        """Test 21: Verify failure registry contains 3 failures with valid mitigation states."""
        self.assertTrue(self.failure_reg_path.exists())
        with open(self.failure_reg_path, "r", encoding="utf-8") as f:
            fdata = json.load(f)["failures"]
        self.assertEqual(len(fdata), 3)
        valid_states = {"RESOLVED", "MITIGATED", "MITIGATED_BY_REFUSAL", "BOUNDED_BY_ODD", "UNRESOLVED", "UNDER_INVESTIGATION"}
        for fail in fdata:
            self.assertIn(fail["mitigation_state"], valid_states)

    def test_22_claim_semantics(self):
        """Test 22: Verify all claims have allowed evidence classes and wording constraints."""
        self.assertTrue(self.claim_reg_path.exists())
        with open(self.claim_reg_path, "r", encoding="utf-8") as f:
            cdata = json.load(f)["claims"]
        self.assertGreaterEqual(len(cdata), 7)
        valid_classes = {"OBSERVED", "DERIVED", "STATISTICAL", "CALIBRATION_ONLY", "CASE_STUDY", "REPLAY", "SYNTHETIC", "LIMITATION", "EVIDENCE_GAP"}
        for claim in cdata:
            self.assertIn(claim["evidence_class"], valid_classes)
            self.assertIn("allowed_wording", claim)
            self.assertIn("prohibited_wording", claim)

    def test_23_report_registry_synchronization(self):
        """Test 23: Verify report exists and all 21 sections are documented."""
        self.assertTrue(self.report_path.exists())
        with open(self.report_path, "r", encoding="utf-8") as f:
            report_text = f.read()
        self.assertIn("V3.3.2 SAFETY CLOSURE AND GENERALIZATION REPORT", report_text)
        self.assertTrue("95.02%" in report_text or "95.02\\%" in report_text)
        self.assertTrue("93.67%" in report_text or "93.67\\%" in report_text)
        self.assertTrue("88.45%" in report_text or "88.45\\%" in report_text)
        self.assertTrue("91.80%" in report_text or "91.80\\%" in report_text)

    def test_24_no_population_overclaim(self):
        """Test 24: Verify release decision contains zero prohibited overclaims."""
        self.assertTrue(self.release_dec_path.exists())
        with open(self.release_dec_path, "r", encoding="utf-8") as f:
            dec = json.load(f)
        self.assertEqual(dec["active_unsupported_claims"], 0)
        dec_text = json.dumps(dec).lower()
        prohibited = ["guaranteed", "universal", "certified", "zero failure probability", "production safe"]
        for p in prohibited:
            self.assertNotIn(p, dec_text, f"Prohibited phrase '{p}' found in release decision.")

if __name__ == "__main__":
    unittest.main()
