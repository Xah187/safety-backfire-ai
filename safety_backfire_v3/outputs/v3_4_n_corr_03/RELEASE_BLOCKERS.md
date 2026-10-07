# V3.4-N-CORR-03 — Final Physical Commissioning Release Blockers
## Milestone V3.4-N-CORR-03: Final Metrology & Acceptance Decision Closure

---

### Executive Milestone Status Declaration

```text
========================================================================================
MILESTONE STATUS:               BLOCKED
PHYSICAL CAPTURE AUTHORIZATION: NOT_GRANTED (STRICTLY PROHIBITED)
DESIGN READINESS STATE:         INSTRUMENTATION_DESIGN_COMPLETE
METROLOGY DECISION RULE:        DEFINED (GUARDED_ACCEPTANCE - ISO 14253-1 / ILAC-G8)
STANDARDS APPLICABILITY:        CLASSIFIED (DRIVERLESS VS REMOTE CONDITIONALITY)
BLOCKING ROOT CAUSE:            TRACTION_CURRENT_ENDPOINT_PERSISTENCE = TBD
COMMISSIONING GATES C1-C9:      UNVERIFIED_PENDING_PHYSICAL_COMMISSIONING
PHYSICAL FIELD RECORDING:       ZERO BYTES (STRICT PRE-DEPLOYMENT GATE ONLY)
========================================================================================
```

Milestone **V3.4-N-CORR-03** completes the comprehensive metrology, decision-rule, and semantic closure audit of the physical commissioning package:
1. **Synchronization Margin Decoupling:** Decoupled `component_margin_state` from `composite_margin_state`. Individual channel excursions into $(2.0, 5.0]\,\text{ms}$ are classified as `COMPONENT_MARGIN_CONSUMED` and do not algebraically deduct from the $15.33\,\text{ms}$ composite reserve.
2. **C4 20m Threshold Resolution (Option A Policy):** Established that only 9 of the 36 sample points are physically located at $20\,\text{m}$. Enforced distinct rules: all 36 points must pass line-of-sight visibility, while the 9 points at the $20\,\text{m}$ depth plane must meet guarded spatial resolution ($\ge 67.5\,\text{px/m}$).
3. **C7 Spatial Lux Point-by-Point Acceptance:** Enforced that both `spatial_mean` and **every required measurement point** must fall within guarded limits ($[310.5, 389.5]\,\text{lux}$), preventing spatial averaging from concealing localized dark pockets.
4. **Flicker Metrology Governance:** Defined complete optoelectronic parameters ($1.0\,\text{MSa/s}$, $50\,\text{kHz}$ analog bandwidth, 4th-order anti-alias filter, Hann window, $\Delta f \le 0.5\,\text{Hz}$). Classified $FI \le 0.05$ / $f_{\text{mod}} \ge 1000\,\text{Hz}$ as `PROJECT_CURRENT_ACCEPTANCE_TARGET`.
5. **E-Stop Endpoint Decoupling:** Renamed to `ELECTRICAL_TRACTION_DEENERGIZED` and separated motor current from DC-bus bulk capacitor discharge ($V_{\text{bus}} < 50\,\text{V}$), mechanical brake shoe clamping, and vehicle kinetic stopping.
6. **Metrology Uncertainty & Guarded Acceptance:** Applied ISO 14253-1 / ILAC-G8 Guarded Acceptance ($g = U$, $k = 2$) across all physical gates C1–C9.
7. **Standards Conditionality:** Explicitly established that ISO 3691-4:2023 applies strictly to driverless/automated operations and is outside the stated scope for remote-controlled operations.

---

### Why Milestone Status is `BLOCKED`

In strict accordance with the Section 8 and Section 14 mandates of Milestone V3.4-N-CORR-03:

> "Audit whether: $I_{\text{motor}} < 0.5\,\text{A}$ RMS is a single instant threshold or a sustained condition. Define a deterministic measurement window or persistence rule. Do NOT invent an arbitrary persistence value. Use an explicit project-approved value if one already exists. Otherwise mark: `TRACTION_CURRENT_ENDPOINT_PERSISTENCE = TBD` and do not claim the endpoint semantics are fully closed."
> 
> "Set `V3_4_N_CORR_03_STATUS = BLOCKED` if any of the following remain unresolved: ... endpoint persistence rule ... Otherwise: `READY_FOR_PHYSICAL_COMMISSIONING`."

