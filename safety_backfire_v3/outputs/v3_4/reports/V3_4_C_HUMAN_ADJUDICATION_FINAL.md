# Milestone V3.4-C — Final Human Adjudication & Ground Truth Architecture Report

**Document ID:** `V3_4_C_HUMAN_ADJUDICATION_FINAL`  
**Milestone Version:** V3.4-C  
**Timestamp:** 2026-09-30  
**Repository:** `safety-backfire-ai`  
**Current Governance State:** `SAFETY_BACKFIRE_GT = PENDING_HUMAN_REVIEW`  
**Perception & Causal Status:** `SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED`

---

## 1. Executive Summary & Epistemic Boundaries

Milestone **V3.4-C** establishes the formal **Independent Human Adjudication Infrastructure** for the Safety Backfire AI framework. This milestone completes the transition from automated candidate discovery (V3.4-B) to an uncompromised, double-blind human ground-truth protocol.

### Fundamental Governance Principles Enforced

1. **Absolute Agent Non-Interference:** The AI agent is strictly forbidden from inventing, guessing, or auto-populating `BACKFIRE`, `NO_BACKFIRE`, or `AMBIGUOUS` decisions. Any candidate lacking authentic human assessment remains strictly `PENDING_HUMAN_REVIEW`.
2. **Double-Blind Review Isolation:** Reviewer 1 and Reviewer 2 evaluate candidates independently. Neither reviewer has access to AI relevance scores, YOLO bounding boxes, ByteTrack identifiers, Model H parameters, or the peer reviewer's entries.
3. **No Premature Model Performance Metrics:** Calculation of Precision, Recall, F1-Score, Sensitivity, Specificity, and False Alarm Rate is strictly barred until human adjudication is completed.
4. **Physical & Mathematical Model Invariance:** Model H remains frozen ($k_0 = 2.40$, $\beta_d = 0.08$, $\beta_l = 0.12$, $\beta_{\text{pitch}} = 0.22$). Raw video captures are maintained read-only.

---

## 2. Candidate Pool & Union Event Inventory

The candidate pool under adjudication originates from the rigorous union of AI-generated candidates and blind human screening:

$$\text{UNION\_EVENT\_POOL} = 51$$

```
AI Candidates (V3.4-B)                 : 49
Human Independent Screening (V3.4-B REV2): 5
Overlapping Identified Events          : 3
--------------------------------------------------
Total Distinct Union Events            : 51
```

### Event Provenance Hierarchy

To avoid circular reasoning ($\text{Model} \rightarrow \text{Event GT}$), the framework enforces a 4-tier event classification:

$$\text{AI\_CANDIDATE} \longrightarrow \text{HUMAN\_DISCOVERED} \longrightarrow \text{UNION\_CANDIDATE} \longrightarrow \text{HUMAN\_ADJUDICATED\_EVENT}$$

No candidate is deleted from the union registry (`outputs/v3_4/candidates/union_events_registry.json`).

---

## 3. Window Integrity & Eligibility Breakdown

Every union candidate underwent a strict temporal window integrity audit based on three sequential phases:

$$\text{PRE-INTERVENTION} \quad \longrightarrow \quad \text{INTERVENTION} \quad \longrightarrow \quad \text{POST-INTERVENTION}$$

```
+------------------------------------+-------+-----------------------------------------------------------+
| Eligibility Category               | Count | Operational Status                                        |
+------------------------------------+-------+-----------------------------------------------------------+
| ELIGIBLE_EVENTS (WINDOW_VALID=TRUE)| 38    | Review packages initialized with derived MP4 video clips  |
| INELIGIBLE_EVENTS (WINDOW_VALID=F) | 13    | status: INELIGIBLE_WINDOW (excluded from causal adjudication) |
+------------------------------------+-------+-----------------------------------------------------------+
| TOTAL UNION CANDIDATES             | 51    | 100% cataloged and SHA256 hashed                         |
+------------------------------------+-------+-----------------------------------------------------------+
```

### Invalidation Root Causes for Ineligible Events ($N=13$)

The 13 ineligible events (e.g., `UNION_CAND_Warehouse_026_001`, `UNION_CAND_Warehouse_026_002`, `UNION_CAND_Warehouse_026_008`) were invalidated for specific empirical defects:
- Truncation at stream start ($F_0 < 30$, baseline duration insufficient for baseline risk estimation).
- Truncation at stream conclusion ($F_{\text{end}} > \text{Max Frames} - 30$, preventing post-intervention observation).
- Overlapping pre- and intervention boundaries ($F_{\text{start}} = F_{\text{end}}$).

These 13 events are preserved in the archive under `outputs/v3_4/adjudication/<event_id>/` with metadata marked `INELIGIBLE_WINDOW` and `EXCLUDED_FROM_ADJUDICATION`, guaranteeing complete data provenance without contaminating causal adjudication.

---

## 4. Completed vs. Unresolved Reviews

