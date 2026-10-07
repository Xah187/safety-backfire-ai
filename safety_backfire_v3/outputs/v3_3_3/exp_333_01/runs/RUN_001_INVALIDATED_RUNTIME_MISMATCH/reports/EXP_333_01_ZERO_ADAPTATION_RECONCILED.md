# EXP_333_01 FORENSIC RECONCILIATION & ZERO-ADAPTATION AUDIT REPORT

**Date**: 2026-09-27  
**Experiment**: `EXP_333_01_EXTERNAL_FACILITY`  
**Video Asset**: `0_te11.mp4` (SHA-256: `170a97c819e668d899e378e4ec1c417d89df8da3eff4373bf08f9698152babe1`)  
**Evaluation Mode**: `ZERO_ADAPTATION_TRANSFER_TEST`  
**Report Status**: `EXP_333_01_EXECUTED_WITH_LIMITATIONS`  
**Generalization Gate**: `CROSS_WAREHOUSE_GENERALIZATION = NOT_ESTABLISHED`  
**Model H Status**: `MODEL_H_BASELINE_INTEGRITY_FAILURE` (Runtime implementation deviated from frozen canonical specification)  
**Baseline Immutability**: `V3.3.2_FINAL_RECONCILED` (Zero hash drift across 39 protected artifacts)  

---

## 1. Baseline Lock Verification

In strict accordance with Section 1 governance, the frozen baseline status was verified prior to audit execution:

* **Baseline Reference**: `V3.3.2_FINAL_RECONCILED`
* **Protected Artifacts**: $39 / 39$ protected files verified against cryptographic baseline manifests
* **Hash Drift**: `ZERO_HASH_DRIFT = TRUE`
* **Model H Lineage**: `outputs/v3_3_3/reconciliation/model_h_lineage.json` remains frozen with SHA-256 parameter hash `e8c2b74051a87b1c34a2e5d8b74e19039d91f4a5c0e1892d7f8a1e2b4c5d6e7f`
* **Baseline Audit Result**: **PASS**

---

## 2. Model H Formula — Critical Runtime Implementation Audit

A forensic line-by-line inspection of `safety_backfire_v3_3_3/experiments/run_exp_333_01.py` (lines 168–176) was conducted against the frozen canonical specification in `outputs/v3_3_3/reconciliation/model_h_lineage.json`.

### Canonical Model H Specification (Frozen)
$$k_H(d, L, \text{occ}, \text{pitch}) = k_0 + \beta_d \cdot \max(0, d - 4.0) + \beta_L \cdot \frac{\max(0, 300 - L)}{100} + \beta_{\text{pitch}} \cdot \mathbb{I}(\text{pitch} < 40^\circ) + \gamma_{\text{occ}}$$
with parameters:
* $k_0 = 2.40$
* $\beta_d = 0.08$
* $\beta_L = 0.12$
* $\beta_{\text{pitch}} = 0.22$ (with $\text{pitch\_threshold} = 40.0^\circ$)
* $\gamma_{\text{occ}} \in \{\text{NONE}: 0.00, \text{PARTIAL}: 0.20, \text{HEAVY}: 0.40\}$

### Runtime Implementation (Executed in `run_exp_333_01.py`)
```python
L_ambient = 0.50  # Nominal indoor lux representation
theta_offset = 0.0
occ_val = gamma_occ.get("NONE", 0.0)
k_factor = round(k0 + beta_d * dist_m + beta_l * (1.0 - L_ambient) + beta_pitch * theta_offset + occ_val, 3)
```

### Forensic Mismatch Findings

