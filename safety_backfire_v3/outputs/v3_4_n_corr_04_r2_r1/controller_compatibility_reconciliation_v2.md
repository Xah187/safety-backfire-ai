# V3.4-N-CORR-04-R2-R1 — Controller Compatibility & Functional Safety Governance

**Document Identifier:** `outputs/v3_4_n_corr_04_r2_r1/controller_compatibility_reconciliation_v2.md`  
**Milestone:** `V3.4-N-CORR-04-R2-R1`  
**Classification:** Powertrain Controller Compatibility & Functional Safety Governance Reconciliation  
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

Earlier milestone reports alternated between asserting an unsupported "SIL 3 / PL e" rating for the Curtis 1238E-5421 controller and claiming that the 1238E "could never control a PMSM."

Per Section 12 and Section 13 of the V3.4-N-CORR-04-R2-R1 mandate, this document:
1. Reconciles the motor controller classification: standard 1238E factory documentation specifies AC Induction control, while specialized variants (e.g. SE series or custom VCL software blocks) exist for PMAC/PMSM.
2. Refrains from ungrounded negative generalizations (we do not claim that the 1238E can *never* control a PMSM under any circumstances).
3. Establishes that for the specific testbed unit `CUR-1238E-ENG-08412`, physical evidence of a validated PMSM configuration is missing, maintaining:
   $$\mathbf{MOTOR\_CONTROLLER\_COMPATIBILITY = BLOCKED}$$
4. Reconciles functional safety claims: separates component-level sub-function ratings from vehicle-level claims, and expunges unverified SIL/PL certifications, maintaining:
   $$\mathbf{VEHICLE\_FUNCTIONAL\_SAFETY\_CLAIM = NOT\_ESTABLISHED}$$

---

## 2. Inverter Controller Motor Type Baseline

### 2.1 Factory Baseline vs. Custom Firmware
According to official Curtis Instruments documentation (*Curtis 1232E/34E/36E/38E Series AC Motor Controllers*, Document No. 177-1232E-XX):
- The standard catalog `1238E` controller is engineered and documented as an **AC Induction motor controller** utilizing Indirect Field-Oriented Control (IFOC).
- Curtis maintains separate product lines and firmware packages (such as the `1238SE` series and specialized PMSM VCL libraries) supporting Permanent Magnet AC Synchronous (PMAC/PMSM) motors.
- Therefore:
  $$\mathbf{CURTIS\_1238E\_STANDARD\_MOTOR\_TYPE = AC\_INDUCTION}$$

### 2.2 Rebuttal of Absolute Exclusion
We explicitly avoid over-claiming that "a 1238E can never control a PMSM." In industrial practice, customized OEM firmware or proprietary VCL software packages can implement synchronous $d-q$ frame control on certain 1238E hardware revisions when paired with appropriate encoder/Hall interfaces.

### 2.3 The Testbed Evidence Gap
An exhaustive inspection of the engineering assets for `BENCH-TESTBED-E04` reveals:
- No Curtis software license certificate for PMSM control.
- No encoder commutation offset angle calibration log ($\theta_{\text{offset}}$).
- No motor dynamometer commissioning report matching the $5.5\,\text{kW}$ PMSM parameters.

Therefore, because evidence does not establish that the specific testbed configuration (`1238E-5421`, OS 5.12, Build 2489, VCL `AGV_TRACTION_CORE_V34.vcl`) is a validated PMSM control platform:

$$\mathbf{MOTOR\_CONTROLLER\_COMPATIBILITY = BLOCKED}$$

---

## 3. Functional Safety Classification & Claims Audit

### 3.1 Separation of Component-Level vs. Vehicle-Level Safety Claims
A foundational principle of evidence governance is the strict separation between:
1. **Component-Level Sub-Function Ratings:** A manufacturer's declaration that an internal hardware sub-circuit (e.g. gate driver inhibit) satisfies certain SIL or PL metrics when integrated under specified conditions.
2. **Vehicle-Level Functional Safety Claims:** The overall machine safety integrity of the entire machine (E-Stop button $\to$ wiring $\to$ safety relay $\to$ contactor $\to$ inverter STO $\to$ mechanical brakes $\to$ kinetic stopping).

### 3.2 Audit Findings on Curtis 1238E Safety Documentation
1. Prior milestone drafts cited "SIL 3 / PL e" for the standalone controller. This claim is **completely ungrounded** by manufacturer documentation and is **EXPUNGED**.
2. Certain Curtis documents state that 1238E dual-microprocessor architecture can support up to EN ISO 13849-1 Category 2/3, PL d, and IEC 61508 SIL 2 for specific drive-inhibit sub-functions. However, transferring a generic PL d rating from marketing brochures to the specific `1238E-5421` unit without the manufacturer's official Safety Manual and certificate is prohibited.
3. Even if the controller possesses a component-level PL d rating, this does **NOT** constitute proof of vehicle-level functional safety.

### 3.3 Authoritative Ruling: Vehicle Safety Claim Not Established
Per Section 13 of the mandate:

$$\mathbf{VEHICLE\_FUNCTIONAL\_SAFETY\_CLAIM = NOT\_ESTABLISHED}$$

All claims of `SAFETY_CERTIFIED`, `ISO_COMPLIANT`, `PL_D`, `PL_E`, and `SIL` are **STRICTLY PROHIBITED AND WITHHELD**.

---

## 4. Final Reconciled Governance Matrix

```text
========================================================================================
CONTROLLER MODEL                  : Curtis Instruments 1238E-5421 (Serial: CUR-1238E-ENG-08412)
STANDARD MOTOR TYPE               : AC_INDUCTION
PMSM COMPATIBILITY STATUS         : MOTOR_CONTROLLER_COMPATIBILITY = BLOCKED
COMPONENT SIL/PL CLAIM            : UNVERIFIED (Expunged from baseline)
VEHICLE SAFETY CLAIM              : VEHICLE_FUNCTIONAL_SAFETY_CLAIM = NOT_ESTABLISHED
PHYSICAL CAPTURE AUTHORIZATION    : NOT_GRANTED
GOVERNANCE STATUS                 : BLOCKED_PENDING_RECONCILIATION
========================================================================================
```
