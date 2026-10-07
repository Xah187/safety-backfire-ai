# V3.4-N-CORR-02 — Physical Measurement Semantics & Standards Specification

## Milestone V3.4-N-CORR-02: Safety, Measurement & Standards Applicability Closure

---

### 1. Purpose and Epistemic Scope

This document provides the authoritative engineering measurement specifications, probe configurations, signal processing criteria, and standards applicability taxonomy for physical commissioning of the research data acquisition (DAQ) platform.

```text
========================================================================================
GOVERNANCE STATE:               PRE-COMMISSIONING DOCUMENTATION & SCHEMA CLOSURE ONLY
PHYSICAL FIELD RECORDING:       ZERO BYTES (PROHIBITED)
ACTUATOR AUTHORITY:             ZERO (GALVANIC & PROTOCOL ISOLATION)
STANDARDS APPLICABILITY:        CLASSIFIED (STANDARDS APPLICABILITY FRAMEWORK)
GATES C1-C9:                    UNVERIFIED_PENDING_PHYSICAL_COMMISSIONING
========================================================================================
```

---

### 2. Camera Synchronization Reserve Semantics & Channel Hierarchy

#### 2.1 Operational State Taxonomy for Camera Synchronization
Prior documentation defined camera jitter as nominal ($\le 2.0\,\text{ms}$) or reserve consumed ($2.0 < P_{99} \le 5.0\,\text{ms}$) without operational state transitions. Milestone V3.4-N-CORR-02 defines four unambiguous operational states:

1. **`SYNC_NOMINAL_PASS` ($P_{99} \le 2.0\,\text{ms}$):**
   - *Operational Status:* `NOMINAL_OPERATION`.
   - *Margin Disposition:* Full design margin preserved; $0.0\,\text{ms}$ of the $15.33\,\text{ms}$ unallocated design reserve is consumed.
   - *Commissioning Action:* Unconditional gate pass for camera optical sync.
2. **`SYNC_RESERVE_CONSUMED` / `PASS_WITH_DEGRADED_MARGIN` ($2.0\,\text{ms} < P_{99} \le 5.0\,\text{ms}$):**
   - *Operational Status:* `PASS_WITH_DEGRADED_MARGIN`.
   - *Margin Disposition:* Component jitter complies with the hard component acceptance limit ($\le 5.0\,\text{ms}$), but up to $3.0\,\text{ms}$ of the $15.33\,\text{ms}$ design reserve is consumed.
   - *Commissioning Action:* Acceptable for physical capture **only if** composite skew across all channels remains $\le 33.33\,\text{ms}$. Triggers an automated system warning event, logs jitter telemetry, and requires verification from the Lead DAQ Systems Engineer.
3. **`SYNC_ACCEPTABLE` ($P_{99} \le 5.0\,\text{ms}$):**
   - Formal superset encompassing `SYNC_NOMINAL_PASS` and `SYNC_RESERVE_CONSUMED`.
4. **`SYNC_FAIL` ($P_{99} > 5.0\,\text{ms}$):**
   - *Operational Status:* `FAIL`.
   - *Margin Disposition:* Hard component rejection threshold breached.
   - *Commissioning Action:* Immediate Gate C1/C2 failure. In real-time capture, triggers `DATA_INVALIDATION_ABORT`.

#### 2.2 Mandatory Independent Channel Evaluation
A primary vulnerability in composite time budgets is that a low composite skew can mask severe component failure. Milestone V3.4-N-CORR-02 enforces the **Rule of Independent Channel Evaluation**:

$$\mathbf{\text{Gate C1 PASS}} \iff \left(\tau_{\text{composite}} \le 33.33\,\text{ms}\right) \land \bigwedge_{i \in \text{Deployed Channels}} \left(\tau_i \le \tau_{\text{limit}, i}\right)$$

