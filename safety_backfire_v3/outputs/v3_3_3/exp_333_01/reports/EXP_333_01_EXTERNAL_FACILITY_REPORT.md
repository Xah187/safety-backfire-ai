# EXP_333_01 EXTERNAL FACILITY GENERALIZATION GATE REPORT
## Forensic Evaluation, Physical Independence Audit, and Generalization Gate

**Date**: 2026-09-25  
**Experiment Identifier**: `EXP_333_01_EXTERNAL_FACILITY`  
**Preregistered Primary Metric**: $\text{External\_Facility\_Perception\_F1} \ge 85.00\%$  
**Lead Roles**: Lead Computer Vision Validation Engineer, Statistical Auditor, Uncertainty Quantification Researcher, Safety Policy Engineer, Release Integrity Engineer  
**Baseline Status**: `V3.3.2_FINAL_RECONCILED` (Zero hash drift across 39 protected artifacts)  
**Experiment Status**: `NOT_ESTABLISHED` (Held pending authenticated physical external facility data)  
**Next Step**: `HOLD` (Do not execute EXP_333_02 until independent external data is captured)  

---

## 1. Executive Summary

`EXP_333_01_EXTERNAL_FACILITY` was preregistered as the primary generalization gate for V3.3.3 of Safety Backfire AI. The objective is to determine whether the perception, tracking, geometry, uncertainty, hazard, event, and policy pipeline generalizes to a physically independent warehouse without parameter re-tuning.

Before evaluation, the **Hard Baseline Lock** was verified: V3.3.2 remains frozen as `V3.3.2_FINAL_RECONCILED` with zero hash drift, and Model H formulation ($k_0 = 2.40, \beta_d = 0.08, \beta_L = 0.12, \beta_{\text{pitch}} = 0.22, \gamma_{\text{occ}}$) remains unchanged.

A rigorous data provenance and independence audit was conducted against the physical footage available on disk. The audit established that **no authenticated physical video footage from an external warehouse facility currently resides on disk**. All available local video assets (`test.mp4`, `test2.mp4`, and candidate files) originate from `FACILITY_CENTRAL_01` (Door 4.1 CCTV). In accordance with Section 2 governance rules, physical independence cannot be fabricated or replaced by synthetic transformations. Consequently:
$$\mathbf{EXTERNAL\_FACILITY\_INDEPENDENCE = NOT\_ESTABLISHED}$$
$$\mathbf{V3.3.3\ EXP\_333\_01\ STATUS = NOT\_ESTABLISHED}$$

The zero-adaptation evaluation harness, blind quarantine manifests, metric registries, and red-team stress suites have been constructed and cryptographically locked. Empirical model evaluation is held pending physical site data acquisition.

---

## 2. Experiment Objective

The primary scientific objective of `EXP_333_01` is a **zero-adaptation transfer test**:
$$\text{V3.3.2\_FROZEN\_MODEL} \longrightarrow \text{EXTERNAL\_FACILITY} \longrightarrow \text{ZERO\_PARAMETER\_ADAPTATION} \longrightarrow \text{VALIDATION}$$

The experiment directly evaluates the hypothesis:
$$\mathcal{H}_0: F1_{\text{external}} < 0.8500 \quad \text{vs.} \quad \mathcal{H}_1: F1_{\text{external}} \ge 0.8500$$
The $85.00\%$ perception F1 threshold serves as a necessary go/no-go gate for cross-warehouse generalization claims.

---

## 3. Facility Independence

