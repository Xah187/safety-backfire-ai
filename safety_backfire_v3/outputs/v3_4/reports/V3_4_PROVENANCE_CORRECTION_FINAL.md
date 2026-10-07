# V3.4 Data Provenance Correction & Governance Hardening Final Report

**Report Identifier**: `V3_4-PROV-CORR-FINAL-01`  
**Milestone**: `SAFETY_BACKFIRE_AI_V3.4`  
**Release Date**: 2026-09-28T22:45:00Z  
**Classification**: Formal Governance and Safety Assurance Technical Report  
**Authoritative Reference**: NVIDIA PhysicalAI-SmartSpaces Official Dataset Card ([https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces))  
**Governance Framework**: ISO 3691-4:2023, ISO 13849-1:2023, ASME V&V 40:2018  

---

## 1. Executive Summary

This report establishes the definitive, audited data provenance resolution for Safety Backfire AI, correcting previous data classification discrepancies in V3.3.3 and hardening the governance infrastructure for V3.4.

Based on official NVIDIA dataset documentation and the release changelog dated **2026-06-04**, the benchmark **NVIDIA PhysicalAI-SmartSpaces** is formally classified as a **`MIXED_PROVENANCE_DATASET`**. While early benchmark components were synthetically generated using Omniverse and Cosmos Transfer, test scenes **`Warehouse_026`** (4 synchronized cameras, 7,200 frames) and **`Warehouse_027`** (7 synchronized cameras, 12,600 frames) are officially designated as **`REAL_WORLD_TEST_CAPTURE`** scenes.

The 19,800 frames, 11 synchronized camera streams, 45,836 detections, and 318 tracks processed during V3.3.3 represent valid **`REAL_WORLD_EXTERNAL_EXECUTION_EVIDENCE`**. However, because NVIDIA withholds ground-truth annotations (bounding boxes, trajectories, and depth maps) for blind benchmark evaluation, and because synchronized physical lux meter telemetry is unavailable, perception accuracy, tracking fidelity, Model H formal coverage, and Safety Backfire validation remain strictly **`NOT_ESTABLISHED`**.

All historical sealed artifacts have been preserved without alteration. Revision artifacts have been published alongside them, supported by automated programmatic gates (`provenance_gate.py`), formal source authority schemas (`source_authority.schema.json`), and comprehensive governance test suites (`test_provenance_governance.py`).

Milestone V3.4 is formally redefined as **`REAL_WORLD_EVIDENCE_COMPLETION`**.

---

## 2. Root Cause Analysis

The provenance classification error originated from three distinct root causes:

1. **Blind Sub-Dataset Assumption (Over-Generalization)**:
   Early project briefs extracted the top-level dataset description (*"This dataset is synthetically generated with Omniverse and Cosmos Transfer..."*) and incorrectly applied it uniformly across all splits, failing to account for the official 2026-06-04 changelog that introduced `Warehouse_026` and `Warehouse_027` as physical, real-world test captures.
2. **Conflation of Calibration with Field Surveying**:
   In the forensic synthesis, Cartesian extrinsic matrices and homography arrays supplied with the benchmark were described as *"independently surveyed facilities"*. In reality, the calibration was provided by the dataset publisher without accompanying in-situ physical transit survey logs or field measurement uncertainty bounds.
3. **Over-Generalization of Camera Pitch Statistics**:
   The empirical observation that optical-axis depression angles across the 11 benchmark cameras ranged from $20.56^\circ$ to $35.69^\circ$ was incorrectly generalized into an assertion that *"real-world logistics facilities always deploy shallow cameras"*. A sample of 11 cameras across 2 scenes cannot support universal claims regarding global warehouse architecture.

---

## 3. Official Source Evidence

The definitive truth is established by NVIDIA's official documentation:

