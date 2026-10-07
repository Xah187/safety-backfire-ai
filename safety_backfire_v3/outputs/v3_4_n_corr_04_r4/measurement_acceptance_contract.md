# V3.4-N-CORR-04-R4 — Non-Circular Measurement Acceptance Contract

**Document:** `outputs/v3_4_n_corr_04_r4/measurement_acceptance_contract.md`  
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
CIRCULAR_ACCEPTANCE_CRITERIA    = STRICTLY_EXPUNGED
FINAL_STATUS                    = BLOCKED
```

---

## 1. Expunging Circular Acceptance Language

In earlier milestones (specifically CORR-04-R2 and early draft revisions of `BLK_PERSIST_04`), acceptance protocols contained circular clauses requiring future experimental captures to *"confirm $\Delta_{\text{flush}} \approx 1.12\,\text{ms}$"* or *"validate that physical decay matches the analytical model of 1.117 ms"*.

**Epistemic Correction:**
- Requiring an experimental observation to match an analytical prediction as a condition of acceptance is the definition of **circular reasoning**. It biases measurement protocols toward confirmation rather than objective falsification.
- If physical rotating-machine trials exhibit an offset of $0.85\,\text{ms}$, $1.45\,\text{ms}$, or non-monotonic oscillation due to synchronous back-EMF, that discrepancy is vital empirical truth. Forcing experimental results to rubber-stamp $1.117\,\text{ms}$ would hide dangerous physical realities.
- All language requiring future captures to "confirm", "prove", or "match" prior theoretical constants has been **completely expunged**.

---

## 2. The Seven-Parameter Non-Circular Evaluation Protocol

Any future characterization analysis authorized by a separate, governed commissioning body **SHALL** evaluate de-energization timing strictly according to the following seven-parameter protocol. 

The protocol **does not predefine success** and explicitly allows observed physical data to disagree with analytical models.

```text
┌────────────────────────────────────────────────────────────────────────┐
│               NON-CIRCULAR METROLOGICAL EVALUATION PROTOCOL            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
[RAW PHYSICAL OBSERVATION]                              [ALGORITHMIC RMS OUTPUT]
1. OBSERVED_PHYSICAL_CROSSING                           2. OBSERVED_RMS_CROSSING
   (t_phys_obs from raw calibrated trace)                  (t_rms_obs from frozen code)
    │                                                               │
    └───────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
                         3. OBSERVED_OFFSET
                            (Delta_obs = t_rms_obs - t_phys_obs)
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
     4. MODEL_PREDICTION                       6. MEASUREMENT_UNCERTAINTY
        (Delta_pred from analytical               (u_Delta from certified
         bisection / asymptotic model)             traceable uncertainty budget)
               │                                         │
               └────────────────────┬────────────────────┘
                                    │
                                    ▼
                              5. DIFFERENCE
                                 (epsilon = Delta_obs - Delta_pred)
                                    │
                                    ▼
                        7. EXPLANATION_OF_DEVIATION
                           (Physical, metrological, and model domain analysis)
```

### Parameter 1: `OBSERVED_PHYSICAL_CROSSING` ($t_{\text{phys}}^{\text{obs}}$)
- **Definition:** The physical timestamp at which the calibrated stator current envelope or instantaneous magnitude physically crosses below the guarded threshold ($0.410\,\text{A}$).
- **Contract:** Must be determined directly from the calibrated, anti-alias-filtered raw waveform using a certified threshold detection algorithm. It **SHALL NOT** be computed by subtracting an analytical constant from the RMS crossing.

### Parameter 2: `OBSERVED_RMS_CROSSING` ($t_{\text{RMS}}^{\text{obs}}$)
- **Definition:** The timestamp of the first discrete RMS frame satisfying $I_{\text{RMS}}[k_p] \le 0.410\,\text{A RMS}$.
- **Contract:** Must be evaluated strictly by the frozen, hashed discrete RMS execution engine running over the raw sample stream, adhering to the index contract ($N=2000, M=100$, right-edge timestamp).

### Parameter 3: `OBSERVED_OFFSET` ($\Delta^{\text{obs}}$)
- **Definition:** The actual temporal lag between physical threshold crossing and digital RMS qualification:
  $$\Delta^{\text{obs}} = t_{\text{RMS}}^{\text{obs}} - t_{\text{phys}}^{\text{obs}}$$

### Parameter 4: `MODEL_PREDICTION` ($\Delta^{\text{pred}}$)
- **Definition:** The theoretical latency predicted by the continuous analytical model for the exact operating conditions (initial current $I_0$, fitted physical $\tau$, and discrete grid phase $\phi$):
  - In Region 3 ($I_0 \ge 0.562\,\text{A}$): $\Delta^{\text{pred}} = \tau \cdot \ln(C) \approx 1.117\,\text{ms}$ (asymptotic limit).
  - In Region 2 ($0.410 < I_0 < 0.562\,\text{A}$): $\Delta^{\text{pred}}$ evaluated via the continuous root-solving bisection integral.

### Parameter 5: `DIFFERENCE` ($\epsilon$)
- **Definition:** The quantitative divergence between observation and prediction:
  $$\epsilon = \Delta^{\text{obs}} - \Delta^{\text{pred}}$$

### Parameter 6: `UNCERTAINTY` ($U_{\Delta}$)
- **Definition:** The combined expanded uncertainty ($k=2$, $95\%$ confidence) associated with the observed offset, incorporating timebase jitter, trigger latency, vertical ADC quantization noise, and probe phase delay:
  $$U_{\Delta} = 2 \cdot u_c(\Delta^{\text{obs}})$$
- If the uncertainty budget is incomplete, this field **SHALL** be explicitly recorded as `UNCERTAINTY_UNKNOWN`.

### Parameter 7: `EXPLANATION_OF_DEVIATION`
- **Definition:** An authoritative engineering report reconciling the observed difference $\epsilon$:
  - Is $|\epsilon| \le U_{\Delta}$ (divergence fully explained by measurement uncertainty)?
  - If $|\epsilon| > U_{\Delta}$, identify the physical or mathematical root cause:
    1. Inverter freewheeling diode non-linear forward voltage drop ($V_f$);
    2. Motor magnetic saturation altering stator inductance $L(i)$;
    3. Permanent magnet rotor rotation generating back-EMF;
    4. Analog or digital filter group delay;
    5. Discretization fencepost and grid phase effects.

---

## 3. Epistemic Governance Rules

1. **Disagreement is Acceptable:** A capture in which $\epsilon \ne 0$ is a valid, auditable scientific finding. It **SHALL NOT** be discarded, hidden, or branded an execution failure merely because it departs from Model H or analytical predictions.
2. **No Automated Threshold Adjustment:** Observed deviations **SHALL NOT** be used to tune Model H parameters ($k_0, \beta_d, \beta_l, \beta_{\text{pitch}}$) or production scripts.
3. **No Inferred Success:** A trial report does not achieve "success" or "validation"; it provides calibrated measurement evidence with defined uncertainty.

---

## 4. Physical Testing Non-Authorization Notice

This document establishes the metrological contract for future evidence evaluation. 

```text
PHYSICAL_CAPTURE_AUTHORIZATION    = NOT_GRANTED
RESEARCH_DAQ_ACTUATION_AUTHORITY  = ZERO
```

Nothing in this contract grants authority to energize traction inverters, execute vehicle maneuvers, or collect physical laboratory data.