In accordance with Section 2, an external facility must satisfy 9 physical criteria:
1. **Different Physical Building**: Target site is designated `FACILITY_E_COLD_STORAGE` (physically separate from `FACILITY_CENTRAL_01`). *Status: NOT ESTABLISHED on disk.*
2. **Different Camera Hardware**: External site utilizes distinct high-mount IP cameras. *Status: NOT ESTABLISHED on disk.*
3. **Independent Mounting Geometry**: Ceiling heights $> 8.0\,\text{m}$ and pitch angles $< 40^\circ$. *Status: NOT ESTABLISHED on disk.*
4. **Independent Lighting Environment**: High-bay LED with cold-storage vapor condensation. *Status: NOT ESTABLISHED on disk.*
5. **Independent Acquisition Session**: Completely separate calendar capture. *Status: NOT ESTABLISHED on disk.*
6. **Independent Raw-Video Provenance**: Authenticated RTSP/MP4 stream with verifiable camera hardware metadata. *Status: NOT ESTABLISHED on disk.*
7. **Zero Frame Overlap with V3.3.x**: No temporal or spatial overlap with existing corpora. *Status: NOT ESTABLISHED on disk.*
8. **Zero Tuning on Evaluation Footage**: Strictly enforced by blind lock protocol. *Status: VERIFIED.*
9. **No Synthetic Transformations as Substitute**: Strictly enforced; synthetic distortion of Central 01 is rejected. *Status: VERIFIED.*

**Audit Result**: Because criteria 1–7 cannot be confirmed from local raw media, physical independence is formally marked:
$$\mathbf{EXTERNAL\_FACILITY\_INDEPENDENCE = NOT\_ESTABLISHED}$$

---

## 4. Dataset Provenance

Documented in `outputs/v3_3_3/exp_333_01/provenance/`:
- **External Facility Manifest** (`external_facility_manifest.json`): Facility ID `FACILITY_E_COLD_STORAGE_PENDING`; raw video available = `false`; frame count = $0$; duration = $0.0\,\text{s}$.
- **Camera Manifest** (`camera_manifest.json`): 4 candidate camera viewports specified (`CAM_EXT_01` through `CAM_EXT_04`), all currently marked `NOT_AVAILABLE`.
- **Acquisition Manifest** (`acquisition_manifest.json`): Ingested files = 0; sensor logs (lux, fiducials) = `false`.
- **Integrity Hash Manifest** (`integrity_hash_manifest.json`): Verified by `DatasetProvenanceGate_V3.3`. Disallowed status `UNAVAILABLE` detected; dataset rejected from blind execution.

---

## 5. Camera Configuration

Planned optical specifications for `FACILITY_E`:
- `CAM_EXT_01` (Inbound Staging): $1920 \times 1080$, $30\,\text{fps}$, mounting height $7.2\,\text{m}$, nominal pitch $34^\circ$.
- `CAM_EXT_02` (Main Aisle Crossing): $1920 \times 1080$, $30\,\text{fps}$, mounting height $8.5\,\text{m}$, nominal pitch $31^\circ$.
- `CAM_EXT_03` (Cold Storage Buffer): $1920 \times 1080$, $30\,\text{fps}$, mounting height $6.8\,\text{m}$, nominal pitch $42^\circ$.
- `CAM_EXT_04` (Outbound Dock): $1920 \times 1080$, $30\,\text{fps}$, mounting height $7.5\,\text{m}$, nominal pitch $38^\circ$.

All camera parameters remain `NOT_AVAILABLE` until physical sensor ingestion.

---

## 6. Dataset Split

Documented in `outputs/v3_3_3/exp_333_01/splits/split_manifest.json`:
- **`EXTERNAL_CALIBRATION`** ($20\%$): Quarantined for potential post-evaluation adaptation studies. Inaccessible during zero-adaptation test.
- **`EXTERNAL_VALIDATION`** ($40\%$): Designated target for primary zero-adaptation out-of-sample evaluation.
- **`EXTERNAL_BLIND`** ($40\%$): Quarantined and cryptographically locked.

### Blind Quarantine Lock
- **Blind Manifest** (`blind_manifest.json`): `BLIND_LOCKED = TRUE`.
- **Blind Hash** (`blind_hash.json`): `LOCKED_PRE_EVALUATION`.
- Prohibitions Enforced: Zero threshold tuning, zero model selection, zero error-driven parameter adjustments, zero manual relabeling, zero hyperparameter search.

---

## 7. Ground Truth

Ground truth specifications established for external footage:
- **Perception Classes**: `Person`, `Vehicle`, `Storage`, `Load`, `Machine`.
- **Annotation Provenance**: Multi-annotator cross-validated bounding boxes with occlusion flags (`NONE`, `PARTIAL`, `HEAVY`).
- **Tracking Ground Truth**: Unique trajectory IDs across contiguous frames.
- **Geometry Ground Truth**: Surveyed laser distance fiducials on ground plane.