* **Repository**: `nvidia/PhysicalAI-SmartSpaces` on HuggingFace Hub ([https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces))
* **License**: CC-BY-4.0 (NVIDIA Corporation)
* **Official Release Changelog (2026-06-04)**:
  - Added `MTMC_Tracking_2026/test/Warehouse_026`: 4 synchronized cameras, 1,800 frames per camera (60s @ 30 FPS, 1080p), raw video + Cartesian calibration matrices provided. Classified explicitly as a real-world test capture.
  - Added `MTMC_Tracking_2026/test/Warehouse_027`: 7 synchronized cameras, 1,800 frames per camera (60s @ 30 FPS, 1080p), raw video + Cartesian calibration matrices provided. Classified explicitly as a real-world test capture.
  - Ground truth bounding boxes, multi-camera trajectories, and depth maps are **officially withheld** for external blind benchmark evaluation.
  - Earlier training scenes are synthetically generated using NVIDIA Omniverse and Cosmos Transfer.

---

## 4. Correct Canonical Classification

The repository enforces the following canonical taxonomy:

```
┌─────────────────────────────────┬──────────────────────────────────────────┐
│ ENTITY                          │ CANONICAL PROVENANCE CLASSIFICATION      │
├─────────────────────────────────┼──────────────────────────────────────────┤
│ NVIDIA PhysicalAI-SmartSpaces   │ MIXED_PROVENANCE_DATASET                 │
│ Warehouse_026                   │ REAL_WORLD_TEST_CAPTURE                  │
│ Warehouse_027                   │ REAL_WORLD_TEST_CAPTURE                  │
│ Early Benchmark Scenes          │ SYNTHETIC_BENCHMARK                      │
│ Camera Calibration              │ DATASET_PROVIDED                         │
│ Physical Lux Telemetry          │ NOT_AVAILABLE (UNKNOWN)                  │
│ Ground Truth Status             │ WITHHELD_FOR_TEST_SCENES                 │
│ Optical Tilt Depression Range   │ 20.56° to 35.69° (Limited to 11 cameras) │
└─────────────────────────────────┴──────────────────────────────────────────┘
```

* **Calibration Clarification**: *"The available project evidence does not independently establish the physical surveying methodology or field measurement uncertainty underlying the supplied calibration."*
* **Camera Pitch Clarification**: *"Across the 11 cameras analyzed in Warehouse_026 and Warehouse_027, the optical-axis depression angles derived from the supplied calibration were within the observed range of 20.56°–35.69°. This observation is limited to the two benchmark scenes and must not be generalized to industrial warehouses as a whole."*

---

## 5. Affected V3.3.3 Claims & Resolutions

| Historical Claim | Resolution / Corrective Action |
|---|---|
| *"The dataset is entirely synthetic."* | Replaced with: *"The NVIDIA PhysicalAI-SmartSpaces benchmark contains mixed provenance, including synthetic scenes and the real-world Warehouse_026 and Warehouse_027 test captures."* |
| *"Warehouse_026/027 are synthetic simulations with a sim-to-real gap."* | Replaced with real-world classification; sim-to-real gap replaced by the `REAL-WORLD EVIDENCE GAPS` matrix. |
| *"Independently surveyed physical warehouse facilities."* | Corrected to *"dataset-provided calibration"* with explicit measurement uncertainty caveats. |
| *"Global warehouse mounting standards refute top-down cameras."* | Scope restricted to the 11 observed benchmark cameras; global generalization retracted. |
| *"Self-validation is scientific fraud."* | Replaced with objective ASME V&V 40 terminology: *"scientifically invalid self-validation (methodologically invalid ground-truth substitution)"*. |

---

## 6. Corrected V3.3.3 Milestone State

The authoritative status of Milestone V3.3.3 is officially sealed as:

```
DATA_PROVENANCE             = REAL_WORLD_EXTERNAL_BENCHMARK
DATASET_COMPOSITION         = MIXED_PROVENANCE_DATASET
WH026                       = REAL_WORLD_TEST_CAPTURE
WH027                       = REAL_WORLD_TEST_CAPTURE
GROUND_TRUTH                = WITHHELD_FOR_TEST_SCENES
PHYSICAL_LUX                = NOT_AVAILABLE
PERCEPTION_ACCURACY         = NOT_ESTABLISHED
TRACKING_ACCURACY           = NOT_ESTABLISHED
MODEL_H_FORMAL_COVERAGE     = NOT_ESTABLISHED
SAFETY_BACKFIRE_VALIDATION  = NOT_ESTABLISHED
SAFETY_CERTIFICATION        = NOT_ESTABLISHED
SOFTWARE_PIPELINE_STATUS    = VERIFIED_FOR_EXTERNAL_EVALUATION
REAL_WORLD_GENERALIZATION   = NOT_ESTABLISHED
```

