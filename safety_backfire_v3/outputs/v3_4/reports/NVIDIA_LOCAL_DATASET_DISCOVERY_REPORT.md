# Safety Backfire AI — V3.4 Local Dataset Discovery & Official Provenance Verification Report

**Document Identifier**: `V3_4-DATASET-DISCOVERY-001`  
**Milestone**: `SAFETY_BACKFIRE_AI_V3.4`  
**Execution Timestamp**: `2026-09-29T10:06:10Z`  
**Verification Gate**: `PROVENANCE_GATE & INTEGRITY_AUDIT`  
**Authoritative Reference**: [NVIDIA PhysicalAI-SmartSpaces Official Dataset Card](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces)  
**Governance Scope**: Pre-Validation Discovery, Cryptographic Verification & Evidence Invariance  

---

## 1. Executive Summary & Final Verdict

```
================================================================================
LOCAL DATASET DISCOVERY & PROVENANCE VERIFICATION VERDICT — V3.4
================================================================================
LOCAL_NVIDIA_DATASET       = FOUND
WH026                      = VERIFIED
WH027                      = VERIFIED
PROVENANCE                 = VERIFIED
HASH_INTEGRITY             = PASS
NO_DOWNLOAD_REQUIRED       = TRUE
V3_4_ACQUISITION_STATE     = LOCAL_DATA_READY_FOR_VALIDATION
================================================================================
```

* **Core Discovery Finding**: All required NVIDIA benchmark footage and dataset-provided calibration files are already present locally on the host machine. Zero missing required files were identified.
* **Download Policy Enforcement**: **NO DOWNLOADS PERFORMED** (no `hf download`, no `git clone`, no `wget`, no `curl`, no `snapshot_download`).
* **Cryptographic Status**: 100% of all 11 video streams across both scenes match their historical run manifests and the official Hugging Face Hub download cache metadata bit-for-bit ($0$ drift, $0$ mismatch).
* **Execution Boundary**: No detection, tracking, Model H, or risk engine inferences were triggered. No files were relocated, renamed, or modified.

---

## 2. Section A: Discovery Overview

A comprehensive local filesystem scan was performed targeting the repository root, user directories (`~/Downloads`, `~/Documents`, `~/Desktop`), and cached Hugging Face directories.

### 2.1 Discovered Copies & Topologies

```
┌─────────────────┬──────────────────────┬─────────────┬────────────────────────────────────────────────────────┐
│ DATASET SCENE   │ LOGICAL STREAM COUNT │ DISCOVERED  │ LOCAL STORAGE LOCATION                                 │
├─────────────────┼──────────────────────┼─────────────┼────────────────────────────────────────────────────────┤
│ Warehouse_026   │ 4 videos + 1 calib   │ 1 copy      │ data/external_facility/raw/Warehouse_026/...           │
│ Warehouse_027   │ 7 videos + 1 calib   │ 2 copies    │ 1. data/external_facility_02/raw/Warehouse_027/...    │
│                 │                      │             │ 2. /Users/xah187/Downloads/                            │
│ Facility Pilot  │ 1 video (mock 1.0s)  │ 1 copy      │ data/external_v3_4/raw/Camera_0001.mp4 (mock pilot)    │
└─────────────────┴──────────────────────┴─────────────┴────────────────────────────────────────────────────────┘
```

### 2.2 Relocation & Preservation Status

Per project governance, **no data files were moved or deleted**.

* **Warehouse_026 Current Path**:  
  `/Users/xah187/Projects/safety-backfire-ai/data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026`  
  *Canonical Target Path*: `/Users/xah187/Projects/safety-backfire-ai/data/external_v3_4/raw/Warehouse_026`  
  *RELOCATION_REQUIRED*: `NO_PRESERVE_EXISTING_UNTIL_CONSOLIDATION` (Recorded for future phase).

* **Warehouse_027 Current Path**:  
  `/Users/xah187/Projects/safety-backfire-ai/data/external_facility_02/raw/Warehouse_027/MTMC_Tracking_2026/test/Warehouse_027`  
  *Canonical Target Path*: `/Users/xah187/Projects/safety-backfire-ai/data/external_v3_4/raw/Warehouse_027`  
  *RELOCATION_REQUIRED*: `NO_PRESERVE_EXISTING_UNTIL_CONSOLIDATION` (Recorded for future phase).

---

## 3. Section B: Warehouse_026 Deep Audit

