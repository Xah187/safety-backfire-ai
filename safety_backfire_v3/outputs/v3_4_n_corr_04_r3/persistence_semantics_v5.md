# V3.4-N-CORR-04-R3 — Persistence Semantics v5 (Mode B)

**Document:** `outputs/v3_4_n_corr_04_r3/persistence_semantics_v5.md`
**Executable reference + test vectors:** `persistence_modeb_reference.py` (11 vectors, all pass)
**Supersedes:** `r2_r1/persistence_semantics_v4.md`, `r2_r1/persistence_fsm_audit.md`, FSM/pseudocode in `r2_r1/r2_r1_master_audit.md`, failure-mode text in `r2/persistence_state_machine_v3.md`

```text
T_persist = 10.0 ms                       = CANDIDATE_ONLY  (nominal LOGICAL duration)
PERSISTENCE_MODE_B                        = DEFINED_PENDING_IMPLEMENTATION_AUDIT
CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED = a measurement/qualification label (see §4)
TRACTION_DEENERGIZED                      = NOT_DIRECTLY_MEASURED
```

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

---

## 1. Mode B (preserved, made exact)

```text
evaluation step            = 0.1 ms (logical; frame index k, t_k = k·100 µs)
k_start                    = index of the FIRST qualifying evaluation point
evaluation points counted  = 1 at k_start (the first qualifying frame IS point #1)
k_qualified                = k_start + 100
elapsed intervals          = 100        (k_qualified − k_start)
evaluation points          = 101        (k_start … k_start+100 inclusive)
nominal logical duration   = 100 × 0.1 ms = 10.0 ms   (NOT a physical-duration claim; see timing_timestamp_governance.md)
data span examined         = (t_start − Tw, t_start + 10.0 ms] = 12.0 ms of samples (Tw = 2.0 ms)
```

Mode A (an inclusive 100-point counter: 100 points, 99 intervals, 9.9 ms) is **not** Mode B and is not used.

## 2. Comparator and threshold conventions (conflict resolved by declaration)

The legacy documents use `I_RMS <= 0.413` (CORR-04), `<= 0.410` (R2 FSM) and `< 0.410` (R2-R1 pseudocode). The **value** of the threshold is unresolved and untouched here. For the **comparator**, the reference model declares **strict** `I_RMS[k] < I_guarded` as the default, with an explicit parameter `inclusive` (vector TV05a/TV05b shows the only behavioural difference: an RMS value exactly equal to the threshold). This is a declaration for determinism, **not** a tuning and not an approval; it is subject to the frozen-definition decision in `BLK_R3_01`.

## 3. Deterministic procedure (normative; executable form in `persistence_modeb_reference.py`)

Record states (no "terminal safe state" wording; monitoring continues in every state):

| State | Name | Meaning |
| :--- | :--- | :--- |
| S0 | `S0_NO_CANDIDATE` | counter = 0, no candidate |
| S1 | `S1_CANDIDATE_COUNTING` | `points` consecutive qualifying frames counted (1…100) |
| S2 | `S2_QUALIFIED_MONITORING` | qualification **recorded**; monitoring/logging continues |
| S3 | `S3_POST_QUALIFICATION_ANOMALY_LATCHED` | anomaly **latched in the record**; monitoring/logging continues; **no outbound transition** |

```text
init:  state = S0 ; points = 0 ; k_start = None ; k_qualified = None ; prev_k = None

step(k, rms):                                   # one call per evaluation frame, in order
  1. if prev_k is not None and k != prev_k+1:   event FRAME_GAP
         if state == S1: reset to S0 (points=0, k_start=None); event CANDIDATE_RESET_BY_GAP
     prev_k = k
  2. if rms is not finite:  event INVALID_FRAME
         S1 -> reset to S0 ;  S2 -> unchanged (NOT an anomaly) ;  S3 -> unchanged ;  return
  3. q = (rms < I_guarded)                       # strict by default
  4. S0: if q: state=S1 ; k_start=k ; points=1 ; event CANDIDATE_START
            (event ..._AT_FIRST_FRAME_OF_RECORD if k is the first frame ever seen)
         else: nothing                           # a rebound frame never starts a candidate
     S1: if q: points += 1                       # first increment happens on the 2nd point
                if points == 101: state=S2 ; k_qualified=k ; event QUALIFIED_...
         else: event PRE_QUALIFICATION_REBOUND_RESET ; reset to S0   # rebound frame is NOT a new start
     S2: if not q: state=S3 ; k_anomaly=k ; event POST_QUALIFICATION_REBOUND_ANOMALY_LATCHED
     S3: nothing (counts frames only)
```

Disambiguation of the points the task singled out:

| Item | Rule |
| :--- | :--- |
| Counter initialization | `points = 0` in S0; set to **1** on the first qualifying frame |
| First qualifying frame | becomes `k_start`; it is evaluation point #1; elapsed intervals = 0 |
| First increment | on the **second** consecutive qualifying frame (`points = 2`) |
| Rebound frame (pre-qualification) | resets to S0; it is **not** counted and **not** a new start; the next qualifying frame starts a new candidate |
| Qualification frame | the frame where `points` becomes **101**, i.e. `k = k_start + 100` |
| Timestamp | `logical_t_qualified_us = k_qualified × 100` (integer µs), `LOGICAL`, not physical |
| Frame gap / invalid frame | resets an in-progress candidate (never silently bridged); an invalid frame after qualification is **not** a rebound |

