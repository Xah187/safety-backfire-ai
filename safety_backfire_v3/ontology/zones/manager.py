"""
V3.1 Safety Ontology — Spatial Zone Definitions & Manager
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from safety_backfire_v3.ontology.entities.infrastructure import InfraType

@dataclass
class ZoneDefinition:
    zone_id: str
    infra_type: InfraType
    polygon_vertices_m: List[Tuple[float, float]]
    speed_limit_m_s: Optional[float] = None
    is_egress: bool = False
    is_pedestrian_only: bool = False
    is_vehicle_only: bool = False
    is_restricted: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "type": self.infra_type.value,
            "polygon": [list(v) for v in self.polygon_vertices_m],
            "speed_limit_m_s": self.speed_limit_m_s,
            "is_egress": self.is_egress,
            "is_restricted": self.is_restricted
        }

class ZoneManager:
    """
    Manages 2D ground warehouse zones and spatial containment queries.
    """
    def __init__(self):
        self._zones: Dict[str, ZoneDefinition] = {}

    def register_zone(self, zone: ZoneDefinition):
        self._zones[zone.zone_id] = zone

    def get_zone(self, zone_id: str) -> Optional[ZoneDefinition]:
        return self._zones.get(zone_id)

    def find_containing_zones(self, point: Tuple[float, float]) -> List[ZoneDefinition]:
        """Finds all zones whose 2D ground footprint contains the point."""
        containing = []
        for z in self._zones.values():
            if self._point_in_poly(point, z.polygon_vertices_m):
                containing.append(z)
        return containing

    @staticmethod
    def _point_in_poly(pt: Tuple[float, float], verts: List[Tuple[float, float]]) -> bool:
        if not verts or len(verts) < 3:
            return False
        x, y = pt
        n = len(verts)
        inside = False
        p1x, p1y = verts[0]
        for i in range(1, n + 1):
            p2x, p2y = verts[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
