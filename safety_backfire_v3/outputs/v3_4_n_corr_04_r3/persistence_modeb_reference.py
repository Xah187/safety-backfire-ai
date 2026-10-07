#!/usr/bin/env python3
"""
V3.4-N-CORR-04-R3 — Mode-B persistence reference model (executable, deterministic).

PURPOSE
-------
Unambiguous executable definition of the Mode-B persistence semantics over a stream of
RMS frames I_RMS[k] (k = integer frame index, logical step 0.1 ms).

GOVERNANCE (hard constraints encoded in the API)
------------------------------------------------
* PASSIVE OBSERVER ONLY.  The class exposes NO command, enable, restore, re-arm, reset-
  vehicle or actuator method and returns only annotation records.
  RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO.
* "QUALIFIED" means ONLY: CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED.
  Traction de-energization is NOT measured here: TRACTION_DEENERGIZED = NOT_DIRECTLY_MEASURED.
* Timestamps produced here are LOGICAL (k * 100 us, exact integers).  They are NOT
  physical acquisition timestamps (see timing_timestamp_governance.md).
* Comparator is a declared parameter.  Default = STRICT (I_RMS < I_guarded qualifies;
  I_RMS == I_guarded does NOT).  The legacy documents disagree (<= vs <); see
  persistence_semantics_v5.md section 2.
"""

import math

# ---- Mode-B constants ------------------------------------------------------
STEP_US = 100                 # logical evaluation step: 0.1 ms
ELAPSED_INTERVALS = 100       # required elapsed intervals
EVAL_POINTS = ELAPSED_INTERVALS + 1   # 101 evaluation points (first qualifying frame included)
NOMINAL_LOGICAL_DURATION_US = ELAPSED_INTERVALS * STEP_US   # 10_000 us = 10.0 ms (logical, nominal)

# ---- Record-state names (NO "terminal safe state" wording) -----------------
S0_NO_CANDIDATE = "S0_NO_CANDIDATE"
S1_CANDIDATE_COUNTING = "S1_CANDIDATE_COUNTING"
S2_QUALIFIED_MONITORING = "S2_QUALIFIED_MONITORING"            # monitoring continues
S3_POST_QUALIFICATION_ANOMALY_LATCHED = "S3_POST_QUALIFICATION_ANOMALY_LATCHED"  # record-latched


