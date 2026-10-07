# V3.3.3 CROSS-SCENE FORENSIC REPORT & FINAL EXTERNAL GATE (REV 1 — CORRECTED)

**Experiment ID**: `EXP_333_01_EXTERNAL_FACILITY`  
**Milestone**: `SAFETY_BACKFIRE_AI_V3.3.3`  
**Revision**: `REV_1_CORRECTED` (Re-issued under `PCN-V3.3.3-20260928`)  
**Audit Scope**: Multi-Facility Cross-Scene Forensic Synthesis (`RUN_003_NVIDIA_WAREHOUSE_026` + `RUN_004_NVIDIA_WAREHOUSE_027`)  
**Publication Date**: 2026-09-28T22:30:00Z  
**Original Artifact**: `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md` (Preserved)  
**Correction Notice**: `outputs/v3_3_3/exp_333_01/provenance/PROVENANCE_CORRECTION_NOTICE_V3_3_3.md`  
**Software Readiness**: `VERIFIED_FOR_EXTERNAL_EVALUATION`  
**External Dataset Readiness**: `INADEQUATE_FOR_SAFETY_CERTIFICATION`  
**System State**: `AWAITING_FULLY_ANNOTATED_SENSOR_DATASET`  

---

> [!NOTE]
> **Revision Summary (REV 1)**: This corrected edition supersedes previous working interpretations of data provenance. In accordance with NVIDIA's official dataset documentation ([https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces)), `Warehouse_026` and `Warehouse_027` are recognized as **`REAL_WORLD_TEST_CAPTURE`** scenes released on 2026-06-04 within a mixed-provenance benchmark. Camera calibration is categorized as **dataset-provided**, empirical camera tilt observations are restricted to the 11 observed cameras without global generalization, and unvalidated ground-truth comparisons are classified as **scientifically invalid self-validation**.

---

## 1. Synthesis of Scale & Robustness

The V3.3.3 zero-adaptation external evaluation successfully scaled across two real-world test captures (`Warehouse_026` and `Warehouse_027`) released by NVIDIA as part of the **NVIDIA PhysicalAI-SmartSpaces** benchmark:

```
                            Warehouse_026 (RUN_003)   Warehouse_027 (RUN_004)    Combined Total
Real-World Test Captures:   1 (WH026)                 1 (WH027)                  2 Scenes
Synchronized Cameras:       4 cameras                 7 cameras                  11 Cameras
Total Video Frames:         7,200 frames              12,600 frames              19,800 Frames @ 30 FPS
Video Stream Duration:      240.0 seconds             420.0 seconds              660.0 s (11.0 minutes)
Total Detections:           10,942                    34,894                     45,836 Instances
Forklift Detections:        3,983                     3,968                      7,951 Forklifts
Worker / Person Detections: 6,959                     30,926                     37,885 Workers
Active Track Trajectories:  81 tracks                 237 tracks                 318 Unique Tracks
Detection Density:          1.52 dets/frame           2.77 dets/frame            2.315 dets/frame
Weighted Mean Distance:     6.923 m                   6.342 m                    6.481 m
In-ODD Range (<=8m):        71.54% (7,828)            74.32% (25,933)            73.66% (33,761)
Degraded Range (8-10m):     10.71% (1,172)             9.27% (3,233)              9.61% (4,405)
Out-of-ODD Range (>10m):    17.75% (1,942)            16.42% (5,728)             16.73% (7,670)
```

### Absolute Governance Integrity
* **Zero Parameter Tuning**: Not a single hyperparameter of the detection or tracking pipeline was adjusted between scenes.
* **Zero Threshold Manipulation**: Detection confidence threshold remained strictly anchored at $0.25$ and ByteTrack parameters remained untouched.
* **Model H Baseline Immobility**: Canonical baseline ($k_0 = 2.40, \beta_d = 0.08, \beta_l = 0.12, \beta_{\text{pitch}} = 0.22$) remained 100% frozen with zero hash drift across all 39 protected project files.
* **Zero Cross-Contamination**: Data, calibration matrices, and intermediate representations for `Warehouse_026` and `Warehouse_027` were processed in strictly isolated execution environments.

