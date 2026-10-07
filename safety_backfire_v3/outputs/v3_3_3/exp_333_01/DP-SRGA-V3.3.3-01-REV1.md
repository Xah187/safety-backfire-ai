# DATA PROVENANCE & REAL-WORLD EVIDENCE GAP ASSESSMENT (REV 1 — CORRECTED)
## Re-Evaluation of NVIDIA PhysicalAI-SmartSpaces (Warehouse_026 & Warehouse_027) Real-World Test Captures

**Document Identifier**: `DP-SRGA-V3.3.3-01-REV1`  
**Classification**: Safety Assurance Technical Report / Regulatory Evidence Audit  
**Revision Date**: 2026-09-28T22:35:00Z  
**Original Artifact**: `outputs/v3_3_3/exp_333_01/DATA_PROVENANCE_AND_SIM_TO_REAL_GAP_ASSESSMENT.md` (Preserved)  
**Correction Notice**: `outputs/v3_3_3/exp_333_01/provenance/PROVENANCE_CORRECTION_NOTICE_V3_3_3.md`  
**Authoritative Reference**: NVIDIA PhysicalAI-SmartSpaces Dataset Card & Changelog ([https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces))  

---

> [!NOTE]
> **Revision Summary (REV 1)**: This revised document supersedes the preliminary sim-to-real gap analysis. Following official NVIDIA release documentation (changelog dated 2026-06-04), `Warehouse_026` and `Warehouse_027` are recognized as **`REAL_WORLD_TEST_CAPTURE`** scenes within a mixed-provenance benchmark. The engineering limitation for these scenes is **not** synthetic rendering or domain adaptation; rather, it is the **unavailability of physical sensor telemetry and the withholding of human ground-truth annotations**.

---

## 1. Executive Summary

Although Warehouse_026 and Warehouse_027 are real-world video captures, the released evaluation package does not expose all physical sensor metadata or human ground-truth annotations required to establish the intended safety claims.

The V3.3.3 execution processed 19,800 frames across 11 synchronized camera views (4 cameras in WH026, 7 cameras in WH027), generating 45,836 detections and tracking 318 object trajectories. This establishes extensive **`REAL_WORLD_EXTERNAL_EXECUTION_EVIDENCE`**.

However, because NVIDIA officially withholds ground truth for blind benchmark evaluation, and because synchronized environmental sensors (lux meters, inclinometers) were not packaged with the release, perception accuracy, tracking fidelity, Model H formal coverage, and Safety Backfire validation remain strictly **`NOT_ESTABLISHED`**.

---

## 2. Separation of Scientific Concerns: Real-World vs. Synthetic Limitations

To avoid conflation of data limitations, the engineering framework strictly distinguishes between two separate categories of evidence gaps:

### 2.1 Synthetic Data Limitations (Applicable to Synthetic Benchmark Splits Only)
* **Domain Adaptation / Sim-to-Real Domain Gap**: Differences between Cosmos Transfer / Omniverse rendered textures and physical sensor noise patterns.
* **Physics & Kinematics Approximations**: Simulated worker movements and forklift dynamics that may deviate from real human behavior.
* **Synthetic Sensor Models**: Virtual ray-traced optics that omit physical camera lens distortion, chromatic aberration, and sensor blooming.
* *Note*: These limitations apply exclusively to the synthetic training components of PhysicalAI-SmartSpaces, **not** to Warehouse_026 or Warehouse_027.

### 2.2 Real-World Data Limitations (Applicable to Warehouse_026 & Warehouse_027)
* **Withheld Ground Truth**: Annotations (bounding boxes, trajectories, identity associations) are withheld by NVIDIA for competition/test evaluation, precluding detector accuracy verification.
* **Missing In-Situ Telemetry**: Physical illuminance (lux) logs and ambient temperature readings are absent, leaving Model H's illumination input in `UNKNOWN` status.
* **Unsurveyed Physical Mounting**: Camera calibration matrices are provided as Cartesian arrays without accompanying field survey reports or physical tilt measurement uncertainties.
* **Absence of Safety Event Annotations**: No safety intervention logs or Safety Backfire trigger annotations exist in the raw test footage.

---

## 3. Real-World Evidence Gaps Matrix

The following matrix documents the specific evidence gaps for `Warehouse_026` and `Warehouse_027`, detailing available evidence, missing evidence, safety case impact, confidence level, and required validation:

| Dimension | Evidence Available | Evidence Missing | Impact | Confidence | Validation Needed |
|---|---|---|---|---|---|
| **1. Human Bounding Box GT** | Inferred YOLOv8 detections (37,885 instances) | Hand-annotated, human-verified 2D bounding boxes | Precludes computation of Precision, Recall, and F1. Detector outputs cannot self-validate. | `HIGH` (Missing) | Acquisition of independent human-annotated bounding boxes on test splits. |
| **2. Trajectory GT** | ByteTrack automated multi-camera tracks (318 trajectories) | Verified ground-truth trajectories and cross-camera ID handovers | IDF1, MOTA, and HOTA cannot be formally established. Track fragmentation unquantifiable. | `HIGH` (Missing) | Multi-camera trajectory annotations with verified identity associations. |
| **3. Physical Lux Telemetry** | Qualitative visual exposure across 11 camera views | Calibrated NIST-traceable illuminance (lux) meter logs synchronized to frames | Model H formal coverage cannot be evaluated. Lux status remains strictly `UNKNOWN`. | `CRITICAL` (Missing) | Synchronized physical lux meter data logged during camera recording. |
| **4. Independent Camera Survey** | Dataset-supplied extrinsic matrices $[R \mid t]$ | Independent physical surveying logs, laser transit measurements, mounting height audits | Reprojection error known (RMSE 0.0542 / 0.0925), but absolute physical coordinate confidence unverified. | `MEDIUM` (Missing) | In-situ physical surveying audit of camera mount locations and tilt brackets. |
| **5. Physical Camera Calibration Validation** | Reprojection error metrics provided in dataset card | Field measurement uncertainty bounds and target-based calibration verification | Lens distortion residuals in periphery may introduce metric distance estimation errors. | `MEDIUM` (Missing) | Checkerboard / CharUco physical calibration validation on physical camera sensors. |
| **6. Long-Term Camera Drift** | 60-second fixed duration recording per camera | Multi-hour or multi-day thermal and mechanical vibration drift telemetry | Structural building vibrations and temperature swings can alter camera extrinsic tilt over time. | `MEDIUM` (Missing) | Extended time-series recording assessing mechanical tilt stability. |
| **7. Physical Sensor Noise Characterization** | Raw H.264 compressed video streams | Uncompressed raw sensor captures and sensor SNR characterization profiles | Compression artifacts (H.264 macroblocking) can degrade subtle edge detection at corridor distances $>10\text{m}$. | `LOW-MEDIUM` (Missing) | Sensor noise profile analysis on uncompressed video feeds. |
| **8. Physical Lighting Variation** | Constant ambient warehouse lighting during 60s clips | Dynamic diurnal lighting, daylight ingress shifts, and luminaire failure cases | Robustness to sudden lighting drops or high-contrast glare cannot be verified. | `MEDIUM` (Missing) | Multi-condition lighting evaluations (dawn, noon, night, emergency lighting). |
| **9. Safety Intervention Ground Truth** | Observational forklift-worker proximity interactions | Formal records of automated or manual emergency braking interventions | System cannot verify whether proximity events warranted an emergency stop under ISO 3691-4. | `CRITICAL` (Missing) | Synchronized AGV/forklift telemetry (CAN bus brake status, E-stop triggers). |
| **10. Safety Backfire Event Ground Truth** | Spatial overlap and trajectory intersection profiles | Structured ground-truth event labels: PRE $\to$ INTERVENTION $\to$ POST with PRIMARY/SECONDARY zones | Safety Backfire validation remains pending. System cannot verify whether intervention exacerbated risk. | `CRITICAL` (Missing) | Human-verified Safety Backfire annotations (BACKFIRE, NO_BACKFIRE, AMBIGUOUS). |

---

## 4. Model H Frozen Baseline & Lux Telemetry Governance

### 4.1 Parameter Invariance
Model H parameters remain strictly frozen:
$$k_0 = 2.40, \quad \beta_d = 0.08, \quad \beta_l = 0.12, \quad \beta_{\text{pitch}} = 0.22$$

Under no circumstances will parameters be tuned, adapted, or re-weighted for external benchmark data.

### 4.2 Lux Telemetry Treatment
* Physical lux measurements for Warehouse_026 and Warehouse_027 are **`NOT_AVAILABLE`** (`NOT_DOCUMENTED_IN_RELEASE`).
* The formal value of illuminance is strictly **`UNKNOWN`**.
* Missing lux is **never** converted to $0\text{ lux}$, never estimated via heuristic pixel brightness, and never synthesized.
* **Formal Status**: *"Model H formal coverage remains unestablished because the physical lux telemetry required by the illumination-dependent component is not available in the released evaluation package."*

---

## 5. Camera Extrinsics & Pitch Distribution Scope

Across the 11 cameras analyzed in Warehouse_026 and Warehouse_027, the optical-axis depression angles derived from the supplied calibration were within the observed range of **$20.56^\circ$–$35.69^\circ$**.

* **Scope Constraint**: This observation is strictly limited to the two benchmark scenes and must not be generalized to industrial warehouses as a whole.
* **Calibration Documentation**: The dataset provides calibration matrices. The available project evidence does not independently establish the underlying field-survey methodology or measurement uncertainty.

---

## 6. Regulatory Framework Positioning

| Regulatory Standard | Applicability | Formal Compliance Status | Governance Phrasing |
|---|---|---|---|
| **ISO 3691-4:2023** | Relevant safety standard for driverless industrial trucks and their systems | **`NOT_CERTIFIED`** | Relevant engineering safety standard for driverless industrial trucks; project evidence is not certified or compliant without accredited physical field assessment. (ISO/DIS 3691-4 represents the emerging draft revision). |
| **ISO 13849-1:2023** | Relevant methodology for safety-related parts of control systems | **`NOT_CERTIFIED`** | Relevant methodology for safety-related parts of control systems; formal performance-level determination (PL d/e) has not been established for Safety Backfire AI. |
| **ASME V&V 40:2018** | Credibility assessment framework for computational models | **`CREDIBILITY_INFORMED`** | V3.4 governance is informed by the credibility concepts of ASME V&V 40. Project governance is internally aligned with risk-based credibility concepts, not an external conformity certification. |
| **EU AI Act** | Data quality and risk-management principles | **`GOVERNANCE_ALIGNED`** | Project data-governance practices are designed with relevant EU AI Act data-quality and accuracy principles in mind. This is an internal engineering governance statement, not a formal legal conformity determination. |

---

## 7. Conclusions & Directives for Milestone V3.4

1. **Reclassification Complete**: Warehouse_026 and Warehouse_027 are permanently established as real-world test captures.
2. **Execution Integrity Preserved**: The 45,836 detections and 318 tracks stand as valid execution stress-test evidence.
3. **Evidence Completion Mandate**: Milestone V3.4 is formally designated as **`REAL_WORLD_EVIDENCE_COMPLETION`**, focusing squarely on addressing the 10 dimensions identified in the Real-World Evidence Gaps matrix.
