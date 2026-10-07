# V3.4-I — Real-Data Shadow Execution Report

**Milestone Identifier**: V3.4-I  
**Execution Context**: Read-Only Real-Data Shadow Execution & Evidence Availability Audit  
**Evaluation Mode**: Deterministic Shadow Execution (No Label Generation, No Model Validation)  
**Target Repository**: `safety-backfire-ai`  
**Execution Date**: 2026-10-01  
**Governance State**: `HUMAN_REVIEW = BYPASSED` | `SAFETY_BACKFIRE_GT = NOT_ESTABLISHED` | `SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED` | `PERCEPTION_METRICS = NOT_ESTABLISHED` | `MODEL_H = FROZEN_INVARIANT` | `PRODUCTION_MODEL = UNCHANGED` | `REAL_WORLD_BACKFIRE_VALIDATION = NOT_ESTABLISHED`

---

## Executive Summary

Milestone **V3.4-I** performs a strictly **read-only shadow execution** of the V3.4-H / V3.4-G Backfire State Machine across real warehouse video datasets (`Warehouse_026` and `Warehouse_027`). The primary objective of this audit is not to evaluate algorithmic precision or recall, nor to generate ground truth labels, but rather to empirically test the **Evidence Contract** against field operational conditions:
1. Is the multi-stage Evidence Contract executable on real monocular CCTV warehouse footage?
2. What is the **First Blocking Gate** preventing candidate transition?
3. What required evidence is physically available versus missing?
4. Can secondary risk delta ($\Delta R_{\text{sec}}$) be computed under existing sensor topologies?
5. Does any event from the 38 eligible historical interactions qualify as a candidate under the formal evidence contract?

### Key Empirical Findings:
- **`SHADOW_BACKFIRE_CANDIDATE = 0`**: Under the available observable evidence, zero backfire candidates were generated. *(Note: This reflects available line-of-sight and sensor constraints; it does not claim that safety backfire never occurs in warehouse logistics).*
- **`SHADOW_INSUFFICIENT_EVIDENCE = 38` (100%)**: All 38 eligible events were routed to insufficient evidence due to visual occlusion of secondary cross-aisle depths.
- **`FIRST_BLOCKING_GATE = G2` (100%)**: In all 38 events, Gate 2 (Observability) was the immediate first blocking gate. Monocular ceiling cameras capture central transit lanes, but pallet racks completely occlude the interior depth of adjacent cross-aisles (`secondary_depth_visible == False` in 38/38 events).
- **`Gate 3 (Secondary Risk Delta) = UNKNOWN` (100%)**: Because the interior depth behind the racks is occluded, true physical hazard states ($R_{\text{sec\_PRE}}$, $R_{\text{sec\_POST}}$) are completely unavailable. In accordance with V3.4-G tri-state logic, G3 outputs `UNKNOWN` (not 0, not FAIL).
- **`Gate 4 (Causal Isolation) = FAIL` (100%)**: 14 events failed due to competitive independent confounders (worker crowd arrivals or external forklifts); 24 events failed due to the absence of a continuous physical trajectory into the secondary zone (vehicles stopped or cleared without hazard redirection).

---

## 1. Scope

Milestone V3.4-I executes the Backfire State Machine in shadow mode on the 38 eligible real-world warehouse events from the Union Events Registry:
- **Read-Only Access**: Video streams, detector tracks, proximity metrics, temporal window bounds, and previous audit metadata were ingested without alteration.
- **Zero Label Mutation**: No ground-truth labels were generated; no human reviewer forms were modified; verified ground-truth records remain exactly 0.
- **No Performance Metrics**: Precision, Recall, F1, Sensitivity, Specificity, FAR, and Accuracy are strictly excluded.
- **Separation of Concerns**: Results are formally designated with the `SHADOW_` prefix to guarantee complete epistemic separation from ground truth.

---

## 2. Governance State

