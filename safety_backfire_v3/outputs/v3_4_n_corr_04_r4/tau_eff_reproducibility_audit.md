# V3.4-N-CORR-04-R4 — Effective Time Constant (tau_eff) Reproducibility Audit

**Document:** `outputs/v3_4_n_corr_04_r4/tau_eff_reproducibility_audit.md`  
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
TAU_EFF_STATUS                  = DESCRIPTIVE_UNTRACEABLE_FIT
FINAL_STATUS                    = BLOCKED
```

---

## 1. Forensic Mandate: Demanding Proof of the 2.8 ms Constant

Throughout milestones V3.4-N-CORR-04 through R3, the figure:
$$\tau_{\text{eff}} = 2.8\,\text{ms}$$
has served as the foundational physical decay rate parameter, driving:
1. The analytical flush lag calculation: $\Delta_{\text{flush}} = \tau_{\text{eff}} \cdot \ln(C) \approx 1.117\,\text{ms}$;
2. The continuous RMS decay curve equations;
3. The Region-2 bisection solver;
4. The historical manifest derived columns.

This audit examines whether $\tau_{\text{eff}} = 2.8\,\text{ms}$ is a mathematically reproducible physical measurement or an unsubstantiated historical narrative constant.

**Authoritative Governance Rule:**  
Unless primary regression waveforms, fitting intervals, residuals, and uncertainty bounds exist in the repository, $\tau_{\text{eff}} = 2.8\,\text{ms}$ **SHALL NOT** be treated as an authoritative physical or safety timing constant. Its status must remain `DESCRIPTIVE_UNTRACEABLE_FIT`.

---

## 2. Thirteen-Point Regression Artifact Audit

| # | Required Regression Artifact | Authoritative Definition & Expectation | Repository Finding | Status |
| :-: | :--- | :--- | :--- | :---: |
| **1** | **Source Waveform** | Unprocessed time-series oscillogram ($i(t)$ vs $t$) in machine-readable format (`.csv`, `.h5`). | Zero raw waveform files exist. | `MISSING` |
| **2** | **Fit Interval** | Explicit start time $t_{\text{start}}$ and end time $t_{\text{stop}}$ defining the regression window. | Unrecorded. | `MISSING` |
| **3** | **Pre-Event Baseline** | Measured steady-state current and DC offset prior to E-Stop de-energization. | Unrecorded. | `MISSING` |
| **4** | **Post-Event Interval** | Terminal boundary establishing when current reached noise floor. | Unrecorded. | `MISSING` |
| **5** | **Fit Equation** | Mathematical regression model (e.g. $I_0 e^{-t/\tau}$ vs $I_{\text{offset}} + I_0 e^{-t/\tau}$). | Asserted in text as $I_0 e^{-t/\tau}$; model details unrecorded. | `UNVERIFIED` |
| **6** | **Fitting Method** | Regression algorithm (e.g. non-linear Levenberg-Marquardt vs linear log-transform OLS). | Unrecorded. | `MISSING` |
| **7** | **Weighting Function** | Sample weighting scheme ($w_i = 1$ vs $w_i = 1/\sigma_i^2$). | Unrecorded. | `MISSING` |
| **8** | **Residuals Vector** | Explicit error vector $r_i = y_i - \hat{y}_i$ across the fitting window. | Zero residual vectors exist. | `MISSING` |
| **9** | **Goodness of Fit** | Quantitative metrics: $R^2$, Adjusted $R^2$, Reduced $\chi^2$, or RMSE. | Unrecorded. | `MISSING` |
| **10**| **Independent Captures** | Number of independent trial waveforms used to estimate parameter distribution. | Stated as 10 runs in text; individual fits missing. | `UNVERIFIED` |
| **11**| **Operating Conditions** | Test conditions (rotor speed, stator temperature, bus voltage) corresponding to fit. | Narrative table only; no synchronized logs. | `UNVERIFIED` |
| **12**| **Fit Uncertainty** | Standard error of the fit parameter: $\hat{\tau}_{\text{eff}} \pm u(\hat{\tau}_{\text{eff}})$. | Unrecorded; treated as zero-error scalar. | `MISSING` |
| **13**| **Hardware Configuration** | Controller model, firmware, and motor state during decay recording. | Unverified (see `powertrain_identity_chain.md`). | `MISSING` |

---

## 3. Analysis of Critical Anomalies

### 3.1 The Invariant Time Constant Across Divergent Operating Points
In `evidence_manifest_v3.csv`, ten distinct operating conditions are reported:
- Speeds ranging from $10\,\text{Hz}$ electrical ($15\%$ torque) to $90\,\text{Hz}$ electrical ($100\%$ torque);
- Stator temperatures reported at $22.0^\circ\text{C}$;
- Operating modes spanning forward drive, reverse drive, and field weakening.

In physical rotating machines:
- **Temperature Dependence:** Copper stator resistance $R_s$ increases with temperature ($\approx +0.393\% / ^\circ\text{C}$). A $50^\circ\text{C}$ rise in winding temperature decreases the electrical time constant $L/R$ by approximately $16\%$.
- **Magnetic Saturation:** At $100\%$ rated torque ($\sim 115\,\text{A}$), stator core saturation reduces incremental inductance $L_q$, decreasing $\tau = L/R$ relative to low-current operating points.
- **Rotor Speed & Back-EMF:** As shown in Section 4 of `powertrain_identity_chain.md`, a PMSM spinning at $90\,\text{Hz}$ generates nine times greater back-EMF than at $10\,\text{Hz}$, fundamentally altering freewheeling diode conduction and decay trajectory.

**Forensic Finding:** Despite these large physical variations across the 10 operating points, historical reports applied an identical, constant $\tau_{\text{eff}} = 2.8\,\text{ms}$ across every single run without adjustment or variance. This uniform application indicates that $\tau_{\text{eff}} = 2.8\,\text{ms}$ was used as an *a priori* assumed parameter or rough single-point estimate rather than an empirically fitted variable.

### 3.2 Absence of Fit Equation Specification
Whether the decay was fitted to:
$$\text{Model A: } I(t) = I_0 e^{-t/\tau}$$
or
$$\text{Model B: } I(t) = I_0 e^{-t/\tau} + I_{\text{offset}}$$
fundamentally changes the fitted value of $\tau$. A small baseline DC offset of $50\,\text{mA}$ (well within current probe zero drift) fitted under Model A distorts the estimated $\tau$ by over $30\%$ in the tail region ($< 0.5\,\text{A}$). Because the fit equation and baseline subtraction method are undocumented, the numerical value $2.8\,\text{ms}$ cannot be verified.

---

## 4. Metrological Verdict & Operational Boundary

```text
TAU_EFF_VALUE               = 2.8 ms (ILLUSTRATIVE_PARAMETER_ONLY)
TAU_EFF_STATUS              = DESCRIPTIVE_UNTRACEABLE_FIT
REGRESSION_REPRODUCIBILITY  = ZERO
EMPIRICAL_UNCERTAINTY       = INDETERMINATE
SAFETY_TIMING_APPLICATION   = STRICTLY_PROHIBITED
```

$\tau_{\text{eff}} = 2.8\,\text{ms}$ **SHALL NOT** be utilized as an authoritative safety cutoff constant, contactor timing limit, or proof of vehicle de-energization latency. It remains purely an illustrative coefficient within synthetic reference models.
