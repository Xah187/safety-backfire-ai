# V3.3.3 — RUN_003 EXTERNAL BENCHMARK FORENSIC AUDIT REPORT

**Target Run**: `RUN_003_NVIDIA_WAREHOUSE_026`  
**Audit ID**: `RUN_003_FORENSIC_AUDIT`  
**Dataset Source**: NVIDIA PhysicalAI-SmartSpaces (`MTMC_Tracking_2026/test/Warehouse_026`)  
**Audit Date**: 2026-09-28T09:54:00Z  
**Optimization Status**: **NO MODEL OPTIMIZATION, NO RETRAINING, NO THRESHOLD TUNING**  
**Final Run Classification**: `EXECUTED_EXTERNAL_BENCHMARK_WITH_LIMITATIONS`  

---

## 1. Official Source Verification & Provenance

The provenance authority for this benchmark is the official **NVIDIA PhysicalAI-SmartSpaces** dataset repository hosted on the Hugging Face Hub:
* **Repository Identifier**: `nvidia/PhysicalAI-SmartSpaces`
* **Subset**: `MTMC_Tracking_2026`
* **Primary Scene**: `Warehouse_026` (Real-world test capture, 4 cameras, 1,800 frames/cam)
* **Secondary Scene**: `Warehouse_027` (Real-world test capture, 7 cameras, 1,800 frames/cam)
* **License**: CC-BY-4.0 (NVIDIA Corporation)
* **Official Statement on Real-World Captures**: The overall PhysicalAI-SmartSpaces repository contains predominantly synthetic data. However, the evaluation test scenes `Warehouse_026` and `Warehouse_027` are explicitly designated and provided as **authentic real-world test captures**.
* **Ground Truth Availability**: Official human annotations (bounding boxes, track IDs) are **withheld** by NVIDIA for real-world test scenes to serve as an uncompromised evaluation benchmark.
* **Building Independence**: Classified as `REAL_WORLD_EXTERNAL_DATASET = VERIFIED`. Physical building independence is `SOURCE_SUPPORTED / NOT_DIRECTLY_VERIFIED` because NVIDIA does not publish facility deed or architectural survey documentation.

---

## 2. Calibration Language Correction

In strict adherence to scientific precision, all references equivalent to `SURVEY_GRADE` have been formally expunged from the repository and replaced with:
`NVIDIA_REPORTED_CALIBRATION_REPROJECTION_QUALITY`

### Quantitative Reprojection Metrics (NVIDIA Verified)
* **Correspondence Points**: 1,000 points across the warehouse floor plane
* **Mean Reprojection Error**: $0.0369$ units
* **Reprojection RMSE**: **$0.0542$ units**
* **Median Error**: $0.0240$ units
* **95th Percentile (P95)**: $0.1082$ units
* **Maximum Error**: $0.3630$ units
* **Verdict**: High mathematical reprojection precision as reported by NVIDIA; not certified as an independent physical survey-grade certification.

---

## 3. Camera Extrinsic Convention Audit

A forensic decomposition of the $3 \times 4$ extrinsic matrices $[R \mid t]$ from `calibration.json` revealed critical convention dependencies:

| Camera ID | World Position $C = -R^T t$ (m) | Height (m) | RUN_003 Euler ZYX Pitch | Optical Axis Depression Angle | Tilt from Nadir |
|-----------|---------------------------------|------------|-------------------------|-------------------------------|-----------------|
| `Camera_0000` | $(0.00, 0.00, 3.60)$ | $3.60$ | $56.51^\circ$ | $31.94^\circ$ | $58.06^\circ$ |
| `Camera_0001` | $(-13.69, -2.63, 2.95)$ | $2.95$ | $53.84^\circ$ | $27.45^\circ$ | $62.55^\circ$ |
| `Camera_0002` | $(-7.00, 4.88, 3.41)$ | $3.41$ | $4.42^\circ$ | $27.25^\circ$ | $62.75^\circ$ |
| `Camera_0003` | $(-6.51, -9.10, 3.07)$ | $3.07$ | $1.59^\circ$ | $24.33^\circ$ | $65.67^\circ$ |

