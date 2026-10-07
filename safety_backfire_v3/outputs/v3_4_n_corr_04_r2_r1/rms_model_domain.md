# V3.4-N-CORR-04-R2-R1 — Signal Model Domain & Decay Parameter Governance

**Document Identifier:** `outputs/v3_4_n_corr_04_r2_r1/rms_model_domain.md`  
**Milestone:** `V3.4-N-CORR-04-R2-R1`  
**Classification:** Metrological Signal Definition & Phenomenological Decay Audit  
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

## 1. Executive Summary & Purpose

Earlier reports (V3.4-N-CORR-04 through R2) cited the decay model:
$$i(t) = I_0 \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right)$$
without explicitly stating the mathematical domain of the signal $i(t)$. In various sections, $i(t)$ was described alternately as "instantaneous phase current," "motor current amplitude," or "pre-shutdown RMS current."

Furthermore, $\tau_{\text{eff}} = 2.8\,\text{ms}$ was repeatedly cited as if it were an intrinsic physical constant of the vehicle safety system.

Per Section 5 and Section 6 of the V3.4-N-CORR-04-R2-R1 mandate, this document:
1. Conducts a forensic metrological audit of the signal definition $i(t)$.
2. Formally establishes the exact domain and limitations of the mathematical model.
3. Classifies $\tau_{\text{eff}} = 2.8\,\text{ms}$ as an empirical curve fit and prohibits unevidenced generalization across vehicle operating regimes.

---

## 2. Metrological Audit of the Signal Definition $i(t)$

We evaluate the three competing interpretations of $i(t)$:

### Option A: Instantaneous Stator Phase AC Current
If $i(t)$ represented the true instantaneous physical phase current of an AC permanent magnet synchronous motor, it would possess an alternating sinusoidal carrier at stator electrical frequency $\omega_e = 2\pi f_e$:
$$i_{\text{AC}}(t) = \sqrt{2} I_0 \cos(\omega_e t + \phi) \cdot \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right) \quad \text{for } t \ge t_0$$
Squaring this instantaneous signal yields:
$$i_{\text{AC}}^2(t) = 2 I_0^2 \cos^2(\omega_e t + \phi) e^{-\frac{2(t - t_0)}{\tau_{\text{eff}}}} = I_0^2 \big[ 1 + \cos(2\omega_e t + 2\phi) \big] e^{-\frac{2(t - t_0)}{\tau_{\text{eff}}}}$$
Integrating over a finite moving window $T_w$:
$$I_{\text{RMS}}^2(t) = \frac{1}{T_w} \int_{t - T_w}^{t} i_{\text{AC}}^2(\tau) \, d\tau$$
This integral generates non-zero sinusoidal double-frequency terms $\int \cos(2\omega_e \tau + 2\phi) d\tau$ that depend strongly on the electrical phase angle $\phi$ at the moment of trigger ($t_0$) and on the ratio of $T_w$ to the AC period $T_e = 1/f_e$.

**Audit Finding on Option A:**  
Because the derivation in [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md) integrates $\int I_0^2 e^{-2\tau/\tau} d\tau$ without sinusoidal cross-terms or initial phase dependence $\phi$, **the model does NOT describe instantaneous AC phase current**.

---

### Option B: Instantaneous DC Envelope (Unmodulated)
If $i(t)$ represents the instantaneous unmodulated DC current in a DC motor or chopper circuit, then $i(t) = I_0 e^{-(t-t_0)/\tau}$ directly. While mathematically consistent with the integral, `AGV-RES-TRUCK-01` has a 3-phase AC PMSM motor, not a DC commutator motor.

---

### Option C: Cycle-Averaged Exponential Envelope / RMS-Equivalent Signal
If $i(t)$ represents the continuous-time **envelope** of the 3-phase AC stator current vector (i.e. magnitude of the Park $d-q$ current vector $\|i_{dq}\|$, or the instantaneous amplitude envelope where the sinusoidal carrier is treated as fast relative to the window or pre-demodulated), then:
$$\big\langle i^2(\tau) \big\rangle_{\text{carrier}} = I_{\text{env}}^2(\tau) = I_0^2 \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right)$$
Under this formulation, the mathematical integral in [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md) is exact.

---

## 3. Formal Declaration of Model Domain

Per Section 5 of the mandate:

$$\mathbf{MODEL\_DOMAIN = EXPONENTIAL\;ENVELOPE\;/\;RMS-EQUIVALENT\;SIGNAL}$$

### Mandatory Usage Constraints:
1. **Interpretation Restriction:** The closed-form RMS equations in this milestone suite describe the filtering of an exponential current envelope or RMS-equivalent amplitude signal.
2. **Instantaneous AC Waveforms Prohibited:** This model must **NOT** be interpreted as a universal closed-form solution for an instantaneous sinusoidal phase current trace unless a carrier modulation term and initial phase parameter $\phi_0$ are explicitly incorporated into the integral.
3. **Model Invariance:** No new physical model is added to production software.

---

## 4. Metrological Governance of $\tau_{\text{eff}} = 2.8\,\text{ms}$

In prior milestones, $\tau_{\text{eff}} \approx 2.8\,\text{ms}$ was repeatedly cited as the de facto standard decay constant of the vehicle platform.

### 4.1 Metrological Classification
Per Section 6 of the mandate, the parameter $\tau_{\text{eff}} = 2.8\,\text{ms}$ is formally classified as:

$$\mathbf{\tau_{\text{eff}} = EMPIRICAL\_SINGLE\_EXPONENTIAL\_FIT}$$

It is an empirical curve-fit parameter derived from a limited set of bench oscilloscope captures on a single dyno setup. It is **NOT**:
- An intrinsic electromagnetic property of the motor (which is $L_s / R_s = 4.94\,\text{ms}$).
- A universal vehicle decay constant.
- A functional safety guaranteed hardware parameter.

---

### 4.2 Multi-Factor Physical Dependencies of Current Decay
The physical rate of current collapse during inverter Safe Torque Off (STO) depends on eight interacting physical and operating variables:

| Variable | Physical Mechanism | Effect on Effective Decay Rate |
| :--- | :--- | :--- |
| **1. Motor Inductance & Resistance** | Stator winding $L_s, R_s$ | Lower $L/R$ speeds up unforced decay; saturation at high currents reduces effective $L_s$. |
| **2. Inverter Power Stage** | IGBT freewheeling diode $V_f$ and snubber network | Higher forward drop $V_f$ increases counter-EMF, accelerating initial current collapse. |
| **3. Pre-Trip Current Amplitude ($I_0$)** | Initial magnetic energy $E_m = \frac{1}{2} L I_0^2$ | High currents saturate stator iron, making initial decay non-exponential. |
| **4. Motor Speed & Back-EMF ($\omega_e$)** | Spinning permanent magnets induce back-EMF $E = k_e \omega_e$ | High rotor speed opposes diode decay or drives continuous rectification into DC link. |
| **5. DC Link Capacitor Voltage ($V_{\text{bus}}$)** | Diode clamping counter-voltage $(V_{\text{bus}} + 2V_f)$ | Higher bus voltage increases opposing voltage, shortening linear collapse phase. |
| **6. Inverter Controller & Firmware** | Gate driver active pull-down timing ($t_{\text{STO}}$) | Slower gate discharge prolongs active conduction before freewheeling begins. |
| **7. Operating Temperature** | Diode $V_f$ and copper resistance $R_s(T)$ | Elevated temperature increases copper resistance ($+0.393\%/^\circ\text{C}$), speeding decay. |
| **8. Current Measurement Chain** | Probe bandwidth and amplifier roll-off | Insufficient bandwidth artificially rounds edges, distorting exponential curve fits. |

---

### 4.3 Governance Ruling: Generalization Prohibited

Because the documentation in the repository does not establish or validate the functional dependence of $\tau_{\text{eff}}$ across variations in vehicle speed, pre-trip torque, bus voltage, and temperature:

$$\mathbf{TAU\_EFF\_GENERALIZATION = PROHIBITED}$$

**Rules of Application:**
1. The figure $\tau_{\text{eff}} = 2.8\,\text{ms}$ may be used **only** as a nominal descriptive benchmark for evaluating algorithm behavior under the historical bench trial conditions.
2. It must **never** be cited as proof that all vehicle E-Stop events will collapse with $\tau \le 2.8\,\text{ms}$.
3. Safety timing margins must be derived from bounded worst-case empirical envelopes, not from an unvalidated single-exponential fit.
