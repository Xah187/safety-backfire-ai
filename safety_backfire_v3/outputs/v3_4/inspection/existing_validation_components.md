# Safety Backfire AI — Existing Validation Components & Gap Analysis

**Document Identifier**: `V3_4-INSP-03-VALIDATION-COMPONENTS`  
**Inspection Date**: 2026-09-28  
**Inspector**: Safety Assurance & Validation Infrastructure Engineer  
**Scope**: In-Depth Review of Verification Architecture and V3.4 Validation Infrastructure Requirements  

---

## 1. Existing Validation Harnesses

The repository contains validation frameworks developed across previous milestones:

### 1.1 V3.2 Validation Framework (`validation/v3_2/`)
* **Perception & Tracking Validators**:
  * `perception_validator.py`: Evaluates detection thresholds, IoU overlaps, and class distribution bounds.
  * `tracking_validator.py`: Analyzes track continuity, fragmentation count, and ID preservation.
* **Geometry & Hazard Validators**:
  * `geometry_validator.py`: Validates homography matrix stability and coordinate transformation limits.
  * `hazard_validator.py` & `ttc_cpa_validator.py`: Evaluates time-to-collision and closest point of approach between mobile agents.
* **Backfire & Causality Validators**:
  * `backfire_validator.py` & `causality_validator.py`: Audits risk inflation decisions against event episodes.

### 1.2 V3.3 Ingestion & Provenance Gates (`validation/v3_3/` & `validation/v3_3_3/`)
* `validate_external_provenance.py`: Enforces SHA-256 integrity of candidate videos, verifies exclusion of `Central 01` footage via 256-bit perceptual hashing, and verifies video stream dimensions.
* `test_run_003_integrity.py` & `test_run_004_integrity.py`: Verifies deterministic execution outputs, parameter immobility, and matrix decomposition fidelity across synthetic benchmarks (`Warehouse_026` and `Warehouse_027`).
* `test_model_h_canonical_conformance.py`: Enforces strict immobility of Model H frozen parameters ($k_0 = 2.40, \beta_d = 0.08, \beta_l = 0.12, \beta_{\text{pitch}} = 0.22$).

---

## 2. Identified Deficiencies in Pre-V3.4 Validation Infrastructure

While the existing codebase provides mathematical and integrity checks for simulation and synthetic benchmarks, several critical structural gaps exist that prevent safety-critical evaluation on physical external facility data:

```
┌─────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┐
│ EXISTING CAPABILITY (V3.3.3)                                │ DEFICIENCY REQUIRING V3.4 INFRASTRUCTURE                     │
├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 1. Evaluates model predictions on synthetic benchmarks.     │ Lacks schemas and validators for independent human           │
│                                                             │ ground-truth bounding boxes, footpoints, and trajectories.   │
├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 2. Illumination treated as synthetic or `NOT_AVAILABLE`.     │ Lacks structured ingestion, calibration verification, and    │
│                                                             │ monotonic timestamp checks for physical lux sensor data.     │
├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 3. Camera extrinsics parsed from virtual CAD nodes.         │ Lacks formal schema for physical camera surveying records    │
│                                                             │ (mounting heights, tilt angles, physical coordinate frames). │
├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 4. No formal event adjudication framework for physical      │ Lacks multi-reviewer, 3-window temporal schema for           │
│    operational interventions.                               │ intervention events (`BACKFIRE`, `NO_BACKFIRE`, `AMBIGUOUS`). │
├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 5. Blind splits implemented on ad-hoc basis.                │ Lacks facility-level blind evaluation protocol that prevents  │
│                                                             │ cross-camera frame leakage while withholding ground truth.   │
├─────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 6. Silent handling of missing values in some scripts.       │ Missing explicit enforcement of `"UNKNOWN"` for nullables;   │
│                                                             │ missing data must fail loudly rather than silently default.   │
└─────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 3. V3.4 Validation Infrastructure Specifications

To resolve these deficiencies, V3.4 introduces:

1. **Deterministic Schema Validation Engine (`scripts/v3_4/validate_acquisition_package.py`)**:
   * Evaluates incoming facility packages against all 6 explicit JSON schemas.
   * Performs 20 mandatory checks spanning SHA-256 hashes, video readability, monotonic timestamps, ID consistency, bounding box coordinate bounds, non-negative physical lux, survey completeness, and temporal window non-overlap.
   * **Strict Failure Semantics**: Fails loudly and unconditionally upon encountering invalid, corrupted, or uncalibrated data. Silent data imputation is strictly forbidden.
2. **Comprehensive Event-Level Quality Control Reporting (`outputs/v3_4/qc/` and `outputs/v3_4/reports/`)**:
   * Generates machine-readable (`.json`) and audit-grade Markdown (`.md`) reports summarizing coverage across all data dimensions without inventing missing numbers.
3. **Facility-Level Blind Split Harness (`scripts/v3_4/create_blind_manifest.py`)**:
   * Guarantees that evaluation code receives strictly unlabelled video streams and calibration data, locking true ground truth behind cryptographic hash manifests until formal adjudication.
4. **Automated Unit & Regression Suite (`tests/v3_4/test_schema_validation.py`)**:
   * Deterministic test suite verifying all positive and negative failure modes, schema edge cases, and frozen parameter protection.
