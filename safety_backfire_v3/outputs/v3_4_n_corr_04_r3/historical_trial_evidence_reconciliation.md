# V3.4-N-CORR-04-R3 — Historical Trial Evidence Reconciliation

**Document:** `outputs/v3_4_n_corr_04_r3/historical_trial_evidence_reconciliation.md`
**Supersedes:** `r2_r1/historical_trial_evidence_status.md`

```text
TIMING_EVIDENCE          = REPORT_BASED
HISTORICAL_CURRENT_SCALE = UNRESOLVED
RAW_WAVEFORM_EVIDENCE    = MISSING
EMPIRICAL_VALIDATION     = NOT_ESTABLISHED
```

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

---

## 1. Inventory (`r2/evidence_manifest_v3.csv`)

Ten rows `CHAR_RUN_01…10`. For **every** row: `raw_waveform_file = MISSING`, `raw_waveform_sha256 = MISSING`, `scope_config_file = MISSING`, `instrument_range_setting = INDETERMINATE`, `instrument_calibration_certificate = MISSING`, `operator_record = MISSING`, `evidence_class = REPORT_BASED`. No raw trace exists anywhere in the repository. None is reconstructed here.

## 2. New finding R3-E08 — the manifest's timing columns are partly *derived*, not observed

In all ten rows `Delta_flush_ms = 1.12` and `t_phys_envelope_cross_ms = t_rms_threshold_cross_ms − 1.12`, while the other timestamps vary from row to row (e.g. `t_rms` from 21.20 to 25.80 ms). A constant, row-independent offset across ten different operating conditions is what a **subtraction of the analytical constant** produces; it is not what ten independent measurements produce. (`audit_r3.py` re-checks this arithmetic from the CSV.)

Conclusions:

| Column | Treatment |
| :--- | :--- |
| `t_rms_threshold_cross_ms`, `persistence_start/completion_timestamp_ms` | `REPORT_BASED` (origin: R1 narrative figures; no raw data) |
| `t_phys_envelope_cross_ms` | **DERIVED** from the analytical constant — **not an observation** |
| `Delta_flush_ms` | **DERIVED** (constant 1.12 = rounded `tau_eff·ln C`) — **not an observation**; consuming it as a measurement would be circular |
| `trigger_timestamp_ms = 0.0`, `contactor_timestamp_ms` | `REPORT_BASED`; not physical timestamps (`timing_timestamp_governance.md`) |
| amplitude columns (`max_residual_current_a_rms`, …) | scale `UNRESOLVED`; not quantitatively usable |
| `rebound_count = 0`, `temperature_c` | `REPORT_BASED` |

R2-R1's statement that the flush lag "was completely absent from the historical records" is **inconsistent** with this manifest (which carries a lag in every row, but derived). Both narratives are unusable as evidence; neither is promoted.

## 3. What these ten trials are and are not

**They are:** report-based narrative figures of unlocated provenance, usable only as *hypothesis context* for planning.

**They are not:** traceable quantitative evidence; empirical validation of `tau_eff`, of `Delta_flush`, of the 1.117 ms Region-3 offset, of `T_persist = 10.0 ms`, of the guarded threshold, or of any rebound-count claim.

## 4. Prohibitions upheld

* No reverse-engineering of the missing current scale from reported magnitudes (including the unlocated "~115 A"; see `current_probe_range_reconciliation.md` §3).
* No reconstruction of raw traces, and no synthetic trace may be presented as, or merged into, historical evidence.
* The synthetic envelopes in `discrete_rms_verification.py` are model test vectors only.

## 5. Evidence that would upgrade the status (none exists today)

Original raw time-series files with recorded hashes and acquisition metadata, scope setup/range/termination records, calibration evidence, operator logs, and an unambiguous mapping of each file to a trial. Only then could any trial be re-classified; until then `REPORT_BASED`.

## 6. Status

```text
TIMING_EVIDENCE          = REPORT_BASED
HISTORICAL_CURRENT_SCALE = UNRESOLVED
RAW_WAVEFORM_EVIDENCE    = MISSING
MANIFEST_t_phys_AND_DELTA_FLUSH = DERIVED_NOT_OBSERVED
```
