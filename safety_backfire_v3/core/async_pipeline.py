"""
V3.0 Core — Asynchronous Multi-Threaded Live Pipeline Engine

Architecture:
  Frame Ingest Thread -> Bounded Buffer (Freshness Gate)
        │
        ▼
  Detection & Tracking Worker (Full Source Rate: ~25 Hz)
        │
        ▼
  Conservative Identity Layer (Assigns Durable Entity IDs)
        │
   ┌────┴──────────────────────────┐
   │                               │
   ▼                               ▼
  Pose Worker (Decoupled Stride)  Fast-Path State Cache
  (5 Hz / 8 Hz / 10 Hz)           (Timestamp Ordering & Monotonicity)
   │                               │
   └───────────────┬───────────────┘
                   ▼
  Fused Safety Engine (Relation -> Geometry -> CPA/TTC -> Risk -> EventV3)
                   │
                   ▼
  Traceable Structured Event Stream with Microsecond Latency Logging
"""
import time
import math
import threading
import queue
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import cv2
from ultralytics import YOLO

from safety_backfire_v3.core.async_ingest import FramePacket, BoundedFrameQueue, FreshnessPolicy
from safety_backfire_v3.core.identity_layer import ConservativeIdentityLayer
from safety_backfire_v3.core.event_engine_v3 import EventEngineV3
from safety_backfire_v3.core.geometry_v3 import GeometryEngineV3, GeometricProjectionMethod, CameraCalibrationContract
from safety_backfire_v3.core.uncertainty_risk_engine import UncertaintyAwareRiskEngine, RiskEvaluationResult
import sys
from pathlib import Path

# Ensure V2 core is resolvable
_V2_PATH = Path(__file__).resolve().parent.parent.parent / "safety_backfire_v2"
if str(_V2_PATH) not in sys.path:
    sys.path.insert(0, str(_V2_PATH))

from core.geometry import load_default_calibrator
from core.operator_relation_v2 import OperatorVehicleRelationEngineV2
from core.track_manager import TrackManager, TrackState
from core.observation_gate import ObservationIntegrityGate, ObservationValidity
from core.kinematics import calculate_world_velocity, compute_metric_ttc

