# V3.4-L — INSTRUMENTED FIELD PILOT EXECUTION PROTOCOL
## Formal Engineering Specification, Safety Plan, Commissioning Gating, and Operational Protocol

---

### EXECUTIVE SUMMARY & STATUS DECLARATION

```
========================================================================================
MILESTONE STATUS:          V3_4_L_INSTRUMENTED_FIELD_PILOT_PROTOCOL_COMPLETED
GOVERNANCE CLASS:          FIELD EXECUTION DESIGN ONLY (PRE-RECORDING SPECIFICATION)
PRODUCTION MODEL:          UNCHANGED (discover_event_candidates.py / automated_evidence_screening.py)
MODEL H STATUS:            FROZEN_INVARIANT (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
SAFETY BACKFIRE GT:        NOT_ESTABLISHED (ZERO FIELD GROUND TRUTH LABELS GENERATED)
SAFETY VALIDATION:         NOT_ESTABLISHED (CLAIMS OF SAFETY OR BACKFIRE MITIGATION FORBIDDEN)
REAL-WORLD VALIDATION:     NOT_ESTABLISHED (NO PHYSICAL FIELD DEPLOYMENT COMPLETED)
FIELD DATASET STATUS:      NOT_COLLECTED (DESIGN SPECIFICATION ONLY - ZERO BYTES RECORDED)
INSTRUMENTATION READINESS: SPECIFIED_FOR_PHYSICAL_PILOT (GATES C1-C6 DEFINED)
========================================================================================
```

---

## 1. PURPOSE OF THIS MILESTONE

The primary objective of Milestone **V3.4-L** is to synthesize the instrumentation architectures formulated in [V3.4-J](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/FIELD_DATASET_SPECIFICATION.md) and the verification harnesses constructed in [V3.4-K](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_k/v3_4_k_readiness_report.md) into an exhaustive, fully actionable, and deployable **Field Pilot Execution Protocol**.

This protocol defines with absolute operational clarity:
1. **Physical Facility Selection & Layout:** Where multi-camera rigs, LiDAR nodes, and PTP grandmasters are anchored.
2. **Hardware Commissioning & Burn-In:** How sensors, vehicle telemetry interfaces, and clocks are certified prior to active trials.
3. **Synchronization & Dynamic Calibration:** The mathematical criteria governing IEEE 1588-2019 (PTPv2) synchronization and optical photogrammetry.
4. **Sensor Health & Gating:** Real-time signal validation preventing corrupt or incomplete feeds from entering the capture stream.
5. **Controlled Trials Execution:** Safe execution procedures for scenarios L01 through L09 using certified soft proxies, with strict zero-human exposure.
6. **Naturalistic Operations Monitoring:** Passive, non-invasive data acquisition across industrial shifts without altering worker behavior.
7. **Dynamic Temporal Packaging:** Generation of event recording manifests supporting dynamic PRE, INTERVENTION, and POST windows.
8. **Rejection & Abort Criteria:** Fail-safe criteria terminating trials upon safety breaches or telemetry packet dropouts.
9. **Cryptographic Provenance & Custody:** Tamper-evident SHA-256 Merkle logging preserving evidentiary admissibility.

> [!CAUTION]
> **CRITICAL BOUNDARY:** This milestone is strictly an **engineering design and protocol definition**. It **DOES NOT** perform physical field recording, does not collect dataset clips, does not train or tune models, does not evaluate Model H, and does not establish Ground Truth.

---

## 2. GOVERNANCE & SCIENTIFIC INVARIANTS

The execution of V3.4-L is locked under strict scientific and ethical governance:

| Governance Invariant | Enforced State | Operational Meaning |
| :--- | :--- | :--- |
| `PRODUCTION_MODEL` | **`UNCHANGED`** | Production screening and candidate generation algorithms remain bit-identical. |
| `MODEL_H` | **`FROZEN_INVARIANT`** | Primary collision avoidance model parameters remain hardcoded: $k_0 = 2.40$, $\beta_d = 0.08$, $\beta_l = 0.12$, $\beta_{\text{pitch}} = 0.22$. |
| `SAFETY_BACKFIRE_GT` | **`NOT_ESTABLISHED`** | No human ground truth labels have been generated. Field pilot data has not been acquired. |
| `SAFETY_BACKFIRE_VALIDATION` | **`NOT_ESTABLISHED`** | The backfire-aware evidence model is not validated against physical events. |
| `REAL_WORLD_BACKFIRE_VALIDATION`| **`NOT_ESTABLISHED`** | Real-world validation cannot occur prior to field capture and human adjudication. |
| `FIELD_DATASET` | **`NOT_COLLECTED`** | Zero hours of physical field data have been recorded under this specification. |
| `HARDWARE_FIELD_VALIDATION` | **`NOT_PERFORMED`** | Synthetic bench verification (V3.4-K) demonstrated harness functionality, not hardware validation. |

