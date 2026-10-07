# Safety Backfire AI — V3.4-B Safety Backfire Event Discovery & Ground-Truth Preparation Report (REV 2)

**Document Identifier**: `V3_4-B-EVENT-DISCOVERY-001-REV2`  
**Milestone**: `SAFETY_BACKFIRE_AI_V3.4-B REV2`  
**Publication Date**: `2026-09-30T00:30:00Z`  
**Revision Context**: Dual-Path Architecture (AI Discovery + Independent Human Screening), Temporal Window Integrity Audit & Epistemic Decoupling  
**Governance Scope**: Candidate Event Screening, Human Review Packaging & Ground-Truth Preparation  
**Authoritative Reference**: NVIDIA PhysicalAI-SmartSpaces ([Warehouse_026](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_026), [Warehouse_027](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_027))  

---

## 1. Executive Summary & Revised Governance Verdict

```
================================================================================
V3.4-B REV2 EVENT DISCOVERY & DUAL-PATH SCREENING VERDICT
================================================================================
AI_GENERATED_CANDIDATE_EVENTS      = 49
HUMAN_INDEPENDENT_SCREENING_EVENTS = 5
DUAL_DISCOVERED_OVERLAP            = 3
HUMAN_ONLY_CANDIDATE_EVENTS        = 2
UNION_EVENT_SET                    = 51 Unique Events
WINDOW_INTEGRITY_AUDIT             = 36 VALID / 13 INVALID
SAFETY_BACKFIRE_GT                 = PENDING_HUMAN_REVIEW
SAFETY_BACKFIRE_VALIDATION         = NOT_ESTABLISHED
SOURCE_A_STATUS                    = VERIFIED_LOCAL (Warehouse_026 & Warehouse_027)
SOURCE_B_STATUS                    = NOT_FOUND_LOCALLY (Mendeley; Halted without download)
MODEL_H_STATUS                     = INVARIANT_UNTOUCHED (Parameters strictly frozen)
RAW_DATA_MODIFICATION              = NONE (Zero raw file alteration)
================================================================================
```

### 1.1 Critical Revision Principles
1. **Model as Candidate Generator Only**: Algorithms are strictly restricted to heuristic screening. Automated systems cannot label events as `BACKFIRE` or `NO_BACKFIRE`.
2. **Event $\neq$ Proximity**: Spatial proximity, bounding box overlap, or distance threshold crossing does **not** constitute proof of a safety intervention. The fields `possible_interaction`, `possible_intervention`, `confirmed_intervention`, and `human_verified_event` are formally separated.
3. **Dual-Path Architecture**: To mitigate algorithmic candidate-selection bias, independent blind human screening was conducted across all 11 streams (60s each), discovering events missed by proximity thresholds.
4. **Window Integrity Mandate**: Candidates lacking valid pre-, active, or post-intervention observation windows (such as `CAND_Warehouse_026_008` where `before` is truncated at F0000) are flagged as `WINDOW_VALID = FALSE` and excluded from final adjudication.

---

## 2. Dual-Path Candidate Set Quantification

```
┌─────────────────────────────────┬──────────────────────┬──────────────────────────────────────────────────────┐
│ SCREENING PATH                  │ EVENT COUNT          │ EPISTEMIC CHARACTERIZATION                           │
├─────────────────────────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│ Path A: AI Candidate Screening  │ 49 events            │ Automated spatial convergence (proximity heuristic)  │
│ Path B: Human Scene Screening   │ 5 events             │ Full-scene blinded human observation (11 streams)    │
├─────────────────────────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│ Dual-Discovered (Path A ∩ B)    │ 3 events             │ Detected by both tracker proximity and visual review │
│ Human-Only Candidates           │ 2 events             │ Precautionary hesitation / worker gesturing (>12m)   │
├─────────────────────────────────┼──────────────────────┼──────────────────────────────────────────────────────┤
│ UNION EVENT SET (Path A ∪ B)    │ 51 unique events     │ Master candidate pool for formal human review        │
└─────────────────────────────────┴──────────────────────┴──────────────────────────────────────────────────────┘
```

* Master Union Registry: [`outputs/v3_4/candidates/union_events_registry.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/candidates/union_events_registry.json)
* Blind Human Screening Record: [`outputs/v3_4/human_screening/human_discovered_events.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/human_screening/human_discovered_events.json)

---

## 3. Candidate Temporal Window Integrity Audit

