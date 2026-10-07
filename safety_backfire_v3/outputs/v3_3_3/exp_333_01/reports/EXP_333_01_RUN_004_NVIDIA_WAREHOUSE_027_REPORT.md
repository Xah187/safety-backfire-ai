# EXP_333_01 — RUN_004 NVIDIA WAREHOUSE_027 EXECUTION REPORT

**Experiment**: `EXP_333_01_EXTERNAL_FACILITY`  
**Run ID**: `RUN_004_NVIDIA_WAREHOUSE_027`  
**Dataset**: NVIDIA PhysicalAI-SmartSpaces (`MTMC_Tracking_2026/test/Warehouse_027`)  
**License**: CC-BY-4.0 (NVIDIA Corporation)  
**Execution Timestamp**: 2026-09-28T09:59:50Z  
**Optimization Status**: **NO MODEL OPTIMIZATION, NO RETRAINING, NO THRESHOLD TUNING**  
**Runtime Implementation**: `CONFORMANT_TO_FROZEN_SPECIFICATION`  
**Model H Baseline**: **FROZEN ($k_0 = 2.40, \beta_d = 0.08, \beta_l = 0.12, \beta_{\text{pitch}} = 0.22$)**  
**Model H Formal Status**: `INPUT_INSUFFICIENT` (`MISSING_ILLUMINATION_LUX` only)  
**Perception Metrics Status**: `OBSERVATIONAL_ONLY_NO_GROUND_TRUTH` (`NOT_ESTABLISHED`)  

---

## 1. Executive Summary

This report documents the autonomous execution of **RUN_004** in `EXP_333_01_EXTERNAL_FACILITY` using the 7-camera real-world benchmark **NVIDIA PhysicalAI-SmartSpaces (`Warehouse_027`)**.

RUN_004 validates pipeline scalability, multi-camera geometric projection, and cross-facility distributional robustness across an expanded industrial environment:
* **Massive Scale**: **12,600 total frames** across **7 synchronized 1080p cameras** (1,800 frames per camera, 60.0s each @ 30 FPS) — totaling **420.0 seconds** of multi-view warehouse operations.
* **Observation Density**: Extracted **34,894 detection instances** (3,968 forklifts, 30,926 workers) with a high density of $2.769$ detections per frame.
* **Tracking Topology**: Tracked **237 unique multi-camera trajectories** across 7 independent camera streams.
* **Calibrated Metric Projection**: Detections were projected to the floor plane using the NVIDIA calibration geometry $(P_{:, [0,1,3]})^{-1}$, yielding metric distances from $1.56\text{m}$ to $25.67\text{m}$ (overall mean $6.342\text{m}$).
* **Physical Extrinsic Tilt Decomposition**: Camera pitch angles were extracted as true physical optical-axis depression angles ($20.56^\circ$ to $35.69^\circ$), discarding raw Euler decomposition artifacts. All 7 cameras operate within the degraded shallow pitch regime ($<40^\circ \implies$ pitch penalty $0.22$).
* **Strict Governance Enforcement**: Because physical lux telemetry is not available in the released evaluation package, Model H strictly outputs `INPUT_INSUFFICIENT (MISSING_ILLUMINATION_LUX)` without synthetic substitution. Dual-mode uncertainty (MODE_A base standard and MODE_B proxy inclusion) is reported honestly.

---

## 2. Multi-Run Evolution Matrix

| Run ID | Dataset | Cameras | Frames | Detections | Tracks | Distance Source | Optical Tilt Range | Model H Status |
|---|---|---|---|---|---|---|---|---|
| `RUN_001` (Invalidated) | `0_te11.mp4` | 1 | 173 | 251 | — | Linear proxy | Unmeasured ($0.0^\circ$) | `INVALIDATED_MISMATCH` |
| `RUN_002` (Conformance) | `0_te11.mp4` | 1 | 173 | 251 | — | Model estimate | Unmeasured | `INPUT_INSUFFICIENT` (3 missing) |
| `RUN_003` (WH026) | `Warehouse_026` | 4 | 7,200 | 10,942 | 81 | Calibrated Homography | $24.33^\circ - 31.94^\circ$ | `INPUT_INSUFFICIENT` (Lux only) |
| **`RUN_004` (WH027)** | **`Warehouse_027`** | **7** | **12,600** | **34,894** | **237** | **Calibrated Geometry** | **$20.56^\circ - 35.69^\circ$** | **`INPUT_INSUFFICIENT` (Lux only)** |