| Channel ID | Deployed Subsystem | Measurement Parameter | Nominal Target | Component Limit | Hard Rejection | Degraded Margin Range |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **`CH_CAM`** | Cameras A, C (B, D if deployed) | PTP 1PPS vs Shutter Strobe | $2.0\,\text{ms}$ | $5.0\,\text{ms}$ | $> 5.0\,\text{ms}$ | $(2.0, 5.0]\,\text{ms}$ |
| **`CH_CAN`** | Vehicle Telemetry Gateway | CAN EOF to UDP Egress | $5.0\,\text{ms}$ | $5.0\,\text{ms}$ | $> 10.0\,\text{ms}$ | $(5.0, 10.0]\,\text{ms}$ |
| **`CH_SEC`** | Secondary LiDAR/Radar | UDP Aggregation & Transit | $5.0\,\text{ms}$ | $8.0\,\text{ms}$ | $> 8.0\,\text{ms}$ | $(5.0, 8.0]\,\text{ms}$ |
| **`CH_OS`** | Host Linux Kernel DAQ | Socket Read to Thread Queue | $1.0\,\text{ms}$ | $3.0\,\text{ms}$ | $> 5.0\,\text{ms}$ | $(1.0, 3.0]\,\text{ms}$ |

*Under no circumstances may any subsystem channel bypass its individual component limit simply because the composite total is below $33.33\,\text{ms}$.*

---

### 3. Secondary Hazard Zone Bounded Sampled Observability

#### 3.1 Geometric Mismatch Reconciliation & Terminology Purge
In prior drafts, the term "voxel grid" was utilized without a mathematical voxelization model, and the corridor boundary width ($3.5\,\text{m}$) conflicted with the sample rail span ($2.4\,\text{m}$).

- **Voxel Terminology Purge:** A voxel requires a finite 3D bounding envelope $[dx, dy, dz]$ with volume integration. The 36 test locations are point measurements; the term "voxel" is permanently replaced with `OBSERVABILITY_SAMPLE_POINTS`.
- **Lateral Rail Mismatch Audit:**
  - `ZONE_POLYGON`: Corridor horizontal footprint is $20.0\,\text{m} \times 3.5\,\text{m}$ ($Y \in [-1.75, +1.75]\,\text{m}$, total floor area $70.0\,\text{m}^2$).
  - `MEASUREMENT_GRID`: 3 lateral rails positioned at $Y \in \{-1.2, 0.0, +1.2\}\,\text{m}$ (total grid span $2.4\,\text{m}$).
  - *Identified Margin:* The outer lateral clearance strips ($|Y| \in [1.2, 1.75]\,\text{m}$, total area $22.0\,\text{m}^2$) represent unmonitored margins adjacent to warehouse pallet racking.

```text
|<--------------------------- 3.5 m Corridor Width -------------------------->|
|  0.55 m margin  |<------------- 2.4 m Grid Span ------------->|  0.55 m margin  |
| [Unmonitored]   | Left (-1.2m)    Center (0.0m)    Right (+1.2m)| [Unmonitored]   |
+-----------------+---------------+----------------+---------------+----------------+
| Pallet Rack     |               |                |               | Pallet Rack    |
```

#### 3.2 Area vs. Point Observability Claims
The previous assertion that discrete point sampling proves $\text{CRITICAL\_OBSTRUCTION\_AREA} = 0.0\,\text{m}^2$ is mathematically unsound: 36 discrete points cannot guarantee continuous volumetric coverage.

- **Sampled-Point Observability Criterion:**
  $$\text{SAMPLED\_POINT\_OBSERVABILITY} = \frac{N_{\text{passed}}}{36} = 100\% \quad \left(\text{Target Resolution} \ge 65.0\,\text{px/m at } 20\,\text{m}\right)$$
- **Continuous Corridor Coverage Qualification:**
  $$\text{CONTINUOUS\_CORRIDOR\_COVERAGE} = \text{UNVERIFIED\_BOUNDED\_INTERPOLATION}$$
  *(Direct optical resolution is proven solely along the 36 specific line-of-sight rays. Continuous volumetric zero-blindness across the full $70.0\,\text{m}^2$ polygon remains unproven pending continuous surface LiDAR scanning).*

---

### 4. High-Speed Optoelectronic Photometry vs. Temporal Flicker