* **Scene Classification**: `REAL_WORLD_TEST_CAPTURE`
* **Local Root Path**: `/Users/xah187/Projects/safety-backfire-ai/data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026`
* **Total Streams**: 4 synchronized physical camera feeds
* **Total Frames**: 7,200 frames (1,800 frames per camera)
* **Total Size**: 105,741,502 bytes (~100.84 MB)

### 3.1 Video Streams Technical Inventory

| Camera ID | Filename | Size (Bytes) | Size (MB) | SHA-256 Checksum | Codec | Resolution | FPS | Frames | Duration | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `Camera_0000` | `Camera_0000.mp4` | 19,802,011 | 18.88 MB | `83ed232a2f5fe3031807ed19020e1a44fe386e89b68f9bea621797f1552c9cda` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0001` | `Camera_0001.mp4` | 27,633,596 | 26.35 MB | `dd37e801eec30528e2af88d137eb3c9b68306b29ac56c014fe1f68293767bfca` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0002` | `Camera_0002.mp4` | 38,707,343 | 36.91 MB | `abe39e20ef9b2b9c64b2e66f082809951540c8c719d4fe31d5a5e0176af928ee` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0003` | `Camera_0003.mp4` | 19,598,552 | 18.69 MB | `9051adb98e17a1425c6d70486972f2dd17f7ada0c0f8023db64d504bc2bc0077` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |

### 3.2 Calibration File Verification

* **Relative Path**: `data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026/calibration.json`
* **File Size**: 8,692 bytes
* **SHA-256**: `94644b9bb5bf71d967c0b87036d9c1b8186f2c2b7e8a106ac517d2fa49640e46`
* **JSON Syntax Validity**: `VALID`
* **Calibration Type**: `cartesian`
* **Sensor Count**: 4 sensors (`Camera_0000`, `Camera_0001`, `Camera_0002`, `Camera_0003`)
* **Matrix Conformance**:
  - `intrinsicMatrix`: Present for all 4 cameras ($3 \times 3$ matrix)
  - `extrinsicMatrix`: Present for all 4 cameras ($4 \times 4$ rigid transform matrix)
  - `cameraMatrix`: Present for all 4 cameras ($3 \times 4$ projection matrix)
  - `homography`: Present for all 4 cameras ($3 \times 3$ ground-plane homography)
  - `attributes`: Valid per sensor (`fps: 30`, `frameWidth: 1920`, `frameHeight: 1080`)
* **Formal Status**: `CALIBRATION_STATUS = DATASET_PROVIDED`
* **Epistemic Invariant**: **NO PHYSICAL SURVEYING INFERRED**. Strictly prohibited from designating as `PHYSICALLY_SURVEYED` or `TOTAL_STATION_VERIFIED`.

---

## 4. Section C: Warehouse_027 Deep Audit

* **Scene Classification**: `REAL_WORLD_TEST_CAPTURE`
* **Local Root Path**: `/Users/xah187/Projects/safety-backfire-ai/data/external_facility_02/raw/Warehouse_027/MTMC_Tracking_2026/test/Warehouse_027`
* **Total Streams**: 7 synchronized physical camera feeds
* **Total Frames**: 12,600 frames (1,800 frames per camera)
* **Total Size**: 184,173,020 bytes (~175.64 MB)

### 4.1 Video Streams Technical Inventory

| Camera ID | Filename | Size (Bytes) | Size (MB) | SHA-256 Checksum | Codec | Resolution | FPS | Frames | Duration | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `Camera_0000` | `Camera_0000.mp4` | 36,433,143 | 34.75 MB | `7a56955a524e8454ba63df4878a1634fba6f8f59a6136fce9b7a35c2b54a8caa` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0001` | `Camera_0001.mp4` | 28,351,858 | 27.04 MB | `bf1bb1fd71a811cfdab83bdad01c0c4cf426124f3e7e6635a77bbdc23f68cb45` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0002` | `Camera_0002.mp4` | 29,101,239 | 27.75 MB | `29bc455831e1b80210307405601a4b33fbe00430eea8839b9c8ffd3eccfd526a` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0003` | `Camera_0003.mp4` | 27,477,008 | 26.20 MB | `7deacc1aa539bb999ea16c0f656f52695b6fb034e6269bd80e670c090023766c` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0004` | `Camera_0004.mp4` | 22,303,508 | 21.27 MB | `57934396f19a0b777da07c6171985bf861f546d42c2c0203b1a6f972a9c3a210` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0005` | `Camera_0005.mp4` | 16,892,801 | 16.11 MB | `87d37341d65464f48d1d028f63b80279d302bf341d429d73df9bf55353bd1632` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |
| `Camera_0006` | `Camera_0006.mp4` | 23,613,453 | 22.52 MB | `175816231eced5e215d1733640a65757ad9c0429b3c846966342d142aed54b1a` | h264 | 1920x1080 | 30.0 | 1800 | 60.00s | **MATCH** |

