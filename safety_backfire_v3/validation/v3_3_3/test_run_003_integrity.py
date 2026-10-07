"""
validation/v3_3_3/test_run_003_integrity.py
Unit test suite verifying integrity, cryptographic provenance, and governance gates for RUN_003_NVIDIA_WAREHOUSE_026.
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


class TestRun003Integrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.exp_dir = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01"
        cls.run3_dir = cls.exp_dir / "runs/RUN_003_NVIDIA_WAREHOUSE_026"
        cls.metrics_dir = cls.run3_dir / "metrics"
        cls.per_camera_dir = cls.run3_dir / "per_camera"
        cls.lineage_path = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/model_h_lineage.json"
        cls.hash_manifest_path = cls.run3_dir / "run_003_hash_manifest.json"

    def test_01_run_isolation_preserved(self):
        """Test 01: Verify RUN_001 and RUN_002 remain preserved and uncorrupted."""
        run1 = self.exp_dir / "runs/RUN_001_INVALIDATED_RUNTIME_MISMATCH"
        run2 = self.exp_dir / "runs/RUN_002_CANONICAL_CONFORMANCE"
        self.assertTrue(run1.exists(), "RUN_001 directory must be preserved")
        self.assertTrue(run2.exists(), "RUN_002 directory must be preserved")
        self.assertTrue((run1 / "run_manifest.json").exists())
        self.assertTrue((run2 / "canonical_conformance_evaluation.json").exists())

    def test_02_run_003_structure_and_hash_manifest(self):
        """Test 02: Verify RUN_003 artifacts exist and match cryptographic hash manifest."""
        self.assertTrue(self.run3_dir.exists())
        self.assertTrue(self.hash_manifest_path.exists())

        with open(self.hash_manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["run_id"], "RUN_003_NVIDIA_WAREHOUSE_026")
        self.assertGreater(len(manifest["artifacts"]), 5)

        for rel_path, expected_hash in manifest["artifacts"].items():
            if rel_path == "run_003_hash_manifest.json":
                continue
            artifact_file = self.run3_dir / rel_path
            self.assertTrue(artifact_file.exists(), f"Missing artifact: {rel_path}")
            current_hash = compute_sha256(artifact_file)
            self.assertEqual(current_hash, expected_hash, f"Hash mismatch in {rel_path}")

    def test_03_data_volume_and_cameras(self):
        """Test 03: Verify 7,200 frames across 4 cameras and 10,942 total detections."""
        eval_path = self.run3_dir / "canonical_evaluation.json"
        self.assertTrue(eval_path.exists())
        with open(eval_path, "r", encoding="utf-8") as f:
            ev = json.load(f)

        manifest = ev["run_manifest"]
        self.assertEqual(manifest["total_frames_processed"], 7200)
        self.assertEqual(manifest["cameras_processed"], 4)
        self.assertEqual(manifest["total_detection_instances"], 10942)

        for cam_id in ["Camera_0000", "Camera_0001", "Camera_0002", "Camera_0003"]:
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

    def test_05_distance_evidence_from_calibrated_homography(self):
        """Test 05: Verify distance evidence is FROM_CALIBRATED_HOMOGRAPHY with RMSE 0.0542."""
        geom_path = self.metrics_dir / "geometry_metrics.json"
        self.assertTrue(geom_path.exists())
        with open(geom_path, "r", encoding="utf-8") as f:
            gm = json.load(f)

        self.assertEqual(gm["distance_evidence_type"], "FROM_CALIBRATED_HOMOGRAPHY")
        self.assertEqual(gm["reprojection_rmse"], 0.0542)
        self.assertEqual(gm["total_distance_measurements"], 10942)
        self.assertAlmostEqual(gm["distance_mean_m"], 6.923, places=2)
        self.assertGreater(gm["distance_range_m"][0], 1.0)
        self.assertLess(gm["distance_range_m"][1], 30.0)

    def test_06_model_h_input_insufficient_lux_only(self):
        """Test 06: Verify Model H reports INPUT_INSUFFICIENT strictly due to missing lux."""
        unc_path = self.metrics_dir / "uncertainty_metrics.json"
        self.assertTrue(unc_path.exists())
        with open(unc_path, "r", encoding="utf-8") as f:
            um = json.load(f)

        self.assertEqual(um["model_h_formal_status"], "INPUT_INSUFFICIENT")
        self.assertEqual(um["model_h_reason"], "MISSING_ILLUMINATION_LUX")
        self.assertEqual(um["missing_inputs"], ["illumination_lux"])
        self.assertFalse(um["default_substitution_performed"])
        self.assertEqual(um["available_inputs"]["distance_m"], "FROM_CALIBRATED_HOMOGRAPHY")
        self.assertEqual(um["available_inputs"]["camera_pitch_deg"], "FROM_CALIBRATED_EXTRINSIC")
        self.assertEqual(um["available_inputs"]["occlusion_state"], "DERIVED_FROM_BBOX_IOU")

    def test_07_perception_and_tracking_honesty(self):
        """Test 07: Verify perception and tracking metrics honestly report NOT_ESTABLISHED without GT."""
        perc_path = self.metrics_dir / "perception_metrics.json"
        track_path = self.metrics_dir / "tracking_metrics.json"
        self.assertTrue(perc_path.exists())
        self.assertTrue(track_path.exists())

        with open(perc_path, "r", encoding="utf-8") as f:
            pm = json.load(f)
        self.assertEqual(pm["perception_f1"], "NOT_ESTABLISHED")
        self.assertFalse(pm["ground_truth_available"])

        with open(track_path, "r", encoding="utf-8") as f:
            tm = json.load(f)
        self.assertEqual(tm["tracking_idf1"], "NOT_ESTABLISHED")
        self.assertEqual(tm["total_active_tracks"], 81)


if __name__ == "__main__":
    unittest.main()