The locked governance directives established throughout Milestone V3.4 remain strictly invariant:
```yaml
HUMAN_REVIEW: BYPASSED
SAFETY_BACKFIRE_GT: NOT_ESTABLISHED (Verified Records = 0)
SAFETY_BACKFIRE_VALIDATION: NOT_ESTABLISHED
PERCEPTION_METRICS: NOT_ESTABLISHED
MODEL_H: FROZEN_INVARIANT (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
PRODUCTION_MODEL: UNCHANGED (discover_event_candidates.py, automated_evidence_screening.py)
BACKFIRE_AWARE_IMPLEMENTATION: SANDBOX_ONLY
REAL_WORLD_BACKFIRE_VALIDATION: NOT_ESTABLISHED
STOP_CONDITION: V3_4_I_REAL_DATA_SHADOW_EXECUTION_COMPLETED
```

---

## 3. Input Dataset & Provenance

The evaluation ingests the previously locked Union Event Pool derived from NVIDIA PhysicalAI-SmartSpaces:
- **Total Union Events**: 51 events.
- **Eligible Events for Shadow Execution**: 38 events (`eligibility == 'ELIGIBLE_FOR_ADJUDICATION'`, valid temporal window with pre $\ge 3.0\text{s}$, intervention $\ge 1.5\text{s}$, post $\ge 4.0\text{s}$).
- **Ineligible Events**: 13 events (`eligibility == 'INELIGIBLE_WINDOW'`, truncated baseline or buffer clipping).
- **Facilities**: `Warehouse_026` (Cameras 0000, 0001, 0002, 0003) and `Warehouse_027` (Cameras 0000, 0001, 0002, 0003, 0004, 0005, 0006).
- **Integrity**: Source video SHA256 hashes match the provenance manifest.

---

## 4. State Machine Version & Shadow Rule Override

The shadow execution utilizes the state machine architecture defined in `scripts/v3_4_h_sandbox/backfire_state_machine.py` with an explicit, documented rule override:

> [!IMPORTANT]
> **`V3_4_I_SHADOW_RULE_OVERRIDE`**:  
> In Milestone V3.4-H, synthetic case H14 introduced an exploratory sensor-noise threshold ($\Delta R_{\text{sec}} < 0.01$). This threshold was exploratory only and was **not** part of the formal V3.4-G specification.  
> In this real-data shadow execution, the 0.01 threshold is **excluded**. In accordance with V3.4-G:
> - $\Delta R_{\text{sec}} \le 0 \implies \text{FAIL}$
> - $\Delta R_{\text{sec}} > 0 \implies \text{PASS}$
> Any small positive delta is annotated as `SMALL_POSITIVE_DELTA` and is not failed on a noise heuristic.  
> If secondary depth is occluded, Gate 3 strictly evaluates to **`UNKNOWN`** (not 0, not SAFE, not FAIL).

---

## 5. Gate 1 (Intervention Confirmation) Shadow Results

- **Pass Count**: 38 / 38 (100%)
- **Fail Count**: 0 / 38
- **Unknown Count**: 0 / 38
- **Analysis**:
  - Telemetry: CAN bus signals (brake pedal switch, longitudinal deceleration, steering angle) are **UNAVAILABLE** in the dataset.
  - Visual Kinematics: High-quality visual kinematic deceleration, complete halting, or pedestrian yielding was observed in all 38 eligible interactions (25 evaluated as `FULL`, 13 as `PARTIAL` amidst visual clutter).
  - Under V3.4-G/H rules, verified visual deceleration qualifies for Gate 1 `PASS` without fabricating telemetry signals.

---

## 6. Gate 2 (Observability) Shadow Results

- **Pass Count**: 0 / 38 (0%)
- **Fail Count**: 38 / 38 (100%)
- **Unknown Count**: 0 / 38
- **Analysis**:
  - **Primary Zone**: Visible in all 38 events (33 FULL, 5 PARTIAL).
  - **Secondary Zone Entrance**: Visible in 36 events; 2 HEVT events lacked defined secondary zones.
  - **Secondary Zone Interior Depth**: **0 / 38 visible (100% occluded)**.
  - **Post-Window Duration**: Adequate ($\ge 8.0\text{s}$) in 35 events, partial in 1, inadequate in 2.
  - **The Core Bottleneck**: Pallet racks obstruct line-of-sight beyond the immediate aisle entrance. Because `secondary_depth_visible == False`, Gate 2 outputs `FAIL` (`SECONDARY_DEPTH_EVIDENCE = UNAVAILABLE`) for every single event.
  - **Rule Enforcement**: In accordance with V3.4-G, depth occlusion is never interpreted as `NO_BACKFIRE`.

---