class ModeBPersistence:
    def __init__(self, i_guarded, inclusive=False):
        self.i_guarded = float(i_guarded)
        self.inclusive = bool(inclusive)
        self.state = S0_NO_CANDIDATE
        self.points = 0               # number of consecutive qualifying evaluation points counted
        self.k_start = None
        self.k_qualified = None
        self.k_anomaly = None
        self.prev_k = None
        self.first_k = None
        self.events = []              # list of (k, event_name) -- annotations only
        self.frames_after_latch = 0

    # -- comparator -------------------------------------------------------
    def _qualifies(self, rms):
        return (rms <= self.i_guarded) if self.inclusive else (rms < self.i_guarded)

    def _ev(self, k, name):
        self.events.append((k, name))

    # -- single deterministic evaluation step ---------------------------------
    def step(self, k, rms):
        """
        Process frame k.  Order of operations is fixed:
          1. gap check (k must equal prev_k + 1 after the first frame)
          2. non-finite check
          3. state transition on the comparator result
        """
        # 1. gap handling
        if self.prev_k is not None and k != self.prev_k + 1:
            self._ev(k, "FRAME_GAP")
            if self.state == S1_CANDIDATE_COUNTING:
                self._reset_candidate()
                self._ev(k, "CANDIDATE_RESET_BY_GAP")
        if self.first_k is None:
            self.first_k = k
        self.prev_k = k

        # 2. non-finite sample: never qualifies, never counted as a rebound after qualification
        if not math.isfinite(rms):
            self._ev(k, "INVALID_FRAME")
            if self.state == S1_CANDIDATE_COUNTING:
                self._reset_candidate()
                self._ev(k, "CANDIDATE_RESET_BY_INVALID_FRAME")
            elif self.state == S3_POST_QUALIFICATION_ANOMALY_LATCHED:
                self.frames_after_latch += 1
            return

        q = self._qualifies(rms)

        # 3. transitions
        if self.state == S0_NO_CANDIDATE:
            if q:
                self.state = S1_CANDIDATE_COUNTING
                self.k_start = k
                self.points = 1                      # first qualifying frame IS evaluation point #1
                self._ev(k, "CANDIDATE_START")
                if k == self.first_k:
                    # cannot distinguish 'already below at record start' from a genuine crossing
                    self._ev(k, "CANDIDATE_START_AT_FIRST_FRAME_OF_RECORD")
            # non-qualifying frame in S0: nothing (a rebound frame is never a start)

        elif self.state == S1_CANDIDATE_COUNTING:
            if q:
                self.points += 1                     # first increment occurs on the SECOND point
                if self.points == EVAL_POINTS:       # 101st point <=> 100 elapsed intervals
                    self.state = S2_QUALIFIED_MONITORING
                    self.k_qualified = k
                    self._ev(k, "QUALIFIED_CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED")
            else:
                self._ev(k, "PRE_QUALIFICATION_REBOUND_RESET")
                self._reset_candidate()              # rebound frame does not start a new candidate

        elif self.state == S2_QUALIFIED_MONITORING:
            if not q:
                self.state = S3_POST_QUALIFICATION_ANOMALY_LATCHED
                self.k_anomaly = k
                self._ev(k, "POST_QUALIFICATION_REBOUND_ANOMALY_LATCHED")

        else:  # S3: latched; monitoring/logging continues, NO outbound transition
            self.frames_after_latch += 1

    def _reset_candidate(self):
        self.state = S0_NO_CANDIDATE
        self.points = 0
        self.k_start = None

    # -- annotation record (read-only) ---------------------------------------
    def record(self):
        qualified = self.k_qualified is not None
        return {
            "state": self.state,
            "CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED": qualified,
            "TRACTION_DEENERGIZED": "NOT_DIRECTLY_MEASURED",
            "POST_QUALIFICATION_ANOMALY": self.k_anomaly is not None,
            "k_start": self.k_start if self.state != S0_NO_CANDIDATE else self._last_start(),
            "k_qualified": self.k_qualified,
            "k_anomaly": self.k_anomaly,
            "logical_t_qualified_us": None if not qualified else self.k_qualified * STEP_US,
            "logical_t_anomaly_us": None if self.k_anomaly is None else self.k_anomaly * STEP_US,
            "evaluation_points_at_qualification": EVAL_POINTS if qualified else None,
            "elapsed_intervals_at_qualification": ELAPSED_INTERVALS if qualified else None,
            "events": list(self.events),
        }

    def _last_start(self):
        # start index of the (now qualified or latched) candidate, if any
        if self.k_qualified is not None:
            return self.k_qualified - ELAPSED_INTERVALS
        return None


def run_stream(rms_by_k, i_guarded, inclusive=False):
    """rms_by_k: iterable of (k, rms).  Returns the final annotation record."""
    fsm = ModeBPersistence(i_guarded, inclusive=inclusive)
    for k, r in rms_by_k:
        fsm.step(k, r)
    return fsm.record()


# ---- Deterministic test vectors -----------------------------------------------
IG = 0.410
HI, LO = 1.000, 0.100


def _seq(spec, k0=0):
    """spec: list of (count, value); returns [(k, value)] with consecutive k from k0."""
    out, k = [], k0
    for count, val in spec:
        for _ in range(count):
            out.append((k, val))
            k += 1
    return out


