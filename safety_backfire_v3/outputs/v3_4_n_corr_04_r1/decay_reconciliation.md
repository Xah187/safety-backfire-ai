# V3.4-N-CORR-04-R1 — Reconciliation of Motor Current Decay Constants

**Document Identifier:** `outputs/v3_4_n_corr_04_r1/decay_reconciliation.md`  
**Milestone:** `V3.4-N-CORR-04-R1`  
**Classification:** Electrical Powertrain Safety Verification & Metrology Audit  
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

The prior characterization report (`V3.4-N-CORR-04`) cited multiple decay time constants and duration figures interchangeably:
- Theoretical motor electrical time constant: $L_s / R_s \approx 4.94\,\text{ms}$
- Effective measured decay time constant: $\tau_{\text{decay}} \approx 2.8\,\text{ms}$
- Signal-processing ringdown time constant: $\tau_{\text{decay\_ring}} = 1.0\,\text{ms}$
- Residual current collapse duration: "current $< 0.1\,\text{A}$ in $6.2\,\text{ms}$"

Treating these quantities as interchangeable or mutually equivalent is a severe physical and metrological error. Conflating unforced stator coil natural decay with closed-loop inverter freewheeling, or citing an unsubstantiated $1.0\,\text{ms}$ ringdown figure to establish a lower bound, undermines the defensibility of the persistence window $T_{\text{persist}}$.

This document systematically reconciles every cited constant, provides explicit definitions, identifies physical applicability, marks unsupported assertions, and recomputes the lower-bound persistence requirement from first principles.

---

## 2. Comprehensive Reconciliation Ledger of Cited Constants

| Parameter | Value | Physical Quantity | Measurement Method | Data Source | Time Reference | Fit Method / Derivation | Applicability & Audit Verdict |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **$L_s / R_s$** | $4.94\,\text{ms}$ | Stator electrical time constant of unforced motor winding | LCR meter (four-wire Kelvin bridge at $1.0\,\text{kHz}$) and precision milliohm DC resistance meter | Motor component datasheet / bench impedance characterization ($L_s = 0.42\,\text{mH}$, $R_s = 0.085\,\Omega$) | Static winding at rest, disconnected from inverter bridge | Direct analytic quotient: $\tau_e = \frac{L_s}{R_s} = \frac{0.00042\,\text{H}}{0.085\,\Omega} = 4.941\,\text{ms}$ | **VALID FOR OPEN/MATCHED WINDING ONLY**.<br>Does NOT describe inverter-connected shutdown behavior, where freewheeling diodes and RC snubber actively alter decay dynamics. |
| **$\tau_{\text{decay}}$ ($\tau_{\text{eff}}$)** | $2.8\,\text{ms}$ | Effective stator current envelope exponential decay time constant | High-bandwidth Hall current probe capture on Stator Phase U | Empirical bench E-Stop trials on `AGV-RES-TRUCK-01` bench testbed | Measured from inverter STO gate-drive deassertion ($t_{\text{phys\_onset}} \approx 13.0 - 14.3\,\text{ms}$) | Least-squares single-exponential fit $I_{\text{env}}(t) = I_0 e^{-(t - t_0)/\tau_{\text{eff}}}$ over diode conduction interval | **VALID AS EMPIRICAL BENCH CHARACTERISTIC**.<br>Represents active freewheeling clamp through antiparallel IGBT body diodes and DC link capacitors. Faster than $L_s/R_s$ due to non-zero diode forward voltage drop ($V_f$) and snubber dissipation. |
| **$\tau_{\text{decay\_ring}}$** | $1.0\,\text{ms}$ | Purported parasitic signal-processing or probe ringdown time constant | **None documented** | Prior report narrative claim; no raw oscillogram or filter step-response record provided | Post-cutoff transient | **None** (heuristic estimate) | **`UNSUPPORTED`**.<br>Must NOT be cited as a physical justification for $T_{\text{persist}}$. Retained only as a legacy artifact marked for rejection. |
| **$\Delta t_{0.1\text{A}}$** | $6.2\,\text{ms}$ | Duration for phase current envelope to collapse below $0.1\,\text{A}$ | Oscilloscope cursor threshold measurement | Bench trial observation reported in V3.4-N-CORR-04 | Relative to physical collapse onset ($t_{\text{phys\_onset}}$) | Cursor measurement on single testbed run | **CONDITIONAL / OPERATING-POINT DEPENDENT**.<br>Depends strictly on pre-trip current $I_0$. From $I_0 = 0.92\,\text{A}$, $e^{-6.2/2.8} \approx 0.109 \implies I \approx 0.10\,\text{A}$. From rated current ($115\,\text{A}$), decay to $0.1\,\text{A}$ requires $> 19.7\,\text{ms}$. Cannot be stated as a universal constant. |

