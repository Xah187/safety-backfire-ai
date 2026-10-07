"""
validation/v3_3_3/test_run_004_integrity.py
Unit test suite verifying integrity, cryptographic provenance, and governance gates for RUN_004_NVIDIA_WAREHOUSE_027.
"""

import sys
import json
import hashlib
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


def compute_sha256(fp: Path) -> str:
    hasher = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class TestRun004Integrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.exp_dir = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01"
        cls.run4_dir = cls.exp_dir / "runs/RUN_004_NVIDIA_WAREHOUSE_027"
        cls.metrics_dir = cls.run4_dir / "metrics"
        cls.per_camera_dir = cls.run4_dir / "per_camera"
        cls.lineage_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/model_h_lineage.json"
        cls.hash_manifest_path = cls.run4_dir / "run_004_hash_manifest.json"

    def test_01_run_isolation_preserved(self):
        """Test 01: Verify RUN_001, RUN_002, and RUN_003 remain preserved without overwrite."""
        run1 = self.exp_dir / "runs/RUN_001_INVALIDATED_RUNTIME_MISMATCH"
        run2 = self.exp_dir / "runs/RUN_002_CANONICAL_CONFORMANCE"
        run3 = self.exp_dir / "runs/RUN_003_NVIDIA_WAREHOUSE_026"
        self.assertTrue(run1.exists(), "RUN_001 directory must be preserved")
        self.assertTrue(run2.exists(), "RUN_002 directory must be preserved")
        self.assertTrue(run3.exists(), "RUN_003 directory must be preserved")
        self.assertTrue((run3 / "run_003_hash_manifest.json").exists())

    def test_02_run_004_artifacts_exist(self):
        """Test 02: Verify RUN_004 required artifacts and manifests exist."""
        self.assertTrue(self.run4_dir.exists(), "RUN_004 directory must exist")
        self.assertTrue(self.hash_manifest_path.exists(), "run_004_hash_manifest.json must exist")
        self.assertTrue((self.run4_dir / "run_004_manifest.json").exists())
        self.assertTrue((self.run4_dir / "odd_observation_ledger_027.json").exists())
        self.assertTrue((self.run4_dir / "camera_extrinsic_convention_audit_027.json").exists())
        self.assertTrue((self.run4_dir / "cross_scene_distribution_shift.json").exists())
        self.assertTrue((self.run4_dir / "canonical_evaluation.json").exists())
        self.assertTrue((self.run4_dir / "observation_ledger.json").exists())
        self.assertTrue((self.run4_dir / "track_topology.json").exists())

    def test_03_data_volume_and_seven_cameras(self):
        """Test 03: Verify 12,600 frames across 7 cameras in Warehouse_027."""
        eval_path = self.run4_dir / "canonical_evaluation.json"
        self.assertTrue(eval_path.exists())
        with open(eval_path, "r", encoding="utf-8") as f:
            ev = json.load(f)

        manifest = ev["run_manifest"]
        self.assertEqual(manifest["total_frames_processed"], 12600)
        self.assertEqual(manifest["cameras_processed"], 7)
        self.assertGreater(manifest["total_detection_instances"], 1000)

        for i in range(7):
            cam_id = f"Camera_{i:04d}"
            self.assertIn(cam_id, manifest["per_camera_summary"])
            self.assertEqual(manifest["per_camera_summary"][cam_id]["frames_processed"], 1800)

    def test_04_model_h_parameter_freeze(self):
        """Test 04: Verify Model H parameters are frozen at canonical values."""
        with open(self.lineage_path, "r", encoding="utf-8") as f:
            lineage = json.load(f)

        params = lineage["parameters"]
        self.assertEqual(params["k0"], 2.40)
        self.assertEqual(params["beta_d"], 0.08)
        self.assertEqual(params["beta_l"], 0.12)
        self.assertEqual(params["beta_pitch"], 0.22)
        self.assertEqual(params["gamma_occ"], {"NONE": 0.0, "PARTIAL": 0.20, "HEAVY": 0.40})

    def test_05_optical_axis_pitch_decomposition(self):
        """Test 05: Verify pitch is extracted from optical axis depression angle."""
        audit_path = self.run4_dir / "camera_extrinsic_convention_audit_027.json"
        self.assertTrue(audit_path.exists())
        with open(audit_path, "r", encoding="utf-8") as f:
            audit = json.load(f)

        for i in range(7):
            cam_id = f"Camera_{i:04d}"
            cam_audit = audit["per_camera_audit"][cam_id]
            dep_deg = cam_audit["physical_optical_depression_deg"]
            self.assertGreater(dep_deg, 15.0)
            self.assertLess(dep_deg, 40.0)
            self.assertEqual(cam_audit["pitch_governance_decision"], "DEPRESSION_ANGLE_APPLIED (Euler artifact discarded)")

    def test_06_model_h_input_insufficient_lux_only(self):
        """Test 06: Verify Model H reports INPUT_INSUFFICIENT strictly due to missing lux."""
        unc_path = self.metrics_dir / "uncertainty_metrics.json"
        self.assertTrue(unc_path.exists())
        with open(unc_path, "r", encoding="utf-8") as f:
            um = json.load(f)

        self.assertEqual(um["model_h_formal_status"], "INPUT_INSUFFICIENT")
        self.assertEqual(um["model_h_reason"], "MISSING_ILLUMINATION_LUX")
        self.assertEqual(um["missing_inputs"], ["illumination_lux"])
        self.assertIn("mode_a_no_occlusion", um)
        self.assertIn("mode_b_with_occlusion_proxy", um)

    def test_07_hash_manifest_verification(self):
        """Test 07: Verify cryptographic integrity across all generated JSON artifacts."""
        with open(self.hash_manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["run_id"], "RUN_004_NVIDIA_WAREHOUSE_027")
        self.assertGreater(len(manifest["artifacts"]), 10)

        for rel_path, expected_hash in manifest["artifacts"].items():
            if rel_path == "run_004_hash_manifest.json":
                continue
            artifact_file = self.run4_dir / rel_path
            self.assertTrue(artifact_file.exists(), f"Missing artifact: {rel_path}")
            current_hash = compute_sha256(artifact_file)
            self.assertEqual(current_hash, expected_hash, f"Hash mismatch in {rel_path}")


if __name__ == "__main__":
    unittest.main()