---

## 3. Per-Camera Geometry & Detection Breakdown (Warehouse_027)

```
Warehouse_027 Camera Network (7 Synchronized Views):
├── Camera_0000: 10,135 dets | 52 tracks | H=2.86m | Tilt=32.37° | Mean Dist=5.02m (In-ODD: 95.8%)
├── Camera_0001:  4,816 dets | 44 tracks | H=2.52m | Tilt=20.63° | Mean Dist=12.83m (Out-ODD: 77.6% ⚠️)
├── Camera_0002:  2,253 dets | 27 tracks | H=2.71m | Tilt=35.69° | Mean Dist=4.38m (In-ODD: 86.6%)
├── Camera_0003:  1,538 dets |  9 tracks | H=2.57m | Tilt=20.75° | Mean Dist=3.03m (In-ODD: 100.0%)
├── Camera_0004:  1,635 dets | 14 tracks | H=2.56m | Tilt=20.56° | Mean Dist=9.30m (Out-ODD: 54.7% ⚠️)
├── Camera_0005:  5,060 dets | 41 tracks | H=2.71m | Tilt=28.15° | Mean Dist=6.80m (Degraded: 45.5% ⚠️)
└── Camera_0006:  9,457 dets | 50 tracks | H=2.99m | Tilt=33.77° | Mean Dist=4.70m (In-ODD: 94.7%)
```

### Quantitative Camera Summary

| Camera ID | Height ($z$) | Physical Optical Depression | Detections | Forklifts | Workers | Tracks | Mean Dist | $\le 8\text{m}$ (In-ODD) | $8-10\text{m}$ (Degraded) | $>10\text{m}$ (Out-of-ODD) |
|---|---|---|---|---|---|---|---|---|---|---|
| `Camera_0000` | $2.86\text{ m}$ | $32.37^\circ$ | 10,135 | 392 | 9,743 | 52 | $5.02\text{ m}$ | $95.85\%$ | $1.66\%$ | $2.50\%$ |
| `Camera_0001` | $2.52\text{ m}$ | $20.63^\circ$ | 4,816 | 288 | 4,528 | 44 | **$12.83\text{ m}$** | $18.69\%$ | $3.70\%$ | **$77.62\%$** |
| `Camera_0002` | $2.71\text{ m}$ | $35.69^\circ$ | 2,253 | 486 | 1,767 | 27 | $4.38\text{ m}$ | $86.64\%$ | $13.36\%$ | $0.00\%$ |
| `Camera_0003` | $2.57\text{ m}$ | $20.75^\circ$ | 1,538 | 215 | 1,323 | 9 | $3.03\text{ m}$ | $100.00\%$ | $0.00\%$ | $0.00\%$ |
| `Camera_0004` | $2.56\text{ m}$ | $20.56^\circ$ | 1,635 | 402 | 1,233 | 14 | **$9.30\text{ m}$** | $40.24\%$ | $5.02\%$ | **$54.74\%$** |
| `Camera_0005` | $2.71\text{ m}$ | $28.15^\circ$ | 5,060 | 971 | 4,089 | 41 | $6.80\text{ m}$ | $43.77\%$ | **$45.53\%$** | $10.69\%$ |
| `Camera_0006` | $2.99\text{ m}$ | $33.77^\circ$ | 9,457 | 1,214 | 8,243 | 50 | $4.70\text{ m}$ | $94.70\%$ | $2.11\%$ | $3.18\%$ |
| **All Cameras** | **$2.70\text{ m}$** | **$27.42^\circ$** | **34,894** | **3,968** | **30,926** | **237** | **$6.34\text{ m}$** | **$74.32\%$** | **$9.27\%$** | **$16.42\%$** |

---

## 4. ODD & Long-Corridor Deep Challenges

Applying the master canonical ODD boundaries (`outputs/v3_2_1/canonical_odd.json`):
1. **Camera Height Shift**:
   * All 7 cameras are mounted between $2.517\text{m}$ and $2.988\text{m}$ ($< 3.0\text{m}$ boundary), representing an **ODD Height Shift** compared to the nominal $3.5\text{m} - 6.0\text{m}$ specification.
2. **Camera Pitch Shift**:
   * All 7 cameras operate with optical axis depression between $20.56^\circ$ and $35.69^\circ$ ($< 40.0^\circ$ threshold), incurring a constant pitch penalty $\beta_{\text{pitch}} = 0.22$.
