# V3.4-N-CORR-04-R2-R1 — Reconciliation of Moving RMS Threshold Crossing & Flush Offset

**Document Identifier:** `outputs/v3_4_n_corr_04_r2_r1/rms_crossing_reconciliation.md`  
**Milestone:** `V3.4-N-CORR-04-R2-R1`  
**Classification:** Analytical Signal Processing & Crossing Offset Restriction  
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

In Milestone V3.4-N-CORR-04-R2, the timing delay between instantaneous physical current envelope crossing and moving RMS threshold crossing was derived as:
$$\Delta_{\text{flush}} = \tau_{\text{eff}} \ln C(T_w, \tau_{\text{eff}}) \approx 1.117\,\text{ms}$$
and described in generalized language as an "exact analytical delay."

Per Section 4 of the V3.4-N-CORR-04-R2-R1 mandate:
1. **Scope Restriction:** The constant delay $\Delta_{\text{flush}} \approx 1.117\,\text{ms}$ is formally restricted to **Region 3 only**.
2. **Nomenclature Correction:** The term "exact analytical delay" is replaced by:
   $$\mathbf{\Delta_{\text{flush}} \approx 1.117\,ms \equiv \text{Exact Region-3 Analytical Threshold-Crossing Offset}}$$
3. **Region 2 Direct Solution:** For Region 2 crossings ($I_0 < I_{0,\text{crit}} \approx 0.562\,\text{A}$ at $0.410\,\text{A}$ threshold), the threshold equation must be solved directly, proving that $\Delta_{\text{flush}}$ is non-constant and strictly less than $\tau_{\text{eff}} \ln C$.

---

## 2. Mathematical Proof of Region-3 Specificity

As established in [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md), for all $t \ge t_0 + T_w$ (Region 3), the moving RMS current satisfies:
$$I_{\text{RMS}}(t) = I_0 \cdot C(T_w, \tau_{\text{eff}}) \cdot \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right)$$
where $C(T_w, \tau_{\text{eff}}) = \sqrt{ \frac{\tau_{\text{eff}}}{2 T_w} \left( \exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1 \right) }$.

The threshold crossing $I_{\text{RMS}}(t_{\text{rms}}) = I_{\text{guarded}}$ in Region 3 yields:
$$t_{\text{rms\_threshold\_cross}} = t_0 + \tau_{\text{eff}} \ln\left( \frac{I_0 \cdot C}{I_{\text{guarded}}} \right) = t_0 + \tau_{\text{eff}} \ln\left(\frac{I_0}{I_{\text{guarded}}}\right) + \tau_{\text{eff}} \ln C$$

Because physical envelope crossing is $t_{\text{phys\_envelope\_cross}} = t_0 + \tau_{\text{eff}} \ln\left(\frac{I_0}{I_{\text{guarded}}}\right)$, the difference is:
$$\mathbf{\Delta_{\text{flush, Region\_3}} = t_{\text{rms\_threshold\_cross}} - t_{\text{phys\_envelope\_cross}} = \tau_{\text{eff}} \ln C(T_w, \tau_{\text{eff}})}$$

### Critical Mathematical Properties:
1. In Region 3, $\Delta_{\text{flush}}$ is **strictly constant**: it depends only on the filter window length $T_w$ and the decay constant $\tau_{\text{eff}}$. It is completely invariant to pre-trip operating current $I_0$ and guarded threshold $I_{\text{guarded}}$.
2. For $T_w = 2.0\,\text{ms}$ and $\tau_{\text{eff}} = 2.8\,\text{ms}$, this offset is exactly:
   $$\Delta_{\text{flush, Region\_3}} = 2.8 \times \ln(1.490272) = \mathbf{1.1171\,ms \approx 1.12\,ms}$$

---

## 3. Direct Solution for Region-2 Threshold Crossings

When initial pre-trip current $I_0$ is below the critical boundary derived in [rms_region_boundary.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2_r1/rms_region_boundary.md):
$$I_0 < I_{0,\text{crit}} \equiv \frac{I_{\text{guarded}}}{B(T_w, \tau_{\text{eff}})} \approx \frac{0.410\,\text{A}}{0.72955} \approx 0.562\,\text{A}$$
the moving RMS threshold crossing occurs within the transition interval $t_0 \le t < t_0 + T_w$ (Region 2).

### 3.1 The Region-2 Governing Equation
In Region 2, the moving window still contains a pre-event segment of duration $T_w - (t - t_0)$ at current $I_0$. Setting $I_{\text{RMS}}^2(t) = I_{\text{guarded}}^2$:

$$I_0^2 \left[ 1 - \frac{t - t_0}{T_w} + \frac{\tau_{\text{eff}}}{2 T_w} \left( 1 - \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right) \right) \right] = I_{\text{guarded}}^2$$

Dividing by $I_0^2$ and defining the normalized elapsed time $x \equiv \frac{t - t_0}{T_w} \in [0, 1)$:

$$\mathbf{g(x) \equiv 1 - x + \frac{\tau_{\text{eff}}}{2 T_w} \left( 1 - \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}} x\right) \right) = \left( \frac{I_{\text{guarded}}}{I_0} \right)^2}$$