---

## 3. V3.4-K SEMANTIC CORRECTIONS

To maintain absolute scientific integrity, the semantic inconsistencies identified during the transition from V3.4-K are reconciled and codified in [v3_4_k_semantic_corrections.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/v3_4_k_semantic_corrections.md):

### A. Test Count Reconciliation (`TEST_COUNT_RECONCILIATION`)
The V3.4-K readiness report text cited "37 fault injection tests", whereas the summary test table enumerated 58 distinct checks. An exhaustive audit of the underlying test execution artifacts (`v3_4_k_verification_summary.json` and `v3_4_k_audit_log.jsonl`) confirms:
- **37 Fault Injection Tests:** Executed by `test_field_verification.py` across 6 fault suites (Clock Jitter/Dropout, Camera Drop, CAN Timeout, Secondary Observability, Evidence Gate, Package Corruption).
- **4 Cryptographic Tamper Tests:** Byte-level mutation and manifest mismatch verifications.
- **3 Blinding & Isolation Tests:** Model score leakage and label leak verifications.
- **4 Deterministic Recovery Tests:** Restart and state restoration tests.
- **10 Infrastructure & Meta-Verification Checks:** Schema compliance, JSON validation, and file integrity checks.
- **Reconciled Total:** Exactly **58 automated verification checks**, achieving a **100% TEST PASS RATE**.

### B. Decoupling Component Limits from Composite Budgets
The temporal budget is strictly bifurcated to prevent sub-millisecond clock drifts from masking individual sensor failures:
- **`COMPONENT_SYNC_LIMIT` ($18.0\text{ ms}$ Allocated Subsystem Limit):** Camera inter-frame offset ($\le 5.0\text{ ms}$), CAN gateway delay ($\le 10.0\text{ ms}$), and Secondary Sensor delay ($\le 3.0\text{ ms}$). If any sensor exceeds its component threshold, it is marked **`REJECTED`**, even if total composite skew is within $33.3\text{ ms}$.
- **`COMPOSITE_SYNC_BUDGET` ($33.33\text{ ms}$ System Frame Target):** Represents one video frame at 30 fps, leaving an unallocated safety reserve of $15.33\text{ ms}$.

### C. Gated Readiness State Decoupling
Readiness is partitioned into three distinct phases. Crucially, Ground Truth is **NOT** a prerequisite for starting physical pilot capture:
1. `INSTRUMENTATION_READY_FOR_CAPTURE`: Hardware, rigging, network, and clocks are commissioned and ready to record.
2. `DATASET_READY_FOR_REVIEW`: Data has been captured, verified against quality gates D1–D6, and packaged for humans.
3. `VALIDATION_READY`: Blinded human adjudication is complete and Ground Truth is committed.

### D. Nomenclature Standardization
The misleading phrase "100% accuracy" is purged and replaced with **`100% TEST PASS RATE`**, accurately reflecting software verification rather than empirical sensor accuracy.

### E. Physical Threshold Classification
Engineering thresholds ($5\text{ ms}$, $20\text{ ms}$, $1.5\text{ px}$, $33.3\text{ ms}$, $\tau_{\max} \le 2.0\text{ s}$) are classified as **`DESIGN_REQUIREMENT`** or **`CURRENT_ACCEPTANCE_TARGET`**, strictly refuting any characterization as "Universal Physical Truths".

---

## 4. PILOT READINESS STATE MACHINE

The operational lifecycle of the field pilot is governed by a finite state machine codified in [pilot_readiness_state_machine.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/pilot_readiness_state_machine.json):

