# V3.4-N-CORR-04-R3 — Timestamp / Clock Governance

**Document:** `outputs/v3_4_n_corr_04_r3/timing_timestamp_governance.md`
**Status:** `BLK_R3_07` OPEN — timestamp semantics **not** verified.

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

---

## 1. Two time bases that must never be conflated

| Time base | Symbol | Definition | Where it lives | Metrological status |
| :--- | :--- | :--- | :--- | :--- |
| **Logical index time** | `t_k^logical = k · 100 µs` (integer µs) | Counts evaluation frames; exact integer arithmetic | Mode-B reference model, RMS reference model | **Exact by construction; says nothing about physical elapsed time** |
| **Physical acquisition time** | `τ_n` | True time at which sample `n` was converted by the digitizer | Instrument | **Unknown**: depends on clock source, accuracy, jitter, trigger path |

The relationship is `τ_n = τ_0 + Σ (true sample intervals)`, with `τ_0` set by the trigger path. Counting 100 software intervals proves **only** that 100 frame-steps of 100 samples were processed.

## 2. What "10.0 ms" does and does not mean

* **Logical**: `(k_qualified − k_start) × 100 µs = 10 000 µs` exactly (101 evaluation points, 100 intervals).
* **Physical duration** of the same span is `T_phys = Σ_{j=k_start}^{k_start+99} (τ_{(j+1)M} − τ_{jM})`. If the sample clock has fractional error `ε` (unknown), `T_phys = 10.0 ms · (1 + ε)` plus timestamp/jitter terms. **No value of `ε` is evidenced.**
* **Observation granularity**: the sub-threshold condition is verified at 101 frame instants only; behaviour between instants is not observed. The RMS windows overlap by 95 %, so the data span examined is `(t_start − 2.0 ms, t_start + 10.0 ms]` = 12.0 ms of samples (corrects the R2-R1 endpoint wording).
* **Therefore:** the statement "persistence of 10.0 ms" is a **nominal logical duration**. It must **not** be presented as a 10.0 ms *metrologically accurate* duration, and no uncertainty on it exists.

## 3. Required evidence (none is currently present)

| # | Quantity | Why it matters | Evidence required to close | Status |
| :-- | :--- | :--- | :--- | :---: |
| T1 | **Acquisition clock source** (instrument internal timebase vs external reference) | Defines what `τ_n` is referenced to | Instrument identification + settings record (clock source, reference) for the exact unit | `MISSING` |
| T2 | **Timestamp accuracy** (absolute and relative, specification and as-found) | Converts logical to physical duration | Manufacturer timebase specification for the exact model/firmware, and calibration/verification record | `MISSING` |
| T3 | **Sample-rate tolerance** (actual rate at the 1.0 MSa/s setting) | Direct scale error on `T_phys` | Verified actual sampling interval, e.g. from a traceable reference signal recorded by the same chain | `MISSING` |
| T4 | **Scheduling jitter** (if any software/real-time stage assigns timestamps) | Randomizes frame-to-physical mapping | Description of where timestamps are generated; jitter measurement; or statement that stamps come only from the digitizer | `MISSING` |
| T5 | **Trigger latency** (E-Stop command edge → trigger event → first stored sample; pre-trigger position) | Sets `τ_0`; defines the "t = 0" of every latency figure (the CORR-04 protocol triggers on a channel-1 falling edge) | Trigger source, threshold, delay, pre-trigger setting and a measured latency of the trigger path | `MISSING` |
| T6 | **RMS evaluation latency** | If the RMS is computed online it adds algorithmic (causal window) and processing delay; if offline from stored records it adds none to timestamps | Statement and evidence of online/offline operation. The CORR-04 protocol describes offline post-processing of recorded traces; no executable exists | `UNDETERMINED` |
| T7 | **Frame-grid phase** (index 0 vs physical event) | Grid quantization is up to 0.1 ms and depends on this phase | Record the trigger position in samples for each acquisition | `MISSING` |
| T8 | **Cross-channel time alignment** (E-Stop channel vs current channel) | Latency from command to current collapse needs a common time base | Channel skew/deskew record | `MISSING` |

## 4. Rules

1. Logical timestamps in any output must be labelled `LOGICAL`. Physical timestamps must carry their time base, reference, and uncertainty or be labelled `UNCERTAINTY_UNKNOWN`.
2. A claim of the form "`≥ 10.0 ms` persistence" may not state a physical value or uncertainty until T1–T3 and T5 are evidenced.
3. Acceptance limits (such as the legacy "48.8 ms" latency budget) **must not** appear inside the persistence state machine; they belong to a separately governed acceptance step (R2-R1's FSM pseudocode embedded one; superseded).
4. The R2 manifest columns `trigger_timestamp_ms = 0.0`, `contactor_timestamp_ms`, etc. are report-based and are not physical timestamps for any purpose (`historical_trial_evidence_reconciliation.md`).

## 5. Status

```text
LOGICAL_TIMESTAMP_SEMANTICS   = DEFINED (integer µs, k·100)
PHYSICAL_TIMESTAMP_SEMANTICS  = NOT_VERIFIED
T_PERSIST_PHYSICAL_ACCURACY   = NOT_ESTABLISHED
```
