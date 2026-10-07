"""
test_audit_v3_2_1_suite.py
Master Test Suite Runner for V3.2.1 Validation Integrity & Statistical Reconciliation.
Executes all 12 audit tests synchronously and verifies full system consistency.
"""

import sys
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

# Import all 12 test modules
from safety_backfire_v3.validation.v3_2_1.test_dataset_duration_consistency import test_dataset_duration_consistency
from safety_backfire_v3.validation.v3_2_1.test_odd_consistency import test_odd_consistency
from safety_backfire_v3.validation.v3_2_1.test_hazard_metric_definitions import test_hazard_metric_definitions
from safety_backfire_v3.validation.v3_2_1.test_denominator_integrity import test_denominator_integrity
from safety_backfire_v3.validation.v3_2_1.test_uncertainty_lineage import test_uncertainty_lineage
from safety_backfire_v3.validation.v3_2_1.test_event_rate_statistics import test_event_rate_statistics
from safety_backfire_v3.validation.v3_2_1.test_claim_evidence_traceability import test_claim_evidence_traceability
from safety_backfire_v3.validation.v3_2_1.test_failure_registry_integrity import test_failure_registry_integrity
from safety_backfire_v3.validation.v3_2_1.test_backfire_case_lineage import test_backfire_case_lineage
from safety_backfire_v3.validation.v3_2_1.test_causality_evidence_integrity import test_causality_evidence_integrity
from safety_backfire_v3.validation.v3_2_1.test_long_duration_label_integrity import test_long_duration_label_integrity
from safety_backfire_v3.validation.v3_2_1.test_report_metric_consistency import test_report_metric_consistency

class TestV321AuditSuite(unittest.TestCase):

    def test_01_dataset_duration_consistency(self):
        test_dataset_duration_consistency()

    def test_02_odd_consistency(self):
        test_odd_consistency()

    def test_03_hazard_metric_definitions(self):
        test_hazard_metric_definitions()

    def test_04_denominator_integrity(self):
        test_denominator_integrity()

    def test_05_uncertainty_lineage(self):
        test_uncertainty_lineage()

    def test_06_event_rate_statistics(self):
        test_event_rate_statistics()

    def test_07_claim_evidence_traceability(self):
        test_claim_evidence_traceability()

    def test_08_failure_registry_integrity(self):
        test_failure_registry_integrity()

    def test_09_backfire_case_lineage(self):
        test_backfire_case_lineage()

    def test_10_causality_evidence_integrity(self):
        test_causality_evidence_integrity()

    def test_11_long_duration_label_integrity(self):
        test_long_duration_label_integrity()

    def test_12_report_metric_consistency(self):
        test_report_metric_consistency()

if __name__ == "__main__":
    print("=" * 80)
    print("   V3.2.1 VALIDATION INTEGRITY & STATISTICAL RECONCILIATION SUITE   ")
    print("=" * 80)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV321AuditSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("=" * 80)
        print("   [SUCCESS] V3.2.1 AUDIT SUITE 100% PASSED! ALL CLAIMS RECONCILED.   ")
        print("=" * 80)
        sys.exit(0)
    else:
        print("=" * 80)
        print("   [FAILURE] V3.2.1 AUDIT SUITE DETECTED UNRECONCILED CLAIMS.   ")
        print("=" * 80)
        sys.exit(1)