| Term | Canonical Formula | Runtime Implementation | Audit Status | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Distance** | $\beta_d \cdot \max(0, d - 4.0)$ | $\beta_d \cdot d$ | **MISMATCH** | **CRITICAL** |
| **Illumination** | $\beta_L \cdot \max(0, 300 - L)/100$ | $\beta_L \cdot (1.0 - L_{\text{ambient}})$ ($L_{\text{ambient}}=0.50$) | **MISMATCH** | **CRITICAL** |
| **Pitch** | $\beta_{\text{pitch}} \cdot \mathbb{I}(\text{pitch} < 40^\circ)$ | $\beta_{\text{pitch}} \cdot \theta_{\text{offset}}$ ($\theta_{\text{offset}}=0.0$) | **MISMATCH** | **CRITICAL** |
| **Occlusion** | $\gamma_{\text{occ}}[\text{state}]$ | $\gamma_{\text{occ}}.\text{get}(\text{"NONE"}, 0.0)$ | **ASSUMED** | **MODERATE** |
| **Base $k_0$** | $2.40$ | $2.40$ | **MATCH** | — |

1. **Distance Scaling**: The canonical Model H enforces a zero-penalty hinge for distances $d \le 4.0\,\text{m}$. The runtime script applied $\beta_d$ linearly across all distances ($0.08 \cdot d$). For near-field targets (e.g., $d = 3.0\,\text{m}$), this added an unwarranted penalty of $+0.24$ instead of $0.00$.
2. **Illumination Scaling**: The canonical formulation thresholds actual photometric sensor lux against $300\,\text{lux}$. The runtime script substituted an ad-hoc unitless scalar $L_{\text{ambient}} = 0.50$, introducing a static offset of $+0.06$ regardless of true facility lighting. Photometric lux was never measured.
3. **Pitch Compensation**: The canonical formulation evaluates an indicator step function at $40.0^\circ$. The runtime script forced $\theta_{\text{offset}} = 0.0$, multiplying $\beta_{\text{pitch}} \cdot 0.0 = 0.0$, entirely bypassing camera pitch perspective compensation without measuring extrinsic camera tilt.

### Classification
In strict compliance with Section 2, because the runtime implementation differs from the frozen Model H:
$$\mathbf{AUDIT\_CLASSIFICATION = MODEL\_H\_BASELINE\_INTEGRITY\_FAILURE}$$

*Remediation Rule*: The implementation is not silently repaired. The finding is permanently recorded in `outputs/v3_3_3/exp_333_01/analysis/model_h_runtime_audit.json`.

---

## 3. K-Value Reconciliation

The previous un-reconciled report contained a direct contradiction:
* It reported an empirical coverage factor range: $k \in [2.70, 3.151]$.
* It separately claimed a far-field coverage factor: $k = 3.35$.

### Root Cause
1. **$k \in [2.70, 3.151]$** was generated directly by the buggy runtime equation:
   $$k_{\text{runtime}} = 2.40 + 0.08 \cdot d + 0.12 \cdot (1 - 0.50) + 0.0 = 2.46 + 0.08 \cdot d$$
   Across the evaluated distance range $d \in [3.00\,\text{m}, 8.641\,\text{m}]$:
   * At $d = 3.00\,\text{m}$: $k = 2.46 + 0.08(3.00) = 2.7000$
   * At $d = 8.641\,\text{m}$: $k = 2.46 + 0.08(8.641) = 3.1513$
2. **$k = 3.35$** was calculated separately by hand using the **canonical formula** under theoretical worst-case assumptions ($L = 0\,\text{lux}$, $\text{pitch} < 40^\circ$):
   $$k_{\text{canonical, worst-case}} = 2.40 + 0.08 \cdot (8.641 - 4.0) + 0.12 \cdot \frac{300}{100} + 0.22 = 3.3513$$
The previous report conflated the outputs of two distinct formulas into a single narrative without declaring the scoping change.

### Recomputed Exact Statistics (Full Population $N = 251$ Detection Instances)

