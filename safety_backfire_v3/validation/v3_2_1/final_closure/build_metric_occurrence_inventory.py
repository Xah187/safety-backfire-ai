"""
build_metric_occurrence_inventory.py
Scans repository for key numerical values and metric terms to catalog every occurrence
with forensic classification (CANONICAL, DERIVED, LEGACY, RETRACTED, CONFLICTING, UNSUPPORTED).
Outputs: outputs/v3_2_1/final_closure/metric_occurrence_inventory.json
"""

import sys
import re
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

OUT_DIR = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_VALUES = [
    "0.9442", "0.9480", "0.9576", "0.9412", "0.9141", "1768", "1851",
    "3154", "3450", "1672", "0.0169", "0.0410", "1.521", "90", "100",
    "0.9537", "268", "281", "515", "540", "0.9371", "0.9288", "0.9400",
    "0.9375", "7.83", "5.45", "30.360", "30.388", "2.24", "2.448",
    "97.60", "488", "500", "23.0", "39,900", "1,922", "1,672", "64.05"
]

TARGET_METRIC_NAMES = [
    "precision", "recall", "F1", "IDF1", "IDTP", "IDFP", "IDFN",
    "geometry MAE", "RMSE", "uncertainty coverage", "false event rate",
    "missed event rate", "hazard precision", "hazard recall",
    "macro precision", "micro precision", "event precision", "event recall"
]

def classify_occurrence(val, file_str, line):
    line_lower = line.lower()
    file_lower = file_str.lower()
    
    # Retracted or conflicting numbers
    if val in ["0.9576", "0.9412", "881", "920", "936"] and "perception" in line_lower:
        return "LEGACY_RETRACTED"
    if val == "0.0410":
        return "CONFLICTING_LEGACY"
    if val in ["515", "540"] and "hazard" in line_lower:
        return "RETRACTED_UNSUPPORTED"
    if val == "30.360":
        return "CONFLICTING_ROUNDING"
    if val in ["1768", "1851"] and "idf1" in line_lower:
        return "RETRACTED_FORMULATION"
    if val == "2.5" and "hour" in line_lower:
        return "RETRACTED"
        
    # Canonical numbers
    if val == "0.9442" or val == "0.9480" and "perception" in line_lower:
        return "CANONICAL"
    if val == "0.9141" and "idf1" in line_lower:
        return "CANONICAL"
    if val in ["0.0169", "1.521", "90", "100"] and "geometry" in line_lower or "planar" in line_lower:
        return "CANONICAL"
    if val in ["0.9537", "268", "281", "286", "0.9371"] and "hazard" in line_lower:
        return "CANONICAL"
    if val in ["0.9400", "47", "3", "50"] and "event" in line_lower:
        return "CANONICAL"
    if val in ["7.83", "5.45", "30.388", "1.614", "22.868", "0.138"] and ("rate" in line_lower or "event" in line_lower):
        return "CANONICAL"
    if val in ["2.24", "488", "500", "97.60"] and "uncertainty" in line_lower:
        return "CANONICAL"
    if val in ["1672", "64.05"] and ("frame" in line_lower or "sec" in line_lower):
        return "CANONICAL"
    if val in ["23.0", "39,900"] and ("corpus" in line_lower or "frame" in line_lower):
        return "CANONICAL_WITH_LIMITATION"
        
    if "legacy" in file_lower or "frozen" in file_lower:
        return "LEGACY"
        
    return "DERIVED"

def scan_repository():
    occurrences = []
    
    # We scan outputs/, reports/, and validation/
    scan_dirs = [
        WORKSPACE_ROOT / "outputs",
        WORKSPACE_ROOT / "reports",
        WORKSPACE_ROOT / "validation"
    ]
    
    for s_dir in scan_dirs:
        if not s_dir.exists():
            continue
        for p in s_dir.rglob("*"):
            if p.is_file() and p.suffix in [".json", ".md", ".py", ".csv", ".txt"]:
                # skip git or cache
                if ".git" in str(p) or "__pycache__" in str(p):
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                
                lines = text.splitlines()
                rel_p = str(p.relative_to(WORKSPACE_ROOT))
                
                for idx, line in enumerate(lines):
                    for val in TARGET_VALUES:
                        if val in line:
                            cls = classify_occurrence(val, rel_p, line)
                            occurrences.append({
                                "target": val,
                                "type": "NUMERICAL_VALUE",
                                "file": rel_p,
                                "line_number": idx + 1,
                                "classification": cls,
                                "snippet": line.strip()[:160]
                            })
                            
                    for name in TARGET_METRIC_NAMES:
                        if re.search(r'\b' + re.escape(name) + r'\b', line, re.IGNORECASE):
                            occurrences.append({
                                "target": name,
                                "type": "METRIC_NAME",
                                "file": rel_p,
                                "line_number": idx + 1,
                                "classification": "REFERENCED",
                                "snippet": line.strip()[:160]
                            })
                            
    return occurrences

def main():
    occurrences = scan_repository()
    
    # Group by target
    target_summary = {}
    for o in occurrences:
        t = o["target"]
        if t not in target_summary:
            target_summary[t] = {
                "total_occurrences": 0,
                "classifications": {}
            }
        target_summary[t]["total_occurrences"] += 1
        c = o["classification"]
        target_summary[t]["classifications"][c] = target_summary[t]["classifications"].get(c, 0) + 1

    inventory = {
        "inventory_version": "V3.2.1_METRIC_OCCURRENCE_INVENTORY",
        "timestamp_utc": "2026-09-24T18:25:00Z",
        "total_occurrences_found": len(occurrences),
        "target_summary": target_summary,
        "sample_occurrences": occurrences[:100]
    }
    
    out_file = OUT_DIR / "metric_occurrence_inventory.json"
    with open(out_file, "w") as f:
        json.dump(inventory, f, indent=2)
        
    print(f"Generated metric occurrence inventory: {out_file}")
    print(f"Total cataloged occurrences: {len(occurrences)}")

if __name__ == "__main__":
    main()
