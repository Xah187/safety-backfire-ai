# V3.4-N-CORR-04-R2 — Persistence State Machine & Decision Logic Specification

**Document Identifier:** `outputs/v3_4_n_corr_04_r2/persistence_state_machine_v3.md`  
**Milestone:** `V3.4-N-CORR-04-R2`  
**Classification:** Discrete State Machine Architecture & Rebound Failure Analysis  
**Vehicle Platform:** `AGV-RES-TRUCK-01` (48V PMSM Electric Industrial Truck)  
**Governance Invariants:**
```text
MODEL_H                         = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
PRODUCTION_MODEL                = UNCHANGED
FIELD_DATA                      = ZERO
GROUND_TRUTH                    = NOT_ESTABLISHED
REAL_WORLD_VALIDATION           = NOT_ESTABLISHED
PHYSICAL_CAPTURE_AUTHORIZATION  = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

---

## 1. Primary Purpose: Why Persistence Actually Exists

In early milestone drafts, persistence was conflated with "a waiting period for inductive decay." That conceptualization is flawed:
- **Decay Time:** Physical energy decay is an electromagnetic phenomenon governed by $L_s, R_s$, and the inverter freewheeling clamp. As derived in [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md), decay is complete when $I_{\text{RMS}}(t) \le I_{\text{guarded}}$, defining $t_{\text{rms\_threshold\_cross}}$.
- **Persistence Time ($T_{\text{persist}}$):** Persistence begins **AFTER** the current has already dropped below threshold.

$$\mathbf{\text{Persistence does NOT cause or wait for physical decay. Persistence guards against FALSE DE-ENERGIZATION DECLARATION.}}$$

### 1.1 The Rebound & Chatter Threat Taxonomy
Persistence exists exclusively as a temporal guard against five physical failure modes:

| # | Hazard Mechanism | Physical Description | Failure Signature Without Persistence |
| :---: | :--- | :--- | :--- |
| **F1** | **E-Stop Contactor Micro-Bounce** | Mechanical parting of safety relay contacts or main contactor microswitch can chatter for $0.5 - 2.5\,\text{ms}$, momentarily dropping gate drives before re-connecting. | Current dips below $0.410\,\text{A}$ for $1.0\,\text{ms}$, declares safe state, and then surges back to $50\,\text{A}$ when contacts re-close. |
| **F2** | **Inductive Energy Clamping Kickback** | Antiparallel freewheeling diodes conduct until forward voltage drop ($V_f \approx 0.7\,\text{V}$) is reached. Residual snubber capacitor resonance can produce an underdamped ringing burst. | Transient zero-crossing crossing occurs during oscillation, falsely triggering safe state before coil energy is settled. |
| **F3** | **Regenerative Back-EMF Rebound** | If the truck continues rolling down a ramp after torque cutoff, PMSM rotor permanent magnets generate sinusoidal phase back-EMF ($E = k_e \omega_m$). If inverter low-side IGBTs undergo body-diode conduction, current rebounds. | Current collapses, triggers immediate safe state, but vehicle inertia drives speed back up, producing residual regenerative current $> 1.0\,\text{A}$. |
| **F4** | **Inverter STO Watchdog Fault Latch Race** | Inverter internal micro-controller STO supervisory circuit may execute a fault retry or un-latch if safety relay signal de-bouncing experiences an edge glitch. | A momentary torque cut lasting $5\,\text{ms}$ is mistaken for permanent de-energization. |
| **F5** | **Noise Excursion / Threshold Chatter** | Laboratory EMI, DC link switching of auxiliary DC-DC converters, or ground loops can momentarily pull the sliding RMS metric below $0.410\,\text{A}$ for a few samples during active low-torque operation. | Single-sample threshold crossing triggers false safe state during active drive crawl. |

---

## 2. Reconciling the 100-Frame / 10-ms Temporal Semantics

Prior reports asserted:
$$\text{"100 consecutive frames = exactly 10.0 ms"}$$
This statement is mathematically ambiguous. In discrete digital signal processing with a step size of $\Delta t_{\text{step}} = 0.1\,\text{ms}$, there are two distinct implementations:

### 2.1 Mode A: Fixed Evaluation Frame-Count (Inclusive Sample Window)
- **Definition:** The counter initializes to $1$ at the first qualifying frame $k_0$ where $I_{\text{RMS}}[k_0] \le I_{\text{guarded}}$.
- It increments on each consecutive qualifying frame: $k_0, k_0+1, \dots, k_0 + 99$.
- Total qualifying evaluation frames: **$100$ evaluations**.
- **Elapsed Temporal Duration:**
  $$\Delta t_{\text{Mode\_A}} = (100 - 1) \times \Delta t_{\text{step}} = 99 \times 0.1\,\text{ms} = \mathbf{9.9\,ms}$$
- In Mode A, exactly $9.9\,\text{ms}$ of elapsed time separates the leading edge of the first qualifying evaluation from the leading edge of the 100th evaluation.

### 2.2 Mode B: Elapsed Interval Timer (Full Hold Duration)
- **Definition:** Frame $k_0$ triggers a timer initialized to $0.0\,\text{ms}$.
- Exactly $100$ consecutive evaluation *intervals* must elapse while remaining sub-threshold.
- Total required evaluations: **$101$ evaluations** ($k_0$ through $k_0 + 100$).
- **Elapsed Temporal Duration:**
  $$\Delta t_{\text{Mode\_B}} = 100 \times \Delta t_{\text{step}} = 100 \times 0.1\,\text{ms} = \mathbf{10.0\,ms}$$

### 2.3 Authoritative Implementation Selection: Mode B
The frozen verification pipeline `RMS-PROC-V1.0` is formally assigned to **Mode B**:
$$\mathbf{\text{Implementation Semantics} = \text{MODE\_B (100 Elapsed Step Intervals = Exactly 10.0 ms)}}$$
- Qualifying Frames Required: $K = 101$ evaluation points ($k_0$ through $k_0 + 100$).
- Elapsed Time: $\Delta T = 100 \times 0.1\,\text{ms} = 10.0\,\text{ms}$.
- Phrase "100 frames = 10.0 ms" without interval specification is **PROHIBITED**.

---

## 3. Finite State Machine (FSM) Specification

The discrete decision engine operates as a deterministic 4-state Mealy/Moore automaton:

```text
       ┌────────────────────────┐
       │   STATE 0: ACTIVE      │◄──────────────────────────────────┐
       │   (I_RMS > I_guarded)  │                                   │
       └───────────┬────────────┘                                   │
                   │                                                │
                   │ I_RMS[k] <= I_guarded                          │
                   ▼                                                │
       ┌────────────────────────┐                                   │
       │   STATE 1: ARMED       │                                   │
       │   counter = 0          │                                   │
       │   t_start = t_k        │                                   │
       └───────────┬────────────┘                                   │
                   │                                                │
                   │ I_RMS[k+1] <= I_guarded                        │
                   ▼                                                │
       ┌────────────────────────┐       I_RMS[k] > I_guarded        │
       │   STATE 2: PERSISTING  ├───────────────────────────────────┤
       │   counter++            │       (REBOUND / CHATTER DETECTED)│
       │   (counter < 100)      │                                   │
       └───────────┬────────────┘                                   │
                   │                                                │
                   │ counter == 100 (10.0 ms elapsed)               │
                   │ AND t_k <= 48.8 ms                             │
                   ▼                                                │
       ┌────────────────────────┐                                   │
       │   STATE 3: QUALIFIED   │                                   │
       │   (DE-ENERGIZED DECLARED)                                  │
       └────────────────────────┘                                   │
                   │                                                │
                   │ Any post-qualification surge I_RMS > 0.410 A   │
                   └────────────────────────────────────────────────┘
