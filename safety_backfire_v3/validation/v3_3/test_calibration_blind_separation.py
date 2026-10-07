"""
test_calibration_blind_separation.py
V3.3 Calibration vs Blind Evaluation Separation Test Suite.
Verifies that uncertainty factor k is strictly locked before out-of-sample evaluation,
and that calibration coverage and out-of-sample coverage are never conflated.
"""

import sys
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3_3.uncertainty import UncertaintyPoint, UncertaintyEvaluator

class TestCalibrationBlindSeparation(unittest.TestCase):

    def setUp(self):
        self.evaluator = UncertaintyEvaluator()

        # Calibration points (simulate 20 points in Sector B)
        self.calib_points = [
            UncertaintyPoint(
                point_id=f"calib_{i}",
                dx=0.02 * ((-1) ** i),
                dy=0.015 * ((-1) ** (i // 2)),
                sigma_x=0.015,
                sigma_y=0.015,
                distance_m=3.5,
                illumination_lux=400.0,
                camera_pitch_deg=45.0,
                occlusion_state="NONE"
            ) for i in range(20)
        ]

        # Independent Out-of-sample points (simulate Sector C with varying conditions)
        self.oos_points = [
            UncertaintyPoint(
                point_id=f"oos_{i}",
                dx=0.03 * ((-1) ** i),
                dy=0.025 * ((-1) ** (i // 3)),
                sigma_x=0.018,
                sigma_y=0.018,
                distance_m=2.0 + (i * 0.4),  # Spans 2.0m to 9.6m
                illumination_lux=200.0 if i % 2 == 0 else 500.0,
                camera_pitch_deg=42.0,
                occlusion_state="PARTIAL" if i % 4 == 0 else "NONE"
            ) for i in range(20)
        ]

    def test_01_cannot_evaluate_before_lock(self):
        """Verify evaluating out-of-sample before locking k raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            self.evaluator.evaluate_out_of_sample(self.oos_points)

    def test_02_strict_k_locking(self):
        """Verify fit_and_lock_k permanently locks k and records calibration provenance."""
        locked_k = self.evaluator.fit_and_lock_k(self.calib_points, target_coverage=0.95)
        self.assertGreaterEqual(locked_k, 2.0)
        self.assertEqual(self.evaluator.locked_k, locked_k)

        rec = self.evaluator.calibration_record
        self.assertIn("locked_factor_k", rec)
        self.assertIn("in_sample_calibration_coverage", rec)
        self.assertEqual(rec["status"], "CALIBRATION_LOCKED_DO_NOT_ALTER")

    def test_03_out_of_sample_evaluation_integrity(self):
        """Verify out-of-sample evaluation does not alter locked k and separates coverage metrics."""
        locked_k = self.evaluator.fit_and_lock_k(self.calib_points, target_coverage=0.95)
        results = self.evaluator.evaluate_out_of_sample(self.oos_points)

        # Factor k must not change
        self.assertEqual(results["locked_factor_k"], locked_k)
        self.assertEqual(self.evaluator.locked_k, locked_k)

        # In-sample vs out-of-sample separation
        in_sample = self.evaluator.calibration_record["in_sample_calibration_coverage"]
        oos = results["out_of_sample_coverage"]
        self.assertIsInstance(in_sample, float)
        self.assertIsInstance(oos, float)

        # Verify condition-specific strata exist
        by_cond = results["coverage_by_condition"]
        self.assertIn("distance_strata", by_cond)
        self.assertIn("illumination_strata", by_cond)
        self.assertIn("occlusion_strata", by_cond)

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCalibrationBlindSeparation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
