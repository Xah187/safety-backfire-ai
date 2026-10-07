"""
Phase 12 — Counterfactual Analysis

Provides a heuristic estimation of what might have happened without the intervention.
Strictly avoids claiming causal proof; outputs use terms like "consistent with", "suggests signal".
"""
from typing import Dict, Any, List

class CounterfactualEngine:
    
    @staticmethod
    def _calculate_exposure_rate(events: List[Dict[str, Any]], total_frames: int) -> float:
        if total_frames == 0: return 0.0
        total_risk = sum([e.get("risk_exposure_score", 0.0) for e in events])
        # Rate per 1000 frames for numerical stability
        return (total_risk / total_frames) * 1000.0

    @staticmethod
    def analyze(
        before_events: List[Dict[str, Any]], 
        after_events: List[Dict[str, Any]], 
        before_frames: int, 
        after_frames: int
    ) -> Dict[str, Any]:
        """
        Calculates counterfactual exposure using a naive rate-based projection.
        """
        before_rate = CounterfactualEngine._calculate_exposure_rate(before_events, before_frames)
        
        # Expected exposure in the AFTER segment IF the BEFORE rate had continued unchanged
        expected_after_exposure = before_rate * (after_frames / 1000.0) if after_frames > 0 else 0.0
        
        # Actual observed exposure
        observed_after_exposure = sum([e.get("risk_exposure_score", 0.0) for e in after_events])
        
        deviation = observed_after_exposure - expected_after_exposure
        
        # Determine counterfactual signal
        if deviation > 20.0:
            signal = "CONSISTENT_WITH_BACKFIRE"
            desc = "Observed risk significantly exceeds the counterfactual projection."
        elif deviation < -20.0:
            signal = "CONSISTENT_WITH_IMPROVEMENT"
            desc = "Observed risk is significantly lower than the counterfactual projection."
        else:
            signal = "NO_STRONG_SIGNAL"
            desc = "Observed risk is within margin of error of the counterfactual projection."
            
        # Confidence heuristically scales with volume of data
        total_events = len(before_events) + len(after_events)
        counterfactual_confidence = min(0.9, total_events / 50.0)
        
        return {
            "expected_exposure": round(expected_after_exposure, 2),
            "observed_exposure": round(observed_after_exposure, 2),
            "counterfactual_deviation": round(deviation, 2),
            "counterfactual_signal": signal,
            "description": desc,
            "counterfactual_confidence": round(counterfactual_confidence, 2),
            "limitations": [
                "Assumes linear, constant risk generation over time.",
                "Does not account for external variables (e.g. shift changes, fatigue).",
                "NOT A CAUSAL PROOF. Represents statistical evidence only."
            ]
        }
