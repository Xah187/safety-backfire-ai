# Milestone V3.4-E — Observability & Candidate Disposition Audit Report

**Document ID:** `V3_4_E_OBSERVABILITY_AUDIT_REPORT`  
**Milestone Version:** V3.4-E  
**Timestamp:** 2026-10-01  
**Repository:** `safety-backfire-ai`  
**Governance State:**  
- `HUMAN_REVIEW = BYPASSED`  
- `SAFETY_BACKFIRE_GT = NOT_ESTABLISHED`  
- `SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED`  
- `PERCEPTION_METRICS = NOT_ESTABLISHED`  
- `AUTOMATED_SCREENING_LABEL != GROUND_TRUTH_LABEL`  
- `SCREENING_DISPOSITION != GROUND_TRUTH_LABEL`  

---

## 1. Scope

This milestone performs a systematic observational and forensic audit across the complete pool of **51 union events** derived from NVIDIA PhysicalAI-SmartSpaces captures in `Warehouse_026` and `Warehouse_027`. 

Specifically, this audit:
1. Evaluates all **38 eligible events** across **5 standardized Observability dimensions** to determine whether monocular surveillance video provides sufficient empirical visibility to detect primary interventions, hazard transitions, and secondary risk cascades.
2. Preserves the **13 ineligible events** (`window_valid = False`) without causal analysis under the status `INELIGIBLE_WINDOW`.
3. Categorizes each eligible event under a strict **Screening Disposition** (`BACKFIRE_CANDIDATE_RETAINED`, `NO_BACKFIRE_OBSERVED`, `INSUFFICIENT_OBSERVABILITY`, or `INELIGIBLE_WINDOW`).
4. Re-evaluates the 5 automated candidates from V3.4-D and the 33 remaining eligible events against physical camera perspectives, storage rack occlusions, and operational confounders.

---

## 2. Method

The audit was executed empirically using direct frame inspection, calibrated camera homography matrices, and temporal trajectory ledgers from RUN_003 and RUN_004:
- **Clip Verification:** All 38 eligible event packages (`before.mp4`, `intervention.mp4`, `after.mp4`) were verified on disk for container readability, codec compliance, frame counts, and fps stability (30.0 fps).
- **Temporal Alignment:** Frame timestamps were audited across PRE (baseline), INTERVENTION (conflict/avoidance), and POST (hazard propagation or resolution) windows.
- **Physical Zone Delineation:** Primary transit lanes and secondary storage rack aisles were mapped to calibrated camera views.
- **Displacement Auditing:** Post-intervention kinematic displacement was computed for vehicles to separate active trajectory swerves from complete stops.
- **Confounder Tagging:** Operational confounders (independent worker clusters, vehicle turnovers, shift routines) were isolated from intervention-induced reactions.

---

## 3. Observability Definitions

To maintain epistemic rigor and prevent conflating lack of visibility with safety, observability is classified along five orthogonal axes:

1. **`INTERVENTION_OBSERVABILITY`:**
   - `FULL`: The physical avoidance maneuver, deceleration, or pedestrian yield is unobstructed and clearly identifiable.
   - `PARTIAL`: The interaction is visible but obscured by distance, mild visual clutter, or partial foreground overlap.
   - `NONE`: The interaction occurs off-camera or behind total occlusions.
   - `UNKNOWN`: Insufficient evidence to determine.

2. **`PRIMARY_ZONE_OBSERVABILITY`:**
   - `FULL`: The entire primary conflict zone (corridor or intersection) is within the camera field of view.
   - `PARTIAL`: A portion of the primary zone is truncated by the frame edge or structural elements.
   - `NONE`: Primary zone is completely outside the frame.

3. **`SECONDARY_ZONE_OBSERVABILITY`:**
   - `FULL`: Both the access point and the interior depth of the secondary zone are fully unobstructed.
   - `PARTIAL`: The entrance to the adjacent rack aisle is visible, but interior storage slots are occluded by structural pallet racks.
   - `NONE`: The secondary zone is unobservable or geometrically undefined (`UNKNOWN`).

4. **`POST_EVENT_OBSERVABILITY`:**
   - `ADEQUATE`: The post-intervention window is $\ge 4.0$ seconds (nominally 8.0s / 240 frames) and clear of abrupt cuts.
   - `PARTIAL`: The window is between 2.0s and 4.0s.
   - `INADEQUATE`: The post-window is $< 2.0$ seconds or terminated by stream end.

5. **`CAUSAL_SEQUENCE_OBSERVABILITY`:**
   - `FULL`: The continuous physical chain ($\text{Intervention} \rightarrow \text{Primary Mitigation} \rightarrow \text{Redirection} \rightarrow \text{Secondary Risk Exposure}$) is unbroken.
   - `PARTIAL`: Individual links are visible, but the chain is interrupted by independent motion or partial occlusion.
   - `NONE`: No causal continuity can be tracked due to confounding, vehicle departures, or dense clutter.

