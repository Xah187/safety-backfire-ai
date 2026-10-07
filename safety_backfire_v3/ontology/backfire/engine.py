"""
V3.1 Safety Ontology — Safety Backfire & Counterfactual Assessment Engine

Analyzes whether a safety intervention truly reduced risk or merely moved, transformed,
split, or aggravated risk elsewhere in the warehouse.
"""
from typing import Dict, Any, List, Optional
from collections import defaultdict

from safety_backfire_v3.ontology.interventions.types import InterventionRecord
from safety_backfire_v3.ontology.interventions.model import CounterfactualTimeline, TemporalLeakageError
from safety_backfire_v3.ontology.backfire.redistribution import (
    RiskRedistributionCategory,
    BackfireSignal,
    BackfireAssessmentRecord
)
from safety_backfire_v3.core.universal_risk_engine import UniversalRiskDecision

class SafetyBackfireEngine:
    """
    Evaluates before vs after risk graphs to uncover unintended safety consequences (Safety Backfire).
    """
    _assessment_counter = 0

    @classmethod
    def evaluate_intervention_effect(
        cls,
        timeline: CounterfactualTimeline,
        before_decisions: List[UniversalRiskDecision],
        after_decisions: List[UniversalRiskDecision]
    ) -> BackfireAssessmentRecord:
        cls._assessment_counter += 1
        ass_id = f"BFA_{cls._assessment_counter:05d}"
        intervention = timeline.intervention

        # 1. Strict Temporal Leakage Invariant Verification
        for d in before_decisions:
            if d.provenance:
                timeline.validate_baseline_frame(d.provenance.source_timestamp)

        # 2. Aggregations
        hz_before = defaultdict(int)
        hz_after = defaultdict(int)
        zone_before_exp = defaultdict(float)
        zone_after_exp = defaultdict(float)
        
        tot_exp_before = 0.0
        for d in before_decisions:
            hz_before[d.hazard_type] += 1
            z = d.telemetry.get("zone", "GLOBAL")
            zone_before_exp[z] += d.risk_score
            tot_exp_before += d.risk_score

        tot_exp_after = 0.0
        for d in after_decisions:
            hz_after[d.hazard_type] += 1
            z = d.telemetry.get("zone", "GLOBAL")
            zone_after_exp[z] += d.risk_score
            tot_exp_after += d.risk_score

        # 3. Check Intended Hazards
        intended_reduced = True
        for int_hz in intervention.intended_hazards:
            b_cnt = hz_before.get(int_hz, 0)
            a_cnt = hz_after.get(int_hz, 0)
            if a_cnt >= b_cnt and b_cnt > 0:
                intended_reduced = False

        # 4. Check for New Hazards Introduced
        new_hazards = []
        for hz, cnt in hz_after.items():
            if cnt > 0 and hz_before.get(hz, 0) == 0:
                new_hazards.append(hz)

        # 5. Zone Risk Shift Analysis
        all_zones = set(list(zone_before_exp.keys()) + list(zone_after_exp.keys()))
        decreased_zones = []
        increased_zones = []
        shifted_zones_details = []

        for z in all_zones:
            b_z = zone_before_exp.get(z, 0.0)
            a_z = zone_after_exp.get(z, 0.0)
            delta = a_z - b_z
            if delta < -0.15 * max(1.0, b_z):
                decreased_zones.append(z)
            elif delta > 0.15 * max(1.0, b_z):
                increased_zones.append(z)
            
            shifted_zones_details.append({
                "zone": z,
                "before_exposure": round(b_z, 2),
                "after_exposure": round(a_z, 2),
                "delta": round(delta, 2)
            })

        has_zone_shift = (len(decreased_zones) > 0 and len(increased_zones) > 0)

        # 6. Counterfactual Expected Exposure
        t_base_dur = max(1.0, timeline.baseline_end_ts - timeline.baseline_start_ts)
        t_post_dur = max(1.0, timeline.post_end_ts - timeline.post_start_ts)
        base_rate = tot_exp_before / t_base_dur
        expected_post_exp = base_rate * t_post_dur

        pct_change = ((tot_exp_after - tot_exp_before) / max(0.1, tot_exp_before)) * 100.0

        # 7. Classification of Primary Category & Backfire Signal
        if new_hazards:
            category = RiskRedistributionCategory.NEW_HAZARD_CREATED
            signal = BackfireSignal.PARTIAL_BACKFIRE if intended_reduced else BackfireSignal.TRUE_BACKFIRE
            explanation = f"Intervention successfully reduced intended hazard but created new unmodeled hazard(s): {', '.join(new_hazards)}."
        elif has_zone_shift:
            category = RiskRedistributionCategory.RISK_SHIFTED
            signal = BackfireSignal.PARTIAL_BACKFIRE
            explanation = f"Intervention shifted risk: decreased in {decreased_zones}, but displaced into {increased_zones}."
        elif pct_change > 15.0:
            category = RiskRedistributionCategory.RISK_INCREASED
            signal = BackfireSignal.TRUE_BACKFIRE
            explanation = f"Intervention backfired: total warehouse risk exposure increased by {pct_change:.1f}%."
        elif pct_change < -15.0 and intended_reduced:
            category = RiskRedistributionCategory.RISK_REDUCED
            signal = BackfireSignal.GENUINE_SAFETY_GAIN
            explanation = f"Intervention achieved genuine safety gain: risk reduced by {abs(pct_change):.1f}% without collateral hazards."
        else:
            category = RiskRedistributionCategory.RISK_UNCHANGED
            signal = BackfireSignal.NEUTRAL
            explanation = "No statistically significant net risk change detected post-intervention."

        conf = min(0.95, (len(before_decisions) + len(after_decisions)) / 30.0)

        return BackfireAssessmentRecord(
            assessment_id=ass_id,
            intervention_id=intervention.intervention_id,
            primary_category=category,
            backfire_signal=signal,
            risk_delta_percent=pct_change,
            intended_hazard_reduced=intended_reduced,
            new_hazards_introduced=new_hazards,
            shifted_zones=shifted_zones_details,
            hazard_counts_before=dict(hz_before),
            hazard_counts_after=dict(hz_after),
            exposure_before=tot_exp_before,
            exposure_after=tot_exp_after,
            counterfactual_expected_exposure=expected_post_exp,
            confidence=conf,
            explanation=explanation,
            metadata={
                "decreased_zones": decreased_zones,
                "increased_zones": increased_zones,
                "baseline_duration_s": t_base_dur,
                "post_duration_s": t_post_dur
            }
        )
