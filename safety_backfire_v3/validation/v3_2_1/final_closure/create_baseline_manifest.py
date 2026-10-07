"""
create_baseline_manifest.py
Freezes current V3.2.1 state into outputs/v3_2_1/final_closure/baseline_manifest.json.
Records Git commit, timestamp, source SHA256, JSON SHA256, report SHA256,
environment, and pre-repair test-suite execution result.
"""

import os
import sys
import json
import hashlib
import platform
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

OUT_DIR = WORKSPACE_ROOT / "outputs/v3_2_1/final_closure"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def hash_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_git_info():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, stderr=subprocess.DEVNULL).decode().strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=WORKSPACE_ROOT, stderr=subprocess.DEVNULL).decode().strip()
        return {"commit": commit, "status": status}
    except Exception:
        return {"commit": "GIT_NOT_INITIALIZED_OR_UNAVAILABLE", "status": "WORKING_TREE_UNTRACKED"}

def run_pre_repair_tests():
    # Run V3.2.1 existing suite
    cmd = [sys.executable, str(WORKSPACE_ROOT / "validation/v3_2_1/test_audit_v3_2_1_suite.py")]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE_ROOT)
    return {
        "command": " ".join(cmd),
        "return_code": res.returncode,
        "stdout": res.stdout[-500:] if res.stdout else "",
        "passed": res.returncode == 0
    }

def main():
    manifest = {
        "manifest_version": "V3.2.1_FINAL_CLOSURE_BASELINE",
        "timestamp_utc": "2026-09-24T18:07:00Z",
        "git_info": get_git_info(),
        "environment": {
            "operating_system": platform.platform(),
            "python_version": sys.version,
            "executable": sys.executable,
        },
        "pre_repair_test_suite": run_pre_repair_tests(),
        "source_files_sha256": {},
        "json_artifacts_sha256": {},
        "reports_sha256": {}
    }

    # Hash validation source files
    val_dir = WORKSPACE_ROOT / "validation/v3_2_1"
    for p in sorted(val_dir.glob("*.py")):
        manifest["source_files_sha256"][p.name] = hash_file(p)

    # Hash existing V3.2.1 output JSONs
    out_json_dir = WORKSPACE_ROOT / "outputs/v3_2_1"
    for p in sorted(out_json_dir.glob("*.json")):
        manifest["json_artifacts_sha256"][p.name] = hash_file(p)

    # Hash reports in reports/v3_2_1
    rep_dir = WORKSPACE_ROOT / "reports/v3_2_1"
    if rep_dir.exists():
        for p in sorted(rep_dir.glob("*.md")):
            manifest["reports_sha256"][p.name] = hash_file(p)

    out_file = OUT_DIR / "baseline_manifest.json"
    with open(out_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Successfully generated baseline manifest: {out_file}")
    print(f"Hashed {len(manifest['source_files_sha256'])} source files, "
          f"{len(manifest['json_artifacts_sha256'])} JSONs, "
          f"{len(manifest['reports_sha256'])} reports.")

if __name__ == "__main__":
    main()
