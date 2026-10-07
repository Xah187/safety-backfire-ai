# V3.4-N-CORR-04-R4 — Measurement Uncertainty & Decision Framework

**Document:** `outputs/v3_4_n_corr_04_r4/measurement_uncertainty_decision_framework.md`  
**Milestone:** V3.4-N-CORR-04-R4 (Evidence Readiness, Dependency Closure & Traceability Audit)  
**Governance Invariants:**
```text
MODEL_H                         = FROZEN (k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22)
PRODUCTION_MODEL                = UNCHANGED
FIELD_DATA                      = ZERO
GROUND_TRUTH                    = NOT_ESTABLISHED
REAL_WORLD_VALIDATION           = NOT_ESTABLISHED
PHYSICAL_CAPTURE_AUTHORIZATION  = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
UNCERTAINTY_BUDGET              = INCOMPLETE
FINAL_STATUS                    = BLOCKED
```

---

## 1. Governance Principles of Metrological Uncertainty

In ISO/IEC Guide 98-3 (GUM - *Guide to the Expression of Uncertainty in Measurement*) and ASME B89.7.3.1 (*Guidelines for Decision Rules*), establishing a guarded acceptance threshold requires a rigorous, traceable uncertainty budget.

**Authoritative Governance Rules:**
1. **Separation of Uncertainty Domains:** Uncertainty contributions **SHALL NOT** be combined automatically using a single Root-Sum-Square (RSS) equation without establishing mathematical sensitivity coefficients and correlation matrices.
2. **No Fabricated Budgets:** If experimental or calibration data for any component is absent, the parameter **SHALL NOT** be filled with synthetic "engineering estimates".
3. **Budget Status:** With zero calibration records, unrecorded oscilloscope vertical scales, and unverified motor parameters:
   $$\text{UNCERTAINTY\_BUDGET} = \text{INCOMPLETE}$$
4. **No Synthetic Guarded Threshold:** Guarded thresholds ($0.410\,\text{A}$, $0.413\,\text{A}$, or $0.460\,\text{A}$) **SHALL NOT** be claimed as certified boundaries.

---

## 2. Six-Domain Uncertainty Decomposition

The total uncertainty associated with traction current de-energization qualification is decomposed into six independent physical and algorithmic domains:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   TOTAL DE-ENERGIZATION UNCERTAINTY                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────┬───────────────┼───────────────┬────────────────┐
    ▼               ▼               ▼               ▼                ▼
[1. MEASUREMENT] [2. MODEL]  [3. IMPL]      [4. TIMING]     [5. CAL]  [6. ALIAS]
 - ADC noise     - Diode drop - Fencepost    - Clock jitter  - Probe   - HF folding
 - Transducer    - Inductance - Float64      - Trigger delay - Scope   - Decimation
   gain error      saturation - Grid phase   - Skew          - Term    - Beat notes
