# Milestone V3.4-D — Forensic Analysis of Automated Backfire Candidates

**Document ID:** `V3_4_D_CANDIDATE_FORENSIC_REPORT`  
**Milestone Version:** V3.4-D  
**Timestamp:** 2026-10-01  
**Repository:** `safety-backfire-ai`  
**Current Governance State:** `SAFETY_BACKFIRE_GT = NOT_ESTABLISHED`  
**Validation Status:** `SAFETY_BACKFIRE_VALIDATION = NOT_ESTABLISHED`  
**Perception Metrics Status:** `PERCEPTION_METRICS = NOT_ESTABLISHED`  

---

## 1. Scope

This milestone performs a rigorous, empirical forensic examination of the **5 events previously flagged by automated screening as `CANDIDATE_BACKFIRE`** (out of the 38 eligible events and 51 total union events in the NVIDIA PhysicalAI-SmartSpaces captures for Warehouse_026 and Warehouse_027).

The objective is to characterize the physical, visual, and kinematic strength of observable evidence within the derived video packages (`before.mp4`, `intervention.mp4`, `after.mp4`) and underlying trajectory records, without delegating judgment to automated detectors or unverified heuristics.

---

## 2. Epistemic Boundaries

1. **No Ground Truth Conversion:** Forensic analysis evaluates candidate hypotheses; it does **not** establish or fabricate Ground Truth. `SAFETY_BACKFIRE_GT` remains strictly `NOT_ESTABLISHED`.
2. **Automated Screening Label Distinction:** The designation `CANDIDATE_BACKFIRE` originated purely as an algorithmic screening threshold ($\text{relevance score} \ge 0.60$ with corridor trajectory). It is **not** an established ground truth label ($\text{AUTOMATED\_SCREENING\_LABEL} \neq \text{GROUND\_TRUTH\_LABEL}$).
3. **No Model Performance Metrics:** Precision, Recall, F1-Score, Sensitivity, Specificity, False Alarm Rate, and Backfire Accuracy are **prohibited** and remain `NOT_ESTABLISHED`.
4. **Physical Invariance:** Model H parameters remain strictly frozen:
   $$k_0 = 2.40, \quad \beta_d = 0.08, \quad \beta_l = 0.12, \quad \beta_{\text{pitch}} = 0.22$$
   Raw video sources remain read-only and SHA256-verified.
5. **Domain Separation:** The lack of physical telemetry (lux sensors, floor-load cells, acoustic alarms, CAN-bus) constitutes a limitation for `MODEL_H_INPUT_SUFFICIENCY`, but does not automatically disqualify visually clear evidence under `EVENT_FORENSIC_EVIDENCE_SUFFICIENCY`.

---

## 3. Candidate Inventory

All 5 candidates flagged as `CANDIDATE_BACKFIRE` are located in **Camera_0002** (the primary wide-angle perspective overlooking the central intersection and adjacent storage rack aisles):

| Candidate Event ID | Scene | Camera | Primary Zone | Secondary Zone | Screened Relevance | Key Actors |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **`UNION_CAND_Warehouse_026_010`** | Warehouse_026 | Camera_0002 | Central Corridor | Adjacent Rack Aisle | 0.642 | Person 148, Forklift 136 |
| **`UNION_CAND_Warehouse_027_001`** | Warehouse_027 | Camera_0002 | Central Corridor | Adjacent Rack Aisle | 0.757 | Person 367, Forklift 378 |
| **`UNION_CAND_Warehouse_027_003`** | Warehouse_027 | Camera_0002 | Central Corridor | Adjacent Rack Aisle | 0.750 | Person 397, Forklift 378 |
| **`UNION_CAND_Warehouse_027_004`** | Warehouse_027 | Camera_0002 | Central Corridor | Adjacent Rack Aisle | 0.658 | Person 417, Forklift 418 |
| **`UNION_CAND_Warehouse_026_014`** | Warehouse_026 | Camera_0002 | Central Corridor | Adjacent Rack Aisle | 0.619 | Person 195, Forklift 188 |

---

## 4. Event-by-Event Forensic Analysis

### 4.1. Event `UNION_CAND_Warehouse_026_010`
- **Spatiotemporal Window:** PRE (Frames 91–240, 5.0s) $\rightarrow$ INTERVENTION (Frames 241–313, 2.43s) $\rightarrow$ POST (Frames 314–553, 8.0s).
- **PRE Analysis:** Forklift 136 moves along the transit corridor at nominal operating speed. Workers 134 and 135 are stationary near the pallet racks.
- **INTERVENTION Analysis:** Person 148 steps across the corridor. Forklift 136 executes an immediate deceleration and stops (closest approach: 115.1 px at Frame 257). Intervention visibility is **`YES`**.
- **POST Analysis:** Person 148 clears the lane. Forklift 136 **remains completely stationary** throughout the entire 8.0-second post-window (total displacement across 240 frames is 2.5 pixels: from $(886, 359)$ to $(888, 357)$).
- **Primary Risk Change:** **`OBSERVED`** (collision was averted by vehicle braking).
- **Secondary Risk Change:** **`NOT_OBSERVED`**. Because Forklift 136 remained stopped and parked, no kinetic hazard or near-miss was transferred to the workers stationed at the adjacent rack.
- **Causal Mechanism Evidence:** **`LOW`**. The intervention did not propagate a secondary hazard.
- **Forensic Status:** **`MODERATE_CANDIDATE`**. Coherent primary safety intervention, but the secondary backfire cascade did not materialize.

