"""
validation/v3_3_3/test_model_h_canonical_conformance.py
10 mandatory regression tests enforcing Section 19 Model H Canonical Conformance:
1. frozen formula is reproduced exactly;
2. d<=4 has zero distance penalty;
3. L>=300 has zero illumination penalty;
4. pitch>=40 has zero pitch term;
5. NONE/PARTIAL/HEAVY map correctly;
6. missing lux blocks canonical Model H execution;
7. missing pitch blocks canonical Model H execution;
8. runtime cannot substitute default values;
9. RUN_001 remains immutable;
10. V3.3.2 protected artifacts remain unchanged.
"""

import sys
import json
import hashlib
import unittest
from pathlib import Path

def find_workspace_root() -> Path:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "data").is_dir() and (p / "safety_backfire_v3").is_dir():
            return p
        p = p.parent
    return Path("/Users/xah187/Projects/safety-backfire-ai")

WORKSPACE_ROOT = find_workspace_root()
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3_3_3.uncertainty.model_h import (
    K0, BETA_D, BETA_L, BETA_PITCH, PITCH_THRESHOLD_DEG, GAMMA_OCC,
    compute_distance_penalty, compute_illumination_penalty, compute_pitch_penalty, compute_occlusion_penalty,
    compute_canonical_model_h
)

