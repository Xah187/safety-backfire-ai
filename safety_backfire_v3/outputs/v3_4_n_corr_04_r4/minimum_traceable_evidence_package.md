# V3.4-N-CORR-04-R4 — Minimum Traceable Evidence Package Specification

**Document:** `outputs/v3_4_n_corr_04_r4/minimum_traceable_evidence_package.md`  
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
FINAL_STATUS                    = BLOCKED
```

---

## 1. Scope & Objective

This specification establishes the **minimum physical, metrological, and software evidence package** that must exist in the repository before any future characterization campaign may be submitted for engineering audit or closure review.

**Requirement Classification Tags:**
- `REQUIRED_FOR_TRACEABILITY`: Mandatory to establish an unbroken calibration and custodial chain of evidence.
- `REQUIRED_FOR_MODEL_RELEVANCE`: Mandatory to prove that the measurement corresponds to the physical motor/controller equations.
- `REQUIRED_FOR_TIMING_CLOSURE`: Mandatory to bound and verify timebase, trigger, and latency parameters.
- `OPTIONAL`: Recommended for audit defense but not strictly required to close core metrological blockers.

---

## 2. Evidence Package Categories (A – K)

### Category A: Instrument Identity
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **A1** | **Current Probe Asset Record:** Tektronix TCP303 nameplate photo, serial number, and repository asset registration. | `REQUIRED_FOR_TRACEABILITY` | Anchors the primary magnetic transducer identity. |
| **A2** | **Current Amplifier Asset Record:** Tektronix TCPA300 nameplate photo, serial number, and asset registration. | `REQUIRED_FOR_TRACEABILITY` | Anchors the amplifier electronics identity. |
| **A3** | **Oscilloscope Asset Record:** Keysight DSOX1204G nameplate photo, serial number, and asset registration. | `REQUIRED_FOR_TRACEABILITY` | Anchors the digitizer hardware platform. |
| **A4** | **Installed Hardware/Software Options:** Screen capture or report of oscilloscope installed license options (e.g. DSOX1B100 bandwidth upgrade). | `REQUIRED_FOR_TRACEABILITY` | Determines actual analog channel bandwidth. |

---

### Category B: Metrological Calibration
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **B1** | **Current Probe Calibration Certificate:** Calibration record showing DC gain, frequency response, and date of calibration. | `REQUIRED_FOR_TRACEABILITY` | Bounds probe transconductance error. |
| **B2** | **Amplifier Calibration Certificate:** TCPA300 calibration certificate verifying gain accuracy on $5\,\text{A/V}$ and $50\,\text{A/V}$ ranges. | `REQUIRED_FOR_TRACEABILITY` | Eliminates uncalibrated transducer gain drift. |
| **B3** | **Oscilloscope Calibration Certificate:** Digitizer vertical gain accuracy and timebase calibration certificate. | `REQUIRED_FOR_TRACEABILITY` | Establishes voltage and timebase traceability. |
| **B4** | **Pre-Test Degauss / Autobalance Log:** Operator log documenting execution and pass result of TCPA300 Degauss/AutoBalance routine prior to test. | `REQUIRED_FOR_TRACEABILITY` | Ensures residual core magnetization and DC offset are zeroed. |

---

### Category C: Signal Path & Hardware Coupling
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **C1** | **Amplifier Range Switch Setting Record:** Machine-readable or photographic verification of TCPA300 range switch position ($5\,\text{A/V}$ or $50\,\text{A/V}$) per trial. | `REQUIRED_FOR_TRACEABILITY`  <br>`REQUIRED_FOR_MODEL_RELEVANCE` | Unambiguously establishes Volts-to-Amperes transfer factor. |
| **C2** | **Channel Termination Verification:** Record of oscilloscope input impedance and part/serial number of external $50\,\Omega$ feedthrough terminator. | `REQUIRED_FOR_TRACEABILITY` | Prevents $\times 2$ voltage scaling error and transmission line reflection. |
| **C3** | **Signal Cabling Specification:** Cable type (e.g. RG-58 50 $\Omega$), length, and connector integrity verification. | `REQUIRED_FOR_TRACEABILITY` | Eliminates unmodeled cable capacitance and phase delay. |
| **C4** | **Analog Bandwidth Limit State:** Documented state of oscilloscope channel $20\,\text{MHz}$ bandwidth limit filter (ON/OFF). | `REQUIRED_FOR_TRACEABILITY`  <br>`REQUIRED_FOR_MODEL_RELEVANCE` | Defines pre-ADC analog frequency cutoff. |
| **C5** | **Out-of-Band Spectral Scan:** High-rate spectral capture (up to $50\,\text{MHz}$) verifying that inverter switching energy above $500\,\text{kHz}$ is negligible. | `REQUIRED_FOR_MODEL_RELEVANCE` | Closes anti-aliasing validation (`BLK_R3_03`). |

---

### Category D: Raw Machine Waveforms
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **D1** | **Raw Waveform Files:** Unprocessed time-series data exported directly from digitizer memory (`.csv`, `.bin`, or `.h5`) without post-processing. | `REQUIRED_FOR_TRACEABILITY`  <br>`REQUIRED_FOR_TIMING_CLOSURE` | Primary empirical basis; allows independent re-execution. |
| **D2** | **Cryptographic Hash Manifest:** Immutable SHA-256 hash manifest locking every raw waveform file immediately upon export. | `REQUIRED_FOR_TRACEABILITY` | Guarantees non-repudiation and data integrity. |
| **D3** | **Synchronized Auxiliary Waveforms:** Raw trace of E-Stop switch contact voltage and contactor auxiliary feedback channel. | `REQUIRED_FOR_TIMING_CLOSURE` | Establishes physical actuator de-energization timing. |

---

### Category E: Acquisition Metadata
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **E1** | **Oscilloscope Setup File:** Machine-readable binary or XML setup file (`.setup`) exported from the oscilloscope for each trial run. | `REQUIRED_FOR_TRACEABILITY` | Captures complete internal state of the digitizer. |
| **E2** | **Timebase Setting Record:** Explicit record of horizontal scale ($\text{s/div}$), timebase reference point, and delay. | `REQUIRED_FOR_TIMING_CLOSURE` | Validates timebase resolution. |
| **E3** | **Vertical Channel Configuration:** Vertical sensitivity ($\text{V/div}$), vertical offset, and coupling (DC) per channel. | `REQUIRED_FOR_TRACEABILITY` | Allows calculation of exact LSB quantization resolution. |
| **E4** | **Acquisition Mode Record:** Documented mode setting (`Normal`, `High-Res`, `Averaging`, `Peak Detect`) and native ADC rate. | `REQUIRED_FOR_MODEL_RELEVANCE` | Eliminates decimation and filtering ambiguity. |
| **E5** | **Buffer Memory Depth Record:** Total sample points acquired per channel. | `REQUIRED_FOR_TRACEABILITY` | Ensures acquisition buffer did not truncate or wrap around. |

---

### Category F: Discrete RMS Software Implementation
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **F1** | **Executable DSP Implementation:** Python/C source module committed to `scripts/` adhering to `discrete_rms_index_contract.md`. | `REQUIRED_FOR_TRACEABILITY`  <br>`REQUIRED_FOR_TIMING_CLOSURE` | Provides actual executable pipeline (replaces missing pipeline). |
| **F2** | **Cryptographic Code Hash:** Recorded SHA-256 hash of the operational RMS script locked in production baseline. | `REQUIRED_FOR_TRACEABILITY` | Proves algorithm invariance across trials. |
| **F3** | **Unit Test Verification Suite:** Automated test suite verifying execution against standardized synthetic test vectors. | `REQUIRED_FOR_MODEL_RELEVANCE` | Proves code correctness before physical processing. |

---

### Category G: Powertrain Identity & Configuration
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **G1** | **Motor Nameplate Photograph:** Clear photograph showing OEM nameplate, model, serial number, and ratings. | `REQUIRED_FOR_MODEL_RELEVANCE` | Proves physical motor identity. |
| **G2** | **Motor Electrical Parameters:** Manufacturer datasheet certifying phase resistance $R_s$, inductances $L_d, L_q$, and $k_e$. | `REQUIRED_FOR_MODEL_RELEVANCE` | Provides physical basis for electrical time constant $L/R$. |
| **G3** | **Controller Nameplate Photograph:** Clear photograph showing Curtis model number, dash number, and serial number. | `REQUIRED_FOR_MODEL_RELEVANCE` | Proves physical controller identity. |
| **G4** | **Firmware Version Record:** Diagnostic software screen capture showing installed controller firmware build. | `REQUIRED_FOR_MODEL_RELEVANCE` | Anchors controller control algorithms and safety architecture. |
| **G5** | **Controller Parameter Archive:** Machine-readable parameter export file (`.cpf`) containing all programmed settings. | `REQUIRED_FOR_MODEL_RELEVANCE` | Proves active `Motor_Type` and PWM carrier frequency. |
| **G6** | **Vehicle Control Language (VCL) Program:** Source code or compiled binary of VCL script governing E-Stop shutdown. | `REQUIRED_FOR_MODEL_RELEVANCE` | Proves whether inverter executes active short or freewheel. |
| **G7** | **Commutation Alignment Log:** Documented rotor position sensor alignment calibration procedure and results. | `REQUIRED_FOR_MODEL_RELEVANCE` | Verifies correct field-oriented control operation. |

---

### Category H: Timing, Synchronization & Clocks
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **H1** | **Timebase Accuracy Specification:** Digitizer crystal oscillator tolerance and calibration data ($\pm \text{ppm}$). | `REQUIRED_FOR_TIMING_CLOSURE` | Bounds long-term timebase drift. |
| **H2** | **Trigger Pick-off Schematic:** Circuit schematic showing how E-Stop switch or contactor state is coupled to scope trigger. | `REQUIRED_FOR_TIMING_CLOSURE` | Proves trigger electrical isolation and bandwidth. |
| **H3** | **Contactor Contact Bounce Record:** Measured latency and bounce duration of mechanical contactor auxiliary switches. | `REQUIRED_FOR_TIMING_CLOSURE` | Eliminates trigger timestamp uncertainty ($t=0$). |
| **H4** | **Cross-Channel Deskew Calibration:** Calibration record documenting channel-to-channel deskew alignment. | `REQUIRED_FOR_TIMING_CLOSURE` | Eliminates probe cable propagation delay skew. |

---

### Category I: Uncertainty Budget & Decision Rule
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **I1** | **GUM-Compliant Uncertainty Budget:** Formal calculation of combined expanded uncertainty ($k=2$) across all 6 domains. | `REQUIRED_FOR_TRACEABILITY`  <br>`REQUIRED_FOR_MODEL_RELEVANCE` | Provides metrological defense for threshold acceptance. |
| **I2** | **Sensitivity & Correlation Analysis:** Derivation of sensitivity coefficients and covariance terms between gain and time. | `REQUIRED_FOR_TRACEABILITY` | Replaces invalid naive RSS calculations. |
| **I3** | **Governed Decision Rule Specification:** Formal document establishing acceptance zone and guard band limits. | `REQUIRED_FOR_MODEL_RELEVANCE` | Closes decision boundary authority (`BLK_R3_10`). |

---

### Category J: Trial Provenance & Execution Context
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **J1** | **Controlled Test Procedure:** Formal test protocol with version control, sign-offs, and hazardous energy control rules. | `REQUIRED_FOR_TRACEABILITY` | Ensures test repeatability and laboratory safety. |
| **J2** | **Operator Logbook:** Signed, dated operator log recording ambient temperature, relative humidity, and run sequence. | `REQUIRED_FOR_TRACEABILITY` | Provides human custodial chain of evidence. |
| **J3** | **Bench Setup Photographs:** Photographic documentation of the physical testbed, transducer placement, and grounding. | `REQUIRED_FOR_TRACEABILITY` | Proves physical transducer geometry and noise shielding. |
| **J4** | **Pre-Event Motor Telemetry:** Recorded rotor speed, stator winding temperature, and DC bus voltage immediately prior to E-Stop. | `REQUIRED_FOR_MODEL_RELEVANCE` | Provides exact boundary conditions for Region 2/3 model. |

---

### Category K: Reviewer & Adjudication Evidence
| Item ID | Evidence Description | Requirement Tag | Objective Justification |
| :--- | :--- | :--- | :--- |
| **K1** | **Independent Metrology Review:** Formal sign-off report by an independent, qualified measurement engineer. | `REQUIRED_FOR_TRACEABILITY` | Validates compliance with ISO/IEC 17025 principles. |
| **K2** | **Anomaly & Deviation Log:** Formal log documenting any unexpected hardware resets, clipping, or trigger jitter. | `REQUIRED_FOR_TRACEABILITY` | Ensures negative evidence is not suppressed. |
| **K3** | **Calibration Laboratory Scope:** ISO/IEC 17025 certificate of accreditation for external calibration facilities. | `OPTIONAL` | Enhances formal auditability of calibration chain. |
| **K4** | **Video Recording of Test Execution:** Synchronized video recording of instrument display and motor dyno bench. | `OPTIONAL` | Qualitative corroboration of physical test execution. |

---

## 3. Evidence Package Completeness Rule

No gate transition from `NOT_READY` to `READY_FOR_ENGINEERING_REVIEW` may occur until **100% of items tagged with `REQUIRED_*`** are physically present in the repository, hashed, and verified.
