# V3.4-N-CORR-04-R4 — Frozen RMS Implementation Forensic Search

**Document:** `outputs/v3_4_n_corr_04_r4/rms_implementation_forensic_search.md`  
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

## 1. Forensic Search Methodology

A comprehensive, automated ripgrep and file-system audit was executed across the entire repository (`scripts/`, `safety_backfire_v3/outputs/`, `outputs/`, and root directories) to discover any operational, archived, or legacy code implementing the digital signal processing pipeline historically designated as `RMS-PROC-V1.0`.

The search targeted sixteen exact and regex patterns:
1. `RMS-PROC-V1.0`
2. `moving RMS`
3. `rms_stream`
4. `2000`
5. `window`
6. `2.0 ms`
7. `1.0 MSa/s`
8. `100 us`
9. `0.1 ms`
10. `threshold crossing`
11. `CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED`
12. `persistence`
13. `numpy.sqrt`
14. `mean(square`
15. `rolling RMS`
16. `sliding RMS`

---

## 2. Findings by Query

### Query 1: `RMS-PROC-V1.0`
- **Occurrences:** Found across 15+ markdown reports and JSON schemas in `safety_backfire_v3/outputs/v3_4_n_corr_04/`, `r1/`, `r2/`, and `r3/`.
- **Script occurrences:** Found in `scripts/v3_4_n_corr_04/run_v3_4_n_corr_04_audit.py`, `scripts/v3_4_n_corr_04_r1/audit_v3_4_n_corr_04_r1.py`, and `outputs/v3_4_n_corr_04_r3/audit_r3.py`.
- **Finding:** Every occurrence in existing code is a **string check** verifying that metadata contains the literal string `"RMS-PROC-V1.0"`. No algorithm, DSP kernel, or math routine bearing this name was found in any executable file prior to R3.

### Query 2: `moving RMS` / `sliding RMS` / `rolling RMS`
- **Occurrences:** Found exclusively in markdown discussions (`persistence_state_machine_v3.md`, `signal_path_audit_v2.md`, `discrete_rms_specification.md`, `r2_r1_master_audit.md`).
- **Discrepancy detected:** `r2_r1_master_audit.md` (line 290) defined the algorithm as operating at $\Delta t = 0.1\,\text{ms}$ with window $T_w = 2.0\,\text{ms}$ ($N_w = 20\,\text{samples}$ at $10\,\text{kHz}$), while CORR-04 and R3 define $N = 2000$ samples at $1.0\,\text{MSa/s}$. This demonstrates fundamental confusion between decimated evaluation and raw sampling.

### Query 3: `rms_stream`
- **Occurrences:** Appears only in pseudocode within `outputs/v3_4_n_corr_04_r2_r1/persistence_fsm_audit.md` (lines 118, 143) as a conceptual argument to an illustrative Python snippet. No production module exposes this stream.

### Query 4: `2000`, `2.0 ms`, `1.0 MSa/s`, `100 us`, `0.1 ms`
- **Occurrences:** Found in parameter dictionaries, markdown text, and audit verification bounds. In R3, `outputs/v3_4_n_corr_04_r3/discrete_rms_verification.py` was authored specifically as an independent reference model of these documented parameters. It does not exist in any production path.

### Query 5: `CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED`
- **Occurrences:** Found in `outputs/v3_4_n_corr_04_r3/persistence_modeb_reference.py`, `outputs/v3_4_n_corr_04_r3/persistence_semantics_v5.md`, and `outputs/v3_4_n_corr_04_r3/audit_r3.py`.
- **Finding:** This is an R3 synthetic qualification label created to formalize Mode-B state-machine transitions. It does not exist in historical production code.

### Query 6: `numpy.sqrt`, `mean(square`
- **Occurrences:** Zero occurrences in the production codebase (`scripts/v3_4/`). Python scripts in `scripts/` do not import `numpy`. `outputs/v3_4_n_corr_04_r3/discrete_rms_verification.py` uses standard library `math.sqrt` and list comprehension sums.

---

## 3. Forensic Evaluation Questions (A – F)

