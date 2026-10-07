"""
sensor_replay.py
Milestone V3.4-K — Synthetic Multi-Modal Sensor Replay & Fault Injection Engine

Provides deterministic replay for 4 cameras, CAN bus telemetry, secondary sensor,
facility geometry, cryptographic provenance, and human reviewer sanitization.
Supports programmatic fault injection to test data quality gates.
"""

import hashlib
import json
import copy
from typing import Dict, Any, List, Optional, Tuple
from interfaces import (
    GlobalClock, CameraStream, VehicleTelemetryStream, SecondarySensorStream,
    FacilityGeometry, EventRecorder, ProvenanceRecorder, HumanReviewPackage,
    SensorPacket, TimestampRecord, SourceType, ReadinessState
)


class DeterministicGlobalClock(GlobalClock):
    def __init__(self, start_us: int = 1700000000000000, drift_ppm: float = 0.0):
        self._current_us = start_us
        self._drift_ppm = drift_ppm
        self._state = "LOCKED"

    def now_us(self) -> int:
        return self._current_us

    def advance_us(self, delta_us: int):
        drifted_delta = int(delta_us * (1.0 + self._drift_ppm / 1e6))
        self._current_us += drifted_delta

    def set_sync_state(self, state: str):
        self._state = state

    def clock_domain(self) -> str:
        return "PTP_IEEE_1588_TAI"

    def synchronization_state(self) -> str:
        return self._state


class DeterministicCameraStream(CameraStream):
    def __init__(
        self,
        cam_id: str,
        fps: float = 30.0,
        resolution: Tuple[int, int] = (1920, 1080),
        offset_us: int = 0
    ):
        self._cam_id = cam_id
        self._fps = fps
        self._resolution = resolution
        self._offset_us = offset_us
        self._frame_idx = 0
        self._connected = True

    def camera_id(self) -> str:
        return self._cam_id

    def set_connected(self, connected: bool):
        self._connected = connected

    def is_connected(self) -> bool:
        return self._connected

    def fps(self) -> float:
        return self._fps

    def resolution(self) -> Tuple[int, int]:
        return self._resolution

    def generate_packet(
        self,
        base_clock_us: int,
        fault: Optional[str] = None
    ) -> Optional[SensorPacket]:
        if not self._connected:
            return None

        self._frame_idx += 1
        frame_time_us = base_clock_us + self._offset_us
        seq = self._frame_idx
        res = self._resolution
        checksum_valid = True
        is_black = False

        if fault == "FRAME_DROP":
            return None
        elif fault == "TIMESTAMP_OFFSET_HIGH":
            frame_time_us += 45000  # +45ms (exceeds 33.3ms)
        elif fault == "TIMESTAMP_NON_MONOTONIC":
            frame_time_us -= 100000  # jumps backward 100ms
        elif fault == "TIMESTAMP_DUPLICATE":
            frame_time_us = base_clock_us  # identical to previous
        elif fault == "CODEC_CORRUPTION":
            checksum_valid = False
        elif fault == "RESOLUTION_MISMATCH":
            res = (1280, 720)
        elif fault == "BLACK_FRAME":
            is_black = True
        elif fault == "FRAME_REORDER":
            seq -= 2

        payload = {
            "frame_index": seq,
            "width": res[0],
            "height": res[1],
            "channels": 3,
            "is_black": is_black,
            "encoding": "H264_HIGH_PROFILE",
            "mock_pixel_hash": hashlib.sha256(f"{self._cam_id}_{seq}".encode()).hexdigest()
        }

        chk = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if not checksum_valid:
            chk = "CORRUPTED_CHECKSUM_0000000000000000"

        ts_rec = TimestampRecord(
            timestamp_utc_us=frame_time_us,
            sequence_number=seq,
            source_clock_domain="PTP_CAMERA_HARDWARE",
            is_monotonic=(fault != "TIMESTAMP_NON_MONOTONIC")
        )

        return SensorPacket(
            source_id=self._cam_id,
            source_type=SourceType.DIRECT_SENSOR,
            timestamp=ts_rec,
            payload=payload,
            checksum=chk,
            metadata={"lens_model": "4mm_pinhole", "mount_height_m": 5.0}
        )

    def next_frame(self) -> Optional[SensorPacket]:
        return None


