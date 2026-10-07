# Safety Backfire AI — V3.4-B REV2 Candidate Validation & Independent Screening Report

**Document Identifier**: `V3_4-B-REV2-VALIDATION-FINAL`  
**Milestone**: `SAFETY_BACKFIRE_AI_V3.4-B REV2`  
**Publication Date**: `2026-09-30T00:30:00Z`  
**Governance Scope**: Dual-Path Screening Validation, Window Integrity Audit & Human Adjudication Readiness  
**Target Corpus**: NVIDIA PhysicalAI-SmartSpaces Real-World Test Captures ([Warehouse_026](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_026), [Warehouse_027](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_027))  

---

## Executive Summary

```
================================================================================
V3.4-B REV2 DUAL-PATH VALIDATION AUDIT SUMMARY
================================================================================
AI_CANDIDATE_SET           = 49 Events (Algorithmic Proximity Screening)
INDEPENDENT_HUMAN_SET      = 5 Events (Blinded Full-Scene Observation)
DUAL_DISCOVERED_EVENTS     = 3 Events (Concurrently Discovered by AI & Human)
HUMAN_ONLY_CANDIDATES      = 2 Events (AI Missed via Proximity Cutoff)
UNION_EVENT_POOL           = 51 Unique Events (Master Human Adjudication Set)
WINDOW_INTEGRITY_STATUS    = 36 VALID (73.5%) / 13 INVALID (26.5%)
HUMAN_REVIEW_PACKAGES      = GENERATED & BLINDED (Zero AI Cues)
SAFETY_BACKFIRE_GT         = PENDING_HUMAN_REVIEW
SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED
================================================================================
```

---

## 1. AI Candidate Set (Path A)

