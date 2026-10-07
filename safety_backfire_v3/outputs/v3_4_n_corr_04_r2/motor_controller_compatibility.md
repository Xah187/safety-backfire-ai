# V3.4-N-CORR-04-R2 — Motor / Inverter Controller Compatibility Audit

**Document Identifier:** `outputs/v3_4_n_corr_04_r2/motor_controller_compatibility.md`  
**Milestone:** `V3.4-N-CORR-04-R2`  
**Classification:** Electrical Powertrain Compatibility & Firmware Functionality Audit  
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

## 1. The Core Engineering Discrepancy

The physical traction motor installed on `AGV-RES-TRUCK-01` is:
$$\mathbf{5.5\,kW \quad 48\,V \quad \text{3-Phase AC Permanent Magnet Synchronous Motor (PMSM)}}$$

However, official Curtis Instruments documentation (*Curtis 1232E/34E/36E/38E Manual*, Document 177-1232E-XX) explicitly classifies the baseline `1238E` controller family as:
$$\text{"AC Induction Motor Controllers with Indirect Field-Oriented Control (IFOC)"}$$

Per Section 11 of the V3.4-N-CORR-04-R2 mandate, we must independently establish compatibility between the Curtis 1238E-5421 controller and a 48V PMSM motor. If compatibility cannot be verified from evidence:
$$\mathbf{MOTOR\_CONTROLLER\_COMPATIBILITY = BLOCKED}$$

---

## 2. Technical Compatibility Analysis: Induction vs. Synchronous Control

Operating an AC Induction motor vs. a Permanent Magnet Synchronous Motor requires fundamentally different control and modulation architectures:

| Functional Domain | AC Induction Motor (ACIM) | Permanent Magnet Synchronous Motor (PMSM) | Curtis 1238E Standard Baseline |
| :--- | :--- | :--- | :--- |
| **Rotor Magnetic Field** | Induced via stator slip current ($\omega_s = \omega_e - \omega_r$) | Fixed NdFeB permanent magnets on rotor | ACIM slip control natively supported |
| **Commutation Alignment** | No absolute rotor angle required; incremental encoder tracks relative speed | **Strict absolute rotor angle alignment required** (resolver or UVW Hall + encoder) | Standard 1238E firmware lacks native absolute resolver decoding without add-on board |
| **Torque Control Law** | Rotor flux orientation ($i_{ds}$ magnetizing, $i_{qs}$ torque) | Synchronous $d-q$ frame ($i_d = 0$ or MTPA trajectory, $T_e = \frac{3}{2} p \lambda_m i_q$) | Standard firmware implements induction IFOC |
| **Freewheeling Dynamics** | Stator flux collapses as rotor demagnetizes naturally | **Rotor permanent magnets continue spinning**, generating back-EMF ($E_g = \omega_e \lambda_m$) | Antiparallel diodes freewheel back-EMF directly into DC link capacitor bus |
| **Safe Torque Off (STO) Clamping** | Disabling gate drives eliminates stator current; motor coasts freely | Disabling gate drives cuts active inverter torque, but **spinning rotor generates back-EMF** | If rotor speed $\omega_e > V_{\text{bus}} / \lambda_m$, diodes rectify into bus, maintaining stator current |

---

## 3. Firmware Configuration & Parameter Ledger Audit

In Curtis documentation, PMSM support on the "E" series requires either:
1. The specialized **`1238SE`** hardware variant, OR
2. A customized Curtis Vehicle Control Language (VCL) build incorporating the proprietary Curtis PMAC/PMSM motor control software block.

### 3.1 Audit of Bench Testbed Configuration Files
An audit of `BENCH-TESTBED-E04` configuration files reveals:
- Controller Model: `1238E-5421` (Standard "E" hardware, NOT "SE")
- Firmware: OS 5.12, Build 2489
- VCL Application File: `AGV_TRACTION_CORE_V34.vcl`
- Motor Parameter Block: Cites `Motor_Type = 2` (AC Induction).
- Parameter Set Hash: `a94f728c03264b18274640195e7b165432d0c15926719875f10b776f827a5814`

### 3.2 Finding: Lack of Validated PMSM Commutation Profile
1. The configuration ledger in the repository **does not contain** an audited rotor position offset calibration, cross-coupling inductance map ($L_d, L_q$), or back-EMF constant parameter set for the $5.5\,\text{kW}$ PMSM.
2. Attempting to characterize E-Stop current decay on a PMSM driven by an induction motor parameter profile introduces uncontrolled freewheeling diode conduction and invalidates the claimed $\tau_{\text{eff}} \approx 2.8\,\text{ms}$ decay dynamics.

---

## 4. Formal Audit Determination

Because documented evidence fails to establish that controller `CUR-1238E-ENG-08412` has been flashed, configured, and dyno-calibrated with an approved PMSM control package:

$$\mathbf{MOTOR\_CONTROLLER\_COMPATIBILITY = BLOCKED}$$

$$\mathbf{V3\_4\_N\_CORR\_04\_R2\_STATUS = BLOCKED\_PENDING\_RECONCILIATION}$$

**Required Corrective Actions for Unblocking:**
1. Document whether the physical motor on `BENCH-TESTBED-E04` is an AC Induction or a PMSM motor.
2. If PMSM, provide the official Curtis PMSM software license certificate, resolver/encoder commutation alignment report, and motor dynamometer commissioning certificate.
3. If AC Induction, correct all vehicle documentation to remove the PMSM designation.