An exhaustive audit of all 49 AI-generated candidates was executed via [`candidate_window_audit.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/candidates/candidate_window_audit.json) enforcing the mandatory criteria:
$$\text{duration}(\text{PRE}) > 0, \quad \text{duration}(\text{INTERVENTION}) > 0, \quad \text{duration}(\text{POST}) > 0$$
$$\text{pre\_end} < \text{intervention\_start} \le \text{intervention\_end} < \text{post\_start}$$

```
┌─────────────────────────────────┬──────────┬──────────┬───────────────────────────────────────────────────────┐
│ CANDIDATE SUBSET                │ VALID    │ INVALID  │ PRIMARY INVALIDATION REASONS                          │
├─────────────────────────────────┼──────────┼──────────┼───────────────────────────────────────────────────────┤
│ Warehouse_026 Candidates (N=14) │ 10 valid │ 4 invalid│ Pre-window truncated at stream start (start_frame<30) │
│ Warehouse_027 Candidates (N=35) │ 26 valid │ 9 invalid│ Pre-window truncated (start) / Post-window (end)      │
├─────────────────────────────────┼──────────┼──────────┼───────────────────────────────────────────────────────┤
│ TOTAL AUDITED CANDIDATES (N=49) │ 36 VALID │ 13 INVAL │ WINDOW_VALID = FALSE logged; zero frame fabrication   │
└─────────────────────────────────┴──────────┴──────────┴───────────────────────────────────────────────────────┘
```

### 3.1 Case Audit: `CAND_Warehouse_026_008`
* **Observed State**: Start frame $= 1$, End frame $= 430$.
* **Audit Finding**: `before` clip corresponds to `F0000–F0000` ($\text{duration} = 0.03\,\text{s}$).
* **Governance Invariant**: Classified as **`WINDOW_VALID = FALSE`** with reason:  
  `PRE = INSUFFICIENT (start_frame < 30; baseline window truncated at stream start)`.  
  *No frames prior to stream start are fabricated or assumed.*

---

## 4. Intervention Evidence Taxonomy

Per schema [`schemas/v3_4/intervention_evidence.schema.json`](file:///Users/xah187/Projects/safety-backfire-ai/schemas/v3_4/intervention_evidence.schema.json), proximity alone is never classified as intervention. Allowed evidence types:
* `VISIBLE_HARD_BRAKING` (Observable pitching / tyre lockup / abrupt stop)
* `VISIBLE_STEERING_AVOIDANCE` (Sharp angular trajectory deviation around an obstacle)
* `VISIBLE_WORKER_EVASION` (Pedestrian stepping backwards, sideways into rack, or halting)
* `AUDIBLE_WARNING_OBSERVED` (Horn alert if audio available; currently UNKNOWN in silent benchmark)
* `WARNING_BEACON_OBSERVED` (Flashing strobe / visual beacon)
* `SAFETY_CONTROLLER_SIGNAL` / `VEHICLE_TELEMETRY` (CAN-bus velocity / deceleration telemetry)
* `UNKNOWN` (Absence of objective corroborating channel)

---

## 5. Metric Distance vs Pixel Distance Decoupling

* **Image Coordinates**: Measured as Euclidean distance between 2D foot-points in pixel space ($\text{dist}_{\text{px}}$).
* **World Coordinates**: Converted to metric ground-plane meters ($\text{dist}_{\text{m}}$) strictly via verified planar homographies from [`calibration.json`](file:///Users/xah187/Projects/safety-backfire-ai/data/external_facility/raw/Warehouse_026/MTMC_Tracking_2026/test/Warehouse_026/calibration.json).
* **Rule**: Where homography or multi-camera intersection is unverified, `world_distance_m = UNKNOWN`. Direct heuristic scaling from pixels to meters is prohibited.

---

## 6. Spatial Zone Status Governance

* **Primary Zones**: Optical corridors derived from ground homography are classified as **`DATASET_GEOMETRIC`** or **`PROVISIONAL`**.
* **Secondary Zones**: Adjacent storage aisles and rack corridors without independent CAD blueprints or physical surveying logs are formally classified as **`PROVISIONAL`** or **`UNKNOWN`**.
* **Rule**: Absence of observable secondary zone hazards cannot be used to infer `NO_SECONDARY_RISK`.

---

## 7. Blinded Human Review Protocol

Human review bundles generated in [`outputs/v3_4/candidates/`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/candidates/) enforce total assessor blinding:
* **Excluded**: `candidate_relevance_score`, detector confidence, YOLO boxes, ByteTrack IDs, Model H values, and automated Backfire recommendations.
* **Included**: Raw review clips (`before.mp4`, `intervention.mp4`, `after.mp4`), neutral contact sheets, and standard `human_review_form.json`.
* **7-Criterion Scoring Rubric**: Evaluated strictly as `YES`, `NO`, or `UNKNOWN` (the designation `PASS` is prohibited).
* **Dual Reviewers**: Two independent assessors must concur; discrepancies require formal adjudication notes.

---

## 8. Final Status Declaration

```
SAFETY_BACKFIRE_GT         = PENDING_HUMAN_REVIEW
SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED
BASELINE_MODEL_H_STATUS    = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
```

Milestone V3.4-B REV 2 establishes a dual-path discovery architecture that insulates the safety case from circular model bias.
