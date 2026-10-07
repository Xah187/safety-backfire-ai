"""
V3.1 Safety Ontology — Reusable Interaction Matrix

Evaluates domain-specific interactions across entity categories without hardcoded pairwise logic.
"""
from typing import Dict, Any, Optional, List
from safety_backfire_v3.ontology.entities.base import EntityBase, EntityCategory
from safety_backfire_v3.ontology.entities.people import PersonEntity
from safety_backfire_v3.ontology.entities.vehicles import VehicleEntity
from safety_backfire_v3.ontology.entities.storage import StorageStructureEntity, LoadEntity
from safety_backfire_v3.ontology.entities.machinery import MachineEntity
from safety_backfire_v3.ontology.entities.infrastructure import InfrastructureEntity
from safety_backfire_v3.ontology.relations.types import (
    RelationRecord,
    SpatialRelationType,
    KinematicRelationType,
    TopologicalRelationType,
    StructuralRelationType
)
from safety_backfire_v3.ontology.interactions.types import (
    InteractionType,
    InteractionSeverity,
    InteractionImminence,
    InteractionRecord
)

class InteractionMatrix:
    """
    Evaluates risk interactions between any two entities based on categories, states, and relations.
    """
    _interaction_counter = 0

    @classmethod
    def evaluate(cls, entity_a: EntityBase, entity_b: EntityBase, relation: RelationRecord) -> InteractionRecord:
        cls._interaction_counter += 1
        int_id = f"INT_{cls._interaction_counter:05d}"
        
        cat_a = entity_a.category
        cat_b = entity_b.category
        
        # Order-independent category pair matching
        # 1. Person ↔ Vehicle
        if (cat_a == EntityCategory.PERSON and cat_b == EntityCategory.VEHICLE) or \
           (cat_a == EntityCategory.VEHICLE and cat_b == EntityCategory.PERSON):
            person = entity_a if cat_a == EntityCategory.PERSON else entity_b
            vehicle = entity_b if cat_a == EntityCategory.PERSON else entity_a
            return cls._evaluate_person_vehicle(int_id, person, vehicle, relation)

        # 2. Vehicle ↔ Storage Structure (Forklift ↔ Rack)
        if (cat_a == EntityCategory.VEHICLE and cat_b == EntityCategory.STORAGE_STRUCTURE) or \
           (cat_a == EntityCategory.STORAGE_STRUCTURE and cat_b == EntityCategory.VEHICLE):
            vehicle = entity_a if cat_a == EntityCategory.VEHICLE else entity_b
            storage = entity_b if cat_a == EntityCategory.VEHICLE else entity_a
            return cls._evaluate_vehicle_storage(int_id, vehicle, storage, relation)

        # 3. Load ↔ Storage Structure (Pallet ↔ Rack)
        if (cat_a == EntityCategory.LOAD and cat_b == EntityCategory.STORAGE_STRUCTURE) or \
           (cat_a == EntityCategory.STORAGE_STRUCTURE and cat_b == EntityCategory.LOAD):
            load = entity_a if cat_a == EntityCategory.LOAD else entity_b
            storage = entity_b if cat_a == EntityCategory.LOAD else entity_a
            return cls._evaluate_load_storage(int_id, load, storage, relation)

        # 4. Person ↔ Machinery (Worker ↔ Conveyor/Compactor)
        if (cat_a == EntityCategory.PERSON and cat_b == EntityCategory.MACHINE) or \
           (cat_a == EntityCategory.MACHINE and cat_b == EntityCategory.PERSON):
            person = entity_a if cat_a == EntityCategory.PERSON else entity_b
            machine = entity_b if cat_a == EntityCategory.PERSON else entity_a
            return cls._evaluate_person_machine(int_id, person, machine, relation)

        # 5. Entity ↔ Infrastructure (Obstruction, Blocking Egress, Zone Intrusion)
        if cat_b == EntityCategory.INFRASTRUCTURE:
            return cls._evaluate_entity_infrastructure(int_id, entity_a, entity_b, relation)
        elif cat_a == EntityCategory.INFRASTRUCTURE:
            return cls._evaluate_entity_infrastructure(int_id, entity_b, entity_a, relation)

        # 6. Load ↔ Person (Falling object / crush exposure)
        if (cat_a == EntityCategory.LOAD and cat_b == EntityCategory.PERSON) or \
           (cat_a == EntityCategory.PERSON and cat_b == EntityCategory.LOAD):
            load = entity_a if cat_a == EntityCategory.LOAD else entity_b
            person = entity_b if cat_a == EntityCategory.LOAD else entity_a
            return cls._evaluate_load_person(int_id, load, person, relation)

        # 7. Vehicle ↔ Vehicle
        if cat_a == EntityCategory.VEHICLE and cat_b == EntityCategory.VEHICLE:
            return cls._evaluate_vehicle_vehicle(int_id, entity_a, entity_b, relation)

        # Default Benign
        return InteractionRecord(
            interaction_id=int_id,
            interaction_type=InteractionType.BENIGN_INTERACTION,
            entity_a_id=entity_a.entity_id,
            entity_b_id=entity_b.entity_id,
            relation=relation,
            severity=InteractionSeverity.NEGLIGIBLE,
            imminence=InteractionImminence.NONE
        )

    @classmethod
    def _evaluate_person_vehicle(cls, int_id: str, person: Any, vehicle: Any, rel: RelationRecord) -> InteractionRecord:
        # Operator suppression check
        if getattr(person, "is_operator_suppressed", False) or getattr(person, "associated_vehicle_id", None) == vehicle.entity_id:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.BENIGN_INTERACTION,
                entity_a_id=person.entity_id,
                entity_b_id=vehicle.entity_id,
                relation=rel,
                severity=InteractionSeverity.NEGLIGIBLE,
                imminence=InteractionImminence.NONE,
                metadata={"suppressed_operator": True}
            )

        dist = rel.distance_m if rel.distance_m is not None else 99.0
        ttc = rel.ttc_sec

        if dist <= 0.30 or rel.spatial_relation == SpatialRelationType.TOUCHING:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.IMPACT if dist <= 0.15 else InteractionType.COLLISION_RISK,
                entity_a_id=person.entity_id,
                entity_b_id=vehicle.entity_id,
                relation=rel,
                severity=InteractionSeverity.CRITICAL,
                imminence=InteractionImminence.IMMINENT
            )
        elif ttc is not None and ttc <= 2.5:
            imminence = InteractionImminence.IMMINENT if ttc <= 1.5 else InteractionImminence.HIGH
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.COLLISION_RISK,
                entity_a_id=person.entity_id,
                entity_b_id=vehicle.entity_id,
                relation=rel,
                severity=InteractionSeverity.CRITICAL,
                imminence=imminence
            )
        elif dist <= 1.5:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.COLLISION_RISK,
                entity_a_id=person.entity_id,
                entity_b_id=vehicle.entity_id,
                relation=rel,
                severity=InteractionSeverity.CRITICAL,
                imminence=InteractionImminence.HIGH
            )
        elif dist <= 3.0:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.ENCROACHMENT,
                entity_a_id=person.entity_id,
                entity_b_id=vehicle.entity_id,
                relation=rel,
                severity=InteractionSeverity.MODERATE,
                imminence=InteractionImminence.MEDIUM
            )
        return InteractionRecord(
            interaction_id=int_id,
            interaction_type=InteractionType.BENIGN_INTERACTION,
            entity_a_id=person.entity_id,
            entity_b_id=vehicle.entity_id,
            relation=rel,
            severity=InteractionSeverity.NEGLIGIBLE,
            imminence=InteractionImminence.NONE
        )

    @classmethod
    def _evaluate_vehicle_storage(cls, int_id: str, vehicle: Any, storage: Any, rel: RelationRecord) -> InteractionRecord:
        dist = rel.distance_m if rel.distance_m is not None else 99.0
        ttc = rel.ttc_sec
        if dist <= 0.25:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.IMPACT,
                entity_a_id=vehicle.entity_id,
                entity_b_id=storage.entity_id,
                relation=rel,
                severity=InteractionSeverity.CATASTROPHIC, # Racking collapse danger!
                imminence=InteractionImminence.IMMINENT
            )
        elif ttc is not None and ttc <= 2.0:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.COLLISION_RISK,
                entity_a_id=vehicle.entity_id,
                entity_b_id=storage.entity_id,
                relation=rel,
                severity=InteractionSeverity.CRITICAL,
                imminence=InteractionImminence.HIGH
            )
        return InteractionRecord(
            interaction_id=int_id,
            interaction_type=InteractionType.BENIGN_INTERACTION,
            entity_a_id=vehicle.entity_id,
            entity_b_id=storage.entity_id,
            relation=rel,
            severity=InteractionSeverity.NEGLIGIBLE,
            imminence=InteractionImminence.NONE
        )

    @classmethod
    def _evaluate_load_storage(cls, int_id: str, load: Any, storage: Any, rel: RelationRecord) -> InteractionRecord:
        load_state = getattr(load, "structural_state", None)
        tilt = getattr(load, "tilt_angle_deg", 0.0)
        overhang = getattr(load, "overhang_distance_m", 0.0)
        
        is_unstable = (load_state and load_state.value in ["UNSTABLE", "TILTED", "OVERHANGING", "DAMAGED"]) or tilt > 8.0 or overhang > 0.30
        if is_unstable:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.COLLAPSE_EXPOSURE,
                entity_a_id=load.entity_id,
                entity_b_id=storage.entity_id,
                relation=rel,
                severity=InteractionSeverity.CRITICAL,
                imminence=InteractionImminence.HIGH,
                metadata={"tilt_deg": tilt, "overhang_m": overhang}
            )
        return InteractionRecord(
            interaction_id=int_id,
            interaction_type=InteractionType.BENIGN_INTERACTION,
            entity_a_id=load.entity_id,
            entity_b_id=storage.entity_id,
            relation=rel,
            severity=InteractionSeverity.NEGLIGIBLE,
            imminence=InteractionImminence.NONE
        )

    @classmethod
    def _evaluate_person_machine(cls, int_id: str, person: Any, machine: Any, rel: RelationRecord) -> InteractionRecord:
        dist = rel.distance_m if rel.distance_m is not None else 99.0
        op_state = getattr(machine, "operational_state", None)
        has_guard = getattr(machine, "has_physical_guard", True)
        
        is_running = (op_state and op_state.value == "RUNNING")
        if is_running and dist <= 1.2:
            severity = InteractionSeverity.CATASTROPHIC if not has_guard else InteractionSeverity.CRITICAL
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.ENTRAPMENT_EXPOSURE,
                entity_a_id=person.entity_id,
                entity_b_id=machine.entity_id,
                relation=rel,
                severity=severity,
                imminence=InteractionImminence.HIGH if dist > 0.5 else InteractionImminence.IMMINENT
            )
        return InteractionRecord(
            interaction_id=int_id,
            interaction_type=InteractionType.BENIGN_INTERACTION,
            entity_a_id=person.entity_id,
            entity_b_id=machine.entity_id,
            relation=rel,
            severity=InteractionSeverity.NEGLIGIBLE,
            imminence=InteractionImminence.NONE
        )

    @classmethod
    def _evaluate_entity_infrastructure(cls, int_id: str, entity: Any, infra: Any, rel: RelationRecord) -> InteractionRecord:
        infra_type = getattr(infra, "infra_type", None)
        is_inside = (rel.topological_relation == TopologicalRelationType.INSIDE_ZONE)
        is_blocking = (rel.structural_relation == StructuralRelationType.BLOCKING)
        
        if is_blocking or (is_inside and getattr(infra, "is_egress_path", False) and entity.category.value in ["LOAD", "VEHICLE"]):
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.BLOCKING,
                entity_a_id=entity.entity_id,
                entity_b_id=infra.entity_id,
                relation=rel,
                severity=InteractionSeverity.CRITICAL if getattr(infra, "is_egress_path", False) else InteractionSeverity.MODERATE,
                imminence=InteractionImminence.HIGH
            )
        elif is_inside and getattr(infra, "is_restricted_access", False) and entity.category == EntityCategory.PERSON:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.RESTRICTED_ZONE_INTRUSION,
                entity_a_id=entity.entity_id,
                entity_b_id=infra.entity_id,
                relation=rel,
                severity=InteractionSeverity.CRITICAL,
                imminence=InteractionImminence.HIGH
            )
        return InteractionRecord(
            interaction_id=int_id,
            interaction_type=InteractionType.BENIGN_INTERACTION,
            entity_a_id=entity.entity_id,
            entity_b_id=infra.entity_id,
            relation=rel,
            severity=InteractionSeverity.NEGLIGIBLE,
            imminence=InteractionImminence.NONE
        )

    @classmethod
    def _evaluate_load_person(cls, int_id: str, load: Any, person: Any, rel: RelationRecord) -> InteractionRecord:
        dist = rel.distance_m if rel.distance_m is not None else 99.0
        load_state = getattr(load, "structural_state", None)
        is_unstable = (load_state and load_state.value in ["UNSTABLE", "TILTED", "OVERHANGING"])
        
        # If load is elevated above or near pedestrian and unstable
        if dist <= 1.5 and is_unstable:
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.FALL_EXPOSURE,
                entity_a_id=load.entity_id,
                entity_b_id=person.entity_id,
                relation=rel,
                severity=InteractionSeverity.CATASTROPHIC, # Crushing by falling load
                imminence=InteractionImminence.IMMINENT
            )
        return InteractionRecord(
            interaction_id=int_id,
            interaction_type=InteractionType.BENIGN_INTERACTION,
            entity_a_id=load.entity_id,
            entity_b_id=person.entity_id,
            relation=rel,
            severity=InteractionSeverity.NEGLIGIBLE,
            imminence=InteractionImminence.NONE
        )

    @classmethod
    def _evaluate_vehicle_vehicle(cls, int_id: str, v1: Any, v2: Any, rel: RelationRecord) -> InteractionRecord:
        dist = rel.distance_m if rel.distance_m is not None else 99.0
        ttc = rel.ttc_sec
        if dist <= 1.5 or (ttc is not None and ttc <= 2.0):
            return InteractionRecord(
                interaction_id=int_id,
                interaction_type=InteractionType.COLLISION_RISK,
                entity_a_id=v1.entity_id,
                entity_b_id=v2.entity_id,
                relation=rel,
                severity=InteractionSeverity.CRITICAL,
                imminence=InteractionImminence.HIGH
            )
        return InteractionRecord(
            interaction_id=int_id,
            interaction_type=InteractionType.BENIGN_INTERACTION,
            entity_a_id=v1.entity_id,
            entity_b_id=v2.entity_id,
            relation=rel,
            severity=InteractionSeverity.NEGLIGIBLE,
            imminence=InteractionImminence.NONE
        )
