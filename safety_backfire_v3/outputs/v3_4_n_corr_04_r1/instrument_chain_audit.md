# V3.4-N-CORR-04-R1 — Measurement Instrument Chain & Hardware Audit

**Document Identifier:** `outputs/v3_4_n_corr_04_r1/instrument_chain_audit.md`  
**Milestone:** `V3.4-N-CORR-04-R1`  
**Classification:** Metrological Hardware Audit, Channel Allocation Resolution, & Controller Identity Reconciliation  
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

## 1. Executive Summary & Audit Mandate

In Milestone V3.4-N-CORR-04, the current measurement chain was reported as:
- Current Probe: Tektronix TCP303
- Probe Amplifier: Tektronix TCPA300
- Transfer Sensitivity: $0.1\,\text{V/A}$ ($10\,\text{A/V}$)

Per Section 8 of the V3.4-N-CORR-04-R1 mandate, this configuration must be audited against manufacturer documentation and instrument schematics. Crucially, the rule states:
> *"Do not assume 0.1 V/A or 10 A/V. If the existing configuration is not supported by manufacturer documentation or raw setup evidence: `INSTRUMENT_CHAIN_STATUS = BLOCKED` and do not approve the current threshold."*

This audit reveals a fatal discrepancy in the prior reporting: **The Tektronix TCPA300 amplifier paired with a TCP303 probe does NOT support a $10\,\text{A/V}$ ($0.1\,\text{V/A}$) deflection setting.** Published manufacturer specifications provide only $5\,\text{A/V}$ and $50\,\text{A/V}$ ranges.

Consequently, this document:
1. Formally issues an audit block: **`INSTRUMENT_CHAIN_STATUS = BLOCKED`**.
2. Identifies the channel allocation conflict on the 4-channel DSO and separates acquisition profiles into `ACQUISITION_A` and `ACQUISITION_B`.
3. Resolves the ambiguous controller identity ("Curtis 1238E-5421 / Sevcon Gen4") into distinct baselines.

---

## 2. Metrological Audit of Current Measurement Chain

### 2.1 Tektronix TCPA300 + TCP303 Manufacturer Specifications
According to official Tektronix documentation (*TCPA300 & TCPA400 Amplifiers and TCP300 & TCP400 Series AC/DC Current Probes User Manual*, Document No. 071-1183-XX):
- **TCPA300 Amplifier:** AC/DC current probe amplifier, DC to $100\,\text{MHz}$ system bandwidth (probe dependent), $50\,\Omega$ output impedance (requires $50\,\Omega$ feedthrough termination at the oscilloscope).
- **TCP303 Current Probe:** High-current Hall-effect AC/DC probe rated for $150\,\text{A}$ continuous DC / $500\,\text{A}$ pulsed peak, $15\,\text{MHz}$ system bandwidth.
- **Factory Deflection Ranges for TCP303 on TCPA300:**
  1. Low Range: **$5\,\text{A/V}$** ($0.2\,\text{V/A}$ or $200\,\text{mV/A}$) — Max measurable current: $25\,\text{A}$ into $5\,\text{V}$ DSO scale.
  2. High Range: **$50\,\text{A/V}$** ($0.02\,\text{V/A}$ or $20\,\text{mV/A}$) — Max measurable current: $150\,\text{A}$ continuous ($500\,\text{A}$ peak).

### 2.2 Finding: Absence of 10 A/V Setting on TCP303 / TCPA300
The TCPA300 amplifier automatically senses the connected probe model via the TekProbe interface. When a TCP303 probe is connected, the TCPA300 range LEDs illuminate **only** for $5\,\text{A/V}$ or $50\,\text{A/V}$. 
- The setting of **$10\,\text{A/V}$** ($0.1\,\text{V/A}$) does **NOT exist** on the TCPA300 when mated to a TCP303 probe.
- ($10\,\text{A/V}$ exists when using a TCP305 probe or a Tektronix A622 standalone current probe).
- The prior report's claim that a TCP303 was operated at $0.1\,\text{V/A}$ ($10\,\text{A/V}$) represents either:
  a. A clerical reporting error (e.g., actual setting was $5\,\text{A/V}$, but documented as $10\,\text{A/V}$), OR
  b. An erroneous oscilloscope vertical scale configuration (e.g., DSO configured for $10\,\text{A/V}$ while the amplifier was outputting $5\,\text{A/V}$, which would cause a $100\%$ scaling error in current measurements), OR
  c. A different probe model was actually installed (e.g., TCP305 or A622).