Current Status: $0$ ground truth instances available on disk.

---

## 8. Perception Results

Documented in `outputs/v3_3_3/exp_333_01/metrics/perception_metrics.json`:
- **Preregistered Gate**: $\text{Perception F1} \ge 85.00\%$.
- **Observed Micro Metrics**:
  - $\text{TP} = \text{NOT\_AVAILABLE}$
  - $\text{FP} = \text{NOT\_AVAILABLE}$
  - $\text{FN} = \text{NOT\_AVAILABLE}$
  - Micro Precision: $\text{NOT\_ESTABLISHED}$
  - Micro Recall: $\text{NOT\_ESTABLISHED}$
  - Micro F1: $\mathbf{NOT\_ESTABLISHED}$
- **Macro F1**: $\text{NOT\_ESTABLISHED}$
- **Per-Class F1**:
  - Person: $\text{NOT\_ESTABLISHED}$
  - Vehicle: $\text{NOT\_ESTABLISHED}$
  - Storage: $\text{NOT\_ESTABLISHED}$
  - Load: $\text{NOT\_ESTABLISHED}$
  - Machine: $\text{NOT\_ESTABLISHED}$
- **Stratified Breakdowns**: Distance, occlusion, and illumination strata all report sample count $N=0$.

---

## 9. Tracking Results

Documented in `outputs/v3_3_3/exp_333_01/metrics/tracking_metrics.json`:
- **IDF1 Point Estimate**: $\text{NOT\_ESTABLISHED}$ (Target: $\ge 85.00\%$).
- **Identity Switches**: $\text{NOT\_ESTABLISHED}$.
- **Track Fragmentations**: $\text{NOT\_ESTABLISHED}$.
- **Forced Wrong Identity Rate**: $\text{NOT\_ESTABLISHED}$ (Target: $0.00\%$).
- **Ambiguity Policy**: Verified that ambiguous identities are classified as `SAFE_IDENTITY_AMBIGUITY` and not penalized as forced wrong identities.

---

## 10. Geometry Results

Documented in `outputs/v3_3_3/exp_333_01/metrics/geometry_metrics.json`:
- **Planar Homography MAE**: $\text{NOT\_ESTABLISHED}$.
- **Median Absolute Error**: $\text{NOT\_ESTABLISHED}$.
- **P95 Error**: $\text{NOT\_ESTABLISHED}$.
- **Geometry Residual RMSE**: $\text{NOT\_ESTABLISHED}$.
- **Non-Planar / Ramp Regions**: Safety gating policy enforces `OUT_OF_ODD_REFUSAL` when floor slope $> 3.0^\circ$ or non-planar curvature is detected.

---

## 11. Model H Uncertainty Results

Documented in `outputs/v3_3_3/exp_333_01/metrics/uncertainty_metrics.json`:
- **Locked Model H Parameters**: $k_0 = 2.40, \beta_d = 0.08, \beta_L = 0.12, \beta_{\text{pitch}} = 0.22, \gamma_{\text{NONE}}=0.0, \gamma_{\text{PARTIAL}}=0.20, \gamma_{\text{HEAVY}}=0.40$.
- **Zero Adaptation**: Parameters were not tuned or adjusted.
- **External OOS Coverage**:
  $$\text{Covered} = \text{NOT\_AVAILABLE}, \quad \text{Uncovered} = \text{NOT\_AVAILABLE}, \quad N = 0$$
  $$\text{Coverage Rate} = \mathbf{NOT\_ESTABLISHED}$$
  $$\text{Wilson 95\% CI} = \mathbf{NOT\_AVAILABLE}$$
- **Interval Width Statistics**: Mean, median, P95 widths = $\text{NOT\_ESTABLISHED}$.

---

## 12. Action Policy Results

Documented in `outputs/v3_3_3/exp_333_01/metrics/policy_metrics.json`:
- **Action Gating Breakdown**:
  - `FULL_AUTONOMOUS_ACTION`: $\text{NOT\_ESTABLISHED}$
  - `ADVISORY_ONLY`: $\text{NOT\_ESTABLISHED}$
  - `SAFE_REFUSAL`: $\text{NOT\_ESTABLISHED}$