### Question A: Is there an actual executable implementation?
**NO.** There is no operational executable script or binary in the repository that ingests a raw digitized stator current waveform and computes the moving RMS window according to `RMS-PROC-V1.0`. The script `discrete_rms_verification.py` created in R3 is explicitly documented as a synthetic reference model to test mathematical consistency of the documentation against closed-form integrals, not an operational processing pipeline.

### Question B: Is there an older implementation?
**NO.** Inspection of git history and legacy directories (`v3_4_h_sandbox`, `v3_4_k`, `v3_4_m`, `v3_4_n`, `v3_4_n_corr`, `v3_4_n_corr_02`, `v3_4_n_corr_03`, `v3_4_n_corr_04`) reveals no prior executable script for moving RMS calculation. Earlier milestones cited historical results produced outside the repository.

### Question C: Is there only documentation?
**YES.** Prior to R3, `RMS-PROC-V1.0` existed entirely as:
1. Narrative prose in markdown specifications;
2. Parameter key-value pairs in JSON schemas (`window_length_ms: 2.0`, `sliding_step_ms: 0.1`);
3. String-matching assertions in audit scripts (`ver == "RMS-PROC-V1.0"`).

### Question D: Are there conflicting implementations?
**YES (Documentary Conflicts).** While no conflicting code exists, multiple mutually incompatible pipeline specifications exist in the documentation:
1. **Filtering Conflict:** CORR-04 protocol specifies an upstream "4th-order 20 kHz hardware low-pass filter" preceding the RMS stage. R2/R2-R1/R3 documents specify that `RMS-PROC-V1.0` operates directly on raw digitized samples, rejecting any upstream math filter.
2. **Threshold Comparator Conflict:**
   - CORR-04 schema: $I_{\text{motor}} < 0.500\,\text{A}$ (nominal);
   - R1 reconciliation: $I_{\text{motor}} \le 0.460\,\text{A}$;
   - R2-R1 audit: $I_{\text{motor}} \le 0.413\,\text{A}$;
   - R3 reference: $I_{\text{motor}} \le 0.410\,\text{A}$ (continuous) vs $< 0.410\,\text{A}$.
3. **Decimation / Window Size Conflict:** $N_w = 20\,\text{samples}$ at $10\,\text{kHz}$ vs $N = 2000\,\text{samples}$ at $1.0\,\text{MSa/s}$.

### Question E: Is there a hash for the actual implementation?
**NO.** No cryptographic hash (SHA-256 or otherwise) exists for any historical implementation of `RMS-PROC-V1.0`.

### Question F: Is the implementation that generated historical data identifiable?
**NO.** The tool, software package, language, or instrument firmware that generated the timestamps in `evidence_manifest_v3.csv` (`CHAR_RUN_01` through `CHAR_RUN_10`) cannot be identified. Moreover, as proven in R3, the manifest's physical crossing times were produced by subtracting $1.12\,\text{ms}$ from RMS crossings by hand or spreadsheet formula, rather than by running an executable algorithm over measured data.

---

## 4. Preservation of R3 Finding: Critical State Separation

We preserve the fundamental distinction established in Milestone R3:

```text
REFERENCE_MODEL_VERIFIED            = TRUE
FROZEN_RMS_IMPLEMENTATION_VERIFIED  = FALSE
```

1. **`REFERENCE_MODEL_VERIFIED = TRUE`** indicates solely that the synthetic reference implementation (`discrete_rms_verification.py`) created in R3 accurately matches the analytical closed-form equations for continuous exponential decay across Regions 1, 2, and 3 under synthetic test conditions.
2. **`FROZEN_RMS_IMPLEMENTATION_VERIFIED = FALSE`** reflects the reality that the historical, frozen production implementation does not exist in the repository, was never hashed, and cannot be executed against historical data.

These two states MUST NOT be collapsed. Verifying that a mathematical formula reproduces a reference simulation does not prove that historical bench trials used that algorithm.

---

## 5. Final Authoritative State

In accordance with forensic evidence governance:

```text
RMS_IMPLEMENTATION_STATUS = RMS_IMPLEMENTATION_MISSING
```