```mermaid
stateDiagram-v2
    [*] --> PLANNED
    PLANNED --> INSTALLATION_READY: Facility Leased & Hardware Staged
    INSTALLATION_READY --> COMMISSIONING: Mechanical Rigging & Cabling Complete
    COMMISSIONING --> INSTRUMENTATION_READY_FOR_CAPTURE: Pre-Capture Gates C1-C6 = PASS
    COMMISSIONING --> INSTALLATION_READY: Hardware Fault / Remount Required
    
    INSTRUMENTATION_READY_FOR_CAPTURE --> CAPTURE_IN_PROGRESS: Safety Sweep & Marshal Authorization
    CAPTURE_IN_PROGRESS --> CAPTURE_ABORTED: E-Stop / Sensor Dropout / Perimeter Breach
    CAPTURE_ABORTED --> INSTRUMENTATION_READY_FOR_CAPTURE: Incident Audit & Recalibration
    CAPTURE_IN_PROGRESS --> CAPTURE_COMPLETED: Nominal Run Finished
    
    CAPTURE_COMPLETED --> DATASET_READY_FOR_REVIEW: Post-Capture Gates D1-D6 = PASS
    DATASET_READY_FOR_REVIEW --> VALIDATION_READY: Blinded Human Panel Consensus Committed
    
    VALIDATION_READY --> [*]
```

### Strictly Forbidden State Transitions
1. **`INSTRUMENTATION_READY_FOR_CAPTURE` $\rightarrow$ `VALIDATION_READY`:** Strictly prohibited. No leapfrogging data collection, quality checks, and human adjudication is permitted.
2. **`COMMISSIONING` $\rightarrow$ `DATASET_READY_FOR_REVIEW`:** Calibration and test artifacts cannot be reviewed as operational events.
3. **`CAPTURE_COMPLETED` $\rightarrow$ `VALIDATION_READY`:** Raw, unadjudicated field data cannot establish validation without blinded human consensus.

---

## 5. FACILITY SELECTION REQUIREMENTS

Facility criteria are standardized in [facility_selection_requirements.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/facility_selection_requirements.json) to guarantee geometric repeatability and physical safety:

| Facility Domain | Engineering Parameter | Threshold / Specification | Governance Classification |
| :--- | :--- | :--- | :--- |
| **Geometry** | Primary Corridor Length | $\ge 35.0\text{ m}$ (continuous line of sight) | `DESIGN_REQUIREMENT` |
| | Primary Corridor Width | $\ge 3.5\text{ m}$ (accommodates 1.8m vehicle + 0.8m margin) | `DESIGN_REQUIREMENT` |
| | Secondary Cross-Aisle Depth | $\ge 25.0\text{ m}$ (unbroken optical depth) | `DESIGN_REQUIREMENT` |
| | Secondary Aisle Width | $\ge 3.0\text{ m}$ | `DESIGN_REQUIREMENT` |
| **Floor Surface** | Flatness Specification | DIN 18202 Table 3 Group 4 ($\le 3\text{ mm}$ over $1\text{ m}$) | `CURRENT_ACCEPTANCE_TARGET` |
| | Friction Coefficient | $\mu \ge 0.55$ (dry industrial polished concrete) | `DESIGN_REQUIREMENT` |
| **Safety Zone** | Physical Exclusion Perimeter | $1.8\text{ m}$ high chain-link / interlocked modular fence | `MANDATORY_SAFETY_RULE` |
| | Longitudinal Buffer Margin | $\ge 10.0\text{ m}$ beyond maximum stopping distance | `MANDATORY_SAFETY_RULE` |
| | Lateral Buffer Margin | $\ge 2.0\text{ m}$ from vehicle dynamic envelope | `MANDATORY_SAFETY_RULE` |
| **Environment** | Ambient Illuminance | $350 \pm 50\text{ lux}$ (high-frequency LED, zero flicker) | `CURRENT_ACCEPTANCE_TARGET` |
| | Temperature / Humidity | $15^\circ\text{C}$ to $28^\circ\text{C}$, non-condensing | `OPERATIONAL_ENVELOPE` |
| **Infrastructure** | Network Backbone | Dual isolated 10GbE SFP+ optical trunk switches | `DESIGN_REQUIREMENT` |
| | Storage Ingest Rate | NVMe Direct RAID Array ($\ge 2.5\text{ GB/s}$ sustained write) | `DESIGN_REQUIREMENT` |

---

## 6. SAFETY CONTROL PLAN (ZERO-HUMAN-HAZARD MANDATE)

> [!CAUTION]
> **ETHICAL IMPERATIVE:** No human being shall enter the dynamic travel envelope, braking buffer, or secondary diversion zone of any experimental vehicle during testing under any circumstances.

