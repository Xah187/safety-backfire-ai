# V3.4-N-CORR-04-R2-R1 — Mode B Persistence Semantics & Timing Specification

**Document Identifier:** `outputs/v3_4_n_corr_04_r2_r1/persistence_semantics_v4.md`  
**Milestone:** `V3.4-N-CORR-04-R2-R1`  
**Classification:** Discrete Digital Logic & Verification Pipeline Timing Specification  
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

## 1. Mode B Discrete Timer Specification

In discrete-time digital signal processing evaluated at fixed intervals $\Delta t_{\text{step}} = 0.1\,\text{ms}$ ($100\,\mu\text{s}$), the persistence qualification logic is formally defined by **Mode B (Elapsed Timer Intervals)**.

### 1.1 Formal Mathematical Definitions
Let $k \in \mathbb{N}$ denote the evaluation frame index, with timestamp:
$$t_k = k \cdot \Delta t_{\text{step}}$$

1. **Trigger / Arming Instant ($k_{\text{start}}$):**
   The first discrete frame index $k$ such that the moving RMS current satisfies the guarded threshold:
   $$k_{\text{start}} = \min \big\{ k \in \mathbb{N} \;:\; I_{\text{RMS}}[k] \le I_{\text{guarded}} \big\}$$
   Timestamp:
   $$t_{\text{persist\_start}} = k_{\text{start}} \cdot \Delta t_{\text{step}}$$

2. **Hold Condition:**
   For every frame index $k$ in the interval $k_{\text{start}} \le k \le k_{\text{start}} + 100$:
   $$I_{\text{RMS}}[k] \le I_{\text{guarded}}$$

3. **Qualification Instant ($k_{\text{qualified}}$):**
   The frame index exactly $100$ intervals after $k_{\text{start}}$:
   $$\mathbf{k_{\text{qualified}} = k_{\text{start}} + 100}$$
   Timestamp:
   $$\mathbf{t_{\text{qualified}} = k_{\text{qualified}} \cdot \Delta t_{\text{step}} = (k_{\text{start}} + 100) \cdot \Delta t_{\text{step}} = t_{\text{persist\_start}} + 10.0\,ms}$$

---

## 2. Exhaustive Enumeration of Frame Counts & Time Spans

| Timing Parameter | Exact Value | Mathematical Definition |
| :--- | :---: | :--- |
| **Evaluation Step Size ($\Delta t_{\text{step}}$)** | $0.1\,\text{ms}$ | $100\,\mu\text{s}$ interval between successive sliding RMS evaluations |
| **Window Length ($T_w$)** | $2.0\,\text{ms}$ | $2000$ raw ADC samples at $f_s = 1.0\,\text{MSa/s}$ |
| **First Qualifying Frame Index** | $k_{\text{start}}$ | Frame where $I_{\text{RMS}}[k] \le I_{\text{guarded}}$ is first detected |
| **Final Qualifying Frame Index** | $k_{\text{start}} + 100$ | Frame where safe state qualification is confirmed |
| **Total Evaluation Points Evaluated** | **$101$ points** | Set of frame indices $\{ k_{\text{start}}, k_{\text{start}}+1, \dots, k_{\text{start}}+100 \}$ |
| **Total Elapsed Step Intervals** | **$100$ intervals** | Number of $0.1\,\text{ms}$ intervals separating frame $k_{\text{start}}$ and $k_{\text{start}}+100$ |
| **Total Elapsed Time Span** | **$10.0\,\text{ms}$** | $\Delta T = 100 \times 0.1\,\text{ms} = 10.0\,\text{ms}$ |
| **Total Raw Time Span Covered by Data** | **$12.0\,\text{ms}$** | Leading edge of window at $k_{\text{start}}$ to trailing edge at $k_{\text{start}}+100$ ($T_w + \Delta T$) |

---

## 3. Contrast with Mode A (Inclusive Sample Counter)

To ensure zero ambiguity during software auditing:
- In an inclusive 100-sample counter (**Mode A**), the 100th evaluation occurs at $k = k_{\text{start}} + 99$. The elapsed time is $(100 - 1) \times 0.1\,\text{ms} = 9.9\,\text{ms}$.
- In **Mode B**, qualification requires that **100 full intervals elapse**, meaning evaluation continues until $k = k_{\text{start}} + 100$, achieving an exact elapsed duration of **$10.0\,\text{ms}$**.

$$\mathbf{\text{PIPELINE\_STATUS} = \text{MODE\_B (101 EVALUATION POINTS, 100 INTERVALS, 10.0 ms ELAPSED)}}$$
