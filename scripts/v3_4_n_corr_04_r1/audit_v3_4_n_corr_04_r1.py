#!/usr/bin/env python3
"""
V3.4-N-CORR-04-R1 — Comprehensive Persistence Characterization Reconciliation Audit
Milestone: V3.4-N-CORR-04-R1
Location: scripts/v3_4_n_corr_04_r1/audit_v3_4_n_corr_04_r1.py

Validates all 12 reconciliation criteria:
1. Invariants and production code immutability
2. Timing model timestamp semantics and arithmetic correction
3. Motor current decay constants reconciliation
4. Sliding RMS window latency and discrete persistence semantics
5. Measurement instrument chain audit (TCP303/TCPA300)
6. GUM uncertainty budget recomputation (RSS = 0.04520 A)
7. Guarded threshold derivation (0.410 A RMS)
8. Sampled persistence decision rule & purged claims
9. Trial evidence manifest and missing artifact verification
10. Statistical metrics separation
11. Oscilloscope channel allocation & controller identity
12. Release blockers and final governance status
"""

import sys
import os

# Delegate execution to the authoritative output file
AUDIT_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "v3_4_n_corr_04_r1", "audit_v3_4_n_corr_04_r1.py"))

if __name__ == "__main__":
    if not os.path.isfile(AUDIT_SCRIPT):
        print(f"[FATAL] Authoritative audit script not found at {AUDIT_SCRIPT}")
        sys.exit(1)
    
    # Execute the audit script
    with open(AUDIT_SCRIPT, "r") as f:
        code = compile(f.read(), AUDIT_SCRIPT, "exec")
        exec(code, {"__name__": "__main__", "__file__": AUDIT_SCRIPT})