```
                              [PHYSICAL EXCLUSION PERIMETER (1.8m Fence)]
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|   [SAFE BUFFER]             [PRIMARY TRAVEL CORRIDOR]                         [SAFE BUFFER]   |
|   +-----------+   =============================================               +-----------+   |
|   | Light     |   --> Vehicle Heading (max 4.0 m/s)                            | Light     |   |
|   | Curtain   |   ---------------------------------------------               | Curtain   |   |
|   | Entry     |         [Foam Mannequin P1]                                   | Exit      |   |
|   +-----------+            (Target Waypoint)                                  +-----------+   |
|                             \                                                                 |
|                              \ Swerve Diversion Vector                                        |
|                               v                                                               |
|                        +--------------+                                                       |
|                        | CROSS-AISLE  |                                                       |
|                        | SECONDARY    |                                                       |
|                        | ZONE         |                                                       |
|                        | [Robotic     |                                                       |
|                        |  Dummy P2]   |                                                       |
|                        +--------------+                                                       |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
        ^                                                                       ^
        |                                                                       |
 [Hardwired E-Stop]                                                      [Safety Marshal Station]
                                                                         - Unobstructed Sightline
                                                                         - Dual Wireless SIL-3 E-Stops
```

### Safety Defense-in-Depth Mechanisms
1. **Certified Test Proxies:** All pedestrian interactions are executed using certified soft foam mannequins mounted on remote overhead rails or low-profile motorized ground carts.
2. **Dual-Channel SIL-3 Emergency Stop:** Safety Marshal holds a dedicated Cat 4 / SIL-3 certified wireless remote E-Stop. Power cutoff to vehicle traction drives engages within $\le 50\text{ ms}$.
3. **Hardware Perimeter Interlocks:** Perimeter fence gates feature safety interlock switches; opening any gate breaks the safety loop and triggers an immediate vehicle shutdown.
4. **Pre-Test Inspection Walkthrough:** Standardized 15-minute walkthrough confirming perimeter integrity, barrier latches, and clear travel envelopes before every active test.

---

## 7. FOUR-CAMERA DEPLOYMENT ARCHITECTURE

Camera placement is engineered to eliminate tracking ambiguity across the primary-to-secondary transition:

```mermaid
graph TD
    CA[Camera A: Primary Corridor Frontal] -->|Approaching Kinematics & Primary Obstacle| TRK[Unified Tracking Engine]
    CB[Camera B: Lateral Junction Overhead] -->|Swerve Vector & Heading Diversion| TRK
    CC[Camera C: Cross-Aisle Longitudinal] -->|Secondary Zone Penetration >= 20m| TRK
    CD[Camera D: Diagonal Redundant Cross-View] -.->|Optional Overlap & Occlusion Bridging| TRK
```

### Configuration Options & Deployment Tradeoffs
Camera deployment supports three standardized tiers:

| Configuration Tier | Cameras Deployed | Coverage Capabilities | Blind Zones | Failure Impact |
| :--- | :--- | :--- | :--- | :--- |
| **`MINIMUM_CONFIGURATION`** | Camera A + Camera C | Covers primary approach and secondary cross-aisle depth. | Acute blind spot at immediate corner junction ($< 1.5\text{ m}$). | If either camera fails, entire trial is invalid. |
| **`RECOMMENDED_CONFIGURATION`** | Camera A + Camera B + Camera C | Full coverage of approach, junction threshold, and cross-aisle depth. | Minor edge vignetting behind vertical rack pillars. | Failure of B degrades swerve yaw accuracy but preserves event validity. |
| **`HIGH-COMPLEXITY_CONFIGURATION`**| Camera A + Camera B + Camera C + Camera D | Overlapping stereo baseline across junction; redundant diagonal cross-view. | Zero blind zones in operational envelope. | High resilience; Camera D compensates for optical occlusion or dropped frames. |

---

## 8. PTP TIME SYNCHRONIZATION COMMISSIONING

Time synchronization is enforced using IEEE 1588-2019 (PTPv2) under the schema specified in [ptp_commissioning_schema.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/ptp_commissioning_schema.json):

