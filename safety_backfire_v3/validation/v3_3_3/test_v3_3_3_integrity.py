"""
validation/v3_3_3/test_v3_3_3_integrity.py
Comprehensive integrity suite for Safety Backfire AI V3.3.2 Final Reconciliation & V3.3.3 Execution Gate.
Strictly enforces Section 22 (15 required regression tests) and full governance release criteria.
"""

import sys
import json
import hashlib
import unittest
import math
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

def compute_sha256(fp: Path) -> str:
    hasher = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_wilson_score_interval(successes: int, total: int, z: float = 1.95996):
    p = successes / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + (z**2) / (4.0 * (total**2)))
    return round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4)

class TestV333Integrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.baseline_dir = WORKSPACE_ROOT / "outputs/v3_3_3/baseline"
        cls.reconciliation_dir = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation"
        cls.blind_lock_dir = WORKSPACE_ROOT / "outputs/v3_3_3/blind_lock"
        cls.metric_reg_path = WORKSPACE_ROOT / "outputs/v3_3_3/metric_registry.json"
        cls.canonical_legacy_metric_path = WORKSPACE_ROOT / "outputs/v3_3_3/canonical_metric_registry.json"
        cls.threshold_reg_path = WORKSPACE_ROOT / "outputs/v3_3_3/canonical_threshold_registry.json"
        cls.claim_reg_path = WORKSPACE_ROOT / "outputs/v3_3_3/canonical_claim_evidence_registry.json"
        cls.claims_audit_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/claims_language_audit.json"
        cls.metric_semantics_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/metric_semantics_registry.json"
        cls.final_recon_metric_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/v3_3_2_final_metric_reconciliation.json"
        cls.recon_manifest_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/v3_3_2_final_reconciliation_manifest.json"
        cls.provenance_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/autonomous_uncovered_provenance.json"
        cls.failure_reg_path = WORKSPACE_ROOT / "outputs/v3_3_3/failure_registry/v3_3_3_failure_registry.json"
        cls.exp_reg_path = WORKSPACE_ROOT / "outputs/v3_3_3/experiment_registry.json"
        cls.report_path = WORKSPACE_ROOT / "reports/v3_3_3/V3.3.3_READINESS_AND_V3.3.2_FINAL_RECONCILIATION_REPORT.md"
        cls.refusal_indep_path = WORKSPACE_ROOT / "outputs/v3_3_3/refusal/refusal_independence_registry.json"
        cls.tracking_sens_path = WORKSPACE_ROOT / "outputs/v3_3_3/tracking/idf1_bootstrap_sensitivity.json"
        cls.release_decision_path = WORKSPACE_ROOT / "outputs/v3_3_3/release_decision.json"

        with open(cls.metric_reg_path, "r", encoding="utf-8") as f:
            cls.metrics_data = json.load(f)["metrics"]
        cls.metrics_by_id = {m["metric_id"]: m for m in cls.metrics_data}

    # =========================================================================
    # SECTION 22 MANDATORY REGRESSION TESTS (1 through 15)
    # =========================================================================

    def test_sec22_01_model_h_nominal_oos_coverage_ratio_630_663(self):
        """Sec 22 Test 1: Verify 630 / 663 = 95.02% nominal OOS coverage and Wilson CI [93.09%, 96.43%]."""
        stats_file = self.reconciliation_dir / "model_h_oos_statistics.json"
        self.assertTrue(stats_file.exists())
        with open(stats_file, "r", encoding="utf-8") as f:
            sdata = json.load(f)

        counts = sdata["exact_counts"]
        self.assertEqual(counts["covered_count"], 630)
        self.assertEqual(counts["total_nominal_n"], 663)
        self.assertAlmostEqual(counts["covered_count"] / counts["total_nominal_n"], 0.950226, places=5)
        self.assertEqual(counts["reported_coverage_rounded"], 0.9502)

        low, high = compute_wilson_score_interval(630, 663)
        self.assertEqual(low, 0.9309)
        self.assertEqual(high, 0.9643)
        self.assertEqual(sdata["wilson_ci_95"]["low"], 0.9309)
        self.assertEqual(sdata["wilson_ci_95"]["high"], 0.9643)

    def test_sec22_02_oos_uncovered_rate_33_663(self):
        """Sec 22 Test 2: Verify 33 / 663 = 4.98% total nominal OOS uncovered rate."""
        with open(self.reconciliation_dir / "action_width_distribution.json", "r", encoding="utf-8") as f:
            wdata = json.load(f)

        metric = wdata["canonical_metrics"]["OOS_UNCOVERED_RATE"]
        self.assertEqual(metric["numerator"], 33)
        self.assertEqual(metric["denominator"], 663)
        self.assertAlmostEqual(33 / 663, 0.0497737, places=5)
        self.assertEqual(metric["value"], 0.0498)
        self.assertEqual(metric["percentage"], "4.98%")

    def test_sec22_03_autonomous_action_frames_502_663(self):
        """Sec 22 Test 3: Verify 502 / 663 = 75.72% autonomous action frames."""
        with open(self.reconciliation_dir / "action_width_distribution.json", "r", encoding="utf-8") as f:
            wdata = json.load(f)

        metric = wdata["canonical_metrics"]["AUTONOMOUS_ACTION_FRAMES"]
        self.assertEqual(metric["numerator"], 502)
        self.assertEqual(metric["denominator"], 663)
        self.assertAlmostEqual(502 / 663, 0.757164, places=5)
        self.assertEqual(metric["value"], 0.7572)
        self.assertEqual(metric["percentage"], "75.72%")

    def test_sec22_04_autonomous_subset_uncovered_rate_26_502(self):
        """Sec 22 Test 4: Verify 26 / 502 = 5.18% autonomous subset uncovered rate."""
        with open(self.reconciliation_dir / "action_width_distribution.json", "r", encoding="utf-8") as f:
            wdata = json.load(f)

        metric = wdata["canonical_metrics"]["AUTONOMOUS_SUBSET_UNCOVERED_RATE"]
        self.assertEqual(metric["numerator"], 26)
        self.assertEqual(metric["denominator"], 502)
        self.assertAlmostEqual(26 / 502, 0.0517928, places=5)
        self.assertEqual(metric["value"], 0.0518)
        self.assertEqual(metric["percentage"], "5.18%")

    def test_sec22_05_advisory_action_frames_161_663(self):
        """Sec 22 Test 5: Verify 161 / 663 = 24.28% advisory action frames."""
        with open(self.reconciliation_dir / "action_width_distribution.json", "r", encoding="utf-8") as f:
            wdata = json.load(f)

        metric = wdata["canonical_metrics"]["ADVISORY_ACTION_FRAMES"]
        self.assertEqual(metric["numerator"], 161)
        self.assertEqual(metric["denominator"], 663)
        self.assertAlmostEqual(161 / 663, 0.242836, places=5)
        self.assertEqual(metric["value"], 0.2428)
        self.assertEqual(metric["percentage"], "24.28%")

    def test_sec22_06_advisory_subset_uncovered_rate_7_161(self):
        """Sec 22 Test 6: Verify 7 / 161 = 4.35% advisory subset uncovered rate."""
        with open(self.reconciliation_dir / "action_width_distribution.json", "r", encoding="utf-8") as f:
            wdata = json.load(f)

        metric = wdata["canonical_metrics"]["ADVISORY_SUBSET_UNCOVERED_RATE"]
        self.assertEqual(metric["numerator"], 7)
        self.assertEqual(metric["denominator"], 161)
        self.assertAlmostEqual(7 / 161, 0.043478, places=5)
        self.assertEqual(metric["value"], 0.0435)
        self.assertEqual(metric["percentage"], "4.35%")

    def test_sec22_07_safe_refusal_width_frames_0_663(self):
        """Sec 22 Test 7: Verify 0 / 663 = 0.00% safe refusal width frames under nominal conditions."""
        with open(self.reconciliation_dir / "action_width_distribution.json", "r", encoding="utf-8") as f:
            wdata = json.load(f)

        metric = wdata["canonical_metrics"]["SAFE_REFUSAL_WIDTH_FRAMES"]
        self.assertEqual(metric["numerator"], 0)
        self.assertEqual(metric["denominator"], 663)
        self.assertEqual(metric["value"], 0.0000)
        self.assertEqual(metric["percentage"], "0.00%")

    def test_sec22_08_distinction_coverage_vs_unsafe_action(self):
        """Sec 22 Test 8: Verify strict separation between statistical uncertainty coverage and operational safety policy."""
        # 1. Check metric_semantics_registry.json
        self.assertTrue(self.metric_semantics_path.exists())
        with open(self.metric_semantics_path, "r", encoding="utf-8") as f:
            sreg = json.load(f)
        
        families = sreg["metric_families"]
        self.assertIn("FAMILY_A_STATISTICAL_UNCERTAINTY_COVERAGE", families)
        self.assertIn("FAMILY_B_OPERATIONAL_SAFETY_POLICY_PERFORMANCE", families)
        self.assertEqual(families["FAMILY_A_STATISTICAL_UNCERTAINTY_COVERAGE"]["decision_layer"], "UNCERTAINTY")
        self.assertEqual(families["FAMILY_B_OPERATIONAL_SAFETY_POLICY_PERFORMANCE"]["decision_layer"], "POLICY")

        # 2. Check autonomous_uncovered_provenance.json
        self.assertTrue(self.provenance_path.exists())
        with open(self.provenance_path, "r", encoding="utf-8") as f:
            prov = json.load(f)

        self.assertEqual(prov["total_oos"], 663)
        self.assertEqual(prov["autonomous_frames"], 502)
        self.assertEqual(prov["autonomous_uncovered"], 26)
        self.assertEqual(prov["actual_unsafe_actions_confirmed"], 0)
        self.assertEqual(prov["evaluation_only"], 26)
        self.assertEqual(prov["operational_safety_status"], "NOT_ESTABLISHED_FOR_THE_26_UNCOVERED_OOS_POINTS")
        self.assertEqual(prov["semantic_classification"], "UNCERTAINTY_COVERAGE_FAILURE_WITHIN_AUTONOMOUS_POLICY_REGION")

        # 3. Check prohibition in action_width_distribution.json
        with open(self.reconciliation_dir / "action_width_distribution.json", "r", encoding="utf-8") as f:
            wdata = json.load(f)
        self.assertTrue(wdata["semantic_correction_governance"]["separation_enforced"])
        self.assertIn("UNSAFE_NON_REFUSAL_RATE", wdata["semantic_correction_governance"]["prohibited_terminology"])

    def test_sec22_09_calibration_vs_stress_validation_population_labels(self):
        """Sec 22 Test 9: Verify separation of in-sample calibration vs cross-sector stress validation populations."""
        calib_file = self.reconciliation_dir / "calibration_metric_lineage.json"
        self.assertTrue(calib_file.exists())
        with open(calib_file, "r", encoding="utf-8") as f:
            cdata = json.load(f)

        pop1 = cdata["populations"]["POPULATION_1_TRUE_CALIBRATION"]
        self.assertEqual(pop1["dataset_id"], "DS_V3_3_CALIB_SECTOR_B")
        self.assertEqual(pop1["sample_size"], 500)
        self.assertEqual(pop1["in_sample_coverage"]["MODEL_A_FIXED_K_2_42"]["coverage"], 0.9500)
        self.assertEqual(pop1["in_sample_coverage"]["MODEL_D_CONDITION_AWARE"]["coverage"], 0.9480)
        self.assertEqual(pop1["in_sample_coverage"]["MODEL_H_PITCH_COMPENSATED"]["coverage"], 0.9580)

        pop2 = cdata["populations"]["POPULATION_2_CROSS_SECTOR_STRESS_SPLIT"]
        self.assertEqual(pop2["dataset_id"], "DS_V3_3_2_PSEUDO_OOS_STRESS_SPLIT")
        self.assertEqual(pop2["sample_size"], 500)
        self.assertEqual(pop2["evaluated_coverage"]["MODEL_A_FIXED_K_2_42"]["coverage"], 0.8740)
        self.assertEqual(pop2["evaluated_coverage"]["MODEL_D_CONDITION_AWARE"]["coverage"], 0.9020)
        self.assertEqual(pop2["evaluated_coverage"]["MODEL_H_PITCH_COMPENSATED"]["coverage"], 0.9320)
        self.assertIn("RETRACTED_FROM_CALIBRATION_LABEL_RECLASSIFIED_AS_STRESS_VALIDATION", 
                      pop2["evaluated_coverage"]["MODEL_A_FIXED_K_2_42"]["status"])

    def test_sec22_10_physical_new_count(self):
        """Sec 22 Test 10: Verify intervention provenance: PHYSICAL_NEW = 1, physical historical = 2, replay = 3."""
        interv_file = self.reconciliation_dir / "intervention_provenance_registry.json"
        self.assertTrue(interv_file.exists())
        with open(interv_file, "r", encoding="utf-8") as f:
            idata = json.load(f)

        counts = idata["counts"]
        self.assertEqual(counts["new_physical_evidence_count"], 1)
        self.assertEqual(counts["historical_physical_evidence_count"], 2)
        self.assertEqual(counts["replayed_evidence_count"], 3)
        self.assertEqual(counts["total_documented_cases_count"], 6)

    def test_sec22_11_evidence_gap_semantics(self):
        """Sec 22 Test 11: Verify failure semantics: UNDERLYING_LIMITATION=PRESENT, SAFETY_EXPOSURE=MITIGATED, STATE=NOT_ESTABLISHED."""
        self.assertTrue(self.failure_reg_path.exists())
        with open(self.failure_reg_path, "r", encoding="utf-8") as f:
            fdata = json.load(f)["failures"]

        fail_1 = [f for f in fdata if f["failure_id"] == "V3.3.3-FAIL-001"][0]
        fail_2 = [f for f in fdata if f["failure_id"] == "V3.3.3-FAIL-002"][0]
        fail_3 = [f for f in fdata if f["failure_id"] == "V3.3.3-FAIL-003"][0]

        # Dual state for mitigated physical/algorithmic limitations
        self.assertEqual(fail_1["underlying_limitation"], "PRESENT")
        self.assertEqual(fail_1["safety_exposure"], "MITIGATED")
        self.assertNotEqual(fail_1["mitigation_state"], "RESOLVED")

        # Evidence gaps strictly NOT_ESTABLISHED (never BOUNDED_BY_ODD)
        self.assertEqual(fail_2["mitigation_state"], "NOT_ESTABLISHED")
        self.assertIn("EVIDENCE_GAP", fail_2["classification"])
        self.assertNotEqual(fail_2["mitigation_state"], "BOUNDED_BY_ODD")

        self.assertEqual(fail_3["mitigation_state"], "NOT_ESTABLISHED")
        self.assertIn("EVIDENCE_GAP", fail_3["classification"])
        self.assertNotEqual(fail_3["mitigation_state"], "BOUNDED_BY_ODD")

    def test_sec22_12_did_p_value_interpretation(self):
        """Sec 22 Test 12: Verify DiD p-value interpretation: p=0.008 rejected / insufficient, p=0.42 difference not detected."""
        did_file = self.reconciliation_dir / "did_assumption_audit.json"
        self.assertTrue(did_file.exists())
        with open(did_file, "r", encoding="utf-8") as f:
            ddata = json.load(f)

        case_05 = [c for c in ddata["audited_cases"] if c["intervention_id"] == "INT_331_05"][0]
        case_06 = [c for c in ddata["audited_cases"] if c["intervention_id"] == "INT_331_06"][0]

        self.assertEqual(case_05["pre_trend_p_value"], 0.008)
        self.assertEqual(case_05["causal_status"], "INSUFFICIENT_EVIDENCE")

        self.assertEqual(case_06["pre_trend_p_value"], 0.42)
        self.assertEqual(case_06["causal_status"], "SUPPORTED_UNDER_TESTED_ASSUMPTIONS")

        with open(self.claims_audit_path, "r", encoding="utf-8") as f:
            cdata = json.load(f)["audited_claims"]
        causal_claim = [c for c in cdata if c["claim_area"] == "CAUSAL_INFERENCE_AND_DID"][0]
        self.assertTrue(any("No statistically significant pre-trend difference was detected" in s for s in causal_claim["allowed_phrasing"]))
        self.assertIn("Parallel trends proven.", causal_claim["prohibited_phrasing"])

    def test_sec22_13_micro_vs_macro_f1(self):
        """Sec 22 Test 13: Verify exact object counts and separation of micro F1, macro F1, and cross-sector F1."""
        micro_f1_metric = self.metrics_by_id["METRIC_PERC_003_MICRO_F1"]
        macro_f1_metric = self.metrics_by_id["METRIC_PERC_004_MACRO_F1"]
        cross_mean_metric = self.metrics_by_id["METRIC_PERC_005_CROSS_SECTOR_MEAN_F1"]
        micro_prec_metric = self.metrics_by_id["METRIC_PERC_001_MICRO_PRECISION"]
        micro_rec_metric = self.metrics_by_id["METRIC_PERC_002_MICRO_RECALL"]

        self.assertEqual(micro_prec_metric["value"], 0.9136)
        self.assertEqual(micro_rec_metric["value"], 0.8924)
        self.assertEqual(micro_f1_metric["value"], 0.9029)
        self.assertEqual(macro_f1_metric["value"], 0.8983)
        self.assertEqual(cross_mean_metric["value"], 0.8845)

        # Ensure distinct aggregation levels
        self.assertEqual(micro_f1_metric["aggregation"], "MICRO_OBJECT_LEVEL")
        self.assertEqual(macro_f1_metric["aggregation"], "MACRO_CLASS_LEVEL")
        self.assertEqual(cross_mean_metric["aggregation"], "SECTOR_MEAN_LEVEL")

    def test_sec22_14_trajectory_vs_recording_cluster_bootstrap(self):
        """Sec 22 Test 14: Verify tracking IDF1 trajectory bootstrap [90.57%, 92.95%] vs recording cluster [89.42%, 93.85%]."""
        self.assertTrue(self.tracking_sens_path.exists())
        with open(self.tracking_sens_path, "r", encoding="utf-8") as f:
            tdata = json.load(f)

        self.assertEqual(tdata["point_estimate_idf1"], 0.9180)
        traj_ci = tdata["sensitivity_comparison"]["TRAJECTORY_BLOCK_BOOTSTRAP"]["ci_95"]
        rec_ci = tdata["sensitivity_comparison"]["RECORDING_CLUSTER_BOOTSTRAP"]["ci_95"]
        self.assertEqual(traj_ci, [0.9057, 0.9295])
        self.assertEqual(rec_ci, [0.8942, 0.9385])
        # Recording cluster interval is strictly wider due to recording-level intra-cluster correlation
        self.assertGreater(rec_ci[1] - rec_ci[0], traj_ci[1] - traj_ci[0])

    def test_sec22_15_prohibition_six_new_physical_experiments(self):
        """Sec 22 Test 15: Verify strict prohibition of 'six new physical experiments' claim."""
        self.assertTrue(self.claims_audit_path.exists())
        with open(self.claims_audit_path, "r", encoding="utf-8") as f:
            cdata = json.load(f)["audited_claims"]

        interv_claim = [c for c in cdata if c["claim_area"] == "INTERVENTION_PROVENANCE"][0]
        self.assertIn("Six new physical experiments.", interv_claim["prohibited_phrasing"])
        self.assertIn("Six documented intervention cases, including one newly captured prospective physical case, two historical physical cases, and three replayed cases.", 
                      interv_claim["allowed_phrasing"])

        # Verify intervention registry strictly separates the counts
        with open(self.reconciliation_dir / "intervention_provenance_registry.json", "r", encoding="utf-8") as f:
            idata = json.load(f)

        counts = idata["counts"]
        self.assertEqual(counts["new_physical_evidence_count"], 1)
        self.assertNotEqual(counts["new_physical_evidence_count"], 6)

    # =========================================================================
    # RECONCILIATION INTEGRITY, CANONICAL REGISTRY, AND RELEASE GATE TESTS
    # =========================================================================

    def test_23_reconciliation_manifest_integrity(self):
        """Test 23: Verify all 15 reconciliation artifacts have zero hash drift against manifest."""
        self.assertTrue(self.recon_manifest_path.exists())
        with open(self.recon_manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["reconciliation_gate"], "FULL_RECONCILIATION_PASSED")
        self.assertEqual(manifest["release"], "V3.3.2_FINAL_RECONCILED")
        self.assertGreaterEqual(len(manifest["reconciliation_artifacts"]), 15)

        for filename, meta in manifest["reconciliation_artifacts"].items():
            full_path = self.reconciliation_dir / filename
            self.assertTrue(full_path.exists(), f"Reconciliation artifact missing: {filename}")
            current_hash = compute_sha256(full_path)
            self.assertEqual(current_hash, meta["sha256"], f"Hash drift in reconciliation artifact {filename}")

    def test_24_canonical_metric_registry_decision_layers(self):
        """Test 24: Verify canonical metric registry specifies all 9 decision layers and complete schema."""
        self.assertTrue(self.metric_reg_path.exists())
        with open(self.metric_reg_path, "r", encoding="utf-8") as f:
            reg = json.load(f)

        expected_layers = {
            "PERCEPTION", "TRACKING", "GEOMETRY", "UNCERTAINTY", 
            "HAZARD", "EVENT", "POLICY", "INTERVENTION", "CAUSAL"
        }
        self.assertEqual(set(reg["allowed_decision_layers"]), expected_layers)

        found_layers = set()
        required_keys = {
            "metric_id", "metric_name", "numerator", "denominator", "value", 
            "unit", "population", "split", "aggregation", "decision_layer", 
            "source_artifact", "status"
        }

        for m in reg["metrics"]:
            self.assertTrue(required_keys.issubset(set(m.keys())), f"Incomplete metric keys in {m['metric_id']}")
            self.assertIn(m["decision_layer"], expected_layers)
            self.assertIn(m["status"], {"CONFIRMED", "NOT_RECONSTRUCTABLE", "EVIDENCE_GAP"})
            found_layers.add(m["decision_layer"])

        self.assertEqual(found_layers, expected_layers, "Not all 9 decision layers represented in metric registry")

    def test_25_v3_3_2_immutability(self):
        """Test 25: Verify all 39 V3.3.2 baseline artifacts have zero hash drift."""
        manifest_path = self.baseline_dir / "v3_3_2_source_hash_manifest.json"
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertGreaterEqual(manifest["total_protected_files"], 35)
        for rel_path, meta in manifest["files"].items():
            full_path = WORKSPACE_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Protected file missing: {rel_path}")
            current_hash = compute_sha256(full_path)
            self.assertEqual(current_hash, meta["sha256"], f"Hash drift in {rel_path}")

    def test_26_release_gate_and_report_sync(self):
        """Test 26: Verify release decision and report synchronize on V3.3.2_FINAL_RECONCILED and V3.3.3_READY_WITH_LIMITATIONS."""
        self.assertTrue(self.release_decision_path.exists())
        with open(self.release_decision_path, "r", encoding="utf-8") as f:
            dec = json.load(f)

        self.assertEqual(dec["v3_3_2_reconciled_status"], "V3.3.2_FINAL_RECONCILED")
        self.assertEqual(dec["readiness_status"], "V3.3.3_READY_WITH_LIMITATIONS")
        self.assertEqual(dec["reconciliation_gate"], "FULL_RECONCILIATION_PASSED")

        with open(self.report_path, "r", encoding="utf-8") as f:
            text = f.read()

        self.assertIn("V3.3.2_FINAL_RECONCILED", text)
        self.assertIn("V3.3.3_READY_WITH_LIMITATIONS", text)
        self.assertIn("FULL_RECONCILIATION_PASSED", text)
        self.assertIn("OPERATIONAL_SAFETY_STATUS: NOT_ESTABLISHED_FOR_THE_26_UNCOVERED_OOS_POINTS", text)

    def test_27_model_h_formula_parameters(self):
        """Test 27: Verify exact mathematical formula and locked parameter values for Model H."""
        lineage_file = self.reconciliation_dir / "model_h_lineage.json"
        self.assertTrue(lineage_file.exists())
        with open(lineage_file, "r", encoding="utf-8") as f:
            hdata = json.load(f)

        self.assertEqual(hdata["model"], "MODEL_H")
        self.assertEqual(hdata["parameters"]["k0"], 2.40)
        self.assertEqual(hdata["parameters"]["beta_d"], 0.08)
        self.assertEqual(hdata["parameters"]["beta_l"], 0.12)
        self.assertEqual(hdata["parameters"]["beta_pitch"], 0.22)
        self.assertEqual(hdata["parameters"]["pitch_threshold_deg"], 40.0)
        self.assertTrue(hdata["locked_before_blind"])

    def test_28_refusal_independence_sample_units(self):
        """Test 28: Verify scenario-level and decision-level sample unit independence in refusal benchmarks."""
        self.assertTrue(self.refusal_indep_path.exists())
        with open(self.refusal_indep_path, "r", encoding="utf-8") as f:
            rdata = json.load(f)

        boundary = rdata["benchmark_sample_units"]["boundary_stress_benchmark"]
        self.assertEqual(boundary["scenario_count"], 10)
        self.assertEqual(boundary["frame_count"], 150)
        self.assertEqual(boundary["scenario_level_appropriate_refusal_rate"], 1.0)
        self.assertEqual(boundary["decision_level_appropriate_refusal_rate"], 1.0)

        nominal = rdata["benchmark_sample_units"]["nominal_operational_benchmark"]
        self.assertEqual(nominal["scenario_count"], 25)
        self.assertEqual(nominal["frame_count"], 500)
        self.assertEqual(nominal["scenario_level_false_refusal_rate"], 0.0)
        self.assertEqual(nominal["decision_level_false_refusal_rate"], 0.0)

    def test_29_distribution_shift_stress_battery(self):
        """Test 29: Verify distribution shift stress battery retains 0 unsafe non-refusals."""
        with open(self.refusal_indep_path, "r", encoding="utf-8") as f:
            rdata = json.load(f)

        shift = rdata["benchmark_sample_units"]["distribution_shift_stress_battery"]
        self.assertEqual(shift["scenario_count"], 50)
        self.assertEqual(shift["frame_count"], 500)
        self.assertEqual(shift["unsafe_non_refusals"], 0)
        self.assertEqual(shift["unsafe_non_refusal_rate"], 0.0)

    def test_30_experiment_registry_priority_order(self):
        """Test 30: Verify V3.3.3 experiment registry preserves canonical priority order."""
        self.assertTrue(self.exp_reg_path.exists())
        with open(self.exp_reg_path, "r", encoding="utf-8") as f:
            edata = json.load(f)["experiments"]

        expected_order = [
            "EXP_333_01_EXTERNAL_FACILITY",
            "EXP_333_02_PROSPECTIVE_BACKFIRE",
            "EXP_333_03_OOS_UNCERTAINTY_CROSS_CAMERA",
            "EXP_333_04_WIDEBaseline_REID",
            "EXP_333_05_REAL_LONG_DURATION",
            "EXP_333_06_DISTRIBUTION_SHIFT_REFUSAL"
        ]
        actual_order = [e["experiment_id"] for e in edata]
        self.assertEqual(actual_order, expected_order)

    def test_31_blind_lock_manifests(self):
        """Test 31: Verify all 4 blind lock manifests exist with LOCKED_PRE_EVALUATION."""
        manifests = ["blind_dataset_hash.json", "parameter_lock.json", "code_lock.json", "experiment_lock.json"]
        for m in manifests:
            p = self.blind_lock_dir / m
            self.assertTrue(p.exists(), f"Missing lock manifest: {m}")
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["status"], "LOCKED_PRE_EVALUATION")

    def test_32_claims_language_audit_structure(self):
        """Test 32: Verify claims language audit registry contains all audited claim areas."""
        self.assertTrue(self.claims_audit_path.exists())
        with open(self.claims_audit_path, "r", encoding="utf-8") as f:
            cdata = json.load(f)

        self.assertEqual(cdata["audit_conclusion"], "ALL_PROHIBITED_PHRASES_INTERCEPTED_AND_BANNED")
        areas = {c["claim_area"] for c in cdata["audited_claims"]}
        expected_areas = {
            "UNCERTAINTY_COVERAGE",
            "OPERATIONAL_SAFETY_AND_ACTION_WIDTH",
            "MULTI_FACILITY_GENERALIZATION",
            "INTERVENTION_PROVENANCE",
            "CAUSAL_INFERENCE_AND_DID",
            "FAILURE_STATE_SEMANTICS"
        }
        self.assertEqual(areas, expected_areas)

if __name__ == "__main__":
    unittest.main()
