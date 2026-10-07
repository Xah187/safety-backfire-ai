# V3.4-N-CORR-04-R4 — Powertrain Identity Chain & Controller/Motor Traceability

**Document:** `outputs/v3_4_n_corr_04_r4/powertrain_identity_chain.md`  
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
MOTOR_CONTROLLER_COMPATIBILITY  = BLOCKED
VEHICLE_FUNCTIONAL_SAFETY_CLAIM = NOT_ESTABLISHED
FINAL_STATUS                    = BLOCKED
```

---

## 1. Epistemic Principles of Powertrain Traceability

To establish the physical relevance of inductive current decay ($\tau_{\text{eff}}$) and de-energization timing, the exact physical identity, electrical characteristics, and software configuration of the traction motor and inverter must be fully evidenced.

**Strict Governance Prohibitions:**
1. **No Inferences from Catalog Names:** Do **NOT** infer that `"1238E"` automatically dictates an AC induction motor control mode or precludes PMAC operation.
2. **No Feedback Presumptions:** Do **NOT** assume that a permanent magnet synchronous motor (PMSM) universally requires an absolute encoder; resolvers, Hall sensors, and incremental optical encoders with index tracks are alternative industrial configurations.
3. **No Generalization from Family Literature:** Controller family documentation (e.g. Curtis 1232E/34E/36E/38E manual) **SHALL NOT** be substituted for exact unit configuration evidence.
4. `MOTOR_CONTROLLER_COMPATIBILITY` remains `BLOCKED` until primary physical evidence resolves all dimensions.

---

## 2. Exhaustive Powertrain Identity Audit

The physical powertrain chain is audited across eighteen discrete mechanical, electrical, firmware, and parameter dimensions:

| # | Dimension | Historical Assertion in Repository | Primary Physical Evidence | Status | Impact on De-Energization Characterization |
| :-: | :--- | :--- | :---: | :---: | :--- |
| **1** | **Motor Manufacturer** | Unnamed in project records. | `MISSING` | `MISSING` | Motor OEM and design heritage cannot be verified. |
| **2** | **Motor Model Number** | Unnamed in project records. | `MISSING` | `MISSING` | Datasheet and mechanical drawings cannot be retrieved. |
| **3** | **Motor Serial Number** | Unrecorded. | `MISSING` | `MISSING` | Unit-specific traceability is zero. |
| **4** | **Motor Type** | Cited as "5.5 kW PMSM" in secondary vehicle description. | `MISSING` | `UNVERIFIED` | Fundamental motor physics (induction vs PM synchronous) unproven. |
| **5** | **Rated Power** | Stated as $5.5\,\text{kW}$. | `MISSING` | `UNVERIFIED` | Thermal and electrical operating envelope unanchored. |
| **6** | **Rated Voltage** | Unrecorded (implied 48 V – 96 V nominal DC bus). | `MISSING` | `MISSING` | Peak stator voltage and inverter modulation index unknown. |
| **7** | **Rated Base Speed** | Unrecorded. | `MISSING` | `MISSING` | Synchronous electrical frequency at base speed unknown. |
| **8** | **Pole Pair Count ($p$)** | Unrecorded. | `MISSING` | `MISSING` | Electrical-to-mechanical frequency ratio cannot be computed. |
| **9** | **Phase Resistance ($R_s$)**| Unrecorded. | `MISSING` | `MISSING` | Resistance part of electrical time constant $L/R$ is absent. |
| **10**| **Stator Inductance ($L_d, L_q$)**| Unrecorded. | `MISSING` | `MISSING` | Inductive energy storage $E = \frac{1}{2} L I^2$ cannot be modeled. |
| **11**| **Back-EMF Constant ($k_e$)**| Unrecorded. | `MISSING` | `MISSING` | Rotational voltage generation during spin-down is unknown. |
| **12**| **Controller Manufacturer**| Cited as "Curtis Instruments". | `MISSING` | `UNVERIFIED` | Manufacturer asset verification missing. |
| **13**| **Controller Exact Model** | Cited as "Curtis 1238E-5421". | `MISSING` | `UNVERIFIED` | Hardware dash-variant dictates voltage and current rating. |
| **14**| **Controller HW Revision** | Unrecorded. | `MISSING` | `MISSING` | Gate drive circuitry and internal freewheeling diode specs unknown. |
| **15**| **Controller Firmware Build**| Unrecorded. | `MISSING` | `MISSING` | Core motor control algorithms and shutdown sequences unknown. |
| **16**| **VCL / Application Logic** | Unrecorded. | `MISSING` | `MISSING` | E-Stop interlock logic (freewheel vs active brake) unverified. |
| **17**| **`Motor_Type` Parameter** | Unrecorded in configuration files. | `MISSING` | `MISSING` | Controller motor algorithm mode (Induction vs PMSM) unverified. |
| **18**| **Commutation / Sensor Mode**| Unrecorded (no encoder/Hall logs). | `MISSING` | `MISSING` | Rotor angle tracking and alignment calibration status unknown. |

---

## 3. Forensic Analysis of the Curtis 1238E Documentation Conflict

A significant conflict exists between published Curtis product literature and vehicle claims:

### 3.1 Documentation Generation Discrepancy
- **Current Official Curtis Product Catalog:** Categorizes the standard **`1238E`** series specifically as an **AC Induction motor controller**. In contrast, the **`1238SE`** and **`1238E-6xxx`** series are documented with expanded capabilities for Permanent Magnet AC (PMAC / PMSM) control.
- **Family Manuals (Legacy 1232E/34E/36E/38E Series):** Certain distributor and third-party technical reference manuals describe the broader E/SE family platform as supporting dual induction and surface permanent magnet motor algorithms, subject to factory firmware options and software licenses.

### 3.2 Epistemic Resolution
This documentation conflict cannot be resolved by debate over external PDF brochures. A controller's active motor control capability is determined by:
1. The exact hardware variant (dash number);
2. The installed OEM firmware binary;
3. The programmed internal parameter file (`.cpf` / `.iap`);
4. The custom Vehicle Control Language (`.vcl`) script.

Because zero configuration files, parameter dumps, or nameplate photographs exist in the repository, the controller's active mode remains completely unknown.

---

## 4. Physical Decay Implications: Induction vs. PMSM

The physical behavior of stator current de-energization following an E-Stop event differs drastically depending on the motor architecture:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   INVERTER E-STOP GATE SHUTDOWN                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
   [AC INDUCTION MOTOR]                             [PMSM TRACTION MOTOR]
   • Rotor field created by stator flux.             • Permanent magnets on rotor.
   • Gate shutdown collapses stator flux.            • Rotating magnets continue to
   • Rotor currents die out rapidly.                   induce back-EMF voltages:
   • Back-EMF drops to zero in tens of ms              V_bemf = k_e * omega_mech.
     as rotor time constant decays.                  • If freewheeling diodes conduct
   • Current decay is purely monotonic                  (inverter bus lower than back-EMF)
     RL decay: tau = L_sigma / R_total.                or active short-circuit occurs,
                                                       current persists indefinitely
                                                       until vehicle stops rotating!
```