#### 4.1 Separation of Photometric Channels
Gate C7 enforces complete separation between steady-state illuminance and high-frequency temporal modulation:
1. `ILLUMINANCE_ACCEPTANCE`: Steady-state photopic illuminance $E_v \in [300.0, 400.0]\,\text{lux}$. Measured with a Class B DIN 5032-7 lux meter at $1.0\,\text{Hz}$ over $30\,\text{s}$.
2. `TEMPORAL_LIGHT_MODULATION_ACCEPTANCE`: High-frequency optical flicker ($FI \le 0.05$, $f_{\text{mod}} \ge 1000.0\,\text{Hz}$).

#### 4.2 Practical Reconstruction Sampling Margin
Nyquist sampling ($2 \times f_{\max}$) is insufficient for waveform pulse-shape reconstruction, harmonic analysis, and crest-factor calculation. To evaluate LED driver PWM harmonics up to $50\,\text{kHz}$:
- **Analog Measurement Bandwidth:** $\text{DC to } 50.0\,\text{kHz}$ (Thorlabs PDA36A2 amplified silicon photodetector).
- **Digitizer Bandwidth:** $\ge 70.0\,\text{MHz}$ (Keysight DSOX1204G DSO).
- **Anti-Alias Filter:** Hardware 4th-order low-pass filter ($f_{\text{cutoff}} = 50.0\,\text{kHz}$).
- **Minimum Digitizer Sampling Rate:** $\ge 1.0\,\text{MSa/s}$ (Providing $\mathbf{20\times}$ oversampling margin over the $50\,\text{kHz}$ analog cutoff).
- **Capture Duration & Frequency Resolution:** Duration $\ge 2.0\,\text{s}$, achieving FFT frequency bin resolution $\Delta f = \frac{1}{T} \le 0.5\,\text{Hz}$.
- **Rolling-Shutter Qualification:** A modulation frequency $f_{\text{mod}} \ge 1000\,\text{Hz}$ does **not** intrinsically guarantee zero CMOS rolling-shutter artifacts. If camera exposure time $t_{\text{exp}} \le 1.0\,\text{ms}$ or sensor line readout time $t_{\text{row}} \approx 25\,\mu\text{s}$ aliases with driver duty cycles, spatial luminance banding can still occur.

---

### 5. E-Stop Safe Endpoint Separation & Traction De-Energization

#### 5.1 Four-Stage Physical Transition Sequence
The transition sequence from E-Stop switch actuation to verified safe state is explicitly decoupled:

```text
t0: E-Stop Switch Break (NC dry contact opens, 24V -> 0V)
    │
    ▼ [delta_t <= 15.0 ms]
t1: Safety Relay Logic Output Drops Low (OSSD / relay contacts open)
    │
    ▼ [delta_t <= 35.0 ms - Diagnostic Precursor]
t2: Main Contactor Auxiliary Microswitch Opens (NO contact opens)
    │
    ▼ [delta_t <= 50.0 ms - AUTHORITATIVE KINETIC SAFETY ENDPOINT]
t3: Traction Safe State (Motor Phase Current I_motor < 0.5 A RMS)
```

#### 5.2 Independent Physical Quantities
1. **`TRACTION_CURRENT_SAFE` ($I_{\text{motor}} < 0.5\,\text{A}$ RMS):**
   - *Endpoint Role:* Authoritative kinetic safety acceptance metric. Proves motor electromagnetic torque is extinguished.
   - *Measurement:* Calibrated Hall-effect current probe clamped to Motor Phase U stator conductor.
2. **`CONTACTOR_OPEN`:**
   - *Endpoint Role:* Diagnostic precursor. Indicates mechanical armature displacement. Does not detect contact welding or plasma arcs.
   - *Measurement:* Auxiliary microswitch continuity probe.
3. **`DC_BUS_ISOLATED` ($V_{\text{DC\_bus}} < 50.0\,\text{V}$):**
   - *Critical Distinction:* **$I_{\text{motor}} < 0.5\,\text{A} \ne \text{DC\_BUS\_ISOLATED}$**. Inverter IGBT gate-drive deassertion cuts motor current to zero in $< 1\,\text{ms}$, but high-voltage DC link bulk capacitors remain charged at hazardous potential ($48\,\text{V}$ / $80\,\text{V}$ / $400\,\text{V}$) until discharged. If DC bus isolation is required, it must be verified independently with a high-voltage differential probe.