This is a transcendental equation in $x$. It **cannot** be reduced to the simple logarithmic offset $\tau_{\text{eff}} \ln C$.

---

### 3.2 Numerical Evaluation of a True Region-2 Case ($I_0 = 0.500\,\text{A}$)
Consider an operating state where the motor was idling at low current prior to E-Stop:
- $I_0 = 0.500\,\text{A}$ ($I_0 < 0.562\,\text{A} \implies \text{Region 2 crossing}$)
- $I_{\text{guarded}} = 0.410\,\text{A}$
- $t_0 = 13.0\,\text{ms}$, $\tau_{\text{eff}} = 2.8\,\text{ms}$, $T_w = 2.0\,\text{ms}$

1. **Physical Envelope Crossing:**
   $$t_{\text{phys}} = t_0 + \tau_{\text{eff}} \ln\left(\frac{I_0}{I_{\text{guarded}}}\right) = 13.0 + 2.8 \ln\left(\frac{0.500}{0.410}\right) = 13.0 + 2.8 \times 0.19845 = \mathbf{13.556\,ms}$$
   *(Elapsed physical decay time: $0.556\,\text{ms}$)*

2. **RMS Boundary Check at $t_0 + T_w = 15.0\,\text{ms}$:**
   $$I_{\text{RMS}}(15.0\,\text{ms}) = 0.500\,\text{A} \times 0.72955 = \mathbf{0.3648\,A} < 0.410\,\text{A}$$
   *(Confirms threshold crossing occurred prior to $15.0\,\text{ms}$, i.e., inside Region 2)*

3. **Direct Numerical Root-Finding for $g(x) = (0.410 / 0.500)^2 = (0.820)^2 = 0.6724$:**
   - Parameter: $\frac{2 T_w}{\tau_{\text{eff}}} = \frac{4.0}{2.8} \approx 1.42857$; $\frac{\tau_{\text{eff}}}{2 T_w} = 0.70$.
   - At $x = 0.80$ ($t = 14.60\,\text{ms}$):
     $$g(0.80) = 1 - 0.80 + 0.70 \big[ 1 - \exp(-1.42857 \times 0.80) \big] = 0.20 + 0.70 [1 - \exp(-1.14286)] = 0.20 + 0.70 [1 - 0.31891] = 0.20 + 0.47676 = 0.67676$$
   - At $x = 0.81$ ($t = 14.62\,\text{ms}$):
     $$g(0.81) = 1 - 0.81 + 0.70 \big[ 1 - \exp(-1.42857 \times 0.81) \big] = 0.19 + 0.70 [1 - 0.31438] = 0.19 + 0.47993 = 0.66993$$
   - Linear interpolation for $g(x) = 0.67240$:
     $$x^* = 0.80 + (0.81 - 0.80) \times \frac{0.67676 - 0.67240}{0.67676 - 0.66993} = 0.80 + 0.01 \times \frac{0.00436}{0.00683} \approx 0.8064$$
   - RMS crossing time:
     $$t_{\text{rms\_threshold\_cross}} = t_0 + x^* T_w = 13.0\,\text{ms} + 0.8064 \times 2.0\,\text{ms} = 13.0\,\text{ms} + 1.613\,\text{ms} = \mathbf{14.613\,ms}$$

4. **Actual Flush Lag in Region 2:**
   $$\mathbf{\Delta_{\text{flush, Region\_2}} = t_{\text{rms\_threshold\_cross}} - t_{\text{phys\_envelope\_cross}} = 14.613\,ms - 13.556\,ms = 1.057\,ms}$$

---

## 4. Comparison and Synthesis

| Crossing Regime | Physical Condition | Applicable Formula for $\Delta_{\text{flush}}$ | Numerical Offset Value |
| :--- | :--- | :--- | :--- |
| **Region 3 Crossing** | $I_0 > 0.562\,\text{A}$ ($I_{\text{guarded}} = 0.410\,\text{A}$) | $\mathbf{\Delta_{\text{flush}} = \tau_{\text{eff}} \ln C(T_w, \tau_{\text{eff}})}$ (Constant) | **$\mathbf{1.117\,ms}$ (Exact)** |
| **Region 2 Crossing** | $I_0 < 0.562\,\text{A}$ ($I_{\text{guarded}} = 0.410\,\text{A}$) | **Transcendental Root Solution** $g(x) = (I_{\text{guarded}}/I_0)^2$ | **Variable: $0.0\,\text{ms} < \Delta_{\text{flush}} < 1.117\,\text{ms}$** |

### Definitive Metrological Ruling:
1. The formula $\Delta_{\text{flush}} = \tau_{\text{eff}} \ln C$ is **NOT** a universal crossing-delay formula. It is mathematically valid **ONLY** in Region 3.
2. In Region 2, the moving RMS flush lag is strictly smaller than $1.117\,\text{ms}$ and decreases as $I_0 \to I_{\text{guarded}}$.
3. Because all normal vehicle driving states operate with $I_0 \gg 0.562\,\text{A}$ (e.g., $15\,\text{A}$ to $115\,\text{A}$), standard vehicle E-Stop events cross in **Region 3**, where the exact analytical offset is $1.12\,\text{ms}$.