```mermaid
graph TD
    GNSS[GNSS Satellite Constellation] -->|Antenna Line-of-Sight| GM[PTP Grandmaster Clock Class 6]
    GM -->|PTP over TSN Fiber Backbone| SW[Time-Sensitive Network Switch]
    SW -->|Hardware PTP Sub-Microsecond| CA[Camera A NIC]
    SW -->|Hardware PTP Sub-Microsecond| CB[Camera B NIC]
    SW -->|Hardware PTP Sub-Microsecond| CC[Camera C NIC]
    SW -->|Hardware PTP Sub-Microsecond| CD[Camera D NIC]
    SW -->|Hardware PTP Bridge| CAN[CAN Gateway Transceiver]
    SW -->|Hardware PTP Sub-Microsecond| LID[Secondary LiDAR Node]
```

### Synchronization Budget Allocations
- **Grandmaster Lock State:** Must maintain `clock_class = 6` with $\ge 8$ GNSS satellites locked in RTK/DGPS fix.
- **Component Synchronization Limits (`DESIGN_REQUIREMENT`):**
  - Optical Cameras: Inter-frame offset $\le 5.0\text{ ms}$ (mean offset $\le 100\,\mu\text{s}$, P99 $\le 500\,\mu\text{s}$).
  - Vehicle CAN Gateway: Hardware bridge offset $\le 10.0\text{ ms}$ (mean offset $\le 1.0\text{ ms}$).
  - Secondary Sensor (LiDAR/Radar): Sensor timestamp offset $\le 5.0\text{ ms}$.
- **Composite System Target (`CURRENT_ACCEPTANCE_TARGET`):** Total multi-modal skew across all streams $\le 33.33\text{ ms}$ (one frame duration at 30 fps), providing a $13.33\text{ ms}$ unallocated safety margin.

---

## 9. VEHICLE TELEMETRY (CAN) COMMISSIONING

Vehicle dynamic state is acquired via non-intrusive CAN bus tapping conforming to [vehicle_telemetry_commissioning_schema.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/vehicle_telemetry_commissioning_schema.json):

### Required Signals Manifest
1. `vehicle_speed`: Calibrated longitudinal velocity in $\text{m/s}$ ($\ge 50\text{ Hz}$).
2. `brake_state`: Brake activation signal ($\text{boolean}$ or line pressure in $\text{bar}$, $\ge 50\text{ Hz}$).
3. `longitudinal_acceleration`: Accelerometer reading in $\text{m/s}^2$ ($\ge 50\text{ Hz}$).
4. `steering_angle`: Handwheel or steer knuckle angle in $\text{deg}$ ($\ge 50\text{ Hz}$).
5. `yaw_rate`: Gyroscopic angular velocity in $\text{deg/s}$ ($\ge 50\text{ Hz}$).
6. `throttle_position`: Accelerator demand in $\%$ ($\ge 50\text{ Hz}$).
7. `wheel_speed`: Individual wheel encoders in $\text{rad/s}$ (where available).

---

## 10. SIGNAL VALIDATION & INTEGRITY CHECKING

Telemetry validation relies strictly on **mathematical signal fidelity checks**, completely avoiding safety assertions or model risk thresholds:

```mermaid
graph TD
    SIG[Raw CAN / Sensor Signal Stream] --> M1[Monotonicity Verification: dt > 0]
    SIG --> M2[Continuity Verification: gap < 20ms]
    SIG --> M3[Range Validity: Physical Limits]
    SIG --> M4[Unit Consistency: SI Units]
    SIG --> M5[Flatline Detection: Zero Variance Check]
    SIG --> M6[Cross-Sensor Dynamics: Integral a dt vs v]
    
    M1 & M2 & M3 & M4 & M5 & M6 -->|All Checks PASS| C3[Pre-Capture Gate C3: PASS]
    M1 | M2 | M3 | M4 | M5 | M6 -->|Any Check FAILS| REJ[Gate C3: REJECTED]
```

---

## 11. SECONDARY ZONE OBSERVABILITY COMMISSIONING

Secondary hazard zone observability is governed by [secondary_zone_commissioning_schema.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/secondary_zone_commissioning_schema.json):

> [!IMPORTANT]
> **SEMANTIC ENFORCEMENT:** The flag `secondary_depth_visible` **CANNOT** be set to `TRUE` based on architectural assumptions. It **MUST** remain `FALSE` until physically proven in the field using a standardized calibration target deployed at the required penetration depth ($\ge 20.0\text{ m}$).