### 4.2 Calibration File Verification

* **Relative Path**: `data/external_facility_02/raw/Warehouse_027/MTMC_Tracking_2026/test/Warehouse_027/calibration.json`
* **File Size**: 14,164 bytes
* **SHA-256**: `c616492ddc892c618a765dc5924cff03e7754a6d0b9e74b71ba1c38fa723121c`
* **JSON Syntax Validity**: `VALID`
* **Calibration Type**: `cartesian`
* **Sensor Count**: 7 sensors (`Camera_0000` through `Camera_0006`)
* **Matrix Conformance**:
  - `intrinsicMatrix`: Present for all 7 cameras ($3 \times 3$ matrix)
  - `extrinsicMatrix`: Present for all 7 cameras ($4 \times 4$ rigid transform matrix)
  - `cameraMatrix`: Present for all 7 cameras ($3 \times 4$ projection matrix)
  - `homography`: Present for all 7 cameras ($3 \times 3$ ground-plane homography)
  - `attributes`: Valid per sensor (`fps: 30`, `frameWidth: 1920`, `frameHeight: 1080`)
* **Formal Status**: `CALIBRATION_STATUS = DATASET_PROVIDED`
* **Epistemic Invariant**: **NO PHYSICAL SURVEYING INFERRED**. Strictly prohibited from designating as `PHYSICALLY_SURVEYED` or `TOTAL_STATION_VERIFIED`.

---

## 5. Section D: Official NVIDIA Source Verification & Provenance Mapping

The official source of truth is the canonical dataset published by NVIDIA on Hugging Face:

* **Official Dataset Page**: [https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces)
* **Official WH026 Subtree**: [https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_026](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_026)
* **Official WH027 Subtree**: [https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_027](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_027)
* **Repository Git Commit / ETag**: `1eebcf0f74a510994fe4c886f4fa77fbc6724ea8` (Verified against Hugging Face download cache metadata on local disk).

### 5.1 Official Classification Mapping

```
┌─────────────────────────────────┬────────────────────────────────────────────────────────┐
│ GOVERNANCE DIMENSION            │ FORMAL CLASSIFICATION                                  │
├─────────────────────────────────┼────────────────────────────────────────────────────────┤
│ Dataset Name                    │ nvidia/PhysicalAI-SmartSpaces                          │
│ Dataset Overall Classification  │ MIXED_PROVENANCE_DATASET                               │
│ Warehouse_026 Classification    │ REAL_WORLD_TEST_CAPTURE                                │
│ Warehouse_027 Classification    │ REAL_WORLD_TEST_CAPTURE                                │
│ Synthetic Benchmark Splits      │ SYNTHETIC_BENCHMARK (Omniverse / Cosmos Transfer 2.5)   │
│ Ground Truth Status             │ WITHHELD_FOR_TEST_SCENES                               │
│ Physical Lux Sensor Telemetry   │ NOT_AVAILABLE_IN_RELEASE                               │
│ Calibration Status              │ DATASET_PROVIDED                                       │
│ License                         │ CC-BY-4.0                                              │
└─────────────────────────────────┴────────────────────────────────────────────────────────┘
```

* **Official Card Confirmation**: NVIDIA explicitly states in the changelog and dataset card:  
  *"Warehouse_026 and Warehouse_027 are real-world test captures (4 and 7 cameras); the first 60 s (1800 frames) per camera is provided — videos + calibration only. Their ground truth and depth maps are withheld, so the box counts and the 'Depth Maps' column reflect the synthetic scenes only."*

---

## 6. Section E: Historical Linkage to RUN_003 and RUN_004

A forensic audit of previous run scripts and manifests confirmed the exact source paths and hashes utilized during V3.3.3:

### 6.1 RUN_003_NVIDIA_WAREHOUSE_026 Linkage