Because no empirical persistence duration has been experimentally validated or approved for this specific vehicle inverter, setting an arbitrary persistence window (e.g. 5 ms or 10 ms) is strictly forbidden. Consequently, `TRACTION_CURRENT_ENDPOINT_PERSISTENCE` is recorded as `TBD`, which formally locks the milestone status at:

$$\mathbf{V3\_4\_N\_CORR\_03\_STATUS = BLOCKED}$$

This blocked status prevents premature deployment and mandates that the Lead Safety Systems Engineer and Electrical Powertrain Engineer bench-test the inverter PWM zero-crossing characteristics and formally sign off on a deterministic persistence window before on-site commissioning commences.

---

### Mandatory Physical Release Blockers (Pre-requisites for `PHYSICAL_CAPTURE_AUTHORIZED`)

Physical field recording is strictly blocked until all nine Commissioning Acceptance Gates (`C1` through `C9`) achieve `GATE_PASS`:

```mermaid
graph TD
    subgraph CRITICAL_METROLOGY_PREREQUISITE [Pre-Commissioning Metrology Gate]
        PERSIST[Traction Current Persistence Window Signed Off: TBD -> APPROVED]
    end

    subgraph PHYSICAL_COMMISSIONING_GATES [Guarded Acceptance Gates C1-C9]
        C1["Gate C1: Guarded Sync Skew <= 32.83 ms"]
        C2["Gate C2: Guarded Bolt Torque >= 9.12 N*m & 0 Drops"]
        C3["Gate C3: Guarded CAN Gap <= 19.80 ms"]
        C4["Gate C4: 36-Point Visibility & 9-Point Resolution >= 67.5 px/m"]
        C5["Gate C5: Guarded ChArUco Reprojection <= 1.42 px"]
        C6["Gate C6: Guarded Ground Plane Residual <= 2.60 mm"]
        C7["Gate C7: Guarded Lux 310.5-389.5 & Flicker FI <= 0.047"]
        C8["Gate C8: Guarded Electrical Cutoff <= 48.8 ms with Verified Persistence"]
        C9["Gate C9: Microphones Desoldered & Bilateral Agreement Signed"]
    end
    
    PERSIST --> C8
    C1 & C2 & C3 & C4 & C5 & C6 & C7 & C8 & C9 -->|All Gates Verified PASS| READY[INSTRUMENTATION_READY_FOR_CAPTURE]
    READY -->|Safety Marshal Signed Clearance| AUTH[PHYSICAL_CAPTURE_AUTHORIZED]
    AUTH -->|Arm DAQ & Safety Loops| RUN[CAPTURE_IN_PROGRESS]
```

#### Detailed Blocker Ledger:

| Blocker ID | Gate Required | Corrected Physical Acceptance Test | Measuring Instrument | Guarded Acceptance Threshold | Current Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BLK_00_PERSIST**| `Gate C8_PRE` | Bench characterization of motor inverter PWM ripple to define sustained persistence duration for $I_{\text{motor}} < 0.5\,\text{A}$. | Tektronix Isolated DSO + Inverter Bench Rig | Formal engineering approval of $T_{\text{persist}}$ window. | `BLOCKED (TBD)` |
| **BLK_01_SYNC** | `Gate C1_CLOCK` | Measure actual camera strobe, CAN gateway, and secondary sensor timestamp offsets under multi-modal impact rig. All channels evaluated independently. | Keysight DSOX1204G Oscilloscope + Vector VN1640A | Guarded composite skew $\le 32.83\,\text{ms}$ ($U = 0.50\,\text{ms}$); all channels in NOMINAL or COMPONENT_MARGIN_CONSUMED. | `UNVERIFIED` |
| **BLK_02_RIGGING**| `Gate C2_CAMERA` | Torque wrench audit of all optical camera truss clamps; 30-min frame loss soak test across all deployed cameras. | Norbar Calibrated Torque Wrench + Wireshark Monitor | Guarded torque $\ge 9.12\,\text{N}\cdot\text{m}$ ($U = 0.38\,\text{N}\cdot\text{m}$); zero dropped frames over 30 min across deployed cameras. | `UNVERIFIED` |
| **BLK_03_TELEMETRY**| `Gate C3_CAN` | Non-intrusive CAN bus tap validation; verify 50 Hz streaming of speed, brake state, accel, and steering. | Vector CANoe with high-impedance CAN tap | Guarded packet gaps $\le 19.80\,\text{ms}$ ($U = 0.20\,\text{ms}$); SI units confirmed; steering rate derivation verified. | `UNVERIFIED` |
| **BLK_04_SECONDARY**| `Gate C4_SEC_OBS` | Option A grid sweep (36 discrete test points): visibility unoccluded on all 36 points; guarded resolution on 9 points at $20\,\text{m}$ depth. | Leica DISTO D2 Laser Measure + OpenCV Target Resolution | 36/36 points visibility PASS; 9/9 points at $20\,\text{m}$ resolution $\ge 67.5\,\text{px/m}$ ($U = 2.5\,\text{px/m}$). | `UNVERIFIED` |
| **BLK_05_OPTICAL_CAL**| `Gate C5_CALIB` | Photogrammetric calibration using 12x9 ChArUco diamond board across **all deployed cameras** (D = NOT_APPLICABLE if absent). | Calib.io Certified Precision ChArUco Target | Guarded RMS reprojection error $\le 1.42\,\text{px}$ ($U = 0.08\,\text{px}$) across all deployed cameras. | `UNVERIFIED` |
| **BLK_06_GEOMETRY**| `Gate C6_GEOM` | Geodetic Total Station survey establishing facility origin, corridor boundaries, and floor ground plane. | Leica TS16 Total Station (1\" angle accuracy) | Guarded ground plane residual $\text{RMS} \le 2.60\,\text{mm}$ ($U = 0.40\,\text{mm}$); facility monument locked. | `UNVERIFIED` |
| **BLK_07_ILLUMINANCE**| `Gate C7_LUX` | Path 1: Every point & mean within guarded photopic range. Path 2: Guarded high-speed photodiode trace ($1.0\,\text{MSa/s}$, $50\,\text{kHz}$ filter). | Testo 540 Lux Meter + Thorlabs PDA36A2 / Keysight DSO | Path 1: Every point $310.5 \le E_v \le 389.5\,\text{lux}$; Path 2: $FI \le 0.047$ ($U = 0.003$), $f_{\text{mod}} \ge 1000\,\text{Hz}$. | `UNVERIFIED` |
| **BLK_08_ESTOP** | `Gate C8_ESTOP` | Empirical oscilloscope trace measuring $t_{\text{electrical\_traction\_deenergized}} - t_{\text{estop\_command}}$ to motor phase current extinction ($I_{\text{motor}} < 0.5\,\text{A}$). | Keysight DSOX1204G + Hall-effect Current Clamp | Guarded latency $\le 48.8\,\text{ms}$ ($U = 1.2\,\text{ms}$) WITH verified persistence; contactor microswitch $\le 35.0\,\text{ms}$. | `UNVERIFIED (BLOCKED)` |
| **BLK_09_PRIVACY** | `Gate C9_PRIVACY` | Physical inspection of camera microphones; formal execution of bilateral Data Agreement. | Visual inspection + Legal document registry | Microphones physically disconnected/desoldered; agreement signed by site & labor. | `UNVERIFIED` |

---

### Conclusion & Operational Boundary

The lifecycle transition rule is absolute:

$$\mathbf{BLOCKED \quad \nrightarrow \quad READY\_FOR\_PHYSICAL\_COMMISSIONING \quad \nrightarrow \quad PHYSICAL\_CAPTURE\_AUTHORIZED}$$

Only the empirical characterization and formal signoff of `BLK_00_PERSIST` can transition the status to `READY_FOR_PHYSICAL_COMMISSIONING`. Only the subsequent physical clearance of Gates `C1` through `C9` on physical hardware at the facility can advance the system to `INSTRUMENTATION_READY_FOR_CAPTURE`, and only the final Safety Marshal site signoff can grant `PHYSICAL_CAPTURE_AUTHORIZED`.