### Verification Procedure
1. Deploy certified reflective test mannequin at $20.0\text{ m}$ depth inside the secondary cross-aisle.
2. Optical resolution check: Camera C must achieve $\ge 65\text{ px/m}$ resolution on the mannequin torso.
3. Blind pocket survey: Verify that pallet racks or structural columns create zero blind pockets larger than $0.25\text{ m}^3$ within the travel corridor.
4. If verified, commit manifest with `secondary_depth_visible_state = TRUE_FIELD_PROVEN`.

---

## 12. FACILITY GEOMETRY SURVEY

Geodetic, structural, and optical extrinsic survey conforms to [facility_geometry_schema.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/facility_geometry_schema.json):
- **Survey Equipment:** Licensed Total Station and Laser Tracker ($\text{accuracy} \le 2.0\text{ mm}$).
- **Facility Coordinate Reference System:** Local Cartesian Right-Handed ($X=\text{Forward}, Y=\text{Left}, Z=\text{Up}$ relative to permanent facility brass monument).
- **Ground Plane Fitting:** Best-fit plane equation $Ax + By + Cz + D = 0$ with residual $\text{RMS} \le 3.0\text{ mm}$.
- **Extrinsic Poses:** Sensor 6-DoF translation ($x, y, z$) and rotation quaternions ($q_x, q_y, q_z, q_w$) with optical reprojection error $\le 1.5\text{ px}$.

---

## 13. MULTI-SENSOR REGISTRATION MATRIX

Spatial and temporal co-registration between sensors is verified across four distinct interfaces:

```
+--------------------+---------------------------+------------------------+-------------------------+
| Sensor Pair        | Registration Method       | Quality Target         | Failure Action          |
+--------------------+---------------------------+------------------------+-------------------------+
| Camera <-> Camera  | Common Checkerboard Poses | Reprojection <= 1.5 px | Recalibrate Extrinsics  |
| Camera <-> CAN     | Kinetic Motion Derivative | Temporal Skew <= 5 ms  | Re-lock PTP Bridge      |
| Camera <-> LiDAR   | Target Pointcloud Overlay | Spatial Error <= 20 mm | Adjust Transform Matrix |
| Camera <-> UWB     | Fixed Anchor Survey Poses | GDOP <= 1.5, Res <= 5cm| Re-anchor Transceivers  |
+--------------------+---------------------------+------------------------+-------------------------+
```

---

## 14. DYNAMIC EVENT WINDOWS & EVENT PACKAGING

Event windows are defined dynamically relative to physical intervention kinetics, rejecting fixed 8-second approximations:

```
[--- PRE WINDOW (1.5s - 5.0s) ---] [--- INTERVENTION (0.5s - 3.0s) ---] [--- POST WINDOW (2.0s - 10.0s) ---]
|                                  |                                   |                                   |
t_pre_start                        t_intervention_start                t_intervention_end                  t_post_end
                                   \                                  /
                                    \-- tau <= 2.0s (DESIGN REQ) ----/
                                        Secondary Hazard Onset
```

- **Dynamic Pre-Window:** Captures unperturbed steady-state kinematics prior to obstacle detection.
- **Dynamic Intervention Window:** Begins upon brake pedal actuation ($\ge 5\text{ bar}$) or steering swerve ($\ge 12^\circ$), ending upon trajectory stabilization.
- **Dynamic Post-Window:** Monitors downstream corridor and secondary aisle for secondary hazard emergence or safe resolution.
- **Latency Constraint ($\tau_{\max} \le 2.0\text{ s}$):** Classified strictly as `CURRENT_SPECIFICATION_CONSTRAINT`.

---

## 15. CONTROLLED TRIAL MATRIX (SCENARIOS L01–L09)

Controlled trials are specified in [controlled_trial_matrix.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/controlled_trial_matrix.json). All scenarios enforce the zero-human-hazard rule:

| ID | Scenario Name | Primary Actor | Secondary Actor | Vehicle Maneuver | Expected Class |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **L01** | Safe Complete Stop | Foam Mannequin P1 | None | Full straight stop ($\ge 3\text{m}$ clearance) | Primary Resolved, No Backfire |
| **L02** | Safe Clearance | Safety Cones | None | Nominal straight pass | Nominal Operation |
| **L03** | Swerve Toward Empty Secondary Zone | Foam Mannequin P1 | None (Empty Aisle) | Lateral swerve into clear cross-aisle | Benign Swerve |
| **L04** | Controlled Secondary Exposure | Foam Mannequin P1 | Robotic Dummy P2 | Lateral swerve intersecting P2 path | Simulated Safety Backfire |
| **L05** | Independent Actor Confounder | Foam Mannequin P1 | Motorized Trolley | Straight brake; trolley passes laterally | Confounded Independent Actor |
| **L06** | Tracker Handoff Stress Case | Mobile Dummy | None | Diagonal transit across camera seams | Tracker Stress Control |
| **L07** | Occluded Zone | Foam Mannequin P1 | Dummy Behind Pallet | Swerve toward occluded cross-aisle | Insufficient Observability Rejected |
| **L08** | Sensor Failure | Foam Mannequin P1 | Robotic Dummy P2 | Forced RTSP dropout during swerve | Invalid Run (Data Integrity Fail) |
| **L09** | Clock Offset | Foam Mannequin P1 | None | CAN timestamp perturbed $+25\text{ ms}$ | Invalid Run (Sync Fail) |

### Counterfactual Paired Design
Each scenario pairs a `RUN_BASELINE` with a `RUN_INTERVENTION`.
> [!NOTE]
> **CAUSALITY DISCLAIMER:** The pairing of Run Baseline and Run Intervention provides controlled contrastive observations only; it **DOES NOT** prove universal counterfactual causality due to potential unobserved environmental covariates.

---

## 16. NATURALISTIC CAPTURE PROTOCOL

Naturalistic recording captures real warehouse operations under [naturalistic_capture_protocol.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/naturalistic_capture_protocol.json):
1. **Passive Monitoring:** Instrumentation operates silently in background.
2. **Zero Behavioral Alteration:** Workers and vehicle operators are not prompted, deceived, or instructed to alter normal workflows.
3. **No Forced Hazards:** Test crews are strictly forbidden from stepping into vehicle paths to induce braking.
4. **Sampling Strategy:** `TARGET_SAMPLE_SIZE = TBD_AFTER_POWER_ANALYSIS`. Sample size calculation ($n = Z^2 p(1-p)/E^2$) is deferred until pilot phase measures empirical event prevalence.

---

## 17. HUMAN REVIEW TRANSITION & STRICT BLINDING

The protocol transition from raw capture to human review is governed by [review_transition_protocol.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/review_transition_protocol.json):

```mermaid
graph TD
    RAW[Captured Event Package] --> POST[Post-Capture Gating D1-D6]
    POST --> SAN[Blinding Sanitization Engine]
    
    SAN -->|STRIP ALL AI METRICS| SAN_PKG[Sanitized Review Package]
    
    SAN_PKG --> REV1[Blinded Adjudicator 1]
    SAN_PKG --> REV2[Blinded Adjudicator 2]
    SAN_PKG --> REV3[Blinded Adjudicator 3]
    
    REV1 & REV2 & REV3 --> ADJ[Consensus & Cohen Kappa Evaluation]
    ADJ --> GT[Committed Ground Truth Dataset]
```

### Strictly Forbidden Review Artifacts
To prevent cognitive confirmation bias, review packages **MUST NEVER CONTAIN**:
- AI risk scores or candidate rankings.
- YOLO bounding boxes or detection confidences.
- ByteTrack track IDs or trajectory predictions.
- Model H risk curves or braking margins.
- Automated screening labels from prior scripts.

---

## 18. DATA QUALITY GATES ARCHITECTURE

Quality gating is strictly bifurcated into pre-capture commissioning and post-capture verification:

```mermaid
graph LR
    subgraph PRE_CAPTURE_COMMISSIONING [Pre-Capture Commissioning Gates]
        C1[C1: CLOCK SYNC]
        C2[C2: CAMERA HEALTH]
        C3[C3: CAN TELEMETRY]
        C4[C4: SEC ZONE VIS]
        C5[C5: CALIBRATION]
        C6[C6: GEOMETRY]
    end
    
    PRE_CAPTURE_COMMISSIONING -->|All PASS| CAPTURE[INSTRUMENTATION_READY_FOR_CAPTURE]
    CAPTURE --> RUN[Execute Trial Run]
    RUN --> COMPLETE[CAPTURE_COMPLETED]
    
    subgraph POST_CAPTURE_VERIFICATION [Post-Capture Quality Gates]
        D1[D1: EVENT COMPLETENESS]
        D2[D2: SENSOR COMPLETENESS]
        D3[D3: PROVENANCE]
        D4[D4: FILE INTEGRITY]
        D5[D5: REPLAYABILITY]
        D6[D6: BLINDING SANITIZATION]
    end
    
    COMPLETE --> POST_CAPTURE_VERIFICATION
    POST_CAPTURE_VERIFICATION -->|All PASS| REVIEW[DATASET_READY_FOR_REVIEW]
```