---

## 4. 38-Event Observability Inventory

The 38 eligible events are distributed across 6 camera streams in two warehouse facilities:

| Camera Stream | Eligible Events | Primary Zone Description | Secondary Zone Description |
| :--- | :---: | :--- | :--- |
| **`Warehouse_026_Camera_0002`** | 5 | Central Transit Corridor | Adjacent Pallet Rack Aisle |
| **`Warehouse_027_Camera_0002`** | 5 | Central Transit Corridor | Adjacent Pallet Rack Aisle |
| **`Warehouse_027_Camera_0005`** | 16 | Staging / Transit Corridor | Adjacent Storage Racks |
| **`Warehouse_026_Camera_0000`** | 6 | Main Intersection / Corridor | Adjacent Storage Racks / Undefined |
| **`Warehouse_027_Camera_0006`** | 4 | Warehouse Cross-Aisle | Adjacent Pallet Storage |
| **`Warehouse_027_Camera_0003`** | 2 | Blind Corner / Cross-Aisle | Adjacent Rack / Undefined |

---

## 5. Intervention Observability Analysis

$$\text{Total Eligible} = 38$$
- **`FULL`**: 25 events (65.8%)
- **`PARTIAL`**: 13 events (34.2%)
- **`NONE`**: 0 events (0.0%)
- **`UNKNOWN`**: 0 events (0.0%)

In 25 events, the interaction between pedestrian and forklift occurred in open corridor space with clean line-of-sight. In 13 events, partial intervention visibility resulted from multi-vehicle visual overlap (e.g. `Warehouse_026_Camera_0002` frames 900–1400) or distance attenuation at frame edges (e.g. `Warehouse_026_Camera_0000`).

---

## 6. Primary Zone Observability Analysis

- **`FULL`**: 33 events (86.8%)
- **`PARTIAL`**: 5 events (13.2%)
- **`NONE`**: 0 events (0.0%)
- **`UNKNOWN`**: 0 events (0.0%)

All 5 `PARTIAL` events occurred in `Warehouse_026_Camera_0000` (`UNION_CAND_Warehouse_026_003` through `007`), where Forklift 2 operated along the extreme bottom border of the camera view ($y \approx 1060\text{--}1075$ px on a 1080p canvas), exhibiting edge truncation (`OBS_07_EDGE_TRUNCATION`).

---

## 7. Secondary Zone Observability Analysis

- **`FULL`**: 0 events (0.0%)
- **`PARTIAL`**: 36 events (94.7%)
- **`NONE`**: 2 events (5.3%)
- **`UNKNOWN`**: 0 events (0.0%)

### Critical Architectural Finding:
- **Secondary Zone Entry Visible:** 36 / 38 events (94.7%).
- **Secondary Zone Interior Depth Visible:** 0 / 38 events (0.0%).

In every warehouse camera perspective, heavy steel pallet racks loaded with boxed cargo completely occlude the visual interior of cross-aisles. While surveillance cameras capture agents entering or exiting the aisle threshold, the deep interior remains physically unobservable from fixed overhead CCTV cameras. The 2 `NONE` events represent human-discovered incidents where the secondary zone was inherently undefined (`UNKNOWN`).

---

## 8. Post-Event Observability Analysis

- **`ADEQUATE` ($\ge 4.0\text{s}$):** 35 events (92.1%)
- **`PARTIAL` ($2.0\text{s} \le t < 4.0\text{s}$):** 1 event (2.6%) — `UNION_CAND_Warehouse_027_025` ($t = 3.8\text{s}$)
- **`INADEQUATE` ($< 2.0\text{s}$):** 2 events (5.3%) — `UNION_CAND_Warehouse_027_006` ($t = 1.8\text{s}$) and `UNION_CAND_Warehouse_027_026` ($t = 2.4\text{s}$, truncated near stream termination).
- **`UNKNOWN`**: 0 events (0.0%)

35 events provided an uninterrupted 8.0-second (240 frames) post-window, sufficient to detect any delayed vehicle motion or pedestrian displacement.

---

## 9. Causal Sequence Observability Analysis

- **`FULL`**: 14 events (36.8%)
- **`PARTIAL`**: 10 events (26.3%)
- **`NONE`**: 14 events (36.8%)
- **`UNKNOWN`**: 0 events (0.0%)

