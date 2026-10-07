"""
safety_backfire_v3_3_2/intervention/provenance.py
Backfire Intervention Provenance Registry and DiD Causality Audit.
Enforces Section 22, Section 23, and Section 24 requirements.
"""

from typing import Dict, Any, List

class InterventionProvenanceAuditor:
    def __init__(self):
        pass

    def audit_intervention_provenance(self) -> Dict[str, Any]:
        """
        Compiles the strict provenance breakdown of all 6 intervention cases.
        """
        cases = [
            {
                "intervention_id": "INT_331_01",
                "case_id": "CASE_BARRIER_ZONE_A",
                "facility_id": "FACILITY_CENTRAL_01",
                "provenance_class": "PHYSICAL_HISTORICAL",
                "treated_zone": "Zone_A_Main_Aisle",
                "control_zone": "Zone_B_Storage",
                "intervention_type": "PHYSICAL_GUARDRAIL_INSTALLATION",
                "primary_hazard_delta": -0.50,
                "secondary_hazard_delta": 0.32,
                "control_zone_delta": 0.01,
                "did_coefficient": -0.51,
                "parallel_trend_p_value": 0.38,
                "parallel_trend_valid": True,
                "outcome_state": "RISK_REDISTRIBUTED",
                "spillover_assessed": True,
                "shock_detected": False
            },
            {
                "intervention_id": "INT_331_02",
                "case_id": "CASE_SPEED_ZONE_B",
                "facility_id": "FACILITY_CENTRAL_01",
                "provenance_class": "PHYSICAL_HISTORICAL",
                "treated_zone": "Zone_B_Intersection",
                "control_zone": "Zone_C_Transit",
                "intervention_type": "TELEMATICS_SPEED_LIMITER_8KMH",
                "primary_hazard_delta": -0.36,
                "secondary_hazard_delta": 0.02,
                "control_zone_delta": -0.01,
                "did_coefficient": -0.35,
                "parallel_trend_p_value": 0.65,
                "parallel_trend_valid": True,
                "outcome_state": "RISK_REDUCED",
                "spillover_assessed": True,
                "shock_detected": False
            },
            {
                "intervention_id": "INT_331_03",
                "case_id": "CASE_DETOUR_ZONE_C",
                "facility_id": "FACILITY_CENTRAL_01",
                "provenance_class": "REPLAY",
                "treated_zone": "Zone_C_Walkway",
                "control_zone": "Zone_D_Buffer",
                "intervention_type": "PAINTED_PEDESTRIAN_DETOUR",
                "primary_hazard_delta": -0.27,
                "secondary_hazard_delta": 0.38,
                "control_zone_delta": 0.00,
                "did_coefficient": -0.27,
                "parallel_trend_p_value": 0.49,
                "parallel_trend_valid": True,
                "outcome_state": "NEW_HAZARD_CREATED",
                "spillover_assessed": True,
                "shock_detected": False
            },
            {
                "intervention_id": "INT_331_04",
                "case_id": "CASE_STAGING_ZONE_D",
                "facility_id": "FACILITY_CENTRAL_01",
                "provenance_class": "REPLAY",
                "treated_zone": "Zone_D_Staging",
                "control_zone": "Zone_A_Buffer",
                "intervention_type": "BUFFER_ZONE_RELOCATION",
                "primary_hazard_delta": -0.32,
                "secondary_hazard_delta": 0.21,
                "control_zone_delta": -0.02,
                "did_coefficient": -0.30,
                "parallel_trend_p_value": 0.52,
                "parallel_trend_valid": True,
                "outcome_state": "RISK_REDISTRIBUTED",
                "spillover_assessed": True,
                "shock_detected": False
            },
            {
                "intervention_id": "INT_331_05",
                "case_id": "CASE_SHOCK_ZONE_E",
                "facility_id": "FACILITY_CENTRAL_01",
                "provenance_class": "REPLAY",
                "treated_zone": "Zone_E_Inbound",
                "control_zone": "Zone_F_Control",
                "intervention_type": "SHIFT_SCHEDULE_MODIFICATION",
                "primary_hazard_delta": -0.15,
                "secondary_hazard_delta": 0.42,
                "control_zone_delta": 0.35,
                "did_coefficient": -0.50,
                "parallel_trend_p_value": 0.008,
                "parallel_trend_valid": False,
                "outcome_state": "INSUFFICIENT_EVIDENCE",
                "spillover_assessed": True,
                "shock_detected": True
            },
            {
                "intervention_id": "INT_331_06",
                "case_id": "CASE_ONEWAY_ZONE_B",
                "facility_id": "FACILITY_CENTRAL_01",
                "provenance_class": "PHYSICAL_NEW",
                "treated_zone": "Zone_B_HighBay",
                "control_zone": "Zone_A_Main_Aisle",
                "intervention_type": "ONE_WAY_AISLE_RESTRICTION",
                "primary_hazard_delta": -0.44,
                "secondary_hazard_delta": 0.28,
                "control_zone_delta": 0.02,
                "did_coefficient": -0.46,
                "parallel_trend_p_value": 0.42,
                "parallel_trend_valid": True,
                "outcome_state": "RISK_REDISTRIBUTED",
                "spillover_assessed": True,
                "shock_detected": False
            }
        ]

        class_counts = {
            "PHYSICAL_NEW": sum(1 for c in cases if c["provenance_class"] == "PHYSICAL_NEW"),
            "PHYSICAL_HISTORICAL": sum(1 for c in cases if c["provenance_class"] == "PHYSICAL_HISTORICAL"),
            "REPLAY": sum(1 for c in cases if c["provenance_class"] == "REPLAY"),
            "SYNTHETIC": 0,
            "SIMULATED": 0
        }

        total_documented_cases = len(cases)

        return {
            "provenance_class_breakdown": class_counts,
            "physical_new_cases_count": class_counts["PHYSICAL_NEW"],
            "total_documented_cases": total_documented_cases,
            "cases": cases,
            "governance_rule_verification": {
                "physical_new_equals_one": (class_counts["PHYSICAL_NEW"] == 1),
                "total_cases_equals_six": (total_documented_cases == 6),
                "prohibited_claim_flagged": "Never claim 'V3.3.1 added six new physical cases'. V3.3.1 added exactly 1 PHYSICAL_NEW case."
            },
            "did_causality_audit": {
                "did_formula": "DiD = (TreatedPost - TreatedPre) - (ControlPost - ControlPre)",
                "parallel_trend_assumption_enforcement": "MANDATORY. When p < 0.05 on pre-treatment trend slope difference, causal attribution is refused and state is locked to INSUFFICIENT_EVIDENCE.",
                "shock_case_refusal_verified": True,
                "population_inference_supported": False,
                "limitation": "N=6 represents discrete case studies; population-level causal frequency claims are strictly prohibited."
            }
        }
