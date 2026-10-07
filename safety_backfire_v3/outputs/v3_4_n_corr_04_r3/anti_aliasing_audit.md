# V3.4-N-CORR-04-R3 — Anti-Aliasing Audit

**Document:** `outputs/v3_4_n_corr_04_r3/anti_aliasing_audit.md`

```text
ANTI_ALIAS_VALIDATION = BLOCKED
20_KHZ_ANALOG_FILTER  = NOT_VERIFIED
```

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

**Source note.** Manufacturer figures below were obtained from web search summaries of manufacturer/distributor pages on 2026-10-05; the primary PDF manuals were **not** retrieved or archived in the repository. They are labelled `MFR_VIA_SEARCH_SUMMARY` and must be re-confirmed against the archived manuals before being used as evidence.

---

## 1. Chain, as far as it is documented

| # | Stage | Documented content | Evidence status |
| :-- | :--- | :--- | :--- |
| 1 | Current transducer TCP303 | DC–15 MHz bandwidth, rise time ≤ 23 ns (`MFR_VIA_SEARCH_SUMMARY`) | manufacturer-level only; unit not evidenced |
| 2 | Amplifier TCPA300 | output must be terminated into 50 Ω (`MFR_VIA_SEARCH_SUMMARY`) | termination history unknown |
| 3 | Oscilloscope Keysight DSOX1204G channel | base bandwidth **70 MHz**, licence upgrades to 100/200 MHz; selectable **20 MHz bandwidth limit** (`MFR_VIA_SEARCH_SUMMARY`) | installed licence and the BW-limit setting during any past/future acquisition **unknown** |
| 4 | Digitizer | max 2 GSa/s (interleaved) (`MFR_VIA_SEARCH_SUMMARY`) | rate/memory actually used unknown |
| 5 | Acquisition mode and **decimation to 1.0 MSa/s** | **not documented anywhere** (normal/peak/averaging/high-resolution mode; native vs decimated) | `UNDOCUMENTED` |
| 6 | "Hardware 4th-order 20 kHz LPF" (CORR-04 protocol diagram, stage before the RMS) | existence, location, topology, group delay, initial conditions | `NOT_VERIFIED` — no instrument, probe or accessory documentation supports a 20 kHz analog filter; R2-R1 conclusion ("no 20 kHz analog filter in the DSO") is itself only partly supported (see Section 4) |
| 7 | Frozen RMS stage | N = 2000, M = 100 (`discrete_rms_specification.md`) | implementation not located |

## 2. Signal frequencies involved

* **Sample rate** 1 MSa/s → **Nyquist 500 kHz**.
* **PWM**: the CORR-04 documents assume 10 kHz. The controller's actual switching frequency is **not established** by any retrieved controller documentation, so 10 kHz is a *project assumption*. At 1 MSa/s a 10 kHz period has 100 samples and harmonics up to the 50th (500 kHz) lie below Nyquist (arithmetic only).
* **Possible high-frequency content**: switching edges, diode turn-off/ringing and any inverter-related resonances can exceed 500 kHz. The *only verified-by-manufacturer* band limits ahead of the ADC are the probe/amplifier (to 15 MHz) and the scope channel (70–200 MHz, or 20 MHz if the BW limit is on). None of them attenuates content between 500 kHz and several MHz.
* The measured content in that band is **unknown**: no spectrum, high-rate capture, or ringing record exists (`FIELD_DATA = ZERO`).

## 3. Is 1 MSa/s sufficient for the actual measured signal path?

**Not demonstrable.** Three independent gaps:

1. **Decimation/aliasing unknown.** If the 1 MSa/s record is produced by *dropping* samples from a faster ADC stream (no anti-alias filtering), out-of-band energy aliases into band. If it is produced by an averaging/high-resolution mode, a box-car filter is implicitly applied, which changes the effective bandwidth and adds its own delay. The acquisition mode is unrecorded.
2. **Out-of-band content unknown.** Sufficiency requires a statement of the maximum significant frequency content (or an upper bound on its energy), which is not available.
3. **Estimator nuance.** The sample mean-square is an unbiased estimator of mean power for stationary broadband content under uncorrelated sampling; that does **not** carry over to deterministic/periodic components that are synchronous with the sample clock, nor to the non-stationary ring-down immediately after STO. Whether either applies cannot be decided without data. (This is why "RMS is insensitive to aliasing" is not accepted as an argument here.)

```text
ANTI_ALIAS_VALIDATION = BLOCKED
```

## 4. The filter question is a definition conflict, not just a hardware question

* The R2/R2-R1 position: "RMS-PROC-V1.0 processes raw digitized samples; scope math/display filters stay outside."
* The CORR-04 position: a 20 kHz 4th-order low-pass is part of the V1.0 chain.

These cannot both be the frozen definition. Resolution rules:

1. **Scope math/display filters are outside RMS-PROC-V1.0** unless they are explicitly part of the frozen *acquisition* chain (setup file, mode and filter parameters recorded). None is.
2. **A 20 kHz analog filter is not invented.** Its existence is `NOT_VERIFIED`. If a filter is intended in the chain, it must be specified (type, order, topology, analog or digital, group delay, initial conditions) as part of RMS-PROC-V1.0; none is specified.
3. R2-R1's statements that the DSOX1204G has only a 70/20 MHz analog limit and that a 20 kHz filter exists "exclusively in scope DSP firmware as a Math channel filter" are **not fully evidenced** (the manufacturer-level facts are the bandwidth/limit above; the exclusivity claim and a "2-pole" characterisation were not sourced). They are downgraded to `NOT_VERIFIED`. R2-R1's master-audit statement "hardware analog bandwidth = 20 MHz" is **wrong** (20 MHz is the optional limit; base bandwidth is 70 MHz).
4. Magnitude check only (not adoption): a 4th-order Butterworth low-pass at 20 kHz has a DC group delay of `2.613/(2π·20 kHz) = 20.8 µs`, i.e. ~0.02 ms on the ~0.1 ms frame grid and ≪ `tau_eff`. Whether the filter (if any) would affect the crossing in the actual chain is unknown because its type is unspecified.

## 5. Evidence that would unblock (documentation of intent; **no capture is authorized**)

| Needed | Purpose |
| :--- | :--- |
| Archived primary manuals for the exact TCP303/TCPA300/DSOX1204G units (bandwidth, licence, timebase) | replace `MFR_VIA_SEARCH_SUMMARY` |
| Recorded acquisition mode, native sampling rate, memory depth, decimation method | decide aliasing path |
| A normative statement whether RMS-PROC-V1.0 includes a filter (and its exact specification) | resolve definition conflict |
| Spectral/ring-down evidence of the actual current signal up to the probe bandwidth | bound out-of-band content |
| Same-event comparison between the 1 MSa/s record and a higher-rate reference | test sufficiency empirically |

## 6. Status

```text
ANTI_ALIAS_VALIDATION            = BLOCKED
SAMPLE_RATE_1MSA_SUFFICIENT      = NOT_DEMONSTRATED
20_KHZ_ANALOG_FILTER             = NOT_VERIFIED
SCOPE_MATH_OR_DISPLAY_FILTER_IN_RMS_PROC_V1_0 = EXCLUDED (not part of any recorded frozen acquisition chain)
```
