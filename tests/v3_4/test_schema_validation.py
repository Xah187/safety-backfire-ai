#!/usr/bin/env python3
"""
tests/v3_4/test_schema_validation.py
Safety Backfire AI — Version V3.4 Verification Suite.

Deterministic unit and integrity tests covering:
 1. Valid detection GT
 2. Invalid bbox
 3. Missing object ID
 4. Valid lux
 5. UNKNOWN lux
 6. Invalid negative lux
 7. Valid camera survey
 8. Missing optical-axis definition
 9. Valid intervention event
10. Overlapping PRE/POST windows
11. Invalid gt_label
12. Duplicate event_id
13. Hash mismatch
14. Facility-level split violation
15. Model H frozen parameters immobility
"""

import sys
import os
import json
import shutil
import tempfile
import unittest
import hashlib
from pathlib import Path

# Add project root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.v3_4.validate_acquisition_package import (
    AcquisitionPackageValidator,
    ValidationError
)
from scripts.v3_4.create_blind_manifest import (
    create_facility_blind_manifest,
    BlindSplitError
)
from safety_backfire_v3_3_3.uncertainty.model_h import (
    K0, BETA_D, BETA_L, BETA_PITCH, PITCH_THRESHOLD_DEG, GAMMA_OCC
)


def compute_sha256_bytes(data: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


class TestV34SchemaValidation(unittest.TestCase):
    """Rigorous test suite for V3.4 evidence schemas and governance rules."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="v3_4_test_pkg_")
        self.pkg_path = Path(self.test_dir)
        (self.pkg_path / "raw").mkdir(parents=True, exist_ok=True)
        (self.pkg_path / "metadata").mkdir(parents=True, exist_ok=True)
        (self.pkg_path / "annotations").mkdir(parents=True, exist_ok=True)

        # Create dummy dummy video file
        self.dummy_video_path = self.pkg_path / "raw" / "Camera_0001.mp4"
        self.dummy_video_content = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2avc1mp41"
        self.dummy_video_path.write_bytes(self.dummy_video_content)
        self.video_hash = compute_sha256_bytes(self.dummy_video_content)

        # Valid minimal camera survey
        self.valid_survey = {
            "facility_id": "WH_TEST_01",
            "camera_id": "Camera_0001",
            "camera_height_m": 3.25,
            "optical_axis_vector": [0.0, 0.866025, -0.5],  # Normalized unit vector
            "depression_angle_deg": 30.0,
            "roll_deg": 0.0,
            "yaw_deg": 90.0,
            "intrinsics": [
                [1000.0, 0.0, 960.0],
                [0.0, 1000.0, 540.0],
                [0.0, 0.0, 1.0]
            ],
            "distortion": [0.0, 0.0, 0.0, 0.0],
            "extrinsics": [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 0.866, -0.5, 0.0],
                [0.0, 0.5, 0.866, -3.25]
            ],
            "coordinate_system": "RIGHT_HAND_Z_UP",
            "survey_timestamp": "2026-09-28T10:00:00Z",
            "survey_source": "TOTAL_STATION_LEICA_TS16"
        }
        self.survey_file = self.pkg_path / "metadata" / "camera_survey.json"
        self.survey_file.write_text(json.dumps([self.valid_survey], indent=2), encoding="utf-8")
        self.survey_hash = compute_sha256_bytes(self.survey_file.read_bytes())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_manifest(self, **kwargs) -> Path:
        manifest = {
            "facility_id": kwargs.get("facility_id", "WH_TEST_01"),
            "source_name": "Test Industrial Facility",
            "source_uri": "https://vault.safety-ai.internal/wh_test_01",
            "acquisition_timestamp": "2026-09-28T10:00:00Z",
            "license": "Proprietary Test License",
            "camera_count": 1,
            "resolution": "1920x1080",
            "fps": 30.0,
            "duration": 60.0,
            "synchronization_method": "HARDWARE_GENLOCK",
            "synchronization_error_ms": 0.5,
            "calibration_available": True,
            "lux_available": kwargs.get("lux_available", False),
            "bbox_gt_available": kwargs.get("bbox_gt_available", False),
            "trajectory_gt_available": kwargs.get("trajectory_gt_available", False),
            "intervention_gt_available": kwargs.get("intervention_gt_available", False),
            "provenance_status": "AUTHENTIC_PHYSICAL_FACILITY_INGESTED",
            "sha256_manifest": kwargs.get("sha256_manifest", {
                "raw/Camera_0001.mp4": self.video_hash,
                "metadata/camera_survey.json": self.survey_hash
            })
        }
        mf_path = self.pkg_path / "acquisition_manifest.json"
        mf_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return mf_path

    # 1. Valid detection GT
    def test_valid_detection_gt(self):
        det_data = [{
            "facility_id": "WH_TEST_01",
            "camera_id": "Camera_0001",
            "frame_id": 0,
            "timestamp": 0.0,
            "object_id": "PERSON_001",
            "class": "person",
            "bbox": [100.0, 200.0, 150.0, 350.0],
            "foot_point": [125.0, 350.0],
            "visibility": 0.95,
            "occlusion": "NONE"
        }]
        det_file = self.pkg_path / "annotations" / "detection_gt.json"
        det_file.write_text(json.dumps(det_data, indent=2), encoding="utf-8")
        det_hash = compute_sha256_bytes(det_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "annotations/detection_gt.json": det_hash
        }
        self._write_manifest(bbox_gt_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        # Mocking video read for unit tests without full video encoding
        validator._check_03_and_04_videos = lambda manifest: None
        self.assertTrue(validator.validate())

    # 2. Invalid bbox (x_min >= x_max)
    def test_invalid_bbox(self):
        det_data = [{
            "facility_id": "WH_TEST_01",
            "camera_id": "Camera_0001",
            "frame_id": 0,
            "timestamp": 0.0,
            "object_id": "PERSON_001",
            "class": "person",
            "bbox": [300.0, 200.0, 150.0, 350.0],  # INVALID: x1 > x2
            "foot_point": [125.0, 350.0],
            "visibility": 0.95,
            "occlusion": "NONE"
        }]
        det_file = self.pkg_path / "annotations" / "detection_gt.json"
        det_file.write_text(json.dumps(det_data, indent=2), encoding="utf-8")
        det_hash = compute_sha256_bytes(det_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "annotations/detection_gt.json": det_hash
        }
        self._write_manifest(bbox_gt_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        with self.assertRaises(ValidationError) as ctx:
            validator.validate()
        self.assertIn("CHECK_08_FAIL", str(ctx.exception))

    # 3. Missing object ID
    def test_missing_object_id(self):
        det_data = [{
            "facility_id": "WH_TEST_01",
            "camera_id": "Camera_0001",
            "frame_id": 0,
            "timestamp": 0.0,
            "object_id": "",  # INVALID: Empty object ID
            "class": "person",
            "bbox": [100.0, 200.0, 150.0, 350.0],
            "foot_point": [125.0, 350.0],
            "visibility": 0.95,
            "occlusion": "NONE"
        }]
        det_file = self.pkg_path / "annotations" / "detection_gt.json"
        det_file.write_text(json.dumps(det_data, indent=2), encoding="utf-8")
        det_hash = compute_sha256_bytes(det_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "annotations/detection_gt.json": det_hash
        }
        self._write_manifest(bbox_gt_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        with self.assertRaises(ValidationError) as ctx:
            validator.validate()
        self.assertIn("CHECK_07_FAIL", str(ctx.exception))

    # 4. Valid lux
    def test_valid_lux(self):
        lux_data = [{
            "facility_id": "WH_TEST_01",
            "sensor_id": "LUX_SENSOR_01",
            "timestamp": 0.0,
            "lux": 150.5,
            "sampling_rate_hz": 10.0,
            "measurement_uncertainty": 2.5,
            "calibration_reference": "NIST_CAL_2026_09",
            "location": [10.0, 20.0, 3.0]
        }]
        lux_file = self.pkg_path / "metadata" / "lux_telemetry.json"
        lux_file.write_text(json.dumps(lux_data, indent=2), encoding="utf-8")
        lux_hash = compute_sha256_bytes(lux_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "metadata/lux_telemetry.json": lux_hash
        }
        self._write_manifest(lux_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        self.assertTrue(validator.validate())

    # 5. UNKNOWN lux
    def test_unknown_lux(self):
        lux_data = [{
            "facility_id": "WH_TEST_01",
            "sensor_id": "LUX_SENSOR_01",
            "timestamp": 0.0,
            "lux": "UNKNOWN",  # Explicitly UNKNOWN
            "sampling_rate_hz": "UNKNOWN",
            "measurement_uncertainty": "UNKNOWN",
            "calibration_reference": "UNKNOWN",
            "location": "UNKNOWN"
        }]
        lux_file = self.pkg_path / "metadata" / "lux_telemetry.json"
        lux_file.write_text(json.dumps(lux_data, indent=2), encoding="utf-8")
        lux_hash = compute_sha256_bytes(lux_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "metadata/lux_telemetry.json": lux_hash
        }
        self._write_manifest(lux_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        self.assertTrue(validator.validate())

    # 6. Invalid negative lux
    def test_invalid_negative_lux(self):
        lux_data = [{
            "facility_id": "WH_TEST_01",
            "sensor_id": "LUX_SENSOR_01",
            "timestamp": 0.0,
            "lux": -12.5,  # FORBIDDEN: Negative lux
            "sampling_rate_hz": 10.0,
            "measurement_uncertainty": 2.5,
            "calibration_reference": "NIST_CAL_2026_09",
            "location": [10.0, 20.0, 3.0]
        }]
        lux_file = self.pkg_path / "metadata" / "lux_telemetry.json"
        lux_file.write_text(json.dumps(lux_data, indent=2), encoding="utf-8")
        lux_hash = compute_sha256_bytes(lux_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "metadata/lux_telemetry.json": lux_hash
        }
        self._write_manifest(lux_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        with self.assertRaises(ValidationError) as ctx:
            validator.validate()
        self.assertIn("CHECK_11_FAIL", str(ctx.exception))

    # 7. Valid camera survey
    def test_valid_camera_survey(self):
        self._write_manifest()
        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        self.assertTrue(validator.validate())

    # 8. Missing optical-axis definition
    def test_missing_optical_axis_definition(self):
        invalid_survey = dict(self.valid_survey)
        del invalid_survey["optical_axis_vector"]
        self.survey_file.write_text(json.dumps([invalid_survey], indent=2), encoding="utf-8")
        self.survey_hash = compute_sha256_bytes(self.survey_file.read_bytes())

        self._write_manifest(sha256_manifest={
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash
        })

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        with self.assertRaises(ValidationError) as ctx:
            validator.validate()
        self.assertIn("CHECK_12_FAIL", str(ctx.exception))

    # 9. Valid intervention event
    def test_valid_intervention(self):
        ev_data = [{
            "event_id": "EV_001",
            "facility_id": "WH_TEST_01",
            "intervention_id": "INT_AGV_STOP_99",
            "intervention_type": "AGV_EMERGENCY_STOP",
            "pre_start": 10.0,
            "pre_end": 14.0,
            "intervention_start": 14.5,
            "intervention_end": 16.0,
            "post_start": 16.5,
            "post_end": 20.0,
            "primary_zone": "AISLE_04",
            "secondary_zones": ["INTERSECTION_NORTH"],
            "affected_person_ids": ["PERSON_01"],
            "affected_vehicle_ids": ["AGV_02"],
            "gt_label": "BACKFIRE",
            "reviewer_count": 2,
            "adjudicated_label": "BACKFIRE",
            "adjudication_notes": "Abrupt AGV stop provoked load tip toward pedestrian footway."
        }]
        ev_file = self.pkg_path / "annotations" / "intervention_event.json"
        ev_file.write_text(json.dumps(ev_data, indent=2), encoding="utf-8")
        ev_hash = compute_sha256_bytes(ev_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "annotations/intervention_event.json": ev_hash
        }
        self._write_manifest(intervention_gt_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        self.assertTrue(validator.validate())

    # 10. Overlapping PRE/POST windows
    def test_overlapping_pre_post_windows(self):
        ev_data = [{
            "event_id": "EV_001",
            "facility_id": "WH_TEST_01",
            "intervention_id": "INT_AGV_STOP_99",
            "intervention_type": "AGV_EMERGENCY_STOP",
            "pre_start": 10.0,
            "pre_end": 15.0,        # OVERLAP: pre_end (15.0) > intervention_start (14.0)
            "intervention_start": 14.0,
            "intervention_end": 16.0,
            "post_start": 16.5,
            "post_end": 20.0,
            "primary_zone": "AISLE_04",
            "secondary_zones": [],
            "affected_person_ids": ["PERSON_01"],
            "affected_vehicle_ids": ["AGV_02"],
            "gt_label": "NO_BACKFIRE",
            "reviewer_count": 2,
            "adjudicated_label": "NO_BACKFIRE",
            "adjudication_notes": "Window collision test."
        }]
        ev_file = self.pkg_path / "annotations" / "intervention_event.json"
        ev_file.write_text(json.dumps(ev_data, indent=2), encoding="utf-8")
        ev_hash = compute_sha256_bytes(ev_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "annotations/intervention_event.json": ev_hash
        }
        self._write_manifest(intervention_gt_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        with self.assertRaises(ValidationError) as ctx:
            validator.validate()
        self.assertIn("CHECK_14_FAIL", str(ctx.exception))

    # 11. Invalid gt_label
    def test_invalid_gt_label(self):
        ev_data = [{
            "event_id": "EV_001",
            "facility_id": "WH_TEST_01",
            "intervention_id": "INT_AGV_STOP_99",
            "intervention_type": "AGV_EMERGENCY_STOP",
            "pre_start": 10.0,
            "pre_end": 13.0,
            "intervention_start": 13.5,
            "intervention_end": 15.0,
            "post_start": 15.5,
            "post_end": 18.0,
            "primary_zone": "AISLE_04",
            "secondary_zones": [],
            "affected_person_ids": [],
            "affected_vehicle_ids": [],
            "gt_label": "POTENTIAL_HAZARD",  # FORBIDDEN LABEL
            "reviewer_count": 2,
            "adjudicated_label": "POTENTIAL_HAZARD",
            "adjudication_notes": "Invalid label test."
        }]
        ev_file = self.pkg_path / "annotations" / "intervention_event.json"
        ev_file.write_text(json.dumps(ev_data, indent=2), encoding="utf-8")
        ev_hash = compute_sha256_bytes(ev_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "annotations/intervention_event.json": ev_hash
        }
        self._write_manifest(intervention_gt_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        with self.assertRaises(ValidationError) as ctx:
            validator.validate()
        self.assertIn("CHECK_16_FAIL", str(ctx.exception))

    # 12. Duplicate event_id
    def test_duplicate_event_id(self):
        ev_data = [
            {
                "event_id": "EV_DUPLICATE_01",
                "facility_id": "WH_TEST_01",
                "intervention_id": "INT_01",
                "intervention_type": "AUDIBLE_HORN_ALERT",
                "pre_start": 1.0,
                "pre_end": 2.0,
                "intervention_start": 2.5,
                "intervention_end": 3.0,
                "post_start": 3.5,
                "post_end": 4.0,
                "primary_zone": "ZONE_A",
                "secondary_zones": [],
                "affected_person_ids": [],
                "affected_vehicle_ids": [],
                "gt_label": "NO_BACKFIRE",
                "reviewer_count": 2,
                "adjudicated_label": "NO_BACKFIRE",
                "adjudication_notes": "First instance."
            },
            {
                "event_id": "EV_DUPLICATE_01",  # DUPLICATE ID
                "facility_id": "WH_TEST_01",
                "intervention_id": "INT_02",
                "intervention_type": "AUDIBLE_HORN_ALERT",
                "pre_start": 5.0,
                "pre_end": 6.0,
                "intervention_start": 6.5,
                "intervention_end": 7.0,
                "post_start": 7.5,
                "post_end": 8.0,
                "primary_zone": "ZONE_A",
                "secondary_zones": [],
                "affected_person_ids": [],
                "affected_vehicle_ids": [],
                "gt_label": "AMBIGUOUS",
                "reviewer_count": 2,
                "adjudicated_label": "AMBIGUOUS",
                "adjudication_notes": "Second instance with same ID."
            }
        ]
        ev_file = self.pkg_path / "annotations" / "intervention_event.json"
        ev_file.write_text(json.dumps(ev_data, indent=2), encoding="utf-8")
        ev_hash = compute_sha256_bytes(ev_file.read_bytes())

        sha_manifest = {
            "raw/Camera_0001.mp4": self.video_hash,
            "metadata/camera_survey.json": self.survey_hash,
            "annotations/intervention_event.json": ev_hash
        }
        self._write_manifest(intervention_gt_available=True, sha256_manifest=sha_manifest)

        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        with self.assertRaises(ValidationError) as ctx:
            validator.validate()
        self.assertIn("CHECK_17_FAIL", str(ctx.exception))

    # 13. Hash mismatch
    def test_hash_mismatch(self):
        tampered_hash = "a" * 64
        self._write_manifest(sha256_manifest={
            "raw/Camera_0001.mp4": tampered_hash,  # Tampered
            "metadata/camera_survey.json": self.survey_hash
        })
        validator = AcquisitionPackageValidator(self.pkg_path)
        validator._check_03_and_04_videos = lambda manifest: None
        with self.assertRaises(ValidationError) as ctx:
            validator.validate()
        self.assertIn("CHECK_20_FAIL", str(ctx.exception))

    # 14. Facility-level split violation
    def test_facility_level_split_violation(self):
        mf_path = self._write_manifest(facility_id="WH_TEST_01")
        blind_out = self.pkg_path / "blind_manifest.json"

        # Attempt to hold out a non-existent facility
        with self.assertRaises(BlindSplitError) as ctx:
            create_facility_blind_manifest(
                facilities_manifests=[mf_path],
                held_out_facilities=["NON_EXISTENT_FACILITY_99"],
                output_manifest_path=blind_out
            )
        self.assertIn("not found among ingested manifests", str(ctx.exception))

    # 15. Model H frozen parameters immobility
    def test_model_h_frozen_parameters(self):
        # 1. Assert memory constants in code
        self.assertEqual(K0, 2.40, "Model H k0 parameter has drifted!")
        self.assertEqual(BETA_D, 0.08, "Model H beta_d parameter has drifted!")
        self.assertEqual(BETA_L, 0.12, "Model H beta_l parameter has drifted!")
        self.assertEqual(BETA_PITCH, 0.22, "Model H beta_pitch parameter has drifted!")
        self.assertEqual(PITCH_THRESHOLD_DEG, 40.0, "Model H pitch threshold has drifted!")
        self.assertEqual(GAMMA_OCC["NONE"], 0.00)
        self.assertEqual(GAMMA_OCC["PARTIAL"], 0.20)
        self.assertEqual(GAMMA_OCC["HEAVY"], 0.40)

        # 2. Assert against frozen reference manifest
        ref_manifest_path = WORKSPACE_ROOT / "outputs/v3_4/manifests/model_h_frozen_reference.json"
        self.assertTrue(ref_manifest_path.is_file(), "model_h_frozen_reference.json not found!")

        with open(ref_manifest_path, "r", encoding="utf-8") as f:
            ref_data = json.load(f)

        fp = ref_data["frozen_parameters"]
        self.assertEqual(fp["k0"], 2.40)
        self.assertEqual(fp["beta_d"], 0.08)
        self.assertEqual(fp["beta_l"], 0.12)
        self.assertEqual(fp["beta_pitch"], 0.22)

        # 3. Assert cryptographic hash of model_h.py implementation
        model_h_py = WORKSPACE_ROOT / "safety_backfire_v3_3_3/uncertainty/model_h.py"
        self.assertTrue(model_h_py.is_file())
        actual_hash = hashlib.sha256(model_h_py.read_bytes()).hexdigest()

        expected_hash = None
        for entry in ref_data.get("canonical_source_files", []):
            if "model_h.py" in entry.get("source_file_path", ""):
                expected_hash = entry.get("sha256")
                break

        self.assertIsNotNone(expected_hash, "Hash entry for model_h.py not found in reference manifest")
        self.assertEqual(actual_hash, expected_hash, f"Cryptographic drift detected in model_h.py! Expected {expected_hash}, got {actual_hash}")


if __name__ == "__main__":
    unittest.main()