- **Operational Refusal Metrics**:
  - Appropriate Refusal Rate: $\text{NOT\_ESTABLISHED}$
  - False Refusal Rate: $\text{NOT\_ESTABLISHED}$
  - Unsafe Non-Refusal Rate: $\text{NOT\_ESTABLISHED}$
- **Semantic Separation Rule**: Statistical undercoverage is isolated from policy actions. No uncovered point is assumed to be an unsafe action without closed-loop vehicle trace evidence.

---

## 13. Hazard Results

Documented in `outputs/v3_3_3/exp_333_01/metrics/hazard_metrics.json`:
- **Hazard Precision / Recall / F1**: $\text{NOT\_ESTABLISHED}$.
- **Hazard Classification**:
  - `HAZ_01_PEDESTRIAN_FORKLIFT_PROXIMITY`: $\text{NOT\_ESTABLISHED}$
  - `HAZ_02_BLIND_CORNER_INCUSION`: $\text{NOT\_ESTABLISHED}$
  - `HAZ_03_TTC_TIME_TO_COLLISION_BREACH`: $\text{NOT\_ESTABLISHED}$
  - `HAZ_04_UNSTABLE_STORAGE_LOAD`: $\text{NOT\_ESTABLISHED}$
- **Overall Hazard Layer State**: `NOT_ESTABLISHED`.

---

## 14. Event Results

Documented in `outputs/v3_3_3/exp_333_01/metrics/event_metrics.json`:
- **Event Precision / Recall / F1**: $\text{NOT\_ESTABLISHED}$.
- **False Events per Hour**: $\text{NOT\_ESTABLISHED}$.
- **Event Debounce Latency**: $\text{NOT\_ESTABLISHED}$.
- **Integrity Rule**: Event layer metrics are not inferred from perception bounding boxes.

---

## 15. Red-Team Results

Documented in `outputs/v3_3_3/exp_333_01/analysis/red_team_results.json`:
- 10 red-team stress fixtures preregistered and locked:
  1. `REDTEAM_EXT_001_HEAVY_OCCLUSION`: Expected `ADVISORY_DOWNGRADE`
  2. `REDTEAM_EXT_002_CROSSING_WORKERS`: Expected `SAFE_REFUSAL`
  3. `REDTEAM_EXT_003_VEHICLE_PERSON_PROXIMITY`: Expected `SAFE_REFUSAL`
  4. `REDTEAM_EXT_004_LOW_ILLUMINATION`: Expected `SAFE_REFUSAL`
  5. `REDTEAM_EXT_005_HIGH_ILLUMINATION_TRANSITION`: Expected `ADVISORY_DOWNGRADE`
  6. `REDTEAM_EXT_006_DISTANT_OBJECT`: Expected `SAFE_REFUSAL`
  7. `REDTEAM_EXT_007_CAMERA_PITCH_VARIATION`: Expected `ADVISORY_DOWNGRADE`
  8. `REDTEAM_EXT_008_GEOMETRY_DISTURBANCE`: Expected `SAFE_REFUSAL`
  9. `REDTEAM_EXT_009_TEMPORARY_CAMERA_MOVEMENT`: Expected `SAFE_REFUSAL`
  10. `REDTEAM_EXT_010_HIGH_TRAFFIC_DENSITY`: Expected `ADVISORY_DOWNGRADE`
- Current Execution State: All 10 scenarios marked `AWAITING_EXTERNAL_DATA`.

---

## 16. Failure Analysis

Documented in `outputs/v3_3_3/exp_333_01/analysis/failure_taxonomy.json`:
- Total Failures Logged: **1**.
- **`FAIL_EXP333_01_001`**:
  - Primary Category: `DATA_PROVENANCE`
  - Secondary Causal Label: `EVIDENCE_GAP`
  - Description: Absence of authenticated physical footage from an independent facility.
  - Operational Impact: Precludes empirical execution of `EXP_333_01`.
  - Non-Model Attribution: This is a data acquisition limitation, not an algorithmic defect of the V3.3.2 pipeline.

---

## 17. Statistical Analysis

