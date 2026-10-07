"""
test_v3_2_1_immutability.py
V3.3 Baseline Protection Test Suite for Safety Backfire AI.
Ensures that the frozen V3.2.1 baseline artifacts, source code, canonical registries,
and reports are never mutated, corrupted, or altered by V3.3 development.
"""

import sys
import hashlib
import json
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

BASELINE_DIR = WORKSPACE_ROOT / "outputs/v3_3/baseline"
MANIFEST_PATH = BASELINE_DIR / "v3_2_1_source_hash_manifest.json"
METRIC_SNAP_PATH = BASELINE_DIR / "v3_2_1_metric_snapshot.json"
FAIL_SNAP_PATH = BASELINE_DIR / "v3_2_1_failure_registry_snapshot.json"

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class TestV321Immutability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.exists():
            raise FileNotFoundError(f"Missing baseline hash manifest: {MANIFEST_PATH}")
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            cls.manifest = json.load(f)

        if not METRIC_SNAP_PATH.exists():
            raise FileNotFoundError(f"Missing metric snapshot: {METRIC_SNAP_PATH}")
        with open(METRIC_SNAP_PATH, "r", encoding="utf-8") as f:
            cls.metric_snapshot = json.load(f)

        if not FAIL_SNAP_PATH.exists():
            raise FileNotFoundError(f"Missing failure snapshot: {FAIL_SNAP_PATH}")
        with open(FAIL_SNAP_PATH, "r", encoding="utf-8") as f:
            cls.failure_snapshot = json.load(f)

    def test_01_protected_artifact_hashes(self):
        """Verify all 39 protected V3.2.1 artifacts have identical SHA-256 hashes to baseline manifest."""
        files = self.manifest["files"]
        self.assertGreaterEqual(len(files), 39, "Expected at least 39 protected artifacts in manifest")

        mismatches = []
        for rel_path, meta in files.items():
            full_path = WORKSPACE_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Protected V3.2.1 file deleted or missing: {rel_path}")
            current_hash = compute_sha256(full_path)
            expected_hash = meta["sha256"]
            if current_hash != expected_hash:
                mismatches.append(f"{rel_path}: expected {expected_hash}, got {current_hash}")

        self.assertEqual(len(mismatches), 0, f"MUTATION DETECTED in protected V3.2.1 artifacts:\n" + "\n".join(mismatches))

    def test_02_v3_2_1_frozen_state_flag(self):
        """Verify V3.2.1 release descriptor retains release_state == FINAL_FROZEN."""
        frozen_json_path = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure/V3.2.1_FINAL_FROZEN.json"
        with open(frozen_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["release_state"], "FINAL_FROZEN")
        self.assertEqual(data["decision"], "FINAL_RELEASE_ACCEPTED_WITH_LIMITATIONS")
        self.assertEqual(data["operational_status"], "APPROVED_FOR_BOUNDED_OPERATIONAL_PILOT")

    def test_03_canonical_metric_drift_zero(self):
        """Verify all 18 canonical metrics have zero numerical or lineage drift from locked baseline."""
        reg_path = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure/canonical_metric_registry.json"
        with open(reg_path, "r", encoding="utf-8") as f:
            curr_reg = json.load(f)

        snap_metrics = {m["metric_id"]: m for m in self.metric_snapshot["metrics"]}
        curr_metrics = {m["metric_id"]: m for m in curr_reg["metrics"]}

        self.assertEqual(len(snap_metrics), len(curr_metrics))
        for m_id, snap_m in snap_metrics.items():
            self.assertIn(m_id, curr_metrics, f"Missing metric {m_id} in active registry")
            curr_m = curr_metrics[m_id]
            self.assertEqual(snap_m["value"], curr_m["value"], f"Metric {m_id} value altered!")
            self.assertEqual(snap_m.get("ci_lower"), curr_m.get("ci_lower"), f"Metric {m_id} CI lower altered!")
            self.assertEqual(snap_m.get("ci_upper"), curr_m.get("ci_upper"), f"Metric {m_id} CI upper altered!")

    def test_04_failure_catalog_semantics_preserved(self):
        """Verify failure catalog summary maintains 55 master entries (49 confirmed + 6 hypotheses)."""
        curr_summary_path = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure/failure_catalog_summary.json"
        with open(curr_summary_path, "r", encoding="utf-8") as f:
            curr_sum = json.load(f)
        snap_sum = self.failure_snapshot["catalog_summary"]

        self.assertEqual(curr_sum["master_catalog_entries"], snap_sum["master_catalog_entries"])
        self.assertEqual(curr_sum["confirmed_failure_modes"], snap_sum["confirmed_failure_modes"])
        self.assertEqual(curr_sum["resolved_failure_modes"], snap_sum["resolved_failure_modes"])
        self.assertEqual(curr_sum["documented_boundary_ids"], snap_sum["documented_boundary_ids"])
        self.assertEqual(curr_sum["unreproduced_candidate_hypotheses"], snap_sum["unreproduced_candidate_hypotheses"])

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV321Immutability)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