* **Execution Script**: `safety_backfire_v3_3_3/experiments/execute_run_003_nvidia_warehouse.py` (line 43)
* **`RUN_003_ACTUAL_INPUT_PATH`**:  
  `/Users/xah187/Projects/safety-backfire-ai/data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026`
* **Historical Manifest**: `safety_backfire_v3/outputs/v3_3_3/exp_333_01/runs/RUN_003_NVIDIA_WAREHOUSE_026/run_manifest.json`
* **Recorded Video Hashes**:
  - `Camera_0000.mp4`: `83ed232a2f5fe3031807ed19020e1a44fe386e89b68f9bea621797f1552c9cda` $\to$ **EXACT MATCH**
  - `Camera_0001.mp4`: `dd37e801eec30528e2af88d137eb3c9b68306b29ac56c014fe1f68293767bfca` $\to$ **EXACT MATCH**
  - `Camera_0002.mp4`: `abe39e20ef9b2b9c64b2e66f082809951540c8c719d4fe31d5a5e0176af928ee` $\to$ **EXACT MATCH**
  - `Camera_0003.mp4`: `9051adb98e17a1425c6d70486972f2dd17f7ada0c0f8023db64d504bc2bc0077` $\to$ **EXACT MATCH**

### 6.2 RUN_004_NVIDIA_WAREHOUSE_027 Linkage

* **Execution Script**: `safety_backfire_v3_3_3/experiments/execute_run_004_nvidia_warehouse_027.py` (line 37)
* **`RUN_004_ACTUAL_INPUT_PATH`**:  
  `/Users/xah187/Projects/safety-backfire-ai/data/external_facility_02/raw/Warehouse_027/MTMC_Tracking_2026/test/Warehouse_027`
* **Historical Manifest**: `data/external_facility_02/manifests/warehouse_027_file_manifest.json`
* **Recorded Video Hashes**:
  - `Camera_0000.mp4` through `Camera_0006.mp4`: All 7 SHA-256 hashes $\to$ **EXACT MATCH**
  - `calibration.json`: `c616492ddc892c618a765dc5924cff03e7754a6d0b9e74b71ba1c38fa723121c` $\to$ **EXACT MATCH**

---

## 7. Section F: Integrity Comparison Matrix

Every local file was compared against three independent cryptographic baselines:
1. **Live Computation**: SHA-256 computed on disk in this turn.
2. **Historical Run Manifest**: Values locked in `RUN_003` and `RUN_004` manifests.
3. **Official Download Cache**: `.metadata` records written by `hf download` from commit `1eebcf0f74a510994fe4c886f4fa77fbc6724ea8`.

```
┌─────────────────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┬─────────┐
│ FILE IDENTIFIER                 │ LIVE SHA-256 HASH    │ RUN MANIFEST HASH    │ HF CACHE META HASH   │ VERDICT │
├─────────────────────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼─────────┤
│ WH026 / Camera_0000.mp4         │ 83ed232a2f5fe303... │ 83ed232a2f5fe303... │ 83ed232a2f5fe303... │ MATCH   │
│ WH026 / Camera_0001.mp4         │ dd37e801eec30528... │ dd37e801eec30528... │ dd37e801eec30528... │ MATCH   │
│ WH026 / Camera_0002.mp4         │ abe39e20ef9b2b9c... │ abe39e20ef9b2b9c... │ abe39e20ef9b2b9c... │ MATCH   │
│ WH026 / Camera_0003.mp4         │ 9051adb98e17a142... │ 9051adb98e17a142... │ 9051adb98e17a142... │ MATCH   │
│ WH026 / calibration.json        │ 94644b9bb5bf71d9... │ (calib hash locked)  │ 94644b9bb5bf71d9... │ MATCH   │
│ WH027 / Camera_0000.mp4         │ 7a56955a524e8454... │ 7a56955a524e8454... │ 7a56955a524e8454... │ MATCH   │
│ WH027 / Camera_0001.mp4         │ bf1bb1fd71a811cf... │ bf1bb1fd71a811cf... │ bf1bb1fd71a811cf... │ MATCH   │
│ WH027 / Camera_0002.mp4         │ 29bc455831e1b802... │ 29bc455831e1b802... │ 29bc455831e1b802... │ MATCH   │
│ WH027 / Camera_0003.mp4         │ 7deacc1aa539bb99... │ 7deacc1aa539bb99... │ 7deacc1aa539bb99... │ MATCH   │
│ WH027 / Camera_0004.mp4         │ 57934396f19a0b77... │ 57934396f19a0b77... │ 57934396f19a0b77... │ MATCH   │
│ WH027 / Camera_0005.mp4         │ 87d37341d65464f4... │ 87d37341d65464f4... │ 87d37341d65464f4... │ MATCH   │
│ WH027 / Camera_0006.mp4         │ 175816231eced5e2... │ 175816231eced5e2... │ 175816231eced5e2... │ MATCH   │
│ WH027 / calibration.json        │ c616492ddc892c61... │ c616492ddc892c61... │ c616492ddc892c61... │ MATCH   │
└─────────────────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┴─────────┘
```

