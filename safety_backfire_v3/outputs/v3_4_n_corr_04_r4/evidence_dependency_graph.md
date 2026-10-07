# V3.4-N-CORR-04-R4 — Evidence Dependency Graph

**Document:** `outputs/v3_4_n_corr_04_r4/evidence_dependency_graph.md`  
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

## 1. Overview & Architectural Pipelines

This document establishes the formal directed evidence dependency graph required to transition the persistence characterization from an internally consistent reference/analytical model into a traceable, auditable measurement evidence package.

The evidence space is structured into two independent primary causal pipelines:

### Pipeline 1: Measurement, Digitization & Signal Processing Chain
```text
[E09 Probe Identity]      [E10 Amp Identity]      [E12 Scope Identity]
         │                         │                        │
         └───────────┬─────────────┴────────────────────────┘
                     ▼
         [E15 Calibration Status]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  [E11 Amp Range]         [E14 Termination]
         │                       │
         └───────────┬───────────┘
                     ▼
         [E16 Analog Bandwidth] ──► [E17 Anti-Alias Path]
                                            │
                                            ▼
[E13 Scope Config] ───────────────► [E18 ADC Sample Rate]
                                            │
                                            ▼
[E26 SHA-256] ──► [E25 Raw Waveform] ──► [E19 Raw Sample Format]
                                            │
                                            ▼
[E20 Discrete RMS Implementation] ◄─────────┘
         │
         ├────────────────────────► [E21 RMS Timestamp Convention]
         │                                    │
         ▼                                    ▼
[E22 Threshold Scale] ───────────► [E23 Persistence Implementation]
         │                                    │
         ▼                                    ▼
[E28 Uncertainty Budget] ────────► [E29 Decision Rule] ──► [E24 Physical Endpoint]
```

### Pipeline 2: Powertrain Identity, Configuration & Physical Decay Chain
```text
[E01 Physical Motor Identity] ──────────► [E02 Motor Electrical Parameters]
         │                                               │
         │         ┌─────────────────────────────────────┘
         ▼         ▼
[E03 Controller Model] ──► [E04 Controller HW Rev] ──► [E05 Controller Firmware]
                                                              │
                                                              ▼
[E08 Commutation / Alignment] ◄── [E07 Control Mode] ◄── [E06 VCL / App Config]
                                          │
                                          ▼
                               [Physical Decay Behavior]
                                          │
                                          ▼
                               [E27 tau_eff Fit Provenance]
```

---

## 2. Evidence Classification Typology

Every piece of evidence in the repository is classified into exactly one of the following canonical types:

| Evidence Type Code | Name | Definition & Epistemic Boundary |
| :--- | :--- | :--- |
| `ANALYTICAL` | Analytical Derivation | Closed-form mathematical derivations, limits, and solutions derived from symbolic differential equations (e.g. continuous RMS piecewise models, root solving). |
| `REFERENCE_IMPLEMENTATION` | Reference Implementation | Pure-software algorithmic implementations synthesized to verify internal consistency of documentary parameter definitions against synthetic test vectors. Not historical code. |
| `HISTORICAL_REPORT` | Historical Narrative Report | Textual tables, summaries, or reports citing historical values without associated raw machine waveforms, instrument setup files, or cryptographic hashes. |
| `TRACEABLE_MEASUREMENT` | Traceable Measurement | Quantitatively calibrated measurement data directly tied to NIST/accredited laboratory calibration standards with complete uncertainty budgets. |
| `PRIMARY_MANUFACTURER_EVIDENCE` | Primary Manufacturer Evidence | Primary OEM-published datasheets, technical reference manuals, or engineering schematics directly retrieved and archived. |
| `CONFIGURATION_EVIDENCE` | Configuration Evidence | Machine-readable controller configuration dumps (`.cpf`), VCL code files, parameter archives, or oscilloscope setup files (`.dat`/`.xml`). |
| `PHYSICAL_OBSERVATION` | Direct Physical Observation | Direct sensor records captured from physical hardware with authenticated timebase, environment, and physical chain logs. |

---

## 3. Node Ledger (E01 – E29)

Below is the complete audit of all twenty-nine required evidence nodes. No node is marked `VERIFIED` unless actual repository evidence establishes it.