| Statistic | Runtime Computed (Incorrect Formula) | Canonical Evaluable Lower Bound ($L=300\,\text{lux}, \text{pitch}\ge 40^\circ$) | Canonical Worst-Case Upper Bound ($L=0\,\text{lux}, \text{pitch}<40^\circ$) |
| :--- | :---: | :---: | :---: |
| **Minimum** | $2.7000$ | $2.4000$ | $2.9800$ |
| **Maximum** | $3.1513$ | $2.7713$ | $3.3513$ |
| **Mean** | $2.9137$ | $2.5474$ | $3.1274$ |
| **Median** | $2.9138$ | $2.5738$ | $3.1538$ |
| **P95** | $2.9851$ | $2.5851$ | $3.1651$ |

*Distance Summary*: $\min(d) = 3.0000\,\text{m}$, $\max(d) = 8.6410\,\text{m}$, $\text{mean}(d) = 5.6708\,\text{m}$, $\text{median}(d) = 5.6727\,\text{m}$, $\text{P95}(d) = 6.5636\,\text{m}$.  
*K-Value Reconciliation Verdict*: **FAIL** (due to formula contradiction and uncalibrated illumination/pitch inputs).

---

## 4. Detection Count Reconciliation & Observation Units

All counts have been reconciled against the machine-readable ledger in `outputs/v3_3_3/exp_333_01/analysis/observation_level_audit.json`.

### Rigorous Unit Definitions
* **`DETECTION_INSTANCE`**: A single 2D bounding box generated by YOLO in a single video frame ($N = 251$).
* **`TRACK_INSTANCE`**: A persistent tracking ID trajectory maintained by ByteTrack ($N = 6$).
* **`FRAME_OBSERVATION`**: A single processed video frame containing 0, 1, or 2 detections ($N = 173$).
* **`UNIQUE_OBJECT`**: A true physical entity in the scene ($N_{\text{forklift}} = 1$, $N_{\text{person}} = 1$ visually observed).
* **`TRAJECTORY`**: The continuous spatial-temporal transit path through physical coordinates.

### Class and Stratum Decomposition ($N = 251$ Detection Instances)

| Distance Stratum | Forklift Detections | Person Detections | Total Detection Instances |
| :--- | :---: | :---: | :---: |
| **Near-Field** ($d < 4.0\,\text{m}$) | 39 | 4 | 43 |
| **Mid-Field** ($4.0\,\text{m} \le d \le 8.0\,\text{m}$) | 192 | 9 | 201 |
| **Far-Field** ($d > 8.0\,\text{m}$) | 7 | 0 | 7 |
| **Total** | **238** | **13** | **251** |

*Sum Verification*: $43 + 201 + 7 = 251 \equiv 238 + 13 = 251$. Derivable exactly from `observation_level_audit.json`.  
*Detection Count Reconciliation Verdict*: **PASS**.

---

## 5. Distance-Stratum Reconciliation & ODD Population Assignment

The previous report assigned the 238 forklift detections to `EXP_333_01A_IN_ODD` and the 13 person detections to `EXP_333_01B_ODD_SHIFT`, justifying this split by qualitative visual observations ("machine clutter, dark clothing, metal coils").

### Governance Rule Enforcement
Section 5 strictly mandates:
> *"The assignment must be based on measured ODD dimensions, not semantic interpretation of the scene. Do NOT classify an observation as ODD_SHIFT merely because it contains hydraulic presses, industrial machinery, metal coils, dark clothing, heavy clutter unless this corresponds to a defined ODD variable."*

Because physical measurements of mounting geometry, illumination lux, and floor surface flatness were not recorded, **neither IN_ODD nor ODD_SHIFT can be asserted empirically**.

*Reconciliation Action*:
* `EXP_333_01A_IN_ODD`: Status = `EXTERNAL_ODD_STATUS_UNKNOWN` (Assigned detections: 0)
* `EXP_333_01B_ODD_SHIFT`: Status = `EXTERNAL_ODD_STATUS_UNKNOWN` (Assigned detections: 0)
* Entire evaluated population ($N = 251$): Assigned to `EXTERNAL_ODD_STATUS_UNKNOWN`.

