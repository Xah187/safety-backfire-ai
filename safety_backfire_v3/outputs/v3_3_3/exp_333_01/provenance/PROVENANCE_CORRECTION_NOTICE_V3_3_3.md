# PROVENANCE CORRECTION NOTICE — V3.3.3
## Formal Reclassification of External Benchmark Datasets & Re-Issue of Evaluation Findings

**Notice Identifier**: `PCN-V3.3.3-20260928`  
**Effective Date**: 2026-09-28T22:25:00Z  
**Target Milestone**: `SAFETY_BACKFIRE_AI_V3.3.3` (EXP_333_01)  
**Governance Authority**: Safety Backfire AI Provenance Assurance Committee  
**Status**: `OFFICIALLY_ISSUED_AND_SEALED`  

---

## 1. Background & Context of Reclassification

During internal governance auditing of the `EXP_333_01` evaluation artifacts, a critical data provenance classification discrepancy was identified regarding the **NVIDIA PhysicalAI-SmartSpaces** benchmark.

### 1.1 The Erroneous Assumptions
In certain preliminary documents (notably `DP-SRGA-V3.3.3-01` and earlier working notes):
1. The entire **NVIDIA PhysicalAI-SmartSpaces** dataset was characterized as *completely synthetic* (generated exclusively via Omniverse and Cosmos Transfer), leading to the erroneous classification of `Warehouse_026` and `Warehouse_027` as synthetic simulations.
2. In contrast, in parts of the forensic synthesis, the calibration matrices were described as *"independently surveyed"* without field verification records, and the camera pitch observations ($20.56^\circ$ to $35.69^\circ$) were over-generalized to all industrial warehouses worldwide.

### 1.2 The Authoritative Reference Truth
Review of the official dataset documentation and the official release changelog dated **2026-06-04** ([https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces)) establishes the following facts:
* The **NVIDIA PhysicalAI-SmartSpaces** benchmark has a **`MIXED_PROVENANCE`** architecture.
* Earlier benchmark splits are synthetically generated (`SYNTHETIC_BENCHMARK`).
* **`Warehouse_026`** (4 synchronized cameras, 7,200 frames) and **`Warehouse_027`** (7 synchronized cameras, 12,600 frames) are explicitly released as **`real-world test captures`** (`REAL_WORLD_TEST_CAPTURE`).
* For both test scenes, raw 1080p video streams and Cartesian camera calibration matrices are released; however, human bounding box ground truth, multi-camera trajectory tracking labels, and depth maps are **withheld for test scenes** by NVIDIA for benchmark integrity, and physical lux sensor telemetry is **not available** in the released benchmark package.

---

## 2. Evidence Preservation & Non-Destructive Revision Policy

In accordance with strict safety case auditing standards (ISO 3691-4, ASME V&V 40):
* **No historical sealed artifacts have been deleted or overwritten.**
* All computational outputs ($19,800$ frames, $11$ cameras, $45,836$ detections, and $318$ unique tracks) are permanently preserved as **`REAL_WORLD_EXTERNAL_EXECUTION_EVIDENCE`**.
* The original documents are retained in place, and corrected revision documents have been generated alongside them:

| Original Sealed Artifact | Corrected Revision Artifact | Scope of Revision |
|---|---|---|
| `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md` | `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT_REV1_CORRECTED.md` | Corrects provenance descriptors, camera survey claims, global pitch generalization, and verification terminology. |
| `outputs/v3_3_3/exp_333_01/DATA_PROVENANCE_AND_SIM_TO_REAL_GAP_ASSESSMENT.md` | `outputs/v3_3_3/exp_333_01/DP-SRGA-V3.3.3-01-REV1.md` | Reclassifies test captures from synthetic to real-world, replacing sim-to-real rendering gap with a structured Real-World Evidence Gaps matrix. |
| `outputs/v3_3_3/exp_333_01/final_v3_3_3_gate_status.json` | Supplemented by `outputs/v3_3_3/exp_333_01/provenance/provenance_registry.json` | Introduces central provenance authority and schema-verified metadata. |

---

## 3. Formal Re-Definition of V3.3.3 Milestone State

The definitive engineering state of Milestone V3.3.3 is officially established as follows:

```
DATA_PROVENANCE             = REAL_WORLD_EXTERNAL_BENCHMARK
DATASET_COMPOSITION         = MIXED_PROVENANCE_DATASET
WH026                       = REAL_WORLD_TEST_CAPTURE
WH027                       = REAL_WORLD_TEST_CAPTURE
GROUND_TRUTH                = WITHHELD_FOR_TEST_SCENES
PHYSICAL_LUX                = NOT_AVAILABLE (UNKNOWN)
PERCEPTION_ACCURACY         = NOT_ESTABLISHED
TRACKING_ACCURACY           = NOT_ESTABLISHED
MODEL_H_FORMAL_COVERAGE     = NOT_ESTABLISHED
SAFETY_BACKFIRE_VALIDATION  = NOT_ESTABLISHED
SAFETY_CERTIFICATION        = NOT_ESTABLISHED
SOFTWARE_PIPELINE_STATUS    = VERIFIED_FOR_EXTERNAL_EVALUATION
REAL_WORLD_GENERALIZATION   = NOT_ESTABLISHED
```

---

## 4. Key Scientific Distinctions

1. **Execution Evidence vs. Performance Validation**:
   Successfully processing 19,800 frames without pipeline divergence constitutes robust *Execution Evidence*. It does **not** constitute *Performance Accuracy Validation* because ground truth was withheld.
2. **Missing Sensor Telemetry vs. Synthetic Artifacts**:
   Model H's `INPUT_INSUFFICIENT` status on Warehouse_026/027 is caused strictly by the absence of synchronized physical lux meter telemetry, **not** by synthetic rendering artifacts. Model H parameters remain 100% frozen ($k_0 = 2.40$).
3. **Observation vs. Global Generalization**:
   The shallow optical depression angles observed ($20.56^\circ$ to $35.69^\circ$) apply to the 11 cameras within the two benchmark scenes and must not be asserted as universal properties of all global industrial warehouses.
4. **Safety Backfire AI Status**:
   Safety Backfire AI has **not** been certified or validated for safety-critical deployment. Formal validation requires independent, human-verified event ground truth with pre-intervention, intervention, and post-intervention outcome labeling.

---

## 5. Transition to V3.4: Real-World Evidence Completion

Milestone V3.4 does not start from zero real-world data acquisition. Real-world multi-camera video and dataset-provided calibration were successfully acquired and processed in V3.3.3.

The explicit, updated mandate of **Milestone V3.4** is **`REAL_WORLD_EVIDENCE_COMPLETION`**, focusing on acquiring:
1. Human bounding box ground truth for real-world test scenes.
2. Multi-camera cross-view trajectory tracking ground truth.
3. Calibrated physical lux meter telemetry.
4. In-situ physical surveying of camera mounting geometries.
5. Safety intervention event annotations.
6. Safety Backfire ground-truth event verification (PRE $\to$ INTERVENTION $\to$ POST).
