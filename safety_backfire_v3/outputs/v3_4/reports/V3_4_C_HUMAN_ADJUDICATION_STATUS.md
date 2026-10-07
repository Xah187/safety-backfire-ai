# V3.4-C Human Adjudication Status Report

**Milestone:** V3.4-C — Human Adjudication & Safety Backfire Ground Truth  
**Status Date:** 2026-09-30  
**Governance State:** `PENDING_HUMAN_REVIEW`  
**Quality Control Status:** `ALL_CHECKS_PASSED` (via `scripts/v3_4/validate_adjudication.py`)

---

## 1. Executive Summary & Event Pool Counts

| Metric Category | Metric Identifier | Count | Verification / Rule |
| :--- | :--- | :--- | :--- |
| **Candidate Pool** | **TOTAL_UNION_EVENTS** | **51** | All union events preserved from `union_events_registry.json` |
| | **ELIGIBLE_EVENTS** | **38** | `WINDOW_VALID = TRUE` (complete baseline, intervention, post window) |
| | **INELIGIBLE_EVENTS** | **13** | `WINDOW_VALID = FALSE` (`status: INELIGIBLE_WINDOW`; excluded from causal determination) |
| **Reviewer 1 Progress** | **REVIEWER_1_COMPLETED** | **0** | Awaiting independent human assessor reviews |
| **Reviewer 2 Progress** | **REVIEWER_2_COMPLETED** | **0** | Awaiting independent human assessor reviews (strict double-blind isolation) |
| **Inter-Rater Consensus** | **AGREEMENTS** | **0** | Requires both Reviewer 1 & Reviewer 2 submissions |
| | **DISAGREEMENTS** | **0** | Triggers mandatory third-party adjudication form |
| **Adjudicated Final Labels** | **BACKFIRE** | **0** | Strict 7-criteria causal requirement |
| | **NO_BACKFIRE** | **0** | Strict 4-criteria non-backfire requirement |
| | **AMBIGUOUS** | **0** | Insufficient telemetry / occluded secondary zone |
| | **PENDING** | **38** | All eligible events in `PENDING_HUMAN_REVIEW` state |

---

## 2. Event Invariance & Epistemic Hierarchy

The system strictly enforces the provenance sequence:
$$\text{AI\_CANDIDATE} \rightarrow \text{HUMAN\_DISCOVERED} \rightarrow \text{UNION\_CANDIDATE} \rightarrow \text{HUMAN\_ADJUDICATED\_EVENT}$$

1. **Absolute Agent Prohibition:** The Agent is strictly prohibited from populating or guessing `BACKFIRE`, `NO_BACKFIRE`, or `AMBIGUOUS` on behalf of human reviewers.
2. **Review Blinding:** Zero detector confidences, zero bounding boxes, zero ByteTrack IDs, and zero Model H calculations are presented in any review package.
3. **Double-Blind Isolation:** `reviewer_2_form.json` contains zero references or visibility into Reviewer 1 notes or decisions.
4. **Frozen Model H Parameters:**
   - $k_0 = 2.40$
   - $\beta_d = 0.08$
   - $\beta_l = 0.12$
   - $\beta_{\text{pitch}} = 0.22$
5. **No Model Performance Metrics:** Precision, Recall, F1, Sensitivity, Specificity, and False Alarm Rate are **prohibited** until human ground truth is officially established.

---

## 3. Package Inventory & Verification Hash

- **Adjudication Root:** `outputs/v3_4/adjudication/` (51 directories generated)
- **Derived Video Packages:** 38 eligible packages contain derived clips (`before.mp4`, `intervention.mp4`, `after.mp4`)
- **Raw Data Integrity:** Read-only, uncompressed, un-cropped, SHA256 validated
- **Ground Truth Container:** `outputs/v3_4/ground_truth/safety_backfire_event_gt.json` (0 completed records; status `PENDING_HUMAN_REVIEW`)
