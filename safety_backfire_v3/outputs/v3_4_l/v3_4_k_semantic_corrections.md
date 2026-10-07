# V3.4-K Semantic Corrections & Test Count Reconciliation

**Document Identifier**: V3.4-K-CORR-01  
**Target Milestone**: V3.4-K (Field Pilot Readiness & Instrumentation Verification)  
**Authoring Context**: Milestone V3.4-L Field Pilot Execution Design  
**Date**: 2026-10-02  
**Status**: Authoritative Semantic Clarification & Audit Reconciliation (Non-Mutating)

---

## 1. Executive Summary & Purpose

Milestone **V3.4-K** successfully verified the pre-pilot multi-modal instrumentation and data quality pipeline using synthetic deterministic replay. To preserve absolute epistemic rigor, prevent misleading interpretations of verification metrics, and establish clean engineering baselines for physical deployment, this document records five mandatory semantic corrections and reconciliations:

1. **Test Count Reconciliation (`TEST_COUNT_RECONCILIATION`)**: Detailed breakdown and reconciliation of the test counters across fault injections, cryptographic audits, blinding tests, and mandatory success conditions.
2. **Component Sync Limit vs. Composite Sync Budget Separation**: Distinct operational separation between component-level latency allocations ($18.0\text{ ms}$) and system-level maximum design targets ($33.3\text{ ms}$).
3. **De-coupling of Life-Cycle Readiness States**: Clear bifurcation ensuring ground-truth adjudication is not falsely treated as a blocker to physical sensor capture.
4. **Epistemic Terminology Replacement**: Permanent replacement of the term "100% accuracy" with "100% TEST PASS RATE" across all verification artifacts.
5. **Threshold Epistemic Classification**: Formal classification of all numerical engineering thresholds as `DESIGN_REQUIREMENT` or `CURRENT_ACCEPTANCE_TARGET` rather than physical universal constants.

In accordance with locked governance directives, original V3.4-K artifacts remain **unmutated**; this standalone correction note serves as the binding reference for Milestone V3.4-L and all subsequent field operations.

---

## 2. Test Count Reconciliation (`TEST_COUNT_RECONCILIATION`)

In the executive summary of the V3.4-K report, test metrics were grouped into categories that require explicit accounting reconciliation against the underlying JSON artifacts:

### Detailed Inventory of Verification Executions:

1. **Pre-Ingestion Fault Injection Suite (`data_quality_gate_results.json`)**:
   - Time & Clock Synchronization: **8 tests** (Cases K01 through K08).
   - Camera Health & Optical Integrity: **6 tests** (CAM_01 through CAM_06).
   - Vehicle Telemetry Health: **6 tests** (TELEM_01 through TELEM_06).
   - Secondary Zone Depth & Observability: **3 tests** (SEC_01 through SEC_03).
   - Spatial Calibration & Alignment: **5 tests** (CALIB_01 through CALIB_05).
   - Facility Geometry & Zone Mapping: **5 tests** (GEOM_01 through GEOM_05).
   - Dynamic Event Window Completeness: **4 tests** (COMP_01 through COMP_04).
   - **Subtotal Fault Injection Tests**: $\mathbf{37\text{ tests}}$ (37 passed / 37 executed = 100% pass rate).

2. **Cryptographic Provenance & Tamper Suite (`provenance_integrity_results.json`)**:
   - Single-byte payload modification (K-TAMPER-01): **1 test**.
   - Previous-hash pointer modification (K-TAMPER-02): **1 test**.
   - Intermediate event deletion (K-TAMPER-03): **1 test**.
   - Chronological event reordering (K-TAMPER-04): **1 test**.
   - **Subtotal Provenance Tamper Tests**: $\mathbf{4\text{ tests}}$ (4 detected / 4 executed = 100%).

3. **Reviewer Blinding & Isolation Suite (`reviewer_blinding_test_results.json`)**:
   - Reviewer package export sanitization audit: **1 test**.
   - Deliberate model string leak injection & trapping test: **1 test**.
   - Model H coefficient perturbation isolation test: **1 test**.
   - **Subtotal Blinding & Isolation Tests**: $\mathbf{3\text{ tests}}$ (3 passed / 3 executed = 100%).

4. **Pipeline Determinism & Recovery (`event_package_validation_results.json`)**:
   - Dual-run bit-identical replay reproducibility test: **1 test**.
   - Sensor disconnect recovery tests (Camera, CAN, Clock): **3 tests**.
   - **Subtotal Determinism & Recovery Tests**: $\mathbf{4\text{ tests}}$ (4 passed / 4 executed = 100%).

5. **Mandatory Success Conditions Meta-Audit**:
   - Verification of the 10 top-level governance criteria: **10 meta-tests** (10/10 passed).

### Summary Reconciliation Table:
$$\text{Total Atomic Test Invocations} = 37 + 4 + 3 + 4 + 10 = \mathbf{58\text{ Verifications}}$$
All 58 verifications completed with zero failures (`Pass Rate: 100.0%`).

---

## 3. Component Sync Limit vs. Composite Sync Budget Separation