## 7. Gate 3 (Secondary Risk Delta) Shadow Results

- **Pass Count**: 0 / 38 (0%)
- **Fail Count**: 0 / 38 (0%)
- **Unknown Count**: 38 / 38 (100%)
- **Analysis**:
  - Because interior depth behind the racks is occluded, true physical hazard states ($R_{\text{sec\_PRE}}$ and $R_{\text{sec\_POST}}$) cannot be measured.
  - Under Section 9 instructions: *"إذا تعذر حسابهما: G3 = UNKNOWN وليس: 0 ولا: NO_RISK ولا: FAIL."*
  - Gate 3 evaluates to **`UNKNOWN`** across all 38 events.
  - Risk Estimate Source: Categorized as **`UNAVAILABLE`**. No model-derived score is substituted as physical ground truth.

---

## 8. Gate 4 (Causal Linkage & Confounder Isolation) Shadow Results

- **Pass Count**: 0 / 38 (0%)
- **Fail Count**: 38 / 38 (100%)
- **Unknown Count**: 0 / 38 (0%)
- **Analysis**:
  - **Confounder Failures (14 events)**: In 14 interactions, independent warehouse activities (pedestrian shift groups walking past or independent forklifts entering) competitively explain any secondary activity.
  - **Kinetic Continuity Failures (24 events)**: In 24 interactions without external confounders, the vehicle either came to a dead stop in the primary corridor (e.g., 026_010) or completed nominal passage without swerving toward the secondary zone. The physical trajectory never entered the secondary zone.

---

## 9. First Blocking Gate Analysis

For each of the 38 eligible events, the **First Blocking Gate** in the sequential cascade was recorded:

| Gate | Description | First Blocker Count | Percentage |
| :--- | :--- | :---: | :---: |
| **G1** | Intervention Confirmation | 0 | 0.0% |
| **G2** | Observability (Secondary Depth Occlusion) | **38** | **100.0%** |
| **G3** | Secondary Risk Delta | 0 | 0.0% |
| **G4** | Causal Linkage & Confounder Isolation | 0 | 0.0% |
| **NONE** | All Gates Passed | 0 | 0.0% |

**Conclusion**: Gate 2 is the **universal first blocker**. In existing fixed CCTV footage, the candidate generation process halts at the observability gate before secondary risk or causal mechanisms can be formally assessed.

---

## 10. Real-World Data Evidence Availability Matrix

