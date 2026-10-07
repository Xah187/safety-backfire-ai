# V3.4-N-CORR-04-R2-R1 — Master Mathematical & Hardware Reconciliation Audit Report

```text
====================================================================================================
MILESTONE:              V3.4-N-CORR-04-R2-R1
ROLE:                   FORENSIC DSP & METROLOGY AUDITOR
AUDIT TARGET:           V3.4-N-CORR-04-R2 PERSISTENCE DECISION BASELINE & SUPPORTING DERIVATIONS
DATE:                   OCTOBER 2026
FINAL AUDIT STATUS:     BLOCKED
====================================================================================================
```

---

## IMMUTABLE GOVERNANCE BLOCK

```text
MODEL_H                         = FROZEN
PRODUCTION_MODEL                = UNCHANGED
FIELD_DATA                      = ZERO
GROUND_TRUTH                    = NOT_ESTABLISHED
REAL_WORLD_VALIDATION           = NOT_ESTABLISHED
PHYSICAL_CAPTURE_AUTHORIZATION  = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO

Frozen Model H Parameters:
  k0         = 2.40
  beta_d     = 0.08
  beta_l     = 0.12
  beta_pitch = 0.22
```

---

## EXECUTIVE SUMMARY & AUDIT TAXONOMY

This milestone acts strictly as a forensic DSP and metrology reconciliation audit. In accordance with mandate:
- **No model tuning** has been performed.
- **Model H parameters** remain frozen.
- **Production software** (`scripts/v3_4/discover_event_candidates.py` and `scripts/v3_4/automated_evidence_screening.py`) remains untouched.
- **Physical capture authorization** is strictly NOT granted.
- **No missing evidence** has been manufactured or replaced by generic assumptions.

The primary objective of this audit is to categorize every statement within the `V3.4-N-CORR-04-R2` milestone baseline into one of seven forensic classes:
1. **Mathematically Verified**: Rigorously proven from explicit closed-form equations.
2. **Mathematically Conditional**: Proven conditionally under restrictive assumptions (e.g., specific signal domain or Region 3).
3. **Empirically Supported**: Supported by verifiable, traceable empirical physical data (currently zero).
4. **Report-Based Only**: Derived solely from secondary narrative technical summaries lacking raw traceable data.
5. **Hardware-Documented**: Proven directly by official manufacturer datasheets, manuals, or calibration sheets.
6. **Unresolved**: Conflicting or absent hardware evidence preventing definitive parameter assignment.
7. **Blocked**: Critical engineering prerequisites or safety invariants not satisfied, halting progress to physical execution.

```text
====================================================================================================
FORENSIC RECONCILIATION TAXONOMY MATRIX
----------------------------------------------------------------------------------------------------
Statement / Finding                                         Forensic Classification
----------------------------------------------------------------------------------------------------
RMS Piecewise Model (Regions 1, 2, 3) & Continuity          MATHEMATICALLY_VERIFIED (CONDITIONAL)
Region Boundary Factor B(Tw, tau_eff) & I0,crit = 0.562 A   MATHEMATICALLY_VERIFIED
0.80 A Example RMS Crossing (t_RMS = 15.99 ms > 15.0 ms)   MATHEMATICALLY_VERIFIED (RECLASSIFIED REGION 3)
Delta_flush = 1.117 ms Region-3 Offset                      MATHEMATICALLY_CONDITIONAL (REGION 3 ONLY)
Signal i(t) Domain (Exponential Envelope / RMS-Equiv)       MATHEMATICALLY_CONDITIONAL (REQUIRES EXPLICIT DOMAIN)
tau_eff = 2.8 ms Single-Exponential Fit                     EMPIRICAL_SINGLE_EXPONENTIAL_FIT (PROHIBITED GENERALIZATION)
Mode B Persistence Discrete Timer (100 intervals, 101 pts)  MATHEMATICALLY_VERIFIED (DEFINED PENDING IMPL AUDIT)
Post-Qualification Rebound Semantics (Non-re-arming FSM)    GOVERNANCE_DEFINED (REQUIRES EXPLICIT SEMANTICS)
TCPA300 Sensitivity (5 A/V & 50 A/V only; no 10 A/V)        HARDWARE_DOCUMENTED (HISTORICAL SCALE UNRESOLVED)
50-Ohm Unterminated Voltage Scaling                         NOT_QUANTITATIVELY_RECONSTRUCTABLE
20 kHz Analog Hardware Filter Claim                         NOT_VERIFIED (KEYSIGHT HARDWARE BW = 20 MHz)
Curtis 1238E Standard Catalog Motor Type (AC Induction)     HARDWARE_DOCUMENTED (PMSM COMPATIBILITY BLOCKED)
Vehicle Functional Safety / PL d Claim                      NOT_ESTABLISHED (TRANSFERS PROHIBITED)
Historical 10 Trials Timing & Waveform Claims               REPORT_BASED_NARRATIVE_ONLY (NON-TRACEABLE)
====================================================================================================
```

---

## SECTION 1: RMS CLOSED-FORM MODEL AUDIT

The continuous-time running RMS model defined in `RMS-PROC-V1.0` operates over an integration window $T_w = 2.0\text{ ms}$:
$$I_{\text{RMS}}(t) = \sqrt{\frac{1}{T_w} \int_{t - T_w}^{t} i^2(\tau)\,d\tau}$$

