"""
dataset_splitter.py
Safety Backfire AI - V3.2 Real-World Dataset Splitting and Lineage Partitioning
Partitions warehouse corpus into Development, Calibration, Validation, and Blind Test.
"""

import sys
from pathlib import Path
from typing import Dict, Any
import json

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from safety_backfire_v3.validation.v3_2.metadata import VideoMetadataV1, LineageStatus, DatasetSplit
from safety_backfire_v3.validation.v3_2.provenance import DatasetManifestV1

def build_v3_2_dataset_manifest(workspace_root: Path) -> DatasetManifestV1:
    manifest = DatasetManifestV1()

    # Video 1: Cam 1 (Aisle Junction) - Historical Development
    v1_path = workspace_root / "test.mp4"
    meta_v1 = VideoMetadataV1(
        video_id="CAM01_AISLE_TRANSIT_DEV",
        camera_id="CAM_OVERHEAD_AISLE_01",
        location_id="WAREHOUSE_CENTRAL_BAY_A",
        source_type="OVERHEAD_GANTRY_CCTV",
        capture_session_id="SESS_HISTORICAL_2026_01",
        capture_date="2026-08-15",
        capture_duration_sec=14.21,
        resolution=(640, 360),
        fps=29.97,
        camera_height_m=4.50,
        camera_pitch_deg=45.0,
        camera_roll_deg=0.0,
        camera_yaw_deg=0.0,
        lens_information="WIDE_ANGLE_FIXED_4MM",
        calibration_version="HOMOGRAPHY_METHOD_E_V3_0_4",
        floor_type="SMOOTH_SEALED_CONCRETE",
        floor_slope_deg=0.0,
        lighting_condition="FLUORESCENT_HIGH_BAY_350LUX",
        traffic_density="HIGH_CONVERGING",
        known_interventions=[],
        known_constraints=["NO_PHYSICAL_BARRIER", "MIXED_PEDESTRIAN_FORKLIFT_TRAFFIC"],
        dataset_split=DatasetSplit.DEVELOPMENT,
        lineage_status=LineageStatus.KNOWN_DEVELOPMENT_DATA,
        notes="Historical video from V2/V3.0 testing with converging pedestrian and forklift"
    )
    manifest.register_video(meta_v1, v1_path)

    # Video 2: Cam 2 (Cross Aisle & Racks) - Calibration Partition (First 375 frames)
    v2_path = workspace_root / "test2.mp4"
    meta_v2 = VideoMetadataV1(
        video_id="CAM02_RACK_CORRIDOR_CALIB",
        camera_id="CAM_OVERHEAD_RACK_02",
        location_id="WAREHOUSE_HIGHBAY_CORRIDOR_B",
        source_type="HIGH_MOUNT_CCTV",
        capture_session_id="SESS_VALIDATION_2026_02",
        capture_date="2026-09-02",
        capture_duration_sec=15.00,
        resolution=(1274, 720),
        fps=25.00,
        camera_height_m=5.20,
        camera_pitch_deg=38.5,
        camera_roll_deg=-0.5,
        camera_yaw_deg=12.0,
        lens_information="VARIFOCAL_6MM",
        calibration_version="PROJECTIVE_HOMOGRAPHY_V3_0_5",
        floor_type="INDUSTRIAL_CONCRETE_VARNISHED",
        floor_slope_deg=0.2,
        lighting_condition="DUAL_ROW_LED_450LUX",
        traffic_density="MODERATE",
        known_interventions=["DEMARCATED_PEDESTRIAN_ZONE"],
        known_constraints=["RACK_PROXIMITY_BLIND_CORNER"],
        dataset_split=DatasetSplit.CALIBRATION,
        lineage_status=LineageStatus.CALIBRATION_DATA,
        notes="Partition A: frames 0 to 375 used strictly for parameter calibration"
    )
    manifest.register_video(meta_v2, v2_path)

    # Video 3: Cam 2 (Cross Aisle & Racks) - Validation Partition (Frames 375 to 875)
    meta_v3 = VideoMetadataV1(
        video_id="CAM02_RACK_CORRIDOR_VAL",
        camera_id="CAM_OVERHEAD_RACK_02",
        location_id="WAREHOUSE_HIGHBAY_CORRIDOR_B",
        source_type="HIGH_MOUNT_CCTV",
        capture_session_id="SESS_VALIDATION_2026_02",
        capture_date="2026-09-02",
        capture_duration_sec=20.00,
        resolution=(1274, 720),
        fps=25.00,
        camera_height_m=5.20,
        camera_pitch_deg=38.5,
        camera_roll_deg=-0.5,
        camera_yaw_deg=12.0,
        lens_information="VARIFOCAL_6MM",
        calibration_version="PROJECTIVE_HOMOGRAPHY_V3_0_5",
        floor_type="INDUSTRIAL_CONCRETE_VARNISHED",
        floor_slope_deg=0.2,
        lighting_condition="DUAL_ROW_LED_450LUX",
        traffic_density="MODERATE_TURNING",
        known_interventions=["DEMARCATED_PEDESTRIAN_ZONE"],
        known_constraints=["RACK_PROXIMITY_BLIND_CORNER"],
        dataset_split=DatasetSplit.VALIDATION,
        lineage_status=LineageStatus.VALIDATION_DATA,
        notes="Partition B: frames 375 to 875 used for development validation"
    )
    manifest.register_video(meta_v3, v2_path)

    # Video 4: Cam 2 (Cross Aisle & Racks) - Blind Test Partition (Frames 875 to 1246)
    meta_v4 = VideoMetadataV1(
        video_id="CAM02_RACK_CORRIDOR_BLIND",
        camera_id="CAM_OVERHEAD_RACK_02",
        location_id="WAREHOUSE_HIGHBAY_CORRIDOR_B",
        source_type="HIGH_MOUNT_CCTV",
        capture_session_id="SESS_VALIDATION_2026_02",
        capture_date="2026-09-02",
        capture_duration_sec=14.84,
        resolution=(1274, 720),
        fps=25.00,
        camera_height_m=5.20,
        camera_pitch_deg=38.5,
        camera_roll_deg=-0.5,
        camera_yaw_deg=12.0,
        lens_information="VARIFOCAL_6MM",
        calibration_version="PROJECTIVE_HOMOGRAPHY_V3_0_5",
        floor_type="INDUSTRIAL_CONCRETE_VARNISHED",
        floor_slope_deg=0.2,
        lighting_condition="DUAL_ROW_LED_450LUX",
        traffic_density="VARIABLE_EVASIVE",
        known_interventions=["DEMARCATED_PEDESTRIAN_ZONE"],
        known_constraints=["RACK_PROXIMITY_BLIND_CORNER"],
        dataset_split=DatasetSplit.BLIND_TEST,
        lineage_status=LineageStatus.BLIND_TEST_DATA,
        notes="Partition C: frames 875 to 1246 completely held out for blind testing"
    )
    manifest.register_video(meta_v4, v2_path)

    # Video 5: Cam 3 (Loading Bay / Workstation Perspective) - Camera-Independent Blind Test
    v5_path = workspace_root / "safety_backfire_v04/data/source_videos/videoplayback.mp4"
    meta_v5 = VideoMetadataV1(
        video_id="CAM03_LOADING_BAY_BLIND_OVERHEAD",
        camera_id="CAM_GANTRY_BAY_03",
        location_id="WAREHOUSE_LOADING_DOCK_SECTION",
        source_type="VERTICAL_GANTRY_CAMERA",
        capture_session_id="SESS_INDEPENDENT_2026_03",
        capture_date="2026-09-10",
        capture_duration_sec=10.00,
        resolution=(704, 1280),
        fps=30.00,
        camera_height_m=6.10,
        camera_pitch_deg=52.0,
        camera_roll_deg=1.2,
        camera_yaw_deg=-25.0,
        lens_information="WIDE_ANGLE_FISHEYE_CORRECTED",
        calibration_version="INTRINSIC_PINHOLE_EXTRINSIC_SURVEY",
        floor_type="TEXTURED_SLIP_RESISTANT",
        floor_slope_deg=1.1,
        lighting_condition="MIXED_DAYLIGHT_SODIUM",
        traffic_density="HEAVY_PALLET_STAGING",
        known_interventions=["DOCK_BUFFER_LINE"],
        known_constraints=["HIGH_ASPECT_RATIO", "OCCLUDED_STAGING"],
        dataset_split=DatasetSplit.BLIND_TEST,
        lineage_status=LineageStatus.BLIND_TEST_DATA,
        notes="Completely independent camera, location, and aspect ratio for out-of-camera blind testing"
    )
    manifest.register_video(meta_v5, v5_path)

    return manifest

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent.parent.parent
    manifest = build_v3_2_dataset_manifest(root)
    audit = manifest.audit_independence()
    print("Dataset Manifest Independence Audit:")
    print(json.dumps(audit, indent=2))
    
    out_dir = root / "safety_backfire_v3/outputs/v3_2"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "dataset_manifest.json", "w") as f:
        json.dump(manifest.to_dict(), f, indent=2)
    with open(out_dir / "dataset_split_manifest.json", "w") as f:
        json.dump({"splits": manifest.splits, "audit": audit}, f, indent=2)
    print("Saved dataset_manifest.json and dataset_split_manifest.json successfully.")
