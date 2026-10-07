# V3.4-N-CORR-04-R2-R1 — Analytical Derivation of RMS Region Boundary

**Document Identifier:** `outputs/v3_4_n_corr_04_r2_r1/rms_region_boundary.md`  
**Milestone:** `V3.4-N-CORR-04-R2-R1`  
**Classification:** Exact Metrology & Filter Dynamic Boundary Mathematics  
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

In Milestone V3.4-N-CORR-04-R2 (`rms_decay_model.md`), a numerical example was presented for a low pre-trip current ($I_0 = 0.80\,\text{A}$) and erroneously classified as crossing the guarded RMS threshold in Region 2. Furthermore, R2 utilized an arbitrary rule-of-thumb statement ($I_0 > 1.0\,\text{A}$) to describe Region-3 crossing applicability.

This document:
1. Derives the **exact symbolic boundary condition** separating Region-2 threshold crossing from Region-3 threshold crossing as a function of $I_0, I_{\text{guarded}}, T_w,$ and $\tau_{\text{eff}}$.
2. Calculates the exact numerical threshold boundary under the frozen pipeline parameters.
3. Provides an independent, step-by-step verification of the $I_0 = 0.80\,\text{A}$ case, proving that it crosses the RMS threshold firmly in **Region 3**, not Region 2.

---

## 2. Symbolic Derivation of the Region Boundary

Consider the causal exponential envelope decay model initiated at $t_0$:

$$i(t) = \begin{cases} I_0, & t < t_0 \\ I_0 \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right), & t \ge t_0 \end{cases}$$

The causal moving RMS signal $I_{\text{RMS}}(t)$ over rectangular window $T_w$ is defined by:
$$I_{\text{RMS}}^2(t) = \frac{1}{T_w} \int_{t - T_w}^{t} i^2(\tau) \, d\tau$$

### 2.1 The Transition Boundary Instant ($t = t_0 + T_w$)
The physical time interval splits into three piecewise regions:
- **Region 1 (Pre-Event):** $t < t_0 \implies I_{\text{RMS}}(t) = I_0$
- **Region 2 (Window Overlap):** $t_0 \le t < t_0 + T_w$
- **Region 3 (Window Post-Event):** $t \ge t_0 + T_w$

The boundary between Region 2 and Region 3 occurs at the exact time instant:
$$t_{\text{boundary}} = t_0 + T_w$$
At this exact instant, the leading edge of the moving window has advanced by $T_w$ after the event onset, meaning the trailing edge is precisely at $t_0$.

Evaluating $I_{\text{RMS}}^2(t)$ at $t = t_0 + T_w$ from either Region 2 or Region 3 yields:
$$I_{\text{RMS}}^2(t_0 + T_w) = \frac{1}{T_w} \int_{t_0}^{t_0 + T_w} I_0^2 \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right) \, d\tau$$

Performing the integration:
$$I_{\text{RMS}}^2(t_0 + T_w) = \frac{I_0^2}{T_w} \left[ -\frac{\tau_{\text{eff}}}{2} \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right) \right]_{t_0}^{t_0 + T_w} = I_0^2 \frac{\tau_{\text{eff}}}{2 T_w} \left( 1 - \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right) \right)$$

Taking the square root:
$$\mathbf{I_{\text{RMS}}(t_0 + T_w) = I_0 \cdot B(T_w, \tau_{\text{eff}})}$$

where the dimensionless boundary attenuation factor $B(T_w, \tau_{\text{eff}})$ is defined symbolically by:

$$\mathbf{B(T_w, \tau_{\text{eff}}) = \sqrt{ \frac{\tau_{\text{eff}}}{2 T_w} \left( 1 - \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right) \right) }}$$

*(Note the relationship to the Region-3 amplification factor $C$: $B(T_w, \tau_{\text{eff}}) = C(T_w, \tau_{\text{eff}}) \cdot \exp\left(-\frac{T_w}{\tau_{\text{eff}}}\right)$).*

---

### 2.2 Threshold-Crossing Region Classification Criterion

Because $I_{\text{RMS}}(t)$ is strictly monotonically decreasing for all $t > t_0$:

1. **Crossing in Region 3:**
   If at the boundary $t = t_0 + T_w$ the RMS current is still strictly above the guarded threshold:
   $$I_{\text{RMS}}(t_0 + T_w) > I_{\text{guarded}} \iff I_0 \cdot B(T_w, \tau_{\text{eff}}) > I_{\text{guarded}}$$
   then the threshold $I_{\text{guarded}}$ cannot be reached during Region 2. It must be reached at some time $t > t_0 + T_w$.
   $$\mathbf{I_0 > \frac{I_{\text{guarded}}}{B(T_w, \tau_{\text{eff}})} \implies \text{Threshold Crossing Occurs in REGION 3}}$$