For a decaying transient initiated at $t_0$ from a steady-state value $I_0$:
$$i(t) = \begin{cases} I_0, & t < t_0 \\ I_0 \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right), & t \ge t_0 \end{cases}$$

### 1.1 Region 1: $t < t_0$
The window $[t - T_w, t]$ lies entirely within the pre-shutdown steady state:
$$I_{\text{RMS}}^2(t) = \frac{1}{T_w} \int_{t - T_w}^{t} I_0^2\,d\tau = \frac{I_0^2}{T_w} [t - (t - T_w)] = I_0^2 \implies I_{\text{RMS}}(t) = I_0$$
**Status**: **MATHEMATICALLY_VERIFIED**.

### 1.2 Region 2: $t_0 \le t < t_0 + T_w$
The integration window spans both steady-state and decaying exponential segments:
$$\int_{t - T_w}^{t} i^2(\tau)\,d\tau = \int_{t - T_w}^{t_0} I_0^2\,d\tau + \int_{t_0}^{t} I_0^2 \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right)\,d\tau$$
$$\int_{t - T_w}^{t_0} I_0^2\,d\tau = I_0^2 [t_0 - (t - T_w)] = I_0^2 [T_w - (t - t_0)]$$
$$\int_{t_0}^{t} I_0^2 \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right)\,d\tau = I_0^2 \left[-\frac{\tau_{\text{eff}}}{2} \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right)\right]_{t_0}^{t} = I_0^2 \frac{\tau_{\text{eff}}}{2} \left[1 - \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right)\right]$$
Dividing by $T_w$:
$$I_{\text{RMS}}^2(t) = I_0^2 \left[1 - \frac{t - t_0}{T_w} + \frac{\tau_{\text{eff}}}{2 T_w} \left(1 - \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right)\right)\right]$$
**Status**: **MATHEMATICALLY_VERIFIED**.

### 1.3 Region 3: $t \ge t_0 + T_w$
The integration window lies entirely within the exponential decay segment:
$$I_{\text{RMS}}^2(t) = \frac{1}{T_w} \int_{t - T_w}^{t} I_0^2 \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right)\,d\tau = \frac{I_0^2 \tau_{\text{eff}}}{2 T_w} \left[\exp\left(-\frac{2(t - T_w - t_0)}{\tau_{\text{eff}}}\right) - \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right)\right]$$
Factoring out $\exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right)$:
$$I_{\text{RMS}}^2(t) = I_0^2 \left[\frac{\tau_{\text{eff}}}{2 T_w} \left(\exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1\right)\right] \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right)$$
Taking the square root:
$$I_{\text{RMS}}(t) = I_0 \cdot C(T_w, \tau_{\text{eff}}) \cdot \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right)$$
where:
$$C(T_w, \tau_{\text{eff}}) = \sqrt{\frac{\tau_{\text{eff}}}{2 T_w} \left(\exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1\right)}$$
**Status**: **MATHEMATICALLY_VERIFIED**.

### 1.4 Boundary Continuity Verification
- **At $t = t_0$**:
  - Region 1: $I_{\text{RMS}}^2(t_0^-) = I_0^2$
  - Region 2: $I_{\text{RMS}}^2(t_0^+) = I_0^2 [1 - 0 + \frac{\tau_{\text{eff}}}{2 T_w}(1 - 1)] = I_0^2$
  - Continuous at $t = t_0$.
- **At $t = t_0 + T_w$**:
  - Region 2: $I_{\text{RMS}}^2((t_0 + T_w)^-) = I_0^2 [1 - 1 + \frac{\tau_{\text{eff}}}{2 T_w}(1 - e^{-2 T_w / \tau_{\text{eff}}})] = I_0^2 \frac{\tau_{\text{eff}}}{2 T_w}(1 - e^{-2 T_w / \tau_{\text{eff}}})$
  - Region 3: $I_{\text{RMS}}^2((t_0 + T_w)^+) = I_0^2 \left[\frac{\tau_{\text{eff}}}{2 T_w}(e^{2 T_w / \tau_{\text{eff}}} - 1)\right] e^{-2 T_w / \tau_{\text{eff}}} = I_0^2 \frac{\tau_{\text{eff}}}{2 T_w}(1 - e^{-2 T_w / \tau_{\text{eff}}})$
  - Continuous at $t = t_0 + T_w$.

**Section 1 Status**: `VERIFIED_CONDITIONALLY` (conditional on the exponential envelope / RMS-equivalent model domain established in Section 5).

---

## SECTION 2: CRITICAL CORRECTION: REGION-2 / REGION-3 CROSSING BOUNDARY

In milestone `V3.4-N-CORR-04-R2`, the narrative asserted that an operating current example with $I_0 = 0.80\text{ A}$ crossed the guarded threshold ($I_{\text{guarded}} = 0.410\text{ A}$) within Region 2.

We perform an independent forensic calculation using baseline parameters:
$$I_0 = 0.80\text{ A},\quad I_{\text{guarded}} = 0.410\text{ A},\quad \tau_{\text{eff}} = 2.8\text{ ms},\quad T_w = 2.0\text{ ms},\quad t_0 = 13.0\text{ ms}$$

