# Safety Backfire AI — Repository Inventory (V3.4 Inspection)

**Document Identifier**: `V3_4-INSP-01-REPO-INVENTORY`  
**Inspection Date**: 2026-09-28  
**Inspector**: Safety Assurance & Validation Infrastructure Engineer  
**Scope**: Safety Backfire AI Repository Pre-V3.4 Infrastructure Audit  

---

## 1. Repository Structure & Lineage

The repository exhibits a structured, multi-version evolutionary architecture representing progressive hardening of the Safety Backfire detection and risk-inflation framework:

* **Core Version Packages**:
  * `safety_backfire_v02` through `safety_backfire_v10`: Early architectural prototypes and initial risk-inflation formulas.
  * `safety_backfire_v2`, `safety_backfire_v3`: Production iterations establishing the base risk multiplier framework.
  * `safety_backfire_v3_3`, `safety_backfire_v3_3_1`, `safety_backfire_v3_3_2`: Introduction of ODD enforcement, refactored uncertainty estimation, and formal refusal/distribution shift gating.
  * `safety_backfire_v3_3_3`: Benchmark conformance testing across multi-camera setups, camera pitch decomposition, and forensic reporting.
* **Workspace Directories**:
  * `data/`: Contains primary external facility assets:
    * `data/external_facility/raw/Warehouse_026/`: 4-camera synthetic benchmark sequence from `nvidia/PhysicalAI-SmartSpaces`.
    * `data/external_facility_02/raw/Warehouse_027/`: 7-camera synthetic benchmark sequence.
  * `outputs/` (symlink to `safety_backfire_v3/outputs`): Historical milestone records, frozen schemas, baseline manifests, and experiment ledgers (`v3_0_5`, `v3_1_frozen`, `v3_2_1`, `v3_3_3`).
  * `validation/` (symlink to `safety_backfire_v3/validation`): Multi-version verification suites spanning `v3_0` through `v3_3_3`.
  * `reports/`: High-level milestone summaries and reconciliation reports.
  * `scripts/`: Operational tools and pipeline runners.

---

## 2. Python Environment & Dependency Inventory

Inspection of the active workspace virtual environment (`.venv/`):

* **Python Runtime**: `Python 3.9.6` (Darwin / macOS Apple Silicon arm64)
* **Core Computational Packages**:
  * `torch`: `2.8.0` (with Apple Metal Performance Shaders - MPS support)
  * `torchvision`: `0.23.0`
  * `ultralytics`: `8.4.150` (YOLOv8 / YOLO26 inference)
  * `numpy`: `1.26.4`
  * `pandas`: `2.3.3`
  * `polars`: `1.36.1`
  * `scipy / lap`: `lap 0.5.13` (Linear Assignment Problem solver for ByteTrack)
  * `opencv-python`: `4.11.0.86`
  * `PyYAML`: `6.0.3`
  * `rich`: `15.0.0`
* **Test & Validation Harness**:
  * Executed using Python standard library `unittest` and custom verification drivers via `.venv/bin/python`.

---

## 3. Existing Model H Implementation (V3.3.3)

* **Primary Implementation**: `safety_backfire_v3_3_3/uncertainty/model_h.py`
* **Lineage & Authority Manifest**: `outputs/v3_3_3/reconciliation/model_h_lineage.json`
* **Canonical Mathematical Formula**:
  $$k_H(d, L, \text{occ}, \text{pitch}) = k_0 + \beta_d \cdot \max(0.0, d - 4.0) + \beta_L \cdot \frac{\max(0.0, 300.0 - L)}{100.0} + \beta_{\text{pitch}} \cdot \mathbb{I}(\text{pitch} < 40.0^\circ) + \gamma_{\text{occ}}[\text{occ}]$$
* **Canonical Frozen Parameters**:
  * $k_0 = 2.40$ (Base risk buffer multiplier)
  * $\beta_d = 0.08$ (Distance slope penalty per meter beyond 4.0 m)
  * $\beta_l = 0.12$ (Illumination slope penalty per 100 lux below 300.0 lux)
  * $\beta_{\text{pitch}} = 0.22$ (Camera optical tilt penalty for depression $< 40.0^\circ$)
  * $\text{pitch\_threshold\_deg} = 40.0^\circ$
  * $\gamma_{\text{occ}} = \{\text{"NONE"}: 0.00, \text{"PARTIAL"}: 0.20, \text{"HEAVY"}: 0.40\}$
* **Governance Status**: **ABSOLUTELY FROZEN**. Protected under hash verification manifests with zero permissible runtime drift.

---

## 4. Existing Dataset Ingestion & Processing

* **Run 003 Execution**: `safety_backfire_v3_3_3/experiments/execute_run_003_nvidia_warehouse.py`
  * Ingests 4 cameras from `Warehouse_026` (7,200 frames @ 30 FPS).
  * Parses JSON sensor calibration (extrinsics $3 \times 4$, intrinsics $3 \times 3$).
  * Derives camera ground position $C_{xy} = (-R^T t)_{xy}$ and ground-plane homography $H_{\text{img}\to\text{ground}} = (P_{:, [0,1,3]})^{-1}$.
* **Run 004 Execution**: `safety_backfire_v3_3_3/experiments/execute_run_004_nvidia_warehouse_027.py`
  * Ingests 7 cameras from `Warehouse_027` (12,600 frames @ 30 FPS).
  * Implements dynamic homography projection and metric distance calculation from bounding box footpoints.
  * Decomposes optical axis depression angle $\theta = -\arcsin(v_{\text{opt}}[2])$ where $v_{\text{opt}} = R^T [0, 0, 1]^T$.

---

## 5. Existing Audit, Hash & Manifest Infrastructure

* **Provenance Validation**: `validation/v3_3_3/validate_external_provenance.py`
  * Enforces SHA-256 digest validation of all video assets.
  * Implements 256-bit perceptual block mean hashing (`compute_frame_hash`) to prevent data contamination from historical facilities (`Central 01`).
* **Hash Manifests**:
  * `outputs/v3_3_3/baseline/v3_3_2_source_hash_manifest.json` (seals 39 baseline code files).
  * `outputs/v3_3_3/exp_333_01/runs/RUN_003_NVIDIA_WAREHOUSE_026/run_003_hash_manifest.json`.
  * `outputs/v3_3_3/exp_333_01/runs/RUN_004_NVIDIA_WAREHOUSE_027/run_004_hash_manifest.json`.

---

## 6. Inventory Summary & Pre-V3.4 Boundary

All existing V3.3.3 code, runs, and reports remain immutable. V3.4 introduces formal validation infrastructure for **authenticated physical external facility data**, requiring explicit data schemas, acquisition manifests, quality control validators, and blind-split protocols.