2. **Crossing in Region 2:**
   If at the boundary $t = t_0 + T_w$ the RMS current has already fallen below the guarded threshold:
   $$I_{\text{RMS}}(t_0 + T_w) < I_{\text{guarded}} \iff I_0 \cdot B(T_w, \tau_{\text{eff}}) < I_{\text{guarded}}$$
   then the threshold was already crossed prior to $t_0 + T_w$.
   $$\mathbf{I_0 < \frac{I_{\text{guarded}}}{B(T_w, \tau_{\text{eff}})} \implies \text{Threshold Crossing Occurs in REGION 2}}$$

3. **Exact Boundary Crossing:**
   $$\mathbf{I_0 = I_{0,\text{crit}} \equiv \frac{I_{\text{guarded}}}{B(T_w, \tau_{\text{eff}})} \implies t_{\text{rms\_threshold\_cross}} = t_0 + T_w}$$

---

## 3. Numerical Evaluation for Frozen Baseline

Frozen parameters:
- Window duration: $T_w = 2.0\,\text{ms} = 0.0020\,\text{s}$
- Effective decay constant: $\tau_{\text{eff}} = 2.8\,\text{ms} = 0.0028\,\text{s}$
- Dimensionless ratio: $\frac{2 T_w}{\tau_{\text{eff}}} = \frac{4.0}{2.8} = \frac{10}{7} \approx 1.4285714$
- Exponential term: $\exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right) = \exp(-1.4285714) \approx 0.2396510$
- Bracket term: $1 - \exp(-1.4285714) \approx 1 - 0.2396510 = 0.7603490$
- Pre-factor: $\frac{\tau_{\text{eff}}}{2 T_w} = \frac{2.8}{4.0} = 0.7000000$
- Squared boundary factor:
  $$B^2 = 0.7000000 \times 0.7603490 = 0.5322443$$
- Boundary attenuation factor:
  $$\mathbf{B(2.0\,\text{ms}, 2.8\,\text{ms}) = \sqrt{0.5322443} \approx 0.7295507 \approx 0.7296}$$

### 3.1 Exact Critical Current $I_{0,\text{crit}}$

Depending on the guarded threshold value applied:

1. **For $I_{\text{guarded}} = 0.410\,\text{A RMS}$ (Reconciled Historical Target):**
   $$I_{0,\text{crit}} = \frac{0.410\,\text{A}}{0.7295507} \approx \mathbf{0.56199\,A \approx 0.562\,A}$$

2. **For $I_{\text{guarded}} = 0.460\,\text{A RMS}$ (Model 5 A/V Calibrated Target):**
   $$I_{0,\text{crit}} = \frac{0.460\,\text{A}}{0.7295507} \approx \mathbf{0.63053\,A \approx 0.631\,A}$$

3. **For $I_{\text{guarded}} = 0.500\,\text{A RMS}$ (Nominal Un-guarded Threshold):**
   $$I_{0,\text{crit}} = \frac{0.500\,\text{A}}{0.7295507} \approx \mathbf{0.68535\,A \approx 0.685\,A}$$

**Analytical Conclusion:**  
An arbitrary heuristic boundary such as "$I_0 > 1.0\,\text{A}$" is mathematically imprecise. The exact mathematical boundary condition for Region-3 crossing under $I_{\text{guarded}} = 0.410\,\text{A}$ is:
$$\mathbf{I_0 > 0.562\,A}$$

---

## 4. Independent Verification & Correction of the 0.80 A Case

We perform an independent, non-circular re-evaluation of the specific test case:
- $I_0 = 0.80\,\text{A}$
- $I_{\text{guarded}} = 0.410\,\text{A}$
- $\tau_{\text{eff}} = 2.8\,\text{ms}$
- $T_w = 2.0\,\text{ms}$
- $t_0 = 13.0\,\text{ms}$

### 4.1 Step 1: Physical Envelope Crossing Time ($t_{\text{phys}}$)
$$i(t_{\text{phys}}) = I_0 \exp\left(-\frac{t_{\text{phys}} - t_0}{\tau_{\text{eff}}}\right) = I_{\text{guarded}}$$
$$\exp\left(-\frac{t_{\text{phys}} - t_0}{\tau_{\text{eff}}}\right) = \frac{0.410}{0.80} = 0.5125$$
$$\frac{t_{\text{phys}} - t_0}{\tau_{\text{eff}}} = -\ln(0.5125) \approx 0.6684293$$
$$t_{\text{phys}} = t_0 + \tau_{\text{eff}} \times 0.6684293 = 13.0\,\text{ms} + 2.8 \times 0.6684293\,\text{ms} = 13.0\,\text{ms} + 1.8716\,\text{ms}$$
$$\mathbf{t_{\text{phys\_envelope\_cross}} \approx 14.8716\,ms \approx 14.87\,ms}$$