1. **Physical Envelope Crossing ($t_{\text{phys}}$)**:
   $$i(t_{\text{phys}}) = I_0 \exp\left(-\frac{t_{\text{phys}} - t_0}{\tau_{\text{eff}}}\right) = I_{\text{guarded}}$$
   $$t_{\text{phys}} = t_0 + \tau_{\text{eff}} \ln\left(\frac{I_0}{I_{\text{guarded}}}\right) = 13.0 + 2.8 \ln\left(\frac{0.80}{0.410}\right) = 13.0 + 2.8 \times 0.668638 = 14.8722\text{ ms} \approx 14.87\text{ ms}$$

2. **RMS Amplitude at Region Boundary ($t = t_0 + T_w = 15.0\text{ ms}$)**:
   $$B(T_w, \tau_{\text{eff}}) = \sqrt{\frac{\tau_{\text{eff}}}{2 T_w}\left(1 - \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right)\right)}$$
   $$\frac{\tau_{\text{eff}}}{2 T_w} = \frac{2.8}{4.0} = 0.70,\quad \frac{2 T_w}{\tau_{\text{eff}}} = \frac{4.0}{2.8} = 1.428571$$
   $$\exp(-1.428571) = 0.239651 \implies 1 - 0.239651 = 0.760349$$
   $$B = \sqrt{0.70 \times 0.760349} = \sqrt{0.532244} \approx 0.729551$$
   $$I_{\text{RMS}}(15.0\text{ ms}) = I_0 \cdot B = 0.80 \times 0.729551 = 0.58364\text{ A} \approx 0.584\text{ A}$$

3. **Comparison with Threshold**:
   $$I_{\text{RMS}}(15.0\text{ ms}) = 0.584\text{ A} > I_{\text{guarded}} = 0.410\text{ A}$$
   Since $I_{\text{RMS}}(t)$ is strictly monotonically decreasing, $I_{\text{RMS}}(t) > 0.410\text{ A}$ for all $t \le 15.0\text{ ms}$.
   Therefore, **threshold crossing DOES NOT occur in Region 2**.

4. **RMS Crossing Time in Region 3 ($t_{\text{RMS}}$)**:
   $$C = \sqrt{0.70 \times (e^{1.428571} - 1)} = \sqrt{0.70 \times (4.172729 - 1)} = \sqrt{0.70 \times 3.172729} = \sqrt{2.220910} \approx 1.490272$$
   $$t_{\text{RMS}} = t_0 + \tau_{\text{eff}} \ln\left(\frac{I_0 \cdot C}{I_{\text{guarded}}}\right) = 13.0 + 2.8 \ln\left(\frac{0.80 \times 1.490272}{0.410}\right) = 13.0 + 2.8 \ln(2.907848) = 13.0 + 2.8 \times 1.067406 = 15.9887\text{ ms} \approx 15.99\text{ ms}$$

**Formal Audit Finding**:
- The prior R2 narrative assertion of Region 2 crossing for $I_0 = 0.80\text{ A}$ is **REFUTED**.
- Expected values confirmed: $t_{\text{phys}} \approx 14.87\text{ ms}$, $I_{\text{RMS}}(15.0\text{ ms}) \approx 0.584\text{ A}$, $t_{\text{RMS}} \approx 15.99\text{ ms}$.
- Formal reclassification: `RMS_CROSSING_REGION = REGION_3`.
- Key status: `low_residual_example = CORRECTED`.

---

## SECTION 3: DERIVATION OF THE ACTUAL REGION BOUNDARY

Rather than adopting an arbitrary threshold such as $I_0 > 1.0\text{ A}$, the boundary separating Region 2 crossing from Region 3 crossing is derived exactly from first principles.

### 3.1 General Symbolic Boundary
The threshold crossing occurs precisely at the boundary $t^* = t_0 + T_w$ when:
$$I_{\text{RMS}}(t_0 + T_w) = I_{\text{guarded}}$$
Since $I_{\text{RMS}}(t_0 + T_w) = I_0 \cdot B(T_w, \tau_{\text{eff}})$, where:
$$B(T_w, \tau_{\text{eff}}) = \sqrt{\frac{\tau_{\text{eff}}}{2 T_w}\left(1 - \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right)\right)}$$

The critical pre-shutdown current $I_{0,\text{crit}}$ is:
$$I_{0,\text{crit}}(I_{\text{guarded}}, T_w, \tau_{\text{eff}}) = \frac{I_{\text{guarded}}}{B(T_w, \tau_{\text{eff}})} = \frac{I_{\text{guarded}}}{\sqrt{\frac{\tau_{\text{eff}}}{2 T_w}\left(1 - \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right)\right)}}$$

### 3.2 Partition Rule
- **Region 2 Crossing ($t_0 \le t_{\text{RMS}} \le t_0 + T_w$)**:
  $$I_0 \le I_{0,\text{crit}} \iff I_0 \cdot B(T_w, \tau_{\text{eff}}) \le I_{\text{guarded}}$$
- **Region 3 Crossing ($t_{\text{RMS}} > t_0 + T_w$)**:
  $$I_0 > I_{0,\text{crit}} \iff I_0 \cdot B(T_w, \tau_{\text{eff}}) > I_{\text{guarded}}$$

### 3.3 Numerical Frozen-Baseline Boundary
For $T_w = 2.0\text{ ms}$, $\tau_{\text{eff}} = 2.8\text{ ms}$, and $I_{\text{guarded}} = 0.410\text{ A}$:
$$B = 0.729551$$
$$I_{0,\text{crit}} = \frac{0.410}{0.729551} = 0.56199\text{ A} \approx 0.562\text{ A}$$

