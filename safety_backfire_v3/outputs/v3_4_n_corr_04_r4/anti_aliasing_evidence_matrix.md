# V3.4-N-CORR-04-R4 — Anti-Aliasing Evidence Matrix & Acquisition Chain Forensics

**Document:** `outputs/v3_4_n_corr_04_r4/anti_aliasing_evidence_matrix.md`  
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
ANTI_ALIAS_VALIDATION           = BLOCKED
FINAL_STATUS                    = BLOCKED
```

---

## 1. Executive Summary & Epistemic Boundaries

Anti-aliasing validation requires physical and mathematical proof that signal energy above the Nyquist frequency ($f_{\text{Nyq}} = f_s / 2 = 500\,\text{kHz}$) is attenuated below the noise floor or measurement uncertainty threshold **prior to analog-to-digital conversion**.

This audit reconstructs the entire measurement acquisition chain solely from authoritative manufacturer documentation and repository evidence. 

**Mandatory Audit Rules Applied:**
1. A digital or display filter executed post-ADC **SHALL NOT** be treated as an anti-aliasing filter.
2. A 20 kHz analog filter **SHALL NOT** be assumed or invented without physical hardware evidence.
3. If the complete analog pre-ADC filter chain cannot be verified, `ANTI_ALIAS_VALIDATION = BLOCKED`.

---

## 2. Stage-by-Stage Acquisition Chain Matrix

| # | Physical / Processing Stage | Hardware / Digital / Unknown | Signal Domain Placement | Bandwidth / Transfer Characteristic | Authoritative Source | Anti-Aliasing Efficacy ($f > 500\,\text{kHz}$) | Evidence Status |
| :-: | :--- | :---: | :---: | :--- | :--- | :--- | :---: |
| **1** | **Current Transducer (Tektronix TCP303)** | `HARDWARE` | `PRE_ADC` | DC to $15\,\text{MHz}$ ($-3\,\text{dB}$); rise time $\le 23\,\text{ns}$. | Tektronix TCP300/TCPA300 Datasheet. | **Zero attenuation.** Passes all frequencies up to $15\,\text{MHz}$ directly to the amplifier. | `UNVERIFIED` (Exact unit serial unverified) |
| **2** | **Current Amplifier (Tektronix TCPA300)** | `HARDWARE` | `PRE_ADC` | DC to $15\,\text{MHz}$ (limited by probe). Requires $50\,\Omega$ termination. | Tektronix TCPA300 Manual. | **Zero attenuation.** Amplifies and outputs broad-band signals up to $15\,\text{MHz}$. | `UNVERIFIED` (Termination history unknown) |
| **3** | **Oscilloscope Analog Front-End (Keysight DSOX1204G)** | `HARDWARE` | `PRE_ADC` | Base analog bandwidth: $70\,\text{MHz}$. Optional hardware limit: $20\,\text{MHz}$ ($-3\,\text{dB}$). | Keysight InfiniiVision 1000 X-Series Datasheet. | **Zero attenuation.** At $500\,\text{kHz}$, response is completely flat ($0\,\text{dB}$). $20\,\text{MHz}$ limit does not attenuate $0.5 - 20\,\text{MHz}$. | `UNVERIFIED` (Bandwidth limit setting unrecorded) |
| **4** | **Purported "20 kHz Hardware LPF"** | `UNKNOWN` | `PRE_ADC` | Asserted as "4th-order 20 kHz hardware low-pass filter" in CORR-04 protocol. | Refuted by instrument specifications; no external hardware filter module in inventory. | **Non-existent in hardware.** DSOX1204G has NO 20 kHz analog filter. | `NOT_VERIFIED` (Fictitious / Refuted) |
| **5** | **ADC Digitizer (Keysight DSOX1204G)** | `HARDWARE` | `CONVERSION` | Flash/SAR ADC operating up to $2.0\,\text{GSa/s}$ interleaved ($1.0\,\text{GSa/s}$ all channels); 8-bit native resolution. | Keysight InfiniiVision 1000 X-Series Technical Reference. | Samples analog voltage into discrete samples. Subject to aliasing if signal bandwidth exceeds sampling Nyquist. | `VERIFIED` (Instrument capability only) |
| **6** | **Oscilloscope Acquisition / Decimation Engine** | `DIGITAL` | `POST_ADC` | Mode options: Normal (sample drop), Peak Detect, Averaging, High-Resolution (boxcar). Decimated to $1.0\,\text{MSa/s}$. | Keysight 1000 X-Series User's Guide. | **Undocumented.** If "Normal" mode decimation was used, out-of-band energy aliases into $[0, 500\,\text{kHz}]$. If "High-Res", boxcar filter introduces uncharacterized phase lag. | `MISSING` (Setup file unarchived) |
| **7** | **Oscilloscope Math Channel Filter** | `DIGITAL` | `DISPLAY_ONLY` | Firmware-based digital low-pass filter available in Math menu. | Keysight InfiniiVision Firmware Manual. | **Post-ADC only.** Cannot prevent ADC aliasing. Excluded from raw data exports by definition. | `EXCLUDED` (Not part of recorded frozen chain) |
| **8** | **Digital RMS Stage (`RMS-PROC-V1.0`)** | `DIGITAL` | `POST_ADC` | Rectangular moving RMS sum ($N=2000$, $M=100$). Sinc-squared frequency response nulls at multiples of $500\,\text{Hz}$. | Specification only (`discrete_rms_index_contract.md`). | Operates on discrete sequence. If aliased energy is already folded into $[0, 500\,\text{kHz}]$, it cannot separate signal from alias. | `MISSING` (Frozen executable unlocated) |

---

## 3. High-Frequency Spectral Environment & Inverter Harmonics

To evaluate aliasing risk, the physical spectral content of the motor stator circuit must be bounded:

### 3.1 Carrier and Switching Components
- **PWM Switching Frequency:** Commonly assumed to be $f_{\text{PWM}} = 10.0\,\text{kHz}$ in historical documentation. However, Curtis 1238E controllers support programmable switching frequencies from $8.0\,\text{kHz}$ to $16.0\,\text{kHz}$. (Actual parameter setting is unrecorded; Node E07 is `MISSING`).
- **Harmonics Below Nyquist:** For $f_{\text{PWM}} = 10\,\text{kHz}$ and $f_s = 1.0\,\text{MSa/s}$, the Nyquist frequency is $f_{\text{Nyq}} = 500\,\text{kHz}$. Exactly 49 integer harmonics of the $10\,\text{kHz}$ carrier lie below Nyquist:
  $$f_m = m \times 10\,\text{kHz} \quad \text{for } m \in \{1, 2, \dots, 49\}$$
  These harmonics are represented without aliasing, provided sampling is uniform.

### 3.2 Out-of-Band Switching Edges & Resonant Ringing
- Modern IGBT and power MOSFET switches exhibit voltage and current transition times ($t_{\text{rise}}, t_{\text{fall}}$) on the order of $50\,\text{ns}$ to $250\,\text{ns}$.
- High-frequency edge transitions generate significant spectral energy extending up to:
  $$f_{\text{edge}} \approx \frac{1}{\pi \cdot t_{\text{rise}}} \approx \frac{1}{\pi \cdot 100 \times 10^{-9}} \approx 3.18\,\text{MHz}$$
- Parasitic motor winding capacitance and cable inductance create high-frequency ring-down oscillations typically situated between $1.0\,\text{MHz}$ and $8.0\,\text{MHz}$.
- **Aliasing Mechanism:** The current transducer (TCP303) has flat response up to $15\,\text{MHz}$. The oscilloscope front-end has flat response up to $20\,\text{MHz}$ or $70\,\text{MHz}$. Therefore, all ringing and switching energy between $500\,\text{kHz}$ and $15\,\text{MHz}$ reaches the ADC unattenuated!
- When sampled at $1.0\,\text{MSa/s}$, any energy at frequency $f_{\text{noise}} \in [500\,\text{kHz}, 15\,\text{MHz}]$ folds directly into the baseband:
  $$f_{\text{alias}} = |f_{\text{noise}} - k \cdot f_s| \le 500\,\text{kHz}$$

---

## 4. Evaluation of the "RMS is Insensitive to Aliasing" Claim

It has been argued in informal discussions that moving RMS is an energy estimator, and that under Parseval's theorem, total signal energy is preserved under aliasing, rendering anti-aliasing filtering unnecessary.

**Forensic Refutation:**
1. **Stationarity Assumption Fails:** Parseval energy equivalence for aliased signals holds as an unbiased estimator only for stationary, zero-mean, white or uncorrelated random noise.
2. **Synchronous Periodic Harmonics:** Inverter PWM harmonics are strongly correlated and phase-locked to controller clock dividers. When periodic components alias, they create low-frequency beat notes (intermodulation products) that modulate the moving RMS window, creating artificial low-frequency oscillations.
3. **Transient Ring-Down at E-Stop:** Immediately upon an E-Stop event, gate drive suppression induces a non-stationary decaying inductive transient accompanied by high-frequency contactor arcing or diode recovery oscillations. Folding this energy into the sub-ampere region distorts the apparent decay curve and delays threshold crossing.
4. **Conclusion:** Aliasing cannot be dismissed mathematically for safety-critical threshold verification.

---

## 5. Keysight DSOX1204G Manufacturer Feature Verification

Authoritative specifications from Keysight Technologies regarding the DSOX1204G:
1. **Analog Bandwidth:**
   - Standard: $70\,\text{MHz}$.
   - Hardware Bandwidth Limit: Selectable $20\,\text{MHz}$ ($-3\,\text{dB}$ roll-off).
   - **No lower analog hardware bandwidth limit (e.g. 20 kHz, 100 kHz, or 1 MHz) exists in this instrument family.**
2. **Built-in Digital Math Filters:**
   - The instrument includes DSP math functions (such as low-pass filtering) applied to displayed math traces.
   - These math filters operate on samples **after** the ADC digitization stage.
   - Exported raw channel CSV waveforms (`CHAN1.CSV`) contain raw ADC samples prior to math channel filtering.

---

## 6. Anti-Aliasing Verdict

Because:
1. No pre-ADC anti-alias filter exists between $500\,\text{kHz}$ and $15\,\text{MHz}$;
2. The oscilloscope acquisition mode and decimation method are unrecorded;
3. No high-rate reference spectrum exists to bound out-of-band energy;

The formal status is:
```text
ANTI_ALIAS_VALIDATION       = BLOCKED
20_KHZ_ANALOG_FILTER        = NOT_VERIFIED (NON_EXISTENT)
OUT_OF_BAND_ENERGY_BOUND    = UNKNOWN
DECIMATION_METHOD           = UNDOCUMENTED
```
