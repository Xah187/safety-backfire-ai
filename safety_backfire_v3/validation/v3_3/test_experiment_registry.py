"""
test_experiment_registry.py
V3.3 Experiment Registry Schema and Pre-Registration Verification Suite.
Ensures that all experiments adhere to Section 20 specifications and have
frozen hypotheses and evaluation protocols before execution.
"""

import sys
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

REGISTRY_PATH = WORKSPACE_ROOT / "outputs/v3_3/experiment_registry.json"

REQUIRED_EXPERIMENT_FIELDS = [
    "ExperimentID",
    "Hypothesis",
    "Dataset",
    "Split",
    "IndependentVariables",
    "DependentVariables",
    "Control",
    "Treatment",
    "SampleSize",
    "RandomSeed",
    "EvaluationMethod",
    "AcceptanceCriteria",
    "Result",
    "Interpretation"
]

class TestExperimentRegistry(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not REGISTRY_PATH.exists():
            raise FileNotFoundError(f"Missing experiment registry: {REGISTRY_PATH}")
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            cls.registry = json.load(f)

    def test_01_registry_schema_completeness(self):
        """Verify each registered experiment contains all 14 required fields."""
        experiments = self.registry.get("experiments", [])
        self.assertGreaterEqual(len(experiments), 4, "Expected at least 4 registered experiments")

        seen_ids = set()
        for exp in experiments:
            for field in REQUIRED_EXPERIMENT_FIELDS:
                self.assertIn(field, exp, f"Experiment missing required field: {field}")
                self.assertIsNotNone(exp[field], f"Field {field} cannot be null in experiment {exp.get('ExperimentID')}")

            exp_id = exp["ExperimentID"]
            self.assertNotIn(exp_id, seen_ids, f"Duplicate ExperimentID: {exp_id}")
            seen_ids.add(exp_id)

    def test_02_hypothesis_and_criteria_rigor(self):
        """Verify hypotheses and acceptance criteria are substantive non-trivial strings."""
        for exp in self.registry["experiments"]:
            self.assertGreater(len(exp["Hypothesis"]), 20, f"Hypothesis too brief in {exp['ExperimentID']}")
            self.assertGreater(len(exp["AcceptanceCriteria"]), 20, f"AcceptanceCriteria too brief in {exp['ExperimentID']}")
            self.assertIsInstance(exp["SampleSize"], (int, float))
            self.assertIsInstance(exp["RandomSeed"], int)
            self.assertIn(exp["Result"], ["PENDING_EXECUTION", "PASS", "FAIL", "INCONCLUSIVE"])

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExperimentRegistry)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