```text
====================================================================================================
NUMERICAL REGION BOUNDARY AUDIT TABLE (T_w = 2.0 ms, tau_eff = 2.8 ms, I_guarded = 0.410 A)
----------------------------------------------------------------------------------------------------
Pre-Shutdown Current I0   I_RMS(t0 + Tw)   Threshold Status               Classification
----------------------------------------------------------------------------------------------------
0.450 A                  0.328 A          < 0.410 A                      REGION_2
0.500 A                  0.365 A          < 0.410 A                      REGION_2
0.550 A                  0.401 A          < 0.410 A                      REGION_2
0.562 A (Critical)       0.410 A          = 0.410 A                      BOUNDARY
0.600 A                  0.438 A          > 0.410 A                      REGION_3
0.800 A                  0.584 A          > 0.410 A                      REGION_3
1.000 A                  0.730 A          > 0.410 A                      REGION_3
====================================================================================================
```
**Section 3 Status**: `REQUIRED_AND_VERIFIED`.

---

## SECTION 4: RESTRICTION OF THE 1.117 ms FLUSH LAG RESULT

In previous documents, $\Delta_{\text{flush}} \approx 1.117\text{ ms}$ was characterized as a universal analytical delay. This audit restricts its validity.

### 4.1 Derivation in Region 3
When $I_0 > I_{0,\text{crit}}$, both $t_{\text{phys}}$ and $t_{\text{RMS}}$ are governed by single-exponential expressions:
$$t_{\text{phys}} = t_0 + \tau_{\text{eff}} \ln\left(\frac{I_0}{I_{\text{guarded}}}\right)$$
$$t_{\text{RMS}} = t_0 + \tau_{\text{eff}} \ln\left(\frac{I_0 \cdot C}{I_{\text{guarded}}}\right)$$
Subtracting $t_{\text{phys}}$ from $t_{\text{RMS}}$:
$$\Delta_{\text{flush}} = t_{\text{RMS}} - t_{\text{phys}} = \tau_{\text{eff}} \ln(C) = \frac{\tau_{\text{eff}}}{2} \ln\left[\frac{\tau_{\text{eff}}}{2 T_w} \left(\exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1\right)\right]$$
For $T_w = 2.0\text{ ms}$ and $\tau_{\text{eff}} = 2.8\text{ ms}$:
$$C \approx 1.490272 \implies \ln(C) \approx 0.398958 \implies \Delta_{\text{flush}} = 2.8 \times 0.398958 = 1.11708\text{ ms} \approx 1.117\text{ ms}$$
Notice that $I_0$ cancels out completely in Region 3.

### 4.2 Failure in Region 2
When $I_0 \le I_{0,\text{crit}}$, the threshold equation in Region 2 is transcendental:
$$g(x) = 1 - \frac{x}{T_w} + \frac{\tau_{\text{eff}}}{2 T_w}\left(1 - \exp\left(-\frac{2 x}{\tau_{\text{eff}}}\right)\right) = \left(\frac{I_{\text{guarded}}}{I_0}\right)^2,\quad \text{where } x = t - t_0 \in [0, T_w]$$
Here, $x$ depends nonlinearly on the ratio $(I_{\text{guarded}} / I_0)^2$. Consequently:
$$\Delta_{\text{flush}}(I_0) = t_{\text{RMS}}(I_0) - t_{\text{phys}}(I_0) = x(I_0) - \tau_{\text{eff}} \ln\left(\frac{I_0}{I_{\text{guarded}}}\right) \ne \tau_{\text{eff}} \ln(C)$$
For example, with $I_0 = 0.500\text{ A}$:
- $t_{\text{phys}} = 13.0 + 2.8 \ln(0.500 / 0.410) = 13.555\text{ ms}$
- Solving $g(x) = (0.410 / 0.500)^2 = 0.6724$ yields $x \approx 1.608\text{ ms} \implies t_{\text{RMS}} \approx 14.608\text{ ms}$
- $\Delta_{\text{flush}} = 14.608 - 13.555 = 1.053\text{ ms} \ne 1.117\text{ ms}$.

### 4.3 Mandatory Terminology Restriction
- The term "exact analytical delay" is prohibited as a general descriptor.
- The term must be replaced with: **"exact Region-3 analytical threshold-crossing offset"**.
- Key status: `region_3_flush_offset = VERIFIED_CONDITIONALLY`.

---

## SECTION 5: SIGNAL DEFINITION & MODEL DOMAIN AUDIT

A critical ambiguity in earlier versions was whether $i(t)$ represented:
- Option A: Instantaneous phase current ($i_{\text{phase}}(t)$)
- Option B: Instantaneous current envelope ($I_{\text{env}}(t)$)
- Option C: RMS-equivalent envelope signal ($i_{\text{RMS-equiv}}(t)$)

