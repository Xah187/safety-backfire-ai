"""
test_final_freeze_semantics.py
Final Semantic Freeze Regression Suite for Safety Backfire AI V3.2.1.
Enforces all 9 required semantic closure tests:
  test_01_catalog_55_entry_semantics
  test_02_confirmed_failure_count_integrity
  test_03_candidate_hypothesis_count_integrity
  test_04_reproducibility_scope_integrity
  test_05_frozen_v3_2_artifact_provenance
  test_06_no_ambiguous_reproducibility_claim
  test_07_no_ambiguous_55_failure_claim
  test_08_canonical_registry_provenance_integrity
  test_09_final_report_semantic_consistency
"""

import sys
import re
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

OUT_DIR = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure"
REPORTS_DIR = WORKSPACE_ROOT / "reports/v3_2_1"

class TestFinalFreezeSemantics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        reg_path = OUT_DIR / "canonical_release_registry.json"
        if not reg_path.exists():
            raise FileNotFoundError(f"Missing canonical registry: {reg_path}")
        with open(reg_path, "r", encoding="utf-8") as f:
            cls.registry = json.load(f)

        sum_path = OUT_DIR / "failure_catalog_summary.json"
        if not sum_path.exists():
            raise FileNotFoundError(f"Missing catalog summary: {sum_path}")
        with open(sum_path, "r", encoding="utf-8") as f:
            cls.catalog_summary = json.load(f)

        repro_path = OUT_DIR / "reproducibility_scope.json"
        if not repro_path.exists():
            raise FileNotFoundError(f"Missing reproducibility scope: {repro_path}")
        with open(repro_path, "r", encoding="utf-8") as f:
            cls.repro_scope = json.load(f)

        prov_path = OUT_DIR / "evidence_provenance_policy.json"
        if not prov_path.exists():
            raise FileNotFoundError(f"Missing provenance policy: {prov_path}")
        with open(prov_path, "r", encoding="utf-8") as f:
            cls.provenance_policy = json.load(f)

    def test_01_catalog_55_entry_semantics(self):
        """Test 01: Verify master catalog has exactly 55 entries with 49 confirmed + 6 candidate hypotheses."""
        cs = self.catalog_summary
        self.assertEqual(cs["master_catalog_entries"], 55)
        self.assertEqual(cs["confirmed_failure_modes"], 49)
        self.assertEqual(cs["resolved_failure_modes"], 42)
        self.assertEqual(cs["documented_boundary_ids"], 7)
        self.assertEqual(cs["documented_boundary_families"], 4)
        self.assertEqual(cs["unreproduced_candidate_hypotheses"], 6)
        self.assertEqual(cs["open_critical_defects"], 0)

        # Mathematical identity: 49 + 6 = 55, 42 + 7 = 49
        self.assertEqual(cs["confirmed_failure_modes"] + cs["unreproduced_candidate_hypotheses"], cs["master_catalog_entries"])
        self.assertEqual(cs["resolved_failure_modes"] + cs["documented_boundary_ids"], cs["confirmed_failure_modes"])

        # Also check canonical registry
        reg_cat = self.registry["catalog_semantics"]
        self.assertEqual(reg_cat["master_catalog_entries"], 55)
        self.assertEqual(reg_cat["confirmed_failure_modes"], 49)
        self.assertEqual(reg_cat["unreproduced_candidate_hypotheses"], 6)
        self.assertEqual(reg_cat["resolved_confirmed_failures"], 42)
        self.assertEqual(reg_cat["documented_boundary_ids"], 7)
        self.assertEqual(reg_cat["documented_boundary_families"], 4)
        self.assertEqual(reg_cat["open_critical_defects"], 0)

    def test_02_confirmed_failure_count_integrity(self):
        """Test 02: Verify confirmed failures count is exactly 49 (42 resolved + 7 documented ODD boundaries)."""
        fail_reg = self.registry["failure_registry"]
        self.assertEqual(fail_reg["confirmed_failures"], 49)
        self.assertEqual(fail_reg["resolved_defects"], 42)
        self.assertEqual(fail_reg["documented_boundaries"], 7)
        self.assertEqual(fail_reg["boundary_families"], 4)
        self.assertEqual(len(fail_reg["boundary_ids"]), 7)

        expected_boundary_ids = {"FAIL-13", "FAIL-26", "FAIL-27", "FAIL-30", "FAIL-38", "FAIL-44", "FAIL-45"}
        self.assertEqual(set(fail_reg["boundary_ids"]), expected_boundary_ids)

    def test_03_candidate_hypothesis_count_integrity(self):
        """Test 03: Verify candidate hypotheses count is exactly 6 and none are labeled confirmed failures."""
        fail_reg = self.registry["failure_registry"]
        self.assertEqual(fail_reg["unreproduced_candidates"], 6)
        self.assertEqual(self.catalog_summary["unreproduced_candidate_hypotheses"], 6)

        # Check unreproduced candidates are distinct from confirmed failures
        total = self.catalog_summary["master_catalog_entries"]
        confirmed = self.catalog_summary["confirmed_failure_modes"]
        candidates = self.catalog_summary["unreproduced_candidate_hypotheses"]
        self.assertEqual(confirmed + candidates, total)
        self.assertNotEqual(total, confirmed)

    def test_04_reproducibility_scope_integrity(self):
        """Test 04: Verify layered reproducibility structure: core_code=PASS, artifacts=PASS, raw=PARTIAL, overall=PARTIAL_WITH_REPRODUCIBLE_CODE_AND_ARTIFACTS."""
        repro = self.repro_scope
        self.assertEqual(repro["core_code"]["status"], "PASS")
        self.assertEqual(repro["canonical_artifacts"]["status"], "PASS")
        self.assertEqual(repro["full_annotated_corpus_raw_footage"]["status"], "PARTIAL")
        self.assertEqual(repro["overall_release_reproducibility"]["status"], "PARTIAL_WITH_REPRODUCIBLE_CODE_AND_ARTIFACTS")

        # Canonical statement check
        stmt = repro["overall_release_reproducibility"]["canonical_statement"]
        self.assertIn("The V3.2.1 codebase and canonical derived artifacts are reproducible from the repository", stmt)
        self.assertIn("1,672 physical raw frames", stmt)

        # Registry section check
        reg_repro = self.registry["reproducibility_scope"]
        self.assertEqual(reg_repro["core_code"], "PASS")
        self.assertEqual(reg_repro["canonical_artifacts"], "PASS")
        self.assertEqual(reg_repro["full_raw_corpus"], "PARTIAL")
        self.assertEqual(reg_repro["overall"], "PARTIAL_WITH_REPRODUCIBLE_CODE_AND_ARTIFACTS")

    def test_05_frozen_v3_2_artifact_provenance(self):
        """Test 05: Verify V3.2 evidence artifacts are frozen source inputs and metrics carry source_artifact_class."""
        prov = self.provenance_policy
        self.assertEqual(prov["historical_source_release"], "V3.2")
        self.assertEqual(prov["canonical_audit_release"], "V3.2.1")
        self.assertTrue(prov["historical_artifacts_are_frozen"])
        self.assertTrue(prov["canonical_metrics_derive_from_frozen_evidence"])

        # Check all metrics in registry
        for m in self.registry["metrics"]:
            src = m.get("source_artifact", "")
            if src.startswith("outputs/v3_2/"):
                self.assertEqual(m.get("source_artifact_class"), "V3_2_FROZEN_EVIDENCE", f"Metric {m['metric_id']} missing V3_2_FROZEN_EVIDENCE class")
                self.assertEqual(m.get("canonical_release"), "V3.2.1", f"Metric {m['metric_id']} missing canonical_release V3.2.1")

    def test_06_no_ambiguous_reproducibility_claim(self):
        """Test 06: Audit active reports for unqualified 'REPRODUCIBILITY: PASS' or claims of 'entire experiment fully reproducible'."""
        ambiguous_patterns = [
            re.compile(r"^\s*REPRODUCIBILITY:\s*PASS\s*$", re.MULTILINE),
            re.compile(r"\bentire\s+experiment\s+fully\s+reproducible\b", re.IGNORECASE)
        ]

        for md_file in REPORTS_DIR.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            # Filter out retracted/historical sections
            active_lines = [l for l in content.splitlines() if "RETRACTED" not in l and "retracted" not in l and "Retracted" not in l]
            active_text = "\n".join(active_lines)

            for pat in ambiguous_patterns:
                self.assertFalse(
                    pat.search(active_text),
                    f"Ambiguous reproducibility claim matching '{pat.pattern}' found in {md_file.name}!"
                )

    def test_07_no_ambiguous_55_failure_claim(self):
        """Test 07: Audit active reports: never call all 55 entries '55 failure modes', '55 confirmed failures', or '55 physical defects'."""
        ambiguous_terms = [
            re.compile(r"\bCatalog Failure Modes:\s*55\b", re.IGNORECASE),
            re.compile(r"\b55\s+failure\s+modes\b", re.IGNORECASE),
            re.compile(r"\b55\s+confirmed\s+failures\b", re.IGNORECASE),
            re.compile(r"\b55\s+physical\s+defects\b", re.IGNORECASE)
        ]

        for md_file in REPORTS_DIR.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            active_lines = [l for l in content.splitlines() if "RETRACTED" not in l and "retracted" not in l and "Retracted" not in l]
            active_text = "\n".join(active_lines)

            for term in ambiguous_terms:
                self.assertFalse(
                    term.search(active_text),
                    f"Ambiguous 55 failure term matching '{term.pattern}' found in active text of {md_file.name}!"
                )

    def test_08_canonical_registry_provenance_integrity(self):
        """Test 08: Verify canonical release registry provenance, catalog semantics, and reproducibility fields."""
        reg = self.registry
        self.assertIn("catalog_semantics", reg)
        self.assertIn("reproducibility_scope", reg)
        self.assertIn("evidence_provenance", reg)
        self.assertEqual(reg["evidence_provenance"]["historical_source_release"], "V3.2")
        self.assertEqual(reg["evidence_provenance"]["audit_release"], "V3.2.1")
        self.assertTrue(reg["evidence_provenance"]["historical_artifacts_frozen"])

    def test_09_final_report_semantic_consistency(self):
        """Test 09: Verify key reports contain exact master catalog tree, layered reproducibility statement, and provenance declaration."""
        required_reports = [
            "V3.2.1_CORE_STATUS.md",
            "V3.2.1_FINAL_RELEASE_AUDIT.md",
            "V3.2.1_FAILURE_REGISTRY_AUDIT.md",
            "V3.2.1_CLAIM_EVIDENCE_TRACEABILITY.md",
            "V3.2.1_REPRODUCIBILITY_AUDIT.md",
            "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"
        ]

        expected_quote = "The V3.2.1 codebase and canonical derived artifacts are reproducible from the repository. Full raw-footage reproduction of the 39,900-frame annotated corpus is not currently possible because only 1,672 physical raw frames are present locally."

        for r_name in required_reports:
            r_path = REPORTS_DIR / r_name
            self.assertTrue(r_path.exists(), f"Missing required report: {r_name}")
            content = r_path.read_text(encoding="utf-8")
            self.assertGreater(len(content), 100, f"Report {r_name} is unexpectedly short")

            # Check specific expectations
            if r_name in ["V3.2.1_CORE_STATUS.md", "V3.2.1_FAILURE_REGISTRY_AUDIT.md", "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"]:
                self.assertIn("MASTER CATALOG ENTRIES: 55", content, f"Missing exact catalog header in {r_name}")
                self.assertIn("CONFIRMED FAILURE MODES: 49", content, f"Missing confirmed failures in tree in {r_name}")
                self.assertIn("UNREPRODUCED CANDIDATE HYPOTHESES: 6", content, f"Missing candidate hypotheses in tree in {r_name}")

            if r_name in ["V3.2.1_CORE_STATUS.md", "V3.2.1_REPRODUCIBILITY_AUDIT.md", "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"]:
                self.assertIn("CORE_CODE_REPRODUCIBILITY: PASS", content, f"Missing layered reproducibility in {r_name}")
                self.assertIn("CANONICAL_ARTIFACT_REPRODUCIBILITY: PASS", content, f"Missing layered reproducibility in {r_name}")
                self.assertIn("FULL_CORPUS_RAW_DATA_REPRODUCIBILITY: PARTIAL", content, f"Missing layered reproducibility in {r_name}")
                self.assertIn("OVERALL_RELEASE_REPRODUCIBILITY: PARTIAL_WITH_REPRODUCIBLE_CODE_AND_ARTIFACTS", content, f"Missing layered reproducibility in {r_name}")
                self.assertIn(expected_quote, content, f"Missing canonical quotation in {r_name}")

            if r_name in ["V3.2.1_FINAL_RELEASE_AUDIT.md", "V3.2.1_CORE_STATUS.md", "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"]:
                self.assertIn("V3.2 HISTORICAL EVIDENCE ARTIFACT", content, f"Missing provenance declaration in {r_name}")
                self.assertIn("FROZEN SOURCE EVIDENCE INPUT", content, f"Missing provenance declaration in {r_name}")
                self.assertIn("AUDITED / RECONCILED RELEASE DERIVED FROM FROZEN EVIDENCE", content, f"Missing provenance declaration in {r_name}")

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFinalFreezeSemantics)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