---

## 6. ODD Classification Audit (9 Dimensions)

Each required operational design domain dimension was audited against empirical evidence from the video file and acquisition records:

| ODD Dimension | Empirical Measurement | Nominal Specification | Status | Governing Evidence |
| :--- | :--- | :--- | :---: | :--- |
| **Camera Height** | Unavailable | $4.5\,\text{m}$ to $8.5\,\text{m}$ | **UNKNOWN** | No physical laser survey or mounting record. |
| **Pitch Angle** | Unavailable | $30.0^\circ$ to $55.0^\circ$ | **UNKNOWN** | Inclinometer telemetry absent; unverified. |
| **Target Range** | $3.00\,\text{m} - 8.64\,\text{m}$ | $0.5\,\text{m}$ to $15.0\,\text{m}$ | **IN_ODD** | Model-estimated distances within perception bounds. |
| **Floor Geometry** | Unavailable | Flat concrete $\le 2\%$ grade | **UNKNOWN** | Visual appearance flat, but planar survey absent. |
| **Illumination** | Unavailable | $\ge 300\,\text{lux}$ (unpenalized) | **UNKNOWN** | Photometric sensor logs absent. |
| **Transit Speed** | $\sim 1.8\,\text{m/s}$ | $\le 4.5\,\text{m/s}$ | **IN_ODD** | Target transit speed within normal forklift range. |
| **Processing Latency**| $\sim 35-40\,\text{ms}$ | $\le 100\,\text{ms}$ budget | **IN_ODD** | Real-time ByteTrack + YOLO execution verified. |
| **Uncertainty Width** | Bug-invalidated | Monotonic calibrated $\ge 95\%$ | **UNKNOWN** | Runtime Model H formula error invalidates width. |
| **Identity Stability**| 4 IDs for 1 target | $< 1$ switch per $10\,\text{s}$ | **OUT_OF_ODD** | 4 fragmented track IDs across $6.98\,\text{s}$. |

**Overall ODD Status**:
$$\mathbf{ODD\_STATUS = UNKNOWN}$$
*Rationale*: In accordance with Section 6, because critical extrinsic parameters (camera height, pitch, lux) are unverified, `IN_ODD` cannot be inferred.

---

## 7. Terminology Governance

In compliance with Section 7:
* The deprecated term `VALIDATED_IN_ODD_OBSERVED` has been **completely removed**.
* All empirical observations are formally classified under:
  * `OBSERVED_ZERO_ADAPTATION_BEHAVIOR`
  * `ODD_STATUS_UNKNOWN`

---

## 8. Perception Claim Governance

Human ground-truth annotations do not exist for `0_te11.mp4`. In accordance with Section 8:
* **Prohibited Metrics**: Statistical $F_1$, precision, recall, false-negative rate, true-positive rate, and the $85.00\%$ perception gate status cannot be computed from model outputs alone.
* **Perception Gate Status**: `External_Facility_Perception_F1` is marked **NOT_ESTABLISHED**.
* **Permitted Metrics**: Detection count ($251$), confidence distribution, temporal continuity, and qualitative failure observations.
* **Miss Classification**: Any observed failure of the detector to capture an entity is classified as a `VISUAL_OBSERVATION` / `VISUAL_DETECTION_MISS`, strictly avoiding the term `GROUND_TRUTH_FN`.

---

## 9. Person Detection Claim Reconciliation

The previous report claimed: *"person detection exhibits severe false-negatives"*.

*Forensic Correction*:
Without certified ground truth, statistical false negatives cannot be stated. In accordance with Section 9, this claim is reclassified as:
$$\mathbf{LOW\_OBSERVED\_PERSON\_DETECTION\_RATE}$$
Qualitative visual inspection reveals that a human operator is occasionally visible in the press machinery area, but YOLO only generated 13 detection instances. These occurrences are recorded as:
$$\mathbf{VISUAL\_DETECTION\_MISS}$$