```
+------------------------------------+-------+--------------------------------------------------+
| Review Component                   | Count | Status                                           |
+------------------------------------+-------+--------------------------------------------------+
| REVIEWER_1_COMPLETED               | 0     | PENDING_HUMAN_REVIEW (awaiting human assessor 1) |
| REVIEWER_2_COMPLETED               | 0     | PENDING_HUMAN_REVIEW (awaiting human assessor 2) |
| BOTH_REVIEWERS_COMPLETED           | 0     | PENDING_HUMAN_REVIEW                             |
| UNRESOLVED_ELIGIBLE_REVIEWS        | 38    | Awaiting human review                            |
+------------------------------------+-------+--------------------------------------------------+
```

As specified in the absolute governance rules, the AI agent has marked all unsubmitted review forms as `PENDING_HUMAN_REVIEW`. No automated decisions have been injected.

---

## 5. Double-Blind Review Architecture & Blinding Integrity

For each of the 38 eligible events, a self-contained review package has been generated at:
`outputs/v3_4/adjudication/<union_event_id>/`

```
outputs/v3_4/adjudication/UNION_CAND_Warehouse_027_001/
├── review_metadata.json       <- Source video provenance, temporal frames, spatial zones
├── reviewer_1_form.json       <- Independent Form for Reviewer 1
├── reviewer_2_form.json       <- Completely Isolated Form for Reviewer 2
├── adjudication_form.json     <- Third-Party Adjudication Form (disagreements)
├── before.mp4                 <- Extracted pre-intervention clip (baseline)
├── intervention.mp4           <- Extracted safety intervention clip
└── after.mp4                  <- Extracted post-intervention clip (secondary outcome)
```

### Blinding Verification

Every package was audited by `scripts/v3_4/validate_adjudication.py` to ensure:
- **Zero AI Detections:** No YOLO bounding boxes, confidences, or class probabilities.
- **Zero AI Tracking:** No ByteTrack tracking IDs or velocity vectors.
- **Zero AI Relevance:** No automated relevance scores or candidate rankings.
- **Zero Model H:** No $H(\mathbf{x})$, $k_0$, or risk gradient displays.
- **Zero Agent Recommendations:** No suggested or pre-filled labels.
- **Reviewer Isolation:** `reviewer_2_form.json` contains no fields or references to Reviewer 1.

---

## 6. Adjudication Protocol & Disagreement Handling

### Form Evaluation Criteria

Both Reviewer 1 and Reviewer 2 evaluate the physical/visual evidence across 7 structured criteria:

```
1. intervention_visible          : YES / NO / UNKNOWN
2. primary_risk_present          : YES / NO / UNKNOWN
3. primary_risk_reduced          : YES / NO / UNKNOWN
4. secondary_risk_changed        : YES / NO / UNKNOWN
5. causal_mechanism_observed     : YES / NO / UNKNOWN
6. independent_evidence_present  : YES / NO / UNKNOWN
7. evidence_quality              : HIGH / MEDIUM / LOW / UNKNOWN
```

*(Note: The token `PASS` is strictly prohibited in criteria evaluations).*

### Inter-Rater Consensus & Disagreement Protocol

```
+-------------------------------------------------------+
|                 REVIEWER 1 SUBMISSION                 |
|               (BACKFIRE / NO_BACKFIRE / AMBIGUOUS)     |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|                 REVIEWER 2 SUBMISSION                 |
|               (BACKFIRE / NO_BACKFIRE / AMBIGUOUS)     |
+---------------------------+---------------------------+
                            |
           +----------------+----------------+
           |                                 |
           v                                 v
    [R1 == R2]                          [R1 != R2]
           |                                 |
           |                                 v
           |                      disagreement = TRUE
           |                                 |
           |                                 v
           |                      MANDATORY HUMAN ADJUDICATOR
           |                      (Third Expert Reviewer)
           |                      - Inspects R1 & R2 justifications
           |                      - Determines final label
           |                                 |
           +----------------+----------------+
                            |
                            v
               FINAL ADJUDICATED LABEL
               - BACKFIRE
               - NO_BACKFIRE
               - AMBIGUOUS
```

When Reviewer 1 and Reviewer 2 disagree, **no majority voting or automated resolution is permitted**. The adjudication form (`adjudication_form.json`) must be filled by a designated third human adjudicator.

---

## 7. Ground Truth Event Definitions

### Definition: BACKFIRE

A candidate may receive the final label `BACKFIRE` **only if** all seven conditions are fulfilled:
1. **Clear Safety Intervention:** A distinct, observable action was taken to mitigate a primary risk.
2. **Pre-Existing Primary Risk:** Observable hazard present in the primary zone prior to intervention.
3. **Primary Hazard Attenuation:** Reduction or displacement of the primary hazard following intervention.
4. **Independent Secondary Risk Emergence:** Observable elevation or creation of a new hazard in an adjacent or secondary zone.
5. **Plausible Spatiotemporal Linkage:** Plausible temporal delay and spatial reach connecting the primary intervention to the secondary hazard.
6. **Independence from AI Detectors:** Verdict established purely on visual and physical evidence without reliance on detector confidence or Model H.
7. **Complete Human Protocol Verification:** Adjudicated by two concordant human reviewers or an expert adjudicator.

