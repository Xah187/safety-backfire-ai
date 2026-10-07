"""
Phase 13 — Backfire Decision Engine

Integrates all engine outputs (Evidence, Comparison, Redistribution, Counterfactual)
to render a final safety assessment verdict without relying on a single metric.
"""
from typing import Dict, Any, List

class DecisionEngine:
    
    @staticmethod
    def assess(
        evidence_quality: Dict[str, Any],
        comparison_metrics: Dict[str, Any],
        redistribution: Dict[str, Any],
        counterfactual: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes multiple signals to output a final safety verdict.
        """
        # 1. Evidence Check
        if evidence_quality["evidence_level"] == "INSUFFICIENT":
            return {
                "signal": "INSUFFICIENT_EVIDENCE",
                "strength": 0.0,
                "evidence_level": "INSUFFICIENT",
                "confidence": evidence_quality["evidence_confidence"],
                "reasoning": [
                    "Data quality is too poor to render a verdict."
                ] + evidence_quality["limitations"]
            }
            
        reasoning = []
        strength = 0.0
        
        # 2. Extract Key Indicators
        risk_exposure_change = comparison_metrics["total_risk_exposure"]["absolute_change"]
        risk_pct_change = comparison_metrics["total_risk_exposure"]["percentage_change"]
        high_severity_change = comparison_metrics["high_severity_events"]["absolute_change"]
        cf_signal = counterfactual["counterfactual_signal"]
        risk_displaced = redistribution["risk_displaced"]
        
        # 3. Analyze Signals
        if risk_exposure_change > 0:
            strength += 0.3
            reasoning.append(f"Overall risk exposure increased by {risk_pct_change}%.")
            
        if high_severity_change > 0:
            strength += 0.3
            reasoning.append(f"High severity events increased by {high_severity_change}.")
            
        if risk_displaced:
            strength += 0.2
            reasoning.append(f"Risk was displaced spatially (Decreased in {redistribution['decreased_zones']}, but increased in {redistribution['increased_zones']}).")
            
        if cf_signal == "CONSISTENT_WITH_BACKFIRE":
            strength += 0.2
            reasoning.append(f"Observed risk significantly exceeded counterfactual projection (Deviation: +{counterfactual['counterfactual_deviation']}).")
            
        # 4. Render Verdict
        if strength >= 0.7:
            signal = "SAFETY_BACKFIRE"
        elif risk_exposure_change < 0 and cf_signal == "CONSISTENT_WITH_IMPROVEMENT":
            signal = "RISK_IMPROVEMENT"
            strength = 0.8
            reasoning.append("Risk exposure decreased and matched improvement projections.")
        else:
            signal = "NO_SIGNIFICANT_CHANGE"
            reasoning.append("Mixed or weak signals; no definitive backfire or improvement observed.")
            
        # Final Confidence blends evidence quality and signal strength
        final_confidence = round(evidence_quality["evidence_confidence"] * min(1.0, strength + 0.2), 2)
        
        return {
            "signal": signal,
            "strength": round(strength, 2),
            "evidence_level": evidence_quality["evidence_level"],
            "confidence": final_confidence,
            "reasoning": reasoning
        }