In Milestone V3.4-K, the synchronization budget was audited into an allocated sum ($18.0\text{ ms}$) and an unallocated margin ($15.3\text{ ms}$) within the $33.3\text{ ms}$ system design target.

**Operational Rule for Field Pilot**:
1. **`COMPONENT_SYNC_LIMIT`**: Each sensor channel possesses an individual allocation:
   - Camera hardware trigger jitter: $\le 2.0\text{ ms}$
   - CAN bus gateway latency: $\le 5.0\text{ ms}$
   - Secondary sensor network latency: $\le 8.0\text{ ms}$
   - OS inter-process jitter: $\le 3.0\text{ ms}$
2. **`COMPOSITE_SYNC_BUDGET` / `SYSTEM_MAX_DESIGN_TARGET`**: Maximum allowable end-to-end multi-modal skew across all streams: $\mathbf{\le 33.3\text{ ms}}$ (1 frame at 30 fps).
3. **`UNALLOCATED_BUDGET`**: $\mathbf{15.3\text{ ms}}$ held as an engineering reserve.
4. **Enforcement Rule**: A single component exceeding its allocated limit (e.g. camera offset $> 2.0\text{ ms}$ or CAN offset $> 5.0\text{ ms}$) **MUST NOT** be automatically marked clean `PASS` simply because composite skew remains below $33.3\text{ ms}$. It must trigger `PARTIALLY_READY` with an explicit component warning flag.

---

## 4. Separation of Life-Cycle Readiness States

Milestone V3.4-K's readiness taxonomy is refined into a three-tier operational separation:

```
[ PHYSICAL COMMISSIONING ]
             │ (Pre-Capture Gates C1-C6 PASS)
             ▼
┌────────────────────────────────────────┐
│  INSTRUMENTATION_READY_FOR_CAPTURE     │  <-- Permits physical vehicle runs & sensor recording
└──────────────────┬─────────────────────┘
                   │ (Data Captured + Post-Capture Gates D1-D6 PASS)
                   ▼
┌────────────────────────────────────────┐
│      DATASET_READY_FOR_REVIEW          │  <-- Permits human expert adjudication export
└──────────────────┬─────────────────────┘
                   │ (Dual-Blind Human Review Completed + Signed)
                   ▼
┌────────────────────────────────────────┐
│          VALIDATION_READY              │  <-- Permits safety model benchmark evaluation
└────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Capture Decoupling**:  
> Establishing ground truth (`VALIDATION_READY`) is **NOT** a prerequisite for starting physical pilot recording (`INSTRUMENTATION_READY_FOR_CAPTURE`). Recording produces raw evidence packages; ground truth is established downstream.

---

## 5. Terminology Correction: "Test Pass Rate" vs. "Accuracy"

- **Deprecated Formulation**: "100% accuracy in fault tests".
- **Authoritative Formulation**: **"100% TEST PASS RATE"** or **"100% LOGICAL VERIFICATION MATCH"**.
- **Rationale**: "Accuracy" is a statistical perception metric evaluating machine learning predictions against ground truth labels. Applying it to deterministic software unit tests and fault injection suites is an epistemic category error.

---

## 6. Numerical Threshold Classification

All engineering thresholds specified across V3.4-J, V3.4-K, and V3.4-L are formally classified:

| Engineering Parameter | Value | Epistemic Classification | Field Operational Context |
| :--- | :---: | :--- | :--- |
| **Camera Trigger Jitter** | $2.0\text{ ms}$ | `DESIGN_REQUIREMENT` | PTP hardware timestamping threshold |
| **CAN Gateway Latency** | $5.0\text{ ms}$ | `DESIGN_REQUIREMENT` | Hardware CAN-to-Ethernet buffer target |
| **Secondary Network Latency** | $8.0\text{ ms}$ | `DESIGN_REQUIREMENT` | UDP LiDAR packet arrival budget |
| **Allocated Component Sum** | $18.0\text{ ms}$ | `DESIGN_REQUIREMENT` | Sum of individual sensor allocations |
| **Composite Skew Target** | $33.3\text{ ms}$ | `CURRENT_ACCEPTANCE_TARGET` | 1 video frame interval at 30 fps |
| **Reprojection Error Limit** | $1.5\text{ px}$ | `CURRENT_ACCEPTANCE_TARGET` | Multi-camera homography target |
| **Propagation Latency ($\tau_{\max}$)** | $2.0\text{ s}$ | `CURRENT_SPECIFICATION_CONSTRAINT` | Dynamic backfire time horizon |
| **Minimum Pre-Window** | $3.0\text{ s}$ | `DESIGN_REQUIREMENT` | Approach kinematic baseline duration |
| **Minimum Post-Window** | $4.0\text{ s}$ | `DESIGN_REQUIREMENT` | Secondary hazard emergence window |

*Under no circumstances are these parameters to be cited as unalterable physical truths.*

---

```yaml
SEMANTIC_CORRECTION_STATUS: V3_4_K_SEMANTIC_CORRECTIONS_COMPLETED
AFFECTS_HISTORICAL_FILES: FALSE (READ_ONLY_REFERENCE)
MANDATE_FOR_V3_4_L: BINDING_ENGINEERING_SPECIFICATION
```
