"""
V3.2 Master Report Compiler
Merges all 24 individual V3.2 validation reports into a single, cohesive,
unbroken master engineering release document.
"""

import os
from pathlib import Path

REPORTS_DIR = Path("/Users/xah187/Projects/safety-backfire-ai/reports/v3_2")
MASTER_REPORT_FILE = REPORTS_DIR / "V3.2_MASTER_COMPREHENSIVE_VALIDATION_REPORT.md"

SECTIONS_ORDER = [
    ("PART I: EXECUTIVE CORE STATUS & ENGINEERING RELEASE SIGN-OFF", "V3.2_CORE_STATUS.md"),
    ("PART II: MASTER EMPIRICAL VALIDATION & PRIMARY METRICS TABLE", "V3.2_VALIDATION_REPORT.md"),
    ("PART III: REAL-WORLD WAREHOUSE DATASET SPECIFICATION", "V3.2_DATASET_SPEC.md"),
    ("PART IV: DATASET INDEPENDENCE & LEAKAGE AUDIT", "V3.2_DATASET_INDEPENDENCE_AUDIT.md"),
    ("PART V: INDEPENDENT HUMAN GROUND TRUTH PROTOCOL", "V3.2_GROUND_TRUTH_PROTOCOL.md"),
    ("PART VI: INTER-ANNOTATOR AGREEMENT & RELIABILITY AUDIT", "V3.2_ANNOTATION_AGREEMENT.md"),
    ("PART VII: LEVEL A — REAL PERCEPTION VALIDATION", "V3.2_PERCEPTION_VALIDATION.md"),
    ("PART VIII: LEVEL B — REAL TRACKING VALIDATION", "V3.2_TRACKING_VALIDATION.md"),
    ("PART IX: LEVEL C — REAL IDENTITY & REID STRESS VALIDATION", "V3.2_IDENTITY_VALIDATION.md"),
    ("PART X: LEVEL D — REAL GEOMETRY & WORLD PROJECTION VALIDATION", "V3.2_GEOMETRY_REAL_WORLD_VALIDATION.md"),
    ("PART XI: LEVEL E — REAL UNCERTAINTY & NEAR-ZERO STRESS VALIDATION", "V3.2_UNCERTAINTY_REAL_WORLD_VALIDATION.md"),
    ("PART XII: LEVEL F — REAL TTC & CPA KINEMATIC VALIDATION", "V3.2_TTC_CPA_VALIDATION.md"),
    ("PART XIII: LEVEL G — REAL HAZARD VALIDATION & CAPABILITY TAXONOMY", "V3.2_HAZARD_VALIDATION.md"),
    ("PART XIV: PRIMARY SAFETY METRIC — EVENT-LEVEL VALIDATION", "V3.2_EVENT_VALIDATION.md"),
    ("PART XV: TEMPORAL SAFETY & LATENCY RED-TEAM REPORT", "V3.2_TEMPORAL_SAFETY_REPORT.md"),
    ("PART XVI: CONTINUOUS BOUNDARY CHATTER & HYSTERESIS DAMPING", "V3.2_CHATTER_REPORT.md"),
    ("PART XVII: OPERATIONAL DESIGN DOMAIN (ODD) SPECIFICATION", "V3.2_ODD_VALIDATION.md"),
    ("PART XVIII: INTERVENTION VALIDATION & COUNTERFACTUAL TIMELINE", "V3.2_INTERVENTION_VALIDATION.md"),
    ("PART XIX: CAUSALITY VS CORRELATION: EMPIRICAL ATTRIBUTION", "V3.2_CAUSALITY_VALIDATION.md"),
    ("PART XX: REAL-WORLD SAFETY BACKFIRE VALIDATION REPORT", "V3.2_BACKFIRE_REAL_WORLD_REPORT.md"),
    ("PART XXI: COMPUTATIONAL PERFORMANCE & LATENCY PROFILING", "V3.2_PERFORMANCE_REPORT.md"),
    ("PART XXII: LONG-DURATION STABILITY & RESOURCE LEAKAGE AUDIT", "V3.2_LONG_DURATION_STABILITY.md"),
    ("PART XXIII: MASTER DEFECT REGISTRY (FAIL-01 TO FAIL-55)", "V3.2_FAILURE_REGISTRY.md"),
    ("PART XXIV: BASELINE VS IMPROVED: ARCHITECTURAL & EMPIRICAL DELTA", "V3.2_BASELINE_VS_IMPROVED.md"),
]

def build_master_report():
    lines = []
    lines.append("# SAFETY BACKFIRE AI — V3.2 MASTER COMPREHENSIVE VALIDATION DOSSIER")
    lines.append("")
    lines.append("> **Release Version:** V3.2 — Real-World Warehouse Validation, Event Validation & Safety Backfire Red Team  ")
    lines.append("> **Classification:** Engineering Release Dossier & Empirical Safety Validation Record  ")
    lines.append("> **Date:** September 2026  ")
    lines.append("> **Status:** VALIDATED WITHIN TESTED ODD — APPROVED FOR BOUNDED OPERATIONAL PILOT  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")
    for i, (part_title, filename) in enumerate(SECTIONS_ORDER, 1):
        lines.append(f"{i}. [{part_title}](#{part_title.lower().replace(' ', '-').replace(':', '').replace('—', '').replace('&', '').replace('(', '').replace(')', '')})")
    lines.append("")
    lines.append("---")
    lines.append("")

    for part_title, filename in SECTIONS_ORDER:
        file_path = REPORTS_DIR / filename
        if not file_path.exists():
            print(f"Warning: {filename} does not exist!")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Demote top level header
        content_lines = content.splitlines()
        adjusted_lines = []
        for line in content_lines:
            if line.startswith("# "):
                # Skip original title as we supply part_title
                continue
            elif line.startswith("## "):
                adjusted_lines.append("### " + line[3:])
            elif line.startswith("### "):
                adjusted_lines.append("#### " + line[4:])
            elif line.startswith("#### "):
                adjusted_lines.append("##### " + line[5:])
            else:
                adjusted_lines.append(line)

        lines.append(f"## {part_title}")
        lines.append("")
        lines.append(f"*Source Reference: [`{filename}`](file://{file_path})*")
        lines.append("")
        lines.extend(adjusted_lines)
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(MASTER_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Successfully compiled master report to {MASTER_REPORT_FILE}")
    print(f"Total size: {os.path.getsize(MASTER_REPORT_FILE):,} bytes")

if __name__ == "__main__":
    build_master_report()