class DeterministicTelemetryStream(VehicleTelemetryStream):
    def __init__(self, veh_id: str, rate_hz: float = 100.0, offset_us: int = 0):
        self._veh_id = veh_id
        self._rate_hz = rate_hz
        self._offset_us = offset_us
        self._seq = 0
        self._healthy = True

    def vehicle_id(self) -> str:
        return self._veh_id

    def sampling_rate_hz(self) -> float:
        return self._rate_hz

    def set_healthy(self, healthy: bool):
        self._healthy = healthy

    def is_healthy(self) -> bool:
        return self._healthy

    def generate_packet(
        self,
        base_clock_us: int,
        kinematic_state: Dict[str, Any],
        fault: Optional[str] = None
    ) -> Optional[SensorPacket]:
        if not self._healthy or fault == "SENSOR_DROPOUT":
            return None

        self._seq += 1
        pkt_time_us = base_clock_us + self._offset_us
        seq = self._seq

        speed = kinematic_state.get("speed_mps", 3.5)
        accel = kinematic_state.get("long_accel_mps2", -2.8)
        brake = kinematic_state.get("brake_state", "SERVICE_BRAKE_ACTIVE")
        pressure = kinematic_state.get("brake_pressure_kpa", 450.0)
        steer = kinematic_state.get("steering_deg", 18.5)
        yaw = kinematic_state.get("yaw_rate_deg_s", 12.0)
        throttle = kinematic_state.get("throttle_pct", 0.0)

        if fault == "PACKET_LOSS":
            return None
        elif fault == "CAN_OFFSET_HIGH":
            pkt_time_us += 35000  # +35ms (exceeds 20ms CAN budget)
        elif fault == "FLATLINE_SPEED":
            speed = 5.0  # constant non-zero while braking
        elif fault == "FLATLINE_STEERING":
            steer = 0.0  # steering completely flatlined during swerve
        elif fault == "MISSING_BRAKE_STATE":
            brake = None
        elif fault == "OUT_OF_RANGE_VALUE":
            accel = -45.0  # physically impossible forklift deceleration
        elif fault == "UNIT_MISMATCH":
            speed = speed * 2.23694  # speed in mph instead of m/s without tag

        payload = {
            "vehicle_id": self._veh_id,
            "vehicle_speed_mps": speed,
            "longitudinal_acceleration_mps2": accel,
            "brake_state": brake,
            "brake_pressure_kpa": pressure,
            "steering_angle_deg": steer,
            "yaw_rate_deg_s": yaw,
            "throttle_position_pct": throttle
        }

        chk = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        ts_rec = TimestampRecord(
            timestamp_utc_us=pkt_time_us,
            sequence_number=seq,
            source_clock_domain="CAN_GATEWAY_PTP",
            is_monotonic=True
        )

        return SensorPacket(
            source_id=self._veh_id,
            source_type=SourceType.DIRECT_SENSOR,
            timestamp=ts_rec,
            payload=payload,
            checksum=chk,
            metadata={"can_bus": "CAN_0", "baud_rate": "500k"}
        )

    def next_telemetry(self) -> Optional[SensorPacket]:
        return None


class DeterministicSecondarySensorStream(SecondarySensorStream):
    def __init__(self, s_id: str, modality: str = "LIDAR_3D"):
        self._s_id = s_id
        self._modality = modality
        self._seq = 0
        self._depth_observable = True

    def sensor_id(self) -> str:
        return self._s_id

    def sensor_modality(self) -> str:
        return self._modality

    def set_depth_observable(self, obs: bool):
        self._depth_observable = obs

    def is_depth_observable(self) -> bool:
        return self._depth_observable

    def generate_packet(
        self,
        base_clock_us: int,
        fault: Optional[str] = None
    ) -> Optional[SensorPacket]:
        if fault == "SENSOR_DROPOUT" or fault == "LIDAR_DROPOUT" or fault == "UWB_DROPOUT":
            return None

        self._seq += 1
        pkt_time_us = base_clock_us
        depth_obs = self._depth_observable

        if fault == "CAMERA_C_OCCLUSION" or fault == "DEPTH_OCCLUDED":
            depth_obs = False
        elif fault == "SENSOR_TIMESTAMP_MISMATCH":
            pkt_time_us += 50000  # +50ms mismatch

        payload = {
            "sensor_id": self._s_id,
            "modality": self._modality,
            "interior_depth_observable": depth_obs,
            "point_count": 12500 if depth_obs else 0,
            "detected_secondary_occupants": 1 if depth_obs else 0,
            "secondary_hazard_distance_m": 4.2 if depth_obs else None
        }

        chk = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        ts_rec = TimestampRecord(
            timestamp_utc_us=pkt_time_us,
            sequence_number=self._seq,
            source_clock_domain="PTP_SECONDARY_SENSOR"
        )

        return SensorPacket(
            source_id=self._s_id,
            source_type=SourceType.DIRECT_SENSOR,
            timestamp=ts_rec,
            payload=payload,
            checksum=chk,
            metadata={"cross_aisle_id": "AISLE_04_NORTH"}
        )

    def next_reading(self) -> Optional[SensorPacket]:
        return None