```

### 3.1 State Definitions & Transition Rules

1. **`STATE_0_ACTIVE`:**
   - Pre-condition: Instantaneous moving RMS exceeds guarded threshold: $I_{\text{RMS}}[k] > 0.410\,\text{A RMS}$.
   - Action: Persistence counter held at zero (`persist_counter = 0`). Safe state output deasserted (`DEENERGIZED = FALSE`).

2. **`STATE_1_ARMED`:**
   - Entry Condition: First frame $k_0$ where $I_{\text{RMS}}[k_0] \le 0.410\,\text{A RMS}$.
   - Action: Capture timestamp $t_{\text{persist\_start}} = k_0 \cdot \Delta t_{\text{step}}$. Set `persist_counter = 0`.

3. **`STATE_2_PERSISTING`:**
   - Invariant: Each successive frame $k = k_0 + m$ evaluates $I_{\text{RMS}}[k]$.
   - Branch A (Normal Hold): If $I_{\text{RMS}}[k] \le 0.410\,\text{A RMS}$ and `persist_counter < 100`, increment `persist_counter++`.
   - Branch B (Rebound Fault): If at ANY frame $k$ during the 100-step count, $I_{\text{RMS}}[k] > 0.410\,\text{A RMS}$:
     - Transition immediately to `STATE_0_ACTIVE`.
     - Log diagnostic event: `PERSISTENCE_REBOUND_EXCURSION`.
     - Reset `persist_counter = 0`. Clear $t_{\text{persist\_start}}$.

4. **`STATE_3_QUALIFIED` (Terminal Safe State):**
   - Entry Condition: `persist_counter == 100` consecutive intervals completed without excursion.
   - Latency Check: Ensure $t_{\text{endpoint}} = t_{\text{persist\_start}} + 10.0\,\text{ms} \le 48.8\,\text{ms}$.
   - Action: Assert `ELECTRICAL_TRACTION_DEENERGIZED = TRUE`.

---

## 4. Elimination of Continuous-Domain Claims

Milestone V3.4-N-CORR-04-R1 contained the phrase:
$$\text{"provides complete mathematical coverage of continuous analog dynamics"}$$

### 4.1 Formal Revocation & Bounded Decision Domain
This claim is technically ungrounded and hereby **REVOKED**.  
The physical measurement system is a sampled-data system:
- ADC sampling occurs at $f_s = 1.0\,\text{MSa/s}$ ($\Delta t_s = 1.0\,\mu\text{s}$).
- RMS calculation occurs at $f_{\text{eval}} = 10.0\,\text{kHz}$ ($\Delta t_{\text{step}} = 100\,\mu\text{s}$).
- The system evaluates **only** discrete samples.

Per Section 9 of the mandate, the formal decision domain is restricted to:

$$\mathbf{DECISION\_DOMAIN = DISCRETE\_SAMPLED\_RMS}$$

No claim of continuous analog coverage ($\forall t \in \mathbb{R}$) is asserted. Continuous-time behavior is addressed strictly through bounded transient amplitude thresholds as derived in [transient_detectability_bounds.csv](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/transient_detectability_bounds.csv).
