# Safety Backfire AI — V3.4-B Safety Backfire Event Discovery & Ground-Truth Preparation Report

**Document Identifier**: `V3_4-B-EVENT-DISCOVERY-001`  
**Milestone**: `SAFETY_BACKFIRE_AI_V3.4-B`  
**Publication Date**: `2026-09-29T10:22:00Z`  
**Governance Scope**: Candidate Event Screening, Human Review Packaging & Ground-Truth Preparation  
**Authoritative Data Reference**: NVIDIA PhysicalAI-SmartSpaces ([Warehouse_026](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_026), [Warehouse_027](https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces/tree/main/MTMC_Tracking_2026/test/Warehouse_027))  
**Epistemic Standard**: Strict Separation of Algorithmic Candidate Generation from Human Adjudication  

---

## 1. Executive Summary & Governance Verdict

```
================================================================================
MILESTONE V3.4-B EVENT DISCOVERY & GROUND-TRUTH STATUS VERDICT
================================================================================
SAFETY_BACKFIRE_GT         = PENDING_HUMAN_REVIEW
SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED
CANDIDATE_EVENTS_FOUND     = 49
HUMAN_REVIEW_PACKAGES      = 3 GENERATED (Complete isolated review bundles)
SOURCE_A_STATUS            = VERIFIED_LOCAL (Warehouse_026 & Warehouse_027)
SOURCE_B_STATUS            = NOT_FOUND_LOCALLY (Mendeley; Halted without download)
MODEL_H_STATUS             = INVARIANT_UNTOUCHED (Parameters strictly frozen)
RAW_DATA_MODIFICATION      = NONE (Zero raw file alteration)
================================================================================
```

### 1.1 Core Methodological Principles
1. **Model as Candidate Generator Only**: The computer vision and tracking pipelines operate solely as a heuristic screening filter (`candidate_relevance_score`). The algorithms are strictly prohibited from generating ground-truth labels or deciding whether an event constitutes Safety Backfire.
2. **Ground Truth Requires Human Adjudication**: Ground-truth labels (`BACKFIRE`, `NO_BACKFIRE`, `AMBIGUOUS`) originate strictly from independent, multi-expert human review following the canonical protocol:
   $$\text{PRE} \longrightarrow \text{INTERVENTION} \longrightarrow \text{POST}$$
   $$\text{PRIMARY\_ZONE} \quad \text{vs} \quad \text{SECONDARY\_ZONE}$$
3. **Evidence Invariance**: Proximity does not equal risk transfer; risk reduction in one corridor does not equal Backfire; and post-intervention co-occurrence does not prove causality without verified physical evidence.

---

## 2. Data Sources & Provenance Classification

```
┌───────────────────────────────┬──────────────────────────────┬──────────────────────────┬───────────────────────────────────────────┐
│ SOURCE IDENTIFIER             │ NATURE                       │ PROVENANCE STATUS        │ GOVERNANCE ROLE                           │
├───────────────────────────────┼──────────────────────────────┼──────────────────────────┼───────────────────────────────────────────┤
│ NVIDIA Warehouse_026          │ 4-cam real warehouse (60s)   │ REAL_WORLD_TEST_CAPTURE  │ Primary candidate screening corpus        │
│ NVIDIA Warehouse_027          │ 7-cam real warehouse (60s)   │ REAL_WORLD_TEST_CAPTURE  │ Primary candidate screening corpus        │
│ Mendeley Workplace Dataset    │ 691 CCTV workplace clips     │ REAL_WORLD_WORKPLACE_VID │ NOT_FOUND_LOCALLY (Halted; zero download) │
│ NVIDIA SDG Synthetic Scenes   │ Omniverse simulated spaces   │ SYNTHETIC_DEVELOPMENT    │ PROHIBITED from safety backfire evidence  │
└───────────────────────────────┴──────────────────────────────┴──────────────────────────┴───────────────────────────────────────────┘
```

