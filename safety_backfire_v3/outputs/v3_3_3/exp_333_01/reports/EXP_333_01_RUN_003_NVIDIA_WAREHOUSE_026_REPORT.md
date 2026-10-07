# EXP_333_01 — RUN_003 NVIDIA WAREHOUSE_026 EXECUTION REPORT

**Experiment**: `EXP_333_01_EXTERNAL_FACILITY`  
**Run ID**: `RUN_003_NVIDIA_WAREHOUSE_026`  
**Dataset**: NVIDIA PhysicalAI-SmartSpaces (`MTMC_Tracking_2026/test/Warehouse_026`)  
**License**: CC-BY-4.0 (NVIDIA Corporation)  
**Execution Timestamp**: 2026-09-28T08:39:58Z  
**Optimization Status**: **NO MODEL OPTIMIZATION, NO RETRAINING, NO THRESHOLD TUNING**  
**Runtime Implementation**: `CONFORMANT_TO_FROZEN_SPECIFICATION`  
**Model H Formal Status**: `INPUT_INSUFFICIENT` (`MISSING_ILLUMINATION_LUX` only)  
**Inputs Resolved vs RUN_002**: $3 / 4$ physical inputs resolved from calibration data  

---

## 1. Executive Summary

This report documents the execution of **RUN_003** in `EXP_333_01_EXTERNAL_FACILITY` using authentic, multi-camera warehouse recordings from the **NVIDIA PhysicalAI-SmartSpaces** benchmark (`Warehouse_026`).

RUN_003 represents a monumental expansion in scientific evidence volume and calibration fidelity compared to prior single-camera field observations:
* **Data Volume**: Expanded from 173 frames (1 camera, 6.98s) to **7,200 frames across 4 independent cameras** (60.0s each @ 30 FPS) — a **41.6× expansion**.
* **Detections & Tracks**: Processed **10,942 detection instances** (3,983 forklifts, 6,959 workers) and established **81 distinct tracks** (24 forklifts, 57 workers).
* **Calibration & Geometry**: Ground-plane metric distance was computed from NVIDIA-provided **calibrated homography matrices** ($\text{RMSE} = 0.0542$ units), replacing model estimates.
* **Camera Extrinsics**: Physical camera pitch angles were extracted directly from $3 \times 4$ extrinsic rotation matrices, eliminating unmeasured pitch ambiguity.
* **Occlusion Modeling**: Derived from per-frame spatial bounding box IoU interactions ($10,056$ none, $635$ partial, $251$ heavy).
* **Governance Compliance**: Because physical lux meter logs are absent from the NVIDIA dataset, Model H strictly reports `INPUT_INSUFFICIENT (MISSING_ILLUMINATION_LUX)`. **Zero default values or synthetic proxies were substituted**, preserving strict scientific integrity under the frozen $k_0 = 2.40$ baseline.

---

## 2. Multi-Run Forensic Isolation

All three external facility runs are independently preserved in the outputs directory:

| Run ID | Dataset | Cameras | Frames | Detections | Distance Source | Pitch Source | Lux Source | Model H Status |
|--------|---------|---------|--------|------------|-----------------|--------------|------------|----------------|
| `RUN_001_INVALIDATED` | `0_te11.mp4` | 1 | 173 | 251 | Linear proxy | Zeroed ($0.0^\circ$) | Proxy ($0.50$) | `INVALIDATED_MISMATCH` |
| `RUN_002_CONFORMANCE` | `0_te11.mp4` | 1 | 173 | 251 | Model estimate | Unavailable | Unavailable | `INPUT_INSUFFICIENT` (3 missing) |
| `RUN_003_NVIDIA_WH026` | `Warehouse_026` | **4** | **7,200** | **10,942** | **Calibrated Homography** | **Extrinsic Matrix** | Unavailable | **`INPUT_INSUFFICIENT` (lux only)** |

* `RUN_001` remains preserved as an invalidated historical record.
* `RUN_002` remains preserved as the canonical conformance baseline on `0_te11.mp4`.
* `RUN_003` establishes real multi-camera external warehouse benchmark execution.

---

## 3. Physical Asset & Provenance Inventory

### 3.1 Synchronized Video Inventory

| Stream | Resolution | FPS | Frames | Duration | File Size | SHA-256 Digest |
|--------|------------|-----|--------|----------|-----------|----------------|
| `Camera_0000.mp4` | 1920×1080 | 30.0 | 1,800 | 60.0s | 18.88 MB | `83ed232a58b5a034988770c862bc343ea1496a79ce34fbe9932025e1df1fbceb` |
| `Camera_0001.mp4` | 1920×1080 | 30.0 | 1,800 | 60.0s | 26.35 MB | `dd37e801b6a7a02213da9c2794df0537f0709f3e498c8c6913c1c9535eb99dd8` |
| `Camera_0002.mp4` | 1920×1080 | 30.0 | 1,800 | 60.0s | 36.91 MB | `abe39e20560a581e18ec0e72fc10cba7ff0f09a9dbd4ff51a44c5b3641b5b82a` |
| `Camera_0003.mp4` | 1920×1080 | 30.0 | 1,800 | 60.0s | 18.69 MB | `9051adb9ffb0a887cf4878a2e1d743a1314aa78dbfb8b3558f3ee824c965e640` |
| **Total** | — | — | **7,200** | **240.0s** | **100.83 MB** | Verified Hub Ingestion |

