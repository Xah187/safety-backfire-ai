# V3.4-C Automated Evidence Screening Summary Report

**Milestone:** V3.4-C Automated Evidence Screening  
**Timestamp:** 2026-09-30 08:46:41 UTC  
**Human Review State:** `HUMAN_REVIEW = BYPASSED`  
**Ground Truth State:** `SAFETY_BACKFIRE_GT = NOT_ESTABLISHED`  
**Validation State:** `SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED`  
**Perception Metrics:** `PERCEPTION_METRICS = NOT_ESTABLISHED`  

---

## 1. Executive Summary & Epistemic Boundaries

In accordance with user directive, the human review protocol has been formally **BYPASSED** to eliminate dependency on human reviewer availability. An automated, reproducible, evidence-based screening pipeline has been executed across the 38 eligible event packages.

### Crucial Epistemic Warning
> [!IMPORTANT]
> The labels generated in this stage are strictly **`AUTOMATED_SCREENING_LABEL`** hypotheses.
> They are **NOT GROUND TRUTH**.
> Detector observations (YOLO/ByteTrack) are treated as **`DETECTOR_OBSERVATION`** only.
> No precision, recall, F1, or validation metrics are claimed or calculated.

---

## 2. Event Inventory & Screening Distribution

| Category | Count | Governance Status |
| :--- | :--- | :--- |
| **Total Union Event Pool** | **51** | All events preserved in registry |
| **Screened Eligible Events** | **38** | Full computational & video integrity audit |
| **Ineligible Events (Window Invalid)** | **13** | Preserved with status `INELIGIBLE_WINDOW` |
| **CANDIDATE_BACKFIRE** | **5** | High detector convergence with secondary displacement |
| **CANDIDATE_NO_BACKFIRE** | **13** | Primary interaction resolved with zero secondary hazard |
| **INSUFFICIENT_EVIDENCE** | **20** | Ambiguous CCTV observation / occluded secondary zone |
| **NOT_REVIEWED** | **13** | Ineligible window events excluded from causal screening |

---

## 3. Reasons for Insufficient Evidence

The 20 events classified as `INSUFFICIENT_EVIDENCE` exhibit one or more of the following empirical limitations:
1. **Absence of Physical Telemetry:** Observational CCTV footage lacks ground sensor verification (lux readings, AGV floor-load cells, acoustic alarms).
2. **Rack Aisle Occlusion:** Fixed monocular cameras suffer from partial or complete line-of-sight occlusion into adjacent storage aisles.
3. **Undefined Secondary Zones:** In human-discovered events (`UNION_HEVT_Warehouse_026_003` and `UNION_HEVT_Warehouse_027_002`), secondary zone geometry is `UNKNOWN`.
4. **Causal Link Indeterminacy:** Temporal succession cannot prove physical or behavioral causality without counterfactual controls.

---

## 4. Governance & Integrity Verifications

- **Raw Datasets:** Read-only and unmodified; SHA256 verified against official NVIDIA manifests.
- **Model H:** Unchanged and frozen ($k_0 = 2.40, \beta_d = 0.08, \beta_l = 0.12, \beta_{\text{pitch}} = 0.22$).
- **Reviewer Forms:** Untouched; zero synthetic or automated labels inserted into `reviewer_1_form.json` or `reviewer_2_form.json`.
- **Ground Truth File:** `safety_backfire_event_gt.json` strictly maintains `total_verified_gt_events = 0`.
