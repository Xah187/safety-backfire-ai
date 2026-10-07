# V3.4-N-CORR-04-R2 — Closed-Form Moving RMS Response Model

**Document Identifier:** `outputs/v3_4_n_corr_04_r2/rms_closed_form.md`  
**Milestone:** `V3.4-N-CORR-04-R2`  
**Classification:** Exact Digital Signal Processing & Filter Transient Mathematics  
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

## 1. Mathematical Problem Formulation

Consider an idealized exponential current decay initiated at timestamp $t = t_0$:

$$i(t) = \begin{cases} I_0, & t < t_0 \\ I_0 \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right), & t \ge t_0 \end{cases}$$

where:
- $I_0$: Pre-shutdown current amplitude (or pre-shutdown RMS amplitude) [$\text{A}$].
- $t_0$: Timestamp of physical current collapse onset ($t_{\text{phys\_onset}}$) [$\text{s}$].
- $\tau_{\text{eff}}$: Effective exponential decay time constant under inverter STO clamping [$\text{s}$].
- $T_w$: Moving rectangular RMS window duration ($T_w = 2.0\,\text{ms} = 0.002\,\text{s}$).

The causal continuous-time moving RMS metric $I_{\text{RMS}}(t)$ is defined by:

$$I_{\text{RMS}}^2(t) = \frac{1}{T_w} \int_{t - T_w}^{t} i^2(\tau) \, d\tau$$

---

## 2. Derivation of Piecewise Regions

The integration interval $[t - T_w, t]$ traverses three distinct regimes relative to the event boundary $t_0$.

### 2.1 Region 1: Pre-Event Window ($t < t_0$)
The integration interval lies entirely prior to $t_0$ ($t - T_w < t \le t_0$):

$$I_{\text{RMS}}^2(t) = \frac{1}{T_w} \int_{t - T_w}^{t} I_0^2 \, d\tau = I_0^2 \cdot \frac{t - (t - T_w)}{T_w} = I_0^2$$

$$\mathbf{I_{\text{RMS}}(t) = I_0 \quad \text{for } t < t_0}$$

---

### 2.2 Region 2: Window Overlaps Decay Onset ($t_0 \le t < t_0 + T_w$)
The integration window spans both pre-event and decaying post-event current:
- Pre-event sub-interval: $[t - T_w, \; t_0]$, where $i(\tau) = I_0$. Duration: $t_0 - (t - T_w) = T_w - (t - t_0)$.
- Post-event sub-interval: $[t_0, \; t]$, where $i(\tau) = I_0 \exp\left(-\frac{\tau - t_0}{\tau_{\text{eff}}}\right)$. Duration: $t - t_0$.

Evaluating the integral:

$$I_{\text{RMS}}^2(t) = \frac{1}{T_w} \left[ \int_{t - T_w}^{t_0} I_0^2 \, d\tau + \int_{t_0}^{t} I_0^2 \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right) \, d\tau \right]$$

1. First integral:
$$\int_{t - T_w}^{t_0} I_0^2 \, d\tau = I_0^2 \big[ t_0 - (t - T_w) \big] = I_0^2 \big[ T_w - (t - t_0) \big]$$

2. Second integral:
$$\int_{t_0}^{t} I_0^2 \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right) \, d\tau = I_0^2 \left[ -\frac{\tau_{\text{eff}}}{2} \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right) \right]_{t_0}^{t} = I_0^2 \frac{\tau_{\text{eff}}}{2} \left[ 1 - \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right) \right]$$

Combining and dividing by $T_w$:

$$\mathbf{I_{\text{RMS}}^2(t) = I_0^2 \left[ 1 - \frac{t - t_0}{T_w} + \frac{\tau_{\text{eff}}}{2 T_w} \left( 1 - \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right) \right) \right] \quad \text{for } t_0 \le t < t_0 + T_w}$$

**Continuity Verification at $t = t_0$:**
$$I_{\text{RMS}}^2(t_0^+) = I_0^2 [1 - 0 + 0] = I_0^2 = I_{\text{RMS}}^2(t_0^-) \quad \checkmark$$

---

### 2.3 Region 3: Window Entirely Post-Event ($t \ge t_0 + T_w$)
The integration window $[t - T_w, t]$ lies completely within the decaying region ($t - T_w \ge t_0$):

$$I_{\text{RMS}}^2(t) = \frac{1}{T_w} \int_{t - T_w}^{t} I_0^2 \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right) \, d\tau$$

Evaluating:

$$I_{\text{RMS}}^2(t) = \frac{I_0^2}{T_w} \left[ -\frac{\tau_{\text{eff}}}{2} \exp\left(-\frac{2(\tau - t_0)}{\tau_{\text{eff}}}\right) \right]_{t - T_w}^{t} = \frac{I_0^2 \tau_{\text{eff}}}{2 T_w} \left[ \exp\left(-\frac{2(t - T_w - t_0)}{\tau_{\text{eff}}}\right) - \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right) \right]$$

Factoring out $\exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right)$:

$$I_{\text{RMS}}^2(t) = I_0^2 \left( \frac{\tau_{\text{eff}}}{2 T_w} \left( \exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1 \right) \right) \exp\left(-\frac{2(t - t_0)}{\tau_{\text{eff}}}\right)$$