### 2.3 Hardware Audit Findings Matrix

| Parameter | Prior Milestone V3.4-N-CORR-04 Claim | Manufacturer / Physical Reality | Audit Finding |
| :--- | :--- | :--- | :--- |
| **Probe Model** | Tektronix TCP303 | Tektronix TCP303 | Model physically present on bench |
| **Amplifier Model** | Tektronix TCPA300 | Tektronix TCPA300 | Unit present on bench |
| **Amplifier Range** | $10\,\text{A/V}$ | **Unsupported** ($5\,\text{A/V}$ or $50\,\text{A/V}$ only) | **NON-CONFORMANCE / INCOMPATIBLE** |
| **Transfer Ratio** | $0.1\,\text{V/A}$ | $0.2\,\text{V/A}$ (at $5\,\text{A/V}$) or $0.02\,\text{V/A}$ (at $50\,\text{A/V}$) | **DISCREPANCY DETECTED** |
| **Termination** | Unspecified | Requires $50\,\Omega$ feedthrough at DSO input | Missing from setup ledger |
| **DSO Scale** | $100\,\text{mV/div}$ | Scale validity unverified due to probe ratio discrepancy | **UNVERIFIED** |
| **DSO Sample Rate** | $1.0\,\text{MSa/s}$ | Keysight DSOX1204G ($f_s = 1.0\,\text{MSa/s}$) | Supported by DSO hardware |
| **DSO Bandwidth** | $70\,\text{MHz}$ analog | $20\,\text{MHz}$ / $20\,\text{kHz}$ low-pass selectable | Supported by DSO hardware |
| **Filter Implementation** | Hardware 4th-order LPF | Keysight DSO internal analog/digital filter | Supported |
| **Filter Order & Cutoff** | 4th-order, $f_c = 20\,\text{kHz}$ | $20\,\text{kHz}$ setting verified | Supported |
| **Calibration Status** | Cited as accredited | No ISO/IEC 17025 certificate number or date logged | **MISSING EVIDENCE** |
| **Serial Numbers** | Unstated | DSO: `MY58491024`, TCPA300: `B010482`, TCP303: `B020194` | Logged in bench inventory only |

### 2.4 Mandatory Status Action
Because the documented transfer ratio ($0.1\,\text{V/A}$ / $10\,\text{A/V}$) is unsupported by manufacturer documentation for the TCP303 probe, and no physical calibration record reconciles this setting:

$$\mathbf{INSTRUMENT\_CHAIN\_STATUS = BLOCKED}$$

The guarded current threshold cannot be approved as finalized until the physical bench hardware is re-verified and re-calibrated on the correct manufacturer range (e.g. $5\,\text{A/V}$ / $0.2\,\text{V/A}$).

---

## 3. Oscilloscope Channel Allocation Consistency Resolution

### 3.1 The 4-Channel Allocation Conflict
The testbed digitizer is a 4-channel oscilloscope (Keysight DSOX1204G).  
Milestone V3.4-N-CORR-04 listed the active channel assignment as:
- **CH1:** E-Stop Safety Contact ($24\,\text{V} \to 0\,\text{V}$ dual-channel NC)
- **CH2:** Main Contactor Auxiliary Contact ($24\,\text{V}$ logic)
- **CH3:** Stator Phase U Current (Tektronix TCP303 / TCPA300 into $50\,\Omega$)
- **CH4:** Brake Coil De-energization Signal ($24\,\text{V} \to 0\,\text{V}$ PWM)

However, subsequent sections of Milestone V3.4-N-CORR-03 and V3.4-N-CORR-04 discussed:
- Simultaneous DC bus voltage monitoring ($V_{\text{bus}} < 50\,\text{V}$)
- Simultaneous brake caliper mechanical displacement monitoring (linear potentiometer/LVDT)

**Audit Finding:** Capturing 6 independent physical signals on a 4-channel DSO is physically impossible. Implying that DC bus discharge, mechanical caliper displacement, and electrical stator current were recorded simultaneously on a single instrument is false.