3. **Extreme Depth & Long-Corridor Challenges**:
   * **`Camera_0001`**: **$77.62\%$** of detections exceed $10\text{m}$ (out-of-domain for autonomous braking intervention), reaching up to $20.16\text{m}$.
   * **`Camera_0004`**: **$54.74\%$** of detections exceed $10\text{m}$, reaching up to $25.67\text{m}$.
   * **`Camera_0005`**: **$45.53\%$** of detections fall in the $8\text{m} - 10\text{m}$ degraded surveillance advisory zone.

---

## 5. Cross-Scene Distribution Shift Analysis (WH026 vs WH027)

```
                      Warehouse_026 (RUN_003)        Warehouse_027 (RUN_004)
Cameras:              4 cameras                      7 cameras (+75%)
Frames:               7,200 frames                   12,600 frames (+75%)
Duration:             240.0 seconds                  420.0 seconds (+75%)
Detections:           10,942                         34,894 (3.19× increase)
Dets/Frame:           1.52                           2.77 (+82% density)
Forklifts / Persons:  3,983 / 6,959                  3,968 / 30,926
Active Tracks:        81                             237 (2.93× increase)
Tracks / Camera:      20.2                           33.9 (+68% fragmentation)
Mean Distance:        6.92 m                         6.34 m
Mean Optical Tilt:    27.74°                         27.42° (Identical bracket tilt)
In-ODD (<=8m):        71.54%                         74.32%
Degraded (8-10m):     10.71%                          9.27%
Out-of-ODD (>10m):    17.75%                         16.42%
Calibration RMSE:     0.0542 units (1k pts)          0.0925 units (1k pts)
```

### Key Distributional Findings:
1. **Human Traffic Explosion**: Worker detections increased by **$4.44\times$** ($6,959 \to 30,926$), whereas forklift detections remained stable ($3,983 \to 3,968$), indicating a pedestrian-dense sorting and staging warehouse layout in WH027.
2. **Standardized Bracket Pitch**: Despite the different warehouse layouts, the mean optical depression angle ($27.74^\circ$ vs $27.42^\circ$) is virtually identical, demonstrating consistency in industrial ceiling mounting practices.
3. **Multi-Camera Track Fragmentation**: Track count increased from 81 to 237 ($33.9$ tracks/camera vs $20.2$), reflecting increased visual boundary crossings and cross-camera occlusion handoff challenges.

---

## 6. Uncertainty & Model H Dual-Mode Evaluation

Because physical illumination lux remains unmeasured, Model H formally reports `INPUT_INSUFFICIENT (MISSING_ILLUMINATION_LUX)`:

| Evaluation Mode | Definition | Mean $k_{\text{partial}}$ | Min $k_{\text{partial}}$ | Max $k_{\text{partial}}$ | Std $k_{\text{partial}}$ |
|---|---|---|---|---|---|
| **MODE_A (Standard)** | $k_0 + \beta_d \cdot (d-4.0)_+ + \beta_{\text{pitch}} \cdot \mathbb{I}(\text{pitch}<40^\circ)$ | **$2.7844$** | $2.6200$ | $4.3400$ | $0.2798$ |
| **MODE_B (With Proxy)** | $k_0 + \beta_d \cdot (d-4.0)_+ + \beta_{\text{pitch}} \cdot \mathbb{I}(\text{pitch}<40^\circ) + \gamma_{\text{occ}}$ | **$2.8058$** | $2.6200$ | $4.3400$ | $0.2845$ |

* Delta mean: $+0.0214$ (due to $8.2\%$ of detections showing bbox IoU overlap).
* Governance Ruling: MODE_B remains purely informational and cannot be used to claim certified calibration coverage.

---

## 7. Artifact Manifest (RUN_004)

All artifacts are cryptographically hashed and stored in:
`outputs/v3_3_3/exp_333_01/runs/RUN_004_NVIDIA_WAREHOUSE_027/`
* `run_004_manifest.json`
* `canonical_evaluation.json`
* `observation_ledger.json` (34,894 detection records)
* `track_topology.json` (237 tracks)
* `odd_observation_ledger_027.json`
* `camera_extrinsic_convention_audit_027.json`
* `cross_scene_distribution_shift.json`
* `run_004_hash_manifest.json`
* `per_camera/` (Camera_0000 to Camera_0006 summaries)
* `metrics/` (`geometry`, `odd`, `perception`, `tracking`, `uncertainty`)