### 5.1 Mathematical Proof of Unmodulated Carrier Absence
In a physical 3-phase AC traction motor (PMSM or AC Induction), phase currents are modulated by high-frequency PWM (e.g., 8–16 kHz) and synchronous fundamental electrical frequency ($f_e \approx 10\text{--}300\text{ Hz}$):
$$i_{\text{phase}}(t) = I_{\text{pk}}(t) \sin(\omega_e t + \phi_0) + i_{\text{PWM}}(t)$$
If $i(\tau)$ in the running RMS integral $\frac{1}{T_w} \int_{t-T_w}^t i^2(\tau)\,d\tau$ contained $\sin(\omega_e \tau)$, the resulting integral would contain double-frequency cross-terms:
$$\int \sin^2(\omega_e \tau)\,d\tau = \frac{\tau}{2} - \frac{\sin(2\omega_e \tau)}{4\omega_e}$$
The closed-form derivation evaluated in Section 1 integrates purely monotonic terms ($I_0^2$ and $I_0^2 e^{-2\tau/\tau_{\text{eff}}}$) without any oscillatory modulation.

### 5.2 Formal Classification
- The mathematical derivation is valid **only** if the input signal is an unmodulated exponential envelope or an RMS-equivalent envelope.
- Formally declared:
  ```text
  MODEL_DOMAIN = EXPONENTIAL ENVELOPE / RMS-EQUIVALENT SIGNAL
  ```
- **Prohibition**: Interpretation of this closed form as a general instantaneous AC-current waveform is strictly prohibited unless an explicit sinusoidal carrier and PWM ripple model is formulated and integrated.
- Key status: `signal_definition = REQUIRES_EXPLICIT_DOMAIN`.

---

## SECTION 6: TAU_EFF GOVERNANCE

The decay parameter $\tau_{\text{eff}} = 2.8\text{ ms}$ has been repeatedly cited in prior milestones.

### 6.1 Audit of Physical Origin
- The parameter $\tau_{\text{eff}} = 2.8\text{ ms}$ was obtained as an empirical single-exponential best-fit curve to a historical narrative waveform trace.
- It does **not** reflect a first-principles derivation of motor stator inductance $L_s$, stator resistance $R_s$, inverter freewheeling diode characteristics, or active discharge circuitry.

### 6.2 Lack of Documented Dependencies
The project archive contains zero empirical or theoretical characterizations of how $\tau_{\text{eff}}$ varies across:
1. Motor type (AC induction vs interior PMSM vs surface PMSM),
2. Controller hardware revision (Curtis 1238E-5421 vs 1238SE),
3. Inverter gate-drive firmware and VCL shutdown routines,
4. Pre-shutdown operating current magnitude and stator temperature,
5. Vehicle mechanical speed and back-EMF magnitude at E-Stop initiation,
6. DC-link bus voltage,
7. STO (Safe Torque Off) hardware discharge topology,
8. Measurement transducer and anti-aliasing filter delay.

### 6.3 Governance Invariant
- Formally classified as:
  ```text
  TAU_EFF_CLASSIFICATION = EMPIRICAL_SINGLE_EXPONENTIAL_FIT
  TAU_EFF_GENERALIZATION = PROHIBITED
  ```
- Must never be treated as a universal vehicle constant or safety-system physical constant.

---

## SECTION 7: PERSISTENCE STATE MACHINE AUDIT (MODE B)

The discrete persistence monitoring algorithm operates on rolling RMS samples evaluated at interval $\Delta t = 0.1\text{ ms}$ ($f_s = 10\text{ kHz}$) with window $T_w = 2.0\text{ ms}$ ($N_w = 20\text{ samples}$).

### 7.1 Exact Mode B Semantics
- **$k_{\text{start}}$**: The index of the first evaluation point where $I_{\text{RMS}}[k] < I_{\text{guarded}}$.
- **$k_{\text{qualified}}$**: Exactly $k_{\text{start}} + 100$.
- **Elapsed Persistence Duration**:
  $$\Delta T = (k_{\text{qualified}} - k_{\text{start}}) \times \Delta t = 100 \times 0.1\text{ ms} = 10.0\text{ ms}$$
- **Evaluation Points**: Exactly $101$ consecutive evaluations ($k \in [k_{\text{start}}, k_{\text{start}} + 100]$), all satisfying $I_{\text{RMS}}[k] < I_{\text{guarded}}$.
- **Total Data Span**:
  The running RMS at $k_{\text{start}}$ spans $[t_0, t_0 + T_w]$. The running RMS at $k_{\text{qualified}}$ spans $[t_0 + 10.0\text{ ms}, t_0 + 10.0\text{ ms} + T_w]$. Total raw data spanned is:
  $$\Delta T_{\text{span}} = 10.0\text{ ms} + T_w = 10.0\text{ ms} + 2.0\text{ ms} = 12.0\text{ ms}$$

### 7.2 Deterministic Pseudocode
The following reference algorithm eliminates all ambiguities regarding counter initialization, qualification, and rebound:

```python
class PersistenceFSM_ModeB:
    def __init__(self, i_guarded=0.410, n_persist=100, dt=0.0001):
        self.i_guarded = i_guarded
        self.n_persist = n_persist
        self.dt = dt
        self.state = "STATE_0_ACTIVE"
        self.k_start = None
        self.counter = 0
        self.t_qualified = None
        self.declaration = "NOT_DEENERGIZED"
        self.fault = None

    def evaluate_frame(self, k, t_k, i_rms_k):
        """
        Deterministic Mode B evaluation frame.
        k: sample index (integer)
        t_k: timestamp in seconds
        i_rms_k: evaluated running RMS current in Amperes
        """
        # 1. Active State: Awaiting first sub-threshold sample
        if self.state == "STATE_0_ACTIVE":
            if i_rms_k < self.i_guarded:
                self.state = "STATE_1_MONITORING"
                self.k_start = k
                self.counter = 0
            return self.get_status()

        # 2. Monitoring State: Accumulating consecutive qualifying samples
        elif self.state == "STATE_1_MONITORING":
            if i_rms_k < self.i_guarded:
                self.counter += 1
                if self.counter == self.n_persist:  # Exactly 100 increments (101 evaluations)
                    self.state = "STATE_3_QUALIFIED"
                    self.t_qualified = t_k
                    self.declaration = "DEENERGIZED_DECLARED"
            else:
                # Rebound before qualification -> reset to active
                self.state = "STATE_0_ACTIVE"
                self.k_start = None
                self.counter = 0
            return self.get_status()

        # 3. Qualified State: Terminal qualification; monitor for post-qualification rebound
        elif self.state == "STATE_3_QUALIFIED":
            if i_rms_k >= self.i_guarded:
                self.state = "STATE_4_REBOUND_FAULT"
                self.fault = "FAULT_POST_QUALIFICATION_REBOUND"
                # Historical t_qualified is preserved, but trial is invalidated retrospectively
            return self.get_status()

        # 4. Fault State: Latched terminal state
        elif self.state == "STATE_4_REBOUND_FAULT":
            return self.get_status()

    def get_status(self):
        return {
            "state": self.state,
            "declaration": self.declaration,
            "t_qualified": self.t_qualified,
            "fault": self.fault
        }
```
**Section 7 Status**: `persistence_mode_b = DEFINED_PENDING_IMPLEMENTATION_AUDIT`.

---

## SECTION 8: POST-QUALIFICATION REBOUND SEMANTICS

In milestone `V3.4-N-CORR-04-R2`, the state machine contained an unresolved ambiguity between treating `STATE_3_QUALIFIED` as terminal vs permitting a post-qualification surge to transition back to `STATE_0_ACTIVE`.

### 8.1 Zero DAQ Actuator Authority
The research DAQ is strictly an observational instrument:
```text
RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```
The DAQ cannot re-close contactors, reset interlocks, command traction inverter modulation, or alter vehicle physical state. Any current surge occurring after $t_{\text{qualified}}$ is a physical anomaly (e.g., inductive kickback, PWM re-firing, EMI burst, or sensor artifact).

### 8.2 Governance Separation & Invalidation Decision
1. **Declaration**: `DEENERGIZED_DECLARATION` is an immutable record that the electrical system satisfied persistence criteria over $[t_{\text{start}}, t_{\text{qualified}}]$.
2. **Rebound Anomaly**: If current subsequently exceeds $I_{\text{guarded}}$, the state machine transitions to `STATE_4_REBOUND_FAULT` and asserts `FAULT_POST_QUALIFICATION_REBOUND`.
3. **Governance Resolution**:
   - The timestamp $t_{\text{qualified}}$ remains recorded in the diagnostic event log.
   - However, for safety-critical acceptance and commissioning trial approval, the post-qualification rebound **retrospectively invalidates the commissioning trial**.
   - The state machine does **not** silently re-arm or transition back to `STATE_0_ACTIVE`.
- Key status: `post_qualification_rebound = REQUIRES_EXPLICIT_SEMANTICS`.

---

## SECTION 9: SIGNAL-PATH & TRANSDUCER AUDIT

### 9.1 Tektronix TCP303 / TCPA300 Sensitivity Specs
Historical project records repeatedly claimed an instrument range of $10\text{ A/V}$.
Official manufacturer documentation for the Tektronix TCPA300 amplifier paired with TCP303 probe confirms:
- **Available Hardware Ranges**:
  1. $5\text{ A/V}$ (High sensitivity mode: $5\text{ A/V}$ into $50\ \Omega$)
  2. $50\text{ A/V}$ (Low sensitivity mode: $50\text{ A/V}$ into $50\ \Omega$)
- **Finding**: **No $10\text{ A/V}$ range exists on the TCPA300 / TCP303 system**.
- **Audit Ruling**:
  ```text
  HISTORICAL_CURRENT_SCALE = UNRESOLVED
  ```
  The historical current scale cannot be inferred or assumed. It remains formally unresolved until physical calibration records or setup configurations are recovered.

### 9.2 Overall Instrument Chain Status
Due to unresolved current probe gain and unverified analog front-end response:
```text
INSTRUMENT_CHAIN = BLOCKED
```

---

## SECTION 10: 50-OHM TERMINATION SCALING AUDIT

The TCPA300 output amplifier has a $50\ \Omega$ source impedance designed to terminate into a $50\ \Omega$ oscilloscope load.

### 10.1 Audit of the "Exact 2x Error" Claim
Prior technical reports stated that connecting the TCPA300 to a $1\text{ M}\Omega$ oscilloscope input without a feedthrough terminator creates exactly a $2\times$ ($100\%$) voltage error.
- **Circuit Analysis**:
  At DC and low frequencies, a voltage divider between $R_{\text{source}} = 50\ \Omega$ and $R_{\text{load}} = 1\text{ M}\Omega$ yields:
  $$V_{\text{load}} = V_{\text{source}} \frac{1\text{ M}\Omega}{50\ \Omega + 1\text{ M}\Omega} \approx 1.0 \times V_{\text{source}}$$
  Under matched termination ($R_{\text{load}} = 50\ \Omega$):
  $$V_{\text{load,matched}} = V_{\text{source}} \frac{50}{50 + 50} = 0.5 \times V_{\text{source}}$$
  The ratio is $\frac{1.0}{0.5} = 2.0$.
