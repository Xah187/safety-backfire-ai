"""
V3.1 Safety Ontology — Multi-Hazard Classification Engine

Transforms interactions, entity states, and environmental cues into structured, evidence-backed HazardRecords.
"""
from typing import Dict, Any, List, Optional
from safety_backfire_v3.ontology.interactions.types import (
    InteractionRecord,
    InteractionType,
    InteractionSeverity,
    InteractionImminence
)
from safety_backfire_v3.ontology.entities.base import EntityBase, EntityCategory
from safety_backfire_v3.ontology.entities.people import PersonEntity
from safety_backfire_v3.ontology.entities.infrastructure import InfrastructureEntity, InfraType
from safety_backfire_v3.ontology.states.states import PostureState, StructuralState
from safety_backfire_v3.ontology.hazards.taxonomy import (
    HazardType,
    HazardLifecycleState,
    HazardRecord
)

class MultiHazardEngine:
    """
    Evaluates warehouse hazard instances across 20 controlled hazard types.
    """
    _hazard_counter = 0

    @classmethod
    def evaluate_interaction_hazard(
        cls,
        interaction: InteractionRecord,
        entity_a: Optional[EntityBase] = None,
        entity_b: Optional[EntityBase] = None,
        zone_id: str = "GLOBAL"
    ) -> Optional[HazardRecord]:
        """Maps an active interaction record into a concrete hazard."""
        if interaction.interaction_type == InteractionType.BENIGN_INTERACTION:
            return None

        cls._hazard_counter += 1
        hz_id = f"HZ_{cls._hazard_counter:05d}"
        
        int_type = interaction.interaction_type
        entities = [interaction.entity_a_id, interaction.entity_b_id]
        
        hz_type = HazardType.UNKNOWN_HAZARD
        desc = "generic_interaction_hazard"

        if int_type == InteractionType.COLLISION_RISK:
            hz_type = HazardType.COLLISION_HAZARD
            desc = "collision_risk_between_entities"
        elif int_type == InteractionType.IMPACT:
            hz_type = HazardType.STRUCK_BY_HAZARD
            desc = "physical_impact_or_near_strike"
        elif int_type == InteractionType.ENCROACHMENT:
            hz_type = HazardType.COLLISION_HAZARD
            desc = "proximity_clearance_encroachment"
        elif int_type == InteractionType.COLLAPSE_EXPOSURE:
            hz_type = HazardType.COLLAPSE_HAZARD
            desc = "unstable_load_or_structure_collapse_exposure"
        elif int_type == InteractionType.FALL_EXPOSURE:
            hz_type = HazardType.FALLING_OBJECT_HAZARD
            desc = "falling_object_exposure_to_person"
        elif int_type == InteractionType.ENTRAPMENT_EXPOSURE:
            hz_type = HazardType.MACHINERY_EXPOSURE_HAZARD
            desc = "machinery_entrapment_nip_point_exposure"
        elif int_type == InteractionType.BLOCKING:
            # Differentiate blocked egress vs aisle vs fire route
            infra = entity_b if (entity_b and entity_b.category == EntityCategory.INFRASTRUCTURE) else entity_a
            infra_type = getattr(infra, "infra_type", None)
            if infra_type == InfraType.EMERGENCY_EXIT or getattr(infra, "is_egress_path", False):
                hz_type = HazardType.BLOCKED_EGRESS_HAZARD
                desc = "emergency_egress_route_obstructed"
            elif infra_type == InfraType.FIRE_EQUIPMENT_ZONE:
                hz_type = HazardType.FIRE_ACCESS_HAZARD
                desc = "fire_equipment_access_obstructed"
            else:
                hz_type = HazardType.BLOCKED_AISLE_HAZARD
                desc = "traffic_aisle_obstructed"
        elif int_type == InteractionType.RESTRICTED_ZONE_INTRUSION:
            is_person = (entity_a and entity_a.category == EntityCategory.PERSON) or (entity_b and entity_b.category == EntityCategory.PERSON)
            if is_person:
                hz_type = HazardType.PEDESTRIAN_ZONE_INTRUSION
                desc = "unauthorized_pedestrian_in_restricted_zone"
            else:
                hz_type = HazardType.VEHICLE_ZONE_INTRUSION
                desc = "vehicle_in_restricted_zone"

        # State promotion
        lifecycle = HazardLifecycleState.CONFIRMED if interaction.imminence in [InteractionImminence.IMMINENT, InteractionImminence.HIGH] else HazardLifecycleState.CANDIDATE

        return HazardRecord(
            hazard_id=hz_id,
            hazard_type=hz_type,
            entity_ids=entities,
            zone_id=zone_id,
            severity=interaction.severity,
            imminence=interaction.imminence,
            confidence=0.88,
            evidence_quality=interaction.evidence_quality,
            state=lifecycle,
            provenance=interaction.provenance,
            description=desc
        )

    @classmethod
    def evaluate_postural_hazard(cls, person: PersonEntity, zone_id: str = "GLOBAL") -> Optional[HazardRecord]:
        """Evaluates standalone postural hazards (e.g. fallen worker, working at height)."""
        if person.posture == PostureState.FALLEN or person.man_down_candidate:
            cls._hazard_counter += 1
            return HazardRecord(
                hazard_id=f"HZ_{cls._hazard_counter:05d}",
                hazard_type=HazardType.FALL_HAZARD,
                entity_ids=[person.entity_id],
                zone_id=zone_id,
                severity=InteractionSeverity.CRITICAL,
                imminence=InteractionImminence.HIGH,
                confidence=0.90,
                evidence_quality=0.85,
                state=HazardLifecycleState.ACTIVE,
                description="worker_fallen_man_down_candidate"
            )
        elif person.posture == PostureState.WORKING_AT_HEIGHT and person.elevation_z_m > 2.0:
            cls._hazard_counter += 1
            return HazardRecord(
                hazard_id=f"HZ_{cls._hazard_counter:05d}",
                hazard_type=HazardType.FALL_HAZARD,
                entity_ids=[person.entity_id],
                zone_id=zone_id,
                severity=InteractionSeverity.CRITICAL,
                imminence=InteractionImminence.MEDIUM,
                confidence=0.85,
                evidence_quality=0.80,
                state=HazardLifecycleState.CANDIDATE,
                description="worker_elevated_fall_risk"
            )
        return None

    @classmethod
    def evaluate_environmental_hazard(
        cls,
        hazard_type: HazardType,
        affected_entities: List[str],
        zone_id: str = "GLOBAL",
        severity: InteractionSeverity = InteractionSeverity.MODERATE,
        imminence: InteractionImminence = InteractionImminence.MEDIUM,
        description: str = "environmental_hazard"
    ) -> HazardRecord:
        """Constructs an environmental hazard record (spills, dock edges, debris)."""
        cls._hazard_counter += 1
        return HazardRecord(
            hazard_id=f"HZ_{cls._hazard_counter:05d}",
            hazard_type=hazard_type,
            entity_ids=affected_entities,
            zone_id=zone_id,
            severity=severity,
            imminence=imminence,
            confidence=0.85,
            evidence_quality=0.80,
            state=HazardLifecycleState.ACTIVE,
            description=description
        )