Continuous causal sequences could only be verified in scenarios with minimal visual clutter where agents either passed safely and cleared the frame (14 events), or where interventions halted the vehicle without further propagation (e.g. `UNION_CAND_Warehouse_026_010`). In 14 events, the causal sequence was classified as `NONE` due to dense multi-vehicle traffic, track handoffs, or severe frame-edge truncation.

---

## 10. Occlusion Analysis

Across the 38 eligible events:
- **`NONE`**: 14 events (36.8%) — Clear open-aisle transits in Camera_0005, Camera_0006, and Camera_0002.
- **`PARTIAL`**: 17 events (44.7%) — Pallet rack pillars and storage borders partially masking agent bodies.
- **`HEAVY`**: 7 events (18.4%) — Intersecting vehicle bodies and severe frame-edge cutoffs.

---

## 11. Confounder Analysis

Causal Confounders were strictly distinguished from passive Background Context:
- **`CAUSAL_CONFOUNDER = YES`:** 14 events (36.8%)
- **`CAUSAL_CONFOUNDER = NO`:** 24 events (63.2%)

### Major Confounder Typologies Identified:
1. **Independent Pedestrian Routine Clusters (`OBS_10_NEW_ACTOR_ARRIVAL`):** In `UNION_CAND_Warehouse_027_001`, a shift-routine group of 8+ workers entered the adjacent lane during the post-window, creating spurious automated density signals unrelated to the primary vehicle interaction.
2. **Vehicle Turnover and Track Handoff (`OBS_08_TRACK_HANDOFF`):** In `UNION_CAND_Warehouse_027_003`, Forklift 378 exited the frame, and a completely different vehicle (Forklift 418) arrived, conflating automated tracking.
3. **Multi-Forklift Traffic Clutter (`OBS_09_MULTIPLE_ACTORS`):** In `UNION_CAND_Warehouse_026_014`, `011`, `012`, and `013`, five forklifts operated concurrently across intersecting vectors.

---

## 12. Detector Dependence Audit

- **`LOW`**: 16 events (42.1%) — Physical actions (braking, stopping, wide clearance transit) are directly visible to the naked human eye without bounding box reliance.
- **`MEDIUM`**: 9 events (23.7%) — Routine pedestrian transits where distance measurements provide supporting confirmation.
- **`HIGH`**: 13 events (34.2%) — Heavy multi-vehicle clutter where tracking identity disambiguation is entirely dependent on automated tracker IDs.

---

## 13. Screening Disposition Distribution

Every event across the 51-event union pool received exactly one Screening Disposition:

```
+------------------------------------+-------+---------+-----------------------------------------------------------+
| Screening Disposition              | Count | Share   | Operational Interpretation                                |
+------------------------------------+-------+---------+-----------------------------------------------------------+
| BACKFIRE_CANDIDATE_RETAINED        | 0     | 0.0%    | No unconfounded observable safety backfire chain detected |
| NO_BACKFIRE_OBSERVED               | 15    | 29.4%   | Observed safe resolution within observable window         |
| INSUFFICIENT_OBSERVABILITY         | 23    | 45.1%   | Visibility gaps, clutter, or confounders prevent isolation|
| INELIGIBLE_WINDOW                  | 13    | 25.5%   | Temporal baseline truncated at stream boundaries          |
+------------------------------------+-------+---------+-----------------------------------------------------------+
| TOTAL                              | 51    | 100.0%  | Complete Union Event Pool                                 |
+------------------------------------+-------+---------+-----------------------------------------------------------+
```

### Breakdown of the 15 `NO_BACKFIRE_OBSERVED` Events:
- **10 events in `Warehouse_027_Camera_0005`** (`010, 011, 012, 013, 018, 019, 021, 023, 024, 025`): Forklift 557 remained stationary/idling in the central corridor while pedestrians passed with wide margins of safety ($> 5\text{--}10\text{m}$).
- **3 events in `Warehouse_027_Camera_0006`** (`032, 034, 035`): Nominal transit and safe clearance in open aisle.
- **1 event in `Warehouse_026_Camera_0002`** (`UNION_CAND_Warehouse_026_010`): Forklift 136 executed an emergency stop and remained motionless throughout the 8.0s post-window (displacement 2.5 px), producing zero secondary hazard transfer.
- **1 event in `Warehouse_027_Camera_0002`** (`UNION_CAND_Warehouse_027_004`): Forklift 418 and Person 417 cleared the shared corridor and exited the frame with zero secondary hazard.

---

## 14. Comparison with Milestone V3.4-D

Milestone V3.4-D focused exclusively on the 5 candidates flagged as `CANDIDATE_BACKFIRE` by automated screening. Milestone V3.4-E re-evaluates them within the complete 38-eligible event context:

| Candidate ID | V3.4-D Forensic Status | V3.4-E Observability | V3.4-E Screening Disposition | Root Cause of Divergence from Initial Candidate Label |
| :--- | :--- | :--- | :--- | :--- |
| `UNION_CAND_Warehouse_026_010` | `MODERATE_CANDIDATE` | Intervention: FULL, SecZone: PARTIAL | `NO_BACKFIRE_OBSERVED` | Forklift halted completely (disp 2.5px); no secondary hazard transferred |
| `UNION_CAND_Warehouse_027_001` | `WEAK_CANDIDATE` | Intervention: FULL, SecZone: PARTIAL | `INSUFFICIENT_OBSERVABILITY` | Confounded by independent shift-change pedestrian cluster entering in POST |
| `UNION_CAND_Warehouse_027_003` | `WEAK_CANDIDATE` | Intervention: FULL, Track Handoff | `INSUFFICIENT_OBSERVABILITY` | Vehicle turnover (Forklift 378 departs; Forklift 418 enters); tracker conflation |
| `UNION_CAND_Warehouse_027_004` | `INSUFFICIENT_EVIDENCE` | Intervention: FULL, SecZone: PARTIAL | `NO_BACKFIRE_OBSERVED` | Nominal clearing event; both agents vacated corridor with zero secondary hazard |
| `UNION_CAND_Warehouse_026_014` | `INSUFFICIENT_EVIDENCE` | Intervention: PARTIAL, Clutter: HEAVY | `INSUFFICIENT_OBSERVABILITY` | Extreme multi-forklift clutter (5 vehicles active); causal isolation impossible |

---

## 15. Main Observability Bottlenecks

1. **Pallet Rack Interior Occlusion (100% of Scenes):** In all 38 eligible events, the interior depth of secondary rack aisles was unobservable (`depth_visible = 0/38`). Monocular cameras mounted overhead cannot see behind stacked pallets.
2. **Monocular Single-View Blindness:** 3D trajectories cannot be sustained across cross-aisles without multi-camera overlapping views or calibrated 3D ground homography.
3. **Multi-Vehicle Visual Crowding:** When multiple vehicles operate simultaneously (e.g. Warehouse_026 intersection), monocular trackers merge bounding boxes and lose track identity during crossing maneuvers.

---

## 16. Evidence Collection Requirements to Close Observability Gaps

To scientifically substantiate or refute Safety Backfire mechanisms in future industrial datasets, the following physical evidence collection infrastructure is required:

1. **Synchronized On-Vehicle Telemetry:**
   - CAN-bus logging: instantaneous wheel steering angle, accelerator throttle, brake pressure, speed, and gear state.
   - Inertial Measurement Units (IMU): 3-axis linear accelerations ($m/s^2$) and angular yaw rates to empirically detect emergency evasive swerves versus gentle stops.
2. **Multi-Camera Overlapping Coverage:**
   - Ceiling-mounted downward-looking sensors at rack intersections providing multi-view homography to eliminate rack occlusions.
3. **Secondary-Zone Physical Presence Sensors:**
   - In-floor piezoelectric load mats or cross-aisle LiDAR tripwires to detect agent occupancy inside rack aisles independently of camera line-of-sight.
4. **Controlled Safety Counterfactual Trials:**
   - Protocolized vehicle trials where safety interventions (e.g. acoustic reverse alarms, blue spotlights, automated speed restrictors) are systematically tested under controlled, baseline-calibrated worker layouts.

---

## 17. Empirical Limitations

- **Observational Data Only:** All analyzed video captures reflect passive warehouse operations without experimental controls.
- **Absence of Ground Truth Annotations:** No human-verified 3D bounding boxes or verified incident classifications exist in the dataset.
- **Model H Lineage Unaltered:** Model H parameters remain frozen; no threshold tuning or post-hoc model fitting was performed.

---

## 18. Final Governance State

```yaml
MILESTONE_STATUS: V3_4_E_OBSERVABILITY_AUDIT_COMPLETED
HUMAN_REVIEW: BYPASSED
SAFETY_BACKFIRE_GT: NOT_ESTABLISHED
SAFETY_BACKFIRE_VALIDATION: NOT_ESTABLISHED
PERCEPTION_METRICS: NOT_ESTABLISHED
TOTAL_UNION_EVENTS: 51
ELIGIBLE_EVENTS: 38
INELIGIBLE_EVENTS: 13
SCREENING_DISPOSITION_SUMMARY:
  BACKFIRE_CANDIDATE_RETAINED: 0
  NO_BACKFIRE_OBSERVED: 15
  INSUFFICIENT_OBSERVABILITY: 23
  INELIGIBLE_WINDOW: 13
GROUND_TRUTH_VERIFIED_RECORDS: 0
MODEL_H_STATUS: FROZEN_INVARIANT
```
