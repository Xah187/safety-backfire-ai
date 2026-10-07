# V3.4-N-CORR-04-R4 — Discrete RMS Index Contract & Exact Index Semantics

**Document:** `outputs/v3_4_n_corr_04_r4/discrete_rms_index_contract.md`  
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
REFERENCE_MODEL_VERIFIED        = TRUE
FROZEN_RMS_IMPLEMENTATION_VERIFIED = FALSE
FINAL_STATUS                    = BLOCKED
```

---

## 1. Purpose of the Normative Index Contract

Historical specifications cited a "2.0 ms moving RMS window evaluated every 0.1 ms at 1.0 MSa/s" without defining exact fencepost indices, array slicing semantics, or timestamp association. This ambiguity left open whether a window comprises 2000 samples ($1.999\,\text{ms}$ elapsed between extreme samples) or 2001 samples ($2.000\,\text{ms}$ elapsed between extreme samples).

This document establishes the **normative mathematical contract** for discrete RMS computation to eliminate off-by-one errors, timestamp skews, and ambiguity in future audited implementations.

---

## 2. Fundamental Parameters & Definitions

| Parameter Symbol | Mathematical Definition | Canonical Value | Units | Definition & Epistemic Role |
| :--- | :--- | :--- | :---: | :--- |
| $f_s$ | Sampling frequency | $1\,000\,000$ | $\text{Hz}$ ($\text{Sa/s}$) | Exact ADC conversion rate ($1.0\,\text{MSa/s}$). |
| $T_s$ | Sampling period | $1.0 \times 10^{-6}$ | $\text{s}$ ($\mu\text{s}$) | Uniform time increment between consecutive raw samples ($T_s = 1/f_s$). |
| $N$ | Window sample count | $2000$ | samples | Exact number of discrete current samples included in each RMS sum. |
| $T_w^{\text{cont}}$ | Continuous integration support | $2.0 \times 10^{-3}$ | $\text{s}$ ($\text{ms}$) | Analytical integration interval ($N \cdot T_s = 2000\,\mu\text{s}$). |
| $T_w^{\text{span}}$ | Discrete elapsed time span | $1.999 \times 10^{-3}$ | $\text{s}$ ($\text{ms}$) | Elapsed time from first sample to last sample in window: $(N-1) \cdot T_s$. |
| $M$ | Stride / evaluation step | $100$ | samples | Decimation factor between consecutive RMS evaluations ($M = 100 \implies \Delta t = 0.1\,\text{ms}$). |
| $\Delta t$ | RMS evaluation grid step | $1.0 \times 10^{-4}$ | $\text{s}$ ($\text{ms}$) | Time interval between consecutive RMS outputs ($M \cdot T_s = 100\,\mu\text{s} = 0.1\,\text{ms}$). |
| $I_{\text{guard}}$ | Guarded threshold | $0.410$ | $\text{A RMS}$ | Comparator limit for de-energization qualification. |

---

## 3. Resolution: 2000 Sample Values vs. 2001 Timestamped Points

A critical metrological distinction exists between discrete sample count and elapsed boundary span:

1. **The 2001-Point Fencepost Dilemma:**
   If a time window spans exactly $2000.0\,\mu\text{s}$ from initial timestamp $t_{\text{start}}$ to terminal timestamp $t_{\text{end}}$ on a $1\,\mu\text{s}$ uniform grid:
   $$t_{\text{end}} - t_{\text{start}} = 2000\,\mu\text{s} \implies \frac{t_{\text{end}} - t_{\text{start}}}{T_s} = 2000 \text{ intervals}$$
   The number of discrete sample points on that closed interval $[t_{\text{start}}, t_{\text{end}}]$ is:
   $$N_{\text{points}} = 2000 + 1 = 2001 \text{ points}$$

2. **The Normative Discrete Moving Average ($N = 2000$):**
   In discrete signal processing, a uniform moving average filter of order $N = 2000$ operates on a sequence of exactly **2000 sample values**. Each sample represents a left-hand Riemann partition of width $T_s = 1\,\mu\text{s}$, giving an exact integration support of $N \cdot T_s = 2000\,\mu\text{s} = 2.0\,\text{ms}$.
   
   The temporal distance between the earliest sample in the window ($x[k-N+1]$) and the latest sample ($x[k]$) is:
   $$\Delta t_{\text{span}} = (k - (k - N + 1)) \cdot T_s = (N - 1) \cdot T_s = 1999\,\mu\text{s} = 1.999\,\text{ms}$$

### Normative Resolution:
- The normative discrete RMS implementation **SHALL** consume exactly **$N = 2000$ sample values**.
- The phrase "2.0 ms window" **SHALL** refer strictly to the **mathematical integration support** $N \cdot T_s = 2.000\,\text{ms}$.
- Implementations **SHALL NOT** consume 2001 samples. Consuming 2001 samples without adjusting the normalization denominator to 2001 introduces a $0.05\%$ energy distortion and shifts the effective group delay by $+0.5\,\mu\text{s}$.

---

## 4. Exact Slicing Semantics & Formulation

Let raw digitized current samples be represented by the zero-indexed discrete sequence:
$$x[n] \quad \text{for } n \in \{0, 1, 2, \dots, K-1\}$$
where $n = 0$ corresponds to physical timestamp $t = 0.0\,\text{s}$.

### 4.1 Window Sample Set
For an RMS calculation terminating at current sample index $k$ (where $k \ge N - 1$):
$$\mathcal{W}[k] = \{ x[j] \mid j = k - N + 1, k - N + 2, \dots, k \}$$
In Python 0-indexed half-open slice notation:
$$\texttt{window\_samples} = \texttt{raw\_samples[k - N + 1 : k + 1]}$$

### 4.2 Mathematical Operator
The discrete RMS output associated with sample index $k$ is defined by:
$$I_{\text{RMS}}[k] = \sqrt{ \frac{1}{N} \sum_{j=0}^{N-1} x[k - j]^2 } = \sqrt{ \frac{1}{2000} \sum_{m=k-1999}^{k} (x[m])^2 }$$

- **Normalization Denominator:** Exactly $N = 2000$.
- **Window Slicing:** Exactly indices $[k-1999 \dots k]$ inclusive.

---

## 5. Output Evaluation Grid & Timestamp Association

RMS values are not evaluated at every sample step ($1\,\mu\text{s}$), but are decimated by stride factor $M = 100$ ($0.1\,\text{ms}$ grid).

### 5.1 Evaluation Indices
Let $p \in \{0, 1, 2, \dots\}$ be the non-negative integer frame counter.
The $p$-th discrete RMS evaluation occurs at sample index:
$$k_p = (N - 1) + p \cdot M = 1999 + 100 \cdot p$$

- **First Valid Output ($p = 0$):**
  $$k_0 = 1999 \implies \text{Indices } [0 \dots 1999] \text{ consumed}.$$
- **Second Valid Output ($p = 1$):**
  $$k_1 = 2099 \implies \text{Indices } [100 \dots 2099] \text{ consumed}.$$
- **$p$-th Valid Output:**
  $$k_p = 1999 + 100 \cdot p$$

### 5.2 Timestamp Association Convention
The physical timestamp assigned to the discrete RMS output $I_{\text{RMS}}[k_p]$ is the **right-edge (causal arrival) timestamp** of the latest sample in the window:
$$t_{\text{RMS}}[p] = k_p \cdot T_s = (1999 + 100 \cdot p) \times 1.0 \times 10^{-6}\,\text{s}$$
In milliseconds:
$$t_{\text{RMS}}[p] = 1.999 + 0.1 \cdot p \quad [\text{ms}]$$

*Rationale:* The RMS output cannot be known before the final sample in its window has physically arrived at the ADC. Assigning any earlier timestamp (such as the center of the window $t - 1.0\,\text{ms}$) would violate physical causality for real-time monitoring and confuse post-processing delay accounting.

---

## 6. Threshold Crossing & Equality Semantics

### 6.1 Comparator Contract
The threshold crossing comparator is governed by the non-strict inequality:
$$\mathcal{C}(p) = \begin{cases} 
\text{TRUE} & \text{if } I_{\text{RMS}}[k_p] \le I_{\text{guard}} \\ 
\text{FALSE} & \text{if } I_{\text{RMS}}[k_p] > I_{\text{guard}} 
\end{cases}$$
where $I_{\text{guard}} = 0.410\,\text{A RMS}$.

- **Equality Rule:** Non-strict inequality $\le$ is normative. If $I_{\text{RMS}}[k_p]$ evaluates to exactly $0.41000000\,\text{A}$, it is considered below or at threshold ($\text{TRUE}$).
- **Crossing Event:** The threshold crossing occurs at index $p^*$ if $\mathcal{C}(p^*) = \text{TRUE}$ and $\mathcal{C}(p^* - 1) = \text{FALSE}$.
- **Crossing Timestamp:** $t_{\text{cross}} = t_{\text{RMS}}[p^*]$. No fractional-index interpolation is permitted unless specified by a certified superseding protocol.

---

## 7. Numerical Precision & Exception Handling Contract

### 7.1 Arithmetic Precision
- All intermediate squaring, summation, and division operations **SHALL** be performed using standard IEEE 754 double-precision 64-bit floating-point arithmetic (`float64`).
- Implementations must guard against negative accumulator values resulting from floating-point roundoff (e.g. if circular running-sum implementations are used):
  $$\text{accumulator} = \max\left(0.0, \sum (x[m])^2\right)$$

### 7.2 Missing Samples & Non-Uniform Grids
- The pipeline contract strictly assumes a uniform timebase ($T_s = 1.000\,\mu\text{s} \pm 0.001\,\mu\text{s}$).
- If an acquisition contains dropped samples, clock discontinuities, or non-uniform intervals:
  $$\text{PIPELINE\_ERROR: NON\_UNIFORM\_SAMPLING\_DETECTED} \implies \text{HALT}$$
  Zero-padding, linear interpolation, or sample duplication across gaps is **STRICTLY PROHIBITED**.

### 7.3 NaN and Inf Handling
- If any raw sample $x[m]$ in the window contains IEEE NaN, positive infinity, or negative infinity:
  $$I_{\text{RMS}}[k_p] = \text{NaN} \implies \mathcal{C}(p) = \text{FALSE}$$
- The persistence state machine **SHALL** immediately reset its consecutive frame counter to zero upon encountering a NaN output.

---

## 8. Normative Reference Implementation Snippet (Pure Python)

```python
import math
from typing import List, Optional, Tuple

def compute_discrete_rms_stream(
    raw_samples: List[float],
    fs: float = 1_000_000.0,
    window_samples: int = 2000,
    step_samples: int = 100,
    guard_threshold: float = 0.410
) -> List[Tuple[int, float, float, bool]]:
    """
    Normative discrete RMS windowing contract.
    Returns: List of (frame_index p, sample_index k, timestamp_s, comparator_bool)
    """
    Ts = 1.0 / fs
    N = window_samples
    M = step_samples
    results = []
    
    total_samples = len(raw_samples)
    if total_samples < N:
        return results  # Insufficient samples for first window
    
    # Initial valid index
    p = 0
    k = N - 1
    
    while k < total_samples:
        window = raw_samples[k - N + 1 : k + 1]
        
        # Check for NaN / Inf
        has_invalid = any(math.isnan(v) or math.isinf(v) for v in window)
        if has_invalid:
            rms_val = float('nan')
            comp = False
        else:
            sum_sq = sum(v * v for v in window)
            rms_val = math.sqrt(max(0.0, sum_sq / float(N)))
            comp = (rms_val <= guard_threshold)
            
        t_rms = k * Ts
        results.append((p, k, t_rms, comp))
        
        p += 1
        k += M
        
    return results
```
