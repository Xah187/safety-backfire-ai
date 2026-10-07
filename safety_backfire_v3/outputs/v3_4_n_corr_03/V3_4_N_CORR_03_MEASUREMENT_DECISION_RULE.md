# V3.4-N-CORR-03 — Metrology Uncertainty & Guarded Decision Rule Specification

## Milestone V3.4-N-CORR-03: Final Metrology & Acceptance Decision Closure

---

### 1. Metrological Governance Scope & Principles

In safety-critical data-acquisition and industrial vehicle instrumentation, declaring that a physical gate passes simply because a single instrument reading is numerically below a nominal limit ($\text{measured} \le \text{limit}$) is metrologically invalid. Every physical measurement contains inherent uncertainty arising from sensor calibration drift, environmental thermal variations, analog-to-digital quantization, and spatial positioning errors.

Milestone **V3.4-N-CORR-03** formally institutes **Guarded Acceptance** across all physical commissioning gates (`C1` through `C9`), conforming to **ISO 14253-1:2017** (*Geometrical product specifications — Inspection by measurement of workpieces and measuring equipment*) and **ILAC-G8:09/2019** (*Guidelines on Decision Rules and Statements of Conformity*).

```text
========================================================================================
METROLOGY POLICY:               GUARDED_ACCEPTANCE (ISO 14253-1 / ILAC-G8:09/2019)
COVERAGE FACTOR:                k = 2.0 (95.45% EXPANDED CONFIDENCE INTERVAL)
GUARD BAND SPECIFICATION:       g = U (EXPANDED UNCERTAINTY)
PERSISTENCE STATUS:             TRACTION_CURRENT_ENDPOINT_PERSISTENCE = TBD
MILESTONE DECISION STATUS:      BLOCKED (PENDING PERSISTENCE CHARACTERIZATION)
========================================================================================
```

---

### 2. Guarded Acceptance Decision Rule Theory

#### 2.1 The Problem of Consumer Risk (False Pass)
When a measured parameter approaches an acceptance limit, measurement uncertainty creates an unquantified probability of false acceptance (consumer risk):
$$\text{Measured Value} \le L \quad \text{does not guarantee} \quad \text{True Value} \le L$$

To eliminate consumer risk, Guarded Acceptance establishes an internal acceptance zone reduced by the guard band $g = U$, where $U$ is the expanded uncertainty:
$$U = k \cdot u_c \quad (k = 2.0)$$

#### 2.2 Mathematical Decision Rules

1. **Upper Specification Limit ($L$):**
   $$\text{Acceptance Zone} = \left(-\infty,\; L - U\right]$$
   - $\text{Measured Value} \le L - U \implies \mathbf{PASS}$ (Guarded Compliance)
   - $L - U < \text{Measured Value} \le L \implies \mathbf{PASS\_WITH\_DEGRADED\_MARGIN}$ (Conditional / Warning)
   - $\text{Measured Value} > L \implies \mathbf{FAIL}$ (Guarded Non-Compliance)

2. **Lower Specification Limit ($L_{\min}$):**
   $$\text{Acceptance Zone} = \left[L_{\min} + U,\; +\infty\right)$$
   - $\text{Measured Value} \ge L_{\min} + U \implies \mathbf{PASS}$

3. **Two-Sided Tolerance Band ($[L_{\min}, L_{\max}]$):**
   $$\text{Acceptance Zone} = \left[L_{\min} + U,\; L_{\max} - U\right]$$
   - $L_{\min} + U \le \text{Measured Value} \le L_{\max} - U \implies \mathbf{PASS}$

---

### 3. Gate-by-Gate Metrology and Guarded Decision Rules (C1–C9)

| Gate ID | Measurement Quantity | Instrument | Traceability Reference | Sample Size ($N$) | Expanded Uncertainty ($U, k=2$) | Nominal Limit ($L$) | Guarded Acceptance Decision Rule | Initial Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **C1_CLOCK** | Composite Skew ($\tau_{\text{comp}}$) | Keysight DSOX1204G + VN1640A | NIST-TRACEABLE-2026-Q3 | 50 | $\pm 0.50\,\text{ms}$ | $33.33\,\text{ms}$ | $\tau_{\text{comp}} \le 32.83\,\text{ms}$ | `UNVERIFIED` |
| **C2_CAMERA**| Fastener Bolt Torque | Norbar ISO 6789 Torque Wrench | DAkkS-TORQUE-2026 | 8 | $\pm 0.38\,\text{N}\cdot\text{m}$ | $9.5\,\text{N}\cdot\text{m}$ | $\text{Torque} \ge 9.12\,\text{N}\cdot\text{m} \land \text{Drops} == 0$ | `UNVERIFIED` |
| **C3_CAN** | CAN Frame Max Transit Gap | Vector CANoe VN1640A Tap | DAkkS-VECTOR-2026-04 | 90,000 | $\pm 0.20\,\text{ms}$ | $20.0\,\text{ms}$ | $\text{Gap}_{\max} \le 19.80\,\text{ms} \land \text{Monotonic}$ | `UNVERIFIED` |
| **C4_SECONDARY**| SPMT-01 Resolution at 20m | Leica DISTO D2 + OpenCV | NIST-DISTO-2026 | 9 (at 20m) | $\pm 2.5\,\text{px/m}$ | $65.0\,\text{px/m}$ | $\text{Res}_{20\text{m}} \ge 67.5\,\text{px/m} \land \text{Vis}_{36} == 36$ | `UNVERIFIED` |
| **C5_CALIBRATION**| ChArUco Reprojection RMS | Calib.io Aluminum Target | CALIB-IO-CERT-2026-09 | 50 poses | $\pm 0.08\,\text{px}$ | $1.50\,\text{px}$ | $\text{RMS} \le 1.42\,\text{px}$ (all deployed) | `UNVERIFIED` |
| **C6_GEOMETRY**| Ground Plane Residual RMS | Leica TS16 Total Station | SWISS-CAL-LEICA-2026 | 30 points | $\pm 0.40\,\text{mm}$ | $3.0\,\text{mm}$ | $\text{RMS}_{\text{plane}} \le 2.60\,\text{mm} \land \text{Monument Fixed}$ | `UNVERIFIED` |
| **C7_ILLUMINANCE**| Spatial Lux & Flicker Index | Testo 540 + Thorlabs PDA36A2 | ISO17025 / NIST-2026 | 5 points | $\pm 10.5\,\text{lux} / \pm 0.003$ | $[300, 400]\,\text{lux} / 0.05$ | Every point $\in [310.5, 389.5]\,\text{lux} \land FI \le 0.047$ | `UNVERIFIED` |
| **C8_E_STOP** | Electrical Cutoff Latency | Keysight DSO + Current Clamp | NIST-TRACEABLE-2026-Q3 | 10 traces | $\pm 1.2\,\text{ms}$ | $50.0\,\text{ms}$ | $\Delta t \le 48.8\,\text{ms} \land T_{\text{persist}} \text{ verified}$ | `BLOCKED` |
| **C9_PRIVACY** | Mic Disconnect & Legal Ledger | Microscope Audit + Ledger | LEGAL_COUNSEL_2026 | 4 cameras | $0.0$ (Deterministic) | Boolean TRUE | $\text{Mics\_Desoldered} \land \text{Agreement\_Signed}$ | `UNVERIFIED` |