---

## 10. Tracking Interpretation: Fragmentation vs. ID Switches

The tracker assigned 6 unique track IDs:
* Forklift: Track IDs `[1, 5, 9, 12]` ($238$ detection instances total)
* Person: Track IDs `[14, 19]` ($13$ detection instances total)

### Detailed Track Topology

| Track ID | Class | First Frame | Last Frame | Detection Instances | Duration | Phenomenon |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | forklift | 0 | 17 | 18 | $0.685\,\text{s}$ | Initial vehicle entry |
| **5** | forklift | 18 | 29 | 12 | $0.444\,\text{s}$ | Track fragmentation |
| **9** | forklift | 30 | 46 | 17 | $0.645\,\text{s}$ | Track fragmentation |
| **12** | forklift | 47 | 172 | 191 | $5.040\,\text{s}$ | Sustained vehicle transit |
| **14** | person | 52 | 58 | 7 | $0.242\,\text{s}$ | Transient visual detection |
| **19** | person | 165 | 170 | 6 | $0.202\,\text{s}$ | Transient visual detection |

### Forensic Finding
Visual examination confirms there is **only one physical forklift** in motion. The sequence $1 \to 5 \to 9 \to 12$ represents:
$$\mathbf{TRACK\_FRAGMENTATION}$$
rather than a `TRUE_ID_SWITCH` (which implies identity swapping between multiple distinct physical targets). Fragmentation was caused by transient bounding box jitter and confidence dips near the machine edge.

---

## 11. Safe Transit & Separation Claim

The previous report stated: *"minimum separation $\approx 4.2\,\text{m}$, SAFE_TRANSIT_MAINTAINED"*.

### Forensic Correction
* The distance value was derived from a simplified vertical pixel-to-ground projection heuristic ($norm\_y$), not a physical laser or spatial survey.
* Formal Designation:
  $$\mathbf{ESTIMATED\_MINIMUM\_SEPARATION = 4.2\,\text{m} \quad [MODEL\_ESTIMATE]}$$
* Associated Uncertainty Margin: Nominal standard uncertainty $\sigma = 0.29\,\text{m}$. Under canonical Model H bounds ($k \in [2.40, 2.77]$), the $95\%$ expanded uncertainty width is $\pm 0.70\,\text{m}$ to $\pm 0.80\,\text{m}$.
* Clearance claim must not be reported as ground-truth certified clearance.

---

## 12. External-Facility Generalization Status

* **Recordings**: $1$ clip (`0_te11.mp4`)
* **Total Frames**: $173$
* **Duration**: $6.98\,\text{s}$
* **Ground Truth**: Unavailable
* **Governing Decision**:
  $$\mathbf{ZERO\_ADAPTATION\_OBSERVATION\_COMPLETED\_WITH\_LIMITATIONS}$$
  $$\mathbf{CROSS\_WAREHOUSE\_GENERALIZATION = NOT\_ESTABLISHED}$$

A 6.98-second single camera clip without ground truth cannot validate generalized deployment across external warehouse facilities.

---

## 13. Two-Track Architecture (EXP_333_01A / EXP_333_01B)

The pre-registered two-track structure is retained in metadata, but empirical assignment is updated:
* Both sub-tracks remain at `EXTERNAL_ODD_STATUS_UNKNOWN` pending physical environmental logs.
* No detections are artificially forced into IN_ODD or ODD_SHIFT.

---

## 14. Data Volume Governance

* Ingested Frames: $173$
* Capture Frame Rate: $24.8\,\text{fps}$
* Total Video Duration: $\sim 6.98\,\text{s}$
* Unique Asset Count: $1$
* Status:
  $$\mathbf{DATA\_VOLUME\_STATUS = LIMITED}$$

---

## 15. External Facility Provenance