### 4.1 Consequences for `tau_eff = 2.8 ms`
- If the machine is an **AC Induction Motor**, the measured decay reflects stator leakage inductance discharging through inverter freewheeling diodes into the DC link capacitor, characterized by $\tau_{\text{eff}} \approx L_{\sigma} / R$.
- If the machine is a **PMSM**, a spinning motor acts as a synchronous generator. If rotor speed $\omega_m$ is sufficiently high, back-EMF exceeds DC bus voltage, forcing rectified current through the inverter antiparallel diodes regardless of gate turn-off!
- Because neither motor electrical parameters ($R_s, L_d, L_q, k_e$) nor motor type is verified, the physical origin of $\tau_{\text{eff}} = 2.8\,\text{ms}$ cannot be attributed to any verified physical mechanism.

---

## 5. Functional Safety Governance

- **Component-Level Safety:** Claims that the Curtis 1238E provides "SIL 3 / PL e" or "PL d / SIL 2" drive inhibit are completely ungrounded in repository evidence and are formally **expunged**. 
- **Vehicle-Level Safety:** Even if component-level certificates were provided, functional safety under ISO 13849-1 / ISO 26262 requires architectural verification of the entire diagnostic coverage, dual-channel interlocks, and contactor isolation at the vehicle level. No such analysis has been conducted.

---

## 6. Powertrain Compatibility Verdict

```text
MOTOR_CONTROLLER_COMPATIBILITY          = BLOCKED
POWERTRAIN_CONFIGURATION_TRACEABILITY  = MISSING (18 of 18 dimensions)
CURTIS_1238E_ACTIVE_MOTOR_MODE          = UNRESOLVED
MOTOR_ELECTRICAL_PARAMETERS             = MISSING
COMPONENT_LEVEL_SAFETY_CLAIM            = NOT_ESTABLISHED
VEHICLE_FUNCTIONAL_SAFETY_CLAIM         = NOT_ESTABLISHED
```