### Key Forensic Insight:
* The initial pitch values ($56.51^\circ, 53.84^\circ, 4.42^\circ, 1.59^\circ$) were computed using an Euler ZYX decomposition `atan2(-R[2,0], sqrt(R[2,1]^2 + R[2,2]^2))`.
* In physical reality, all four cameras are ceiling-mounted at $2.95\text{m} - 3.60\text{m}$ pointing downward into warehouse aisles with an optical axis depression angle of **$24.33^\circ$ to $31.94^\circ$** below horizontal.
* Under the optical axis physical depression angle, all four cameras are within the degraded ODD tilt range ($20^\circ - 35^\circ$), rather than two being $>55^\circ$ and two being $<5^\circ$.
* Status: **`VERIFIED / CONVENTION_REVIEW_REQUIRED`**.

---

## 4. Model H Input Provenance & Occlusion Circularity

### 4.1 Input Classification
* **Distance ($d$)**: `DATASET_PROVIDED / DERIVED_FROM_CALIBRATION` (Homography ground-plane projection; not physically surveyed ground truth).
* **Pitch ($\text{pitch}$)**: `DATASET_PROVIDED / DERIVED_FROM_EXTRINSIC` (Subject to Euler vs optical axis convention review).
* **Illumination ($L$)**: **`NOT_AVAILABLE`** (Physical lux meter log absent). Prohibited substitutions (pixel mean, exposure, guessed lux) strictly enforced.
* **Occlusion ($\text{occ}$)**: **`MODEL_DERIVED_PROXY`** (Derived from YOLO predicted bbox IoU; strictly prohibited from being termed ground truth).

### 4.2 Occlusion Circularity Evaluation (Mode A vs Mode B)
The pipeline presents a potential circularity:
$$\text{YOLO Bboxes} \longrightarrow \text{IoU Matrix} \longrightarrow \text{Occlusion State} \longrightarrow \gamma_{\text{occ}} \longrightarrow k_H$$

To eliminate circularity bias, two separate modes were evaluated across all 10,942 observations:

| Metric | MODE_A (No Occlusion Contribution, $\gamma_{\text{occ}} = 0$) | MODE_B (With Predicted Occlusion Proxy) | Delta (B - A) |
|--------|---------------------------------------------------------------|-----------------------------------------|---------------|
| **Observations** | 10,942 | 10,942 | 0 |
| **Mean $k_{\text{partial}}$** | **$2.7699$** | **$2.7906$** | $+0.0208$ |
| **Std $k_{\text{partial}}$** | $0.2957$ | $0.2999$ | $+0.0042$ |
| **Min $k_{\text{partial}}$** | $2.4000$ | $2.4000$ | $0.0000$ |
| **Max $k_{\text{partial}}$** | $4.1126$ | $4.1126$ | $0.0000$ |

* Observations with occlusion $> 0$: $886$ instances ($8.10\%$).
* **Governance Ruling**: **Mode B is strictly prohibited from asserting formal calibration coverage.** Mode A constitutes the verified lower-bound partial uncertainty record.

---

## 5. ODD Evaluation & Range Reconciliation

Applying the master canonical ODD specification (`safety_backfire_v3/outputs/v3_2_1/canonical_odd.json`):