```text
STATUS DEFINITIONS:
  VERIFIED       = Evidence exists in the repository, has been inspected, and meets auditable traceability criteria.
  UNVERIFIED     = Artifact or citation exists in repository text, but primary provenance, label, or source is unlocated/unsubstantiated.
  MISSING        = Required evidence does not exist anywhere in the repository.
  NOT_APPLICABLE = Node is not applicable to the current system boundary.
```

### Powertrain & Controller Identity Nodes (E01 – E08)

#### Node E01: Physical motor identity
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Secondary vehicle design documentation citing a "5.5 kW PMSM" (`v3_4_n_corr_04_r3/controller_motor_compatibility_reconciliation_v3.md`).
- **DEPENDENCIES:** None.
- **BLOCKER_IMPACT:** `BLK_R3_05` (Powertrain identity). Without physical motor nameplate, serial number, and manufacturer datasheet, motor type cannot be confirmed.

#### Node E02: Motor electrical parameters
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. Phase resistance $R_s$, d/q-axis inductances $L_d, L_q$, back-EMF constant $k_e$, and pole pair count $p$ are absent.
- **DEPENDENCIES:** E01.
- **BLOCKER_IMPACT:** `BLK_R3_05`, `BLK_R3_12`. Electrical time constants $\tau = L/R$ cannot be calculated; decay mechanism cannot be physically modeled.

#### Node E03: Controller exact model
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Text string `"Curtis 1238E-5421"` in historical narrative files. No nameplate photograph, purchase record, or hardware manifest exists.
- **DEPENDENCIES:** None.
- **BLOCKER_IMPACT:** `BLK_R3_05`. Current official Curtis catalog classifies standard 1238E as AC Induction. Model variant determines hardware capability.

#### Node E04: Controller hardware revision
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. PCB revision, power silicon rating, gate driver revision, and hardware bill-of-materials are unrecorded.
- **DEPENDENCIES:** E03.
- **BLOCKER_IMPACT:** `BLK_R3_05`. Hardware revision dictates supported commutation interfaces and freewheeling diode characteristics.

#### Node E05: Controller firmware
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. Firmware build number, OS version, DSP code hash, and parameter revision are absent.
- **DEPENDENCIES:** E03, E04.
- **BLOCKER_IMPACT:** `BLK_R3_05`, `BLK_R3_13`. Controller safety architecture and drive-inhibit timing depend on specific firmware release.

#### Node E06: VCL/application software
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. Vehicle Control Language (`.vcl`) source scripts, compiled binaries, and user program logic are unarchived.
- **DEPENDENCIES:** E05.
- **BLOCKER_IMPACT:** `BLK_R3_05`. E-Stop shutdown logic (active braking vs freewheel/coast down vs STO inhibit) is implemented in VCL.

#### Node E07: Motor-control mode
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. Parameter settings for `Motor_Type` (e.g. 0=Induction, 1=PMSM), control algorithm (FOC, scalar V/Hz, d-q vector), and PWM carrier rate are absent.
- **DEPENDENCIES:** E02, E05, E06.
- **BLOCKER_IMPACT:** `BLK_R3_05`, `BLK_R3_11`. Determines whether inverter initiates active short-circuit, zero-voltage vector, or high-impedance gate turn-off.

#### Node E08: Commutation/alignment configuration
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. Encoder/Hall/resolver calibration angle, sensor type, and alignment status are completely undocumented.
- **DEPENDENCIES:** E01, E07.
- **BLOCKER_IMPACT:** `BLK_R3_05`. If PMSM is utilized, invalid alignment would produce uncontrolled torque or abnormal back-EMF decay.

---

### Measurement Instrumentation & Signal Chain Nodes (E09 – E19)

#### Node E09: Current probe identity
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Text string `"Tektronix TCP303 s/n B020194"` in `v3_4_n_corr_04_r1/instrument_chain_audit.md`. No calibration record or asset tag is in the repository.
- **DEPENDENCIES:** None.
- **BLOCKER_IMPACT:** `BLK_R3_04`, `BLK_R3_09`. Physical transducer cannot be verified as authentic.

#### Node E10: Current amplifier identity
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Text string `"Tektronix TCPA300 s/n B010482"`. No asset tag, inventory log, or calibration certificate in repository.
- **DEPENDENCIES:** None.
- **BLOCKER_IMPACT:** `BLK_R3_04`, `BLK_R3_09`. Amp-to-probe interface integrity unverified.