- **High-Frequency & Transient Analysis**:
  However, coaxial cable transmission line effects, cable capacitance, amplifier feedback loop compensation, and high-frequency reflections mean that during transient decay and PWM ripple, the frequency response is non-flat and dispersive.
- **Audit Ruling**:
  The assertion of an exact, uniform $2.0\times$ scalar error across dynamic transients is physically unsubstantiated without an active S-parameter calibration of the specific cable and oscilloscope setup.
  Formally downgraded to:
  ```text
  UNTERMINATED_OUTPUT_SCALING = NOT_QUANTITATIVELY_RECONSTRUCTABLE
  ```

---

## SECTION 11: DSOX1204G FILTER AUDIT

### 11.1 Analog Hardware vs Scope Math vs Pipeline Processing
Prior documents confused three distinct filtering domains:
1. **Analog Hardware Front-End**: Keysight DSOX1204G hardware analog bandwidth limit is $20\text{ MHz}$. It does **not** possess an internal $20\text{ kHz}$ analog hardware filter.
2. **Scope Math Filter**: Oscilloscope firmware math functions (such as low-pass DSP math channels) are internal display functions and are not part of the raw ADC acquisition data path.
3. **RMS-PROC-V1.0 Software Pipeline**: The frozen software pipeline ingests raw digitized samples at $10\text{ kHz}$ and computes running RMS over $T_w = 2.0\text{ ms}$.

### 11.2 Audit Rulings
- The claim of an analog $20\text{ kHz}$ hardware filter is unverified:
  ```text
  20_KHZ_ANALOG_FILTER = NOT_VERIFIED
  ```
- Scope math filters must never be inserted into or substituted for the frozen `RMS-PROC-V1.0` measurement pipeline.

---

## SECTION 12: CONTROLLER BASELINE & COMPATIBILITY AUDIT

### 12.1 Curtis 1238E Standard Baseline
Official Curtis documentation establishes that standard 1238E series controllers (e.g., 1238E-5421) are designed natively for **AC Induction motors**, using indirect field-oriented control (IFOC).
In contrast, Curtis "SE" series controllers (e.g., 1238SE) incorporate hardware and firmware updates designed for dual induction / permanent magnet AC (PMAC/PMSM) control.

### 12.2 PMSM Compatibility Finding
- While custom VCL (Vehicle Control Language) and firmware builds theoretically exist, there is **zero evidence** in the project repository of a validated parameter file, encoder interface definition, or VCL script enabling 1238E-5421 to control a 48V PMSM powertrain.
- We do **not** assert the negative that "1238E can never control PMSM".
- Instead, the formal finding is:
  ```text
  CURTIS_1238E_STANDARD_MOTOR_TYPE = AC_INDUCTION
  MOTOR_CONTROLLER_COMPATIBILITY   = BLOCKED
  ```

---

## SECTION 13: SAFETY CLASSIFICATION AUDIT

Prior technical documents contained assertions that the Curtis 1238E provides an overall safety integrity rating of "PL d".

### 13.1 Component Claim vs Vehicle Functional Safety
- A component manufacturer claim (e.g., EN ISO 13849-1 PL d for specific STO or dual-microprocessor supervisor circuits) applies **only** to the isolated component under strict installation conditions.
- It does **not** confer PL d compliance to the vehicle-level emergency stop function, motor de-energization path, or data acquisition pipeline.
- Furthermore, no safety certificate for Curtis 1238SE or other models may be transferred to 1238E-5421 without exact documentation.

### 13.2 Audit Finding
```text
VEHICLE_FUNCTIONAL_SAFETY_CLAIM = NOT_ESTABLISHED
```

---

## SECTION 14: HISTORICAL 10 TRIALS EVIDENCE STATUS

Milestones V3.4-N through V3.4-N-CORR-04-R2 frequently referenced a dataset of "10 historical E-Stop decay trials".

### 14.1 Forensic Provenance Audit
- **Raw Waveform Data**: Zero raw oscillograms, CSV files, or binary trace dumps exist in the repository.
- **Cryptographic Integrity**: Zero SHA-256 hashes or timestamps exist for the raw acquisition.
- **Calibration Certificates**: Zero calibration records for the current probe, amplifier, or scope exist.
- **Quantitative Traceability**: The timing figures ($14.8\text{ ms}$, $15.2\text{ ms}$, etc.) exist solely as narrative citations in secondary technical summaries.

### 14.2 Audit Finding
- The historical trials cannot be used as traceable quantitative evidence.
- They do not validate the $1.117\text{ ms}$ RMS offset or the $10.0\text{ ms}$ persistence time.
- Classified formally as:
  ```text
  TIMING_EVIDENCE          = REPORT_BASED_NARRATIVE_ONLY
  HISTORICAL_CURRENT_SCALE = UNRESOLVED
  ```

---

## SECTION 15: COMPLETE DELIVERABLES MANIFEST

The required milestone artifacts have been established in `outputs/v3_4_n_corr_04_r2_r1/`:

1. [`rms_region_boundary.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/rms_region_boundary.md): Exact symbolic derivation of $B(T_w, \tau_{\text{eff}})$, critical current $I_{0,\text{crit}} \approx 0.562\text{ A}$, and correction of the $0.80\text{ A}$ example to Region 3.
2. [`rms_model_domain.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/rms_model_domain.md): Analysis of signal definition $i(t)$, proof of carrier absence, declaration of `MODEL_DOMAIN`, and $\tau_{\text{eff}}$ governance.
3. [`rms_crossing_reconciliation.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/rms_crossing_reconciliation.md): Detailed comparison of Region 2 vs Region 3 crossing dynamics and restriction of $\Delta_{\text{flush}} = 1.117\text{ ms}$.
4. [`persistence_semantics_v4.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/persistence_semantics_v4.md): Formal definition of Mode B discrete timer semantics ($100$ intervals, $101$ evaluation points, $12.0\text{ ms}$ data span).
5. [`persistence_fsm_audit.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/persistence_fsm_audit.md): Deterministic FSM pseudocode, post-qualification rebound fault latching, and zero DAQ actuator authority.
6. [`signal_path_reconciliation_v3.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/signal_path_reconciliation_v3.md): TCPA300 range audit ($5\text{ A/V}$ and $50\text{ A/V}$ only), unterminated $50\ \Omega$ load scaling analysis, and filter separation.
7. [`controller_compatibility_reconciliation_v2.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/controller_compatibility_reconciliation_v2.md): Curtis 1238E baseline audit, motor compatibility block, and safety claim audit.
8. [`historical_trial_evidence_status.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/historical_trial_evidence_status.md): Evidence status report for the 10 historical trials.
9. [`r2_r1_master_audit.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/r2_r1_master_audit.md): This comprehensive master forensic audit report.
10. [`r2_r1_audit_results.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/r2_r1_audit_results.json): Authoritative machine-readable audit dictionary matching Section 16.
11. [`release_blockers.md`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/release_blockers.md): Formally documented blockers preventing physical capture authorization.

---

## SECTION 16: AUTHORITATIVE AUDIT RESULT JSON

The authoritative audit result dictionary is recorded in [`r2_r1_audit_results.json`](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/r2_r1_audit_results.json):

```json
{
  "rms_closed_form": "VERIFIED_CONDITIONALLY",
  "region_2_boundary": "REQUIRED_AND_VERIFIED",
  "region_3_flush_offset": "VERIFIED_CONDITIONALLY",
  "low_residual_example": "CORRECTED",
  "signal_definition": "REQUIRES_EXPLICIT_DOMAIN",
  "tau_eff_generalization": "PROHIBITED",
  "persistence_mode_b": "DEFINED_PENDING_IMPLEMENTATION_AUDIT",
  "post_qualification_rebound": "REQUIRES_EXPLICIT_SEMANTICS",
  "historical_current_scale": "UNRESOLVED",
  "instrument_chain": "BLOCKED",
  "motor_controller_compatibility": "BLOCKED",
  "vehicle_functional_safety_claim": "NOT_ESTABLISHED",
  "physical_capture_authorization": "NOT_GRANTED",
  "real_world_validation": "NOT_ESTABLISHED",
  "milestone_status": "BLOCKED"
}
```

---

## SECTION 17: ADHERENCE TO ABSOLUTE PROHIBITIONS

This audit certifies total compliance with all mandated prohibitions:
1. **Model H unmodified**: $k_0 = 2.40, \beta_d = 0.08, \beta_l = 0.12, \beta_{\text{pitch}} = 0.22$.
2. **Parameters untuned**: No tuning of $k_0$ or $\beta$ coefficients was performed.
3. **Production scripts unchanged**: Neither `discover_event_candidates.py` nor `automated_evidence_screening.py` was modified.
4. **Calibration certificates uninvented**: No non-existent calibration records were fabricated.
5. **Raw traces uninvented**: No fictitious waveform traces were generated.
6. **Historical settings not inferred**: TCPA300 range remains strictly `UNRESOLVED`.
7. **PMSM compatibility not claimed**: Remains strictly `BLOCKED`.
8. **Vehicle-level PL/SIL compliance not claimed**: Remains strictly `NOT_ESTABLISHED`.
9. **Mathematical derivations not called physical validation**: Explicitly restricted to analytical domain.
10. **Historical 10 trials not called quantitative validation**: Explicitly labeled `REPORT_BASED_NARRATIVE_ONLY`.
11. **Physical capture authorization not granted**: Strictly `NOT_GRANTED`.
12. **Actuator authority not granted to research DAQ**: Strictly `ZERO`.
13. **Missing evidence not replaced by engineering assumptions**: Strictly cataloged as blockers.

---

## FINAL GOVERNANCE AUDIT BLOCK

```text
====================================================================================================
FINAL MILESTONE GOVERNANCE VERDICT
====================================================================================================
V3_4_N_CORR_04_R2_R1_STATUS     = BLOCKED
MILESTONE_STATUS                = BLOCKED
PHYSICAL_CAPTURE_AUTHORIZATION  = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO

MODEL_H                         = FROZEN
PRODUCTION_MODEL                = UNCHANGED
FIELD_DATA                      = ZERO
GROUND_TRUTH                    = NOT_ESTABLISHED
REAL_WORLD_VALIDATION           = NOT_ESTABLISHED
====================================================================================================
```
