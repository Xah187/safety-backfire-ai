# Central Provenance Registry

**Document Identifier**: `PROV-REG-V3.3.3-01`  
**Registry Version**: `1.0.0`  
**Last Verified Date**: 2026-09-28T22:10:00Z  
**Authoritative Reference**: NVIDIA PhysicalAI-SmartSpaces Official Dataset Card ([https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces))  
**Governance Scope**: EXP_333_01 External Benchmark Evaluation & V3.4 Ingestion Pipeline  

---

## 1. Executive Provenance Overview

The NVIDIA PhysicalAI-SmartSpaces benchmark is officially classified as a **`MIXED_PROVENANCE_DATASET`**. It comprises both synthetically synthesized video scenes (via NVIDIA Omniverse and Cosmos Transfer) and designated real-world multi-camera test captures.

Specifically, as documented in the official changelog dated **2026-06-04**:
* **Warehouse_026** and **Warehouse_027** are designated as **`REAL_WORLD_TEST_CAPTURE`** scenes.
* Video streams and camera calibration matrices are released for these scenes.
* Human ground-truth annotations (bounding boxes, trajectories) and depth maps are **officially withheld** for external blind benchmark evaluation.
* Earlier benchmark scenes are classified as **`SYNTHETIC_BENCHMARK`**.

---

## 2. Central Provenance Scene Registry

| Scene ID | Dataset Name | Provenance Classification | Physical Capture Status | Calibration Status | Ground Truth Status | Physical Lux | Provenance Confidence |
|---|---|---|---|---|---|---|---|
| **Warehouse_026** | `nvidia/PhysicalAI-SmartSpaces` | `REAL_WORLD_TEST_CAPTURE` | `PHYSICAL_VIDEO_CAPTURE` | `DATASET_PROVIDED` | `WITHHELD_FOR_TEST_SCENES` | `NOT_AVAILABLE` (`UNKNOWN`) | `AUTHORITATIVE_OFFICIAL` |
| **Warehouse_027** | `nvidia/PhysicalAI-SmartSpaces` | `REAL_WORLD_TEST_CAPTURE` | `PHYSICAL_VIDEO_CAPTURE` | `DATASET_PROVIDED` | `WITHHELD_FOR_TEST_SCENES` | `NOT_AVAILABLE` (`UNKNOWN`) | `AUTHORITATIVE_OFFICIAL` |
| **Synthetic_Scenes_Warehouse** | `nvidia/PhysicalAI-SmartSpaces` | `SYNTHETIC_BENCHMARK` | `SYNTHETIC_SIMULATION` | `VIRTUAL_SYNTHETIC_SENSOR` | `SYNTHETIC_GT_GENERATED` | `NOT_APPLICABLE` | `AUTHORITATIVE_OFFICIAL` |
| **Entire Dataset** | `nvidia/PhysicalAI-SmartSpaces` | `MIXED_PROVENANCE_DATASET` | `MIXED_MODALITY` | `MIXED` | `PARTIALLY_WITHHELD` | `NOT_AVAILABLE` | `AUTHORITATIVE_OFFICIAL` |

---

## 3. Mandatory Engineering & Scientific Governance Rules

### 3.1 Dataset-Level Description Rule (Case A)
* **Prohibited**: *"The dataset is entirely synthetic."* or *"The benchmark represents authentic facilities across all scenes."*
* **Mandatory**: *"The NVIDIA PhysicalAI-SmartSpaces benchmark contains mixed provenance, including synthetic scenes and the real-world Warehouse_026 and Warehouse_027 test captures."*

### 3.2 Warehouse_026 Description Rule (Case B)
* **Mandatory**: *"Warehouse_026 is a real-world test capture released by NVIDIA as part of MTMC_Tracking_2026."*

### 3.3 Warehouse_027 Description Rule (Case C)
* **Mandatory**: *"Warehouse_027 is a real-world test capture released by NVIDIA as part of MTMC_Tracking_2026."*

### 3.4 Calibration Documentation Rule (Case D)
* **Prohibited**: Labeling camera calibration as *"virtual calibration"*, *"Omniverse camera transform"*, or *"synthetic camera extrinsics"* when referring to Warehouse_026/027.
* **Prohibited**: Labeling camera calibration as *"independently surveyed"* or *"physically surveyed"* without an independent physical surveying audit artifact.
* **Mandatory**: *"dataset-provided calibration"*, accompanied by:  
  *"The available project evidence does not independently establish the physical surveying methodology or field measurement uncertainty underlying the supplied calibration."*

### 3.5 Camera Pitch Generalization Rule (Case E)
* **Prohibited**: Claiming *"industrial warehouses generally use 20°–35°"* or *"real-world warehouses always use shallow camera angles"*.
* **Mandatory**: *"Across the 11 cameras analyzed in Warehouse_026 and Warehouse_027, the optical-axis depression angles derived from the supplied calibration were within the observed range of 20.56°–35.69°. This observation is limited to the two benchmark scenes and must not be generalized to industrial warehouses as a whole."*

### 3.6 Model H and Lux Telemetry Rule
* **Model H Parameters**: Strictly frozen ($k_0 = 2.40, \beta_d = 0.08, \beta_l = 0.12, \beta_{\text{pitch}} = 0.22$).
* **Physical Lux Telemetry**: `NOT_AVAILABLE`.
* **Value Interpretation**: Missing physical lux is strictly `UNKNOWN`. It is never converted to 0, never replaced by synthetic proxies, and never substituted with pixel brightness for formal coverage.
* **Coverage Statement**: *"Model H formal coverage remains unestablished because the physical lux telemetry required by the illumination-dependent component is not available in the released evaluation package."*

### 3.7 Ground Truth vs. Physical Lux Distinction
* **Ground Truth**: `WITHHELD_FOR_TEST_SCENES` (officially withheld by NVIDIA for competition/test evaluation).
* **Physical Lux**: `NOT_AVAILABLE` / `NOT_DOCUMENTED_IN_RELEASE` (not provided in the release package).
* These two conditions represent distinct evidence states and must never be conflated.
* Precision, recall, F1, IDF1, MOTA, and HOTA are strictly **`NOT_ESTABLISHED`**.
* Detector outputs (YOLO / ByteTrack) must **never** be treated as Ground Truth.

---

## 4. Hierarchy of Source Authority

1. **Official Dataset Documentation** (Dataset Card, Publisher Specification) — *Rank 1 (Highest)*
2. **Official Dataset Repository Metadata** (HuggingFace repository files, commit tags) — *Rank 2*
3. **Official Release Notes & Changelogs** (NVIDIA dated release notices) — *Rank 3*
4. **Primary Technical Paper** (Peer-reviewed publication introducing the benchmark) — *Rank 4*
5. **Secondary Technical Sources** (Third-party reviews, technical blogs) — *Rank 5*
6. **Internal Engineering Assumptions** (Project notes, heuristic guesses) — *Rank 6 (Lowest)*

*Conflict Resolution Rule*: A higher-ranking source strictly invalidates and overrides any conflicting lower-ranking source.
