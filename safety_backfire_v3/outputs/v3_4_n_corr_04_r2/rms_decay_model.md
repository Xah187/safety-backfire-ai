# V3.4-N-CORR-04-R2 — Physical Decay & RMS Response Model Reconciliation

**Document Identifier:** `outputs/v3_4_n_corr_04_r2/rms_decay_model.md`  
**Milestone:** `V3.4-N-CORR-04-R2`  
**Classification:** Metrology & Filter Dynamic Verification  
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

## 1. Executive Mandate & Deletion of Unsupported Decay Rules

In Milestone V3.4-N-CORR-04 and V3.4-N-CORR-04-R1, the lower bound on persistence was defended with the heuristic:
$$T_{\text{persist, min}} = 3 \times \tau_{\text{eff}} = 3 \times 2.8\,\text{ms} = 8.4\,\text{ms}$$
and prior drafts claimed that $3\tau$ guaranteed "complete decay into baseline" or "noise-floor settlement."

### 1.1 Formal Deletion
1. **Approval Criterion Revocation:** The rule $T_{\text{persist\_min}} = 3 \times \tau_{\text{eff}}$ is **DELETED** as an approval criterion.
2. **Unsupported Generalizations Revoked:** Describing $3\tau$ as "complete decay," "noise-floor settlement," "minimum persistence," or "RMS settlement" is **PROHIBITED** unless mathematically derived from the actual pre-trip current $I_0$ and the actual noise floor.
3. **Descriptive Role of Time Constants:**
   - $\tau_e = L_s / R_s = 4.94\,\text{ms}$: Pure electromagnetic stator constant for unforced RL discharge into open terminals. Descriptive only.
   - $\tau_{\text{eff}} \approx 2.8\,\text{ms}$: Empirical single-exponential envelope fit under inverter STO freewheeling diode clamp. Descriptive only.
   - Neither parameter automatically determines the required duration of $T_{\text{persist}}$.

---

## 2. Decoupling Physical Envelope Crossing from RMS Threshold Crossing

### 2.1 The Semantic Fallacy in Prior Milestones
In prior milestone reports, the timestamps for physical threshold crossing and RMS threshold crossing were listed with identical time ranges:
$$\text{Legacy Report Claim: } t_{\text{phys\_cross}} \in [21.2, 25.8]\,\text{ms}, \quad t_{\text{rms}} \in [21.2, 25.8]\,\text{ms}$$
This implicitly asserted that:
$$\Delta_{\text{flush}} = t_{\text{rms\_threshold\_cross}} - t_{\text{phys\_envelope\_cross}} = 0.0\,\text{ms}$$
This assertion is mathematically impossible. A backward-looking sliding RMS filter integrating over $T_w = 2.0\,\text{ms}$ contains historical, larger current values, causing $I_{\text{RMS}}(t)$ to strictly lag behind the instantaneous current envelope $i(t)$.

### 2.2 Formal Separation of Timing Variables
To eliminate ambiguity, four distinct temporal parameters are strictly defined:

```text
t0: E_STOP_COMMAND (0.0 ms datum)
 │
 ▼
t_phys_onset: Physical onset of inverter gate-drive clamp / current collapse
 │
 ▼
t_phys_envelope_cross: Instantaneous current envelope falls below guarded threshold:
                       i(t_phys_envelope_cross) = I_guarded
 │
 ▼ [Delta_flush = t_rms_threshold_cross - t_phys_envelope_cross > 0]
t_rms_threshold_cross: Sliding RMS evaluation falls below guarded threshold:
                       I_RMS(t_rms_threshold_cross) = I_guarded
 │
 ▼ [Discrete grid alignment latency: Delta_grid in [0.0, 0.1] ms]
t_persist_start: The exact evaluation frame index k_0 where persistence counter starts:
                 t_persist_start = k_0 * Delta_t_step >= t_rms_threshold_cross
 │
 ▼ [Sampled persistence hold duration]
t_endpoint_declaration: Final qualification frame where safe state is declared
```

---

## 3. Mathematical Evaluation of $\Delta_{\text{flush}}$ Across Operating Regimes