---

## 19. FAIL-SAFE ABORT CRITERIA

The pilot execution terminates instantly upon any trigger codified in [abort_criteria.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/abort_criteria.json):

1. **Safety Marshal E-Stop Actuation:** Manual or wireless E-Stop depression ($\le 50\text{ ms}$ response).
2. **Exclusion Zone Intrusion:** Optical curtain or radar detects person in test buffer ($\le 100\text{ ms}$).
3. **PTP Grandmaster Unlock:** Loss of GNSS lock or clock state transition out of `SLAVE_SYNCHRONIZED`.
4. **Camera Frame Drop:** Any camera drops $\ge 1$ frame or loses RTSP link during active run.
5. **CAN Bus Timeout:** Telemetry gap $> 20\text{ ms}$ on speed or braking signals.
6. **Secondary Sensor Loss:** LiDAR/Radar packet drop exceeds $0.01\%$.
7. **Structural Vibration / Camera Shift:** Mount displacement $> 0.5^\circ$ detected via optical fiducials.
8. **Storage Buffer Congestion:** NVMe ingest buffer reaches $> 80\%$ capacity.

---

## 20. CRYPTOGRAPHIC PROVENANCE & CHAIN OF CUSTODY

Data integrity conforms to [chain_of_custody_schema.json](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_l/chain_of_custody_schema.json):
- **Merkle Tree Proofs:** Each event package computes a SHA-256 Merkle root incorporating video feeds, CAN telemetry, extrinsic transforms, and facility CAD models.
- **Write-Blocker Storage:** Raw ingest volumes operate with physical hardware write-blockers enabled.
- **Privacy Preservation:** All operator and technician IDs are pseudonymized (e.g. `OP-78A4B2`), eliminating PII.

---

## 21. PILOT ACCEPTANCE CRITERIA (FIRST CAPTURE REQUIREMENTS)

Before the first physical trial can record a single frame, the following conditions must be met:
1. `pilot_readiness_state` = **`INSTRUMENTATION_READY_FOR_CAPTURE`**.
2. All Pre-Capture Commissioning Gates **`C1` through `C6` = `PASS`**.
3. Safety Marshal signs physical site clearance manifest.
4. Emergency stop test confirms traction power cutoff within $\le 50\text{ ms}$.

---

## 22. OPERATIONAL LIMITATIONS

1. **Optical Occlusions:** Dense warehouse racking creates inescapable line-of-sight shadows beyond secondary aisle depths $> 25\text{ m}$.
2. **Dynamic Lighting:** Sun glare through skylights may degrade optical contrast during midday shifts.
3. **Vehicle Diversity:** CAN signal maps must be individually validated per forklift make/model.

---

## 23. WHAT THIS PILOT DOES NOT ESTABLISH

To eliminate ambiguity, this protocol explicitly declares what it **CANNOT** prove:

```
[ PILOT CAPTURE CAN ESTABLISH ]
  +-- Instrumentation is operational and synchronized.
  +-- Multi-modal data capture is repeatable and complete.
  +-- Event packages can be created with tamper-evident provenance.
  +-- Pre-capture and post-capture quality gates function deterministically.

[ PILOT CAPTURE DOES NOT ESTABLISH ]
  X-- Safety backfire validation in the real world.
  X-- Algorithmic safety or mitigation efficacy.
  X-- Model H validation or parameter correctness.
  X-- Production readiness of any backfire detector.
  X-- Ground truth establishment prior to human adjudication.
```

---

## 24. FINAL GOVERNANCE AUDIT DECLARATION

```
========================================================================================
FINAL AUDIT DECLARATION:
Milestone V3.4-L is successfully completed. All schemas, protocols, safety plans,
and state machines have been formalized and written to disk under outputs/v3_4_l/.
Zero real-world data collection has occurred. Model H and Production Generators
remain completely frozen and unchanged.
========================================================================================
```