class DeterministicFacilityGeometry(FacilityGeometry):
    def __init__(self, fac_id: str = "Wh_Pilot_001"):
        self._fac_id = fac_id
        self._crs = "FACILITY_GLOBAL_DATUM_METRIC_XYZ"

    def facility_id(self) -> str:
        return self._fac_id

    def coordinate_reference_system(self) -> str:
        return self._crs

    def zone_polygons(self, fault: Optional[str] = None) -> Dict[str, Any]:
        if fault == "MISSING_SECONDARY_ZONE":
            return {
                "primary_interaction_zone": [[0.0, 0.0], [30.0, 0.0], [30.0, 4.5], [0.0, 4.5]]
            }
        elif fault == "OVERLAPPING_ZONES":
            # Primary and secondary collide abnormally
            return {
                "primary_interaction_zone": [[0.0, 0.0], [30.0, 0.0], [30.0, 4.5], [0.0, 4.5]],
                "secondary_zone_entry": [[5.0, 0.0], [15.0, 0.0], [15.0, 4.5], [5.0, 4.5]],
                "secondary_zone_depth": [[10.0, 4.5], [10.0, 25.0], [13.2, 25.0], [13.2, 4.5]]
            }
        elif fault == "SELF_INTERSECTING_POLYGON":
            # Bowtie non-simple polygon
            return {
                "primary_interaction_zone": [[0.0, 0.0], [30.0, 4.5], [30.0, 0.0], [0.0, 4.5]],
                "secondary_zone_depth": [[10.0, 4.5], [10.0, 25.0], [13.2, 25.0], [13.2, 4.5]]
            }
        elif fault == "WRONG_CRS":
            return {
                "primary_interaction_zone": [[0.0, 0.0], [30.0, 0.0], [30.0, 4.5], [0.0, 4.5]],
                "secondary_zone_depth": [[10.0, 4.5], [10.0, 25.0], [13.2, 25.0], [13.2, 4.5]],
                "crs_override": "RELATIVE_SCREEN_PIXELS"
            }

        return {
            "primary_interaction_zone": [[0.0, 0.0], [30.0, 0.0], [30.0, 4.5], [0.0, 4.5]],
            "secondary_zone_entry": [[10.0, 3.5], [13.2, 3.5], [13.2, 5.5], [10.0, 5.5]],
            "secondary_zone_depth": [[10.0, 4.5], [10.0, 25.0], [13.2, 25.0], [13.2, 4.5]]
        }

    def validate_geometry(self, fault: Optional[str] = None) -> Tuple[bool, List[str]]:
        zones = self.zone_polygons(fault)
        errs = []

        if "secondary_zone_depth" not in zones:
            errs.append("Missing mandatory secondary_zone_depth polygon.")
        if fault == "OVERLAPPING_ZONES":
            errs.append("Primary and secondary entry zones overlap illegally on ground plane.")
        if fault == "SELF_INTERSECTING_POLYGON":
            errs.append("Primary zone polygon is self-intersecting (non-simple bowtie topology).")
        if fault == "WRONG_CRS" or zones.get("crs_override"):
            errs.append(f"Invalid CRS: {zones.get('crs_override')}. Expected FACILITY_GLOBAL_DATUM_METRIC_XYZ.")

        return len(errs) == 0, errs


