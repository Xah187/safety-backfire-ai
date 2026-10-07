"""
backfire_state_machine.py
Milestone V3.4-H — Deterministic Backfire Evidence State Machine & Gate Validator

GOVERNANCE INVARIANTS:
  - Prototype / Sandbox execution only.
  - Model H parameters frozen invariant: k0=2.40, beta_d=0.08, beta_l=0.12, beta_pitch=0.22.
  - No model training, no retraining, no threshold tuning.
  - Deterministic evaluation: no random seeds, no heuristic heuristics, no machine learning.
  - Strictly distinguishes PRIMARY_NEAR_MISS, BACKFIRE_CANDIDATE, and INSUFFICIENT_BACKFIRE_EVIDENCE.
"""

from typing import Dict, Any, Tuple, List


class BackfireStateMachine:
    """
    Deterministic Two-Stage State Machine implementing Milestone V3.4-G specifications:
      Stage A: Primary Interaction & Near-Miss Detection
      Stage B: Backfire Evidence Gates (G1 to G4)
    """

    def __init__(self):
        self.tau_max_s = 2.0  # Maximum propagation latency between intervention and secondary onset
        self.min_post_duration_s = 4.0  # Minimum post window duration

    def evaluate_stage_a(self, evidence: Dict[str, Any]) -> Tuple[str, float]:
        """
        Stage A: Primary Interaction Filter
        Computes or ingests PRIMARY_INTERACTION_SCORE:
          Score = 0.60 * prox_score + 0.40 * dur_score
        """
        pi = evidence.get("primary_interaction", {})
        if "primary_interaction_score" in pi:
            score = float(pi["primary_interaction_score"])
        else:
            d_px = float(pi.get("minimum_separation_px", 600.0))
            n_frames = int(pi.get("co_occurring_frames", 0))
            prox_score = max(0.0, min(1.0, 1.0 - (d_px / 600.0)))
            dur_score = min(1.0, n_frames / 150.0)
            score = round(0.60 * prox_score + 0.40 * dur_score, 3)

        # Stage A threshold: score >= 0.15 indicates an interaction of interest
        if score >= 0.15:
            return "PRIMARY_INTERACTION_DETECTED", score
        else:
            return "NON_CANDIDATE_INTERACTION", score

    def evaluate_gate_1_intervention(self, evidence: Dict[str, Any]) -> Tuple[str, str]:
        """
        Gate 1: Intervention Confirmation Gate
        Verifies whether an active safety intervention (brake, swerve, yield) occurred.
        """
        sig = evidence.get("intervention_signal", {})
        telemetry = evidence.get("telemetry", {})

        det = sig.get("intervention_detected", False)
        status = sig.get("evidence_status", "NOT_OBSERVED")
        i_type = sig.get("intervention_type", "NONE")

        # Telemetry verification if available
        brake_applied = telemetry.get("brake_applied", None)
        decel = telemetry.get("longitudinal_decel_mps2", None)

        if status == "UNAVAILABLE" or i_type == "UNKNOWN":
            return "UNKNOWN", "Intervention evidence is unavailable or status is unknown."

        if det and status in ["OBSERVED", "PARTIAL"]:
            return "PASS", f"Intervention confirmed ({i_type})."
        else:
            return "FAIL", "No confirmed intervention signal observed."

    def evaluate_gate_2_observability(self, evidence: Dict[str, Any]) -> Tuple[str, str]:
        """
        Gate 2: Observability Gate
        Enforces physical line-of-sight across primary, secondary entry, and secondary depth.
        """
        obs = evidence.get("observability", {})
        pz_stat = obs.get("primary_zone_status", "UNKNOWN")
        sz_stat = obs.get("secondary_zone_status", "UNKNOWN")
        post_stat = obs.get("post_window_status", "UNKNOWN")
        sz_depth_vis = obs.get("secondary_depth_observable", False)
        sz_entry_vis = obs.get("secondary_entry_observable", False)

        sz_def = evidence.get("secondary_zone", {}).get("zone_definition_type", "UNKNOWN")
        if sz_def == "UNKNOWN" or sz_stat == "NONE":
            return "FAIL", "Secondary zone is undefined or unobservable (NONE)."

        if pz_stat in ["NONE", "UNKNOWN"]:
            return "FAIL", f"Primary zone observability is {pz_stat}."

        if post_stat in ["INADEQUATE", "UNKNOWN"]:
            return "FAIL", f"Post-intervention observation window is {post_stat}."

        # Rule from V3.4-G: If secondary depth is occluded, depth evidence is UNAVAILABLE
        if not sz_depth_vis:
            # If entry is visible but depth is not, secondary zone cannot confirm depth hazard
            return "FAIL", "Secondary zone interior depth is occluded (SECONDARY_DEPTH_EVIDENCE = UNAVAILABLE)."

        if pz_stat == "FULL" and sz_stat == "FULL" and sz_entry_vis and sz_depth_vis and post_stat == "ADEQUATE":
            return "PASS", "Complete line-of-sight verified across primary and secondary zones."
        
        return "UNKNOWN", "Observability status could not be conclusively determined."

    def evaluate_gate_3_secondary_risk_delta(self, evidence: Dict[str, Any]) -> Tuple[str, str]:
        """
        Gate 3: Secondary Risk Delta Gate
        Computes Delta_R_sec = R_sec(POST) - R_sec(PRE).
        """
        r_pre_obj = evidence.get("secondary_risk_pre", {})
        r_post_obj = evidence.get("secondary_risk_post", {})
        delta_obj = evidence.get("delta_secondary_risk", {})

        status_pre = r_pre_obj.get("evidence_status", "UNAVAILABLE")
        status_post = r_post_obj.get("evidence_status", "UNAVAILABLE")

        if status_pre == "UNAVAILABLE" or status_post == "UNAVAILABLE":
            return "UNKNOWN", "Secondary zone hazard state is unavailable in PRE or POST window."

        delta_val = delta_obj.get("delta_value")
        if delta_val is None:
            r_pre = float(r_pre_obj.get("risk_score", 0.0))
            r_post = float(r_post_obj.get("risk_score", 0.0))
            delta_val = round(r_post - r_pre, 4)

        # Invariant: Delta_R_sec <= 0 means risk did not increase -> PRIMARY_NEAR_MISS
        if delta_val <= 0.0:
            return "FAIL", f"Secondary risk did not increase (Delta_R_sec = {delta_val:.4f} <= 0)."
        elif delta_val < 0.01:
            # Insignificant noise level delta
            return "FAIL", f"Secondary risk increase is within negligible sensor noise threshold (Delta_R_sec = {delta_val:.4f})."
        else:
            return "PASS", f"Net secondary risk increase observed (Delta_R_sec = +{delta_val:.4f})."

    def evaluate_gate_4_causal_and_confounders(self, evidence: Dict[str, Any]) -> Tuple[str, str]:
        """
        Gate 4: Causal Linkage & Confounder Isolation Gate
        Verifies:
          1. Strict chronological ordering T0 < T1 < T2 <= T3 <= T4 < T5
          2. Latency delta_t <= tau_max (2.0s)
          3. Continuous physical redirection path
          4. Confounder absence or non-interference
        """
        t_order = evidence.get("temporal_order", {})
        stages_valid = t_order.get("chronological_stages_valid", False)
        if not stages_valid:
            return "FAIL", "Temporal stage precedence violated (T0 < T1 < T2 <= T3 <= T4 < T5 not satisfied)."

        # Latency check
        causal_link = evidence.get("causal_link", {})
        delta_t = causal_link.get("latency_to_secondary_onset_s")
        if delta_t is not None and delta_t > self.tau_max_s:
            return "FAIL", f"Propagation latency ({delta_t:.2f}s) exceeds maximum causal threshold ({self.tau_max_s:.2f}s)."

        # Physical trajectory path
        path_status = causal_link.get("causal_chain_status", "UNSUPPORTED")
        path_obs = causal_link.get("observable_causal_path", "FALSE")
        redirection = evidence.get("risk_redirection", {}).get("redirection_observed", False)

        if not redirection or path_obs == "FALSE" or path_status == "UNSUPPORTED":
            return "FAIL", "No continuous physical trajectory linking intervention to secondary exposure."

        # Confounder isolation
        conf = evidence.get("confounders", {})
        c_present = conf.get("confounders_present", "UNKNOWN")
        c_iso = conf.get("causal_isolation_status", "UNKNOWN")

        if c_present == "UNKNOWN" or c_iso == "UNKNOWN":
            return "UNKNOWN", "Confounder status is unknown; causal isolation cannot be verified."

        if c_present == "YES" and c_iso == "FAILED":
            types = conf.get("confounder_types", ["UNSPECIFIED"])
            return "FAIL", f"Causal isolation failed: independent confounder ({', '.join(types)}) explains secondary change."

        if c_iso == "ISOLATED" and (c_present == "NO" or c_present == "NON_COMPETITIVE"):
            return "PASS", "Causal path verified; independent confounders successfully ruled out."

        return "UNKNOWN", "Causal isolation status inconclusive."

    def evaluate(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes full deterministic state machine across Stage A and Stage B gates.
        """
        eid = evidence.get("event_id", "UNKNOWN_EVENT")
        stage_a_result, interaction_score = self.evaluate_stage_a(evidence)

        # Stage B Gates
        g1_res, g1_reason = self.evaluate_gate_1_intervention(evidence)
        g2_res, g2_reason = self.evaluate_gate_2_observability(evidence)
        g3_res, g3_reason = self.evaluate_gate_3_secondary_risk_delta(evidence)
        g4_res, g4_reason = self.evaluate_gate_4_causal_and_confounders(evidence)

        gate_results = {
            "G1_Intervention_Confirmation": g1_res,
            "G2_Observability": g2_res,
            "G3_Secondary_Risk_Delta": g3_res,
            "G4_Causal_Isolation": g4_res
        }

        # Deterministic State Machine Decision Logic
        failure_reasons = []
        if g1_res != "PASS": failure_reasons.append(f"G1: {g1_reason}")
        if g2_res != "PASS": failure_reasons.append(f"G2: {g2_reason}")
        if g3_res != "PASS": failure_reasons.append(f"G3: {g3_reason}")
        if g4_res != "PASS": failure_reasons.append(f"G4: {g4_reason}")

        # Classification rules
        if g1_res == "PASS" and g2_res == "PASS" and g3_res == "PASS" and g4_res == "PASS":
            candidate_class = "BACKFIRE_CANDIDATE"
            evidence_status = "OBSERVED"
        elif g3_res == "FAIL":
            # Delta_R_sec <= 0 means intervention stopped hazard without secondary increase
            candidate_class = "PRIMARY_NEAR_MISS"
            evidence_status = "OBSERVED"
        elif g1_res == "FAIL":
            # No intervention confirmed -> primary near miss / nominal
            candidate_class = "PRIMARY_NEAR_MISS"
            evidence_status = "OBSERVED"
        else:
            # G2 failed (observability), G4 failed (confounder/causal/latency), or UNKNOWN
            candidate_class = "INSUFFICIENT_BACKFIRE_EVIDENCE"
            evidence_status = "UNAVAILABLE" if (g2_res != "PASS") else "PARTIAL"

        audit_trace = [
            f"Stage A: {stage_a_result} (Score: {interaction_score:.3f})",
            f"Gate 1 [Intervention]: {g1_res} -> {g1_reason}",
            f"Gate 2 [Observability]: {g2_res} -> {g2_reason}",
            f"Gate 3 [Secondary Delta]: {g3_res} -> {g3_reason}",
            f"Gate 4 [Causal Isolation]: {g4_res} -> {g4_reason}",
            f"Final Candidate Class: {candidate_class} ({evidence_status})"
        ]

        return {
            "event_id": eid,
            "stage_a_result": stage_a_result,
            "primary_interaction_score": interaction_score,
            "gate_results": gate_results,
            "candidate_class": candidate_class,
            "evidence_status": evidence_status,
            "failure_reasons": failure_reasons,
            "audit_trace": audit_trace,
            "ground_truth_status": "NOT_ESTABLISHED"
        }