---

### 4.2. Event `UNION_CAND_Warehouse_027_001`
- **Spatiotemporal Window:** PRE (Frames 342–491, 5.0s) $\rightarrow$ INTERVENTION (Frames 492–720, 7.63s) $\rightarrow$ POST (Frames 721–960, 8.0s).
- **PRE Analysis:** Forklift 378 advances down the main corridor. Person 367 enters the lane periphery.
- **INTERVENTION Analysis:** Person 367 yields and moves to the corridor wall as Forklift 378 continues past (closest approach: 242.9 px at Frame 720). Intervention visibility is **`YES`**.
- **POST Analysis:** Person 367 vacates the area. Forklift 378 idles/stops (total displacement 5.1 px over 136 post frames: $(1591, 716) \rightarrow (1595, 719)$). During this window, an independent cluster of incoming workers (397, 398, 401, etc.) enters the adjacent lane.
- **Primary Risk Change:** **`OBSERVED`**.
- **Secondary Risk Change:** **`UNCLEAR`**.
- **Causal Mechanism Evidence:** **`LOW`**. The arrival of the pedestrian cluster was an independent shift/work routine, not a displacement caused by Forklift 378.
- **Forensic Status:** **`WEAK_CANDIDATE`**. Confounded by independent pedestrian traffic.

---

### 4.3. Event `UNION_CAND_Warehouse_027_003`
- **Spatiotemporal Window:** PRE (Frames 562–711, 5.0s) $\rightarrow$ INTERVENTION (Frames 712–857, 4.87s) $\rightarrow$ POST (Frames 858–1097, 8.0s).
- **PRE Analysis:** Occurs concurrently with Candidate 001's intervention; Forklift 378 is already active.
- **INTERVENTION Analysis:** Forklift 378 slows down as Person 397 pauses at corridor entrance (closest approach: 231.8 px at Frame 807). Intervention visibility is **`YES`**.
- **POST Analysis:** Forklift 378 departs the field of view ($F_{\text{obs}} = 0$). An entirely different vehicle—**Forklift 418**—enters the scene.
- **Primary Risk Change:** **`OBSERVED`**.
- **Secondary Risk Change:** **`UNCLEAR`**.
- **Causal Mechanism Evidence:** **`LOW`**. The secondary activity is driven by the arrival of a new, unrelated forklift (418), not a cascading effect from Forklift 378.
- **Forensic Status:** **`WEAK_CANDIDATE`**. Confounded by multi-vehicle handoff and tracker conflation.

---

### 4.4. Event `UNION_CAND_Warehouse_027_004`
- **Spatiotemporal Window:** PRE (Frames 843–992, 5.0s) $\rightarrow$ INTERVENTION (Frames 993–1123, 4.37s) $\rightarrow$ POST (Frames 1124–1363, 8.0s).
- **PRE Analysis:** Forklift 418 approaches; Person 417 walks along perimeter.
- **INTERVENTION Analysis:** Forklift 418 passes Person 417 without incident (closest approach: 225.1 px at Frame 1011). Intervention visibility is **`YES`**.
- **POST Analysis:** Both Forklift 418 and Person 417 exit the frame. The camera scene completely clears.
- **Primary Risk Change:** **`OBSERVED`**.
- **Secondary Risk Change:** **`NOT_OBSERVED`**.
- **Causal Mechanism Evidence:** **`NONE`**. No secondary hazard emerged.
- **Forensic Status:** **`INSUFFICIENT_EVIDENCE`**. Represents a nominal clearing interaction with zero secondary risk transfer.

---

### 4.5. Event `UNION_CAND_Warehouse_026_014`
- **Spatiotemporal Window:** PRE (Frames 1144–1293, 5.0s) $\rightarrow$ INTERVENTION (Frames 1294–1364, 2.37s) $\rightarrow$ POST (Frames 1365–1604, 8.0s).
- **PRE Analysis:** Extreme visual clutter. Five distinct forklifts (193, 136, 176, 177, 183) and multiple workers operate simultaneously across the frame.
- **INTERVENTION Analysis:** Forklift 188 passes near Person 195 (closest approach: 117.1 px at Frame 1298) while Forklift 176 operates in immediate background. Intervention visibility is **`PARTIALLY_VISIBLE`**.
- **POST Analysis:** Forklift 188 remains stationary (displacement 0.6 px), while Forklift 200 traverses the rear background.
- **Primary Risk Change:** **`UNCLEAR`**.
- **Secondary Risk Change:** **`UNCLEAR`**.
- **Causal Mechanism Evidence:** **`LOW`**. Visual clutter and multiple intersecting vehicle paths prevent establishing causal attribution.
- **Forensic Status:** **`INSUFFICIENT_EVIDENCE`**. Confounded by high-density multi-vehicle operations.

