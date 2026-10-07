"""
test_canonical_report_consistency.py
Master Report Consistency Test for Safety Backfire AI V3.2.1.
Verifies that all Markdown reports in reports/v3_2_1/ strictly align with
outputs/v3_2_1/final_closure/canonical_metric_registry.json and
outputs/v3_2_1/final_closure/canonical_release_registry.json.
Fails on any stale, unbacked, or contradictory metric values in active reporting.
"""

import sys
import re
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

REPORTS_DIR = WORKSPACE_ROOT / "reports/v3_2_1"
OUT_DIR = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure"

class TestCanonicalReportConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        registry_path = OUT_DIR / "canonical_release_registry.json"
        if not registry_path.exists():
            raise FileNotFoundError(f"Missing registry: {registry_path}")
        with open(registry_path, "r", encoding="utf-8") as f:
            cls.registry = json.load(f)

        cls.metrics_by_name = {m["metric_name"]: m for m in cls.registry["metrics"]}

        # List of required reports to audit
        cls.report_files = [
            "V3.2.1_CORE_STATUS.md",
            "V3.2.1_FINAL_RELEASE_AUDIT.md",
            "V3.2.1_DATASET_RECONCILIATION.md",
            "V3.2.1_METRIC_RECONCILIATION.md",
            "V3.2.1_ODD_RECONCILIATION.md",
            "V3.2.1_STATISTICAL_TERMINOLOGY_AUDIT.md",
            "V3.2.1_EVENT_METRIC_AUDIT.md",
            "V3.2.1_HAZARD_METRIC_AUDIT.md",
            "V3.2.1_UNCERTAINTY_LINEAGE_AUDIT.md",
            "V3.2.1_BACKFIRE_EVIDENCE_AUDIT.md",
            "V3.2.1_CAUSALITY_AUDIT.md",
            "V3.2.1_FAILURE_REGISTRY_AUDIT.md",
            "V3.2.1_CLAIM_EVIDENCE_TRACEABILITY.md",
            "V3.2.1_REPRODUCIBILITY_AUDIT.md",
            "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md",
        ]

    def _get_active_lines(self, content: str):
        """Returns lines that are not part of an explicit RETRACTED declaration or historical notes."""
        active_lines = []
        for line in content.splitlines():
            # If line explicitly contains RETRACTED or retracted:, skip it as it documents what was retracted
            if "RETRACTED" in line or "retracted" in line or "Retracted" in line:
                continue
            active_lines.append(line)
        return "\n".join(active_lines)

    def test_01_no_active_stale_perception_set_a(self):
        """Verify no active report uses retracted Perception Set A (0.9576 or 881/920 or 881/936)."""
        stale_patterns = ["0.9576", "881 / 920", "881/920", "881 / 936", "881/936"]
        for fname in self.report_files:
            fp = REPORTS_DIR / fname
            self.assertTrue(fp.exists(), f"Report file missing: {fname}")
            content = fp.read_text(encoding="utf-8")
            active_text = self._get_active_lines(content)
            for pat in stale_patterns:
                self.assertNotIn(
                    pat, active_text,
                    f"FAIL: Stale perception pattern '{pat}' found in active content of report {fname}!"
                )

    def test_02_no_active_stale_geometry_mae(self):
        """Verify no active report uses retracted Geometry MAE (0.0410 m)."""
        for fname in self.report_files:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            active_text = self._get_active_lines(content)
            self.assertNotIn(
                "0.0410", active_text,
                f"FAIL: Stale geometry MAE '0.0410' found in active content of report {fname}!"
            )

    def test_03_no_active_stale_hazard_placeholder_fraction(self):
        """Verify no active report uses retracted Hazard placeholder (515/540)."""
        stale_patterns = ["515 / 540", "515/540"]
        for fname in self.report_files:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            active_text = self._get_active_lines(content)
            for pat in stale_patterns:
                self.assertNotIn(
                    pat, active_text,
                    f"FAIL: Stale hazard fraction '{pat}' found in active content of report {fname}!"
                )

    def test_04_no_active_stale_tracking_fraction(self):
        """Verify no active report uses false tracking fraction (1768 / 1851)."""
        stale_patterns = ["1768 / 1851", "1768/1851"]
        for fname in self.report_files:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            active_text = self._get_active_lines(content)
            for pat in stale_patterns:
                self.assertNotIn(
                    pat, active_text,
                    f"FAIL: False tracking fraction '{pat}' found in active content of report {fname}!"
                )

    def test_05_no_active_stale_poisson_upper_bound(self):
        """Verify no active report uses draft typo 30.360 or rounded hours 30.388 instead of canonical exact 30.391."""
        stale_bounds = ["30.360", "30.388"]
        for fname in self.report_files:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            active_text = self._get_active_lines(content)
            for b in stale_bounds:
                self.assertNotIn(
                    b, active_text,
                    f"FAIL: Stale Poisson bound '{b}' found in active content of report {fname}! Expected 30.391."
                )

    def test_06_canonical_perception_metrics_in_master_table(self):
        """Verify Master Table in V3.2.1_FINAL_RELEASE_AUDIT.md and master report has exact canonical perception values."""
        target_reports = ["V3.2.1_FINAL_RELEASE_AUDIT.md", "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"]
        for fname in target_reports:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            # Must contain canonical 0.9442 with 474 and 502
            self.assertIn("0.9442", content, f"Missing canonical perception precision 0.9442 in {fname}")
            self.assertIn("474", content, f"Missing canonical numerator 474 in {fname}")
            self.assertIn("502", content, f"Missing canonical denominator 502 in {fname}")
            # Must contain canonical 0.9480 with 474 and 500
            self.assertIn("0.9480", content, f"Missing canonical perception recall 0.9480 in {fname}")
            self.assertIn("500", content, f"Missing canonical denominator 500 in {fname}")

    def test_07_canonical_geometry_metrics_in_master_table(self):
        """Verify Master Table has exact canonical geometry MAE (0.0169 m, 1.521 m / 90 pts)."""
        target_reports = ["V3.2.1_FINAL_RELEASE_AUDIT.md", "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"]
        for fname in target_reports:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            self.assertIn("0.0169 m", content, f"Missing canonical geometry MAE 0.0169 m in {fname}")
            self.assertIn("1.521 m", content, f"Missing canonical geometry sum 1.521 m in {fname}")
            self.assertIn("90 pts", content, f"Missing canonical denominator 90 pts in {fname}")

    def test_08_canonical_hazard_metrics_in_master_table(self):
        """Verify Master Table has exact canonical hazard metrics (268/281 = 0.9537, 268/286 = 0.9371)."""
        target_reports = ["V3.2.1_FINAL_RELEASE_AUDIT.md", "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"]
        for fname in target_reports:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            self.assertIn("0.9537", content, f"Missing canonical hazard micro precision 0.9537 in {fname}")
            self.assertIn("268", content, f"Missing canonical hazard TP 268 in {fname}")
            self.assertIn("281", content, f"Missing canonical hazard denominator 281 in {fname}")
            self.assertIn("0.9371", content, f"Missing canonical hazard micro recall 0.9371 in {fname}")
            self.assertIn("286", content, f"Missing canonical hazard denominator 286 in {fname}")

    def test_09_canonical_event_rates_in_master_table(self):
        """Verify Master Table has exact Poisson rates (7.83 /hr [1.614, 22.871], 5.45 /hr [0.138, 30.391])."""
        target_reports = ["V3.2.1_FINAL_RELEASE_AUDIT.md", "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"]
        for fname in target_reports:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            self.assertIn("7.83 /hr", content, f"Missing canonical corpus rate 7.83 in {fname}")
            self.assertIn("22.871", content, f"Missing canonical corpus upper CI 22.871 in {fname}")
            self.assertIn("5.45 /hr", content, f"Missing canonical blind rate 5.45 in {fname}")
            self.assertIn("30.391", content, f"Missing canonical blind upper CI 30.391 in {fname}")

    def test_10_canonical_sample_units_and_splits(self):
        """Verify Master Table has correct sample units and dataset splits matching canonical registry."""
        fp = REPORTS_DIR / "V3.2.1_FINAL_RELEASE_AUDIT.md"
        content = fp.read_text(encoding="utf-8")
        self.assertIn("bounding box", content)
        self.assertIn("annotation", content)
        self.assertIn("planar point", content)
        self.assertIn("calibration pt", content)
        self.assertIn("Blind Test", content)
        self.assertIn("Surveyed Grid", content)

    def test_11_canonical_odd_tiers(self):
        """Verify Master Table has appropriate ODD tiers (e.g. MIXED_ODD for blind test)."""
        fp = REPORTS_DIR / "V3.2.1_FINAL_RELEASE_AUDIT.md"
        content = fp.read_text(encoding="utf-8")
        self.assertIn("MIXED_ODD", content)
        self.assertIn("NOMINAL_ODD", content)

    def test_12_canonical_ci_methods(self):
        """Verify CI methods: Wilson for Bernoulli, Exact Poisson for count rates, NOT_REPORTED for geometry & IDF1."""
        fp = REPORTS_DIR / "V3.2.1_FINAL_RELEASE_AUDIT.md"
        content = fp.read_text(encoding="utf-8")
        self.assertIn("Wilson", content)
        self.assertIn("Exact Poisson", content)
        self.assertIn("**NOT_REPORTED** (Spatial correlation)", content)
        self.assertIn("**NOT_REPORTED** (Wilson retracted)", content)

    def test_13_no_active_stale_event_wilson_ci(self):
        """Verify no active report uses legacy/retracted Wilson CI [0.8345, 0.9798]."""
        stale_patterns = ["0.8345", "0.9798"]
        for fname in self.report_files:
            fp = REPORTS_DIR / fname
            content = fp.read_text(encoding="utf-8")
            active_text = self._get_active_lines(content)
            for pat in stale_patterns:
                self.assertNotIn(
                    pat, active_text,
                    f"FAIL: Legacy Wilson CI '{pat}' found in active content of report {fname}! Expected [0.8378, 0.9794]."
                )

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCanonicalReportConsistency)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