class DeterministicEventRecorder(EventRecorder):
    def package_event(
        self,
        event_id: str,
        camera_packets: Dict[str, List[SensorPacket]],
        telemetry_packets: List[SensorPacket],
        secondary_packets: List[SensorPacket],
        geometry: FacilityGeometry,
        calibration: Dict[str, Any],
        windows: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Aggregate raw hashes
        cam_hashes = {}
        for cid, pkts in camera_packets.items():
            combined = "".join(p.checksum for p in pkts)
            cam_hashes[cid] = hashlib.sha256(combined.encode()).hexdigest()

        telem_hash = hashlib.sha256("".join(p.checksum for p in telemetry_packets).encode()).hexdigest()
        sec_hash = hashlib.sha256("".join(p.checksum for p in secondary_packets).encode()).hexdigest()
        calib_hash = hashlib.sha256(json.dumps(calibration, sort_keys=True).encode()).hexdigest()
        geom_hash = hashlib.sha256(json.dumps(geometry.zone_polygons(), sort_keys=True).encode()).hexdigest()

        package_manifest = {
            "event_id": event_id,
            "facility_id": geometry.facility_id(),
            "windows": windows,
            "camera_hashes": cam_hashes,
            "telemetry_hash": telem_hash,
            "secondary_sensor_hash": sec_hash,
            "calibration_hash": calib_hash,
            "geometry_hash": geom_hash,
            "software_version": "V3.4-K-PILOT-01",
            "counts": {
                "cameras": {k: len(v) for k, v in camera_packets.items()},
                "telemetry_packets": len(telemetry_packets),
                "secondary_packets": len(secondary_packets)
            }
        }

        pkg_hash = hashlib.sha256(json.dumps(package_manifest, sort_keys=True).encode()).hexdigest()
        package_manifest["event_package_hash"] = pkg_hash
        return package_manifest


class DeterministicProvenanceRecorder(ProvenanceRecorder):
    def __init__(self):
        self._chain: List[Dict[str, Any]] = []

    def compute_payload_hash(self, payload: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def append_event_to_chain(self, event_id: str, payload_hash: str) -> Dict[str, Any]:
        prev_hash = self._chain[-1]["current_hash"] if self._chain else "0" * 64
        entry_payload = f"{event_id}_{payload_hash}_{prev_hash}"
        cur_hash = hashlib.sha256(entry_payload.encode()).hexdigest()

        entry = {
            "sequence_index": len(self._chain),
            "event_id": event_id,
            "payload_hash": payload_hash,
            "previous_hash": prev_hash,
            "current_hash": cur_hash
        }
        self._chain.append(entry)
        return entry

    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        errs = []
        for i, entry in enumerate(self._chain):
            expected_prev = "0" * 64 if i == 0 else self._chain[i - 1]["current_hash"]
            if entry["previous_hash"] != expected_prev:
                errs.append(f"Entry {i} previous_hash mismatch! Found {entry['previous_hash']}, expected {expected_prev}")

            expected_payload = f"{entry['event_id']}_{entry['payload_hash']}_{entry['previous_hash']}"
            expected_cur = hashlib.sha256(expected_payload.encode()).hexdigest()
            if entry["current_hash"] != expected_cur:
                errs.append(f"Entry {i} current_hash tampered! Found {entry['current_hash']}, expected {expected_cur}")

        return len(errs) == 0, errs

    def get_chain(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self._chain)


class DeterministicHumanReviewPackage(HumanReviewPackage):
    FORBIDDEN_STRINGS = [
        "BACKFIRE_SCORE",
        "CANDIDATE_BACKFIRE",
        "Model H risk score",
        "YOLO confidence",
        "ByteTrack score",
        "candidate ranking",
        "automated disposition"
    ]

    def export_reviewer_package(self, event_package: Dict[str, Any]) -> Dict[str, Any]:
        # Strips any AI model metadata
        sanitized = {
            "event_id": event_package.get("event_id"),
            "facility_id": event_package.get("facility_id"),
            "review_presentation": {
                "available_views": ["CAMERA_A_PRIMARY", "CAMERA_B_ENTRY", "CAMERA_C_DEPTH", "CAMERA_D_CROSS"],
                "telemetry_stream_available": True,
                "secondary_occupancy_available": True,
                "windows": event_package.get("windows"),
                "counts": event_package.get("counts")
            },
            "provenance": {
                "package_hash": event_package.get("event_package_hash"),
                "software_version": event_package.get("software_version")
            }
        }
        return sanitized

    def verify_blinding(self, reviewer_package: Dict[str, Any]) -> Tuple[bool, List[str]]:
        text_repr = json.dumps(reviewer_package)
        found_leaks = []
        for s in self.FORBIDDEN_STRINGS:
            if s.lower() in text_repr.lower():
                found_leaks.append(f"Forbidden string detected in reviewer package: '{s}'")
        return len(found_leaks) == 0, found_leaks
