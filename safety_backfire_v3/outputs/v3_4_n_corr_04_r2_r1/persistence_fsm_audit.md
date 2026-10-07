# V3.4-N-CORR-04-R2-R1 — Persistence Finite State Machine & Post-Qualification Rebound Audit

**Document Identifier:** `outputs/v3_4_n_corr_04_r2_r1/persistence_fsm_audit.md`  
**Milestone:** `V3.4-N-CORR-04-R2-R1`  
**Classification:** Digital Verification State Machine Architecture & Fault Recovery Governance  
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

## 1. Executive Summary & Problem Audit

In Milestone V3.4-N-CORR-04-R2 (`persistence_state_machine_v3.md`), an architectural ambiguity existed in the finite state machine:
- Section 3 labeled `STATE_3_QUALIFIED` as a "(Terminal Safe State)".
- However, the FSM diagram included a transition from `STATE_3_QUALIFIED` back to `STATE_0_ACTIVE` labeled "Any post-qualification surge $I_{\text{RMS}} > 0.410\,\text{A}$".
- If `STATE_3` is terminal, it cannot have an outbound transition back to active.
- Furthermore, returning to `STATE_0_ACTIVE` implied that the research DAQ software could "reactivate" traction or re-arm active driving, directly violating the hard invariant:
  $$\mathbf{RESEARCH\_DAQ\_ACTUATION\_AUTHORITY = ZERO}$$

Per Section 7 and Section 8 of the mandate, this document:
1. Formulates the exact deterministic pseudocode for Mode B discrete persistence execution.
2. Resolves post-qualification rebound semantics by separating the historical milestone declaration from subsequent post-qualification monitoring faults.
3. Preserves the passive listener boundary of the research DAQ.

---

## 2. Post-Qualification Rebound Governance Decision

When a transient current surge ($I_{\text{RMS}} > I_{\text{guarded}}$) occurs *after* the 100-step persistence window has completed and safe state has been declared at $t_{\text{qualified}}$:

### 2.1 Competing Governance Models Evaluated
1. **Model 1: Retrospective Invalidation (Rewriting History):**
   Cancels the historical timestamp $t_{\text{qualified}}$ as if it never occurred.
   *Critique:* Metrologically unsound. The digitized oscillogram objectively proves that the current *was* below threshold for 10.0 ms. Rewriting recorded time-series timestamps compromises evidence integrity.
2. **Model 2: State Reset to Active Driving:**
   Transitions back to `STATE_0_ACTIVE` and waits for a new de-energization sequence.
   *Critique:* Violates safety governance. Once an E-Stop de-energization qualification has been reached, a subsequent surge is a **critical system anomaly** (e.g. unintended contactor re-closure or uncontrolled back-EMF surge). It must not be treated as routine pre-shutdown driving.
3. **Model 3: Separate Asynchronous Safety Violation Fault (Adopted):**
   The historical milestone `ELECTRICAL_TRACTION_DEENERGIZED` timestamp ($t_{\text{qualified}}$) remains documented in the immutable capture ledger. However, any subsequent current excursion beyond threshold raises an asynchronous critical diagnostic fault:
   $$\mathbf{FAULT\_POST\_QUALIFICATION\_REBOUND}$$
   and latches the monitoring state into:
   $$\mathbf{STATE\_4\_REBOUND\_FAULT}$$
   This fault invalidates the test trial, aborts characterization logging, and flags the hardware for safety inspection.

### 2.2 Preserving Zero Actuation Authority
The research DAQ software does **NOT** intervene in vehicle hardware. It does not open contactors, energize brakes, or restore gate drives. The DAQ solely asserts software diagnostic error flags, terminates recording, and records the fault in the immutable event package.

---