def test_vectors():
    tv = []
    # TV01 nominal
    tv.append(("TV01_nominal_start50",
               _seq([(50, HI), (250, LO)]), False,
               dict(qualified=True, k_start=50, k_qualified=150, anomaly=False,
                    t_qualified_us=15000)))
    # TV02 exactly 100 points is NOT enough
    tv.append(("TV02_100_points_not_enough",
               _seq([(50, HI), (100, LO), (50, HI)]), False,
               dict(qualified=False, k_start=None, k_qualified=None, anomaly=False,
                    t_qualified_us=None, events_contain="PRE_QUALIFICATION_REBOUND_RESET")))
    # TV03 exactly 101 points then rebound next frame
    tv.append(("TV03_101_points_then_rebound",
               _seq([(50, HI), (101, LO), (1, HI), (20, LO)]), False,
               dict(qualified=True, k_start=50, k_qualified=150, anomaly=True, k_anomaly=151,
                    t_qualified_us=15000, final_state=S3_POST_QUALIFICATION_ANOMALY_LATCHED)))
    # TV04 rebound frame does not start a candidate; restart after it
    tv.append(("TV04_reset_then_restart",
               _seq([(10, HI), (51, LO), (1, HI), (240, LO)]), False,
               dict(qualified=True, k_start=62, k_qualified=162, anomaly=False,
                    t_qualified_us=16200)))
    # TV05a strict: exact equality never qualifies
    tv.append(("TV05a_equality_strict",
               _seq([(50, HI), (250, IG)]), False,
               dict(qualified=False, k_start=None, k_qualified=None, anomaly=False,
                    t_qualified_us=None)))
    # TV05b inclusive variant qualifies on equality (documents the comparator sensitivity)
    tv.append(("TV05b_equality_inclusive",
               _seq([(50, HI), (250, IG)]), True,
               dict(qualified=True, k_start=50, k_qualified=150, anomaly=False,
                    t_qualified_us=15000)))
    # TV06 frame gap resets an in-progress candidate; the gap frame itself may start a new one
    gap = _seq([(50, HI), (50, LO)]) + _seq([(250, LO)], k0=101)    # k=100 missing
    tv.append(("TV06_gap_resets_candidate", gap, False,
               dict(qualified=True, k_start=101, k_qualified=201, anomaly=False,
                    t_qualified_us=20100, events_contain="CANDIDATE_RESET_BY_GAP")))
    # TV07 below threshold already at first valid frame (k=20): flagged, still counted
    tv.append(("TV07_below_at_first_valid_frame",
               _seq([(150, LO)], k0=20), False,
               dict(qualified=True, k_start=20, k_qualified=120, anomaly=False,
                    t_qualified_us=12000,
                    events_contain="CANDIDATE_START_AT_FIRST_FRAME_OF_RECORD")))
    # TV08 never below
    tv.append(("TV08_never_below", _seq([(300, HI)]), False,
               dict(qualified=False, k_start=None, k_qualified=None, anomaly=False,
                    t_qualified_us=None)))
    # TV09 latched anomaly cannot re-arm: later low frames do not change state or create 2nd qualification
    tv.append(("TV09_latched_cannot_rearm",
               _seq([(0, HI), (101, LO), (1, HI), (300, LO)]), False,
               dict(qualified=True, k_start=0, k_qualified=100, anomaly=True, k_anomaly=101,
                    t_qualified_us=10000, final_state=S3_POST_QUALIFICATION_ANOMALY_LATCHED)))
    # TV10 non-finite after qualification is NOT a rebound anomaly
    nan = float("nan")
    tv.append(("TV10_invalid_frame_post_qualification",
               _seq([(101, LO), (1, nan), (10, LO)]), False,
               dict(qualified=True, k_start=0, k_qualified=100, anomaly=False,
                    t_qualified_us=10000, final_state=S2_QUALIFIED_MONITORING,
                    events_contain="INVALID_FRAME")))
    return tv


def run_test_vectors(i_guarded=IG):
    results = []
    for name, seq, inclusive, exp in test_vectors():
        rec = run_stream(seq, i_guarded, inclusive=inclusive)
        ok = True
        why = []

        def chk(cond, msg):
            nonlocal ok
            if not cond:
                ok = False
                why.append(msg)
        chk(rec["CURRENT_BELOW_GUARDED_THRESHOLD_PERSISTED"] == exp["qualified"], "qualified flag")
        chk(rec["k_qualified"] == exp["k_qualified"], f"k_qualified {rec['k_qualified']} != {exp['k_qualified']}")
        chk(rec["POST_QUALIFICATION_ANOMALY"] == exp["anomaly"], "anomaly flag")
        chk(rec["logical_t_qualified_us"] == exp["t_qualified_us"], "t_qualified_us")
        if exp["qualified"]:
            chk(rec["k_start"] == exp["k_start"], f"k_start {rec['k_start']} != {exp['k_start']}")
            chk(rec["k_qualified"] - rec["k_start"] == ELAPSED_INTERVALS, "100 elapsed intervals")
            chk((rec["k_qualified"] - rec["k_start"]) * STEP_US == NOMINAL_LOGICAL_DURATION_US, "10_000 us")
            chk(rec["evaluation_points_at_qualification"] == 101, "101 evaluation points")
        if "k_anomaly" in exp:
            chk(rec["k_anomaly"] == exp["k_anomaly"], "k_anomaly")
        if "final_state" in exp:
            chk(rec["state"] == exp["final_state"], f"final state {rec['state']}")
        if "events_contain" in exp:
            chk(any(e[1] == exp["events_contain"] for e in rec["events"]), "event " + exp["events_contain"])
        chk(rec["TRACTION_DEENERGIZED"] == "NOT_DIRECTLY_MEASURED", "traction label")
        results.append({"name": name, "passed": ok, "why": why, "record": rec})
    return results


if __name__ == "__main__":
    import json
    import sys
    res = run_test_vectors()
    for r in res:
        print(("PASS " if r["passed"] else "FAIL ") + r["name"] + ("" if r["passed"] else f"  {r['why']}"))
    sys.exit(0 if all(r["passed"] for r in res) else 1)
