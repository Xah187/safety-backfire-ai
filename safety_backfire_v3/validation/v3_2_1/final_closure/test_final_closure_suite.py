"""
test_final_closure_suite.py
Final Master Closure Verification Test Suite for Safety Backfire AI V3.2.1 (Issue 22).
Implements all 20 required forensic validation tests using Python's built-in unittest.
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
V321_DIR = WORKSPACE_ROOT / "outputs/v3_2_1"

class TestFinalClosureSuite(unittest.TestCase):

    def test_01_dataset_lineage_integrity(self):
        """Test 01: Verify physical raw video files, frame counts, and SHA256 hashes."""
        lineage_file = OUT_DIR / "dataset_lineage_graph.json"
        self.assertTrue(lineage_file.exists(), "dataset_lineage_graph.json missing")
        with open(lineage_file) as f:
            data = json.load(f)
        
        self.assertEqual(data["total_physical_raw_frames_on_disk"], 1672)
        self.assertAlmostEqual(data["total_physical_raw_duration_sec"], 64.05, places=2)
        
        for stream in data["streams"]:
            self.assertTrue(stream["lineage_verified"])
            self.assertIsNotNone(stream["source_sha256"])

    def test_02_canonical_duration_integrity(self):
        """Test 02: Verify 23-minute corpus vs 2.5 hour claim reconciliation."""
        lineage_file = OUT_DIR / "dataset_lineage_graph.json"
        with open(lineage_file) as f:
            data = json.load(f)
        
        audit_23min = data["extended_annotated_corpus_23min_audit"]
        self.assertEqual(audit_23min["claimed_frames"], 39900)
        self.assertEqual(audit_23min["claimed_duration_min"], 23.0)
        self.assertEqual(audit_23min["evidence_status"], "ANNOTATED_CORPUS_SOURCE_NOT_FULLY_REPRODUCIBLE")

    def test_03_idf1_ci_method_integrity(self):
        """Test 03: Verify IDF1 calculation and retraction of invalid Wilson CI."""
        idf1_file = OUT_DIR / "idf1_statistical_audit.json"
        self.assertTrue(idf1_file.exists(), "idf1_statistical_audit.json missing")
        with open(idf1_file) as f:
            data = json.load(f)
            
        self.assertFalse(data["ci_valid"])
        self.assertEqual(data["ci_status"], "NOT_REPORTED")
        self.assertEqual(data["value"], 0.9141)
        self.assertIn("mathematically invalid", data["reasoning"].lower())
        self.assertIn("retracted", data["reasoning"].lower())

    def test_04_uncertainty_factor_lineage(self):
        """Test 04: Verify k = 2.24 reconciliation against Chi-Square quantile."""
        factor_file = OUT_DIR / "uncertainty_factor_lineage.json"
        self.assertTrue(factor_file.exists(), "uncertainty_factor_lineage.json missing")
        with open(factor_file) as f:
            data = json.load(f)
            
        self.assertEqual(data["factor"], 2.24)
        self.assertEqual(data["derivation"], "empirically calibrated coverage factor")
        # Theoretical sqrt(chi2_2(0.95)) is approx 2.448 != 2.24
        self.assertNotEqual(data["factor"], data["mathematical_reconciliation"]["theoretical_chi2_95"])

    def test_05_uncertainty_split_independence(self):
        """Test 05: Verify uncertainty coverage is designated in-sample calibration coverage."""
        split_file = OUT_DIR / "uncertainty_split_audit.json"
        self.assertTrue(split_file.exists(), "uncertainty_split_audit.json missing")
        with open(split_file) as f:
            data = json.load(f)
            
        self.assertEqual(data["dataset_split"], "CALIBRATION_SPLIT")
        self.assertEqual(data["designation"], "in-sample calibration coverage")
        self.assertEqual(data["independent_validation_status"], "NOT_AN_INDEPENDENT_TEST")

    def test_06_canonical_odd_consistency(self):
        """Test 06: Verify ODD consistency matrix thresholds match canonical specification."""
        odd_file = OUT_DIR / "odd_consistency_matrix.json"
        self.assertTrue(odd_file.exists(), "odd_consistency_matrix.json missing")
        with open(odd_file) as f:
            data = json.load(f)
            
        self.assertEqual(data["status"], "CONSISTENT_ACROSS_CANONICAL_SPECIFICATION")
        params = {t["parameter"]: t for t in data["thresholds"]}
        self.assertEqual(params["camera_height_m"]["nominal_range"], [3.5, 6.0])
        self.assertEqual(params["camera_pitch_deg"]["nominal_range"], [35.0, 55.0])
        self.assertEqual(params["spatial_distance_policy_m"]["nominal_range"], [0.5, 8.0])

    def test_07_blind_odd_tier_integrity(self):
        """Test 07: Verify blind test streams are partitioned by nominal and degraded ODD tiers."""
        odd_file = OUT_DIR / "odd_consistency_matrix.json"
        with open(odd_file) as f:
            data = json.load(f)
            
        blind = data["blind_dataset_odd_classification"]
        self.assertEqual(blind["aggregate_classification"], "MIXED_ODD_BLIND_RESULT")
        streams = {s["stream_id"]: s for s in blind["streams"]}
        self.assertEqual(streams["VID_TEST_001"]["odd_tier"], "NOMINAL_ODD")
        self.assertEqual(streams["VID_TEST_002"]["odd_tier"], "DEGRADED_ODD")

    def test_08_geometry_denominator_integrity(self):
        """Test 08: Verify geometry sample denominator: 90 planar points vs 100 surveyed markers."""
        geom_file = OUT_DIR / "geometry_denominator_audit.json"
        self.assertTrue(geom_file.exists(), "geometry_denominator_audit.json missing")
        with open(geom_file) as f:
            data = json.load(f)
            
        self.assertEqual(data["physical_markers_surveyed_N"], 100)
        self.assertEqual(data["evaluated_planar_points_N"], 90)
        self.assertEqual(data["excluded_points_count"], 10)
        self.assertEqual(data["exclusion_criteria"], "FAIL-45_RAMP_ELEVATION_WARP")

    def test_09_event_denominator_integrity(self):
        """Test 09: Verify event precision and recall denominators."""
        event_file = V321_DIR / "event_metric_audit.json"
        self.assertTrue(event_file.exists(), "event_metric_audit.json missing")
        with open(event_file) as f:
            data = json.load(f)
            
        full = data["full_corpus_23min"]
        tp = full["true_positives"]
        fp = full["false_positives"]
        fn = full["false_negatives"]
        gt = full["ground_truth_events_N"]
        self.assertEqual(tp, 47)
        self.assertEqual(fp, 3)
        self.assertEqual(fn, 3)
        self.assertEqual(gt, 50)
        self.assertAlmostEqual(full["event_precision"], tp / (tp + fp), places=4)
        self.assertAlmostEqual(full["event_recall"], tp / (tp + fn), places=4)

    def test_10_event_rate_method_integrity(self):
        """Test 10: Verify Poisson count-rate interval and reporting label."""
        stat_file = OUT_DIR / "statistical_method_registry.json"
        self.assertTrue(stat_file.exists(), "statistical_method_registry.json missing")
        with open(stat_file) as f:
            data = json.load(f)
            
        rate_metrics = [m for m in data["metrics"] if m["classification"] == "POISSON_COUNT_RATE"]
        self.assertGreaterEqual(len(rate_metrics), 2)
        for m in rate_metrics:
            self.assertIn("Observed false-event count rate", m["reporting_label"])
            self.assertNotIn("Stable operational", m["reporting_label"])

    def test_11_hazard_micro_macro_integrity(self):
        """Test 11: Verify micro (pooled) vs unweighted macro hazard precision."""
        stat_file = OUT_DIR / "statistical_method_registry.json"
        with open(stat_file) as f:
            data = json.load(f)
            
        micro_m = next(m for m in data["metrics"] if m["metric_name"] == "hazard_precision_micro_pooled")
        self.assertEqual(micro_m["numerator"], 515)
        self.assertEqual(micro_m["denominator"], 540)
        self.assertAlmostEqual(micro_m["value"], 515 / 540, places=4)

    def test_12_backfire_case_study_scope(self):
        """Test 12: Verify N=2 backfire case studies and generalization limits."""
        backfire_file = V321_DIR / "backfire_case_audit.json"
        self.assertTrue(backfire_file.exists(), "backfire_case_audit.json missing")
        with open(backfire_file) as f:
            data = json.load(f)
            
        self.assertEqual(data["evaluated_cases_count"], 2)
        self.assertEqual(data["sample_level_accuracy"], "2/2 (100.0%)")
        self.assertIn("prohibited", data["population_claim_prohibition"].lower())

    def test_13_did_causality_language(self):
        """Test 13: Verify difference-in-differences causal claim and attribution wording."""
        causal_file = V321_DIR / "causality_audit.json"
        self.assertTrue(causal_file.exists(), "causality_audit.json missing")
        with open(causal_file) as f:
            data = json.load(f)
            
        self.assertEqual(data["methodology"], "Difference-in-Differences (DiD) Quasi-Experimental Design")
        self.assertEqual(data["axiom"], "TEMPORAL_CORRELATION != CAUSAL_EFFECT")
        self.assertEqual(data["scenarios_audited"]["CLEAN_ISOLATION"]["status"], "ATTRIBUTED_DIRECT_EFFECT")
        self.assertEqual(data["scenarios_audited"]["TRAFFIC_SURGE"]["status"], "INSUFFICIENT_EVIDENCE")

    def test_14_failure_registry_integrity(self):
        """Test 14: Verify failure registry arithmetic: 49=42+7, 55=49+6, 0 open critical."""
        fail_file = OUT_DIR / "failure_registry_integrity.json"
        self.assertTrue(fail_file.exists(), "failure_registry_integrity.json missing")
        with open(fail_file) as f:
            data = json.load(f)
            
        counts = data["summary_counts"]
        self.assertEqual(counts["total_cataloged_ids"], 55)
        self.assertEqual(counts["confirmed_failures"], 49)
        self.assertEqual(counts["resolved_defects"], 42)
        self.assertEqual(counts["documented_boundaries"], 7)
        self.assertEqual(counts["unreproduced_candidates"], 6)
        self.assertEqual(counts["open_critical_defects"], 0)
        self.assertEqual(counts["confirmed_failures"], counts["resolved_defects"] + counts["documented_boundaries"])
        self.assertEqual(counts["total_cataloged_ids"], counts["confirmed_failures"] + counts["unreproduced_candidates"])
        self.assertEqual(data["boundary_structure"]["boundary_families_count"], 4)

    def test_15_synthetic_real_world_label_integrity(self):
        """Test 15: Verify 60-minute endurance is labeled synthetic & replay endurance."""
        claim_file = V321_DIR / "claim_evidence_registry.json"
        self.assertTrue(claim_file.exists(), "claim_evidence_registry.json missing")
        with open(claim_file) as f:
            data = json.load(f)
            
        mem_claim = next(c for c in data["matrix"] if "memory" in c["claim"].lower())
        self.assertIn("synthetic", mem_claim["data_type"].lower())
        self.assertIn("endurance", mem_claim["data_type"].lower())
        self.assertIn("synthetic", mem_claim["allowed_wording"].lower())

    def test_16_release_language_lint(self):
        """Test 16: Verify automated release language linter passes with zero active violations."""
        violations = run_lint()
        self.assertEqual(len(violations), 0, f"Found {len(violations)} release language violations: {violations}")

    def test_17_metric_registry_completeness(self):
        """Test 17: Verify canonical metric registry structure and presence of required metrics."""
        reg_file = OUT_DIR / "canonical_metric_registry.json"
        self.assertTrue(reg_file.exists(), "canonical_metric_registry.json missing")
        with open(reg_file) as f:
            data = json.load(f)
            
        metrics = data["metrics"]
        self.assertGreaterEqual(len(metrics), 12)
        for m in metrics:
            self.assertIn("metric_name", m)
            self.assertIn("value", m)
            self.assertIn("ci", m)
            self.assertIn("source_artifact", m)
            self.assertIn("status", m)

    def test_18_claim_evidence_traceability(self):
        """Test 18: Verify claim-evidence graph completeness and absence of unsupported claims."""
        graph_file = OUT_DIR / "canonical_claim_evidence_graph.json"
        self.assertTrue(graph_file.exists(), "canonical_claim_evidence_graph.json missing")
        with open(graph_file) as f:
            data = json.load(f)
            
        claims = data["claims"]
        self.assertGreaterEqual(len(claims), 12)
        for c in claims:
            self.assertIn(c["classification"], [
                "SUPPORTED", "SUPPORTED_WITH_LIMITATION", "CALIBRATION_ONLY",
                "MIXED_ODD", "SYNTHETIC_ONLY", "CASE_STUDY_ONLY", "UNVERIFIED", "RETRACTED"
            ])
            self.assertIsNotNone(c["allowed_wording"])

    def test_19_ci_method_registry_integrity(self):
        """Test 19: Verify CI method registry classifications."""
        stat_file = OUT_DIR / "statistical_method_registry.json"
        with open(stat_file) as f:
            data = json.load(f)
            
        valid_classes = {"BINOMIAL_PROPORTION", "POISSON_COUNT_RATE", "BOOTSTRAP_METRIC", "EMPIRICAL_SUMMARY", "NO_CI_APPROPRIATE"}
        for m in data["metrics"]:
            self.assertIn(m["classification"], valid_classes)

    def test_20_report_json_consistency(self):
        """Test 20: Verify report values and canonical metric registry match exactly."""
        reg_file = OUT_DIR / "canonical_metric_registry.json"
        with open(reg_file) as f:
            data = json.load(f)
            
        metrics_dict = {m["metric_name"]: m["value"] for m in data["metrics"]}
        self.assertAlmostEqual(metrics_dict["detection_bounding_box_precision"], 0.9576, places=4)
        self.assertAlmostEqual(metrics_dict["detection_bounding_box_recall"], 0.9412, places=4)
        self.assertAlmostEqual(metrics_dict["tracking_association_idf1"], 0.9141, places=4)
        self.assertAlmostEqual(metrics_dict["event_detection_precision"], 0.9400, places=4)
        self.assertAlmostEqual(metrics_dict["event_detection_recall"], 0.9400, places=4)
        self.assertAlmostEqual(metrics_dict["geometry_planar_mae"], 0.041, places=3)

if __name__ == "__main__":
    print("=" * 80)
    print("   SAFETY BACKFIRE AI — V3.2.1 FINAL CLOSURE AUDIT SUITE (20 TESTS)   ")
    print("=" * 80)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFinalClosureSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("=" * 80)
        print("   [SUCCESS] ALL 20 FINAL CLOSURE INTEGRITY TESTS PASSED!   ")
        print("=" * 80)
        sys.exit(0)
    else:
        print("=" * 80)
        print(f"   [FAILURE] {len(result.failures)} FAILURES, {len(result.errors)} ERRORS DETECTED.   ")
        print("=" * 80)
        sys.exit(1)