---

### 4.2 Step 2: Value of $I_{\text{RMS}}$ at the Region Boundary ($t = t_0 + T_w = 15.0\,\text{ms}$)
$$I_{\text{RMS}}(15.0\,\text{ms}) = I_0 \cdot B = 0.80\,\text{A} \times 0.7295507 \approx \mathbf{0.58364\,A \approx 0.584\,A}$$

### Comparison:
$$I_{\text{RMS}}(15.0\,\text{ms}) = 0.584\,\text{A} \quad \mathbf{>} \quad I_{\text{guarded}} = 0.410\,\text{A}$$
Because $0.584\,\text{A} > 0.410\,\text{A}$, the moving RMS value at the end of Region 2 is still significantly above the threshold. Therefore, the threshold crossing **CANNOT** occur in Region 2. It **MUST** occur in Region 3 ($t > 15.0\,\text{ms}$).

---

### 4.3 Step 3: Exact Calculation of $t_{\text{RMS}}$ in Region 3
In Region 3 ($t \ge 15.0\,\text{ms}$):
$$I_{\text{RMS}}(t) = I_0 \cdot C(T_w, \tau_{\text{eff}}) \cdot \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right) = I_{\text{guarded}}$$
From [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md):
$$C = \sqrt{\frac{2.8}{4.0} (\exp(1.4285714) - 1)} \approx 1.490272$$
$$I_0 \cdot C = 0.80\,\text{A} \times 1.490272 \approx 1.1922176\,\text{A}$$
Setting equal to $I_{\text{guarded}} = 0.410\,\text{A}$:
$$\exp\left(-\frac{t_{\text{rms}} - t_0}{\tau_{\text{eff}}}\right) = \frac{0.410}{1.1922176} \approx 0.3438969$$
$$\frac{t_{\text{rms}} - t_0}{\tau_{\text{eff}}} = -\ln(0.3438969) \approx 1.0674121$$
$$t_{\text{rms}} - t_0 = 2.8\,\text{ms} \times 1.0674121 \approx 2.98875\,\text{ms}$$
$$t_{\text{rms\_threshold\_cross}} = 13.0\,\text{ms} + 2.98875\,\text{ms} \approx \mathbf{15.9888\,ms \approx 15.99\,ms}$$

---

### 4.4 Step 4: Verification of Flush Lag $\Delta_{\text{flush}}$
$$\Delta_{\text{flush}} = t_{\text{rms\_threshold\_cross}} - t_{\text{phys\_envelope\_cross}} = 15.9888\,\text{ms} - 14.8716\,\text{ms} = \mathbf{1.1172\,ms \approx 1.12\,ms}$$

This matches the analytical expression:
$$\Delta_{\text{flush}} = \tau_{\text{eff}} \ln C = 2.8 \times \ln(1.490272) = 2.8 \times 0.398958 = \mathbf{1.1171\,ms}$$

---

## 5. Audit Correction Disposition

| Metric | Erroneous R2 Statement | Corrected R2-R1 Audit Baseline | Audit Verdict |
| :--- | :---: | :---: | :---: |
| **Crossing Region for $I_0 = 0.80\,\text{A}$** | Region 2 ($t < 15.0\,\text{ms}$) | **Region 3 ($t > 15.0\,\text{ms}$)** | **ERROR CORRECTED** |
| **Physical Crossing $t_{\text{phys}}$** | $14.87\,\text{ms}$ | $14.87\,\text{ms}$ | Verified |
| **Boundary Value $I_{\text{RMS}}(15.0\,\text{ms})$** | Not evaluated in R2 | **$0.584\,\text{A} > 0.410\,\text{A}$** | Verified |
| **RMS Crossing $t_{\text{rms}}$** | $15.62\,\text{ms}$ (unsupported) | **$15.99\,\text{ms}$** | **CORRECTED** |
| **Flush Lag $\Delta_{\text{flush}}$** | $0.75\,\text{ms}$ (erroneous) | **$1.12\,\text{ms}$** | **CORRECTED** |

**Formal Classification:**
$$\mathbf{RMS\_CROSSING\_REGION(I_0 = 0.80\,A) = REGION\_3}$$
The erroneous statement in Milestone R2 is formally retracted and superseded by this document.