class PoseContract:
    """
    Strict contract ensuring Pose estimates carry full temporal provenance.
    FAIL-18 Resolution & Temporal Contract:
    Maintains 4 distinct timestamps:
      1. pose_source_capture_timestamp: Camera hardware sensor PTS
      2. pose_inference_start_timestamp: Wall clock when pose worker started compute
      3. pose_inference_end_timestamp: Wall clock when pose worker finished compute
      4. decision_timestamp: Wall clock when decision was made on current observation
      
    CRITICAL TEMPORAL SAFETY RULE:
      Freshness is strictly evaluated as:
        pose_source_age_ms = (obs_source_capture_timestamp - pose_source_capture_timestamp) * 1000.0
      Inference compute latency is decoupled and logged as a compute runtime metric only.
    """
    def __init__(
        self,
        pose_id: str,
        pose_source_frame_id: int,
        pose_source_capture_timestamp: float,
        source_track_id: int,
        source_entity_id: str,
        keypoints: Optional[list],
        keypoint_confidence: float,
        pose_inference_start_timestamp: Optional[float] = None,
        pose_inference_end_timestamp: Optional[float] = None,
        decision_timestamp: Optional[float] = None,
        # Backward-compatible parameter name
        pose_frame_id: Optional[int] = None,
        pose_timestamp: Optional[float] = None
    ):
        self.pose_id = pose_id
        self.pose_source_frame_id = pose_source_frame_id if pose_source_frame_id is not None else (pose_frame_id or 0)
        self.pose_source_capture_timestamp = pose_source_capture_timestamp if pose_source_capture_timestamp is not None else (pose_timestamp or 0.0)
        
        now = time.time()
        self.pose_inference_start_timestamp = pose_inference_start_timestamp or now
        self.pose_inference_end_timestamp = pose_inference_end_timestamp or now
        self.decision_timestamp = decision_timestamp
        
        self.source_track_id = source_track_id
        self.source_entity_id = source_entity_id
        self.keypoints = keypoints
        self.keypoint_confidence = keypoint_confidence
        
        # Backward-compatibility properties
        self.pose_frame_id = self.pose_source_frame_id
        self.pose_timestamp = self.pose_source_capture_timestamp

    @property
    def pose_compute_latency_ms(self) -> float:
        """Compute execution duration only (not source freshness)."""
        return max(0.0, (self.pose_inference_end_timestamp - self.pose_inference_start_timestamp) * 1000.0)

    def pose_source_age_ms(self, obs_source_capture_timestamp: float) -> float:
        """True source-time freshness: time elapsed between source frame capture and decision frame capture."""
        return (obs_source_capture_timestamp - self.pose_source_capture_timestamp) * 1000.0

    def source_time_skew_ms(self, obs_source_capture_timestamp: float) -> float:
        """Temporal skew between observation capture and pose capture."""
        return abs(obs_source_capture_timestamp - self.pose_source_capture_timestamp) * 1000.0

    def age_ms(self, wall_now: float) -> float:
        """Wall-clock age since inference finished (for diagnostic compute telemetry)."""
        return max(0.0, (wall_now - self.pose_inference_end_timestamp) * 1000.0)

    def evaluate_suppression_authority(
        self,
        obs_source_frame_id: int,
        obs_source_capture_timestamp: float,
        max_source_age_ms: float = 150.0,
        max_skew_ms: float = 100.0
    ) -> Tuple[bool, str, Dict[str, float]]:
        """
        Determines whether this pose packet possesses safety suppression authority.
        Enforces FAIL-18:
          - Stale pose source frame cannot suppress newer observation.
          - Future or out-of-order timestamps trigger anomaly shutdown.
          - Suppression authority = False immediately if bounds exceeded.
        """
        telemetry = {
            "source_age_ms": round(self.pose_source_age_ms(obs_source_capture_timestamp), 1),
            "source_skew_ms": round(self.source_time_skew_ms(obs_source_capture_timestamp), 1),
            "compute_latency_ms": round(self.pose_compute_latency_ms, 1)
        }
        
        if self.keypoints is None or self.keypoint_confidence < 0.2:
            return False, "UNAVAILABLE_KEYPOINTS", telemetry
            
        # Anomaly checks: packet from the future
        if self.pose_source_frame_id > obs_source_frame_id:
            return False, "FUTURE_FRAME_ANOMALY", telemetry
        if self.pose_source_capture_timestamp > obs_source_capture_timestamp + 0.001:
            return False, "FUTURE_TIMESTAMP_ANOMALY", telemetry
            
        src_age = self.pose_source_age_ms(obs_source_capture_timestamp)
        src_skew = self.source_time_skew_ms(obs_source_capture_timestamp)
        
        if src_age > max_source_age_ms:
            return False, f"STALE_POSE_SOURCE_AGE_{src_age:.1f}MS", telemetry
        if src_skew > max_skew_ms:
            return False, f"SKEW_EXCEEDED_{src_skew:.1f}MS", telemetry
            
        return True, "SUPPRESSION_PERMITTED", telemetry

    def get_status(self, current_frame_id: int, current_timestamp: float) -> str:
        if self.keypoints is None or self.keypoint_confidence < 0.2:
            return "UNAVAILABLE_POSE"
        src_age = (current_timestamp - self.pose_source_capture_timestamp) * 1000.0
        frame_diff = current_frame_id - self.pose_source_frame_id
        if src_age <= 150.0 and frame_diff <= 4:
            return "FRESH_POSE"
        elif src_age <= 400.0:
            return "STALE_POSE"
        return "UNAVAILABLE_POSE"

    def get_staleness_status(self, current_timestamp: float, max_fresh_age_ms: float = 150.0, max_stale_age_ms: float = 400.0) -> str:
        if self.keypoints is None or self.keypoint_confidence < 0.2:
            return "UNAVAILABLE_POSE"
        src_age = (current_timestamp - self.pose_source_capture_timestamp) * 1000.0
        if src_age <= max_fresh_age_ms:
            return "FRESH_POSE"
        elif src_age <= max_stale_age_ms:
            return "STALE_POSE"
        else:
            return "UNAVAILABLE_POSE"

    def is_usable_for_safety(self, current_timestamp: float, max_fresh_age_ms: float = 150.0) -> bool:
        return self.get_staleness_status(current_timestamp, max_fresh_age_ms) == "FRESH_POSE"


