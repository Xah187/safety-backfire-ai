"""
test_odd_enforcement.py
V3.3 Operational Design Domain (ODD) Boundary & Safe Refusal Test Suite.
Verifies that out-of-ODD conditions, non-planar slopes, optical limits, and latency spikes
are strictly converted into safe refusal states rather than silent failure.
"""

import sys
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3_3.geometry import GroundGeometryClassifier, GeometryState
from safety_backfire_v3_3.refusal import SafeRefusalEngine, RefusalDecision

class TestODDEnforcement(unittest.TestCase):

    def setUp(self):
        self.geom_classifier = GroundGeometryClassifier()
        self.refusal_engine = SafeRefusalEngine()

    def test_01_nominal_conditions_permit_intervention(self):
        """Verify nominal floor, pitch (45 deg), distance (4.0m), and latency (20ms) permit intervention."""
        geom = self.geom_classifier.classify_surface(slope_deg=0.3, reprojection_residual_m=0.015, distance_m=4.0)
        self.assertEqual(geom["geometry_state"], GeometryState.PLANAR_VALID.value)

        decision = self.refusal_engine.evaluate_telemetry(
            geometry_state=geom["geometry_state"],
            camera_pitch_deg=45.0,
            distance_m=4.0,
            latency_ms=20.0,
            illumination_lux=400.0,
            odd_tier="NOMINAL_ODD"
        )
        self.assertEqual(decision["decision"], RefusalDecision.AUTONOMOUS_INTERVENTION_PERMITTED.value)
        self.assertFalse(decision["refusal_triggered"])

    def test_02_degraded_pitch_downgrades_to_advisory(self):
        """Verify shallow pitch (22.5 deg like CAM_DOCK_SOUTH) permits advisory warning only, not autonomous braking."""
        geom = self.geom_classifier.classify_surface(slope_deg=0.5, reprojection_residual_m=0.02, distance_m=5.0)

        decision = self.refusal_engine.evaluate_telemetry(
            geometry_state=geom["geometry_state"],
            camera_pitch_deg=22.5,
            distance_m=5.0,
            latency_ms=30.0,
            illumination_lux=300.0,
            odd_tier="DEGRADED_ODD"
        )
        self.assertEqual(decision["decision"], RefusalDecision.ADVISORY_WARNING_ONLY.value)
        self.assertFalse(decision["refusal_triggered"])

    def test_03_non_planar_slope_triggers_safe_refusal(self):
        """Verify ramp slope > 3.0 deg triggers NON_PLANAR_REFUSAL and safe refusal output."""
        geom = self.geom_classifier.classify_surface(slope_deg=3.5, reprojection_residual_m=0.08, distance_m=5.0)
        self.assertEqual(geom["geometry_state"], GeometryState.NON_PLANAR_REFUSAL.value)

        decision = self.refusal_engine.evaluate_telemetry(
            geometry_state=geom["geometry_state"],
            camera_pitch_deg=45.0,
            distance_m=5.0,
            latency_ms=25.0,
            illumination_lux=400.0
        )
        self.assertEqual(decision["decision"], RefusalDecision.SAFE_REFUSAL_INSUFFICIENT_EVIDENCE.value)
        self.assertTrue(decision["refusal_triggered"])
        self.assertTrue(any("non-planar" in r.lower() for r in decision["refusal_flags"]))

    def test_04_critical_latency_triggers_safe_refusal(self):
        """Verify latency spike > 500ms triggers safe refusal."""
        decision = self.refusal_engine.evaluate_telemetry(
            geometry_state="PLANAR_VALID",
            camera_pitch_deg=45.0,
            distance_m=4.0,
            latency_ms=650.0,
            illumination_lux=400.0
        )
        self.assertEqual(decision["decision"], RefusalDecision.SAFE_REFUSAL_INSUFFICIENT_EVIDENCE.value)
        self.assertTrue(decision["refusal_triggered"])
        self.assertTrue(any("latency" in r.lower() for r in decision["refusal_flags"]))

    def test_05_far_field_distance_boundary_refusal(self):
        """Verify distance > 10.0m triggers safe refusal."""
        decision = self.refusal_engine.evaluate_telemetry(
            geometry_state="PLANAR_VALID",
            camera_pitch_deg=45.0,
            distance_m=11.5,
            latency_ms=25.0,
            illumination_lux=400.0
        )
        self.assertEqual(decision["decision"], RefusalDecision.SAFE_REFUSAL_INSUFFICIENT_EVIDENCE.value)
        self.assertTrue(decision["refusal_triggered"])

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestODDEnforcement)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
