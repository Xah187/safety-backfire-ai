"""
V3.1 Safety Ontology — Entity-Agnostic Relation Evaluator

Computes physical, kinematic, and topological relations between any pair of warehouse entities
without hardcoded assumptions on entity types.
"""
import math
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

from safety_backfire_v3.ontology.entities.base import EntityBase
from safety_backfire_v3.ontology.entities.infrastructure import InfrastructureEntity
from safety_backfire_v3.ontology.relations.types import (
    SpatialRelationType,
    KinematicRelationType,
    TopologicalRelationType,
    StructuralRelationType,
    RelationRecord
)

class EntityAgnosticRelationEvaluator:
    """
    Evaluates multi-dimensional spatial, kinematic, and topological relationships.
    """
    def __init__(
        self,
        near_threshold_m: float = 3.0,
        touching_threshold_m: float = 0.25,
        approaching_speed_threshold_m_s: float = 0.15
    ):
        self.near_threshold_m = near_threshold_m
        self.touching_threshold_m = touching_threshold_m
        self.approaching_speed_threshold_m_s = approaching_speed_threshold_m_s

    def evaluate_pair(self, entity_a: EntityBase, entity_b: EntityBase) -> RelationRecord:
        """
        Evaluates physical relations between two dynamic or static entities.
        """
        pos_a = entity_a.world_pos_m
        pos_b = entity_b.world_pos_m
        
        # 1. Spatial Geometry
        if pos_a is not None and pos_b is not None:
            dx = pos_a[0] - pos_b[0]
            dy = pos_a[1] - pos_b[1]
            dist_m = float(math.hypot(dx, dy))
            dist_unc = float(math.hypot(entity_a.position_uncertainty_m, entity_b.position_uncertainty_m))
            
            dz = entity_a.elevation_z_m - entity_b.elevation_z_m
            if dist_m <= self.touching_threshold_m:
                spatial = SpatialRelationType.TOUCHING
            elif abs(dz) >= 0.8 and dist_m <= 1.5:
                spatial = SpatialRelationType.ABOVE if dz > 0 else SpatialRelationType.BELOW
            elif dist_m <= self.near_threshold_m:
                spatial = SpatialRelationType.NEAR
            else:
                spatial = SpatialRelationType.FAR
        else:
            dist_m = None
            dist_unc = None
            spatial = SpatialRelationType.FAR

        # 2D Bounding Box visual overlap check
        if entity_a.bbox_2d is not None and entity_b.bbox_2d is not None:
            if self._check_bbox_overlap(entity_a.bbox_2d, entity_b.bbox_2d):
                if spatial != SpatialRelationType.TOUCHING:
                    spatial = SpatialRelationType.OVERLAPPING_2D

        # 2. Kinematics & Relative Motion
        v_a = entity_a.velocity_m_s or (0.0, 0.0)
        v_b = entity_b.velocity_m_s or (0.0, 0.0)
        speed_a = entity_a.speed_m_s
        speed_b = entity_b.speed_m_s

        if speed_a < 0.05 and speed_b < 0.05:
            kinematic = KinematicRelationType.STATIONARY_PAIR
            approach_speed = 0.0
            ttc_sec = None
        elif pos_a is not None and pos_b is not None and dist_m is not None and dist_m > 1e-4:
            # Relative displacement and velocity vectors
            rx = pos_b[0] - pos_a[0]
            ry = pos_b[1] - pos_a[1]
            # Velocity of A relative to B: v_rel = v_a - v_b
            vx_rel = v_a[0] - v_b[0]
            vy_rel = v_a[1] - v_b[1]
            
            # Radial approach speed: projection of relative velocity onto line of sight
            # Positive if distance is closing
            approach_speed = float((vx_rel * rx + vy_rel * ry) / dist_m)
            
            if approach_speed > self.approaching_speed_threshold_m_s:
                kinematic = KinematicRelationType.APPROACHING
                ttc_sec = max(0.0, dist_m / approach_speed)
            elif approach_speed < -self.approaching_speed_threshold_m_s:
                kinematic = KinematicRelationType.RECEDING
                ttc_sec = None
            else:
                # Check for crossing vs parallel
                cross_dot = abs(v_a[0] * v_b[0] + v_a[1] * v_b[1])
                speed_prod = max(1e-4, speed_a * speed_b)
                cos_ang = cross_dot / speed_prod
                if cos_ang > 0.8:
                    kinematic = KinematicRelationType.PARALLEL
                else:
                    kinematic = KinematicRelationType.CROSSING
                ttc_sec = None
        else:
            kinematic = KinematicRelationType.UNKNOWN_KINEMATICS
            approach_speed = 0.0
            ttc_sec = None

        # 3. Structural Relations
        structural = None
        if spatial == SpatialRelationType.TOUCHING or spatial == SpatialRelationType.ABOVE:
            if entity_a.category.value == "LOAD" and entity_b.category.value in ["STORAGE_STRUCTURE", "VEHICLE"]:
                structural = StructuralRelationType.LOADED_ON
            elif entity_a.category.value == "STORAGE_STRUCTURE" and entity_b.category.value == "LOAD":
                structural = StructuralRelationType.SUPPORTING

        # Confidence
        confidence = 0.85 if dist_m is not None else 0.40

        return RelationRecord(
            subject_entity_id=entity_a.entity_id,
            object_entity_id=entity_b.entity_id,
            spatial_relation=spatial,
            kinematic_relation=kinematic,
            structural_relation=structural,
            distance_m=dist_m,
            distance_uncertainty_m=dist_unc,
            approach_speed_m_s=approach_speed,
            ttc_sec=ttc_sec,
            confidence=confidence,
            start_timestamp=min(entity_a.last_observed_ts, entity_b.last_observed_ts),
            end_timestamp=max(entity_a.last_observed_ts, entity_b.last_observed_ts)
        )

    def evaluate_zone_containment(self, entity: EntityBase, zone: InfrastructureEntity) -> RelationRecord:
        """
        Evaluates topological containment of an entity within an infrastructure zone.
        """
        pos = entity.world_pos_m
        if pos is None or not zone.polygon_vertices_m:
            topological = TopologicalRelationType.OUTSIDE_ZONE
            dist_m = None
        else:
            is_inside = self._point_in_polygon(pos, zone.polygon_vertices_m)
            topological = TopologicalRelationType.INSIDE_ZONE if is_inside else TopologicalRelationType.OUTSIDE_ZONE
            dist_m = 0.0 if is_inside else 2.0

        structural = None
        if topological == TopologicalRelationType.INSIDE_ZONE and zone.is_egress_path:
            if entity.category.value in ["LOAD", "VEHICLE"]:
                structural = StructuralRelationType.BLOCKING

        return RelationRecord(
            subject_entity_id=entity.entity_id,
            object_entity_id=zone.entity_id,
            spatial_relation=SpatialRelationType.NEAR if topological == TopologicalRelationType.INSIDE_ZONE else SpatialRelationType.FAR,
            kinematic_relation=KinematicRelationType.UNKNOWN_KINEMATICS,
            topological_relation=topological,
            structural_relation=structural,
            distance_m=dist_m,
            confidence=0.90 if pos is not None else 0.30
        )

    @staticmethod
    def _check_bbox_overlap(b1: List[float], b2: List[float]) -> bool:
        ix1 = max(b1[0], b2[0])
        iy1 = max(b1[1], b2[1])
        ix2 = min(b1[2], b2[2])
        iy2 = min(b1[3], b2[3])
        return (ix2 > ix1) and (iy2 > iy1)

    @staticmethod
    def _point_in_polygon(point: Tuple[float, float], vertices: List[Tuple[float, float]]) -> bool:
        """Standard ray casting algorithm for 2D point-in-polygon test."""
        x, y = point
        n = len(vertices)
        inside = False
        p1x, p1y = vertices[0]
        for i in range(1, n + 1):
            p2x, p2y = vertices[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