---

## 7. Remaining Real-World Evidence Gaps

The 10 critical evidence dimensions identified in `DP-SRGA-V3.3.3-01-REV1` remain unaddressed in the released benchmark and define the acquisition requirements for V3.4:

1. **Human Bounding Box Ground Truth**: Withheld by NVIDIA; required to evaluate detector precision, recall, and F1.
2. **Trajectory Ground Truth**: Withheld by NVIDIA; required to evaluate IDF1, MOTA, and HOTA tracking metrics.
3. **Physical Lux Telemetry**: Absent; required to evaluate illumination-dependent uncertainty in Model H.
4. **Independent Camera Survey**: Absent; required to establish absolute millimeter-level physical mounting accuracy.
5. **Physical Camera Calibration Validation**: Absent; required to quantify lens distortion and reprojection uncertainty in field conditions.
6. **Long-Term Camera Drift**: Absent; required to verify mechanical and thermal extrinsic stability over extended operational durations.
7. **Physical Sensor Noise Characterization**: Absent; required to model low-light sensor SNR and compression macroblocking.
8. **Physical Lighting Variation**: Absent; required to evaluate performance under dynamic diurnal shifts and glare conditions.
9. **Safety Intervention Ground Truth**: Absent; required to establish whether proximity events warranted emergency braking.
10. **Safety Backfire Event Ground Truth**: Absent; required to verify whether safety interventions induced secondary hazards.

---

## 8. Model H Status: Frozen Baseline & Lux Handling

* **Model H Parameters**: Strictly frozen:
  $$k_0 = 2.40, \quad \beta_d = 0.08, \quad \beta_l = 0.12, \quad \beta_{\text{pitch}} = 0.22$$
* **Model H Hash Drift**: **ZERO (0.0%)**. All 39 baseline files remain completely immobilized.
* **Lux Telemetry**: Physical lux is **`NOT_AVAILABLE`**. The formal value is strictly **`UNKNOWN`**. It is never defaulted to 0, never estimated via pixel brightness, and never synthesized.
* **Formal Coverage**: **`NOT_ESTABLISHED`** because the physical lux telemetry required by the illumination-dependent component is not available in the released evaluation package. Prohibiting default proxy substitutions maintains the integrity of the safety case.

---

## 9. Safety Backfire Validation Status

Safety Backfire validation remains strictly **`NOT_ESTABLISHED`**. 

No claim is made that Safety Backfire has been validated, that it detects risk, or that Model H predicts real-world safety outcomes. Formal validation requires independent, human-verified event ground truth following the canonical state sequence:
$$\text{PRE} \longrightarrow \text{INTERVENTION} \longrightarrow \text{POST}$$
with explicit tracking of `PRIMARY_ZONE` risk reduction, `SECONDARY_ZONE` risk alteration, and definitive human-adjudicated labels (`BACKFIRE`, `NO_BACKFIRE`, `AMBIGUOUS`).

---

## 10. V3.4 Updated Objective: Real-World Evidence Completion

Milestone V3.4 does **not** begin from zero video acquisition. Real-world multi-camera video footage (19,800 frames across 11 cameras) and Cartesian calibrations were successfully acquired in V3.3.3.

The formal mission of Milestone V3.4 is **`REAL_WORLD_EVIDENCE_COMPLETION`**, focused on bridging the remaining gaps:
* Integrating independent human ground truth for detection and tracking.
* Ingesting synchronized physical lux meter telemetry.
* Implementing in-situ physical camera survey verification.
* Establishing structured safety intervention and Safety Backfire event ground truth.

---

## 11. Files Changed (Modified)