### 3.2 Calibration Precision & Reprojection Fidelity

Calibration data was ingested from `calibration.json` accompanied by NVIDIA's reprojection error verification:
* **Calibration Type**: Full Intrinsic + Extrinsic ($3 \times 4$) + Ground-Plane Homography ($3 \times 3$)
* **Evaluated Points**: 1,000 ground-truth correspondences across the warehouse floor
* **Mean Reprojection Error**: $0.0369$ units
* **Reprojection RMSE**: **$0.0542$ units**
* **Median Error**: $0.0240$ units
* **95th Percentile**: $0.1082$ units
* **Maximum Error**: $0.3630$ units
* **Verdict**: `NVIDIA_REPORTED_CALIBRATION_REPROJECTION_QUALITY`

---

## 4. Per-Camera Physical Geometry & Detection Breakdown

```
        Camera_0000 (Elevated High-Angle: 56.51°)
        ├── 1,800 frames | 3,329 detections (2,008 forklifts, 1,321 workers)
        ├── World Pos: (0.19m, 3.05m, 1.91m) | Pitch Penalty: 0.00
        └── Mean Distance: 5.08m (Distance Term Mean: 0.0865)

        Camera_0001 (Aisle Down-View: 53.84°)
        ├── 1,800 frames | 1,718 detections (157 forklifts, 1,561 workers)
        ├── World Pos: (3.22m, -3.69m, 13.38m) | Pitch Penalty: 0.00
        └── Mean Distance: 8.44m (Distance Term Mean: 0.3556)

        Camera_0002 (Wide Transit Aisle: 4.42°)
        ├── 1,800 frames | 3,447 detections (1,782 forklifts, 1,665 workers)
        ├── World Pos: (-6.52m, 0.81m, 6.43m) | Pitch Penalty: 0.22 (Pitch < 40°)
        └── Mean Distance: 9.59m (Distance Term Mean: 0.4473)

        Camera_0003 (Packaging & Sorting Area: 1.59°)
        ├── 1,800 frames | 2,448 detections (36 forklifts, 2,412 workers)
        ├── World Pos: (6.79m, -0.88m, 9.37m) | Pitch Penalty: 0.22 (Pitch < 40°)
        └── Mean Distance: 5.58m (Distance Term Mean: 0.1265)
```

### Summary Table

| Camera ID | Pitch Angle | Pitch Penalty ($\beta_{\text{pitch}} \cdot \mathbb{I}$) | Detections | Forklifts | Workers | Tracks | Mean Distance | Mean Luminance |
|-----------|-------------|----------------------------------------------------------|------------|-----------|---------|--------|---------------|----------------|
| `Camera_0000` | $56.51^\circ$ | $0.00$ | 3,329 | 2,008 | 1,321 | 20 | 5.08 m | 94.74 |
| `Camera_0001` | $53.84^\circ$ | $0.00$ | 1,718 | 157 | 1,561 | 16 | 8.44 m | 77.84 |
| `Camera_0002` | $4.42^\circ$ | $0.22$ | 3,447 | 1,782 | 1,665 | 24 | 9.59 m | 103.10 |
| `Camera_0003` | $1.59^\circ$ | $0.22$ | 2,448 | 36 | 2,412 | 21 | 5.58 m | 101.99 |
| **All Cameras** | — | — | **10,942** | **3,983** | **6,959** | **81** | **6.92 m** | **94.42** |

---

## 5. Model H Input Resolution & Uncertainty Analysis

### 5.1 Canonical Formula & Parameter Lock

The frozen canonical specification is enforced:

$$k_H(d, L, \text{occ}, \text{pitch}) = k_0 + \beta_d \cdot \max(0, d - 4.0) + \beta_L \cdot \frac{\max(0, 300 - L)}{100} + \beta_{\text{pitch}} \cdot \mathbb{I}(\text{pitch} < 40^\circ) + \gamma_{\text{occ}}[\text{occ}]$$

* $k_0 = 2.40$
* $\beta_d = 0.08$
* $\beta_L = 0.12$
* $\beta_{\text{pitch}} = 0.22$
* $\text{pitch\_threshold\_deg} = 40.0^\circ$
* $\gamma_{\text{occ}} = \{\text{NONE}: 0.00, \text{PARTIAL}: 0.20, \text{HEAVY}: 0.40\}$

