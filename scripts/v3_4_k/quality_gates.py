"""
quality_gates.py
Milestone V3.4-K — Sequential Data Quality Gates with Strict Short-Circuit Semantics

Implements DQ1 through DQ8:
  DQ1_CLOCK_SYNC -> DQ2_CAMERA_INTEGRITY -> DQ3_TELEMETRY_INTEGRITY ->
  DQ4_SECONDARY_SENSOR_INTEGRITY -> DQ5_CALIBRATION_INTEGRITY ->
  DQ6_ZONE_GEOMETRY -> DQ7_EVENT_COMPLETENESS -> DQ8_PROVENANCE

Enforces strict sequential short-circuit for live readiness decisions,
while independently capturing PARALLEL_DIAGNOSTIC_METADATA for engineering root-cause analysis.
"""

from typing import Dict, Any, List, Tuple
from interfaces import ReadinessState


class SequentialDataQualityEngine:
    """
    Executes pre-ingestion data quality verification across multi-modal sensor packages.
    """

    def __init__(self, target_max_skew_ms: float = 33.3, allocated_budget_ms: float = 18.0):
        self.target_max_skew_ms = target_max_skew_ms
        self.allocated_budget_ms = allocated_budget_ms

    def evaluate_dq1_clock_sync(self, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        sync_meta = context.get("sync_metrics", {})
        inter_cam_skew_ms = sync_meta.get("max_inter_camera_skew_ms", 0.0)
        can_skew_ms = sync_meta.get("max_can_skew_ms", 0.0)
        composite_skew_ms = sync_meta.get("composite_skew_ms", inter_cam_skew_ms + can_skew_ms)
        is_monotonic = sync_meta.get("timestamps_monotonic", True)
        has_duplicates = sync_meta.get("timestamps_duplicated", False)
        clock_state = sync_meta.get("clock_state", "LOCKED")

        meta = {
            "inter_cam_skew_ms": inter_cam_skew_ms,
            "can_skew_ms": can_skew_ms,
            "composite_skew_ms": composite_skew_ms,
            "allocated_budget_ms": self.allocated_budget_ms,
            "target_max_skew_ms": self.target_max_skew_ms,
            "clock_state": clock_state
        }

        if not is_monotonic or has_duplicates:
            return "FAIL", "Timestamps non-monotonic or duplicated; clock domain corrupted.", meta

        if clock_state in ["UNLOCKED", "DRIFTING"]:
            return "FAIL", f"Master clock synchronization lost ({clock_state}).", meta

        if composite_skew_ms > self.target_max_skew_ms:
            return "FAIL", f"Composite clock skew ({composite_skew_ms:.1f}ms) exceeds maximum design target ({self.target_max_skew_ms}ms).", meta

        if composite_skew_ms > self.allocated_budget_ms:
            return "PARTIAL", f"Composite skew ({composite_skew_ms:.1f}ms) exceeds allocated budget ({self.allocated_budget_ms}ms) but within system target ({self.target_max_skew_ms}ms).", meta

        return "PASS", f"Synchronization verified within allocated budget ({composite_skew_ms:.1f}ms <= {self.allocated_budget_ms}ms).", meta

    def evaluate_dq2_camera_integrity(self, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        cam_meta = context.get("camera_metrics", {})
        active_cams = cam_meta.get("active_cameras", [])
        expected_cams = ["CAMERA_A", "CAMERA_B", "CAMERA_C", "CAMERA_D"]
        missing = [c for c in expected_cams if c not in active_cams]

        frame_drops_pct = cam_meta.get("max_frame_drop_pct", 0.0)
        corrupted = cam_meta.get("checksum_errors", False)
        black_frames = cam_meta.get("black_frames_detected", False)
        res_mismatch = cam_meta.get("resolution_mismatch", False)
        seq_error = cam_meta.get("sequence_reordered", False)

        meta = {
            "active_cameras": active_cams,
            "missing_cameras": missing,
            "max_frame_drop_pct": frame_drops_pct,
            "checksum_errors": corrupted,
            "black_frames": black_frames
        }

        if missing:
            return "FAIL", f"Missing mandatory camera streams: {missing}", meta
        if corrupted:
            return "FAIL", "Camera codec payload corrupted (checksum mismatch).", meta
        if seq_error:
            return "FAIL", "Camera frame sequence reordered out-of-sequence.", meta
        if res_mismatch:
            return "FAIL", "Camera resolution mismatch (expected contracted 1920x1080).", meta
        if black_frames:
            return "FAIL", "Optical sensor blind/black frames detected during interaction window.", meta
        if frame_drops_pct > 1.0:
            return "FAIL", f"Excessive frame drops ({frame_drops_pct:.2f}% > 1.0% limit).", meta

        return "PASS", "All 4 camera streams intact, uncorrupted, and meeting resolution targets.", meta

    def evaluate_dq3_telemetry_integrity(self, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        telem_meta = context.get("telemetry_metrics", {})
        present = telem_meta.get("stream_present", True)
        loss_pct = telem_meta.get("packet_loss_pct", 0.0)
        missing_sig = telem_meta.get("missing_mandatory_signals", [])
        flatline = telem_meta.get("flatline_detected", False)
        out_of_range = telem_meta.get("out_of_range_detected", False)
        unit_mismatch = telem_meta.get("unit_mismatch_detected", False)

        meta = {
            "stream_present": present,
            "packet_loss_pct": loss_pct,
            "missing_signals": missing_sig,
            "flatline": flatline,
            "out_of_range": out_of_range
        }

        if not present:
            return "FAIL", "Vehicle CAN telemetry stream completely absent.", meta
        if missing_sig:
            return "FAIL", f"Missing mandatory CAN control signals: {missing_sig}", meta
        if flatline:
            return "FAIL", "Sensor flatline detected (frozen values during dynamic maneuver).", meta
        if out_of_range:
            return "FAIL", "Sensor values exceed physically plausible limits (out-of-range).", meta
        if unit_mismatch:
            return "FAIL", "Physical unit mismatch detected in telemetry stream.", meta
        if loss_pct > 5.0:
            return "FAIL", f"Excessive CAN packet loss ({loss_pct:.1f}% > 5.0% limit).", meta

        return "PASS", "Vehicle CAN telemetry complete, continuous, and physically plausible.", meta

    def evaluate_dq4_secondary_sensor_integrity(self, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        sec_meta = context.get("secondary_sensor_metrics", {})
        present = sec_meta.get("sensor_present", True)
        depth_obs = sec_meta.get("depth_observable", True)
        sync_ok = sec_meta.get("sync_valid", True)

        meta = {
            "sensor_present": present,
            "depth_observable": depth_obs,
            "modality": sec_meta.get("modality", "LIDAR_3D")
        }

        if not present:
            return "FAIL", "Secondary zone sensor stream disconnected/absent.", meta
        if not depth_obs:
            return "FAIL", "Secondary zone interior depth is occluded (line-of-sight obstructed).", meta
        if not sync_ok:
            return "FAIL", "Secondary sensor timestamp mismatch exceeding tolerance.", meta

        return "PASS", "Secondary cross-aisle depth is actively observable and synchronized.", meta

    def evaluate_dq5_calibration_integrity(self, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        calib = context.get("calibration_manifest", {})
        valid = calib.get("calibration_present", True)
        stale = calib.get("is_stale", False)
        reproj_error = calib.get("mean_reprojection_error_px", 1.1)
        mismatch = calib.get("camera_id_mismatch", False)

        meta = {
            "calibration_present": valid,
            "mean_reprojection_error_px": reproj_error,
            "is_stale": stale
        }

        if not valid:
            return "FAIL", "Calibration manifest missing or empty.", meta
        if mismatch:
            return "FAIL", "Calibration intrinsics hash does not match optical sensor serial.", meta
        if stale:
            return "FAIL", "Calibration is stale (> 30 days old without survey recalibration).", meta
        if reproj_error > 1.5:
            return "FAIL", f"Reprojection error ({reproj_error:.2f}px) exceeds design target (1.5px).", meta

        return "PASS", f"Spatial calibration verified (reprojection error {reproj_error:.2f}px <= 1.5px).", meta

    def evaluate_dq6_zone_geometry(self, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        geom_errs = context.get("geometry_validation_errors", [])
        meta = {"validation_errors": geom_errs}

        if geom_errs:
            return "FAIL", f"Zone geometry invalid: {'; '.join(geom_errs)}", meta

        return "PASS", "2D/3D zone boundary polygons verified and surveyed in facility datum.", meta

    def evaluate_dq7_event_completeness(self, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        win = context.get("windows", {})
        t_pre = win.get("t_pre_s", 4.0)
        t_interv = win.get("t_interv_s", 2.5)
        t_post = win.get("t_post_s", 5.0)

        meta = {"t_pre_s": t_pre, "t_interv_s": t_interv, "t_post_s": t_post}

        if t_pre < 3.0:
            return "FAIL", f"PRE window truncated ({t_pre:.2f}s < 3.0s minimum).", meta
        if t_interv < 1.5:
            return "FAIL", f"INTERVENTION window truncated ({t_interv:.2f}s < 1.5s minimum).", meta
        if t_post < 4.0:
            return "FAIL", f"POST window truncated ({t_post:.2f}s < 4.0s minimum).", meta

        return "PASS", f"Dynamic event windows complete (Pre: {t_pre:.1f}s, Interv: {t_interv:.1f}s, Post: {t_post:.1f}s).", meta

    def evaluate_dq8_provenance(self, context: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        prov = context.get("provenance_status", {})
        chain_valid = prov.get("chain_intact", True)
        tampered = prov.get("tampering_detected", False)
        meta = {"chain_intact": chain_valid, "tampering_detected": tampered}

        if tampered or not chain_valid:
            return "FAIL", "Cryptographic provenance hash chain verification failure (tampering detected).", meta

        return "PASS", "Cryptographic provenance hash chain verified and tamper-evident.", meta

    def evaluate_pipeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes sequential short-circuit evaluation for live readiness state,
        while extracting parallel diagnostics across all gates.
        """
        gates = [
            ("DQ1_CLOCK_SYNC", self.evaluate_dq1_clock_sync),
            ("DQ2_CAMERA_INTEGRITY", self.evaluate_dq2_camera_integrity),
            ("DQ3_TELEMETRY_INTEGRITY", self.evaluate_dq3_telemetry_integrity),
            ("DQ4_SECONDARY_SENSOR_INTEGRITY", self.evaluate_dq4_secondary_sensor_integrity),
            ("DQ5_CALIBRATION_INTEGRITY", self.evaluate_dq5_calibration_integrity),
            ("DQ6_ZONE_GEOMETRY", self.evaluate_dq6_zone_geometry),
            ("DQ7_EVENT_COMPLETENESS", self.evaluate_dq7_event_completeness),
            ("DQ8_PROVENANCE", self.evaluate_dq8_provenance)
        ]

        live_results = {}
        parallel_diagnostics = {}
        first_blocking_gate = "NONE"
        live_short_circuited = False

        # 1. Parallel diagnostic run (all gates evaluated for engineering visibility)
        for gid, fn in gates:
            res, reason, meta = fn(context)
            parallel_diagnostics[gid] = {"result": res, "reason": reason, "metadata": meta}

        # 2. Sequential short-circuit run (decision flow)
        for gid, fn in gates:
            if live_short_circuited:
                live_results[gid] = "NOT_EVALUATED"
                continue

            diag = parallel_diagnostics[gid]
            res = diag["result"]

            if res == "PASS":
                live_results[gid] = "PASS"
            elif res == "PARTIAL":
                live_results[gid] = "PARTIAL"
            else:
                live_results[gid] = "FAIL"
                first_blocking_gate = gid
                live_short_circuited = True

        # Determine overall readiness state
        if live_short_circuited:
            is_tamper = (
                context.get("provenance_status", {}).get("tampering_detected", False)
                or context.get("is_tampered", False)
                or parallel_diagnostics.get("DQ8_PROVENANCE", {}).get("result") == "FAIL"
            )
            if is_tamper:
                overall_state = ReadinessState.REJECTED
            else:
                overall_state = ReadinessState.NOT_READY
        elif any(v == "PARTIAL" for v in live_results.values()):
            overall_state = ReadinessState.PARTIALLY_READY
        else:
            overall_state = ReadinessState.READY_FOR_PILOT

        return {
            "overall_readiness_state": overall_state.value,
            "first_blocking_gate": first_blocking_gate,
            "live_sequential_gate_results": live_results,
            "parallel_diagnostic_metadata": parallel_diagnostics
        }