| ODD Dimension | Specification Boundary | Warehouse_026 Condition | Dimension Status |
|---------------|------------------------|-------------------------|------------------|
| **Camera Height** | $3.5\text{m} - 6.0\text{m}$ (Nominal) | $2.95\text{m}, 3.07\text{m}, 3.41\text{m}, 3.60\text{m}$ | **`ODD_SHIFT`** |
| **Pitch Angle** | $35^\circ - 55^\circ$ (Nominal) | Optical depression: $24.3^\circ - 31.9^\circ$ | **`ODD_SHIFT`** |
| **Distance Range** | Certified: $\le 8.0\text{m}$ | $71.54\% \le 8\text{m}$; $10.71\%$ $8-10\text{m}$; $17.75\% > 10\text{m}$ | **`ODD_SHIFT`** |
| **Floor Geometry** | Slope $\le 1.5^\circ$ | Level industrial concrete floor | **`IN_ODD`** |
| **Illumination** | $150 - 1200\text{ lux}$ | Physical lux logs absent | **`UNKNOWN`** |
| **Entity Speed** | $\le 4.5\text{m/s}$ ($16.2\text{km/h}$) | Warehouse forklifts and pedestrians | **`IN_ODD`** |
| **Stream Latency** | $\le 50.0\text{ms}$ | 30 FPS video streaming ($33.3\text{ms}$ frame interval) | **`IN_ODD`** |
| **Facility Identity** | Building deed / physical audit | Real-world warehouse capture (name unpublished) | **`UNKNOWN`** |
| **Uncertainty Width** | Complete certified Model H score | Formally `INPUT_INSUFFICIENT` | **`UNKNOWN`** |

### Per-Camera Distance Breakdown
* `Camera_0000`: Mean $4.56\text{m}$ | $\le 8\text{m}$: $91.3\%$ | $8-10\text{m}$: $6.6\%$ | $>10\text{m}$: $2.0\%$
* `Camera_0001`: Mean $8.42\text{m}$ | $\le 8\text{m}$: $55.8\%$ | $8-10\text{m}$: $41.6\%$ | $>10\text{m}$: $2.6\%$
* `Camera_0002`: Mean $9.59\text{m}$ | $\le 8\text{m}$: $41.5\%$ | $8-10\text{m}$: $6.5\%$ | $>10\text{m}$: $52.0\%$ (Deep transit aisle)
* `Camera_0003`: Mean $5.33\text{m}$ | $\le 8\text{m}$: $97.9\%$ | $8-10\text{m}$: $0.6\%$ | $>10\text{m}$: $1.6\%$

---

## 6. External Evidence Hierarchy & Claim Matrix

Every claim is attributed to its formal evidence hierarchy level:
* **LEVEL 1**: Official NVIDIA source metadata
* **LEVEL 2**: Raw video media
* **LEVEL 3**: NVIDIA calibration data
* **LEVEL 4**: Model-derived observations
* **LEVEL 5**: Independent human ground truth

| Claim | Evidence Source | Evidence Level | Forensic Status |
|---|---|---|---|
| Warehouse_026 is real-world | NVIDIA source card | LEVEL 1 | **`VERIFIED`** |
| 4 independent cameras | NVIDIA source & raw files | LEVEL 1 / 2 | **`VERIFIED`** |
| 60s / 1800 frames per camera | Video container headers | LEVEL 1 / 2 | **`VERIFIED`** |
| Calibration exists | `calibration.json` package | LEVEL 1 / 3 | **`VERIFIED`** |
| Metric distance available | Homography ground-plane projection | LEVEL 3 | **`VERIFIED`** |
| Camera pitch available | Extrinsic matrix decomposition | LEVEL 3 | **`VERIFY_CONVENTION`** |
| Ambient Lux available | — | LEVEL 5 (Absent) | **`NOT_AVAILABLE`** |
| Occlusion Ground Truth | — | LEVEL 5 (Absent) | **`NOT_AVAILABLE`** |
| Perception Ground Truth | — | LEVEL 5 (Absent) | **`NOT_AVAILABLE`** |
| Perception F1 Score | — | LEVEL 5 (Absent) | **`NOT_ESTABLISHED`** |
| Model H Certified Coverage | — | LEVEL 5 (Absent) | **`NOT_ESTABLISHED`** |
| Cross-Warehouse Generalization | — | LEVEL 5 (Absent) | **`NOT_ESTABLISHED`** |

---

## 7. Preparation for Warehouse_027 (RUN_004)

`data/external_facility_02/` has been prepared with full directory isolation:
* `data/external_facility_02/raw/Warehouse_027/` (184 MB downloaded, 7 cameras, 1,800 frames each = 12,600 frames total).
* `data/external_facility_02/metadata/`
* `data/external_facility_02/calibration/`
* `data/external_facility_02/manifests/`

RUN_004 will execute as a strictly distinct, independent run with zero parameter adaptation.