Documented in `outputs/v3_3_3/exp_333_01/analysis/statistical_analysis.json`:
- **Sample Unit Independence Framework**:
  - Perception: Frame unit with recording-session cluster stratification.
  - Tracking: Trajectory unit with camera-recording cluster block bootstrap.
  - Uncertainty: Pointwise unit with track-sequence clustering.
  - Policy: Decision frame with episodic scenario clustering.
- **Reporting Rule**: Because external sample count is $N=0$, no point estimates or confidence intervals are generated.

---

## 18. Limitations

1. **Physical External Data Absence**: Empirical transfer testing across warehouses is unvalidated on real assets.
2. **Optics Transfer Unknown**: Resilience to uncalibrated camera distortion, sensor blur, and high ceiling mounts ($>8\text{m}$) remains unobserved.
3. **Environmental Boundary Unknown**: Sub-zero temperature vapor and dust attenuation have not been empirically evaluated.

---

## 19. Evidence Gaps

Actively tracked evidence gaps:
- `GAP_V3_3_01`: Multi-facility cross-warehouse footage (Facility E unavailable).
- `GAP_V3_3_02`: Population-level causal backfire inference.
- `GAP_V3_3_03`: Dynamic illumination transition uncertainty scaling.
- `GAP_V3_3_04`: Real-time incline ramp surface reconstruction.
- `GAP_V3_3_05`: Re-identification across wide-baseline camera handoffs.
- `GAP_V3_3_06`: Extended longitudinal behavioral adaptation ($>90$ days).

---

## 20. Claims Supported

1. The frozen V3.3.2 pipeline retains complete baseline integrity with zero hash drift across 39 baseline artifacts.
2. The zero-adaptation evaluation harness, blind quarantine manifests, and 10 red-team stress fixtures are established and locked.
3. The repository adheres to strict provenance governance, rejecting unauthenticated data and prohibiting synthetic substitutes for physical external testing.

---

## 21. Claims Not Supported

1. "Safety Backfire AI generalizes across warehouses." *(Prohibited: unvalidated).*
2. "Perception F1 exceeds 85% on external facilities." *(Prohibited: data absent).*
3. "Model H guarantees 95% coverage in unseen warehouses." *(Prohibited: unevidenced).*
4. "The system is proven safe for multi-site deployment." *(Prohibited: unevidenced).*

---

## 22. Final Experiment Status

In accordance with Section 21 and Section 28 governance criteria:
$$\mathbf{V3.3.3\ EXP\_333\_01\ STATUS = NOT\_ESTABLISHED}$$
$$\mathbf{EXTERNAL\_FACILITY\_INDEPENDENCE = NOT\_ESTABLISHED}$$
$$\mathbf{DATA\_VOLUME\_LIMITATION = PRESENT\ (0\ frames)}$$
$$\mathbf{V3.3.3\ NEXT\ EXPERIMENT = HOLD}$$

> **Mandatory Scientific Finding**: External-facility generalization remains NOT_ESTABLISHED because authenticated physically independent external raw footage is unavailable. It is NOT classified as a failed external generalization.

EXP_333_02 (Prospective Backfire) and subsequent physical experiments must **HOLD** until physical footage from an authenticated external facility is acquired and ingested.

---

## 23. Reproduction Commands

To reproduce the baseline lock, provenance validation, and experiment status:

```bash
# Baseline integrity
./.venv/bin/python validation/v3_3_3/test_v3_3_3_integrity.py

# External provenance validation
./.venv/bin/python validation/v3_3_3/validate_external_provenance.py

# EXP_333_01 readiness
./.venv/bin/python validation/v3_3_3/test_exp_333_01_integrity.py

# External ingestion gate regression tests (10/10 PASS)
./.venv/bin/python validation/v3_3_3/test_external_ingestion_gate.py

# Experiment runner (refuses execution while external data are absent)
./.venv/bin/python safety_backfire_v3_3_3/experiments/run_exp_333_01.py
```

---

## 24. Artifact Hashes

The cryptographic hashes for all `EXP_333_01` artifacts are recorded in `outputs/v3_3_3/exp_333_01/release/exp_333_01_hash_manifest.json`.

---
*End of Report.*