Summarized from [`outputs/v3_4_i/real_data_evidence_availability.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_i/real_data_evidence_availability.json):

| Feature / Evidence Dimension | Available | Partial | Unavailable | Source | Epistemic Type | Ground Truth Status |
| :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| Primary Video Clips (H.264) | 38 | 0 | 0 | `VIDEO_DERIVED` | Direct Observation | Verified Present |
| 2D Actor Bounding Boxes | 38 | 0 | 0 | `TRACK_DERIVED` | YOLO Object Tracks | Unvalidated Heuristic |
| Pixel Separation Distances | 38 | 0 | 0 | `TRACK_DERIVED` | 2D Centroid Distance | Derived Calculation |
| Primary Interaction Score | 38 | 0 | 0 | `MODEL_DERIVED` | Heuristic Formula | Model Output |
| Visual Intervention Kinematics | 25 | 13 | 0 | `VIDEO_DERIVED` | Optical Inspection | Qualitative |
| **Vehicle CAN Bus Telemetry** | 0 | 0 | **38** | `NOT_AVAILABLE` | Hardware Sensor | **NOT_AVAILABLE** |
| Primary Zone Line-of-Sight | 33 | 5 | 0 | `VIDEO_DERIVED` | Direct Observation | High Confidence |
| Secondary Zone Entry Visibility | 36 | 0 | 2 | `VIDEO_DERIVED` | Direct Observation | High Confidence |
| **Secondary Interior Depth Visibility** | 0 | 0 | **38** | `NOT_AVAILABLE` | Direct Observation | **CRITICAL BOTTLENECK** |
| Multi-Camera 3D Homography | 0 | 0 | 38 | `NOT_AVAILABLE` | Physical Survey | **NOT_AVAILABLE** |
| **Secondary Risk Delta ($\Delta R_{\text{sec}}$)** | 0 | 0 | **38** | `NOT_AVAILABLE` | Physical Risk Measurement | **UNAVAILABLE** |
| Post-Window Duration ($\ge 4\text{s}$) | 35 | 1 | 2 | `VIDEO_DERIVED` | Timestamp Duration | High Confidence |
| Continuous Redirection Trajectory | 0 | 0 | 38 | `TRACK_DERIVED` | Spatial Kinematics | Disconnected |
| Confounder Isolation | 24 | 0 | 14 | `VIDEO_DERIVED` | Visual Traffic Audit | Qualitative |
| **Human Adjudicated GT Label** | 0 | 0 | **38** | `NOT_AVAILABLE` | Dual-Blind Human Review | **NOT_ESTABLISHED** |

---

## 11. Secondary-Zone Observability Deep Dive

The architectural failure of fixed-monocular surveillance for backfire detection is rooted in warehouse spatial geometry:
- Fixed CCTV cameras are mounted 6–8 meters high along central transit lanes.
- High pallet racks (4–6 levels high) create blind corridors perpendicular to the camera axis.
- While the camera easily captures the *opening* of an adjacent cross-aisle (observed in 36/38 events), the *interior depth* is completely invisible.
- Consequently, if an AGV swerves toward a cross-aisle, a camera cannot determine whether a worker 5 meters down that aisle was exposed to hazard.
- Any model asserting "NO_BACKFIRE" under such conditions commits an epistemic error by conflating unobservability with safety.

---

## 12. Causal Isolation & Confounder Breakdown

In the 14 events where confounders were present:
- **Warehouse_027_001**: 8+ shift workers entered the adjacent corridor from a breakroom door during the post-window.
- **Warehouse_027_003**: Forklift 418 entered the lane immediately after vehicle 378 completed its interaction.
- **Warehouse_026_014**: 5 active forklifts crossed the central intersection simultaneously, creating severe background motion clutter.
- **Warehouse_026_003 to 007**: Routine background picking operations in adjoining lanes created non-causal motion vectors.

In all 14 cases, the automated screening heuristic from V3.4-C falsely flagged secondary motion because it could not distinguish between intervention-induced evasion and ambient industrial traffic.

---

## 13. Telemetry Availability Audit

No vehicle CAN telemetry exists in the dataset:
- Brake pedal switches, hydraulic line pressure, acceleration telemetry, steering wheel angles, and wheel speed encoder logs are completely missing.
- As demonstrated in Milestone V3.4-H, visual kinematics can establish that an interaction occurred, but determining whether deceleration was automated emergency braking or nominal coasting remains impossible without onboard telemetry.

---

## 14. Model H Separation

Model H parameters remain strictly frozen:
$$k_0 = 2.40, \quad \beta_d = 0.08, \quad \beta_l = 0.12, \quad \beta_{\text{pitch}} = 0.22$$
In this shadow execution:
- Model H is treated exclusively as a **Risk Characterization Model**, not Ground Truth.
- Because secondary zone depth was unobservable, Model H secondary risk characterization could not be physically grounded.
- No model-derived risk estimate was used to manufacture pseudo-ground-truth.

---

## 15. Audit of the Five Historical Candidate Events

Below is the comparative audit of the five events flagged as automated candidates in Milestone V3.4-C:

| Event ID | Facility / Cam | V3.4-D Forensic Status | V3.4-E Disposition | V3.4-I Shadow Results | First Blocker | Root Cause & Key Analytical Difference |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **026_010** | Wh026 / Cam02 | MODERATE_CANDIDATE | NO_BACKFIRE_OBSERVED | `SHADOW_INSUFFICIENT_EVIDENCE` | **G2** | Vehicle stopped dead (2.5px displacement). V3.4-E called this NO_BACKFIRE, but V3.4-I correctly enforces that occluded rack depth prevents ruling out unobserved hazard. |
| **027_001** | Wh027 / Cam02 | WEAK_CANDIDATE | INSUFFICIENT_OBSERVABILITY | `SHADOW_INSUFFICIENT_EVIDENCE` | **G2** | V3.4-C score triggered by crowd of 8+ incoming workers. Blocked at G2 (depth) and G4 (confounder turnover). |
| **027_003** | Wh027 / Cam02 | WEAK_CANDIDATE | INSUFFICIENT_OBSERVABILITY | `SHADOW_INSUFFICIENT_EVIDENCE` | **G2** | V3.4-C score triggered by independent arrival of Forklift 418. Blocked at G2 (depth) and G4 (independent vehicle confounder). |
| **027_004** | Wh027 / Cam02 | INSUFFICIENT_EVIDENCE | NO_BACKFIRE_OBSERVED | `SHADOW_INSUFFICIENT_EVIDENCE` | **G2** | Nominal clearance; both agents exited lane safely. Blocked at G2 (depth) and G4 (zero redirection trajectory). |
| **026_014** | Wh026 / Cam02 | INSUFFICIENT_EVIDENCE | INSUFFICIENT_OBSERVABILITY | `SHADOW_INSUFFICIENT_EVIDENCE` | **G2** | Dense multi-forklift congestion (5 active vehicles). Blocked at G2 (depth) and G4 (extreme visual clutter). |

---

## 16. Comprehensive Shadow Results Table for All 38 Eligible Events

| # | Event Identifier | G1 | G2 | G3 | G4 | First Blocker | Missing Evidence | Shadow Execution Result |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| 1 | `UNION_CAND_Warehouse_027_001` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Confounder Isolation | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 2 | `UNION_CAND_Warehouse_027_003` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Confounder Isolation | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 3 | `UNION_CAND_Warehouse_027_004` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 4 | `UNION_CAND_Warehouse_026_010` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 5 | `UNION_CAND_Warehouse_026_014` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Multi-Vehicle Clutter | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 6 | `UNION_CAND_Warehouse_026_012` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Confounder Isolation | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 7 | `UNION_CAND_Warehouse_026_013` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Confounder Isolation | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 8 | `UNION_CAND_Warehouse_026_011` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Confounder Isolation | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 9 | `UNION_CAND_Warehouse_027_006` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Post Window (<4s) | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 10 | `UNION_CAND_Warehouse_027_017` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 11 | `UNION_CAND_Warehouse_027_005` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Confounder Isolation | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 12 | `UNION_CAND_Warehouse_027_002` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Confounder Isolation | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 13 | `UNION_CAND_Warehouse_026_007` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Visual Clutter | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 14 | `UNION_CAND_Warehouse_026_006` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Visual Clutter | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 15 | `UNION_CAND_Warehouse_027_014` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 16 | `UNION_CAND_Warehouse_027_015` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 17 | `UNION_CAND_Warehouse_026_003` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Visual Clutter | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 18 | `UNION_CAND_Warehouse_026_004` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Visual Clutter | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 19 | `UNION_CAND_Warehouse_027_020` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 20 | `UNION_CAND_Warehouse_027_026` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Post Window (<4s) | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 21 | `UNION_CAND_Warehouse_027_016` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 22 | `UNION_CAND_Warehouse_026_005` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Visual Clutter | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 23 | `UNION_CAND_Warehouse_027_033` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Confounder Isolation | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 24 | `UNION_CAND_Warehouse_027_012` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 25 | `UNION_CAND_Warehouse_027_025` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Post Window Partial | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 26 | `UNION_CAND_Warehouse_027_019` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 27 | `UNION_CAND_Warehouse_027_032` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 28 | `UNION_CAND_Warehouse_027_021` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 29 | `UNION_CAND_Warehouse_027_034` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 30 | `UNION_CAND_Warehouse_027_010` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 31 | `UNION_CAND_Warehouse_027_018` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 32 | `UNION_CAND_Warehouse_027_011` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 33 | `UNION_CAND_Warehouse_027_024` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 34 | `UNION_CAND_Warehouse_027_035` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 35 | `UNION_CAND_Warehouse_027_013` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 36 | `UNION_CAND_Warehouse_027_023` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Depth, Physical Path | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 37 | `UNION_HEVT_Warehouse_026_003` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Zone Undefined | `SHADOW_INSUFFICIENT_EVIDENCE` |
| 38 | `UNION_HEVT_Warehouse_027_002` | **PASS** | FAIL | UNKNOWN | FAIL | **G2** | Telemetry, Secondary Zone Undefined | `SHADOW_INSUFFICIENT_EVIDENCE` |

---

## 17. Shadow Result Distribution Summary

- **Total Eligible Events Evaluated**: 38
- **`SHADOW_BACKFIRE_CANDIDATE`**: **0** (0.0%)
- **`SHADOW_PRIMARY_NEAR_MISS`**: **0** (0.0%)
- **`SHADOW_INSUFFICIENT_EVIDENCE`**: **38** (100.0%)
- **Events Reaching Gate 3**: **0** (0.0%)
- **Events Reaching Gate 4**: **0** (0.0%)

---

## 18. Bottleneck Analysis

When assessing why candidate generation stalls on real datasets, the bottlenecks are categorized as follows:

```
[ Lack of Secondary Observability (100%) ]
  └─ Pallet racking blocks interior cross-aisle line-of-sight in all 38 events.
     └─ Gate 2 fails unconditionally.

[ Inability to Estimate Secondary Risk (100%) ]
  └─ Because interior depth is occluded, R_sec(PRE) and R_sec(POST) are UNAVAILABLE.
     └─ Gate 3 evaluates to UNKNOWN.

[ Lack of Physical Telemetry (100%) ]
  └─ CAN bus signals (brake, decel, steering) are completely absent.
     └─ Forced reliance on visual proxy kinematics for Gate 1.

[ Causal Confounding & Disconnection (100%) ]
  └─ 37% of events confounded by ambient warehouse traffic.
  └─ 63% of events lack kinetic trajectory into secondary zones.
```

The primary blocker is not a failure of detection logic; rather, it is a **fundamental physical limitation of fixed monocular facility surveillance**.

---

## 19. Perception Limitations vs. Observability Limitations

It is critical to distinguish between two distinct failure categories:
1. **Perception Limitation**: The sensor has line-of-sight to an object, but the AI algorithm fails to detect or track it (e.g., YOLO bounding box jitter, detector miss under low lighting, or tracker ID swap).
2. **Observability Limitation**: The physical line-of-sight simply does not exist (e.g., optical rays are blocked by solid steel pallet racks holding cargo). No computer vision algorithm, no matter how advanced, can observe what is physically occluded behind an opaque obstacle.

Milestone V3.4-I proves that the failure to establish backfire candidates in fixed CCTV warehouse footage is an **Observability Limitation**, not merely an algorithmic or perceptual defect.

---

## 20. What This Execution Does NOT Establish

To maintain complete scientific and engineering integrity, the following negative declarations are explicit:
- ❌ **Does NOT establish that "No backfires occurred in Warehouse_026/027"**: Occluded secondary zones mean backfires may or may not have occurred; the sensor data simply cannot confirm or deny them.
- ❌ **Does NOT validate detector performance**: No ground truth exists to compute accuracy, precision, or recall.
- ❌ **Does NOT validate Model H**: Model H was not tested against measured human safety outcomes.
- ❌ **Does NOT authorize production deployment**: The architecture is not ready for real-world automated screening.

---

## 21. Required Field Data for Real-World Deployment

Before this Backfire-Aware Architecture can be deployed in live warehouse facilities, the following four engineering requirements must be satisfied:
1. **Synchronized Vehicle CAN Telemetry**: High-frequency (< 50ms) hardware logging of brake pressure, steering angle, and wheel speed.
2. **Multi-Camera 3D Geometry**: Overlapping multi-camera views with extrinsic homography calibration covering cross-aisle depths.
3. **Dynamic Occlusion Mapping**: Real-time ray-casting against facility CAD layouts to dynamically assess whether secondary spaces are visible.
4. **Independent Human Adjudication**: Dual-blinded expert adjudication of real incident footage to establish ground truth.

---

## 22. Final Governance State

```yaml
MILESTONE_STATUS: V3_4_I_REAL_DATA_SHADOW_EXECUTION_COMPLETED
SHADOW_EXECUTION: COMPLETED (38/38 Audited)
REAL_WORLD_BACKFIRE_VALIDATION: NOT_ESTABLISHED
SAFETY_BACKFIRE_GT: NOT_ESTABLISHED (Verified Records = 0)
PERCEPTION_METRICS: NOT_ESTABLISHED
MODEL_H: FROZEN_INVARIANT (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
PRODUCTION_MODEL: UNCHANGED (discover_event_candidates.py, automated_evidence_screening.py)
STOP_CONDITION: V3_4_I_REAL_DATA_SHADOW_EXECUTION_COMPLETED
```

---
*Report compiled autonomously in accordance with Milestone V3.4-I governance mandates.*
