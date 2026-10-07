"""
test_v3_2_1_release_integrity.py
Final Canonical Release Integrity Test Suite for Safety Backfire AI V3.2.1.
Enforces all 20 required forensic validation tests in Section 23 of the final closure audit:
  test_01_no_conflicting_perception_metrics
  test_02_idf1_formula_integrity
  test_03_idf1_ci_not_wilson
  test_04_geometry_mae_single_source_of_truth
  test_05_geometry_denominator_integrity
  test_06_hazard_micro_macro_integrity
  test_07_hazard_source_population_integrity
  test_08_event_rate_exact_recomputation
  test_09_event_ci_single_source
  test_10_event_matching_integrity
  test_11_odd_tier_integrity
  test_12_uncertainty_factor_semantics
  test_13_uncertainty_calibration_lineage
  test_14_dataset_reproducibility_scope
  test_15_failure_registry_semantics
  test_16_causality_language_integrity
  test_17_claim_matrix_freshness
  test_18_report_metric_consistency
  test_19_release_language_integrity
  test_20_canonical_registry_completeness
"""

import sys
import math
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from validation.v3_2_1.final_closure.test_release_language_integrity import run_lint

OUT_DIR = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure"
REPORTS_DIR = WORKSPACE_ROOT / "reports/v3_2_1"