* `docs/V3_4_EVIDENCE_ACQUISITION_SPEC.md`: Updated mission statement to `REAL_WORLD_EVIDENCE_COMPLETION` and replaced "scientific fraud" with "methodologically invalid ground-truth substitution".

---

## 12. Files Preserved (Sealed Historical Records)

In compliance with non-destructive audit standards, all original artifacts remain intact:
* `outputs/v3_3_3/exp_333_01/V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md` (Original cross-scene report)
* `outputs/v3_3_3/exp_333_01/DATA_PROVENANCE_AND_SIM_TO_REAL_GAP_ASSESSMENT.md` (Original gap assessment)
* `outputs/v3_3_3/exp_333_01/final_v3_3_3_gate_status.json` (Original gate status)
* `outputs/v3_3_3/exp_333_01/runs/RUN_003_NVIDIA_WAREHOUSE_026/` (7,200 frames execution evidence)
* `outputs/v3_3_3/exp_333_01/runs/RUN_004_NVIDIA_WAREHOUSE_027/` (12,600 frames execution evidence)
* `outputs/v3_3_3/baseline/v3_3_2_source_hash_manifest.json` (Protected baseline manifest)

---

## 13. Test Suites & Verification Execution

All regression and governance test suites were executed using the project virtual environment (`.venv/bin/python`):

```
┌─────────────────────────────────────────────────────────────┬──────────┬────────┐
│ TEST SUITE                                                  │ TESTS    │ RESULT │
├─────────────────────────────────────────────────────────────┼──────────┼────────┤
│ tests/v3_4/test_provenance_governance.py                    │ 12 tests │ PASS   │
│ tests/v3_4/test_schema_validation.py                        │ 15 tests │ PASS   │
│ validation/v3_3_3/test_exp_333_01_integrity.py              │ 9 tests  │ PASS   │
│ validation/v3_3_3/test_run_003_integrity.py                 │ 7 tests  │ PASS   │
│ validation/v3_3_3/test_run_004_integrity.py                 │ 7 tests  │ PASS   │
│ validation/v3_3_3/test_model_h_canonical_conformance.py     │ 10 tests │ PASS   │
│ validation/v3_3_3/test_external_ingestion_gate.py           │ 20 tests │ PASS   │
│ validation/v3_3_3/test_exp_333_01_forensic_reconciliation.py│ 5 tests  │ PASS   │
│ validation/v3_3_3/test_v3_3_3_integrity.py                  │ 25 tests │ PASS   │
├─────────────────────────────────────────────────────────────┼──────────┼────────┤
│ TOTAL VERIFICATION SUITE                                    │ 110/110  │ 100%   │
└─────────────────────────────────────────────────────────────┴──────────┴────────┘
```

---

## 14. Provenance Gate Verification Result

Executing `scripts/v3_4/provenance_gate.py` against the central registry:

```json
{
  "gate_status": "PASS",
  "total_evaluated": 3,
  "total_passed": 3,
  "total_failed": 0,
  "evaluations": {
    "Warehouse_026": {
      "status": "PASS",
      "errors": [],
      "provenance_class": "REAL_WORLD_TEST_CAPTURE"
    },
    "Warehouse_027": {
      "status": "PASS",
      "errors": [],
      "provenance_class": "REAL_WORLD_TEST_CAPTURE"
    },
    "Synthetic_Scenes_Warehouse": {
      "status": "PASS",
      "errors": [],
      "provenance_class": "SYNTHETIC_BENCHMARK"
    }
  }
}
```

$$\textbf{PROVENANCE\_GATE} = \textbf{PASS}$$

---

## 15. Final Milestone Status Summary

```
PROVENANCE_CORRECTION       = PASS
WH026_CLASSIFICATION        = REAL_WORLD_TEST_CAPTURE
WH027_CLASSIFICATION        = REAL_WORLD_TEST_CAPTURE
MODEL_H_DRIFT               = NONE
RAW_DATA_INTEGRITY          = PASS
DOCUMENTATION_AUDIT         = PASS
PROVENANCE_GATE             = PASS
V3_4_STATUS                 = READY_FOR_EVIDENCE_ACQUISITION
```