4. **`BRAKE_APPLIED`:**
   - *Critical Distinction:* Brake coil de-energization ($V_{\text{brake}} = 0\,\text{V}$) is an electrical control signal. Mechanical spring displacement and pad clamping require an additional $15\text{ to }35\,\text{ms}$. True mechanical braking is measured via vehicle deceleration transducer ($\ge 1.5\,\text{m/s}^2$) or caliper displacement sensors.

---

### 6. Safety Certification Language & Standards Applicability Framework

#### 6.1 Certification Scope Taxonomy
- `COMPONENT_CERTIFICATION`: Vendor certificate issued by an accredited Notified Body (e.g., TÜV) certifying an isolated component (e.g., Pilz relay, Sick scanner) satisfies IEC 61508 or ISO 13849-1.
- `SYSTEM_ARCHITECTURE`: Circuit design topology (e.g., Category 4 dual-channel architecture).
- `INTEGRATED_SAFETY_FUNCTION`: End-to-end safety loop on this specific vehicle. **A vendor component certificate does not certify the vehicle's integrated safety function.**
- `FIELD_VALIDATION`: Empirical on-site operational proof (strictly `NOT_PERFORMED`).

#### 6.2 Standards Applicability Framework

| Tier | Standard ID | Title | Jurisdiction & Relevance | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Authoritative Applicable** | **ISO 13849-1:2023** | Safety of machinery — Safety-related parts of control systems | Safety circuit architecture, E-Stop dual-channel loops, PLe/Cat 4 requirements. | `DESIGN_ALIGNED_ONLY` |
| | **ISO 13849-2:2012** | Safety of machinery — Validation | Validation and testing procedures for safety control loops. | `PROCEDURE_REFERENCED` |
| | **ISO 3691-4:2023** | Driverless industrial trucks and their systems | Authoritative standard for automated/driverless industrial warehouse vehicles. | `REQUIREMENTS_BENCHMARKED` |
| **Tier 2: Reference** | **IEC 61508:2010** | Functional safety of E/E/PE safety-related systems | Meta-standard for component SIL ratings (PFHd, architecture constraints). | `COMPONENT_REF_ONLY` |
| | **IEEE 1588-2019** | Precision Clock Synchronization (PTP) | Sub-microsecond clock synchronization protocol across Ethernet. | `PROTOCOL_SPEC` |
| | **IEEE 1789-2015** | LED Modulation & Flicker Metrics | Mathematical definition of Flicker Index and modulation frequencies. | `METRIC_REF` |
| | **DIN 5032-7** | Photometry — Classification of lux meters | Class B photometer specifications (cosine response $f_2 \le 3\%$). | `INSTRUMENT_SPEC` |
| **Tier 3: Potentially Applicable** | **ISO/DIS 3691-4** | Draft revision of ISO 3691-4 | Informative draft only; not published or legally enforceable. | `DRAFT_REF_ONLY` |
| | **ANSI/ITSDF B56.5** | Driverless, Automatic Guided Industrial Vehicles | North American industrial AGV/AMR standard. | `INFORMATIVE_REF` |
| **Tier 4: Out of Scope** | **ISO 26262:2018** | Road vehicles — Functional safety | Series production on-road motor vehicles. Excluded by scope. | `OUT_OF_SCOPE` |
| | **ISO 21448:2022** | Road vehicles — SOTIF | On-road vehicle automated driving systems. Excluded by scope. | `OUT_OF_SCOPE` |

---

### 7. Epistemic Baseline Summary

```text
MODEL_H                         = FROZEN_INVARIANT
PRODUCTION_MODEL                = UNCHANGED
FIELD_DATA                      = ZERO
GROUND_TRUTH                    = NOT_ESTABLISHED
REAL_WORLD_VALIDATION           = NOT_ESTABLISHED
PHYSICAL_COMMISSIONING          = NOT_PERFORMED
C1_C9                           = UNVERIFIED_PENDING_PHYSICAL_COMMISSIONING
PHYSICAL_CAPTURE_AUTHORIZATION  = NOT_GRANTED
STANDARDS_APPLICABILITY         = CLASSIFIED
V3_4_N_CORR_02_STATUS           = READY_FOR_PHYSICAL_COMMISSIONING
```
