# V3.4-J — Field Dataset & Instrumentation Specification

**Milestone Identifier**: V3.4-J  
**Document Title**: Field Dataset Architecture, Multi-Modal Sensor Instrumentation, and Evidence Contract Specification  
**Execution Context**: Pure Specification & Engineering Design (No Data Collection, No Model Training)  
**Target Repository**: `safety-backfire-ai`  
**Execution Date**: 2026-10-01  
**Governance State**: `HUMAN_REVIEW = BYPASSED` | `SAFETY_BACKFIRE_GT = NOT_ESTABLISHED` | `SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED` | `PERCEPTION_METRICS = NOT_ESTABLISHED` | `MODEL_H = FROZEN_INVARIANT` | `PRODUCTION_MODEL = UNCHANGED` | `REAL_WORLD_BACKFIRE_VALIDATION = NOT_ESTABLISHED` | `FIELD_DATASET = SPECIFIED_NOT_COLLECTED`

---

## Executive Summary

Milestones V3.4-E through V3.4-I rigorously established that existing warehouse surveillance footage (such as `Warehouse_026` and `Warehouse_027` from the NVIDIA SmartSpaces dataset) is **fundamentally incapable of validating or refuting safety backfire hypotheses**. In Milestone V3.4-I, 100% of eligible events (38/38) were blocked at Gate 2 because ceiling-mounted monocular CCTV cameras looking down central transit aisles cannot see past solid pallet racks into adjacent cross-aisles (`secondary_depth_visible == False` in 38/38 events). Furthermore, vehicle CAN telemetry was completely absent, and secondary hazard states could not be measured.

Milestone **V3.4-J** bridges this empirical gap. It translates the forensic learnings of V3.4-E $\to$ V3.4-I into the first formal **Field Dataset & Instrumentation Specification** engineered specifically around **Event-Level Causal Evidence** rather than generic object detection.

This document establishes:
1. A **4-Camera Spatial Architecture** (Cameras A, B, C, D) that directly eliminates the 0/38 cross-aisle depth occlusion bottleneck and prevents tracker ID swaps.
2. A **Vehicle Telemetry Contract** specifying mandatory 50–100 Hz CAN bus signals (speed, deceleration, brake state/pressure, steering angle, yaw rate).
3. A **Comparative Evaluation of Three Secondary Sensing Alternatives** (Multi-Camera vs. 3D LiDAR vs. Independent Occupancy Networks) without premature selection.
4. A **Rigorous Dual-Blinded Human Ground Truth Protocol** with a 3-class taxonomy, Cohen's Kappa agreement metrics, and cryptographic audit logs.
5. An **Ethics-First Experimental Protocol** strictly prohibiting human endangerment while enabling controlled counterfactual trials via certified soft foam mannequins and remote E-Stop overrides.
6. A **Facility-Level Holdout Partitioning Strategy** ensuring zero spatial data leakage between training, development, validation, and held-out test facilities.

---

## 1. Scope & Constraints

This milestone operates strictly under specification mode:
- **No Data Collection**: No physical recording campaigns are initiated.
- **No Code Mutation**: Production scripts (`discover_event_candidates.py` and `automated_evidence_screening.py`) remain untouched.
- **No Ground Truth Creation**: Verified ground-truth records remain 0.
- **No Model Modification**: Model H parameters remain frozen invariants ($k_0 = 2.40, \beta_d = 0.08, \beta_l = 0.12, \beta_{\text{pitch}} = 0.22$).
- **No Perception Metrics**: Precision, Recall, F1, Sensitivity, Specificity, and False Alarm Rates (FAR) remain uncomputed and unestablished.

---

## 2. Governance Invariants

```yaml
MILESTONE_STATUS: V3_4_J_FIELD_DATASET_SPECIFICATION_COMPLETED
PRODUCTION_MODEL: UNCHANGED
MODEL_H: FROZEN_INVARIANT
SAFETY_BACKFIRE_GT: NOT_ESTABLISHED (Verified Records = 0)
SAFETY_BACKFIRE_VALIDATION: NOT_ESTABLISHED
REAL_WORLD_BACKFIRE_VALIDATION: NOT_ESTABLISHED
CURRENT_GENERATOR: PRIMARY_NEAR_MISS_FILTER
BACKFIRE_AWARE_IMPLEMENTATION: SANDBOX_ONLY
FIELD_DATASET: SPECIFIED_NOT_COLLECTED
STOP_CONDITION: V3_4_J_FIELD_DATASET_SPECIFICATION_COMPLETED
```

