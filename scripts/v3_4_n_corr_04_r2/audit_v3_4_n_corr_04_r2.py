#!/usr/bin/env python3
"""
V3.4-N-CORR-04-R2 — Runner Script
Location: scripts/v3_4_n_corr_04_r2/audit_v3_4_n_corr_04_r2.py
"""

import sys
import os

AUDIT_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "v3_4_n_corr_04_r2", "audit_v3_4_n_corr_04_r2.py"))

if __name__ == "__main__":
    if not os.path.isfile(AUDIT_SCRIPT):
        print(f"[FATAL] Authoritative audit script not found at {AUDIT_SCRIPT}")
        sys.exit(1)
    
    with open(AUDIT_SCRIPT, "r") as f:
        code = compile(f.read(), AUDIT_SCRIPT, "exec")
        exec(code, {"__name__": "__main__", "__file__": AUDIT_SCRIPT})