#### Node E11: Amplifier range
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Unresolved. TCPA300 supports only 5 A/V and 50 A/V. Historical files contradict between 5 A/V and 50 A/V for ~115 A transients (`HISTORICAL_CURRENT_SCALE = UNRESOLVED`).
- **DEPENDENCIES:** E10.
- **BLOCKER_IMPACT:** `BLK_R3_04`. Scale factor error directly invalidates threshold comparisons.

#### Node E12: Oscilloscope identity
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Text string `"Keysight DSOX1204G s/n MY58491024"`. Primary asset record missing.
- **DEPENDENCIES:** None.
- **BLOCKER_IMPACT:** `BLK_R3_09`. Digitizer identity unverified.

#### Node E13: Oscilloscope acquisition configuration
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. Scope setup file (`.setup`/`.xml`), timebase setting, memory depth, vertical attenuation, and trigger mode are unarchived.
- **DEPENDENCIES:** E12.
- **BLOCKER_IMPACT:** `BLK_R3_03`, `BLK_R3_07`. Prevents confirmation of sample acquisition parameters.

#### Node E14: Termination
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. TCPA300 requires $50\,\Omega$ termination. Scope input impedance ($50\,\Omega$ vs $1\,\text{M}\Omega$) is unrecorded (`HISTORICAL_TERMINATION_STATE = UNRESOLVED`).
- **DEPENDENCIES:** E10, E12, E13.
- **BLOCKER_IMPACT:** `BLK_R3_04`. Unterminated reflection or voltage doubling alters transfer function nonlinearly.

#### Node E15: Calibration status
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `TRACEABLE_MEASUREMENT`
- **SOURCE:** None. Calibration certificates for probe, amplifier, and oscilloscope are missing.
- **DEPENDENCIES:** E09, E10, E12.
- **BLOCKER_IMPACT:** `BLK_R3_04`, `BLK_R3_09`. Measurement chain lacks metrological traceability.

#### Node E16: Analog bandwidth
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `PRIMARY_MANUFACTURER_EVIDENCE`
- **SOURCE:** Keysight DSOX1204G published spec: base $70\,\text{MHz}$, optional $20\,\text{MHz}$ bandwidth limit filter. TCP303 spec: $15\,\text{MHz}$.
- **DEPENDENCIES:** E09, E12, E13.
- **BLOCKER_IMPACT:** `BLK_R3_03`. Actual bandwidth limit setting during historical runs is unrecorded.

#### Node E17: Anti-alias path
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** Documented claims of a "4th-order 20 kHz hardware low-pass filter" are refuted by instrument specifications. No external filter hardware exists in repository inventory.
- **DEPENDENCIES:** E13, E16.
- **BLOCKER_IMPACT:** `BLK_R3_03`. `ANTI_ALIAS_VALIDATION = BLOCKED`. Unattenuated energy between 500 kHz and 15 MHz may alias into the 1.0 MSa/s digital stream.

#### Node E18: ADC sample rate
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Asserted as $1.0\,\text{MSa/s}$ in documentation. Scope native digitizer runs at up to $2.0\,\text{GSa/s}$; whether 1 MSa/s is native, decimated, or averaged is unrecorded.
- **DEPENDENCIES:** E13, E17.
- **BLOCKER_IMPACT:** `BLK_R3_03`, `BLK_R3_07`. Timebase resolution and decimation artifacts uncharacterized.

#### Node E19: Raw sample format
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `CONFIGURATION_EVIDENCE`
- **SOURCE:** None. ADC bit depth (8-bit native, 10-bit ERES, or float32 export) and voltage quantization step $\Delta V$ are undocumented.
- **DEPENDENCIES:** E13, E18.
- **BLOCKER_IMPACT:** `BLK_R3_01`, `BLK_R3_28`. Quantization noise floor cannot be bounded.

---

### Signal Processing, Timing & Provenance Nodes (E20 – E29)

#### Node E20: Discrete RMS implementation
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `REFERENCE_IMPLEMENTATION` (for R3 reference model only); `MISSING` (for frozen production pipeline).
- **SOURCE:** `outputs/v3_4_n_corr_04_r3/discrete_rms_verification.py` is a reference model of documented parameters. The historical executable `RMS-PROC-V1.0` does not exist.
- **DEPENDENCIES:** E18, E19.
- **BLOCKER_IMPACT:** `BLK_R3_01`, `BLK_R3_02`. `RMS_IMPLEMENTATION_MISSING`. Reference model verified; frozen production executable unverified.

