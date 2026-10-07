"""
Safety Backfire Comparison Engine — V0.9
Compares pre-intervention and post-intervention risk baselines to detect
the Safety Backfire Effect: when a safety intervention paradoxically increases risk.
"""
from typing import Dict, Any, Optional
import math


class ComparisonEngine:
    METRIC_LOWER_IS_BETTER = {
        "total_near_miss_incidents":    True,
        "total_proximity_warnings":     True,
        "percent_time_in_risk_zones":   True,
        "frames_in_danger_zone":        True,
        "frames_in_caution_zone":       True,
        "peak_approach_speed_px_s":     True,
        "min_passing_distance_meters":  False,
        "min_passing_distance_pixels":  False,
    }

    def compare(self, before: Dict[str, Any], after: Dict[str, Any],
                before_label: str = "Pre-Intervention",
                after_label: str = "Post-Intervention") -> Dict[str, Any]:
        metrics = {}
        backfire_scores = []
        improvement_scores = []

        for key, lower_is_better in self.METRIC_LOWER_IS_BETTER.items():
            b_val = before.get(key)
            a_val = after.get(key)
            if b_val is None or a_val is None:
                metrics[key] = {"before": b_val, "after": a_val, "change": None, "change_pct": None, "verdict": "N/A"}
                continue
            delta = a_val - b_val
            pct = round((delta / abs(b_val)) * 100.0, 1) if b_val != 0 else (None if a_val == 0 else (100.0 if a_val > 0 else -100.0))
            if delta == 0:
                verdict = "UNCHANGED"
            elif lower_is_better:
                verdict = "BACKFIRE" if delta > 0 else "IMPROVEMENT"
            else:
                verdict = "BACKFIRE" if delta < 0 else "IMPROVEMENT"
            # Custom metric weighting
            multiplier = 1.0
            if "min_passing_distance" in key:
                multiplier = 3.0  # Distance is the primary safety indicator
            elif "peak_approach_speed" in key:
                multiplier = 0.2  # Speed is highly susceptible to tracking noise
            elif "near_miss" in key or "danger_zone" in key:
                multiplier = 4.0  # Critical events are heavily weighted

            base_weight = min(abs(pct) / 100.0, 3.0) if pct is not None else min(abs(delta), 3.0)
            weight = base_weight * multiplier

            (backfire_scores if verdict == "BACKFIRE" else improvement_scores if verdict == "IMPROVEMENT" else []).append(weight)
            metrics[key] = {"before": b_val, "after": a_val, "change": round(delta, 3), "change_pct": pct, "verdict": verdict}

        net_score = sum(backfire_scores) - sum(improvement_scores)
        if net_score > 1.0:   overall_verdict = "SAFETY_BACKFIRE_DETECTED"
        elif net_score > 0.2: overall_verdict = "PARTIAL_BACKFIRE_RISK"
        elif net_score < -1.0:overall_verdict = "CLEAR_IMPROVEMENT"
        elif net_score < -0.2:overall_verdict = "MARGINAL_IMPROVEMENT"
        else:                  overall_verdict = "NO_SIGNIFICANT_CHANGE"

        bc = sum(1 for m in metrics.values() if m["verdict"] == "BACKFIRE")
        ic = sum(1 for m in metrics.values() if m["verdict"] == "IMPROVEMENT")

        return {
            "comparison_labels": {"before": before_label, "after": after_label},
            "metrics": metrics,
            "summary": {
                "metrics_showing_backfire": bc,
                "metrics_showing_improvement": ic,
                "metrics_unchanged": len(metrics) - bc - ic,
                "net_backfire_score": round(net_score, 3),
                "overall_verdict": overall_verdict,
            },
            "scientific_note": (
                "Comparison is valid only if both segments were processed through "
                "the same V0.8 pipeline configuration and camera calibration. "
                "Metric distances and TTC values are image-space proxies. "
                "Safety Backfire detection is preliminary subject to V0.7 model "
                "recall limitations (~17% person detection rate on this CCTV angle)."
            ),
        }

    def format_report(self, report: Dict[str, Any]) -> str:
        labels = report["comparison_labels"]
        summary = report["summary"]
        verdict = summary["overall_verdict"]
        emoji = {"SAFETY_BACKFIRE_DETECTED": "BACKFIRE", "PARTIAL_BACKFIRE_RISK": "PARTIAL BACKFIRE",
                 "CLEAR_IMPROVEMENT": "IMPROVEMENT", "MARGINAL_IMPROVEMENT": "MARGINAL IMPROVEMENT",
                 "NO_SIGNIFICANT_CHANGE": "NO CHANGE"}.get(verdict, verdict)
        lines = [f"=== Safety Backfire Analysis: {emoji} ===\n",
                 f"{'Metric':<40} {'BEFORE':>10} {'AFTER':>10} {'CHANGE':>10} {'VERDICT'}"]
        lines.append("-" * 85)
        for key, m in report["metrics"].items():
            if m["verdict"] == "N/A": continue
            b = f"{m['before']:.2f}" if isinstance(m['before'], float) else str(m['before'])
            a = f"{m['after']:.2f}" if isinstance(m['after'], float) else str(m['after'])
            pct = f"{m['change_pct']:+.1f}%" if m['change_pct'] is not None else "—"
            v = "[!]" if m['verdict'] == "BACKFIRE" else "[+]" if m['verdict'] == "IMPROVEMENT" else "[ ]"
            lines.append(f"{key:<40} {b:>10} {a:>10} {pct:>10}  {v} {m['verdict']}")
        lines += ["", f"Net backfire score : {summary['net_backfire_score']:+.3f}",
                  f"Overall verdict    : {verdict}",
                  f"\nNote: {report['scientific_note']}"]
        return "\n".join(lines)