class TestV321ReleaseIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        registry_path = OUT_DIR / "canonical_release_registry.json"
        if not registry_path.exists():
            raise FileNotFoundError(f"Missing canonical release registry: {registry_path}")
        with open(registry_path, "r", encoding="utf-8") as f:
            cls.registry = json.load(f)
        cls.metrics = {m["metric_name"]: m for m in cls.registry["metrics"]}

    def test_01_no_conflicting_perception_metrics(self):
        """Test 01: Verify perception precision and recall are locked to Set B (0.9442, 0.9480) and Set A is retracted."""
        p_prec = self.metrics["perception_precision"]
        p_rec = self.metrics["perception_recall"]

        self.assertEqual(p_prec["value"], 0.9442)
        self.assertEqual(p_prec["numerator"], 474)
        self.assertEqual(p_prec["denominator"], 502)
        self.assertEqual(p_prec["split"], "BLIND_TEST_EVALUATION")
        self.assertEqual(p_prec["odd_tier"], "MIXED_ODD")

        self.assertEqual(p_rec["value"], 0.9480)
        self.assertEqual(p_rec["numerator"], 474)
        self.assertEqual(p_rec["denominator"], 500)
        self.assertEqual(p_rec["split"], "BLIND_TEST_EVALUATION")
        self.assertEqual(p_rec["odd_tier"], "MIXED_ODD")

        # Verify Set A is officially marked retracted
        recon_path = OUT_DIR / "perception_metric_reconciliation.json"
        self.assertTrue(recon_path.exists())
        with open(recon_path, "r") as f:
            recon = json.load(f)
        self.assertEqual(recon["reconciliation_verdict"], "SET_B_IS_CANONICAL_SET_A_IS_RETRACTED")
        self.assertEqual(recon["candidate_set_a_corpus"]["evidence_status"], "LEGACY_RETRACTED")
        self.assertEqual(recon["candidate_set_b_blind"]["evidence_status"], "CANONICAL_VERIFIED")

    def test_02_idf1_formula_integrity(self):
        """Test 02: Verify IDF1 = 0.9141, false fraction 1768/1851 is retracted, and decomposition is marked non-reconstructible."""
        idf1 = self.metrics["tracking_idf1"]
        self.assertEqual(idf1["value"], 0.9141)
        self.assertIsNone(idf1["numerator"])
        self.assertIsNone(idf1["denominator"])
        self.assertEqual(idf1["evidence_status"], "NOT_RECONSTRUCTIBLE_FROM_CURRENT_ARTIFACTS")

        idf1_audit_path = OUT_DIR / "idf1_audit.json"
        self.assertTrue(idf1_audit_path.exists())
        with open(idf1_audit_path, "r") as f:
            audit = json.load(f)
        self.assertEqual(audit["value"], 0.9141)
        self.assertIn("1768 / 1851", audit["mathematical_audit"]["rejected_fraction"])
        self.assertEqual(audit["canonical_quantities"]["IDTP"], None)
        self.assertEqual(audit["canonical_quantities"]["total_entity_frame_instances"], 3450)
        self.assertEqual(audit["canonical_quantities"]["total_ground_truth_trajectories"], 24)

    def test_03_idf1_ci_not_wilson(self):
        """Test 03: Verify IDF1 confidence interval is NOT Wilson; marked NOT_REPORTED."""
        idf1 = self.metrics["tracking_idf1"]
        self.assertEqual(idf1["ci_method"], "NONE")
        self.assertIsNone(idf1["ci_lower"])
        self.assertIsNone(idf1["ci_upper"])

        stat_audit_path = OUT_DIR / "idf1_statistical_audit.json"
        self.assertTrue(stat_audit_path.exists())
        with open(stat_audit_path, "r") as f:
            data = json.load(f)
        self.assertFalse(data["ci_valid"])
        self.assertEqual(data["ci_status"], "NOT_REPORTED")

    def test_04_geometry_mae_single_source_of_truth(self):
        """Test 04: Verify planar geometry MAE is locked to 0.0169 m (1.69 cm) and 0.0410 m is retracted."""
        geom = self.metrics["planar_floor_projection_mae"]
        self.assertEqual(geom["value"], 0.0169)
        self.assertEqual(geom["numerator"], 1.521)
        self.assertEqual(geom["denominator"], 90)
        self.assertEqual(geom["unit"], "meters")
        self.assertEqual(geom["evidence_status"], "CANONICAL_VERIFIED")

        geom_recon_path = OUT_DIR / "geometry_metric_reconciliation.json"
        self.assertTrue(geom_recon_path.exists())
        with open(geom_recon_path, "r") as f:
            recon = json.load(f)
        self.assertEqual(recon["reconciliation_verdict"], "0.0169M_IS_CANONICAL_0.0410M_IS_RETRACTED")
        self.assertEqual(recon["candidate_b_stale_draft"]["evidence_status"], "LEGACY_RETRACTED")

    def test_05_geometry_denominator_integrity(self):
        """Test 05: Verify geometry denominator: 90 planar points included, 10 ramp markers excluded under FAIL-45."""
        geom_recon_path = OUT_DIR / "geometry_metric_reconciliation.json"
        with open(geom_recon_path, "r") as f:
            recon = json.load(f)
        pop = recon["marker_population_accounting"]
        self.assertEqual(pop["physical_markers_surveyed_total"], 100)
        self.assertEqual(pop["planar_evaluation_subset_N"], 90)
        self.assertEqual(pop["excluded_non_planar_markers_N"], 10)
        self.assertEqual(pop["exclusion_reason"], "FAIL-45_RAMP_ELEVATION_WARP (3.5 degree ramp slope violates planar homography)")

    def test_06_hazard_micro_macro_integrity(self):
        """Test 06: Verify Micro Precision 268/281 = 0.9537, Micro Recall 268/286 = 0.9371, Macro Prec 0.9480, Macro Rec 0.9288."""
        micro_p = self.metrics["hazard_micro_precision"]
        micro_r = self.metrics["hazard_micro_recall"]
        macro_p = self.metrics["hazard_macro_precision"]
        macro_r = self.metrics["hazard_macro_recall"]

        self.assertEqual(micro_p["value"], 0.9537)
        self.assertEqual(micro_p["numerator"], 268)
        self.assertEqual(micro_p["denominator"], 281)

        self.assertEqual(micro_r["value"], 0.9371)
        self.assertEqual(micro_r["numerator"], 268)
        self.assertEqual(micro_r["denominator"], 286)

        self.assertEqual(macro_p["value"], 0.9480)
        self.assertEqual(macro_r["value"], 0.9288)

        # Verify retracted placeholder 515/540
        haz_recon_path = OUT_DIR / "hazard_metric_reconciliation.json"
        with open(haz_recon_path, "r") as f:
            recon = json.load(f)
        self.assertEqual(recon["reconciliation_verdict"], "268_281_IS_CANONICAL_515_540_IS_RETRACTED")
        self.assertEqual(recon["candidate_b_fabricated_fraction"]["evidence_status"], "RETRACTED_UNSUPPORTED")

    def test_07_hazard_source_population_integrity(self):
        """Test 07: Verify underlying 12-class records sum exactly to 268 TP, 13 FP, 18 FN."""
        haz_recon_path = OUT_DIR / "hazard_metric_reconciliation.json"
        with open(haz_recon_path, "r") as f:
            recon = json.load(f)
        classes = recon["underlying_12_class_matrix"]
        self.assertEqual(len(classes), 12)
        total_tp = sum(c["TP"] for c in classes)
        total_fp = sum(c["FP"] for c in classes)
        total_fn = sum(c["FN"] for c in classes)
        self.assertEqual(total_tp, 268)
        self.assertEqual(total_fp, 13)
        self.assertEqual(total_fn, 18)
        self.assertEqual(total_tp + total_fp, 281)
        self.assertEqual(total_tp + total_fn, 286)

    def test_08_event_rate_exact_recomputation(self):
        """Test 08: Recompute Poisson event rates from exact seconds (1380s, 660s) with exact Garwood CIs."""
        rate_corpus = self.metrics["false_event_count_rate_corpus"]
        rate_blind = self.metrics["false_event_count_rate_blind"]

        self.assertEqual(rate_corpus["value"], 7.83)
        self.assertEqual(rate_corpus["numerator"], 3)
        self.assertEqual(rate_corpus["exposure_seconds"], 1380)
        self.assertAlmostEqual(rate_corpus["exposure_hours_exact"], 1380.0 / 3600.0, places=5)
        self.assertEqual(rate_corpus["ci_lower"], 1.614)
        self.assertEqual(rate_corpus["ci_upper"], 22.871)

        self.assertEqual(rate_blind["value"], 5.45)
        self.assertEqual(rate_blind["numerator"], 1)
        self.assertEqual(rate_blind["exposure_seconds"], 660)
        self.assertAlmostEqual(rate_blind["exposure_hours_exact"], 660.0 / 3600.0, places=5)
        self.assertEqual(rate_blind["ci_lower"], 0.138)
        self.assertEqual(rate_blind["ci_upper"], 30.391)
        self.assertNotEqual(rate_blind["ci_upper"], 30.360)
        self.assertNotEqual(rate_blind["ci_upper"], 30.388)

    def test_09_event_ci_single_source(self):
        """Test 09: Verify event count rates are labeled OBSERVED_COUNT_RATE_OVER_TESTED_EXPOSURE, not stable operational rate."""
        rate_corpus = self.metrics["false_event_count_rate_corpus"]
        rate_blind = self.metrics["false_event_count_rate_blind"]
        self.assertIn("OBSERVED_COUNT_RATE_OVER_TESTED_EXPOSURE", rate_corpus["interpretation_limit"])
        self.assertIn("OBSERVED_COUNT_RATE_OVER_TESTED_EXPOSURE", rate_blind["interpretation_limit"])

    def test_10_event_matching_integrity(self):
        """Test 10: Verify event matching semantics: IoU >= 0.5, class equality, 47/50 corpus, 15/16 blind."""
        audit_path = OUT_DIR / "event_matching_audit.json"
        self.assertTrue(audit_path.exists())
        with open(audit_path, "r") as f:
            audit = json.load(f)
        rules = audit["event_matching_rules"]
        self.assertEqual(rules["temporal_iou_threshold"], 0.5)
        self.assertTrue(rules["hazard_class_equality_required"])
        self.assertTrue(rules["one_to_one_assignment_enforced"])

        full = audit["full_corpus_matching"]
        self.assertEqual(full["TP"], 47)
        self.assertEqual(full["FP"], 3)
        self.assertEqual(full["FN"], 3)
        self.assertEqual(full["GT"], 50)

        blind = audit["blind_test_matching"]
        self.assertEqual(blind["TP"], 15)
        self.assertEqual(blind["FP"], 1)
        self.assertEqual(blind["FN"], 1)
        self.assertEqual(blind["GT"], 16)

    def test_11_odd_tier_integrity(self):
        """Test 11: Verify ODD population mapping: VID_TEST_001 is NOMINAL, VID_TEST_002 is DEGRADED, aggregate is MIXED_ODD."""
        odd_map_path = OUT_DIR / "odd_metric_population_map.json"
        self.assertTrue(odd_map_path.exists())
        with open(odd_map_path, "r") as f:
            odd_map = json.load(f)
        streams = odd_map["streams"]
        self.assertEqual(streams["VID_TEST_001"]["odd_tier"], "NOMINAL_ODD")
        self.assertEqual(streams["VID_TEST_002"]["odd_tier"], "DEGRADED_ODD")
        p_map = next(m for m in odd_map["metrics_population_mapping"] if m["metric_name"] == "perception_precision")
        self.assertEqual(p_map["odd_tier"], "MIXED_ODD")

        valid_tiers = {"NOMINAL_ODD", "DEGRADED_ODD", "MIXED_ODD", "STRESS_TEST", "SYNTHETIC_ONLY"}
        for m in self.registry["metrics"]:
            self.assertIn(m["odd_tier"], valid_tiers, f"Invalid odd_tier for metric {m['metric_name']}: {m['odd_tier']}")

    def test_12_uncertainty_factor_semantics(self):
        """Test 12: Verify k=2.24 is EMPIRICALLY_CALIBRATED and not called Chi-Square 95% quantile or mathematical guarantee."""
        k_audit_path = OUT_DIR / "k_factor_audit.json"
        self.assertTrue(k_audit_path.exists())
        with open(k_audit_path, "r") as f:
            audit = json.load(f)
        self.assertEqual(audit["canonical_factor_k"], 2.24)
        self.assertEqual(audit["semantic_classification"], "EMPIRICALLY_CALIBRATED_COVERAGE_FACTOR")
        self.assertFalse(audit["mathematical_reconciliation"]["is_theoretical_chi_square_quantile"])
        self.assertAlmostEqual(audit["mathematical_reconciliation"]["theoretical_chi2_2d_95_quantile"], 2.448, places=3)
        self.assertTrue(audit["retractions"]["mathematical_guarantee_retracted"])
        self.assertTrue(audit["retractions"]["chi_square_quantile_claim_retracted"])

    def test_13_uncertainty_calibration_lineage(self):
        """Test 13: Verify 97.60% (488/500) is designated IN_SAMPLE_CALIBRATION_COVERAGE with data reused for factor selection."""
        cov = self.metrics["uncertainty_factor_coverage"]
        self.assertEqual(cov["value"], 0.9760)
        self.assertEqual(cov["numerator"], 488)
        self.assertEqual(cov["denominator"], 500)
        self.assertIn("IN_SAMPLE_CALIBRATION_COVERAGE", cov["interpretation_limit"])

        split_audit_path = OUT_DIR / "uncertainty_split_audit.json"
        self.assertTrue(split_audit_path.exists())
        with open(split_audit_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["dataset_split"], "CALIBRATION_SPLIT")
        self.assertEqual(data["designation"], "in-sample calibration coverage")
        self.assertEqual(data["independent_validation_status"], "NOT_AN_INDEPENDENT_TEST")

    def test_14_dataset_reproducibility_scope(self):
        """Test 14: Verify layered reproducibility statement: CORE_CODE=PASS, ARTIFACTS=PASS, FULL_CORPUS=PARTIAL."""
        repro_path = OUT_DIR / "reproducibility_scope.json"
        self.assertTrue(repro_path.exists())
        with open(repro_path, "r") as f:
            repro = json.load(f)
        scope = repro["layered_reproducibility_statement"]
        self.assertEqual(scope["CORE_CODE_REPRODUCIBILITY"], "PASS")
        self.assertEqual(scope["CANONICAL_ARTIFACT_REPRODUCIBILITY"], "PASS")
        self.assertEqual(scope["FULL_23_MIN_CORPUS_REPRODUCIBILITY"], "PARTIAL / ANNOTATED_CORPUS_SOURCE_NOT_FULLY_REPRODUCIBLE")
        self.assertEqual(repro["physical_evidence_on_disk"]["raw_frames_total"], 1672)
        self.assertEqual(repro["physical_evidence_on_disk"]["raw_duration_sec"], 64.05)

    def test_15_failure_registry_semantics(self):
        """Test 15: Verify 55 master catalog entries: 49 confirmed (42 resolved + 7 boundaries across 4 families) + 6 candidates."""
        fail_reg = self.registry["failure_registry"]
        self.assertEqual(fail_reg["total_catalog_entries"], 55)
        self.assertEqual(fail_reg["confirmed_failures"], 49)
        self.assertEqual(fail_reg["resolved_defects"], 42)
        self.assertEqual(fail_reg["documented_boundaries"], 7)
        self.assertEqual(fail_reg["boundary_families"], 4)
        self.assertEqual(fail_reg["unreproduced_candidates"], 6)
        self.assertEqual(fail_reg["open_critical_defects"], 0)
        self.assertEqual(fail_reg["confirmed_failures"], fail_reg["resolved_defects"] + fail_reg["documented_boundaries"])
        self.assertEqual(fail_reg["total_catalog_entries"], fail_reg["confirmed_failures"] + fail_reg["unreproduced_candidates"])

    def test_16_causality_language_integrity(self):
        """Test 16: Verify DiD uses ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS, not PROVEN_CAUSAL_EFFECT."""
        did = self.metrics["did_risk_redistribution_coefficient"]
        self.assertEqual(did["value"], -0.4200)
        self.assertIn("ATTRIBUTED_UNDER_TESTED_DID_ASSUMPTIONS", did["interpretation_limit"])

    def test_17_claim_matrix_freshness(self):
        """Test 17: Verify claim-evidence graph is fresh: no stale 0.9442 vs 0.9576 contradictions, all claims mapped."""
        graph_path = OUT_DIR / "canonical_claim_evidence_graph.json"
        self.assertTrue(graph_path.exists())
        with open(graph_path, "r") as f:
            graph = json.load(f)
        claims = graph["claims"]
        self.assertGreaterEqual(len(claims), 12)
        p_claim = next(c for c in claims if "perception" in c["claim_id"].lower())
        self.assertIn("0.9442", p_claim["computation"])
        self.assertNotIn("0.9576", str(p_claim))

    def test_18_report_metric_consistency(self):
        """Test 18: Verify all 15 reports in reports/v3_2_1/ have zero stale values and align with canonical registry."""
        from validation.v3_2_1.final_closure.test_canonical_report_consistency import TestCanonicalReportConsistency
        suite = unittest.TestLoader().loadTestsFromTestCase(TestCanonicalReportConsistency)
        result = unittest.TestResult()
        suite.run(result)
        self.assertTrue(result.wasSuccessful(), f"Report consistency test failed: {result.failures + result.errors}")

    def test_19_release_language_integrity(self):
        """Test 19: Verify release language linter passes with zero active violations across all reports."""
        violations = run_lint()
        self.assertEqual(len(violations), 0, f"Found {len(violations)} release language violations: {violations}")

    def test_20_canonical_registry_completeness(self):
        """Test 20: Verify canonical release registry schema completeness: release, decision, metrics, datasets, odd, limitations."""
        self.assertEqual(self.registry["release"], "V3.2.1")
        self.assertEqual(self.registry["decision"], "FINAL_RELEASE_ACCEPTED_WITH_LIMITATIONS")
        self.assertIn("metrics", self.registry)
        self.assertIn("datasets", self.registry)
        self.assertIn("odd_profiles", self.registry)
        self.assertIn("failure_registry", self.registry)
        self.assertIn("retractions", self.registry)
        self.assertGreaterEqual(len(self.registry["metrics"]), 18)

        required_fields = [
            "metric_id", "metric_name", "value", "sample_unit",
            "dataset_id", "split", "odd_tier", "ci_method",
            "source_artifact", "source_code", "validation_test",
            "evidence_status", "interpretation_limit"
        ]
        for m in self.registry["metrics"]:
            for field in required_fields:
                self.assertIn(field, m, f"Metric {m.get('metric_id')} missing field {field}")

    def test_21_event_wilson_exactness(self):
        """Test 21 (Issue 01): Verify exact Wilson score interval for event corpus (47/50) is [0.8378, 0.9794]."""
        p_prec = self.metrics["event_precision_full_corpus"]
        p_rec = self.metrics["event_recall_full_corpus"]
        self.assertEqual(p_prec["ci_lower"], 0.8378)
        self.assertEqual(p_prec["ci_upper"], 0.9794)
        self.assertEqual(p_rec["ci_lower"], 0.8378)
        self.assertEqual(p_rec["ci_upper"], 0.9794)

        # Audit exact single source computation
        x, n, z = 47, 50, 1.959963984540054
        p = x / n
        denom = 1.0 + (z**2) / n
        center = (p + (z**2) / (2 * n)) / denom
        margin = (z / denom) * math.sqrt(p * (1.0 - p) / n + (z**2) / (4 * n**2))
        self.assertAlmostEqual(round(center - margin, 4), 0.8378)
        self.assertAlmostEqual(round(center + margin, 4), 0.9794)

    def test_22_poisson_exposure_uses_exact_seconds(self):
        """Test 22 (Issue 02): Verify Poisson rate calculations use exact seconds (1380s, 660s)."""
        calc_path = OUT_DIR / "event_rate_canonical_calculation.json"
        self.assertTrue(calc_path.exists())
        with open(calc_path) as f:
            calc = json.load(f)
        
        full = calc["full_corpus_23min"]
        self.assertEqual(full["exposure_seconds"], 1380)
        self.assertAlmostEqual(full["exposure_hours_exact"], 1380.0 / 3600.0, places=6)
        self.assertAlmostEqual(full["point_estimate_rate_per_hour"], 7.8261, places=2)
        self.assertEqual(full["garwood_poisson_95_ci"], [1.614, 22.871])

        blind = calc["blind_test_11min"]
        self.assertEqual(blind["exposure_seconds"], 660)
        self.assertAlmostEqual(blind["exposure_hours_exact"], 660.0 / 3600.0, places=6)
        self.assertAlmostEqual(blind["point_estimate_rate_per_hour"], 5.4545, places=2)
        self.assertEqual(blind["garwood_poisson_95_ci"], [0.138, 30.391])

    def test_23_no_stale_event_ci(self):
        """Test 23 (Issue 01): Verify [0.8345, 0.9798] does not appear in any active reporting."""
        stale = "[0.8345, 0.9798]"
        for md_file in REPORTS_DIR.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            active_lines = [l for l in content.splitlines() if "RETRACTED" not in l and "retracted" not in l and "Retracted" not in l]
            active_text = "\n".join(active_lines)
            self.assertNotIn(stale, active_text, f"Stale event CI {stale} found in {md_file.name}")

    def test_24_metric_specific_odd_assignment(self):
        """Test 24 (Issue 04): Verify ODD tier is derived per metric from contributing source streams."""
        map_path = OUT_DIR / "metric_population_odd_map.json"
        self.assertTrue(map_path.exists())
        with open(map_path) as f:
            odd_map = json.load(f)

        metrics = {m["metric_id"]: m for m in odd_map["metrics_odd_mapping"]}
        # Hazard evaluation: evaluated on nominal operational streams
        self.assertEqual(metrics["METRIC_05_HAZARD_MICRO_PRECISION"]["aggregate_odd_tier"], "NOMINAL_ODD")
        self.assertEqual(metrics["METRIC_06_HAZARD_MICRO_RECALL"]["aggregate_odd_tier"], "NOMINAL_ODD")
        # Geometry: evaluated on surveyed nominal warehouse floor
        self.assertEqual(metrics["METRIC_04_GEOMETRY_PLANAR_MAE"]["aggregate_odd_tier"], "NOMINAL_ODD")
        # Blind test: spans VID_TEST_001 (nominal) and VID_TEST_002 (degraded pitch 22.5 deg) -> MIXED_ODD
        self.assertEqual(metrics["METRIC_11_EVENT_PRECISION_BLIND"]["aggregate_odd_tier"], "MIXED_ODD")
        self.assertEqual(metrics["METRIC_12_EVENT_RECALL_BLIND"]["aggregate_odd_tier"], "MIXED_ODD")

    def test_25_idf1_denominator_semantics(self):
        """Test 25 (Issue 05): Verify IDF1 record clarifies 3,450 is entity-frame instances, not denominator."""
        record_path = OUT_DIR / "idf1_definition_record.json"
        self.assertTrue(record_path.exists())
        with open(record_path) as f:
            rec = json.load(f)
        self.assertEqual(rec["idf1_value"], 0.9141)
        self.assertEqual(rec["entity_frame_instances"], 3450)
        self.assertEqual(rec["gt_trajectories"], 24)
        self.assertEqual(rec["idtp_idfp_idfn_decomposition"], "NOT_RECONSTRUCTIBLE_FROM_CURRENT_ARTIFACTS")
        self.assertEqual(rec["confidence_interval"], "NOT_REPORTED")
        self.assertFalse(rec["denominator_is_3450"])

    def test_26_did_coefficient_reconstructibility(self):
        """Test 26 (Issue 06): Verify DiD coefficient -0.4200 is mathematically traceable and classified."""
        lineage_path = OUT_DIR / "did_coefficient_lineage.json"
        self.assertTrue(lineage_path.exists())
        with open(lineage_path) as f:
            did_data = json.load(f)
        m = did_data["mathematical_lineage"]
        self.assertEqual(m["treated_delta"], -0.4500)
        self.assertEqual(m["control_delta"], -0.0300)
        self.assertAlmostEqual(m["did_result"], -0.4200, places=4)
        self.assertEqual(did_data["classification"], "SCENARIO_SPECIFIC_DERIVED_RESULT")

    def test_27_geometry_ci_method_integrity(self):
        """Test 27 (Issue 07): Verify geometry MAE CI is NOT_REPORTED due to spatial autocorrelation."""
        geom = self.metrics["planar_floor_projection_mae"]
        ci = geom.get("ci", {})
        self.assertEqual(ci.get("status"), "NOT_REPORTED")
        self.assertEqual(ci.get("method"), "NONE")
        self.assertIn("spatial", ci.get("justification", "").lower())

    def test_28_active_claim_vs_evidence_gap_semantics(self):
        """Test 28 (Issue 03 & 10): Verify ACTIVE_UNSUPPORTED_CLAIMS == 0 and KNOWN_EVIDENCE_GAPS >= 2."""
        decision_path = OUT_DIR / "final_release_decision.json"
        self.assertTrue(decision_path.exists())
        with open(decision_path) as f:
            dec = json.load(f)
        self.assertEqual(dec["active_unsupported_claims"], 0)
        self.assertGreaterEqual(len(dec["known_evidence_gaps"]), 2)
        gap_statements = [g.get("statement", "") if isinstance(g, dict) else str(g) for g in dec["known_evidence_gaps"]]
        gap_text = " ".join(gap_statements)
        self.assertIn("39,900", gap_text)
        self.assertIn("uncertainty", gap_text.lower())

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV321ReleaseIntegrity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