---

### 4. Resolution of Ambiguity Domains

#### 4.1 C4 20-Meter Depth Threshold Resolution (Option A Policy)
A critical geometric correction is implemented: the 36 sample points are distributed across 4 depth planes ($5\,\text{m}, 10\,\text{m}, 15\,\text{m}, 20\,\text{m}$), meaning **only 9 points** ($3 \text{ lateral} \times 3 \text{ heights}$) are physically located at $20\,\text{m}$.
- **Selected Policy: OPTION A:**
  1. All 36 sample points (PT_01 through PT_36) are evaluated for **line-of-sight unoccluded visibility**.
  2. The 9 points at the $20\,\text{m}$ depth plane (PT_28 through PT_36) are evaluated for **guarded spatial resolution**:
     $$\text{Resolution}_{\text{measured}} \ge 65.0\,\text{px/m} + 2.5\,\text{px/m} = 67.5\,\text{px/m}$$
- Continuous corridor coverage remains formally classified as **`UNVERIFIED_BOUNDED_INTERPOLATION`**.

#### 4.2 C7 Spatial Illuminance Point-by-Point Acceptance
To ensure that spatial averaging does not conceal localized severe shadow zones or glare spots, Gate C7 institutes an 8-parameter structured ledger:
$$\{\text{point\_01}, \text{point\_02}, \text{point\_03}, \text{point\_04}, \text{point\_05}, \text{spatial\_mean}, \text{spatial\_min}, \text{spatial\_max}\}$$
- **Authoritative Acceptance Rule:**
  $$\mathbf{PASS} \iff \left(\text{spatial\_mean} \in [310.5, 389.5]\,\text{lux}\right) \land \left(\forall i \in [1..5],\; \text{point\_}i \in [310.5, 389.5]\,\text{lux}\right)$$
  *(If any individual point falls below $310.5\,\text{lux}$, the gate fails immediately, regardless of the spatial average).*

#### 4.3 C8 Electrical Traction Endpoint & Persistence Window Problem
The safety cutoff metric is renamed to **`ELECTRICAL_TRACTION_DEENERGIZED`** ($I_{\text{motor}} < 0.5\,\text{A}$ RMS) and decoupled from:
1. `CONTACTOR_OPEN`: Diagnostic precursor ($\le 35.0\,\text{ms}$).
2. `DC_BUS_ISOLATED`: High-voltage discharge ($V_{\text{bus}} < 50.0\,\text{V}$) requiring an independent differential probe.
3. `BRAKE_CONTROL_DEENERGIZED` vs. `MECHANICAL_BRAKE_APPLIED`: Electrical coil de-energization vs. physical shoe clamping ($15-35\,\text{ms}$ mechanical travel).
4. `VEHICLE_MOTION_STOPPED`: Kinetic vehicle stopping governed by speed encoder zero velocity.

- **Persistence Window Audit:** Inverter phase currents exhibit PWM switching ripple and zero-crossing instantaneous dips. A single sample of $I_{\text{motor}} < 0.5\,\text{A}$ does not establish sustained de-energization. In accordance with Section 8 instructions prohibiting arbitrary values:
  $$\mathbf{TRACTION\_CURRENT\_ENDPOINT\_PERSISTENCE = TBD}$$
  Because this parameter remains unclosed, Gate C8 cannot be commissioned, and the milestone status is formally set to **`BLOCKED`**.

---

### 5. Standards Applicability Conditionality

The four-tier Standards Applicability Framework is amended to enforce strict operational mode conditionality:

$$\mathbf{ISO\;3691\text{-}4:2023} = \begin{cases} 
\text{EVALUATE\_UNDER\_SCOPE}, & \text{Driverless / Automated Navigation Mode} \\
\text{OUTSIDE\_STATED\_SCOPE}, & \text{Remote-Controlled / Pendant Mode}
\end{cases}$$

- **Scope Boundary:** Scope Clause 1 of ISO 3691-4 explicitly excludes industrial trucks operated by remote control with continuous operator sight and control. Remote operations must be evaluated under ISO 3691-1 and EN 1175.
- **Zero Compliance Assertions:** Zero claims of legal, statutory, or regulatory compliance are asserted.
