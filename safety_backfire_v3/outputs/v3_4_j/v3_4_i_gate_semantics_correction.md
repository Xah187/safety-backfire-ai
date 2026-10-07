# V3.4-I Gate Semantics Correction Note

**Document Identifier**: V3.4-I-CORR-01  
**Target Milestone**: V3.4-I (Real-Data Shadow Execution)  
**Authoring Context**: Milestone V3.4-J Architecture & Specification Design  
**Date**: 2026-10-01  
**Status**: Formal Semantic Correction Artifact (Non-Mutating)

---

## 1. Executive Summary & Purpose

During Milestone **V3.4-I (Real-Data Shadow Execution)**, the Backfire State Machine was executed across 38 eligible real-world events from `Warehouse_026` and `Warehouse_027`. All 38 events exhibited `FIRST_BLOCKING_GATE = G2` due to complete secondary cross-aisle depth occlusion (`secondary_depth_visible == False`).

In the reporting and trace artifacts of V3.4-I, values were simultaneously recorded across all four gates (G1=PASS, G2=FAIL, G3=UNKNOWN, G4=FAIL) to provide an exhaustive forensic diagnostic of what the dataset contained.

**This correction note formally clarifies the operational semantics of sequential gate evaluation:**
1. In a sequential state machine where gates act as cascading preconditions ($G1 \to G2 \to G3 \to G4$), once a gate fails, execution **short-circuits**.
2. When `FIRST_BLOCKING_GATE = G2`, downstream gates in the live execution flow are formally:
   $$\mathbf{G3 = NOT\_EVALUATED}, \quad \mathbf{G4 = NOT\_EVALUATED}$$
3. The G4 confounder classifications recorded in V3.4-I (where 14 events had competitive confounders and 24 had trajectory discontinuities) represent **`PRIOR_FORENSIC_EVIDENCE`** derived from the historical V3.4-E audit, **not** live outputs of a gate reached during sequential execution.
4. In accordance with strict governance principles, original V3.4-I files are **not mutated**; this standalone artifact establishes the authoritative semantic interpretation for Milestone V3.4-J and all future milestones.

---

## 2. Comparison of Semantic Models

### Model A: Exhaustive Matrix Diagnostic (As presented in V3.4-I reporting)
In Model A, each gate is evaluated independently as an offline feature extractor:
- **G1 (Intervention)**: Evaluated independently $\to$ `PASS` (visual deceleration/halt verified).
- **G2 (Observability)**: Evaluated independently $\to$ `FAIL` (secondary depth occluded).
- **G3 (Risk Delta)**: Evaluated independently $\to$ `UNKNOWN` (depth occluded, true risk unavailable).
- **G4 (Causal & Confounders)**: Evaluated independently based on V3.4-E forensic review $\to$ `FAIL` (confounders present or vehicle stationary).

*Benefit*: Provides a complete forensic audit of all data channels in the existing dataset.  
*Limitation*: Can be misinterpreted as implying that the state machine traversed G2 and G3 before failing at G4.

### Model B: Sequential Short-Circuit Execution (Authoritative Specification for V3.4-J+)
In Model B, gates operate in strict temporal and logical dependency:
```
[Event Input]
      │
      ▼
┌───────────┐      PASS
│  Gate G1  │ ───────────────┐
└───────────┘                │
      │ FAIL                 ▼
      │                ┌───────────┐      PASS
      ▼                │  Gate G2  │ ───────────────┐
[PRIMARY_NEAR_MISS]    └───────────┘                │
                             │ FAIL                 ▼
                             │                ┌───────────┐      PASS
                             ▼                │  Gate G3  │ ───────────────┐
               [INSUFFICIENT_BACKFIRE_EVIDENCE] └───────────┘                │
                             │                      │ FAIL                 ▼
                             │                      ▼                ┌───────────┐
                     (Short-Circuit:       [PRIMARY_NEAR_MISS]       │  Gate G4  │
                    G3 = NOT_EVALUATED                               └───────────┘
                    G4 = NOT_EVALUATED)                                    │
                                                                           ▼
                                                                  [BACKFIRE_CANDIDATE]
```

Under Model B, because G2 evaluated to `FAIL` for all 38 events:
- **Gate 1**: `PASS` (38/38)
- **Gate 2**: `FAIL` (38/38) $\implies$ **Execution Short-Circuits Here**
- **Gate 3**: `NOT_EVALUATED` (38/38)
- **Gate 4**: `NOT_EVALUATED` (38/38)
- **Final Disposition**: `SHADOW_INSUFFICIENT_EVIDENCE` (38/38)

---

## 3. Disentangling Prior Forensic Evidence from Live Gate Results

To eliminate any ambiguity in future data acquisition designs:

| Gate | Live Sequential Status in V3.4-I | Source of Historical Data | Proper Semantic Designation |
| :--- | :--- | :--- | :--- |
| **G1** | `PASS` (38/38) | Monocular CCTV optical kinematics | `CURRENT_SHADOW_GATE_RESULT` |
| **G2** | `FAIL` (38/38) | Monocular CCTV rack occlusion mapping | `CURRENT_SHADOW_GATE_RESULT (BLOCKING)` |
| **G3** | `NOT_EVALUATED` | Unobservable interior depth | `UNAVAILABLE_SENSOR_CHANNEL` |
| **G4** | `NOT_EVALUATED` | V3.4-E manual CCTV forensic audit | `PRIOR_FORENSIC_EVIDENCE` |

### Why This Distinction Matters for V3.4-J:
If G4 were claimed as a live failure in an unobservable event, an engineer might mistakenly believe that solving confounders (G4) would allow detection, while ignoring the fact that secondary depth (G2) was never observable in the first place. 

By formally establishing that **G2 is the universal blocker and that G3/G4 were never operationally reached**, Milestone V3.4-J focuses its field instrumentation design where it matters most: **providing the physical line-of-sight and sensor telemetry required to unlock Gates G2 and G3**.

---

## 4. Final Governance Declaration

This correction note is an additive specification artifact. It does not modify production code, does not alter previous JSON manifests, does not adjust Model H parameters, and does not establish ground truth.

```yaml
CORRECTION_NOTE: V3_4_I_GATE_SEMANTICS_CORRECTION_COMPLETED
STATUS: ACTIVE_REFERENCE_SPECIFICATION
AFFECTS_PREVIOUS_FILES: FALSE (READ_ONLY_REFERENCE)
MANDATE_FOR_V3_4_J: ENFORCE_MODEL_B_SEQUENTIAL_SHORT_CIRCUIT
```