* **Source A (NVIDIA Test Captures)**: Fully verified in Milestone V3.4-A with $100\%$ cryptographic hash match across all 11 streams.
* **Source B (Mendeley Workplace Dataset)**: Audited and documented in [`V3_4_B_DATASET_GAP_REPORT.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/reports/V3_4_B_DATASET_GAP_REPORT.md). Zero unauthorized network downloads were initiated.

---

## 3. Candidate Event Discovery & Technical Inventory

The automated screening tool [`scripts/v3_4/discover_event_candidates.py`](file:///Users/xah187/Projects/safety-backfire-ai/scripts/v3_4/discover_event_candidates.py) parsed the validated observation ledgers ($N=45,836$ detections) across all 19,800 frames, clustering sustained spatial convergence between industrial vehicles and pedestrians.

### 3.1 Candidate Screening Statistics

```
┌──────────────────────────────┬────────────────────────┬────────────────────────┬────────────────────────┐
│ METRIC                       │ WAREHOUSE_026          │ WAREHOUSE_027          │ COMBINED TOTAL         │
├──────────────────────────────┼────────────────────────┼────────────────────────┼────────────────────────┤
│ Total Interaction Pairs      │ 3,068 frames           │ 5,758 frames           │ 8,826 frame pairs      │
│ Unique Camera-Track Clusters │ 44 clusters            │ 94 clusters            │ 138 clusters           │
│ Sustained Candidates (>=20f) │ 14 candidates          │ 35 candidates          │ 49 Candidate Events    │
│ Duration Range               │ 0.67s – 30.70s         │ 0.67s – 14.70s         │ 0.67s – 30.70s         │
│ Closest Spatial Approach     │ 115.1 px (~0.16m diff) │ 225.1 px (~0.47m diff) │ 115.1 px               │
│ Packaged for Human Review    │ 2 packages             │ 1 package              │ 3 Complete Packages    │
└──────────────────────────────┴────────────────────────┴────────────────────────┴────────────────────────┘
```

* Complete candidate inventory cataloged in machine-readable registry:  
  [`outputs/v3_4/candidates/candidate_events_registry.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/candidates/candidate_events_registry.json).

### 3.2 Candidate Relevance Scoring
The screening score is formally designated as **`candidate_relevance_score`** (range $[0.0, 1.0]$):
$$\text{Score} = 0.6 \cdot \max\left(0, 1 - \frac{d_{\min}}{600}\right) + 0.4 \cdot \min\left(1, \frac{N_{\text{frames}}}{150}\right)$$
* **Invariant**: The score measures operational saliency for human review, **not** the probability of Backfire.

---

## 4. Event Windowing & Spatial Zone Modeling

### 4.1 Temporal Window Structure
Each candidate event is framed into three distinct observation phases:
1. **`PRE` (Baseline Window)**: 5.0–10.0 seconds prior to convergence. Captures nominal speeds and pedestrian paths.
2. **`INTERVENTION` (Active Interval)**: Duration of spatial convergence, deceleration, or pedestrian path deflection.
3. **`POST` (Follow-on Window)**: 8.0–12.0 seconds post-convergence. Monitors vehicle departure, pedestrian resumption, and cross-zone propagation.
* **Window Definition Method**: `FIXED_OFFSET_BOUNDED_BY_STREAM`. (Constrained by the 60.0-second total stream length of the benchmark release).

### 4.2 Spatial Zone Delineation
* **Primary Zone**: The optical corridor where forklift and worker trajectories interact (e.g., `Camera_0002_CENTRAL_CORRIDOR`).
  - *Zone Status*: `PROVISIONAL_OPTICAL_CORRIDOR`
  - *Zone Source*: Calibrated homography ground-plane projection.
  - *Confidence*: `MEDIUM`
* **Secondary Zone**: The adjoining aisle, blind crossing, or rack interface (e.g., `Camera_0002_ADJACENT_RACK_AISLE`).
  - *Zone Status*: `PROVISIONAL_ADJACENT_CELL`
  - *Zone Source*: Multi-camera geometric overlap and proximity topology.
  - *Confidence*: `LOW`
  - *Mandatory Disclosure*: Without physical surveying total-station logs or architectural blueprints, secondary zone boundaries cannot be claimed as definitive physical ground truth.

---

## 5. Human Review Packages

Three complete, isolated evaluation packages were assembled in [`outputs/v3_4/candidates/`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4/candidates/):