---

## 3. Semantic Correction of Milestone V3.4-I

Prior to formulating new specifications, this document incorporates the semantic correction detailed in [`outputs/v3_4_j/v3_4_i_gate_semantics_correction.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/v3_4_i_gate_semantics_correction.md):

> [!NOTE]
> **Sequential Gate Semantics Correction**:  
> In Milestone V3.4-I, all 38 eligible events had `FIRST_BLOCKING_GATE = G2` due to complete secondary depth occlusion. In a sequential state machine where gates act as cascading preconditions ($G1 \to G2 \to G3 \to G4$), the failure of Gate G2 causes immediate **short-circuiting**.  
> Therefore, in live sequential execution:
> $$\mathbf{G3 = NOT\_EVALUATED}, \quad \mathbf{G4 = NOT\_EVALUATED}$$
> The G4 confounder records noted in V3.4-I represent **`PRIOR_FORENSIC_EVIDENCE`** inherited from the manual V3.4-E audit, **not** live outputs of a gate reached during sequential processing. This clarification ensures future sensor deployments focus squarely on unblocking the true physical bottleneck: **Gate 2 Observability**.

---

## 4. Field Dataset Purpose: Event-Level Causal Evidence vs. Object Detection

Conventional computer vision datasets (e.g., COCO, Pascal VOC, KITTI) are structured around static 2D/3D object detection bounding boxes. While suitable for training perception backbones, they are fundamentally inadequate for studying **Safety Backfire**.

Safety backfire is a **dynamic, causal, multi-agent process** governed by the following sequence:
$$\text{Primary Risk} \xrightarrow{\text{Trigger}} \text{Intervention} \xrightarrow{\text{Kinematics}} \text{Primary Risk Reduction} \xrightarrow{\text{Redirection}} \text{Secondary Risk Increase}$$

To capture this phenomenon, the dataset must record:
1. **Kinetic Control Inputs**: Actual brake pressure and steering angles proving an active avoidance maneuver occurred.
2. **Multi-Zone Spatial Line-of-Sight**: Unbroken optical or volumetric monitoring of both primary and secondary zones throughout the entire propagation window.
3. **Causal Non-Interference**: Spatio-temporal proof that no independent external forklifts or pedestrian crowds entered the secondary zone to confound the risk delta.
4. **Time-Aligned Multimodal Streams**: Hardware-timestamped fusion of video, CAN telemetry, and environmental sensors within a strict error budget.

---

## 5. Master Architecture Diagram

Below is the required system architecture defining how physical signals flow from instrumentation through event packaging to ground-truth adjudication and validation:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               MULTI-MODAL SENSOR ACQUISITION                           │
├─────────────────────┬──────────────────────┬────────────────────┬──────────────────────┤
│ 4-Camera Multi-View │ Vehicle CAN Telemetry│ Secondary Sensors  │  Facility Geometry   │
│  (Cameras A, B, C, D)│ (Speed, Steer, Brake)│ (LiDAR / UWB / RGB)│  (Surveyed Polygons) │
└──────────┬──────────┴──────────┬───────────┴─────────┬──────────┴──────────┬───────────┘
           │                     │                     │                     │
           └─────────────────────┴──────────┬──────────┴─────────────────────┘
                                            ▼
                       ┌────────────────────────────────────────┐
                       │   IEEE 1588 PTP TIME SYNCHRONIZATION   │
                       │   (Master Skew Budget <= 33.3ms)       │
                       └────────────────────┬───────────────────┘
                                            ▼
                       ┌────────────────────────────────────────┐
                       │      STANDARDIZED EVENT PACKAGE        │
                       │   (Dynamic PRE, INTERV, POST Windows)  │
                       └────────────────────┬───────────────────┘
                                            ▼
                       ┌────────────────────────────────────────┐
                       │      V3.4-G/H EVIDENCE CONTRACT        │
                       │   (G1 Interv -> G2 Obs -> G3 Delta ->   │
                       │    G4 Causal Isolation)                │
                       └────────────────────┬───────────────────┘
                                            ▼
                       ┌────────────────────────────────────────┐
                       │  DUAL-BLINDED HUMAN GT ADJUDICATION    │
                       │  (Rev 1 + Rev 2 + Lead Arbitrator)     │
                       └────────────────────┬───────────────────┘
                                            ▼
                       ┌────────────────────────────────────────┐
                       │    FACILITY-LEVEL HOLDOUT SPLIT        │
                       │  (Train, Dev, Internal Val, Held-Out)  │
                       └────────────────────┬───────────────────┘
                                            ▼
                       ┌────────────────────────────────────────┐
                       │        BACKFIRE MODEL VALIDATION       │
                       │   (Executed ONLY on Held-Out Facility) │
                       └────────────────────────────────────────┘
```

---

## 6. Camera Architecture (Cameras A, B, C, D)

As specified in [`camera_coverage_contract.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/camera_coverage_contract.json), a minimum of **four synchronized camera views** per monitored intersection/junction is required:

| Camera Node | Designated Role | Mounting Position & Height | FOV (H / V) | Resolution & FPS | Target Coverage Zone | Blind Spot Profile |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **CAMERA_A** | Primary Interaction View | Corridor centerline, 5.0m height, 25° pitch down aisle | 84° / 52° | 1920x1080 @ 30–60 fps | Primary transit corridor (2.0m to 28.0m depth, 4.5m lane width) | Floor space directly underneath camera; interior depth of cross-aisles. |
| **CAMERA_B** | Secondary-Zone Entry View | Rack upright at aisle intersection, 4.5m height, 45° yaw | 65° / 40° | 1920x1080 @ 30–60 fps | Cross-aisle entrance threshold (1.5m to 15.0m depth, 5.0m width) | Interior cross-aisle depth beyond 4.0m into rack rows (blocked by pallet racks). |
| **CAMERA_C** | **Secondary-Zone Depth View** | **Aisle interior apex looking inward**, 4.0m height, 18° pitch | **52° / 32°** | **1920x1080 @ 30–60 fps** | **Cross-aisle interior depth (2.0m to 30.0m depth, 3.2m width)** | **SOLVES 0/38 OCCLUSION BOTTLENECK**: Directly observes depth behind racks; blind only behind 2.2m+ pallets. |
| **CAMERA_D** | Overlapping Cross-View & Continuity | High diagonal corner mount, 6.5m height, 45° pitch | 92° / 60° | 2560x1440 @ 30–60 fps | Global junction overlap bridging Cameras A, B, and C (12.0m span) | Topmost pallet tier shadow zones; maintains continuous tracking to prevent ID swaps. |

*Status: Cameras A, B, and C are `REQUIRED_SPECIFICATION`; Camera D is `PROPOSED` for tracking continuity.*

---

## 7. Temporal Synchronization & Error Budget

As detailed in [`field_sensor_contract.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/field_sensor_contract.json):
- **Grandmaster Protocol**: IEEE 1588 PTP v2 (Precision Time Protocol) operating across a dedicated Gigabit Ethernet sensor VLAN.
- **Clock Domain**: TAI (International Atomic Time) with standardized UTC offset.
- **Synchronization Error Budget Breakdown**:
  - Camera hardware trigger jitter: $\le 2.0\text{ ms}$
  - CAN bus gateway timestamp latency: $\le 5.0\text{ ms}$
  - Secondary sensor network latency: $\le 8.0\text{ ms}$
  - Operating system inter-process jitter: $\le 3.0\text{ ms}$
  - **Total Composite Skew Budget**: $\mathbf{\le 33.3\text{ ms}}$ (Designated as `CURRENT_DESIGN_TARGET`).
- **Rationale**: A composite budget of $\le 33.3\text{ ms}$ matches the duration of a single 30 fps video frame, ensuring control inputs map to the identical visual epoch without temporal aliasing.

---

## 8. Vehicle Telemetry Contract

As formalized in [`telemetry_contract.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/telemetry_contract.json), vehicles must be instrumented to stream the following nine physical signals via CAN bus / IMU:

| Signal Identifier | Physical Unit | Target Rate | Requirement Level | Purpose in Evidence Contract | Known Failure Mode |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `timestamp_utc_us` | Microseconds | 100 Hz | **MANDATORY** | Global chronological baseline for all signals | Timestamp gap $> 20\text{ms}$ or clock drift |
| `vehicle_speed_mps` | m/s | 50 Hz | **MANDATORY** | Verify approach velocity and dead stop | Zero-speed drift or wheel slip |
| `wheel_speed_rad_per_s` | rad/s | 50 Hz | HIGHLY_DESIRABLE | Slip, traction loss, and differential braking | Encoder pulse dropout from dust |
| `longitudinal_acceleration_mps2` | m/s² | 100 Hz | **MANDATORY** | Deceleration rate for Gate G1 confirmation | Floor joint vibration noise |
| `brake_state` | Discrete Enum | 100 Hz | **MANDATORY** | Direct confirmation of brake pedal actuation | Switch contact bounce or corrosion |
| `brake_hydraulic_pressure_kpa` | kPa | 50 Hz | HIGHLY_DESIRABLE | Physical caliper clamping force measurement | Transducer zero-offset drift |
| `steering_angle_deg` | Degrees | 50 Hz | **MANDATORY** | Detect lateral swerving toward secondary zone | Centering offset calibration drift |
| `yaw_rate_deg_per_s` | deg/s | 100 Hz | **MANDATORY** | Chassis turning rate confirming swerve path | Gyroscope thermal bias drift |
| `throttle_position_pct` | Percent (0–100) | 50 Hz | **MANDATORY** | Verify throttle release and driver reaction time | Potentiometer deadband wear |

*Policy Note: No physical threshold values (e.g., specific deceleration m/s² or steering degrees) are defined here; thresholds must be calibrated per vehicle chassis type.*

---

## 9. Secondary Zone Instrumentation: Three Sensing Alternatives

To resolve the core empirical limitation (`secondary_depth_visible == False` in 38/38 events), [`secondary_zone_sensor_contract.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/secondary_zone_sensor_contract.json) formulates three architectural options without prematurely declaring a winner:

### Option A: Multi-Camera Inward Optical Monitoring (Camera C)
- **Architecture**: Dedicated inward-facing optical camera mounted at the closed end or ceiling apex of the cross-aisle.
- **Capabilities**: Rich 2D texture, human posture, worker activity (picking, climbing), fine-grained semantics.
- **Limitations**: Optical line-of-sight remains vulnerable if workers crouch behind floor pallets; sensitive to warehouse lighting changes and dust.
- **Calibration**: Multi-camera extrinsic homography wand calibration (reprojection error $\le 1.5\text{ px}$).

### Option B: Overhead 3D Solid-State LiDAR
- **Architecture**: Solid-state LiDAR mounted at the cross-aisle ceiling junction scanning the entire 30m aisle volume.
- **Capabilities**: Direct metric 3D point clouds, millimeter spatial accuracy, velocity vectors, immune to shadows and darkness.
- **Limitations**: Cannot classify semantic identity (cannot distinguish between a worker, low pallet jack, or fallen cargo); high-bay shrink-wrap causes specular reflection flares.
- **Calibration**: LiDAR-to-camera ICP registration against retro-reflective calibration targets ($\le 20\text{ mm}$ translation error).

### Option C: Independent Occupancy Sensor Network (UWB + Safety Light Curtains)
- **Architecture**: Ultra-Wideband (UWB) worker tracking tags combined with vertical safety light curtains across the aisle entrance.
- **Capabilities**: Decimeter micro-location, instant perimeter crossing triggers, 100% immune to visual occlusions and lighting.
- **Limitations**: Completely blind to un-tagged visitors, temporary staff, or fallen physical cargo; cannot observe human body posture.
- **Calibration**: Total Station theodolite surveying of fixed UWB anchor positions ($\le 10\text{ mm}$ datum error).

*Recommendation: Deploy Option A as the primary baseline during initial field trials, supplemented by Option B or C at high-risk blind intersections.*

---

## 10. 3D Geometry Contract & Spatial Calibration

- **Coordinate System**: Facility Global Datum Metric XYZ (surveyed via architectural blueprints and laser theodolites).
- **Camera Intrinsics**: Full Brown-Conrady pinhole model ($f_x, f_y, c_x, c_y, k_1, k_2, p_1, p_2, k_3$) calibrated via large-format planar checkerboards.
- **Extrinsics**: 6-DOF Euclidean rigid transformation matrix $[R \mid T]$ per camera relative to the facility origin.
- **When 2D Ground Homography Suffices**:
  - Planar warehouse concrete slab with $< 20\text{ mm}$ elevation variance.
  - Tracking vehicle tire patches, pedestrian footfalls, and 2D ground zone boundary crossings.
- **When 3D Reconstruction is Mandatory**:
  - Pallet racking stacks create vertical volumetric occlusions across cross-aisle lines-of-sight.
  - Forklift mast elevation lifts loads into the overhead camera field-of-view.
  - Dynamic ray-casting against a 3D facility CAD model is required to compute real-time visibility masks.

---

## 11. Event Recording Protocol & Dynamic Window Sizing

As specified in [`event_capture_protocol.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/event_capture_protocol.json), static window durations (such as arbitrary 8.0s clips) are discarded in favor of **Dynamic Kinematic Window Sizing**:

1. **PRE Window ($T_{\text{pre}}$)**:
   $$T_{\text{pre}} = \max\left(3.0\text{s}, \frac{d_{\text{approach}}}{v_{\text{approach}}}\right)$$
   Captures unperturbed baseline trajectories, velocities, and initial secondary zone occupancy prior to interaction onset.
2. **INTERVENTION Window ($T_{\text{interv}}$)**:
   Spans from the first CAN telemetry trigger (brake active, deceleration $> 1.0\text{ m/s}^2$, or steering rate $> 15^\circ/\text{s}$) until completion of the avoidance maneuver or complete vehicle stop (typically 1.5s to 5.0s).
3. **POST Window ($T_{\text{post}}$)**:
   $$T_{\text{post}} = \max\left(4.0\text{s}, \tau_{\max} + t_{\text{stabilization}}\right)$$
   *Constraint Policy*: $\tau_{\max} = 2.0\text{s}$ is maintained as a **`CURRENT_SPECIFICATION_CONSTRAINT`** (not an empirically proven universal constant). The post window must run at least 4.0s to verify whether secondary hazards emerge.

---

## 12. Required Negative and Positive Scenarios

To ensure the dataset does not suffer from selection bias, data collection campaigns must intentionally target nine distinct scenario types:
1. **SAFE_COMPLETE_STOP** (Negative Control): Close approach leading to emergency braking to a full stop without lateral swerve; secondary zone unpenetrated.
2. **SAFE_CLEARANCE** (Negative Control): Nominal passing maneuver where both agents clear the lane safely.
3. **SWERVE_WITHOUT_SECONDARY_RISK** (Negative Control): Evasive swerve into an observable adjacent aisle that is verified empty.
4. **SECONDARY_RISK_FROM_INDEPENDENT_ACTOR** (Confounded Control): Primary intervention occurs; secondary risk rises due to an unlinked pedestrian crowd or independent forklift entering.
5. **SECONDARY_RISK_FROM_PRIMARY_INTERVENTION** (Positive Target): Vehicle swerves to avert primary collision and encroaches into an occupied, observable secondary zone.
6. **TRACK_HANDOFF_ANOMALY** (Perception Stress Test): Vehicle swerves during rapid rotation, testing state machine rejection upon tracker ID swap.
7. **OCCLUDED_SECONDARY_SPACE** (Observability Stress Test): Vehicle swerves toward a cross-aisle whose interior is occluded, testing state machine refusal to classify.
8. **UNKNOWN_CONFOUNDER_BLIND_SPOT** (Causal Stress Test): Secondary risk increases near a blind facility doorway, testing state machine routing to `INSUFFICIENT_EVIDENCE`.
9. **TRUNCATED_OBSERVATION_WINDOW** (Temporal Stress Test): Video buffer drops within 2.0s of intervention, testing temporal completeness rejection.

---

## 13. Controlled Safety Trials vs. Naturalistic Operational Events

To balance experimental control against real-world operational realism:

### Category 1: Controlled Safety Trials (Protocolized Experiments)
- **Purpose**: Systematically isolate counterfactuals (paired Run A baseline vs. Run B intervention) under controlled parameters.
- **Mandatory Safety & Ethics Boundary**:
  - **ZERO HUMAN ENDANGERMENT**: Under no circumstances may a human participant stand in the potential travel envelope of a moving vehicle.
  - Primary collision targets must be certified soft foam mannequins or deformable obstacles.
  - Human test actors in secondary zones must be protected by physical impact barriers or certified safety cages.
  - Test vehicles must feature a remote wireless Emergency Stop (E-Stop) operated by a designated safety marshal.

### Category 2: Naturalistic Operational Capture (Ambient Facility Monitoring)
- **Purpose**: Capture continuous multi-camera operational logistics footage during active shifts to prevent overfitting to artificial trial behaviors.
- **Extraction Mechanism**: Automated telemetry-triggered logging buffering footage whenever CAN deceleration exceeds $1.5\text{ m/s}^2$.

---

## 14. Dual-Blinded Human Ground Truth Protocol

As specified in [`gt_adjudication_protocol.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/gt_adjudication_protocol.json):
- **Reviewer Roles**:
  - **Reviewer 1**: Certified Safety Professional (CSP / PE) with mobile equipment expertise.
  - **Reviewer 2**: Independent Human Factors & Ergonomics Safety Engineer.
  - **Lead Adjudicator**: Senior Safety Research Scientist serving as independent arbitrator.
- **Blinding Protocol**: Reviewers are completely blinded to each other, to AI candidate scores, to Model H characterizations, and to detector bounding boxes.
- **Review Interface**: Time-aligned multi-view player displaying Cameras A, B, C, D in 60 Hz lockstep alongside synchronized CAN telemetry traces.
- **Proposed GT Taxonomy**:
  1. `CONFIRMED_BACKFIRE`: Intervention confirmed + complete observability + secondary hazard increase + causal link validated + confounders excluded.
  2. `NO_BACKFIRE_OBSERVED`: Intervention confirmed + secondary zone observable + zero secondary hazard increase.
  3. `INSUFFICIENT_EVIDENCE`: Secondary depth occluded OR unconfirmed confounder OR missing telemetry.
- **Inter-Rater Consensus**: Measured via Cohen's Kappa ($\kappa \ge 0.80$ required for acceptance). Any discrepancy automatically triggers Lead Adjudication.
- **Audit Log**: Immutable SHA256 hash-chained JSONLines record storing all reviewer timestamps, forms, and digital signatures.

---

## 15. Facility-Level Holdout Partitioning Strategy

As formalized in [`dataset_readiness_schema.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_j/dataset_readiness_schema.json):
- **The Spatial Leakage Trap**: Random frame-level or event-level splits within the same facility cause catastrophic data leakage, because the model memorizes static background textures, specific rack configurations, and camera mount angles.
- **Mandatory Stratified Holdout**:
  - **Training Set**: Facilities 01 and 02 (Used for candidate discovery and parameter exploration).
  - **Development Set**: Facility 03 (Used for hyperparameter tuning and sensitivity analysis).
  - **Internal Validation Set**: Facility 04 (Pre-deployment benchmark testing).
  - **HELD-OUT BENCHMARK FACILITY**: **Facility 05 (Completely Unseen Physical Facility)**.
- **Quarantine Rule**: The Held-Out Facility must feature a completely different physical layout, racking height, and lighting architecture, and must remain strictly quarantined until final model validation.

---

## 16. Pre-Ingestion Data Quality Gates

Before any recorded event enters the validated research dataset, it must pass eight automated quality gates:
1. `G_CAMERA_SYNC`: Inter-camera frame capture time delta $\le 5.0\text{ ms}$.
2. `G_SENSOR_SYNC`: CAN bus telemetry to video frame synchronization delta $\le 20.0\text{ ms}$.
3. `G_CALIBRATION`: Ground-plane homography reprojection error $\le 1.5\text{ pixels}$.
4. `G_ZONE_MAPPING`: 2D/3D polygons defined and surveyed for all zones.
5. `G_TELEMETRY`: CAN signal continuity verified (zero missing packets $> 50\text{ms}$).
6. `G_OCCLUSION`: Secondary zone interior depth line-of-sight confirmed (Camera C or LiDAR active).
7. `G_EVENT_COMPLETENESS`: Unclipped PRE ($\ge 3\text{s}$), INTERVENTION ($\ge 1.5\text{s}$), and POST ($\ge 4\text{s}$) windows.
8. `G_GT_COMPLETENESS`: Dual-blinded human review completed with signed cryptographic audit log.

*Acceptance Policy: Standard ML perception metrics (Accuracy, F1, Precision, Recall) are explicitly forbidden as acceptance criteria at this stage; only Dataset Readiness and Evidence Completeness metrics are evaluated.*

---

## 17. Statistical Sample Size & Power Analysis Requirements

- **Current Status**: Designated as `TBD_AFTER_POWER_ANALYSIS`.
- **Parametric Formula**:
  $$n = \frac{Z_{\alpha/2}^2 \cdot p \cdot (1 - p)}{E^2}$$
- **Required Inputs Prior to Final Integer Selection**:
  1. Estimated true backfire prevalence ($p$) derived from initial operational pilot screening.
  2. Target confidence level ($1 - \alpha = 95\%$, $Z = 1.96$).
  3. Acceptable margin of error ($E$, e.g., $\pm 3\%$).
  4. Statistical power ($1 - \beta \ge 80\%$) for distinguishing baseline vs. intervention risk distributions.
- **Policy**: No arbitrary event count numbers are fabricated; sample size will be derived following pilot prevalence estimation. Minimum facility count is fixed at $\ge 3$ distinct industrial sites.

---

## 18. Explicit Answers to the 10 Core Questions (Section 29)

### 1. What is the absolute minimum sensor configuration that allows observing secondary depth?
The minimum viable sensor configuration is **Two Synchronized Cameras**:
- **Camera 1**: Monocular corridor camera monitoring the primary interaction lane.
- **Camera 2**: Dedicated cross-aisle camera mounted at the ceiling apex looking directly down the interior length of the secondary rack aisle.  
*(Without Camera 2, secondary depth line-of-sight is physically occluded by pallet racking in 100% of cases).*

### 2. When are two cameras sufficient?
Two cameras are sufficient **only in simple, single-junction, straight-line geometries** where:
1. The vehicle approaches from a single predictable direction along the primary corridor.
2. The secondary zone consists of a single cross-aisle with no branching corridors.
3. The primary camera and secondary camera share an overlapping ground plane ($\ge 25\%$) at the aisle entrance, allowing continuous tracking without a blind transition zone.

### 3. When are three or four cameras required?
Three or four cameras are required whenever:
1. **Four-Way Cross Intersections**: The primary aisle intersects cross-aisles on both the left and right sides (requiring Camera A for primary lane, Camera B for left aisle depth, Camera C for right aisle depth).
2. **Tracker Discontinuity / ID Handoffs**: Vehicles execute rapid rotational swerves exceeding camera FOV boundaries, necessitating a high-angle diagonal cross-view (Camera D) to bridge views and prevent tracker ID swaps.
3. **High-Bay Volumetric Occlusion**: Pallet loads on lower rack tiers block ground-level visibility, requiring multiple overlapping sightlines to eliminate blind pockets.

### 4. What is the minimum viable CAN telemetry?
The absolute minimum viable CAN telemetry signals are:
1. **`vehicle_speed`** (m/s, 50 Hz): To verify approach kinematics and confirm complete stop.
2. **`brake_state`** (Digital Boolean/Enum, 100 Hz): To definitively distinguish active brake application from passive deceleration.
3. **`longitudinal_acceleration`** (m/s², 100 Hz): To quantify braking severity and onset rate.
4. **`steering_angle`** (Degrees, 50 Hz): To detect evasive swerving toward secondary zones.

### 5. What information can be reliably extracted from video alone?
From calibrated multi-camera video alone, systems can reliably extract:
1. 2D/3D bounding box trajectories and centroid velocities of visible agents.
2. Spatial separation distances and ground-plane zone boundary crossings.
3. Macro-level visual kinematics (halting, gross pedestrian yielding, lateral vehicle translation).
4. Qualitative actor classifications (pedestrian vs. forklift vs. stationary pallet).
5. Environmental lighting conditions (lux levels) and visual line-of-sight occlusion masks.

### 6. What CANNOT be extracted from video alone?
Video alone cannot reliably extract:
1. **True Control Intent**: Whether vehicle deceleration was automated emergency braking, human foot-brake pressure, regenerative braking, or unpowered coasting.
2. **Hidden / Occluded Hazards**: Presence, movement, or exposure of workers positioned behind solid pallet racks or opaque cargo.
3. **Physical Caliper Clamping Pressure**: The mechanical braking force exerted by vehicle hydraulics.
4. **True Ground Contact Forces**: Tire slippage, skid dynamics, and floor friction coefficients.
5. **Causal Confounder Proof in CCTV Blind Spots**: Verifying whether an unseen worker entered a cross-aisle from a blind emergency exit.

### 7. What must remain strictly independent of Model H?
The following four components must remain completely decoupled from Model H:
1. **Ground Truth Acquisition**: Human adjudication labels must never consult Model H risk scores.
2. **Primary Candidate Discovery**: Event identification must rely on raw physical telemetry and kinematic convergence, not Model H score thresholds.
3. **Sensor Quality Gates**: Camera synchronization and calibration verification must be purely physical checks.
4. **Secondary Risk Ground Truth**: True secondary hazard states must be measured via verified spatial exposure, not calculated via Model H formula coefficients.

### 8. How do we prevent the creation of pseudo-ground-truth?
To prevent pseudo-ground-truth:
1. **No Algorithmic Auto-Labeling**: Outputs of AI detectors, tracker scores, or Model H formulas must never be converted into ground-truth annotations.
2. **Strict Dual-Blind Adjudication**: Reviewers must see only raw synchronized video and CAN telemetry ribbons, with all AI bounding boxes and candidate scores stripped.
3. **Mandatory `INSUFFICIENT_EVIDENCE` Class**: Whenever secondary depth is occluded or telemetry is absent, reviewers are forbidden from defaulting to `NO_BACKFIRE`; the event must be labeled `INSUFFICIENT_EVIDENCE`.
4. **Cryptographic Audit Chains**: All review submissions must be signed and committed to an append-only, tamper-evident JSONLines audit log.

### 9. How do we prevent data leakage between facility splits?
Data leakage is prevented by enforcing **Facility-Level Stratified Holdout**:
1. Zero sharing of facilities between splits: Models trained on Facilities 01 and 02 must never see footage from Facility 03 (Dev) or Facility 04 (Internal Val).
2. **Quarantined Benchmark Facility**: Facility 05 must remain completely unseen, featuring different architectural layouts, rack upright spacing, floor coatings, and ambient luminaire types.
3. Prohibition of Random Frame Splitting: Random frame-by-frame or event-by-event splitting within the same facility is strictly banned.

### 10. What is the absolute minimum threshold required before true validation can begin?
True real-world validation cannot begin until all of the following six milestones are verified:
1. **Instrumented Facility Deployed**: At least one physical facility instrumented with the 4-Camera architecture and verified PTP time synchronization ($\le 33.3\text{ ms}$ composite skew).
2. **CAN Telemetry Integrated**: Active vehicle fleet logging speed, acceleration, brake switch, and steering angle at $\ge 50\text{ Hz}$.
3. **Secondary Depth Line-of-Sight Verified**: Camera C or LiDAR confirming direct visibility down cross-aisle interiors (`secondary_depth_visible == True`).
4. **Targeted Scenarios Collected**: Minimum representation of safe stops, swerves without secondary risk, confounded entries, and true backfire cascades.
5. **Dual-Blind Human GT Completed**: Independent safety experts adjudicating events with Cohen's Kappa $\ge 0.80$.
6. **Held-Out Facility Quarantined**: A separate physical site reserved exclusively for the validation run without prior exposure.

---

## 19. Final Governance State Declaration

```yaml
MILESTONE_STATUS: V3_4_J_FIELD_DATASET_SPECIFICATION_COMPLETED
PRODUCTION_MODEL: UNCHANGED
MODEL_H: FROZEN_INVARIANT (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
SAFETY_BACKFIRE_GT: NOT_ESTABLISHED
SAFETY_BACKFIRE_VALIDATION: NOT_ESTABLISHED
REAL_WORLD_BACKFIRE_VALIDATION: NOT_ESTABLISHED
CURRENT_GENERATOR: PRIMARY_NEAR_MISS_FILTER
BACKFIRE_AWARE_IMPLEMENTATION: SANDBOX_ONLY
FIELD_DATASET: SPECIFIED_NOT_COLLECTED
STOP_CONDITION: V3_4_J_FIELD_DATASET_SPECIFICATION_COMPLETED
```

---
*Report compiled autonomously in accordance with Milestone V3.4-J governance mandates.*