---

## 2. Architectural Findings: Camera Pitch Distribution in Benchmark Scenes

Forensic decomposition of the 11 extrinsic matrices $[R \mid t]$ across both test captures revealed:

### The Empirical Depression Angles
* **`Warehouse_026` (4 Cameras)**: Mean optical axis depression angle = **$27.74^\circ$** (Range: $24.33^\circ$ to $31.94^\circ$).
* **`Warehouse_027` (7 Cameras)**: Mean optical axis depression angle = **$27.42^\circ$** (Range: $20.56^\circ$ to $35.69^\circ$).
* **Combined 11-Camera Mean**: **$27.54^\circ$**.

### Governance Scope Constraint
Across the 11 cameras analyzed in Warehouse_026 and Warehouse_027, the optical-axis depression angles derived from the supplied calibration were within the observed range of **$20.56^\circ$–$35.69^\circ$**. This observation is limited to the two benchmark scenes and must not be generalized to industrial warehouses as a whole.

* **Calibration Provenance**: Camera calibration is **dataset-provided**. The available project evidence does not independently establish the physical surveying methodology or field measurement uncertainty underlying the supplied calibration.
* **Governance Conformance**: The pipeline correctly rejected raw Euler decomposition artifacts (which misleadingly suggested steep angles up to $68.5^\circ$) and systematically applied the physical penalty $\beta_{\text{pitch}} = 0.22$ across all 45,836 observations because the derived depression angles were $<40.0^\circ$.

---

## 3. The Limits of Observational Audits: Execution Evidence vs. Performance Claims

Scientific rigor requires drawing an unyielding line between proven engineering execution capabilities and unestablished safety claims:

### What Is PROVEN (Execution Evidence):
1. **Scalability & Architecture**: The perception and tracking harness processed 19,800 frames across 11 synchronized camera streams without memory leaks, frame drops, or runtime divergence.
2. **Calibrated Geometry Engine**: The pipeline successfully ingested novel, scene-specific calibration matrices and dynamically resolved ground-plane metric coordinates ($C = -R^T t$, $H_{\text{img}\to\text{ground}} = (P_{:, [0,1,3]})^{-1}$) with validated reprojection precision (RMSE $0.0542$ in WH026; RMSE $0.0925$ in WH027).
3. **Automated ODD Profiling**: Dynamically categorized 45,836 observations into certified ($73.66\%$), degraded ($9.61\%$), and out-of-domain ($16.73\%$) strata, successfully identifying extreme depth corridor challenges in `Camera_0001` ($77.62\% >10\text{m}$) and `Camera_0004` ($54.74\% >10\text{m}$).

### What CANNOT Be Claimed (Unestablished Claims):
1. **Perception F1 / Precision / Recall**: **`NOT_ESTABLISHED`**. NVIDIA officially withholds human ground-truth bounding box annotations for real-world test scenes. Generating precision or recall against model predictions would constitute **scientifically invalid self-validation (methodologically invalid ground-truth substitution)**.
2. **Tracking Robustness (IDF1 / MOTA / HOTA)**: **`NOT_ESTABLISHED`**. Although track fragmentation was observed (rising from $20.2$ tracks/camera in WH026 to $33.9$ tracks/camera in the human-dense WH027), true identity-switch penalties and trajectory continuity cannot be computed without annotated ground-truth trajectories.
3. **Model H Formal Coverage**: **`NOT_ESTABLISHED`**. Model H formal coverage remains unestablished because the physical lux telemetry required by the illumination-dependent component is not available in the released evaluation package. Prohibiting default proxy substitutions maintains the integrity of the safety case.
4. **Cross-Warehouse Generalization**: **`NOT_ESTABLISHED`**. High observational throughput across two benchmark scenes proves software execution robustness, but statistical safety generalization requires comparative evaluation against verified ground truth across a representative population of facilities.
5. **Safety Backfire AI Validation**: **`NOT_ESTABLISHED`**. Safety Backfire validation remains pending independent event-level ground truth (pre-intervention, intervention, and post-intervention outcome labeling).
6. **Regulatory Safety Certification & Conformity**: **`NOT_ESTABLISHED`**. The current results provide engineering evidence relevant to verification planning under ISO 3691-4:2023, while V3.4 governance is informed by the credibility concepts of ASME V&V 40:2018. The project is strictly **not certified** and formal regulatory conformity is **not established**.

