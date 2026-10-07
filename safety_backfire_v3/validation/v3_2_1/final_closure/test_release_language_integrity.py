"""
test_release_language_integrity.py
Automated release language linter for Safety Backfire AI V3.2.1 (Issue 19 & Issue E).
Audits Markdown and JSON release artifacts for prohibited overclaiming terminology.
Distinguishes active claims from historical quotes or retracted claim audits.
"""

import sys
import re
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

# Forbidden terms when used as ACTIVE assertions
FORBIDDEN_PATTERNS = [
    r"\bmathematical\s+guarantee\b",
    r"\bguaranteed\s+safety\b",
    r"\bzero\s+failure\s+probability\b",
    r"\buniversal\s+accuracy\b",
    r"\b100%\s+population\s+accuracy\b",
    r"\bformally\s+certified\s+safe\b",
    r"\bformally\s+certified\b",
    r"\bcommercially\s+certified\b",
    r"\bproduction\s+certified\b",
    r"\buniversally\s+validated\b",
    r"\buniversally\s+safe\b",
    r"\bguaranteed\s+safety\s+coverage\b"
]

EXEMPT_LINE_MARKERS = [
    "RETRACTED",
    "HISTORICAL",
    "PREVIOUS CLAIM",
    "ORIGINAL CLAIM",
    "PROHIBITED_TERMS",
    "PROHIBITED TERMS",
    "DISALLOWED",
    "TABLE OF RETRACTED",
    "QUOTED",
    "IN V3.2"
]

def is_line_exempt(line: str) -> bool:
    """Check if the line is part of a table of retracted/prohibited phrases or historical quotation."""
    stripped = line.strip()
    
    # Markdown table row (starts and ends with pipe, or contains multiple pipes)
    if stripped.startswith("|") or stripped.count("|") >= 2:
        return True
        
    # JSON list / property inside prohibited_terms or audit notes
    if '"prohibited_terms"' in line or '"prohibited_actions"' in line or '"mandatory_reporting_terminology"' in line:
        return True
    
    # If line is in quotation marks citing historical text or in JSON list
    if stripped.startswith('"') and (stripped.endswith('",') or stripped.endswith('"') or stripped.endswith('"],')):
        return True
        
    # Check marker keywords
    upper_line = line.upper()
    for marker in EXEMPT_LINE_MARKERS:
        if marker in upper_line:
            return True
            
    # Check if the sentence explicitly discusses, negates, or repudiates the term
    stripped_lower = stripped.lower()
    if any(neg in stripped_lower for neg in [
        "not a", "is not a", "nor a", "not an", "cannot provide", "never",
        "prohibit", "removed from", "unsupported terms", "disallowed", "retracted"
    ]):
        return True
    if "described" in stripped_lower and "as a" in stripped_lower:
        return True
            
    return False

def lint_file(file_path: Path):
    violations = []
    if not file_path.exists():
        return violations
        
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    
    in_code_block = False
    code_block_is_audit = False
    
    for idx, line in enumerate(lines):
        stripped = line.strip()
        
        # Check code block fences
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_block_is_audit = False
            else:
                in_code_block = False
                code_block_is_audit = False
            continue
            
        if in_code_block:
            # If code block mentions prohibited or overclaim or comparison, mark as audit block
            upper = stripped.upper()
            if any(m in upper for m in ["PROHIBITED", "OVERCLAIM", "REPLACEMENT", "RETRACTED", "EPISTEMIC"]):
                code_block_is_audit = True
            if code_block_is_audit:
                continue
                
        if is_line_exempt(line):
            continue
            
        for pattern in FORBIDDEN_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                violations.append({
                    "file": str(file_path.relative_to(WORKSPACE_ROOT)),
                    "line_number": idx + 1,
                    "matched_term": match.group(0),
                    "line_content": line.strip()
                })
    return violations

def run_lint():
    target_dirs = [
        WORKSPACE_ROOT / "outputs/v3_2_1/final_closure",
        WORKSPACE_ROOT / "reports/v3_2_1"
    ]
    
    all_violations = []
    for d in target_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.is_file() and f.suffix in [".md", ".json"]:
                # skip baseline manifest and backup dirs
                if "baseline" in f.name or "frozen" in f.name or "v3_2_original" in str(f):
                    continue
                violations = lint_file(f)
                all_violations.extend(violations)
                
    return all_violations

def main():
    print("=" * 80)
    print("   SAFETY BACKFIRE AI — RELEASE LANGUAGE INTEGRITY LINTER   ")
    print("=" * 80)
    
    violations = run_lint()
    if violations:
        print(f"[FAIL] Found {len(violations)} release language violation(s) in active text:")
        for v in violations:
            print(f"  - {v['file']}:{v['line_number']} [{v['matched_term']}]: \"{v['line_content']}\"")
        sys.exit(1)
    else:
        print("[PASS] Zero prohibited overclaims found in active release text.")
        sys.exit(0)

if __name__ == "__main__":
    main()