class AsyncLivePipeline:
    """
    High-Performance Asynchronous Live Intelligence Pipeline.
    Runs Detection at full source FPS while decoupling Pose estimation onto an
    asynchronous worker thread with controlled stride (5Hz, 8Hz, 10Hz, or Continuous).
    """
    def __init__(
        self,
        detector_weights: str,
        pose_weights: str,
        pose_target_hz: float = 8.0,
        pose_mode: str = "async_decoupled",
        enable_identity_reid: bool = True,
        geometry_method: str = GeometricProjectionMethod.METHOD_E_3D_VEHICLE_OFFSET,
        max_queue_size: int = 5,
        max_allowed_frame_age_ms: float = 150.0,
        max_allowed_input_skew_ms: float = 100.0,
        calibration_contract: Optional[CameraCalibrationContract] = None
    ):
        self.pose_target_hz = pose_target_hz
        self.pose_interval = 1.0 / pose_target_hz if pose_target_hz > 0 else 0.0
        self.pose_mode = pose_mode
        self.enable_identity_reid = enable_identity_reid
        self.geometry_method = geometry_method
        self.max_allowed_frame_age_ms = max_allowed_frame_age_ms
        self.max_allowed_input_skew_ms = max_allowed_input_skew_ms
        
        # Ingestion & Buffer
        self.freshness_policy = FreshnessPolicy(max_allowed_age_ms=max_allowed_frame_age_ms)
        self.frame_queue = BoundedFrameQueue(max_size=max_queue_size, freshness_policy=self.freshness_policy)
        
        # Models
        self.det_model = YOLO(detector_weights)
        self.pose_model = YOLO(pose_weights)
        
        # Core Analytical Engines
        self.calibrator = load_default_calibrator()
        self.geometry_engine = GeometryEngineV3(self.calibrator, calibration_contract=calibration_contract)
        self.track_manager = TrackManager(strong_conf_threshold=0.35, max_prediction_frames=5)
        self.identity_layer = ConservativeIdentityLayer()
        self.relation_engine = OperatorVehicleRelationEngineV2()
        self.event_engine = EventEngineV3(max_gap_frames=15)
        self.risk_engine = UncertaintyAwareRiskEngine()
        
        # Decoupled Pose Worker Queues & State
        self.pose_task_queue = queue.Queue(maxsize=3)
        self.latest_pose_by_entity: Dict[str, PoseContract] = {}
        self._pose_lock = threading.Lock()
        self._last_pose_time = 0.0
        self._pose_counter = 0
        
        # Concurrency & Lifecycle
        self.running = False
        self.pose_worker_thread: Optional[threading.Thread] = None
        
        # Latency Budget & Stage-by-Stage Telemetry (in milliseconds)
        self.latency_records = {
            "decode_ms": [],
            "detection_ms": [],
            "tracking_id_ms": [],
            "pose_worker_ms": [],
            "geometry_ms": [],
            "risk_eval_ms": [],
            "safety_eval_ms": [],
            "end_to_end_ms": [],
            "capture_to_detection_ms": [],
            "capture_to_tracking_ms": [],
            "capture_to_geometry_ms": [],
            "capture_to_risk_ms": [],
            "capture_to_decision_ms": [],
            "pose_age_at_decision_ms": []
        }
        self.processed_frames = 0
        self.dropped_frames = 0

    def start(self):
        self.running = True
        self.pose_worker_thread = threading.Thread(target=self._pose_worker_loop, daemon=True)
        self.pose_worker_thread.start()

    def stop(self):
        self.running = False
        if self.pose_worker_thread and self.pose_worker_thread.is_alive():
            self.pose_worker_thread.join(timeout=1.0)
        self.event_engine.close_all_events()

    def _pose_worker_loop(self):
        """
        Independent Pose Worker processing person crops at decoupled stride (e.g. 8 Hz).
        Respects timestamp ordering: late results cannot overwrite newer entity state.
        """
        while self.running:
            try:
                task = self.pose_task_queue.get(timeout=0.05)
            except queue.Empty:
                continue

            frame_img, frame_id, timestamp, person_targets = task
            t0 = time.time()

            if person_targets and frame_img is not None:
                # Run pose inference on whole frame or crops
                pose_res = self.pose_model.predict(frame_img, imgsz=640, conf=0.25, verbose=False)[0]
                
                with self._pose_lock:
                    for target in person_targets:
                        t_id = target["id"]
                        e_id = target["entity_id"]
                        p_box = target["bbox"]
                        
                        best_iou, best_kpts, best_conf = 0.0, None, 0.0
                        if pose_res.keypoints is not None and len(pose_res.boxes) > 0:
                            for i, box in enumerate(pose_res.boxes.xyxy.cpu().numpy()):
                                ix1, iy1 = max(p_box[0], box[0]), max(p_box[1], box[1])
                                ix2, iy2 = min(p_box[2], box[2]), min(p_box[3], box[3])
                                inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                                area1 = (p_box[2] - p_box[0]) * (p_box[3] - p_box[1])
                                area2 = (box[2] - box[0]) * (box[3] - box[1])
                                iou = inter / float(area1 + area2 - inter) if (area1 + area2 - inter) > 0 else 0
                                if iou > 0.3 and iou > best_iou:
                                    best_iou = iou
                                    kpts = pose_res.keypoints.data.cpu().numpy()[i]
                                    if kpts.shape[1] == 2:
                                        kpts = np.hstack([kpts, np.ones((17, 1))])
                                    best_kpts = kpts.tolist()
                                    best_conf = float(np.mean(kpts[:, 2]))
                                    
                        self._pose_counter += 1
                        t_infer_end = time.time()
                        pose_contract = PoseContract(
                            pose_id=f"POSE_{self._pose_counter:06d}",
                            pose_source_frame_id=frame_id,
                            pose_source_capture_timestamp=timestamp,
                            pose_inference_start_timestamp=t0,
                            pose_inference_end_timestamp=t_infer_end,
                            source_track_id=t_id,
                            source_entity_id=e_id,
                            keypoints=best_kpts,
                            keypoint_confidence=best_conf
                        )
                        
                        # Timestamp Ordering Invariant:
                        # Only update if entity has no pose OR incoming pose is strictly newer
                        existing = self.latest_pose_by_entity.get(e_id)
                        if existing is None or pose_contract.pose_source_frame_id >= existing.pose_source_frame_id:
                            self.latest_pose_by_entity[e_id] = pose_contract

            elapsed_ms = (time.time() - t0) * 1000.0
            self.latency_records["pose_worker_ms"].append(elapsed_ms)

    def process_frame_packet(self, packet: FramePacket) -> Optional[Dict[str, Any]]:
        """
        Processes a single frame packet through the asynchronous perception and safety pipeline.
        """
        packet.mark_processing_start()
        frame = packet.image
        frame_idx = packet.frame_id
        timestamp = packet.source_timestamp
        wall_now = time.time()

        # Check Freshness Gate
        decision, reason = self.freshness_policy.evaluate(packet, wall_now)
        if decision == "DROP":
            packet.drop_reason = reason
            self.dropped_frames += 1
            return None

        # 1. Detection & Tracking (Full rate ~25 Hz)
        t_det0 = time.time()
        res = self.det_model.track(
            frame, imgsz=640, conf=0.15, iou=0.70, classes=[0, 1],
            persist=True, tracker="bytetrack.yaml", verbose=False
        )[0]
        t_det1 = time.time()
        self.latency_records["detection_ms"].append((t_det1 - t_det0) * 1000.0)

        raw_tracked = []
        if res.boxes.id is not None:
            for b, cls, trk_id, conf in zip(
                res.boxes.xyxy.cpu().numpy(), res.boxes.cls.cpu().numpy(),
                res.boxes.id.cpu().numpy(), res.boxes.conf.cpu().numpy()
            ):
                box = [int(v) for v in b]
                cx, fy = (box[0] + box[2]) / 2.0, float(box[3])
                raw_tracked.append({
                    "id": int(trk_id),
                    "class": self.det_model.names[int(cls)],
                    "bbox": box,
                    "px": (cx, fy),
                    "conf": float(conf)
                })

        # 2. Identity Resolution (Durable Layer vs Raw Tracker Baseline)
        t_id0 = time.time()
        if self.enable_identity_reid:
            tracked_entities = self.identity_layer.process_tracks(
                frame_idx, timestamp, raw_tracked, frame_image=frame, calibrator=self.calibrator
            )
        else:
            tracked_entities = []
            for obj in raw_tracked:
                obj["entity_id"] = f"{obj['class'][0].upper()}_{obj['id']}"
                obj["identity_status"] = "RAW_TRACK"
                tracked_entities.append(obj)
        t_id1 = time.time()
        self.latency_records["tracking_id_ms"].append((t_id1 - t_id0) * 1000.0)

        # 3. Pose Execution (Sequential Continuous vs Decoupled Stride)
        persons_in_frame = [obj for obj in tracked_entities if obj["class"] == "person"]
        
        if self.pose_mode == "sequential_continuous":
            t_p0 = time.time()
            if persons_in_frame:
                pose_res = self.pose_model.predict(frame, imgsz=640, conf=0.25, verbose=False)[0]
                for p in persons_in_frame:
                    p_box = p["bbox"]
                    best_iou, best_kpts = 0.0, None
                    if pose_res.keypoints is not None and len(pose_res.boxes) > 0:
                        for i, box in enumerate(pose_res.boxes.xyxy.cpu().numpy()):
                            ix1, iy1 = max(p_box[0], box[0]), max(p_box[1], box[1])
                            ix2, iy2 = min(p_box[2], box[2]), min(p_box[3], box[3])
                            inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                            area1 = (p_box[2] - p_box[0]) * (p_box[3] - p_box[1])
                            area2 = (box[2] - box[0]) * (box[3] - box[1])
                            iou = inter / float(area1 + area2 - inter) if (area1 + area2 - inter) > 0 else 0
                            if iou > 0.3 and iou > best_iou:
                                best_iou = iou
                                kpts = pose_res.keypoints.data.cpu().numpy()[i]
                                if kpts.shape[1] == 2:
                                    kpts = np.hstack([kpts, np.ones((17, 1))])
                                best_kpts = kpts.tolist()
                    p["pose_status"] = "FRESH_POSE" if best_kpts else "UNAVAILABLE_POSE"
                    p["keypoints"] = best_kpts
            else:
                for p in persons_in_frame:
                    p["pose_status"] = "UNAVAILABLE_POSE"
                    p["keypoints"] = None
            t_p1 = time.time()
            self.latency_records["pose_worker_ms"].append((t_p1 - t_p0) * 1000.0)
        else:
            # Decoupled Asynchronous Pose Dispatcher (Controlled Stride)
            time_since_pose = wall_now - self._last_pose_time
            if persons_in_frame and (self.pose_target_hz == 0 or time_since_pose >= self.pose_interval):
                self._last_pose_time = wall_now
                try:
                    task = (frame.copy(), frame_idx, timestamp, persons_in_frame)
                    self.pose_task_queue.put_nowait(task)
                except queue.Full:
                    pass # Drop pose task if worker is saturated (backpressure)

            # Attach Latest Fresh Pose from Worker
            with self._pose_lock:
                for p in persons_in_frame:
                    e_id = p["entity_id"]
                    pose_contract = self.latest_pose_by_entity.get(e_id)
                    if pose_contract:
                        p["pose_status"] = pose_contract.get_status(frame_idx, timestamp)
                        p["keypoints"] = pose_contract.keypoints
                    else:
                        p["pose_status"] = "UNAVAILABLE_POSE"
                        p["keypoints"] = None

        # 5. Safety Firewall & Track Lifecycle
        t_safe0 = time.time()
        valid_objects = self.track_manager.process_tracks(frame_idx, timestamp, tracked_entities, self.calibrator)
        
        persons = [obj for obj in valid_objects if obj["class"] == "person" and obj.get("safety_eligible", False)]
        forklifts = [obj for obj in valid_objects if obj["class"] == "forklift" and obj.get("safety_eligible", False)]

        # 6. Pairwise Relation Engine (Fixed Multi-Vehicle Loop)
        self.relation_engine.classify_frame(persons, forklifts, frame_idx)

        wall_decision_now = time.time()
        obs_age_ms = packet.age_ms(wall_decision_now)

        # 7. Spatial Interactions, Uncertainty-Aware Risk & Temporal Provenance
        frame_interactions = []
        for p in persons:
            p_rel = self.relation_engine.get_person_relation(p["id"], None, frame_idx) or "UNKNOWN"
            p_is_op = (p_rel == "OPERATOR_ON_VEHICLE")

            # Source-Time Freshness & Temporal Skew Contract (FAIL-18 Resolution)
            p_pose = self.latest_pose_by_entity.get(p["entity_id"])
            if p_pose is not None:
                suppression_allowed, auth_reason, auth_telemetry = p_pose.evaluate_suppression_authority(
                    obs_source_frame_id=frame_idx,
                    obs_source_capture_timestamp=timestamp,
                    max_source_age_ms=self.max_allowed_frame_age_ms,
                    max_skew_ms=self.max_allowed_input_skew_ms
                )
                pose_source_age_ms = auth_telemetry["source_age_ms"]
                source_skew_ms = auth_telemetry["source_skew_ms"]
            else:
                suppression_allowed = False
                auth_reason = "NO_POSE_PACKET"
                pose_source_age_ms = 999.0
                source_skew_ms = 0.0

            # If suppression authority revoked (stale pose, skew, or anomaly), forbid operator suppression!
            if (not suppression_allowed) and p_is_op:
                p_is_op = False
                p_rel = "UNKNOWN"
                p["suppression_denial_reason"] = auth_reason

            for f in forklifts:
                f_is_moving = f.get("is_moving", False)
                rel = self.relation_engine.get_person_relation(p["id"], f["id"], frame_idx) or "UNKNOWN"
                if (not suppression_allowed) and rel == "OPERATOR_ON_VEHICLE":
                    rel = "UNKNOWN"

                # Verified operator on moving forklift passing parked vehicle is normal traffic
                if p_is_op and not f_is_moving:
                    continue

                # Empirical Ground Geometry Projection with Parameterized Elevation & Uncertainty
                t_geom0 = time.time()
                p_proj = self.geometry_engine.project_entity_ground(
                    bbox=p["bbox"],
                    keypoints=p.get("keypoints"),
                    entity_class="person",
                    is_operator=p_is_op,
                    method=self.geometry_method
                )
                p_gp = p_proj["world_pos_m"]
                p_unc = p_proj.get("position_uncertainty_m", 0.3)
                f_gp = self.calibrator.pixel_to_world(f["px"])
                f_unc = 0.2
                t_geom1 = time.time()
                self.latency_records["geometry_ms"].append((t_geom1 - t_geom0) * 1000.0)

                if p_gp is not None and f_gp is not None:
                    # Metric Distance with Uncertainty Bounds (FAIL-22)
                    dist_data = self.geometry_engine.compute_distance_with_uncertainty(
                        p_gp, f_gp, p_unc, f_unc
                    )
                    dist_m = dist_data["nominal_distance_m"]
                    dist_unc = dist_data["distance_uncertainty_m"]
                    dist_int = dist_data["distance_interval_m"]
                    unc_lvl = dist_data["uncertainty_level"]

                    # Compute 2D Metric TTC with CPA Miss-Distance Filter
                    p_vel = (p.get("vx", 0.0), p.get("vy", 0.0))
                    f_vel = (f.get("vx", 0.0), f.get("vy", 0.0))
                    ttc_info = compute_metric_ttc(p_gp, f_gp, p_vel, f_vel, dist_m)

                    # Uncertainty-Aware Risk Evaluation
                    t_risk0 = time.time()
                    p_speed = math.hypot(p_vel[0], p_vel[1])
                    risk_res = self.risk_engine.evaluate(
                        nominal_distance_m=dist_m,
                        distance_uncertainty_m=dist_unc,
                        evidence_quality=p_proj.get("ground_confidence", 0.7),
                        ttc_sec=ttc_info.get("ttc_sec"),
                        cpa_miss_m=ttc_info.get("miss_distance_m"),
                        relation_state=rel,
                        approach_speed_m_s=p_speed
                    )
                    t_risk1 = time.time()
                    self.latency_records["risk_eval_ms"].append((t_risk1 - t_risk0) * 1000.0)

                    if risk_res.nominal_risk != "SAFE" or rel == "OPERATOR_ON_VEHICLE" or risk_res.risk_decision != "SAFE":
                        frame_interactions.append({
                            "person_id": p["id"],
                            "forklift_id": f["id"],
                            "person_entity_id": p["entity_id"],
                            "forklift_entity_id": f["entity_id"],
                            "distance_meters": dist_m,
                            "distance_uncertainty_m": dist_unc,
                            "distance_interval_m": dist_int,
                            "nominal_risk": risk_res.nominal_risk,
                            "uncertainty_level": unc_lvl,
                            "risk_decision": risk_res.risk_decision,
                            "zone_status": risk_res.nominal_risk,
                            "relation": rel,
                            "ttc_sec": ttc_info.get("ttc_sec"),
                            "cpa_miss_distance_m": ttc_info.get("miss_distance_m"),
                            "ttc_status": ttc_info.get("ttc_status"),
                            "decision_frame_id": frame_idx,
                            "decision_timestamp": round(wall_decision_now, 4),
                            "observation_age_ms": round(obs_age_ms, 2),
                            "pose_age_ms": round(pose_age_ms, 2),
                            "geometry_age_ms": round((time.time() - t_geom0) * 1000.0, 2),
                            "trajectory_age_ms": round((wall_decision_now - packet.capture_timestamp) * 1000.0, 2),
                            "decision_latency_ms": round((time.time() - t_safe0) * 1000.0, 2),
                            "skew_violation": skew_violation
                        })

        # 8. Event Engine V3 (Durable Entity Pairs & Uncertainty-Aware Updates)
        self.event_engine.process_frame_interactions(frame_idx, timestamp, frame_interactions)
        t_safe1 = time.time()
        self.latency_records["safety_eval_ms"].append((t_safe1 - t_safe0) * 1000.0)

        # Stage Latency Percentiles from Capture Timestamp
        cap_t = packet.capture_timestamp
        self.latency_records["capture_to_detection_ms"].append((t_det1 - cap_t) * 1000.0)
        self.latency_records["capture_to_tracking_ms"].append((t_id1 - cap_t) * 1000.0)
        self.latency_records["capture_to_decision_ms"].append((time.time() - cap_t) * 1000.0)
        if persons:
            first_pose = self.latest_pose_by_entity.get(persons[0]["entity_id"])
            if first_pose:
                self.latency_records["pose_age_at_decision_ms"].append(first_pose.age_ms(wall_decision_now))

        packet.mark_completion()
        e2e_ms = packet.end_to_end_latency_ms()
        if e2e_ms is not None:
            self.latency_records["end_to_end_ms"].append(e2e_ms)

        self.processed_frames += 1
        return {
            "frame_packet": packet.to_dict(),
            "active_entities": len(tracked_entities),
            "active_events": len(self.event_engine.active_events)
        }

    def get_latency_percentiles(self) -> Dict[str, Dict[str, float]]:
        stats = {}
        for stage, recs in self.latency_records.items():
            if recs:
                arr = np.array(recs)
                stats[stage] = {
                    "P50": round(float(np.percentile(arr, 50)), 2),
                    "P95": round(float(np.percentile(arr, 95)), 2),
                    "P99": round(float(np.percentile(arr, 99)), 2),
                    "mean": round(float(np.mean(arr)), 2),
                    "max": round(float(np.max(arr)), 2)
                }
            else:
                stats[stage] = {"P50": 0.0, "P95": 0.0, "P99": 0.0, "mean": 0.0, "max": 0.0}
        return stats

# Alias for backwards/test compatibility
AsyncSafetyPipelineV3 = AsyncLivePipeline