---

## 4. Final Gates & Milestone Status Matrix

The definitive state of Milestone V3.3.3 is summarized below:

| Dimension | Canonical Classification | Justification & Reference |
|---|---|---|
| **Data Provenance** | `REAL_WORLD_EXTERNAL_BENCHMARK` | Real-world test captures from NVIDIA PhysicalAI-SmartSpaces |
| **Dataset Composition** | `MIXED_PROVENANCE_DATASET` | Benchmark contains synthetic training scenes and real test scenes |
| **Warehouse_026** | `REAL_WORLD_TEST_CAPTURE` | 4 cameras, 7,200 frames, official 2026-06-04 release |
| **Warehouse_027** | `REAL_WORLD_TEST_CAPTURE` | 7 cameras, 12,600 frames, official 2026-06-04 release |
| **Ground Truth** | `WITHHELD_FOR_TEST_SCENES` | Withheld by benchmark publisher for blind testing |
| **Physical Lux** | `NOT_AVAILABLE` (`UNKNOWN`) | No physical illuminance meter telemetry provided |
| **Perception Accuracy** | `NOT_ESTABLISHED` | Requires independent human bounding box ground truth |
| **Tracking Accuracy** | `NOT_ESTABLISHED` | Requires independent trajectory ground truth |
| **Model H Coverage** | `NOT_ESTABLISHED` | Frozen parameters intact; lux telemetry missing |
| **Safety Backfire Validation** | `NOT_ESTABLISHED` | Requires independent intervention event ground truth |
| **Safety Certification** | `NOT_ESTABLISHED` | Inadequate sensor data & ground truth for certification |
| **Software Pipeline Status** | `VERIFIED_FOR_EXTERNAL_EVALUATION` | 19,800 frames ingested without software error |
| **Real-World Generalization**| `NOT_ESTABLISHED` | 2 test scenes cannot establish generalizability |

---

## 5. Artifact Manifest & Verification Records

* **Original Sealed Report**: `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md`
* **Corrected Sealed Report**: `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT_REV1_CORRECTED.md`
* **Provenance Registry (JSON)**: `outputs/v3_3_3/exp_333_01/provenance/provenance_registry.json`
* **Provenance Registry (MD)**: `outputs/v3_3_3/exp_333_01/provenance/provenance_registry.md`
* **Correction Manifest**: `outputs/v3_3_3/exp_333_01/provenance/provenance_correction_manifest.json`
* **Provenance Change Log**: `outputs/v3_3_3/exp_333_01/provenance/provenance_change_log.md`
* **Correction Notice**: `outputs/v3_3_3/exp_333_01/provenance/PROVENANCE_CORRECTION_NOTICE_V3_3_3.md`
* **Real-World Evidence Gaps Matrix**: `outputs/v3_3_3/exp_333_01/DP-SRGA-V3.3.3-01-REV1.md`
* **RUN_003 Execution Package**: `outputs/v3_3_3/exp_333_01/runs/RUN_003_NVIDIA_WAREHOUSE_026/`
* **RUN_004 Execution Package**: `outputs/v3_3_3/exp_333_01/runs/RUN_004_NVIDIA_WAREHOUSE_027/`
* **Comprehensive Test Suite**: **100% unit and integrity tests passing**