---

## 5. Cross-Event Findings

1. **Braking and Halting Dominate (No Kinetic Overflow):** In 3 out of 5 candidates (`026_010`, `026_014`, `027_001`), the forklift executed a full stop or idled during the post-window (displacement $< 5.5$ pixels over hundreds of frames). Rather than swerving into adjacent zones, operators adhered to standard safety braking protocols.
2. **Automated Score Origin:** High relevance scores ($\ge 0.60$) reflected **intense primary proximity**, not confirmed secondary risk propagation.
3. **Absence of Observable Backfire Cascades:** In none of the 5 candidates was an active, unconfounded safety backfire chain directly observed.

---

## 6. Confounder Analysis

Confounders were identified in **4 out of 5 events** (`CONFOUNDERS_PRESENT = YES`):
- **Independent Pedestrian Clusters:** In `027_001`, a group of workers entered the adjacent corridor on their routine path.
- **New Vehicle Arrivals:** In `027_003`, Forklift 378 exited and Forklift 418 arrived.
- **Pre-Existing Stationarity:** In `026_010`, workers were already stationed at the rack prior to the event.
- **Multi-Vehicle Clutter:** In `026_014`, five forklifts operated concurrently.

---

## 7. Secondary-Zone Observability

- **Definition:** The secondary zone (`Camera_0002_ADJACENT_RACK_AISLE`) is defined by geometric aisle borders.
- **Observability Limitation:** While the entrance to the aisle is visible, visual depth into rack storage slots is partially occluded.
- **Finding:** No candidate exhibited verifiable risk transfer into the secondary zone.

---

## 8. Detector Dependence

- **Low Dependence (1 event):** `UNION_CAND_Warehouse_026_010` (the abrupt stop is clearly visible to the naked eye).
- **Medium Dependence (2 events):** `UNION_CAND_Warehouse_027_001`, `UNION_CAND_Warehouse_027_004`.
- **High Dependence (2 events):** `UNION_CAND_Warehouse_027_003`, `UNION_CAND_Warehouse_026_014` (interpretation relies heavily on ByteTrack IDs to disambiguate multiple vehicles).

---

## 9. Evidence Quality

| Quality Level | Count | Events |
| :--- | :---: | :--- |
| **HIGH** | 2 | `UNION_CAND_Warehouse_026_010`, `UNION_CAND_Warehouse_027_004` (clean perspective, minimal clutter) |
| **MEDIUM** | 2 | `UNION_CAND_Warehouse_027_001`, `UNION_CAND_Warehouse_027_003` (moderate crowding) |
| **LOW** | 1 | `UNION_CAND_Warehouse_026_014` (heavy visual occlusion and multi-vehicle traffic) |

---

## 10. Candidate Status Distribution

$$\text{Total Candidates Analyzed} = 5$$

```
+------------------------------------+-------+-----------------------------------------------------------+
| Forensic Status                    | Count | Characterization                                          |
+------------------------------------+-------+-----------------------------------------------------------+
| STRONG_CANDIDATE                   | 0     | No candidate exhibited unconfounded secondary backfire    |
| MODERATE_CANDIDATE                 | 1     | UNION_CAND_Warehouse_026_010 (clear stop; no backfire)    |
| WEAK_CANDIDATE                     | 2     | UNION_CAND_Warehouse_027_001, UNION_CAND_Warehouse_027_003|
| INSUFFICIENT_EVIDENCE              | 2     | UNION_CAND_Warehouse_027_004, UNION_CAND_Warehouse_026_014|
+------------------------------------+-------+-----------------------------------------------------------+
```

---

## 11. Empirical Limitations

1. **Observational vs. Controlled Data:** Surveillance captures naturally occurring workflow; safety interventions are spontaneous and cannot be counterfactually compared to an un-intervened baseline.
2. **Absence of On-Vehicle Telemetry:** Lack of vehicle CAN-bus data prevents verification of braking deceleration rates ($m/s^2$) or steering wheel angle.
3. **Rack Occlusion:** Line-of-sight limitations prevent observing whether pedestrians behind pallet racks were aware of incoming traffic.

---

## 12. Recommended Next Evidence Collection

1. **Instrumented Telemetry Acquisition:** Collect synchronized vehicle telemetry (steering angle, accelerator, brake pressure, speed).
2. **Multi-Camera 3D Calibration:** Deploy multi-view calibrated tracking with 3D ground homography to trace agents into occluded rack aisles.
3. **Controlled Safety Trials:** Conduct protocolized intervention experiments where safety warning devices (e.g. blue spotlights, acoustic reverse alarms) are triggered under controlled conditions.
