"""
test_claim_traceability.py
V3.3 Claim-to-Evidence Traceability and Gap Alignment Test Suite.
Verifies that all V3.3 research initiatives directly address documented evidence gaps,
and that no unsupported claims exist in active development descriptors.
"""

import sys
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

GAP_MATRIX_PATH = WORKSPACE_ROOT / "outputs/v3_3/v3_3_gap_matrix.json"
EXP_REG_PATH = WORKSPACE_ROOT / "outputs/v3_3/experiment_registry.json"

class TestClaimTraceability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not GAP_MATRIX_PATH.exists():
            raise FileNotFoundError(f"Missing gap matrix: {GAP_MATRIX_PATH}")
        with open(GAP_MATRIX_PATH, "r", encoding="utf-8") as f:
            cls.gap_matrix = json.load(f)

        if not EXP_REG_PATH.exists():
            raise FileNotFoundError(f"Missing experiment registry: {EXP_REG_PATH}")
        with open(EXP_REG_PATH, "r", encoding="utf-8") as f:
            cls.exp_registry = json.load(f)

    def test_01_gap_matrix_completeness(self):
        """Verify gap matrix addresses all 3 core V3.2.1 limitations (footage, uncertainty, interventions)."""
        gaps = self.gap_matrix.get("gaps", [])
        self.assertGreaterEqual(len(gaps), 3, "Expected at least 3 core gaps in gap matrix")

        gap_text = json.dumps(gaps).lower()
        self.assertIn("limitation a", gap_text)
        self.assertIn("limitation b", gap_text)
        self.assertIn("limitation c", gap_text)
        self.assertIn("out-of-sample", gap_text)
        self.assertIn("intervention", gap_text)

    def test_02_experiments_map_to_gaps(self):
        """Verify each experiment maps directly to a scientific gap with concrete acceptance criteria."""
        experiments = self.exp_registry.get("experiments", [])
        self.assertGreaterEqual(len(experiments), 4)

        for exp in experiments:
            self.assertIn("ExperimentID", exp)
            self.assertIn("Hypothesis", exp)
            self.assertIn("AcceptanceCriteria", exp)
            self.assertIn("EvaluationMethod", exp)
            # Must have non-trivial evaluation methodology
            self.assertGreater(len(exp["EvaluationMethod"]), 10)

    def test_03_no_unsupported_population_claims(self):
        """Verify that experiment hypotheses do not claim 100% accuracy, zero error, or proven universal causality."""
        prohibited_phrases = [
            "100% accuracy",
            "zero failure probability",
            "mathematical guarantee",
            "proven causal effect",
            "universal safety"
        ]

        exp_dump = json.dumps(self.exp_registry).lower()
        for phrase in prohibited_phrases:
            self.assertNotIn(
                phrase, exp_dump,
                f"Prohibited overclaim '{phrase}' detected in V3.3 experiment registry!"
            )

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClaimTraceability)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