## 4. Labels (replacing "ELECTRICAL_TRACTION_DEENERGIZED = TRUE")

R2/R2-R1 set `ELECTRICAL_TRACTION_DEENERGIZED = TRUE` at qualification. That asserts a physical state the measurement chain does not measure. Replaced by:

```text
CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED = TRUE | FALSE      # only: RMS frames satisfied the comparator for 101 consecutive points
TRACTION_DEENERGIZED                      = NOT_DIRECTLY_MEASURED   # always, unless an independent traction-energy measurement exists (none does)
```

The first label is a statement about **processed current-RMS frames**, whose scale, anti-aliasing chain and clock are all unresolved; it implies nothing about contactor state, DC-link, torque or kinetic stopping.

## 5. Post-qualification rebound (governance choice, documented — not silent)

* **Decision (preserved from R2-R1, renamed):** the qualification record is an **immutable historical statement** of what the processed frames did (it is not rewritten), **and** a later excursion is a **separate latched diagnostic anomaly** (`POST_QUALIFICATION_REBOUND_ANOMALY_LATCHED`). The anomaly makes the *record's acceptance disposition* "anomaly — not acceptable without review"; it does not delete or move `k_qualified`.
* **Not chosen:** (a) silent re-arming to S0 (hides an anomaly), (b) retroactive erasure of the qualification timestamp (destroys evidence of what was observed).
* **No actuation, no re-arm, no restore:** the reference model returns annotation records only. It has no method that commands, enables, restores, resets or re-arms anything, and S3 has no outbound transition. R2-R1 phrases such as "aborts characterization logging" and "terminates recording" are **removed**: S3 means *annotate and keep monitoring*; recording control is not a function of this model. `RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO`.
* The legacy latency limit (48.8 ms) is **not** part of the persistence logic (it was embedded in R2-R1's FSM). Acceptance limits are a separate governed step.

## 6. Failure-mode language (all CANDIDATE / HYPOTHESIZED)

| Mechanism | Status | Condition | Directly measured? | OEM-documented? |
| :--- | :--- | :--- | :---: | :---: |
| Contactor/relay contact bounce | `CANDIDATE_HYPOTHESIZED` | a mechanical contactor/relay is in the energy path (not established) | no | no |
| Inductive clamp / snubber ringing after gate-drive disable | `CANDIDATE_HYPOTHESIZED` | inverter topology/clamp details unknown | no | no |
| Regenerative back-EMF while the rotor spins | `CANDIDATE_HYPOTHESIZED`, **conditional on a permanent-magnet rotor and rotation** | motor type unverified (`MOTOR_CONTROLLER_COMPATIBILITY = BLOCKED`) | no | no |
| STO timing race (gate-drive disable vs other shutdown paths) | `CANDIDATE_HYPOTHESIZED` | STO/shutdown architecture not documented | no | no |
| Noise chatter around the threshold | `CANDIDATE_HYPOTHESIZED` | noise floor/scale unresolved | no | no |

**Removed as unsupported:** the "0.5–2.5 ms" contactor-bounce duration, "1.0 ms dip" and "surges back to 50 A" (R2 F1); the "V_f ≈ 0.7 V" clamp-voltage claim (R2 F2); the diode clamp counter-voltage "(V_bus + 2·V_f)" (R2-R1 `rms_model_domain.md`); and any statement that these mechanisms occur or have a bounded duration. Promotion from `CANDIDATE` requires direct measurement with traceable evidence or OEM documentation for the exact unit.

## 7. Test vectors (executed by `persistence_modeb_reference.py` and `audit_r3.py`)

`I_guarded = 0.410`, `HI = 1.0`, `LO = 0.1`; frames `k = 0,1,…` unless stated.

| ID | Sequence | Expected |
| :--- | :--- | :--- |
| TV01 | 50×HI then 250×LO | `k_start=50`, `k_qualified=150`, 101 points, 100 intervals, logical 15000 µs, no anomaly |
| TV02 | 50×HI, 100×LO, 50×HI | **not** qualified (100 points < 101); `PRE_QUALIFICATION_REBOUND_RESET` at k=150 |
| TV03 | 50×HI, 101×LO, 1×HI, 20×LO | qualified at 150; anomaly at 151; state S3 |
| TV04 | 10×HI, 51×LO, 1×HI, 240×LO | rebound frame k=61 not a start; `k_start=62`, `k_qualified=162` |
| TV05a | 50×HI, 250×(RMS = threshold) | strict: never qualifies |
| TV05b | same, `inclusive=True` | qualifies, `k_start=50`, `k_qualified=150` |
| TV06 | frame k=100 missing (50×HI, 50×LO, then LO from k=101) | candidate reset by gap; `k_start=101`, `k_qualified=201` |
| TV07 | LO from k=20 (first valid RMS frame) | `k_start=20`, `k_qualified=120`, flagged `…AT_FIRST_FRAME_OF_RECORD` |
| TV08 | 300×HI | never qualifies |
| TV09 | 101×LO, 1×HI, 300×LO | S3 latched; later LO frames change nothing; no second qualification |
| TV10 | 101×LO, NaN, 10×LO | `INVALID_FRAME`; state stays S2; **no** anomaly |

## 8. Status

```text
PERSISTENCE_MODE_B                  = DEFINED_PENDING_IMPLEMENTATION_AUDIT
POST_QUALIFICATION_REBOUND          = EXPLICIT_SEMANTICS_DEFINED (record-level; no actuation)
T_PERSIST_10_MS                     = CANDIDATE_ONLY
```
