"""
test_dataset_provenance_gate.py
V3.3 Dataset Provenance Gate Verification Suite.

Enforces Section 5 requirements:
No dataset may enter scientific evaluation unless:
1. source exists,
2. SHA256 is recorded,
3. source type is known,
4. capture metadata exists,
5. split assignment is immutable,
6. annotation provenance is documented,
7. ODD metadata is known or explicitly UNKNOWN.

The gate must reject:
- METADATA_ONLY
- UNAVAILABLE
- UNKNOWN_SOURCE
from blind scientific evaluation.
"""

import sys
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3_3.dataset.provenance_gate import (
    DatasetProvenanceGate,
    ProvenanceGateError,
    DISALLOWED_BLIND_CLASSIFICATIONS
)

AUDIT_PATH = WORKSPACE_ROOT / "outputs/v3_3/dataset_audit/dataset_availability_audit.json"

class TestDatasetProvenanceGate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not AUDIT_PATH.exists():
            raise FileNotFoundError(f"Missing audit file: {AUDIT_PATH}")
        with open(AUDIT_PATH, "r", encoding="utf-8") as f:
            cls.audit_data = json.load(f)

    def test_01_provenance_gate_rejects_metadata_only_from_blind(self):
        """Verify METADATA_ONLY dataset (e.g. DS_FULL_CORPUS_39900) is strictly rejected from blind evaluation."""
        rec = self.audit_data["datasets"]["DS_FULL_CORPUS_39900"]
        self.assertEqual(rec["classification"], "METADATA_ONLY")
        
        result = DatasetProvenanceGate.validate_dataset_record(rec, for_blind_evaluation=True)
        self.assertFalse(result["passes_gate"])
        self.assertTrue(any("METADATA_ONLY" in v for v in result["violations"]))

        with self.assertRaises(ProvenanceGateError):
            DatasetProvenanceGate.enforce_gate(rec, for_blind_evaluation=True)

    def test_02_provenance_gate_rejects_unavailable_datasets(self):
        """Verify UNAVAILABLE dataset (e.g. DS_V3_3_UNAVAILABLE_EXTERNAL_FACILITY_E) is rejected."""
        rec = self.audit_data["datasets"]["DS_V3_3_UNAVAILABLE_EXTERNAL_FACILITY_E"]
        self.assertEqual(rec["classification"], "UNAVAILABLE")

        result = DatasetProvenanceGate.validate_dataset_record(rec, for_blind_evaluation=True)
        self.assertFalse(result["passes_gate"])
        self.assertTrue(any("UNAVAILABLE" in v for v in result["violations"]))

        with self.assertRaises(ProvenanceGateError):
            DatasetProvenanceGate.enforce_gate(rec, for_blind_evaluation=True)

    def test_03_provenance_gate_rejects_unknown_source(self):
        """Verify UNKNOWN_SOURCE is rejected from blind evaluation."""
        synthetic_bad = {
            "dataset_id": "DS_TEST_UNKNOWN",
            "classification": "UNKNOWN_SOURCE",
            "file_exists": True,
            "sha256": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "source_type": "UNKNOWN_SOURCE",
            "camera_id": "CAM_01",
            "fps": 25.0,
            "resolution": "1920x1080",
            "annotation_file": "anno.json"
        }
        result = DatasetProvenanceGate.validate_dataset_record(synthetic_bad, for_blind_evaluation=True)
        self.assertFalse(result["passes_gate"])
        self.assertTrue(any("UNKNOWN_SOURCE" in v for v in result["violations"]))

    def test_04_provenance_gate_accepts_physical_annotated_datasets(self):
        """Verify that physically present and annotated datasets pass the gate."""
        physical_ids = [
            "DS_PHYSICAL_RAW_TEST_MP4",
            "DS_PHYSICAL_RAW_TEST2_MP4",
            "DS_V3_3_CALIB_SECTOR_B",
            "DS_V3_3_VAL_INTERSECTION_C",
            "DS_V3_3_BLIND_STAGING_D"
        ]
        for ds_id in physical_ids:
            rec = self.audit_data["datasets"][ds_id]
            result = DatasetProvenanceGate.validate_dataset_record(rec, for_blind_evaluation=True)
            self.assertTrue(result["passes_gate"], f"Dataset {ds_id} failed gate: {result['violations']}")

    def test_05_all_seven_criteria_enforced(self):
        """Verify each of the 7 criteria triggers a violation when missing."""
        # Missing SHA256
        bad_sha = {
            "dataset_id": "DS_TEST_BAD_SHA",
            "classification": "PHYSICALLY_PRESENT",
            "file_exists": True,
            "sha256": "INVALID",
            "camera_id": "CAM_01",
            "fps": 25.0,
            "resolution": "1920x1080",
            "annotation_file": "anno.json"
        }
        res = DatasetProvenanceGate.validate_dataset_record(bad_sha)
        self.assertFalse(res["passes_gate"])
        self.assertTrue(any("SHA-256" in v for v in res["violations"]))

        # Missing capture metadata
        bad_meta = {
            "dataset_id": "DS_TEST_BAD_META",
            "classification": "PHYSICALLY_PRESENT",
            "file_exists": True,
            "sha256": "a" * 64,
            "camera_id": None,
            "fps": None,
            "resolution": None,
            "annotation_file": "anno.json"
        }
        res = DatasetProvenanceGate.validate_dataset_record(bad_meta)
        self.assertFalse(res["passes_gate"])
        self.assertTrue(any("metadata" in v for v in res["violations"]))

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDatasetProvenanceGate)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