#### Node E21: RMS timestamp convention
- **STATUS:** `VERIFIED` (as reference specification); `MISSING` (as historical implementation).
- **EVIDENCE_TYPE:** `REFERENCE_IMPLEMENTATION`
- **SOURCE:** Formally specified in R3/R4 (`discrete_rms_index_contract.md`) as window right edge $t_k = k \cdot T_s$. Historical data source is unrecorded.
- **DEPENDENCIES:** E20.
- **BLOCKER_IMPACT:** `BLK_R3_07`. Without implementation code, historical timestamp alignment cannot be audited.

#### Node E22: Threshold scale
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Conflicting values in documentation: $0.500\,\text{A}$ (nominal), $0.410\,\text{A}$ (guarded), $0.413\,\text{A}$ (continuous), $0.460\,\text{A}$ (R1 draft).
- **DEPENDENCIES:** E11, E14, E28.
- **BLOCKER_IMPACT:** `BLK_R3_04`, `BLK_R3_10`. Thresholds are tied to an unverified current measurement scale.

#### Node E23: Persistence implementation
- **STATUS:** `VERIFIED` (as reference specification); `MISSING` (as historical implementation).
- **EVIDENCE_TYPE:** `REFERENCE_IMPLEMENTATION`
- **SOURCE:** Reference implementation `persistence_modeb_reference.py` defines 101 consecutive frames ($10.0\,\text{ms}$ at $\Delta t = 0.1\,\text{ms}$). Historical code unlocated.
- **DEPENDENCIES:** E20, E21, E22.
- **BLOCKER_IMPACT:** `BLK_R3_01`. `FROZEN_RMS_IMPLEMENTATION_VERIFIED = FALSE`.

#### Node E24: Physical endpoint measurement
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `PHYSICAL_OBSERVATION`
- **SOURCE:** None. Manifest columns `t_phys_envelope_cross_ms` were derived by subtracting $1.12\,\text{ms}$ from RMS crossings, not physically observed.
- **DEPENDENCIES:** E23, E27.
- **BLOCKER_IMPACT:** `BLK_R3_06`. `TIMING_EVIDENCE = REPORT_BASED`. Zero physical endpoint observations exist.

#### Node E25: Raw waveform provenance
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `PHYSICAL_OBSERVATION`
- **SOURCE:** None. Zero `.csv`, `.bin`, `.wfm`, or HDF5 oscillogram files exist for `CHAR_RUN_01` through `CHAR_RUN_10`.
- **DEPENDENCIES:** E13, E18.
- **BLOCKER_IMPACT:** `BLK_R3_06`. Empirical validation is not established.

#### Node E26: SHA-256 provenance
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `TRACEABLE_MEASUREMENT`
- **SOURCE:** None. All historical waveform hashes in `evidence_manifest_v3.csv` are marked `MISSING`.
- **DEPENDENCIES:** E25.
- **BLOCKER_IMPACT:** `BLK_R3_06`. Cryptographic integrity cannot be audited.

#### Node E27: tau_eff fit provenance
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `HISTORICAL_REPORT`
- **SOURCE:** Text parameter $\tau_{\text{eff}} = 2.8\,\text{ms}$. No raw decay curve, fitting window, residuals, or regression code exists in the repository.
- **DEPENDENCIES:** E25.
- **BLOCKER_IMPACT:** `BLK_R3_12`. `TAU_EFF_STATUS = DESCRIPTIVE_UNTRACEABLE_FIT`. Cannot be treated as an authoritative safety constant.

#### Node E28: Uncertainty budget
- **STATUS:** `MISSING`
- **EVIDENCE_TYPE:** `ANALYTICAL`
- **SOURCE:** Incomplete draft figures in R1 ($U = 0.087\,\text{A}$) combined unverified scale, noise, and probe tolerances via naive RSS without correlation analysis.
- **DEPENDENCIES:** E09, E10, E11, E12, E14, E15, E17, E18.
- **BLOCKER_IMPACT:** `BLK_R3_10`. `UNCERTAINTY_BUDGET = INCOMPLETE`. Guarded thresholds cannot be formally closed.