def compute_sha256(fp: Path) -> str:
    hasher = hashlib.sha256()
    with open(fp, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class TestModelHCanonicalConformance(unittest.TestCase):
    """10 required regression tests for Model H Conformance (Section 19)."""

    @classmethod
    def setUpClass(cls):
        cls.exp_dir = WORKSPACE_ROOT / "outputs/v3_3_3/exp_333_01"
        cls.run1_dir = cls.exp_dir / "runs/RUN_001_INVALIDATED_RUNTIME_MISMATCH"
        cls.run2_dir = cls.exp_dir / "runs/RUN_002_CANONICAL_CONFORMANCE"
        cls.baseline_manifest = WORKSPACE_ROOT / "outputs/v3_3_3/baseline/v3_3_2_source_hash_manifest.json"
        cls.lineage_file = WORKSPACE_ROOT / "outputs/v3_3_3/reconciliation/model_h_lineage.json"

    def test_01_frozen_formula_reproduced_exactly(self):
        """Test 1: Frozen formula and parameters are reproduced exactly without drift."""
        with open(self.lineage_file, "r", encoding="utf-8") as f:
            lineage = json.load(f)
        params = lineage["parameters"]

        self.assertEqual(K0, params["k0"])
        self.assertEqual(BETA_D, params["beta_d"])
        self.assertEqual(BETA_L, params["beta_l"])
        self.assertEqual(BETA_PITCH, params["beta_pitch"])
        self.assertEqual(PITCH_THRESHOLD_DEG, params["pitch_threshold_deg"])
        self.assertEqual(GAMMA_OCC, params["gamma_occ"])

        # Test full worst-case evaluation: 2.40 + 0.08*(8-4) + 0.12*(300/100) + 0.22 + 0.40 = 3.70
        res = compute_canonical_model_h(distance_m=8.0, illumination_lux=0.0, camera_pitch_deg=35.0, occlusion_state="HEAVY")
        self.assertEqual(res.status, "SUCCESS")
        self.assertAlmostEqual(res.k_H, 3.70, places=5)
        self.assertAlmostEqual(res.distance_term, 0.32, places=5)
        self.assertAlmostEqual(res.illumination_term, 0.36, places=5)
        self.assertAlmostEqual(res.pitch_term, 0.22, places=5)
        self.assertAlmostEqual(res.occlusion_term, 0.40, places=5)

    def test_02_distance_hinge_d_le_4_zero_penalty(self):
        """Test 2: For d <= 4.0m, distance penalty must equal 0.0; for d > 4.0m, slope is 0.08."""
        for d in [0.5, 1.0, 2.0, 3.0, 3.99, 4.0]:
            self.assertEqual(compute_distance_penalty(d), 0.0, f"Distance penalty non-zero at d={d}")

        for d in [4.5, 5.0, 6.0, 8.0, 10.0]:
            expected = round(0.08 * (d - 4.0), 6)
            self.assertAlmostEqual(compute_distance_penalty(d), expected, places=5)

    def test_03_illumination_threshold_L_ge_300_zero_penalty(self):
        """Test 3: For L >= 300.0 lux, illumination penalty must equal 0.0."""
        for lux in [300.0, 300.1, 400.0, 500.0, 1000.0]:
            self.assertEqual(compute_illumination_penalty(lux), 0.0, f"Illumination penalty non-zero at lux={lux}")

        for lux in [0.0, 50.0, 100.0, 200.0]:
            expected = round(0.12 * (300.0 - lux) / 100.0, 6)
            self.assertAlmostEqual(compute_illumination_penalty(lux), expected, places=5)

    def test_04_pitch_indicator_pitch_ge_40_zero_term(self):
        """Test 4: For pitch >= 40.0 deg, pitch term must equal 0.0; for pitch < 40.0 deg, equals 0.22."""
        for pitch in [40.0, 40.1, 45.0, 50.0, 60.0]:
            self.assertEqual(compute_pitch_penalty(pitch), 0.0, f"Pitch term non-zero at pitch={pitch}")

        for pitch in [0.0, 15.0, 30.0, 35.0, 39.9]:
            self.assertEqual(compute_pitch_penalty(pitch), 0.22, f"Pitch term incorrect at pitch={pitch}")

    def test_05_occlusion_discrete_mapping(self):
        """Test 5: NONE/PARTIAL/HEAVY map correctly to 0.00, 0.20, 0.40."""
        self.assertEqual(compute_occlusion_penalty("NONE"), 0.00)
        self.assertEqual(compute_occlusion_penalty("PARTIAL"), 0.20)
        self.assertEqual(compute_occlusion_penalty("HEAVY"), 0.40)
        with self.assertRaises(KeyError):
            compute_occlusion_penalty("UNKNOWN_STATE")

    def test_06_missing_lux_blocks_canonical_execution(self):
        """Test 6: Missing lux blocks canonical Model H execution without guessing."""
        res = compute_canonical_model_h(distance_m=5.0, illumination_lux=None, camera_pitch_deg=45.0, occlusion_state="NONE")
        self.assertEqual(res.status, "INPUT_INSUFFICIENT")
        self.assertIsNone(res.k_H)
        self.assertEqual(res.reason, "MISSING_ILLUMINATION_LUX")

    def test_07_missing_pitch_blocks_canonical_execution(self):
        """Test 7: Missing pitch blocks canonical Model H execution without guessing."""
        res = compute_canonical_model_h(distance_m=5.0, illumination_lux=300.0, camera_pitch_deg=None, occlusion_state="NONE")
        self.assertEqual(res.status, "INPUT_INSUFFICIENT")
        self.assertIsNone(res.k_H)
        self.assertEqual(res.reason, "MISSING_CAMERA_PITCH_DEG")

    def test_08_runtime_cannot_substitute_default_values(self):
        """Test 8: Runtime cannot substitute default values (e.g. L=0.50, pitch=0.0)."""
        # When neither lux nor pitch are provided, result is strictly INPUT_INSUFFICIENT
        res = compute_canonical_model_h(distance_m=6.0, illumination_lux=None, camera_pitch_deg=None, occlusion_state="NONE")
        self.assertEqual(res.status, "INPUT_INSUFFICIENT")
        self.assertIsNone(res.k_H)

    def test_09_run_001_remains_immutable(self):
        """Test 9: RUN_001 artifacts remain frozen, immutable, and preserved."""
        self.assertTrue(self.run1_dir.exists(), "RUN_001 directory must exist")
        manifest_p = self.run1_dir / "run_manifest.json"
        self.assertTrue(manifest_p.exists(), "RUN_001 run_manifest.json must exist")

        with open(manifest_p, "r", encoding="utf-8") as f:
            m = json.load(f)

        self.assertEqual(m["run_id"], "RUN_001_INVALIDATED_RUNTIME_MISMATCH")
        self.assertEqual(m["run_status"], "INVALIDATED_RUNTIME_MISMATCH")
        self.assertEqual(m["invalidated_reason"], "MODEL_H_RUNTIME_IMPLEMENTATION_NON_CONFORMANT")

        # Verify all retained artifacts in RUN_001 match their recorded hashes
        for rel_path, meta in m["retained_artifacts"].items():
            full_p = self.run1_dir / rel_path
            self.assertTrue(full_p.exists(), f"RUN_001 missing artifact: {rel_path}")
            h = compute_sha256(full_p)
            self.assertEqual(h, meta["sha256"], f"RUN_001 hash drift in {rel_path}")

    def test_10_v3_3_2_protected_artifacts_remain_unchanged(self):
        """Test 10: V3.3.2 protected artifacts remain 100% unchanged with zero hash drift."""
        with open(self.baseline_manifest, "r", encoding="utf-8") as f:
            bm = json.load(f)

        self.assertGreaterEqual(len(bm["files"]), 39, "Expected at least 39 protected artifacts")
        for fpath, meta in bm["files"].items():
            full_p = WORKSPACE_ROOT / fpath
            self.assertTrue(full_p.exists(), f"Missing baseline file: {fpath}")
            current_h = compute_sha256(full_p)
            self.assertEqual(current_h, meta["sha256"], f"Baseline hash drift in {fpath}")

if __name__ == "__main__":
    unittest.main()