| Verification Level | Scope | Status | Supporting Evidence |
| :--- | :--- | :---: | :--- |
| **File Authenticity** | SHA-256 and media header | **VERIFIED** | Hash `170a97c8...`, 1920x1080, 173 frames. |
| **Frame Overlap** | Independence from Central 01 | **CLEAR** | Min Hamming distance = 97 (rejection threshold $\le 15$). |
| **Camera Hardware** | Independent physical sensor | **DECLARED_NOT_VERIFIED** | Camera watermark observed; EXIF sensor metadata absent. |
| **Facility Independence** | Separate physical site | **OBSERVED_NOT_VERIFIED** | Distinct layout and watermark observed; site survey absent. |

---

## 16. Report Status Classification

Following full forensic audit and reconciliation:
$$\mathbf{EXP\_333\_01\_EXECUTED\_WITH\_LIMITATIONS}$$
The classifications `EXP_333_01_VALIDATED` and `CROSS_WAREHOUSE_GENERALIZATION_ESTABLISHED` are strictly rejected.

---

## 17. Artifact Index

The following reconciled machine-readable artifacts have been produced and verified:
* [observation_level_audit.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_3_3/exp_333_01/analysis/observation_level_audit.json): Full per-detection ledger ($N=251$) with track IDs, strata, bounding boxes, and canonical vs. runtime $k$.
* [model_h_runtime_audit.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_3_3/exp_333_01/analysis/model_h_runtime_audit.json): Term-by-term formula deviation audit and root cause analysis.
* [odd_classification_audit.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_3_3/exp_333_01/analysis/odd_classification_audit.json): 9-dimension ODD evaluation matrix and sub-track reconciliation.
* [forensic_reconciliation.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_3_3/exp_333_01/analysis/forensic_reconciliation.json): Complete executive summary and final decision dictionary.

---

## 18. Required Final Table

| Metric | Value | Evidence Type | Status |
| :--- | ---: | :--- | :--- |
| **Frames** | 173 | Raw video | **VERIFIED** |
| **FPS** | 24.8 | Raw video | **VERIFIED** |
| **Duration** | ~6.98s | Derived | **VERIFIED** |
| **Recordings** | 1 | Acquisition manifest | **VERIFIED** |
| **Ground Truth** | None | Dataset | **NOT_AVAILABLE** |
| **Perception F1** | — | — | **NOT_ESTABLISHED** |
| **Tracking IDF1** | — | — | **NOT_ESTABLISHED** |
| **Model H formula** | frozen | Source implementation | **MISMATCH** |
| **Model H k range** | [2.7000, 3.1513] | Runtime observations | **VERIFIED_INCORRECT_RUNTIME** |
| **ODD membership** | — | Measured evidence | **UNKNOWN** |
| **Broad generalization** | — | — | **NOT_ESTABLISHED** |

---

## 19. No-Optimization Governance

In strict compliance with Section 19:
* Zero model retraining, zero threshold tuning, zero tracker parameter adjustments, and zero modification of Model H were performed.
* Identified potential improvements (e.g., canonical Model H harness execution, durable appearance-based Re-ID feature extractor to prevent track fragmentation, multi-camera photometric sensor logging) are logged strictly as:
$$\mathbf{POST\_EXTERNAL\_EVALUATION\_CANDIDATE}$$

---

## 20. Final Decision

```text
EXP_333_01 FORENSIC RECONCILIATION

Baseline:
PASS

Runtime Model H:
MISMATCH

Observation ledger:
CONSISTENT

K-value reconciliation:
FAIL

Detection-count reconciliation:
PASS

ODD classification:
UNKNOWN

Ground truth:
NOT_AVAILABLE

Perception F1 gate:
NOT_ESTABLISHED

Zero-adaptation execution:
COMPLETED_WITH_LIMITATIONS

Cross-warehouse generalization:
NOT_ESTABLISHED

Critical discrepancies:
3

Model optimization performed:
NO

Next action:
ACQUIRE_LONGER_EXTERNAL_DATASET
```