```
outputs/v3_4/candidates/
├── CAND_Warehouse_026_008/
│   ├── before.mp4             # Derived review clip: PRE phase (F0000-F0000)
│   ├── intervention.mp4       # Derived review clip: INTERVENTION phase (F0001-F0430)
│   ├── after.mp4              # Derived review clip: POST phase (F0431-F0670)
│   ├── contact_sheet.jpg      # Multi-frame visual timeline summary
│   ├── metadata.json          # Temporal window boundaries & zone designations
│   ├── event_timeline.json    # Phase-by-phase event narrative
│   ├── model_observations.json# Object bounding boxes & distance telemetry
│   └── human_review_form.json # Independent evaluation rubric & consensus fields
├── CAND_Warehouse_026_009/
└── CAND_Warehouse_027_028/
```

### 5.1 Reviewer Blinding Protocol
* Human assessors review footage using `human_review_form.json` **without viewing Model H risk estimates, detector confidence scores, or automated Backfire classifications**.
* Reviewers independently score the **7 Canonical Safety Backfire Criteria**:
  1. *Clear Physical Intervention*: Visible braking, steering deflection, or worker avoidance.
  2. *Measurable Pre-Intervention Risk*: Hazardous proximity in the primary corridor.
  3. *Primary Risk Mitigation*: Verification that primary hazard was addressed.
  4. *Secondary Risk Escalation*: Measurable hazard increase in adjacent zone.
  5. *Causal Mechanism*: Concrete spatial-temporal link connecting primary action to secondary hazard.
  6. *Independent Objective Evidence*: Grounded in physical telemetry rather than inference.
  7. *Multi-Expert Consensus*: Agreement across at least two independent safety assessors.

---

## 6. Ground-Truth Schema & Epistemic Controls

The project schema [`schemas/v3_4/safety_backfire_event_gt.schema.json`](file:///Users/xah187/Projects/safety-backfire-ai/schemas/v3_4/safety_backfire_event_gt.schema.json) was formally deployed with rigorous constraints:

* **Evidence Quality Levels**: `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`. (Prohibited: `CERTIFIED`, `PROVEN_SAFE`).
* **Causal Link Confidence**: `DIRECTLY_OBSERVED`, `TELEMETRY_SUPPORTED`, `PLAUSIBLE_BUT_UNCONFIRMED`, `NOT_ESTABLISHED`. (Prohibited: `CAUSED_BY_AI`).
* **Adjudicated Labels**: `BACKFIRE`, `NO_BACKFIRE`, `AMBIGUOUS`, `PENDING_HUMAN_REVIEW`.

---

## 7. Data Gaps in Public Benchmark Footage

While the NVIDIA test footage provides real-world physical warehouse streams, critical evidence dimensions are missing for formal safety validation:

```
┌─────────────────────────────────┬─────────────────────────────┬───────────────────────────────────────────────────┐
│ REQUIRED EVIDENCE DIMENSION     │ OBSERVED IN BENCHMARK       │ FORMAL VALIDATION IMPACT                          │
├─────────────────────────────────┼─────────────────────────────┼───────────────────────────────────────────────────┤
│ Stream Temporal Duration        │ 60.0 seconds per camera     │ Insufficient for post-intervention hazard decay   │
│ Vehicle CAN-bus Telemetry       │ Not collected / unavailable │ Braking & deceleration cannot be confirmed        │
│ Machine-to-Machine Triggers     │ Unknown / passive CCTV      │ Emergency stop activation cannot be verified      │
│ In-situ Physical Surveying      │ Dataset-provided matrices   │ Ground-plane accuracy unverified by total station │
│ Physical Lux Telemetry          │ Not available in release    │ Model H returns INPUT_INSUFFICIENT formally       │
│ Multi-Corridor Synchronization  │ Visual camera sync only     │ Secondary zone hazard propagation unconfirmed     │
└─────────────────────────────────┴─────────────────────────────┴───────────────────────────────────────────────────┘
```

---

## 8. Final Status Declaration

In strict compliance with Milestone V3.4-B Governance:

```
SAFETY_BACKFIRE_GT         = PENDING_HUMAN_REVIEW
SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED
```

Candidate events have been systematically discovered, cataloged, and packaged into isolated review bundles. Until dual-expert human adjudication is executed and corroborated by in-situ physical telemetry, no claim of verified Safety Backfire may be asserted.