As derived in [rms_closed_form.md](file:///Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r2/rms_closed_form.md), in Region 3 ($t \ge t_0 + T_w$), the analytical lag is independent of $I_0$ and $I_{\text{guarded}}$:

$$\Delta_{\text{flush}} = \tau_{\text{eff}} \ln\left( \sqrt{ \frac{\tau_{\text{eff}}}{2 T_w} \left( \exp\left(\frac{2 T_w}{\tau_{\text{eff}}}\right) - 1 \right) } \right)$$

Evaluating for $T_w = 2.0\,\text{ms}$ and $\tau_{\text{eff}} = 2.8\,\text{ms}$:
$$\mathbf{\Delta_{\text{flush}} \approx 1.117\,ms}$$

### 3.3 Operating Point Sensitivity Analysis
Let pre-shutdown operating current $I_0$ vary from light load to full rated peak:
- $I_{\text{guarded}} = 0.410\,\text{A RMS}$
- $t_0 = t_{\text{phys\_onset}} = 13.0\,\text{ms}$ (nominal STO deassertion)

| Operating Condition | Pre-trip Current $I_0$ | Physical Envelope Crossing $t_{\text{phys}}$ | RMS Crossing Region | RMS Threshold Crossing $t_{\text{rms}}$ | Actual Flush Lag $\Delta_{\text{flush}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Light Crawl (15% torque)** | $15.0\,\text{A}$ | $13.0 + 2.8 \ln(15 / 0.410) = \mathbf{23.08\,ms}$ | Region 3 ($t > 15.0\,\text{ms}$) | $23.08 + 1.12 = \mathbf{24.20\,ms}$ | **$+1.12\,\text{ms}$** |
| **Medium Cruise (50% torque)** | $50.0\,\text{A}$ | $13.0 + 2.8 \ln(50 / 0.410) = \mathbf{26.45\,ms}$ | Region 3 ($t > 15.0\,\text{ms}$) | $26.45 + 1.12 = \mathbf{27.57\,ms}$ | **$+1.12\,\text{ms}$** |
| **Full Rated Peak (100% torque)**| $115.0\,\text{A}$| $13.0 + 2.8 \ln(115 / 0.410) = \mathbf{28.78\,ms}$ | Region 3 ($t > 15.0\,\text{ms}$) | $28.78 + 1.12 = \mathbf{29.90\,ms}$ | **$+1.12\,\text{ms}$** |
| **Low Residual Boundary** | $0.80\,\text{A}$ | $13.0 + 2.8 \ln(0.8 / 0.410) = \mathbf{14.87\,ms}$ | Region 2 ($t < 15.0\,\text{ms}$) | Numerical solve: $\mathbf{15.62\,ms}$ | **$+0.75\,\text{ms}$** |

### Critical Finding:
Across all dynamic operating conditions where $I_0 > 1.0\,\text{A}$, the threshold crossing occurs firmly in Region 3, and the moving RMS filter adds an exact analytical delay:
$$\mathbf{\Delta_{\text{flush}} = 1.12\,ms}$$

---

## 4. Re-Auditing the 10 Historical Characterization Trials

Because the historical 10 trials recorded only a single threshold timestamp ($t_{\text{threshold}}$) without raw digitized oscillograms:
1. It is impossible to determine whether the reported numbers represented $t_{\text{phys\_envelope\_cross}}$ or $t_{\text{rms\_threshold\_cross}}$.
2. If the reported $25.8\,\text{ms}$ was $t_{\text{phys}}$, then true $t_{\text{rms}}$ was $25.8 + 1.12 = 26.92\,\text{ms}$.
3. If $t_{\text{persist\_start}} = 26.92\,\text{ms}$, adding $10.0\,\text{ms}$ persistence yields $t_{\text{endpoint}} = 36.92\,\text{ms}$ (not $35.8\,\text{ms}$).
4. Therefore, the historical reporting suffered from internal mathematical inconsistency.

Per Section 4 and Section 5 of the mandate:
$$\mathbf{TIMING\_EVIDENCE = REPORT\_BASED}$$
The timing closure must remain **`BLOCKED`** pending ingestion of raw time-series data.
