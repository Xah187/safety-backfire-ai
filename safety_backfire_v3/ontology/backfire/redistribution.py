"""
V3.1 Safety Ontology — Risk Redistribution & Safety Backfire Taxonomy
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class RiskRedistributionCategory(str, Enum):
    RISK_REDUCED = "RISK_REDUCED"
    RISK_UNCHANGED = "RISK_UNCHANGED"
    RISK_SHIFTED = "RISK_SHIFTED"           # Risk in target zone drops, but rises in adjacent/alternate zone
    RISK_SPLIT = "RISK_SPLIT"               # One high-severity hazard replaced by multiple lower-severity hazards
    RISK_INCREASED = "RISK_INCREASED"       # Overall hazard exposure aggravated post-intervention
    NEW_HAZARD_CREATED = "NEW_HAZARD_CREATED" # A brand new hazard type was introduced by the intervention
    HAZARD_REMOVED = "HAZARD_REMOVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class BackfireSignal(str, Enum):
    TRUE_BACKFIRE = "TRUE_BACKFIRE"               # Overall or adjacent risk increased as a direct consequence
    PARTIAL_BACKFIRE = "PARTIAL_BACKFIRE"         # Intended hazard reduced, but collateral hazard created
    GENUINE_SAFETY_GAIN = "GENUINE_SAFETY_GAIN"   # Intended hazard reduced without adverse redistribution
    NEUTRAL = "NEUTRAL"                           # No statistically significant change detected
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

@dataclass
class BackfireAssessmentRecord:
    assessment_id: str
    intervention_id: str
    primary_category: RiskRedistributionCategory
    backfire_signal: BackfireSignal
    risk_delta_percent: float
    intended_hazard_reduced: bool
    new_hazards_introduced: List[str]
    shifted_zones: List[Dict[str, Any]]
    hazard_counts_before: Dict[str, int]
    hazard_counts_after: Dict[str, int]
    exposure_before: float
    exposure_after: float
    counterfactual_expected_exposure: float
    confidence: float
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "intervention_id": self.intervention_id,
            "primary_category": self.primary_category.value,
            "backfire_signal": self.backfire_signal.value,
            "risk_delta_percent": round(self.risk_delta_percent, 2),
            "intended_hazard_reduced": self.intended_hazard_reduced,
            "new_hazards_introduced": self.new_hazards_introduced,
            "shifted_zones": self.shifted_zones,
            "hazard_counts_before": self.hazard_counts_before,
            "hazard_counts_after": self.hazard_counts_after,
            "exposure_before": round(self.exposure_before, 2),
            "exposure_after": round(self.exposure_after, 2),
            "counterfactual_expected_exposure": round(self.counterfactual_expected_exposure, 2),
            "confidence": round(self.confidence, 3),
            "explanation": self.explanation,
            "metadata": self.metadata
        }