Automated candidate generation was executed across the observation ledgers of RUN_003 (Warehouse_026, 4 cameras) and RUN_004 (Warehouse_027, 7 cameras) via [`scripts/v3_4/discover_event_candidates.py`](file:///Users/xah187/Projects/safety-backfire-ai/scripts/v3_4/discover_event_candidates.py).

* **Detection Criteria**: Sustained spatial co-occurrence between a detected person and an industrial forklift lasting $\ge 20$ consecutive frames ($\ge 0.67\,\text{s}$).
* **Total Discovered**: **49 candidate events** (14 in Warehouse_026, 35 in Warehouse_027).
* **Candidate Relevance Score**: Scored on a normalized scale $[0.0, 1.0]$ combining closest approach distance ($60\%$) and temporal duration ($40\%$).
* **Governance Boundary**: The score is strictly designated as **`candidate_relevance_score`** for human review prioritization. It does **not** represent risk probability, collision probability, or Backfire likelihood.

---

## 2. Independent Human Screening (Path B)

To eliminate algorithmic candidate-selection bias where the AI system only presents events that align with its own detection boundaries, an independent blind screening pipeline was deployed:

* **Screening Scope**: 100% of all 11 physical camera streams across Warehouse_026 and Warehouse_027 (660 seconds total; 19,800 frames).
* **Blinding Protocol**: Human assessors evaluated video streams via [`SCREENING_BLIND`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/human_screening/SCREENING_BLIND/) timelines, displaying only raw footage, frame numbers, and timestamps. Zero AI bounding boxes, zero tracker IDs, and zero automated scores were visible.
* **Human Discoveries**: **5 distinct interaction events** were cataloged in [`schemas/v3_4/human_event_screening.schema.json`](file:///Users/xah187/Projects/safety-backfire-ai/schemas/v3_4/human_event_screening.schema.json).
* **Human-Only Events (`HUMAN_ONLY_CANDIDATE`)**:
  - `HEVT_Warehouse_026_003`: Pedestrian precautionary pause at an intersection in Camera_0000 upon observing a turning forklift at a distance $>12\,\text{m}$. Missed by the AI candidate generator because the pixel separation exceeded the 600px proximity cutoff.
  - `HEVT_Warehouse_027_002`: Worker in Camera_0003 verbally/visually warning a co-worker to halt before a blind rack corner.

---

## 3. Union Set Assembly & Provenance Linkage

The master candidate pool is established as the formal set union:
$$\text{UNION\_SET} = \text{AI\_SET} \cup \text{HUMAN\_SET} \quad (N = 51)$$

* **Dual-Discovered Events ($N=3$)**: Events identified by both automated clustering and blinded human observation (e.g., `CAND_Warehouse_026_007` $\leftrightarrow$ `HEVT_Warehouse_026_001`). Both AI provenance and Human provenance records are preserved and linked via `linked_candidate_id`.
* **Master Registry**: Cataloged in [`outputs/v3_4/candidates/union_events_registry.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/candidates/union_events_registry.json).

---

## 4. Window Integrity Audit

In strict compliance with V3.4-B REV2 constraints, every candidate was audited to verify the mandatory temporal sequence:
$$\text{pre\_end} < \text{intervention\_start} \le \text{intervention\_end} < \text{post\_start}$$
$$\text{duration}(\text{PRE}) \ge 1.0\,\text{s}, \quad \text{duration}(\text{INTERVENTION}) > 0, \quad \text{duration}(\text{POST}) \ge 1.0\,\text{s}$$

* **Valid Windows**: **36 candidates** ($73.5\%$) satisfy all three non-zero window conditions.
* **Invalid Windows**: **13 candidates** ($26.5\%$) were classified as **`WINDOW_VALID = FALSE`** and logged in [`candidate_window_audit.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/candidates/candidate_window_audit.json).
* **Case Study `CAND_Warehouse_026_008`**: Start frame $= 1$. The baseline `before` clip corresponds to `F0000–F0000` (duration 0.03s). Formally classified as `WINDOW_VALID = FALSE` with reason `PRE = INSUFFICIENT`. No imaginary frames prior to recording start were fabricated.
* **Governance Rule**: Candidates flagged as `WINDOW_VALID = FALSE` are retained in the registry for provenance completeness but excluded from formal Ground-Truth adjudication.

---

## 5. Intervention Evidence & Physical Decoupling

Under schema [`schemas/v3_4/intervention_evidence.schema.json`](file:///Users/xah187/Projects/safety-backfire-ai/schemas/v3_4/intervention_evidence.schema.json):
* **Proximity $\neq$ Intervention**: Spatial convergence, bounding-box overlap, and distance threshold crossing do not constitute safety interventions.
* **Evidence Channels**: Physical safety interventions must be corroborated by observable physical modalities (`VISIBLE_HARD_BRAKING`, `VISIBLE_STEERING_AVOIDANCE`, `VISIBLE_WORKER_EVASION`, `WARNING_BEACON_OBSERVED`, or `VEHICLE_TELEMETRY`).
* **Current Evidence Reality**: In the silent, passive CCTV benchmark footage, vehicle deceleration can only be inferred through pixel optical flow or tracker velocity; true active safety controller braking commands remain unverified due to lack of CAN-bus telemetry.

---

## 6. Primary Zones Governance

* **Definition**: The operational corridor where the safety intervention or interaction is situated.
* **Status**: Primary zones (e.g., `Camera_0002_CENTRAL_CORRIDOR`) derived from the dataset's calibrated ground-plane homographies are classified as **`DATASET_GEOMETRIC`** or **`PROVISIONAL`**.
* **Epistemic Constraint**: Prohibited from labeling as `PHYSICALLY_SURVEYED` unless independent total-station surveying logs exist.

---

## 7. Secondary Zones Governance

* **Definition**: Adjoining aisles, blind crossings, or egress corridors where displaced hazards or spillover risks might emerge.
* **Status**: In the public NVIDIA test package, camera coverage is unlinked to facility CAD blueprints. Secondary zones without documented geometric mapping are formally classified as **`UNKNOWN`** or **`PROVISIONAL`**.
* **Rule**: Inability to observe a secondary hazard due to camera occlusion or absence of adjacent views does **not** prove `NO_SECONDARY_RISK`.

---

## 8. Blinded Human Review Packages & Scoring Rubric

Human review packages in [`outputs/v3_4/candidates/`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/candidates/) contain derived clips (`before.mp4`, `intervention.mp4`, `after.mp4`), neutral contact sheets, and blinded review forms:
* **Blinding**: Assessor forms contain zero AI metrics, zero YOLO confidence values, and zero Backfire suggestions.
* **Scoring Rubric**: Reviewers evaluate the 7 canonical criteria strictly using categorical responses:
  $$\textbf{Allowed: } \text{YES} \quad / \quad \text{NO} \quad / \quad \text{UNKNOWN} \quad (\textbf{PASS is strictly prohibited})$$
* **Inter-Rater Adjudication**: Requires two independent safety assessors (`reviewer_1`, `reviewer_2`). Disagreements require explicit adjudication notes.
* **Final Adjudicated Labels**: `BACKFIRE`, `NO_BACKFIRE`, `AMBIGUOUS`. (The status `PENDING_HUMAN_REVIEW` applies only prior to completed adjudication).

---

## 9. Causal Link Status

* **Status**: **`NOT_ESTABLISHED`**.
* **Allowed Confidence Levels**: `DIRECTLY_OBSERVED`, `TELEMETRY_SUPPORTED`, `PLAUSIBLE_BUT_UNCONFIRMED`, `NOT_ESTABLISHED`.
* **Prohibited Claims**: The designations `CAUSED_BY_AI` and `PROVEN_CAUSAL` are strictly prohibited on benchmark data. A safety intervention followed by an incident in another zone does not establish causal Backfire without verified temporal-spatial mechanics.

---

## 10. Remaining Evidence Gaps & Next Steps

```
┌─────────────────────────────────┬───────────────────────────────┬─────────────────────────────────────────────┐
│ EVIDENCE DIMENSION              │ PUBLIC BENCHMARK STATUS       │ MANDATORY RESOLUTION PATH                   │
├─────────────────────────────────┼───────────────────────────────┼─────────────────────────────────────────────┤
│ 1. Continuous Recording Length  │ Truncated at 60.0 seconds     │ Extended multi-camera logging (15–30 min)   │
│ 2. Vehicle Dynamics Telemetry   │ Unavailable (no CAN bus)      │ Direct vehicle controller telemetry logging │
│ 3. Physical Illuminance (Lux)   │ Unavailable in release        │ NIST-traceable ground-plane lux sensors     │
│ 4. Ground-Truth Bounding Boxes  │ Withheld by NVIDIA for test   │ Independent dual-annotator human ground truth│
│ 5. Secondary Zone Demarcation   │ Approximate / optical only    │ In-situ total station geometric surveying   │
└─────────────────────────────────┴───────────────────────────────┴─────────────────────────────────────────────┘
```

### Final Milestone Declaration
```
SAFETY_BACKFIRE_GT         = PENDING_HUMAN_REVIEW
SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED
BASELINE_MODEL_H_STATUS    = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
```
Task V3.4-B REV2 is concluded. All screening infrastructure, window integrity validations, union registries, and blinded review packages are locked in place.