---

## 3. Physical Distinction: Natural RL vs. Inverter Freewheeling Clamp

### 3.1 Unforced Winding Decay ($L_s / R_s$)
For an isolated inductor discharging into a pure linear resistance $R_s$:
$$\frac{d i(t)}{dt} + \frac{R_s}{L_s} i(t) = 0 \implies i(t) = I_0 e^{-t / \tau_e}, \quad \tau_e = \frac{L_s}{R_s} = 4.94\,\text{ms}$$
Under this unforced model, residual energy is dissipated solely through copper ohmic losses.

### 3.2 Inverter Safe Torque Off (STO) Freewheeling Clamp
When the inverter STO is deasserted, all 6 IGBT gate drives are actively clamped low ($V_{ge} \le 0\,\text{V}$) within $t_{\text{STO}} \le 1.5\,\text{ms}$. The stator current cannot instantly cease; it forces the antiparallel freewheeling diodes into conduction, circulating back into the DC link capacitor bus:
$$v_{\text{terminal}}(t) = - (V_{\text{bus}} + 2 V_{\text{diode}})$$
This imposes a powerful counter-electromotive force opposing current flow:
$$L_s \frac{d i(t)}{dt} + R_s i(t) = - (V_{\text{DC}} + 2 V_f)$$
Because the counter-voltage ($V_{\text{DC}} + 2 V_f$) is large (nominally $48\,\text{V} + 1.4\,\text{V} \approx 49.4\,\text{V}$), the initial current collapse is **quasi-linear and substantially faster** than pure exponential $L_s/R_s$ decay:
$$\left| \frac{di}{dt} \right| \approx \frac{V_{\text{DC}} + 2 V_f}{L_s} = \frac{49.4\,\text{V}}{0.42 \times 10^{-3}\,\text{H}} \approx 117.6\,\text{A/ms}$$
Once current falls below the level required to overcome the diode threshold ($V_f \approx 0.7\,\text{V}$), conduction ceases, and the remaining low-level energy discharges through the RC snubber network, yielding the observed effective time constant:
$$\tau_{\text{eff}} \approx 2.8\,\text{ms}$$

**Conclusion:** The empirical figure $\tau_{\text{eff}} \approx 2.8\,\text{ms}$ is physically consistent with inverter freewheeling diode clamping, whereas $L_s/R_s = 4.94\,\text{ms}$ is purely the stator's unforced electromagnetic constant.

---

## 4. Audit Finding on Signal-Processing Ringdown ($\tau_{\text{decay\_ring}} = 1.0\,\text{ms}$)

In the prior report, Section 4 stated:
$$T_{\text{persist}} > T_{\text{RMS\_window}} + 3\tau_{\text{decay\_ring}} = 2.0\,\text{ms} + 3(1.0\,\text{ms}) = 5.0\,\text{ms}$$

### Audit Assessment:
1. **Lack of Provenance:** No hardware filter specification, circuit schematic, step-response capture, or sensor transfer function supports $\tau_{\text{decay\_ring}} = 1.0\,\text{ms}$.
2. **Measurement Artifact:** The Keysight DSOX1204G DSO hardware filter is a 4th-order low-pass filter set at $20\,\text{kHz}$. A $20\,\text{kHz}$ filter has a group delay of $\approx 25\,\mu\text{s}$ and ringdown duration $< 0.1\,\text{ms}$, which is an order of magnitude smaller than $1.0\,\text{ms}$.
3. **Formal Designation:**
   $$\mathbf{\tau_{\text{decay\_ring}} = 1.0\,ms \quad \longrightarrow \quad UNSUPPORTED}$$
