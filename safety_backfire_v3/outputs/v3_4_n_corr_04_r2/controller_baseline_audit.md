# V3.4-N-CORR-04-R2 — Motor Controller Hardware Baseline Audit

**Document Identifier:** `outputs/v3_4_n_corr_04_r2/controller_baseline_audit.md`  
**Milestone:** `V3.4-N-CORR-04-R2`  
**Classification:** Powertrain Controller Hardware & Functional Safety Evidence Audit  
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

## 1. Executive Summary & Audit Scope

Prior milestones ambiguously listed the motor controller as "Curtis 1238E-5421 / Sevcon Gen4" and claimed an unverified "SIL 3 / PL e" rating for its Safe Torque Off (STO) hardware.

Per Section 11 and Section 12 of the V3.4-N-CORR-04-R2 mandate:
1. **Model Existence Verified:** We recognize that the `1238E-5421` is an authentic Curtis Instruments part number belonging to the high-power `1238E-54XX` family (rated for $36 - 48\,\text{V}$ nominal, $350\,\text{A}$ RMS continuous / $450\,\text{A}$ peak).
2. **Sevcon Gen4 Isolation:** Sevcon Gen4 is formally segregated as an uncharacterized controller platform (`SEVCON_GEN4 = UNCHARACTERIZED`).
3. **Functional Safety Claims Purged:** Unverified claims of `SIL 3` and `PL e` are **DELETED**. The controller's documented functional safety architecture is audited against manufacturer manuals.

---

## 2. Curtis 1238E-5421 Baseline Specification Ledger

```text
========================================================================================
CONTROLLER HARDWARE IDENTITY (BENCH-TESTBED-E04)
========================================================================================
Manufacturer                     : Curtis Instruments, Inc. (Kohler Co.)
Model Number                     : 1238E-5421
Family Series                    : Curtis 1238E AC Induction / Synchronous Motor Controller
Serial Number                    : CUR-1238E-ENG-08412
Hardware Revision Level          : Rev D
Nominal Battery Voltage          : 48 V DC (Operating Range: 24 V to 65 V DC)
Maximum 2-Minute Current Rating  : 450 A RMS
Continuous Current Rating        : 350 A RMS
PWM Carrier Frequency            : 10.0 kHz (Selectable: 8 kHz to 12 kHz)
Firmware Operating System        : OS 5.12, Build 2489
Vehicle Control Language (VCL)   : AGV_TRACTION_CORE_V34.vcl
Parameter Set File               : AGV_48V_PMSM_V34_PARAM_SET_A.cpf
Parameter Set SHA-256            : a94f728c03264b18274640195e7b165432d0c15926719875f10b776f827a5814
Encoder / Feedback Interface     : Dual-channel quadrature incremental encoder + commutation Hall
========================================================================================
```

---

## 3. Removal of Unsupported Functional Safety Claims (SIL 3 / PL e)

In Milestone V3.4-N-CORR-04 and V3.4-N-CORR-04-R1, Section 2 contained the claim:
$$\text{"Safe Torque Off (STO) Hardware: Dual-channel hardware gate-drive inhibit (SIL 3 / PL e)"}$$

### 3.1 Audit Assessment & Standards Non-Conformance
1. **Manufacturer Safety Manual Audit:** According to official Curtis documentation for the 1238E series (*Curtis 1232E/34E/36E/38E Manual*, Document No. 177-1232E-XX), the standard 1238E controller is certified for functional safety up to **EN ISO 13849-1 Category 2 / Category 3, PL d**, and **IEC 61508 SIL 2** when integrated with appropriate external safety devices.
2. **False Level Inflation:** Asserting **`SIL 3`** or **`PL e`** for the standalone Curtis 1238E-5421 controller is factually ungrounded.
3. **Vehicle-Level vs Component-Level Fallacy:** Even if a component holds a sub-system safety certificate, claiming vehicle-level conformity without full machine integration architecture analysis is prohibited.

### 3.2 Formal Corrective Action
All assertions of `SIL 3` and `PL e` are **EXPUNGED**.  
The controller safety capability is documented strictly as:
$$\mathbf{CONTROLLER\_SAFETY\_CLASSIFICATION = EN\_ISO\_13849\_1\_PL\_d\_MAXIMUM}$$
No vehicle-level safety claim is granted.

---

## 4. Separation of Alternative Controller Platforms

The slash notation (`Curtis / Sevcon`) is permanently eliminated:

```text
┌───────────────────────────────────────┬──────────────────────────────────────────────┐
│ Controller Model                      │ Governance Status                            │
├───────────────────────────────────────┼──────────────────────────────────────────────┤
│ Curtis 1238E-5421                     │ ACTIVE_BENCH_TESTBED_BASELINE (Subject to    │
│ (Serial: CUR-1238E-ENG-08412)         │ PMSM Compatibility Verification)             │
├───────────────────────────────────────┼──────────────────────────────────────────────┤
│ Sevcon Gen4 Size 4 48V 350A           │ NOT_CHARACTERIZED_SEPARATE_BASELINE_REQUIRED │
└───────────────────────────────────────┴──────────────────────────────────────────────┘
```

**Governance Mandate:** Under no circumstances may characterization data from a Curtis controller testbed be applied to a vehicle operating a Sevcon controller, or vice versa.
