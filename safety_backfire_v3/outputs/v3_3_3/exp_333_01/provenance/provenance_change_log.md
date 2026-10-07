# Provenance Governance Change Log

**Governance Scope**: V3.3.3 Re-Issue & V3.4 Infrastructure Transition  
**Audit Standard**: ISO 3691-4 / ASME V&V 40 Provenance Traceability  
**Publication Date**: 2026-09-28T22:20:00Z  

---

## 1. Change Entries

### Entry 001
* **FILE**: `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md` (preserved), revised in `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT_REV1_CORRECTED.md`
* **LINE**: 15
* **OLD**: `The V3.3.3 zero-adaptation external evaluation successfully scaled across two authentic, independently surveyed warehouse facilities provided by the NVIDIA PhysicalAI-SmartSpaces benchmark:`
* **NEW**: `The V3.3.3 zero-adaptation external evaluation successfully scaled across two real-world test captures (Warehouse_026 and Warehouse_027) released by NVIDIA as part of the MTMC_Tracking_2026 benchmark. The available project evidence does not independently establish the physical surveying methodology or field measurement uncertainty underlying the supplied calibration:`
* **REASON**: Inaccurate attribution of independent surveying to camera calibration matrices, and need to clearly distinguish real-world test capture designation from unverified physical surveying claims.
* **SOURCE**: NVIDIA PhysicalAI-SmartSpaces Official Dataset Card ([https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces))
* **DATE**: 2026-09-28

---

### Entry 002
* **FILE**: `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md` (preserved), revised in `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT_REV1_CORRECTED.md`
* **LINE**: 54-56
* **OLD**: `This assumption is empirically refuted by real-world warehouse deployments: 1. In authentic logistics facilities, cameras are mounted on structural ceiling beams (2.5m - 3.6m height) and angled horizontally to achieve long corridor visibility. 2. Across all 11 cameras in two completely distinct facilities, 100% of cameras operate at shallow depression angles between 20.56° and 35.69°.`
* **NEW**: `Across the 11 cameras analyzed in Warehouse_026 and Warehouse_027, the optical-axis depression angles derived from the supplied calibration were within the observed range of 20.56°–35.69°. This observation is limited to the two benchmark scenes and must not be generalized to industrial warehouses as a whole.`
* **REASON**: Over-generalization of an empirical finding from a 2-scene sample (11 cameras) to all industrial warehouse facilities globally.
* **SOURCE**: Statistical Sampling Scope Review & Section 5E Governance Rule
* **DATE**: 2026-09-28

---

### Entry 003
* **FILE**: `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md` (preserved), revised in `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT_REV1_CORRECTED.md`
* **LINE**: 72
* **OLD**: `Generating precision or recall against model predictions would constitute scientific fraud.`
* **NEW**: `Generating precision or recall against model predictions would constitute scientifically invalid self-validation (methodologically invalid ground-truth substitution) because ground truth is officially withheld by NVIDIA for these test scenes.`
* **REASON**: Replacement of subjective/accusatory legal phrasing ("scientific fraud") with objective, standard engineering verification terminology.
* **SOURCE**: ASME V&V 40 Verification and Validation Terminology Standard & Section 22 Governance Rule
* **DATE**: 2026-09-28

---

### Entry 004
* **FILE**: `outputs/v3_3_3/exp_333_01/DATA_PROVENANCE_AND_SIM_TO_REAL_GAP_ASSESSMENT.md` (preserved), re-issued in `outputs/v3_3_3/exp_333_01/DP-SRGA-V3.3.3-01-REV1.md`
* **LINE**: Multiple sections (Title, Executive Summary, Section 1, Section 2)
* **OLD**: Describing Warehouse_026 and Warehouse_027 as "synthetically generated via Omniverse and Cosmos Transfer" and analyzing them purely as a "sim-to-real gap" where synthetic rendering artifacts were assumed to cause perception issues.
* **NEW**: Reclassifying Warehouse_026 and Warehouse_027 as `REAL_WORLD_TEST_CAPTURE` scenes within a `MIXED_PROVENANCE_DATASET`. Replacing the sim-to-real rendering assumption with a structured `REAL-WORLD EVIDENCE GAPS` matrix covering missing annotations (human BBox GT, trajectory GT, physical lux telemetry, independent physical camera surveying, and safety intervention/backfire event labels).
* **REASON**: Aligning project analysis with NVIDIA's official 2026-06-04 release documentation confirming Warehouse_026 and Warehouse_027 are real-world captures, and properly characterizing the actual deficiency: missing sensor telemetry and withheld ground truth, rather than synthetic imagery.
* **SOURCE**: NVIDIA PhysicalAI-SmartSpaces Official Dataset Card and 2026-06-04 Release Changelog
* **DATE**: 2026-09-28

---

### Entry 005
* **FILE**: `outputs/v3_3_3/exp_333_01/final_v3_3_3_gate_status.json`
* **LINE**: 82
* **OLD**: `"empirical_finding": "Industrial ceiling mounting practices overwhelmingly favor shallow perspectives (20° to 35°) rather than steep top-down perspectives (>= 40°). The canonical top-down assumption is empirically refuted in both independent facilities."`
* **NEW**: `"empirical_finding": "Across the 11 cameras analyzed in Warehouse_026 and Warehouse_027, the optical-axis depression angles derived from the supplied calibration were within the observed range of 20.56°–35.69°. This observation is limited to the two benchmark scenes and must not be generalized to industrial warehouses as a whole."`
* **REASON**: Eliminating unwarranted global generalization from two test scenes, in accordance with Section 5E.
* **SOURCE**: Provenance Governance Rule 5E
* **DATE**: 2026-09-28

---

### Entry 006
* **FILE**: Repository-wide Specifications (V3.3.3 and V3.4)
* **LINE**: Milestone definitions
* **OLD**: Framing V3.4 as needing to acquire real-world video footage from scratch because V3.3.3 had none.
* **NEW**: Framing V3.4 as `REAL_WORLD_EVIDENCE_COMPLETION`: real-world multi-camera video and dataset-provided calibration were already acquired in V3.3.3 (Warehouse_026 and Warehouse_027); V3.4 must acquire the missing independent evidence dimensions: human bounding box ground truth, trajectory ground truth, physical lux telemetry, independent physical camera surveys, and safety intervention / backfire ground truth.
* **REASON**: Preserving the authentic value of the 19,800 frames, 11 cameras, and 45,836 detections processed in V3.3.3 without conflating execution evidence with performance validation.
* **SOURCE**: Sections 7, 18, and 19 Governance Requirements
* **DATE**: 2026-09-28