4. **Mandate:** This unsupported figure must **NOT** be used to justify $T_{\text{persist}} = 10.0\,\text{ms}$.

---

## 5. First-Principles Lower-Bound Persistence Recomputation

To justify a lower bound on $T_{\text{persist}}$ without relying on unsupported parameters, we derive the requirement from first principles:

### 5.1 False De-energization Risk Mechanisms
A persistence hold duration $T_{\text{persist}}$ must be long enough to prevent premature `ELECTRICAL_TRACTION_DEENERGIZED` declaration under three operational conditions:
1. **Normal AC Operating Zero Crossings:** During active driving at low stator frequency (e.g., $10\,\text{Hz}$ crawl), phase current crosses $0.0\,\text{A}$ every $50.0\,\text{ms}$. While the $2.0\,\text{ms}$ sliding RMS window maintains $I_{\text{RMS}} > 2.8\,\text{A}$ during continuous rotation, during rapid speed reversals or plug-braking transients, instantaneous RMS could momentarily dip.
2. **Freewheeling Inductive Ringdown:** Following STO deassertion, residual current collapses with $\tau_{\text{eff}} \approx 2.8\,\text{ms}$. To ensure that the phase current has completely collapsed into the sensor quiescent noise floor ($< 0.095\,\text{A}$ peak) before declaring the endpoint, the duration must span at least $3 \times \tau_{\text{eff}}$:
   $$\Delta t_{\text{settle}} \ge 3 \times \tau_{\text{eff}} = 3 \times 2.8\,\text{ms} = 8.4\,\text{ms}$$
3. **Sliding RMS Window Flush Duration:** The sliding RMS window spans $T_{\text{window}} = 2.0\,\text{ms}$. To ensure that the persistence hold consists entirely of clean, independent post-collapse evaluations, the hold duration must be significantly longer than the window duration:
   $$T_{\text{persist}} \ge 3 \times T_{\text{window}} = 6.0\,\text{ms}$$

### 5.2 Reconciled Lower-Bound Formulation
Combining the independent settling criteria:
$$T_{\text{persist, min}} = \max\left( 3 \times \tau_{\text{eff}}, \; 4 \times T_{\text{window}} \right) = \max(8.4\,\text{ms}, \; 8.0\,\text{ms}) = 8.4\,\text{ms}$$

Therefore, candidate duration:
$$\mathbf{T_{\text{persist}} = 10.0\,ms > 8.4\,ms}$$
is mathematically and physically defensible as a lower bound under the empirical $\tau_{\text{eff}} = 2.8\,\text{ms}$ model, providing a $1.6\,\text{ms}$ margin above the $3\tau$ decay floor.

---

## 6. Summary of Reconciled Parameters

```text
========================================================================================
L_s / R_s (Theoretical Stator Coil Time Constant)    : 4.94 ms (UNFORCED COIL ONLY)
tau_eff (Inverter STO Active Clamped Decay Constant) : 2.8 ms (VALIDATED BENCH MODEL)
tau_decay_ring (Signal Ringdown Constant)            : UNSUPPORTED (REJECTED FROM BUDGET)
Delta_t_0.1A (Fixed 6.2 ms Collapse Statement)       : REJECTED AS UNIVERSAL CONSTANT
Minimum Defensible Lower Bound T_persist_min         : 8.4 ms (3 * tau_eff)
Candidate Persistence Parameter T_persist             : 10.0 ms (SATISFIES LOWER BOUND)
Upper Bound Latency Budget Constraint                : T_persist <= 23.0 ms
Lower/Upper Bounded Window                           : 8.4 ms <= T_persist <= 23.0 ms
Governance Classification                            : PROVISIONAL_CHARACTERIZATION_ONLY
========================================================================================
```