### 5.2 Input Resolution Matrix

| Parameter | Required Input | RUN_002 Status | RUN_003 Status | Data Source |
|-----------|----------------|----------------|----------------|-------------|
| $d$ | Ground metric distance | `MODEL_ESTIMATE` | **`FROM_CALIBRATED_HOMOGRAPHY`** | Homography projection ($C = -R^T t$) |
| $\text{pitch}$ | Camera tilt angle | `NOT_AVAILABLE` | **`FROM_CALIBRATED_EXTRINSIC`** | Inclinometer extrinsic rotation matrix |
| $\text{occ}$ | Target occlusion | `NOT_AVAILABLE` | **`DERIVED_FROM_BBOX_IOU`** | Inter-target spatial bounding box overlap |
| $L$ | Ambient illuminance | `NOT_AVAILABLE` | **`NOT_AVAILABLE`** | Physical lux meter log absent |

### 5.3 Partial Term Computation & Conservative Bounds

Because $L$ is absent, formal evaluation remains `INPUT_INSUFFICIENT`. However, all available terms were rigorously computed:
* **Distance Term ($\beta_d \cdot \max(0, d - 4.0)$)**:
  * Count: $10,942$
  * Mean: $0.2513$
  * Min: $0.0000$ (for all $d \le 4.0\text{ m}$)
  * Max: $1.7126$ (at $d = 25.41\text{ m}$)
* **Pitch Term ($\beta_{\text{pitch}} \cdot \mathbb{I}(\text{pitch} < 40^\circ)$)**:
  * Camera_0000 & Camera_0001: $0.00$ ($> 40^\circ$)
  * Camera_0002 & Camera_0003: $0.22$ ($< 40^\circ$)
* **Occlusion Distribution**:
  * NONE: $10,056$ ($91.9\%$) $\rightarrow \gamma_{\text{occ}} = 0.00$
  * PARTIAL: $635$ ($5.8\%$) $\rightarrow \gamma_{\text{occ}} = 0.20$
  * HEAVY: $251$ ($2.3\%$) $\rightarrow \gamma_{\text{occ}} = 0.40$
* **Theoretical Worst-Case Illumination Bound**:
  * If $L = 0\text{ lux}$ (complete darkness): Penalty = $0.12 \times \frac{300}{100} = 0.36$.
  * If $L \ge 300\text{ lux}$ (standard warehouse illumination): Penalty = $0.00$.
  * Governance Note: This theoretical bound is reported strictly for risk quantification; it is **NOT** evaluated into the canonical ledger as a synthetic value.

---

## 6. ODD & Perception Governance Audit

1. **Perception Metrics**:
   * Ground truth annotations (bounding boxes) are not published in the test split of Warehouse_026.
   * Under strict governance rules, **Perception F1, Precision, and Recall are correctly marked as `NOT_ESTABLISHED`**.
   * Forklift mean detection confidence: $0.5874$ (range: $0.2502$ to $0.8535$).
   * Person mean detection confidence: $0.7130$ (range: $0.2500$ to $0.9425$).
2. **Tracking Metrics**:
   * Multi-target multi-camera topology is descriptive.
   * IDF1 and MOTA are `NOT_ESTABLISHED` due to lack of ground truth.
3. **ODD Characterization**:
   * Camera pitch: **Characterized** (extrinsic matrices).
   * Metric distance: **Characterized** (calibrated homography).
   * Illumination: **Partially characterized** (pixel luminance mean $94.42$, but no calibrated lux meter).

---

## 7. Cryptographic Sealed Artifacts

All run outputs are sealed with SHA-256 digests in `run_003_hash_manifest.json`:

```
outputs/v3_3_3/exp_333_01/runs/RUN_003_NVIDIA_WAREHOUSE_026/
├── canonical_evaluation.json
├── observation_ledger.json (10,942 records)
├── track_topology.json (81 tracks)
├── run_manifest.json
├── run_003_hash_manifest.json
├── per_camera/
│   ├── Camera_0000_summary.json
│   ├── Camera_0001_summary.json
│   ├── Camera_0002_summary.json
│   └── Camera_0003_summary.json
└── metrics/
    ├── geometry_metrics.json
    ├── odd_metrics.json
    ├── perception_metrics.json
    ├── tracking_metrics.json
    └── uncertainty_metrics.json
```

---

## 8. Final Conclusion & Next Steps

RUN_003 successfully resolves **3 of the 4 blocking physical inputs** for Model H and expands empirical validation volume by **41.6×** over authentic multi-camera warehouse operations.

Strict scientific boundaries remain enforced:
* Model H evaluation remains `INPUT_INSUFFICIENT` due strictly to missing lux logs.
* No default substitution was permitted.
* Baseline $k_0 = 2.40$ remains intact with zero drift.