Taking the square root:

$$\mathbf{I_{\text{RMS}}(t) = I_0 \cdot C(T_w, \tau_{\text{eff}}) \cdot \exp\left(-\frac{t - t_0}{\tau_{\text{eff}}}\right) \quad \text{for } t \ge t_0 + T_w}$$

where the dimensionless window amplification factor $C(T_w, \tau_{\text{eff}})$ is defined by:

$$\mathbf{C(T_w, \tau_{\text{eff}}) = \sqrt{ \frac{\tau_{\text{eff}}}{2 T_w} \left( \exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1 \right) }}$$

**Continuity Verification at $t = t_0 + T_w$:**
- From Region 2:
  $$I_{\text{RMS}}^2((t_0 + T_w)^-) = I_0^2 \left[ 0 + \frac{\tau_{\text{eff}}}{2 T_w} \left( 1 - \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right) \right) \right]$$
- From Region 3:
  $$I_{\text{RMS}}^2((t_0 + T_w)^+) = I_0^2 \frac{\tau_{\text{eff}}}{2 T_w} \left( \exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1 \right) \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right) = I_0^2 \frac{\tau_{\text{eff}}}{2 T_w} \left( 1 - \exp\left(-\frac{2 T_w}{\tau_{\text{eff}}}\right) \right) \quad \checkmark$$

---

## 3. Threshold-Crossing Derivations

### 3.1 Instantaneous Physical Envelope Crossing
The instantaneous physical current envelope crosses $I_{\text{guarded}}$ when:

$$I_0 \exp\left(-\frac{t_{\text{phys\_envelope\_cross}} - t_0}{\tau_{\text{eff}}}\right) = I_{\text{guarded}}$$

Solving explicitly for $t_{\text{phys\_envelope\_cross}}$:

$$\mathbf{t_{\text{phys\_envelope\_cross}} = t_0 + \tau_{\text{eff}} \ln\left( \frac{I_0}{I_{\text{guarded}}} \right)}$$

---

### 3.2 RMS Threshold Crossing (Region 3 Analysis)
When the threshold crossing occurs in Region 3 ($t \ge t_0 + T_w$):

$$I_{\text{RMS}}(t_{\text{rms\_threshold\_cross}}) = I_0 \cdot C(T_w, \tau_{\text{eff}}) \cdot \exp\left(-\frac{t_{\text{rms\_threshold\_cross}} - t_0}{\tau_{\text{eff}}}\right) = I_{\text{guarded}}$$

Solving explicitly for $t_{\text{rms\_threshold\_cross}}$:

$$\mathbf{t_{\text{rms\_threshold\_cross}} = t_0 + \tau_{\text{eff}} \ln\left( \frac{I_0 \cdot C(T_w, \tau_{\text{eff}})}{I_{\text{guarded}}} \right)}$$

Decomposing the logarithm:

$$\mathbf{t_{\text{rms\_threshold\_cross}} = t_{\text{phys\_envelope\_cross}} + \tau_{\text{eff}} \ln\left( C(T_w, \tau_{\text{eff}}) \right)}$$

---

## 4. Exact Closed-Form Expression for RMS Window Latency ($\Delta_{\text{flush}}$)

The delay between instantaneous physical envelope threshold crossing and moving RMS threshold crossing is:

$$\mathbf{\Delta_{\text{flush}} = t_{\text{rms\_threshold\_cross}} - t_{\text{phys\_envelope\_cross}} = \tau_{\text{eff}} \ln\left( \sqrt{ \frac{\tau_{\text{eff}}}{2 T_w} \left( \exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1 \right) } \right) = \frac{\tau_{\text{eff}}}{2} \ln\left( \frac{\tau_{\text{eff}}}{2 T_w} \left( \exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1 \right) \right)}$$

### Numerical Evaluation for Frozen Baseline:
- Window duration: $T_w = 2.0\,\text{ms}$
- Empirical decay constant: $\tau_{\text{eff}} = 2.8\,\text{ms}$
- Dimensionless ratio: $\frac{2 T_w}{\tau_{\text{eff}}} = \frac{4.0}{2.8} \approx 1.428571$
- Exponential factor: $\exp(1.428571) \approx 4.172729$
- Term value: $\frac{1}{1.428571} (4.172729 - 1) = \frac{3.172729}{1.428571} \approx 2.220910$
- Dimensionless scale factor: $C = \sqrt{2.220910} \approx 1.490272$
- Logarithm: $\ln(1.490272) \approx 0.398958$

$$\mathbf{\Delta_{\text{flush}} = 2.8\,\text{ms} \times 0.398958 \approx 1.117\,\text{ms}}$$

### Crucial Engineering Insight:
1. The moving RMS filter imposes an exact analytical lag of **$\approx 1.12\,\text{ms}$** behind the physical current envelope.
2. Therefore:
   $$\mathbf{t_{\text{rms\_threshold\_cross}} > t_{\text{phys\_envelope\_cross}}}$$
3. Any document equating $t_{\text{rms\_threshold\_cross}} = t_{\text{phys\_envelope\_cross}}$ (such as the identical $[21.2, 25.8]\,\text{ms}$ values in R1) is **physically and mathematically false**.
