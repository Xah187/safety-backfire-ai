"""
interfaces.py
Milestone V3.4-K — Abstract Interfaces for Field Pilot Multi-Modal Evidence Pipeline

GOVERNANCE INVARIANTS:
  - Milestone: V3.4-K Field Pilot Readiness & Instrumentation Verification.
  - Abstract hardware-agnostic interfaces.
  - Zero coupling to commercial hardware vendors or production detector code.
  - Model H remains frozen and completely decoupled from raw evidence streams.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class SourceType(Enum):
    DIRECT_SENSOR = "DIRECT_SENSOR"
    VIDEO_DERIVED = "VIDEO_DERIVED"
    TRACK_DERIVED = "TRACK_DERIVED"
    MODEL_DERIVED = "MODEL_DERIVED"
    SYNTHETIC = "SYNTHETIC"


class ReadinessState(Enum):
    NOT_READY = "NOT_READY"
    PARTIALLY_READY = "PARTIALLY_READY"
    READY_FOR_PILOT = "READY_FOR_PILOT"
    REJECTED = "REJECTED"


@dataclass
class TimestampRecord:
    timestamp_utc_us: int
    sequence_number: int
    source_clock_domain: str = "PTP_IEEE_1588_TAI"
    is_monotonic: bool = True
    clock_drift_ppm: float = 0.0


@dataclass
class SensorPacket:
    source_id: str
    source_type: SourceType
    timestamp: TimestampRecord
    payload: Dict[str, Any]
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class GlobalClock(ABC):
    """Abstract Master Global Clock Reference for Multi-Modal Synchronization."""

    @abstractmethod
    def now_us(self) -> int:
        """Returns current time in integer microseconds from UTC/TAI origin."""
        pass

    @abstractmethod
    def clock_domain(self) -> str:
        """Returns clock domain identification string (e.g. PTP_GRANDMASTER)."""
        pass

    @abstractmethod
    def synchronization_state(self) -> str:
        """Returns clock health status: LOCKED, HOLDOVER, DRIFTING, UNLOCKED."""
        pass


class CameraStream(ABC):
    """Abstract Video Camera Stream Interface."""

    @abstractmethod
    def camera_id(self) -> str:
        pass

    @abstractmethod
    def next_frame(self) -> Optional[SensorPacket]:
        """Returns next video frame packet with hardware timestamp and checksum."""
        pass

    @abstractmethod
    def fps(self) -> float:
        pass

    @abstractmethod
    def resolution(self) -> Tuple[int, int]:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass


class VehicleTelemetryStream(ABC):
    """Abstract CAN Bus / IMU Telemetry Stream Interface."""

    @abstractmethod
    def vehicle_id(self) -> str:
        pass

    @abstractmethod
    def next_telemetry(self) -> Optional[SensorPacket]:
        """Returns next CAN packet (speed, acceleration, brake, steering, yaw)."""
        pass

    @abstractmethod
    def sampling_rate_hz(self) -> float:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass


class SecondarySensorStream(ABC):
    """Abstract Secondary Zone Sensor Stream Interface (LiDAR, UWB, or Camera C)."""

    @abstractmethod
    def sensor_id(self) -> str:
        pass

    @abstractmethod
    def sensor_modality(self) -> str:
        pass

    @abstractmethod
    def next_reading(self) -> Optional[SensorPacket]:
        pass

    @abstractmethod
    def is_depth_observable(self) -> bool:
        pass


class FacilityGeometry(ABC):
    """Abstract Facility Geometry, Coordinate Reference, and Zone Boundary Interface."""

    @abstractmethod
    def facility_id(self) -> str:
        pass

    @abstractmethod
    def coordinate_reference_system(self) -> str:
        pass

    @abstractmethod
    def zone_polygons(self) -> Dict[str, Any]:
        """Returns surveyed polygons for primary and secondary zones."""
        pass

    @abstractmethod
    def validate_geometry(self) -> Tuple[bool, List[str]]:
        """Validates polygon convexity, overlap, and coordinate integrity."""
        pass


class EventRecorder(ABC):
    """Abstract Dynamic Event Packaging Interface."""

    @abstractmethod
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
        pass


class ProvenanceRecorder(ABC):
    """Abstract Cryptographic Provenance and Hash-Chaining Interface."""

    @abstractmethod
    def compute_payload_hash(self, payload: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def append_event_to_chain(self, event_id: str, payload_hash: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        pass


class HumanReviewPackage(ABC):
    """Abstract Human Review Package Export and Blinding Interface."""

    @abstractmethod
    def export_reviewer_package(self, event_package: Dict[str, Any]) -> Dict[str, Any]:
        """Exports sanitized review package with all AI/Model scores stripped."""
        pass

    @abstractmethod
    def verify_blinding(self, reviewer_package: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Verifies package contains ZERO model scores or candidate classifications."""
        pass