### 3.2 Formal Protocol Decoupling: Dual Acquisition Architecture
To eliminate all ambiguity, test procedures are strictly decoupled into two distinct, non-simultaneous acquisition protocols:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ ACQUISITION PROFILE A: POWERTRAIN ELECTRICAL CUTOFF (4 Channels)                       │
├─────────┬──────────────────────────────┬──────────────────┬────────────────────────────┤
│ Channel │ Signal Name                  │ Transducer       │ Coupling / Bandwidth       │
├─────────┼──────────────────────────────┼──────────────────┼────────────────────────────┤
│ CH1     │ E-Stop NC Safety Circuit     │ 10:1 Passive     │ DC 1M, Full BW, Trigger    │
│ CH2     │ Contactor Aux Microswitch    │ 10:1 Passive     │ DC 1M, 20 MHz BW Limit     │
│ CH3     │ Phase U Stator Current       │ TCP303 + TCPA300 │ DC 50 Ohm, 20 kHz LPF      │
│ CH4     │ Brake Coil Control Voltage   │ 10:1 Passive     │ DC 1M, 20 MHz BW Limit     │
└─────────┴──────────────────────────────┴──────────────────┴────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ ACQUISITION PROFILE B: ENERGY STORAGE & MECHANICAL BRAKE (4 Channels)                  │
├─────────┬──────────────────────────────┬──────────────────┬────────────────────────────┤
│ Channel │ Signal Name                  │ Transducer       │ Coupling / Bandwidth       │
├─────────┼──────────────────────────────┼──────────────────┼────────────────────────────┤
│ CH1     │ E-Stop NC Safety Circuit     │ 10:1 Passive     │ DC 1M, Full BW, Trigger    │
│ CH2     │ Contactor Aux Microswitch    │ 10:1 Passive     │ DC 1M, 20 MHz BW Limit     │
│ CH3     │ Inverter DC Bus Voltage      │ 100:1 HV Diff    │ DC 1M, 20 MHz BW Limit     │
│ CH4     │ Brake Caliper Displacement   │ LVDT / Pot       │ DC 1M, 1 kHz Low Pass      │
└─────────┴──────────────────────────────┴──────────────────┴────────────────────────────┘
```

**Rule:** `ACQUISITION_A` evaluates electrical current de-energization (`ELECTRICAL_TRACTION_DEENERGIZED`). `ACQUISITION_B` evaluates DC bus discharge and brake shoe mechanical clamping. Reports must never claim simultaneous single-shot acquisition across all six channels.

---

## 4. Inverter Controller Identity Resolution

### 4.1 Prior Ambiguity
The prior characterization report cited:
$$\text{"Curtis 1238E-5421 / Sevcon Gen4"}$$
The slash symbol created severe ambiguity: was this a dual-controller vehicle, an uncommitted specification, or a merged dataset combining two fundamentally different motor controllers?

### 4.2 Reconciled Configuration Specification
Characterization evidence from different controller architectures can **never** be combined. The two controllers have completely different gate driver topologies, STO reaction times, freewheeling diode packages, and firmware parameter sets.

The active physical testbed baseline is unambiguously assigned to the **Curtis 1238E**:

```text
========================================================================================
PRIMARY TESTBED CONTROLLER CONFIGURATION (BENCH-TESTBED-E04)
========================================================================================
Manufacturer                     : Curtis Instruments, Inc.
Model Number                     : 1238E-5421
Hardware Revision                : Rev D
Serial Number                    : CUR-1238E-ENG-08412
Nominal System Voltage           : 48 V DC
Continuous Current Rating        : 350 A RMS
Firmware OS Version              : OS 5.12
Firmware Build Number            : 2489
Parameter File Name              : AGV_48V_PMSM_V34_PARAM_SET_A.cpf
Parameter Set SHA-256 Hash       : a94f728c03264b18274640195e7b165432d0c15926719875f10b776f827a5814
PWM Switching Frequency          : 10.0 kHz (T_pwm = 100 us)
Safe Torque Off (STO) Hardware   : Dual-channel hardware gate-drive inhibit (SIL 3 / PL e)
STO Propagation Delay (Nominal)  : 1.2 ms (Maximum: 1.5 ms)
========================================================================================
```

### 4.3 Status of Sevcon Gen4 Controller
The Sevcon Gen4 controller is classified as:
$$\mathbf{SEVCON\_GEN4 = NOT\_CHARACTERIZED\_SEPARATE\_BASELINE\_REQUIRED}$$
No characterization data from the Curtis 1238E testbed may be applied to a Sevcon Gen4 controller without a complete, independent 10-trial characterization protocol.

---

## 5. DC Bus Voltage Semantics Reconciliation

### 5.1 Analysis of Prior 50V Limit on a 48V Nominal System
The prior milestone stated:
$$\text{"DC\_BUS\_ISOLATED (Independent HV probe: V\_bus < 50V; requires seconds/minutes)"}$$
This statement is dangerous and conceptually flawed:
- The nominal traction battery pack is **$48\,\text{V}$**.
- Full charge float voltage is **$54.6\,\text{V}$** (for 13S Li-ion or lead-acid equivalent).
- Declaring a $48\,\text{V}$ system "isolated" or "discharged" when $V_{\text{bus}} < 50\,\text{V}$ is meaningless; $48\,\text{V}$ is the normal operating voltage of the vehicle!
- While $50\,\text{V}$ AC/DC is cited in industrial safety standards (e.g. IEC 60204-1) as the threshold for Protection Against Electric Shock (touch-safe extra-low voltage PELV/SELV), it cannot prove de-energization of a $48\,\text{V}$ battery or bus.

### 5.2 Reconciled DC Bus State Definitions
We formally decouple and define three distinct DC bus electrical states:

1. **`DC_BUS_ISOLATED` (Galvanic Contact Separation):**
   - **Definition:** The main traction DC contactor has mechanically parted, physically disconnecting the traction inverter from the high-current battery pack.
   - **Measurement:** Contactor auxiliary microswitch state (`CH2` open) verified simultaneously with contactor coil voltage drop.
   - **Verification:** Resistance across main contactor contacts $R_{\text{open}} > 1.0\,\text{M}\Omega$.

2. **`DC_BUS_DISCHARGED` (Internal Link Capacitor Bleed-Down):**
   - **Definition:** The internal DC link filter capacitors ($C_{\text{bus}} \approx 4,700\,\mu\text{F}$) have bled their stored electrostatic energy through internal discharge resistors to a touch-safe, non-hazardous residual voltage.
   - **Acceptance Criterion:**
     $$\mathbf{V_{\text{bus}} < 5.0\,V\;DC}$$
   - **Latency:** Because bleeder discharge is passive ($R_{\text{bleed}} \approx 10\,\text{k}\Omega$, $\tau_{\text{bleed}} = R C \approx 47\,\text{s}$), complete discharge requires **$180$ to $300\,\text{seconds}$**.
   - **Safety Rule:** `DC_BUS_DISCHARGED` is an offline maintenance state; it is **NOT** a prerequisite for E-Stop safe torque de-energization during dynamic vehicle operation.

3. **`DC_BUS_VOLTAGE_BELOW_ACCEPTANCE_LIMIT`:**
   - Specific to high-voltage platforms ($> 60\,\text{V}$ DC); does not apply to nominal $48\,\text{V}$ systems where operating voltage is already extra-low voltage.

---

## 6. Safety Test Procedure & Passive Boundary Preservation

```text
========================================================================================
SAFETY GOVERNANCE RULE: RESEARCH DAQ HAS ZERO VEHICLE ACTUATOR AUTHORITY
========================================================================================
```
1. The research DAQ hardware and characterization software operate in a strictly **passive monitoring** topology.
2. The DAQ has **zero hardware wiring** to vehicle throttle, steering, brake solenoids, or contactor control coils.
3. E-Stop actuation is performed manually by certified laboratory test personnel or via approved vehicle OEM pendant switches under existing facility safety procedures.
4. This technical report does not constitute a substitute for the approved facility Machine Safety & High-Energy Testing Procedure. All bench trials require dyno wheel chocks, interlocked cage barriers, and emergency stop tripwires.

---

## 7. Audit Conclusion

Due to the ungrounded $10\,\text{A/V}$ sensitivity figure for the Tektronix TCP303 / TCPA300 instrument chain and the lack of an ISO/IEC 17025 accredited calibration certificate:
$$\mathbf{INSTRUMENT\_CHAIN\_STATUS = BLOCKED}$$
$$\mathbf{TRACTION\_CURRENT\_ENDPOINT\_PERSISTENCE = PROVISIONAL\_CHARACTERIZATION\_ONLY}$$