* **Cryptographic Verdict**:  
  $$\textbf{LOCAL\_FILE\_INTEGRITY} = \textbf{MATCH} \quad (100\%)$$

---

## 8. Section G: Duplicate Copies Analysis

A duplicate scan was conducted to locate redundant copies of videos across host volumes:

### 8.1 Discovered Duplicate Sets

* **Warehouse_027 Duplicate in `~/Downloads`**:
  - Contains all 7 video files (`Camera_0000.mp4` to `Camera_0006.mp4`) and `calibration.json`.
  - Sizes and SHA-256 hashes are identical to the primary files in `data/external_facility_02/raw/Warehouse_027/...` bit-for-bit.
  - `DUPLICATE_IDENTICAL = YES`
  - `DUPLICATE_CONFLICT = NO`
  - *Action*: Retained untouched in Downloads; no deletion or moving performed.

* **Warehouse_027 Auxiliary Calibration**:
  - Located at `data/external_facility_02/calibration/calibration.json`.
  - Size: 14,164 bytes, SHA-256: `c616492ddc892c618a765dc5924cff03e7754a6d0b9e74b71ba1c38fa723121c`.
  - `DUPLICATE_IDENTICAL = YES`
  - `DUPLICATE_CONFLICT = NO`

---

## 9. Section H: Missing Items & Gap Analysis

```
┌─────────────────────────────────┬──────────┬─────────────────────────────┬────────────────────────────────────┐
│ ITEM                            │ EXPECTED │ OBSERVED                    │ GOVERNANCE CLASSIFICATION          │
├─────────────────────────────────┼──────────┼─────────────────────────────┼────────────────────────────────────┤
│ Warehouse_026 Video Streams     │ 4 videos │ 4 videos present            │ COMPLETE                           │
│ Warehouse_026 Calibration       │ 1 file   │ 1 file present (valid)      │ COMPLETE                           │
│ Warehouse_027 Video Streams     │ 7 videos │ 7 videos present            │ COMPLETE                           │
│ Warehouse_027 Calibration       │ 1 file   │ 1 file present (valid)      │ COMPLETE                           │
│ Human Ground Truth Bounding Box │ Optional │ Withheld by publisher       │ WITHHELD_FOR_TEST_SCENES (Official)│
│ Ground Truth Trajectories       │ Optional │ Withheld by publisher       │ WITHHELD_FOR_TEST_SCENES (Official)│
│ Physical Lux Telemetry          │ Optional │ Not documented in release   │ NOT_AVAILABLE_IN_RELEASE (Official)│
└─────────────────────────────────┴──────────┴─────────────────────────────┴────────────────────────────────────┘
```

* **Missing Required Files**: **NONE**.
* **Download Requirement**: **`NO_DOWNLOAD_REQUIRED = TRUE`**. All evaluation footage released by NVIDIA for these two benchmark test captures is present locally and verified.

---

## 10. Final Governance Status Declaration

In strict compliance with V3.4 Governance and Epistemic Invariants:

```
LOCAL_NVIDIA_DATASET       = FOUND
WH026                      = VERIFIED
WH027                      = VERIFIED
PROVENANCE                 = VERIFIED
HASH_INTEGRITY             = PASS
NO_DOWNLOAD_REQUIRED       = TRUE
V3_4_ACQUISITION_STATE     = LOCAL_DATA_READY_FOR_VALIDATION
```

* **Associated Machine Manifests**:
  1. [`local_nvidia_video_sha256_manifest.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/manifests/local_nvidia_video_sha256_manifest.json)
  2. [`local_nvidia_provenance_verification.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/manifests/local_nvidia_provenance_verification.json)

* **Stop Condition**: Task V3.4-A is fully concluded. No further execution, data modification, or model inference is authorized.
