"""
merge_v3_2_1_reports.py
Compiles all 14 individual V3.2.1 audit and reconciliation reports into a single
unified, master technical dossier: V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md
"""

import os
from pathlib import Path

REPORTS_DIR = Path("/Users/xah187/Projects/safety-backfire-ai/reports/v3_2_1")
MASTER_REPORT_FILE = REPORTS_DIR / "V3.2.1_MASTER_RECONCILED_AUDIT_REPORT.md"

SECTIONS = [
    ("PART I: EXECUTIVE CORE STATUS & AUDIT RELEASE SIGN-OFF", "V3.2.1_CORE_STATUS.md"),
    ("PART II: FINAL RELEASE AUDIT & MASTER RECONCILED METRIC TABLE", "V3.2.1_FINAL_RELEASE_AUDIT.md"),
    ("PART III: DATASET DURATION & CORPUS RECONCILIATION AUDIT", "V3.2.1_DATASET_RECONCILIATION.md"),
    ("PART IV: MASTER METRIC RECONCILIATION & DENOMINATOR AUDIT", "V3.2.1_METRIC_RECONCILIATION.md"),
    ("PART V: OPERATIONAL DESIGN DOMAIN (ODD) RECONCILIATION", "V3.2.1_ODD_RECONCILIATION.md"),
    ("PART VI: STATISTICAL TERMINOLOGY & FALSE CERTIFICATION AUDIT", "V3.2.1_STATISTICAL_TERMINOLOGY_AUDIT.md"),
    ("PART VII: EVENT-LEVEL METRIC AUDIT & POISSON RATE STATISTICS", "V3.2.1_EVENT_METRIC_AUDIT.md"),
    ("PART VIII: HAZARD METRIC AUDIT & CAPABILITY TAXONOMY", "V3.2.1_HAZARD_METRIC_AUDIT.md"),
    ("PART IX: UNCERTAINTY LINEAGE & STATISTICAL COVERAGE AUDIT", "V3.2.1_UNCERTAINTY_LINEAGE_AUDIT.md"),
    ("PART X: SAFETY BACKFIRE EMPIRICAL EVIDENCE AUDIT", "V3.2.1_BACKFIRE_EVIDENCE_AUDIT.md"),
    ("PART XI: CAUSALITY VS CORRELATION: DIFFERENCE-IN-DIFFERENCES AUDIT", "V3.2.1_CAUSALITY_AUDIT.md"),
    ("PART XII: MASTER FAILURE REGISTRY AUDIT & LINEAGE RECONCILIATION", "V3.2.1_FAILURE_REGISTRY_AUDIT.md"),
    ("PART XIII: CLAIM-TO-EVIDENCE TRACEABILITY MATRIX", "V3.2.1_CLAIM_EVIDENCE_TRACEABILITY.md"),
    ("PART XIV: SCIENTIFIC REPRODUCIBILITY & EXECUTION AUDIT", "V3.2.1_REPRODUCIBILITY_AUDIT.md"),
]

def build_master():
    lines = []
    lines.append("# SAFETY BACKFIRE AI — V3.2.1 MASTER RECONCILED AUDIT DOSSIER")
    lines.append("")
    lines.append("> **Release Version:** Safety Backfire AI V3.2.1  ")
    lines.append("> **Document Classification:** Official Engineering Audit, Statistical Reconciliation & Release Verification Record  ")
    lines.append("> **Audit Decision:** V3.2.1_RELEASE_ACCEPTED_WITH_CORRECTIONS  ")
    lines.append("> **Operational Status:** APPROVED FOR BOUNDED OPERATIONAL PILOT  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")
    for i, (title, filename) in enumerate(SECTIONS, 1):
        anchor = title.lower().replace(" ", "-").replace(":", "").replace("—", "").replace("&", "").replace("(", "").replace(")", "")
        lines.append(f"{i}. [{title}](#{anchor})")
    lines.append("")
    lines.append("---")
    lines.append("")

    for title, filename in SECTIONS:
        fp = REPORTS_DIR / filename
        if not fp.exists():
            print(f"Warning: {filename} missing!")
            continue

        with open(fp, "r", encoding="utf-8") as f:
            content = f.read().strip()

        content_lines = content.splitlines()
        adjusted = []
        for line in content_lines:
            if line.startswith("# "):
                continue
            elif line.startswith("## "):
                adjusted.append("### " + line[3:])
            elif line.startswith("### "):
                adjusted.append("#### " + line[4:])
            elif line.startswith("#### "):
                adjusted.append("##### " + line[5:])
            else:
                adjusted.append(line)

        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"*Source Reference: [`{filename}`](file://{fp})*")
        lines.append("")
        lines.extend(adjusted)
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(MASTER_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Successfully compiled V3.2.1 master audit report: {MASTER_REPORT_FILE}")
    print(f"Total size: {os.path.getsize(MASTER_REPORT_FILE):,} bytes")

if __name__ == "__main__":
    build_master()
