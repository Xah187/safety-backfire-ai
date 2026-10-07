"""
Phase 14 — Explainability Layer

Generates a structured, highly traceable explanation of the decision engine's verdict.
Links every conclusion directly to underlying Event IDs, metrics, and frames.
"""
from typing import Dict, Any, List

class ExplainabilityLayer:
    
    @staticmethod
    def generate_explanation(
        verdict: Dict[str, Any],
        comparison: Dict[str, Any],
        redistribution: Dict[str, Any],
        before_events: List[Dict[str, Any]],
        after_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Creates a traceable explanation for the Safety Backfire AI verdict.
        """
        signal = verdict["signal"]
        
        # 1. Summary
        if signal == "SAFETY_BACKFIRE":
            summary = "The intervention was followed by a significant increase in overall risk exposure and a displacement of risk to new zones, consistent with the Safety Backfire effect."
        elif signal == "RISK_IMPROVEMENT":
            summary = "The intervention successfully reduced overall risk exposure without significantly displacing it."
        elif signal == "INSUFFICIENT_EVIDENCE":
            summary = "The system cannot render a verdict due to insufficient evidence quality."
        else:
            summary = "The data does not show a strong enough signal to definitively conclude a backfire or improvement."
            
        # 2. Key Changes (Metrics tracing)
        key_changes = [
            {
                "metric": "Total Risk Exposure",
                "before": comparison["total_risk_exposure"]["before"],
                "after": comparison["total_risk_exposure"]["after"],
                "change": f"{comparison['total_risk_exposure']['direction']} by {comparison['total_risk_exposure']['percentage_change']}%"
            },
            {
                "metric": "High Severity Events",
                "before": comparison["high_severity_events"]["before"],
                "after": comparison["high_severity_events"]["after"],
                "change": f"{comparison['high_severity_events']['direction']} by {comparison['high_severity_events']['absolute_change']} events"
            }
        ]
        
        # 3. Risk Redistribution (Zone tracing)
        risk_redis = []
        if redistribution["risk_displaced"]:
            for zone in redistribution["decreased_zones"]:
                risk_redis.append({"zone": zone, "trend": "DECREASED", "delta": redistribution["redistribution"][f"zone_{zone}"]["risk_delta"]})
            for zone in redistribution["increased_zones"]:
                risk_redis.append({"zone": zone, "trend": "INCREASED", "delta": redistribution["redistribution"][f"zone_{zone}"]["risk_delta"]})
                
        # 4. Supporting Events (Event & Frame tracing)
        # Extract the top 3 highest risk events from the AFTER segment to support a backfire claim
        sorted_after = sorted(after_events, key=lambda e: e.get("risk_exposure_score", 0.0), reverse=True)
        top_events = sorted_after[:3]
        
        supporting_events = []
        for e in top_events:
            supporting_events.append({
                "event_id": e.get("event_id", "UNKNOWN"),
                "frames": f"{e.get('start_frame', '?')} - {e.get('end_frame', '?')}",
                "zone": e.get("zone", "UNKNOWN"),
                "severity": e.get("severity_level", "UNKNOWN"),
                "risk_contribution": e.get("risk_exposure_score", 0.0)
            })
            
        return {
            "summary": summary,
            "key_changes": key_changes,
            "risk_redistribution": risk_redis,
            "supporting_events": supporting_events,
            "limitations": verdict.get("reasoning", []),
            "confidence": {
                "evidence_level": verdict["evidence_level"],
                "confidence_score": verdict["confidence"]
            }
        }
