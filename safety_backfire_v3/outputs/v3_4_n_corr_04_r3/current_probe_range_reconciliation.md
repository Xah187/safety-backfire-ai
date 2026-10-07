# V3.4-N-CORR-04-R3 — Current Probe Range Reconciliation

**Document:** `outputs/v3_4_n_corr_04_r3/current_probe_range_reconciliation.md`

```text
HISTORICAL_CURRENT_SCALE        = UNRESOLVED
UNTERMINATED_OUTPUT_SCALING     = NOT_QUANTITATIVELY_RECONSTRUCTABLE
HISTORICAL_TERMINATION_STATE    = UNRESOLVED
INSTRUMENT_CHAIN                = BLOCKED
```

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

**Source note.** Manufacturer figures were obtained from web search summaries of Tektronix/distributor pages on 2026-10-05 (`MFR_VIA_SEARCH_SUMMARY`); the primary manual was not retrieved into the repository. The R2-R1 citation "User Manual 071-1183-XX" could not be confirmed and is withdrawn as a reference.

---

## 1. Manufacturer-documented ranges (TCP303 on TCPA300)

| Setting | Continuous DC | Continuous RMS (sinusoidal) | Peak pulse | Nominal scale |
| :--- | ---: | ---: | ---: | :--- |
| **5 A/V** | 25 A | 17.7 A | 500 A | 0.2 V/A into 50 Ω |
| **50 A/V** | 150 A | 150 A | 500 A | 0.02 V/A into 50 Ω |

* Probe bandwidth DC–15 MHz. **No 10 A/V setting is documented** (consistent with R2-R1).
* The amplifier output **must be terminated into 50 Ω**; the amplifier indicates an "unterminated" condition (typically during degauss/autobalance).
* These are *manufacturer ratings of the product*. They say nothing about the settings used in any historical trial.

## 2. Removal of the "lock to 5 A/V" instruction

R2-R1 blocker `BLK_PERSIST_01` required to "lock TCPA300 range to 5 A/V". **Withdrawn.** A fixed range is not justified by any evidence and can be unsafe for the instrument or the measurement:

**Range-selection rule (replaces it):** the range is chosen **only from the expected current envelope of the intended measurement** — the lowest range whose *continuous-RMS* and *peak* ratings (Section 1) cover the maximum expected current, with a margin set by the responsible procedure owner (not set here) — and the **actual switch position, autobalance/degauss result, and termination** are recorded for every acquisition.

Trade-off to be resolved by that procedure, not here: nominal scale at the sub-ampere threshold is `0.41 A / 5 A/V = 82 mV` versus `0.41 A / 50 A/V = 8.2 mV` (arithmetic on nominal scale only). The probe's accuracy, noise and the digitizer resolution at these levels are **not established**, so no uncertainty is stated. Whether a single range can serve both the full operating-current envelope and the sub-ampere decision region is an **open question**, not decided by this milestone.

## 3. The "~115 A" historical trial

* The figure "~115 A" was supplied in the milestone request. A search of `outputs/` for `115 A` finds **no occurrence**; the number's provenance in the repository is therefore **unlocated** (`REPORT_BASED`, unlocated).
* **If** a trial reached ~115 A, then it cannot be treated as acquired on 5 A/V: that range's continuous ratings are 25 A DC / 17.7 A RMS. Equally it **cannot be assumed** to have been 50 A/V: a settings-free inference from a reported magnitude is exactly the reverse-engineering the governance prohibits (the magnitude itself may be mis-reported).
* The only legitimate statement is: *the range used is unknown* → `HISTORICAL_CURRENT_SCALE = UNRESOLVED`, until original setup evidence (setup/screenshot files, notebook, photographs, calibration records) or a new **traceable** acquisition exists.

## 4. Consequences of the unresolved scale

| Item | Effect |
| :--- | :--- |
| Guarded threshold (0.410 / 0.413 / 0.460 A) | Each value embeds an assumed scale/uncertainty; none is authoritative (`r2/guarded_threshold_v3.json` already says so) |
| All amplitudes in the historical manifest (`max_residual_current_a_rms`, etc.) | Not quantitatively usable |
| `tau_eff` | A time constant is scale-independent *in principle* for an ideal linear exponential, but it is `REPORT_BASED` and any baseline/offset/clipping error from a wrong scale would bias a fit; its status stays `EMPIRICAL_DESCRIPTIVE_FIT` |

## 5. Termination

* Manufacturer requirement: terminate into 50 Ω. Whether the historical chain was terminated is **unknown** (`HISTORICAL_TERMINATION_STATE = UNRESOLVED`).
* R2-R1's "DC doubling" argument is a *circuit-model illustration* (50 Ω source impedance vs 1 MΩ load), not a manufacturer-documented scaling. The manufacturer documents the 50 Ω requirement and a detection indicator, not a numerical error for an unterminated output. The exact amplitude/phase error of an unterminated chain (cable length, scope input capacitance, frequency content) is **not reconstructable** retrospectively.

```text
UNTERMINATED_OUTPUT_SCALING = NOT_QUANTITATIVELY_RECONSTRUCTABLE
```

## 6. Instrument identity provenance (new finding R3-E10)

The serials `TCP303 B020194`, `TCPA300 B010482`, `DSO MY58491024` were introduced in R1 (`instrument_chain_audit.md`: *"Logged in bench inventory only"*) and carried through R2/R2-R1 as if factual. **No bench inventory, label photo or certificate exists in the repository.** Status: `UNVERIFIED_PROVENANCE`. No calibration certificate, ISO/IEC 17025 or otherwise, exists; none is invented (R2-R1's remediation text that presumed one is replaced by "calibration evidence, whatever its issuer, must be present and traceable").

## 7. Status

```text
HISTORICAL_CURRENT_SCALE  = UNRESOLVED
INSTRUMENT_CHAIN          = BLOCKED
CALIBRATION_EVIDENCE      = MISSING
SERIAL_NUMBERS            = UNVERIFIED_PROVENANCE
```