```

### Domain 1: Measurement Uncertainty ($u_{\text{meas}}$)
*Physical sensor and front-end analog instrumentation noise.*
- **Type:** Type A (random noise) and Type B (quantization).
- **Distribution:** Normal (analog noise floor); Uniform (ADC quantization step $\pm \frac{1}{2}\,\text{LSB}$).
- **Standard Uncertainty:** `INDETERMINATE`. Because the oscilloscope vertical sensitivity ($\text{V/div}$) used during historical runs is unrecorded (Node E13 is `MISSING`), the physical value of $1\,\text{LSB}$ in Amperes cannot be calculated ($0.781\,\text{A/LSB}$ at $50\,\text{A/V}$ vs $0.078\,\text{A/LSB}$ at $5\,\text{A/V}$).
- **Source:** Keysight DSOX1204G 8-bit digitizer; Tektronix TCPA300 amplifier thermal noise.
- **Correlation Status:** Uncorrelated with external clocks; strongly correlated with vertical channel scale.
- **Justification:** Without recorded vertical scales, measurement uncertainty cannot be bounded.

### Domain 2: Model Uncertainty ($u_{\text{model}}$)
*Approximation errors introduced by simplifying complex physical systems into an ideal exponential decay.*
- **Type:** Type B (systematic modeling error).
- **Distribution:** Unknown / Non-symmetric.
- **Standard Uncertainty:** `INDETERMINATE`. The ideal continuous model assumes:
  $$i(t) = I_0 e^{-t/\tau}$$
  In real powertrains, three physical phenomena introduce large systematic deviations:
  1. **Inverter Freewheeling Diodes:** Diodes exhibit a non-linear threshold voltage drop ($V_f \approx 0.7 - 1.2\,\text{V}$) that accelerates current decay at low currents relative to a pure $L/R$ exponential.
  2. **Magnetic Saturation:** Motor inductance $L(i)$ varies non-linearly with stator current.
  3. **Rotor Rotation / Back-EMF:** If a PMSM rotor continues spinning, back-EMF maintains current, violating the passive decay model entirely.
- **Source:** Analytical piecewise model assumptions.
- **Correlation Status:** Correlated with instantaneous current magnitude and motor speed.
- **Justification:** Zero motor characterization data exists in the repository.

### Domain 3: Implementation Uncertainty ($u_{\text{impl}}$)
*Algorithmic errors resulting from discrete approximation of continuous mathematical operations.*
- **Type:** Type B.
- **Distribution:** Uniform over the decimation stride interval $[0, \Delta t]$.
- **Standard Uncertainty:** For evaluation grid step $\Delta t = 0.1\,\text{ms}$ ($M=100$ samples):
  $$u_{\text{grid}} = \frac{\Delta t}{\sqrt{12}} = \frac{0.1\,\text{ms}}{\sqrt{12}} \approx 0.0289\,\text{ms}$$
  Floating-point IEEE 754 roundoff error is bounded by:
  $$u_{\text{float}} \le 2^{-53} \cdot I_{\text{RMS}} \approx 10^{-16}\,\text{A} \quad \text{(negligible)}$$
- **Source:** Discrete RMS stride $M=100$ and finite window size $N=2000$.
- **Correlation Status:** Uncorrelated with analog noise.
- **Justification:** Derived analytically in `discrete_rms_index_contract.md`.

### Domain 4: Timestamp & Trigger Uncertainty ($u_{\text{time}}$)
*Timing errors in synchronization, trigger latency, and clock stability.*
- **Type:** Type B.
- **Distribution:** Uniform / Rectangular.
- **Standard Uncertainty:** `INDETERMINATE`. The total timing chain error is:
  $$t_{\text{error}} = \delta t_{\text{trig\_delay}} + \delta t_{\text{jitter}} + \delta t_{\text{clock\_skew}} + \delta t_{\text{prop}}$$
  - Oscilloscope timebase accuracy: $\pm 50\,\text{ppm}$ ($\approx 0.05\,\mu\text{s}$ over $1.0\,\text{s}$).
  - Hardware trigger circuit latency: Typically $10 - 50\,\text{ns}$.
  - Primary gap: The electrical source of the E-Stop trigger (auxiliary microswitch contact bounce, optocoupler delay, or software CAN flag) is undocumented. Contactor contact bounce alone can introduce $2.0 - 15.0\,\text{ms}$ of trigger ambiguity!
- **Source:** Bench wiring, trigger pick-off, scope timebase crystal.
- **Correlation Status:** Independent of signal magnitude.
- **Justification:** Unrecorded trigger hardware parameters.

### Domain 5: Calibration & Metrological Traceability Uncertainty ($u_{\text{cal}}$)
*Uncertainty in the physical transfer factors relating millivolts to stator Amperes.*
- **Type:** Type B.
- **Distribution:** Normal ($k=2$).
- **Standard Uncertainty:** `INDETERMINATE`.
  - Tektronix TCP303 / TCPA300 factory gain uncertainty: $\pm 1.0\%$ of reading (when calibrated).
  - Scope vertical gain accuracy: $\pm 1.5\%$ to $\pm 2.0\%$.
  - Scope channel termination impedance: If an external $50\,\Omega$ terminator was used, tolerance is typically $\pm 1.0\%$. If unterminated ($1\,\text{M}\Omega$), voltage doubling error is $\sim 100\%$.
  - **Zero calibration certificates exist in the repository.**
- **Source:** Instrument aging, temperature drift, uncalibrated state.
- **Correlation Status:** Multiplicative systematic error.
- **Justification:** Node E15 is `MISSING`.

### Domain 6: Sampling & Aliasing Uncertainty ($u_{\text{alias}}$)
*Error introduced by unattenuated high-frequency harmonics folding into the baseband.*
- **Type:** Type B.
- **Distribution:** Unknown (phase-dependent deterministic beat frequencies).
- **Standard Uncertainty:** `INDETERMINATE`. As proven in `anti_aliasing_evidence_matrix.md`, inverter switching ringing between $500\,\text{kHz}$ and $15\,\text{MHz}$ folds into the $[0, 500\,\text{kHz}]$ band. Because no spectral capture exists, the total energy of aliased components cannot be bounded.
- **Source:** Inverter power stage PWM ringing without pre-ADC analog filtering.
- **Correlation Status:** Correlated with inverter switching rate and DC bus voltage.
- **Justification:** Out-of-band energy is unknown.

---

## 3. Why Naive Root-Sum-Square (RSS) is Metrologically Invalid Here

In Milestone CORR-04-R1, a draft uncertainty figure of:
$$U_{\text{draft}} = 0.087\,\text{A}$$
was computed by naively applying the formula:
$$U = 2 \times \sqrt{u_1^2 + u_2^2 + \dots + u_n^2}$$

### Metrological Flaws in that Calculation:
1. **Violates Independence Requirement:** GUM Section 5.1.2 mandates that the RSS formula applies **only** when all input quantities are mutually independent. Here, calibration error, termination error, and vertical scale error act multiplicatively on the same voltage reading ($V = I \cdot R_{\text{term}} \cdot G_{\text{amp}}$). Their correlation coefficient is $\rho = +1.0$.
2. **Missing Sensitivity Coefficients:** GUM Section 5.1.3 requires partial derivative sensitivity coefficients ($c_i = \partial f / \partial x_i$). These were omitted.
3. **Conflation of Time and Amplitude:** Sampling jitter ($\mu\text{s}$) and vertical noise ($\text{mV}$) cannot be summed in quadrature without the time-derivative sensitivity:
   $$c_t = \left| \frac{\partial I}{\partial t} \right| = \frac{I_0}{\tau} e^{-t/\tau}$$
   Near threshold ($I \approx 0.410\,\text{A}$), the decay rate is:
   $$\left| \frac{\partial I}{\partial t} \right| \approx \frac{0.410\,\text{A}}{2.8\,\text{ms}} \approx 0.146\,\text{A/ms}$$
   A timing uncertainty of $1.0\,\text{ms}$ therefore translates directly into $0.146\,\text{A}$ of apparent amplitude uncertainty!

---

## 4. Formal Decision-Rule Framework

In accordance with ASME B89.7.3.1 and ISO 14253-1, an acceptance decision rule requires defining:
- Upper Specification Limit ($T_{\text{max}}$);
- Combined Expanded Uncertainty ($U$);
- Guard Band ($g$);
- Acceptance Zone ($A = [0, T_{\text{max}} - g]$).

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        DECISION-RULE BOUNDARIES                        │
├────────────────────────────────────────────────────────────────────────┤
│  [ACCEPTANCE ZONE]               [GUARD BAND g]   [REJECTION ZONE]     │
│  0 ms ──────────────────────────► T_max - g ─────► T_max               │
│                                   (g = U)                              │
└────────────────────────────────────────────────────────────────────────┘
```

Because four of the six uncertainty domains are `INDETERMINATE` ($u_{\text{meas}}, u_{\text{model}}, u_{\text{time}}, u_{\text{cal}}, u_{\text{alias}}$), the guard band $g$ cannot be computed.

---

## 5. Framework Verdict

```text
UNCERTAINTY_BUDGET_STATUS       = INCOMPLETE
DOMAINS_DETERMINATE             = 1 of 6 (Implementation grid only)
DOMAINS_INDETERMINATE           = 5 of 6 (Measurement, Model, Timing, Cal, Alias)
GUARDED_THRESHOLD_STATUS        = UNGROUNDED_IN_TRACEABLE_METROLOGY
CERTIFIED_DECISION_RULE_STATUS  = BLOCKED
```