*If spatiotemporal or causal evidence is insufficient to confirm linkage, the event must be labeled `AMBIGUOUS`.*

### Definition: NO_BACKFIRE

A candidate may receive the final label `NO_BACKFIRE` **only if**:
1. A clear safety intervention occurred.
2. The primary outcome was observable.
3. No observable emergence or transfer of risk occurred in the secondary zone throughout the observation window.
4. Human review was fully completed.

*Crucial Caveat:* **Inability to observe the secondary zone due to camera blind spots, occlusion, or poor lighting does NOT equal `NO_BACKFIRE`**. Such events must be classified as `AMBIGUOUS`.

---

## 8. Causal Link Classification

The causal link between intervention and secondary risk is classified according to four strict categories:

```
+-----------------------------+--------------------------------------------------------------------------+
| Category                    | Definition                                                               |
+-----------------------------+--------------------------------------------------------------------------+
| DIRECTLY_OBSERVED           | Unbroken visual line of sight tracing intervention to secondary consequence |
| TELEMETRY_SUPPORTED         | Corroborated by physical telemetry (lux, speed, floor load)               |
| PLAUSIBLE_BUT_UNCONFIRMED   | Mechanistically consistent but visual trace partially occluded           |
| NOT_ESTABLISHED             | No verifiable causal chain or review pending                             |
+-----------------------------+--------------------------------------------------------------------------+
```

**Prohibited Causal Descriptors:** `CAUSED_BY_AI` and `PROVEN_CAUSAL` are formally barred from the ontology.

Current status across all events: `NOT_ESTABLISHED`.

---

## 9. Quality Control Validation Suite

The quality control script `scripts/v3_4/validate_adjudication.py` automates verification against nine failure modes:

```bash
.venv/bin/python scripts/v3_4/validate_adjudication.py
```

### Verification Checklist Results

```
[PASS] 1. Missing Reviewer Prevention      : Validated (no orphan submissions permitted)
[PASS] 2. Duplicate Event Prevention      : Validated (0 duplicates in registry or packages)
[PASS] 3. Missing Reviewer Label Check    : Validated (strict enums enforced)
[PASS] 4. Unauthorized Final Label Bar   : Validated (only BACKFIRE/NO_BACKFIRE/AMBIGUOUS)
[PASS] 5. Reviewer 2 Isolation            : Validated (0 cross-reviewer leakage)
[PASS] 6. Invalid Event ID Detection      : Validated (all packages match union registry)
[PASS] 7. Hash Integrity Audit            : Validated (source & package SHA256 verified)
[PASS] 8. Window Eligibility Enforcement  : Validated (13 ineligible events strictly excluded from GT)
[PASS] 9. Evidence Quality Verification   : Validated (HIGH/MEDIUM/LOW/UNKNOWN schema verified)
[PASS] 10. AI Blinding Verification       : Validated (0 AI metrics present in forms)
```

---

## 10. Empirical Limitations of Public CCTV Benchmarks

Ground truth development on public surveillance data (NVIDIA MTMC Warehouse 026/027) exhibits structural physical limitations:

1. **Fixed Perspective Blind Spots:** Static ceiling-mounted cameras have substantial blind spots behind storage racks and structural columns. A secondary hazard developing behind a rack cannot be verified as `NO_BACKFIRE` and must remain `AMBIGUOUS`.
2. **Absence of Ground Telemetry:** Public datasets do not contain synchronized physical telemetry (lux readings, AGV floor-pressure sensors, acoustic warnings).
3. **Observational vs. Interventional Data:** The footage contains naturally occurring warehouse activity rather than controlled, protocolized safety interventions.
4. **Provisional Secondary Zones:** In cameras lacking 3D multi-camera homography, secondary zones are designated provisionally based on camera geometry.

---

## 11. Final Milestone Status & Governance Declaration

```
======================================================================
  FINAL GOVERNANCE STATUS — MILESTONE V3.4-C
======================================================================
  UNION_EVENT_POOL                   : 51
  ELIGIBLE_FOR_ADJUDICATION          : 38
  INELIGIBLE_WINDOW (EXCLUDED)       : 13

  REVIEWER_1_COMPLETED               : 0
  REVIEWER_2_COMPLETED               : 0
  AGREEMENTS                         : 0
  DISAGREEMENTS                      : 0

  BACKFIRE                           : 0
  NO_BACKFIRE                        : 0
  AMBIGUOUS                          : 0
  PENDING_HUMAN_REVIEW               : 38

  SAFETY_BACKFIRE_GT                 = PENDING_HUMAN_REVIEW
  SAFETY_BACKFIRE_VALIDATION         = NOT_ESTABLISHED
  MODEL_H_STATE                      = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
  RAW_DATA_STATUS                    = READ_ONLY (SHA256 VERIFIED)
======================================================================
```

**Declaration:** Milestone V3.4-C infrastructure is fully operational, validated, and ready for human subject review. In compliance with the Stop Condition, no automated classification was executed, no performance metrics were generated, and Model H remains unexecuted.