#### Node E29: Decision rule
- **STATUS:** `UNVERIFIED`
- **EVIDENCE_TYPE:** `ANALYTICAL`
- **SOURCE:** Evaluated in R3 reference model, but ungrounded in certified calibration or traceable uncertainty standards.
- **DEPENDENCIES:** E22, E23, E28.
- **BLOCKER_IMPACT:** `BLK_R3_10`, `BLK_R3_13`. Guarded threshold acceptance rules cannot be certified.

---

## 4. Summary Matrix of Nodes

| Node ID | Description | Status | Evidence Type | Blocker Impact |
| :---: | :--- | :---: | :--- | :---: |
| **E01** | Physical motor identity | `UNVERIFIED` | `HISTORICAL_REPORT` | `BLK_R3_05` |
| **E02** | Motor electrical parameters | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_05` |
| **E03** | Controller exact model | `UNVERIFIED` | `HISTORICAL_REPORT` | `BLK_R3_05` |
| **E04** | Controller hardware revision | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_05` |
| **E05** | Controller firmware | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_05` |
| **E06** | VCL/application software | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_05` |
| **E07** | Motor-control mode | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_05` |
| **E08** | Commutation/alignment config | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_05` |
| **E09** | Current probe identity | `UNVERIFIED` | `HISTORICAL_REPORT` | `BLK_R3_04` |
| **E10** | Current amplifier identity | `UNVERIFIED` | `HISTORICAL_REPORT` | `BLK_R3_04` |
| **E11** | Amplifier range | `MISSING` | `HISTORICAL_REPORT` | `BLK_R3_04` |
| **E12** | Oscilloscope identity | `UNVERIFIED` | `HISTORICAL_REPORT` | `BLK_R3_09` |
| **E13** | Oscilloscope acquisition config | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_03` |
| **E14** | Termination | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_04` |
| **E15** | Calibration status | `MISSING` | `TRACEABLE_MEASUREMENT` | `BLK_R3_04` |
| **E16** | Analog bandwidth | `UNVERIFIED` | `PRIMARY_MANUFACTURER_EVIDENCE` | `BLK_R3_03` |
| **E17** | Anti-alias path | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_03` |
| **E18** | ADC sample rate | `UNVERIFIED` | `HISTORICAL_REPORT` | `BLK_R3_03` |
| **E19** | Raw sample format | `MISSING` | `CONFIGURATION_EVIDENCE` | `BLK_R3_01` |
| **E20** | Discrete RMS implementation | `MISSING` | `REFERENCE_IMPLEMENTATION` | `BLK_R3_01` |
| **E21** | RMS timestamp convention | `VERIFIED`* | `REFERENCE_IMPLEMENTATION` | `BLK_R3_07` |
| **E22** | Threshold scale | `UNVERIFIED` | `HISTORICAL_REPORT` | `BLK_R3_10` |
| **E23** | Persistence implementation | `VERIFIED`* | `REFERENCE_IMPLEMENTATION` | `BLK_R3_01` |
| **E24** | Physical endpoint measurement | `MISSING` | `PHYSICAL_OBSERVATION` | `BLK_R3_06` |
| **E25** | Raw waveform provenance | `MISSING` | `PHYSICAL_OBSERVATION` | `BLK_R3_06` |
| **E26** | SHA-256 provenance | `MISSING` | `TRACEABLE_MEASUREMENT` | `BLK_R3_06` |
| **E27** | tau_eff fit provenance | `UNVERIFIED` | `HISTORICAL_REPORT` | `BLK_R3_12` |
| **E28** | Uncertainty budget | `MISSING` | `ANALYTICAL` | `BLK_R3_10` |
| **E29** | Decision rule | `UNVERIFIED` | `ANALYTICAL` | `BLK_R3_10` |

*\* Note: E21 and E23 are VERIFIED solely as internal specifications for the synthetic R3 reference model (`persistence_modeb_reference.py`). For the historical production pipeline, their status remains `MISSING`.*

---

## 5. Epistemic Conclusion

Out of 29 critical evidence nodes:
- **`VERIFIED` (Historical Physical/Production):** `0`
- **`VERIFIED` (Internal Reference Spec Only):** `2`
- **`UNVERIFIED` (Narrative / Secondary Citations):** `8`
- **`MISSING` (Completely Absent):** `19`

Because zero physical measurement or powertrain configuration nodes are verified, the characterization pipeline remains blocked. Internal consistency of analytical models cannot substitute for physical evidence closure.
