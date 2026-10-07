"""
test_dataset_split_integrity.py
V3.3 Dataset Split Integrity and Provenance Test Suite.
Verifies that all registered streams have valid metadata schemas and that zero
data or hash leakage exists between calibration and evaluation/blind splits.
"""

import sys
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3_3.dataset import DatasetRegistry, VALID_SPLITS, VALID_ODD_TIERS

STREAM_REG_PATH = WORKSPACE_ROOT / "outputs/v3_3/stream_registry.json"

class TestDatasetSplitIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not STREAM_REG_PATH.exists():
            raise FileNotFoundError(f"Missing stream registry: {STREAM_REG_PATH}")
        cls.registry = DatasetRegistry.load_registry(STREAM_REG_PATH)

    def test_01_stream_schema_completeness(self):
        """Verify each registered stream possesses complete immutable metadata."""
        streams = self.registry.streams
        self.assertGreaterEqual(len(streams), 5, "Expected at least 5 registered streams in V3.3")

        required_attributes = [
            "dataset_id", "source_type", "camera_id", "camera_height_m",
            "camera_pitch_deg", "floor_slope_deg", "illumination_lux",
            "fps", "resolution", "warehouse_sector", "layout_id",
            "capture_date", "split", "odd_tier", "source_sha256", "annotation_status"
        ]

        for s_id, s in streams.items():
            for attr in required_attributes:
                val = getattr(s, attr, None)
                self.assertIsNotNone(val, f"Stream {s_id} missing required field {attr}")
            self.assertIn(s.split, VALID_SPLITS, f"Stream {s_id} has invalid split {s.split}")
            self.assertIn(s.odd_tier, VALID_ODD_TIERS, f"Stream {s_id} has invalid odd_tier {s.odd_tier}")
            self.assertEqual(len(s.source_sha256), 64, f"Stream {s_id} sha256 hash must be 64 characters")

    def test_02_zero_leakage_between_calibration_and_evaluation(self):
        """Verify zero stream ID or SHA-256 hash overlap between calibration and validation/blind splits."""
        leakage = self.registry.check_leakage()
        self.assertFalse(leakage["leakage_detected"], f"Data leakage detected: {leakage}")
        self.assertEqual(len(leakage["conflicting_dataset_ids"]), 0)
        self.assertEqual(len(leakage["conflicting_sha256_hashes"]), 0)

    def test_03_blind_quarantine_enforcement(self):
        """Verify that accessing V3.3_BLIND split raises PermissionError when blind lock is active."""
        self.assertTrue(self.registry.blind_locked)
        with self.assertRaises(PermissionError):
            self.registry.get_split("V3.3_BLIND", allow_blind_access=False)

        # Allowed explicitly when lock overridden for final unblinding
        blind_streams = self.registry.get_split("V3.3_BLIND", allow_blind_access=True)
        self.assertGreater(len(blind_streams), 0)

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDatasetSplitIntegrity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