## 5-State Machine Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        STATE 0: MONITORING_ACTIVE                      │
│                        (I_RMS[k] > I_guarded)                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ I_RMS[k] <= I_guarded
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        STATE 1: ARMED                                  │
│                        k_start = k                                     │
│                        t_persist_start = k * 0.1 ms                    │
│                        elapsed_intervals = 0                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ [Always advances to STATE 2 on k+1]
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        STATE 2: PERSISTING                             │
│                        elapsed_intervals = k - k_start                 │
│                        (1 <= elapsed_intervals < 100)                  │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │                               │
                    │ I_RMS[k] <= I_guarded         │ I_RMS[k] > I_guarded
                    │ AND elapsed_intervals == 100  │ (REBOUND DETECTED)
                    │ AND t_k <= 48.8 ms            ▼
                    │               ┌────────────────────────────────────┐
                    │               │ REBOUND RESET:                     │
                    │               │ Reset to STATE 0: MONITORING_ACTIVE│
                    │               │ Log PRE_QUAL_REBOUND event         │
                    ▼               └────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────────────┐
│                        STATE 3: QUALIFIED                              │
│                        k_qualified = k                                 │
│                        t_qualified = k * 0.1 ms                        │
│                        ELECTRICAL_TRACTION_DEENERGIZED = TRUE          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ I_RMS[k] > I_guarded
                                    │ (POST-QUALIFICATION EXCURSION)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        STATE 4: REBOUND_FAULT (LATCHED)                │
│                        FAULT_POST_QUALIFICATION_REBOUND = ASSERTED     │
│                        TRIAL_VALIDITY = INVALIDATED                    │
│                        DAQ_STATUS = ANOMALY_ABORT                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Deterministic Reference Pseudocode

The following Python-equivalent pseudocode provides an exact, unambiguous implementation of Mode B persistence logic:

```python
def evaluate_traction_persistence(
    rms_stream,           # Array of moving RMS samples I_RMS[k]
    i_guarded=0.410,       # Guarded current threshold in A RMS
    step_size_ms=0.1,      # Step size Delta_t_step (0.1 ms)
    required_intervals=100,# Mode B: exactly 100 intervals (10.0 ms)
    latency_limit_ms=48.8  # Guarded total shutdown latency limit
):
    """
    Deterministic Mode B Persistence Finite State Machine.
    Evaluates discrete sampled RMS frames and declares safe state.
    """
    # State Enumeration
    STATE_ACTIVE = 0
    STATE_ARMED = 1
    STATE_PERSISTING = 2
    STATE_QUALIFIED = 3
    STATE_REBOUND_FAULT = 4
    
    current_state = STATE_ACTIVE
    k_start = None
    t_persist_start = None
    k_qualified = None
    t_qualified = None
    
    diagnostic_events = []
    
    for k, i_rms_k in enumerate(rms_stream):
        t_k = k * step_size_ms  # Exact discrete frame timestamp
        
        # -------------------------------------------------------------
        # STATE 0: ACTIVE (Pre-shutdown or above threshold)
        # -------------------------------------------------------------
        if current_state == STATE_ACTIVE:
            if i_rms_k <= i_guarded:
                current_state = STATE_ARMED
                k_start = k
                t_persist_start = t_k
                diagnostic_events.append({
                    "frame": k,
                    "timestamp_ms": t_k,
                    "event": "PERSISTENCE_ARMED",
                    "i_rms_a": i_rms_k
                })
                # Immediately advance to PERSISTING to evaluate next frame
                current_state = STATE_PERSISTING
                
        # -------------------------------------------------------------
        # STATE 2: PERSISTING (Counting elapsed intervals)
        # -------------------------------------------------------------
        elif current_state == STATE_PERSISTING:
            elapsed_intervals = k - k_start
            
            # Check for pre-qualification rebound excursion
            if i_rms_k > i_guarded:
                diagnostic_events.append({
                    "frame": k,
                    "timestamp_ms": t_k,
                    "event": "PRE_QUALIFICATION_REBOUND_RESET",
                    "i_rms_a": i_rms_k,
                    "aborted_intervals": elapsed_intervals
                })
                # Reset counter and return to active monitoring
                current_state = STATE_ACTIVE
                k_start = None
                t_persist_start = None
                continue
            
            # Check for completion of 100 elapsed intervals
            if elapsed_intervals == required_intervals:
                # Total points evaluated: k_start through k (101 points)
                # Elapsed time: 100 * 0.1 ms = 10.0 ms
                if t_k <= latency_limit_ms:
                    current_state = STATE_QUALIFIED
                    k_qualified = k
                    t_qualified = t_k
                    diagnostic_events.append({
                        "frame": k,
                        "timestamp_ms": t_k,
                        "event": "ELECTRICAL_TRACTION_DEENERGIZED_QUALIFIED",
                        "t_start_ms": t_persist_start,
                        "t_qualified_ms": t_qualified,
                        "elapsed_hold_ms": t_qualified - t_persist_start
                    })
                else:
                    # Latency budget exceeded before 10.0 ms completed
                    diagnostic_events.append({
                        "frame": k,
                        "timestamp_ms": t_k,
                        "event": "LATENCY_BUDGET_EXCEEDED_FAIL",
                        "t_k_ms": t_k,
                        "limit_ms": latency_limit_ms
                    })
                    return {
                        "status": "PERSISTENCE_LATENCY_FAIL",
                        "events": diagnostic_events
                    }
                    
        # -------------------------------------------------------------
        # STATE 3: QUALIFIED (Monitoring for post-qualification surges)
        # -------------------------------------------------------------
        elif current_state == STATE_QUALIFIED:
            # Safe state has been declared; monitor for anomalous rebound
            if i_rms_k > i_guarded:
                current_state = STATE_REBOUND_FAULT
                diagnostic_events.append({
                    "frame": k,
                    "timestamp_ms": t_k,
                    "event": "FAULT_POST_QUALIFICATION_REBOUND",
                    "i_rms_a": i_rms_k,
                    "declared_t_qualified_ms": t_qualified
                })
                # Latched fault; trial is invalidated
                return {
                    "status": "POST_QUALIFICATION_REBOUND_ABORT",
                    "t_qualified_historical_ms": t_qualified,
                    "rebound_frame": k,
                    "rebound_time_ms": t_k,
                    "events": diagnostic_events
                }
                
        # -------------------------------------------------------------
        # STATE 4: REBOUND_FAULT (Latched anomaly)
        # -------------------------------------------------------------
        elif current_state == STATE_REBOUND_FAULT:
            pass  # Retain latched fault condition
            
    # Terminal disposition
    if current_state == STATE_QUALIFIED:
        return {
            "status": "PERSISTENCE_PASS",
            "k_start": k_start,
            "t_persist_start_ms": t_persist_start,
            "k_qualified": k_qualified,
            "t_qualified_ms": t_qualified,
            "evaluation_points_count": k_qualified - k_start + 1,  # Exactly 101 points
            "elapsed_hold_duration_ms": t_qualified - t_persist_start, # Exactly 10.0 ms
            "events": diagnostic_events
        }
    else:
        return {
            "status": "PERSISTENCE_INCOMPLETE_OR_UNRESOLVED",
            "final_state": current_state,
            "events": diagnostic_events
        }
```

---

## 5. Audit Compliance Verification

The pseudocode above guarantees:
1. **Zero ambiguity in counter initialization:** Frame $k_{\text{start}}$ initializes the sequence; the first increment occurs on the next frame $k_{\text{start}} + 1$.
2. **Exact Mode B timing:** Exactly $100$ elapsed intervals ($\Delta T = 10.0\,\text{ms}$) separating $k_{\text{start}}$ and $k_{\text{qualified}}$, evaluating exactly $101$ consecutive discrete frames.
3. **Strict separation of rebound mechanisms:** Pre-qualification excursions reset to `STATE_ACTIVE`; post-qualification excursions raise `FAULT_POST_QUALIFICATION_REBOUND` without modifying the historical $t_{\text{qualified}}$ timestamp.
4. **Passive DAQ boundary:** Zero actuation authority is exercised.
