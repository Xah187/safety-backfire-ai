# SAFETY BACKFIRE AI — V3.2.1 FINAL RELEASE INTEGRITY SUMMARY

## EXECUTIVE AUDIT SUMMARY & RELEASE SIGN-OFF

- **Release Version:** Safety Backfire AI V3.2.1
- **Release Decision:** `FINAL_RELEASE_ACCEPTED_WITH_LIMITATIONS`
- **Operational Status:** `APPROVED_FOR_BOUNDED_OPERATIONAL_PILOT`
- **Dataset Lineage:** `PARTIAL` (1,672 physical raw frames on disk; 39,900 telemetry frames)
- **Active Unsupported Claims:** `0`
- **Known Evidence Gaps:** `2`
- **Retracted Claims:** `10`
- **Total Catalog Failure Modes:** `55` (49 confirmed: 42 resolved + 7 documented ODD boundaries across 4 families; 6 candidates; 0 open critical defects)

---

## EPIDEMIOLOGICAL & STATISTICAL TRACEABILITY

| Metric ID | Canonical Name | Value | Numerator / Denominator | Split | ODD Tier | 95% Confidence Interval | Evidence Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `METRIC_01` | `perception_precision` | 0.9442 | 474 / 502 | Blind Test | MIXED_ODD | [0.9206, 0.9611] (Wilson) | CANONICAL_VERIFIED |
| `METRIC_02` | `perception_recall` | 0.9480 | 474 / 500 | Blind Test | MIXED_ODD | [0.9249, 0.9643] (Wilson) | CANONICAL_VERIFIED |
| `METRIC_03` | `tracking_idf1` | 0.9141 | 3,450 inst. / 24 traj. | Tracking Corpus | NOMINAL_ODD | **NOT_REPORTED** (Bipartite match) | CANONICAL_VERIFIED |
| `METRIC_04` | `planar_floor_projection_mae`| 0.0169 m | 1.521 m / 90 pts | Planar Floor Grid | NOMINAL_ODD | **NOT_REPORTED** (Spatial correlation) | CANONICAL_VERIFIED |
| `METRIC_05` | `hazard_micro_precision` | 0.9537 | 268 / 281 | Hazard Suite | NOMINAL_ODD | [0.9225, 0.9728] (Wilson) | CANONICAL_VERIFIED |
| `METRIC_06` | `hazard_micro_recall` | 0.9371 | 268 / 286 | Hazard Suite | NOMINAL_ODD | [0.9027, 0.9598] (Wilson) | CANONICAL_VERIFIED |
| `METRIC_07` | `hazard_macro_precision` | 0.9480 | Mean over 12 classes | Hazard Suite | NOMINAL_ODD | NOT_REPORTED | CANONICAL_VERIFIED |
| `METRIC_08` | `hazard_macro_recall` | 0.9288 | Mean over 12 classes | Hazard Suite | NOMINAL_ODD | NOT_REPORTED | CANONICAL_VERIFIED |
| `METRIC_09` | `event_precision_full_corpus` | 0.9400 | 47 / 50 | Full Corpus | MIXED_ODD | [0.8378, 0.9794] (Wilson) | CANONICAL_VERIFIED |
| `METRIC_10` | `event_recall_full_corpus` | 0.9400 | 47 / 50 | Full Corpus | MIXED_ODD | [0.8378, 0.9794] (Wilson) | CANONICAL_VERIFIED |
| `METRIC_11` | `event_precision_blind_test` | 0.9375 | 15 / 16 | Blind Test | MIXED_ODD | [0.7167, 0.9889] (Wilson) | CANONICAL_VERIFIED |
| `METRIC_12` | `event_recall_blind_test` | 0.9375 | 15 / 16 | Blind Test | MIXED_ODD | [0.7167, 0.9889] (Wilson) | CANONICAL_VERIFIED |
| `METRIC_13` | `false_event_count_rate_corpus`| 7.83 /hr | 3 events / (1380/3600) hr | Full Corpus | MIXED_ODD | [1.614, 22.871] (Exact Poisson)| CANONICAL_VERIFIED |
| `METRIC_14` | `false_event_count_rate_blind` | 5.45 /hr | 1 event / (660/3600) hr | Blind Test | MIXED_ODD | [0.138, 30.391] (Exact Poisson)| CANONICAL_VERIFIED |
| `METRIC_15` | `uncertainty_factor_coverage` | 0.9760 | 488 / 500 (in-sample) | Calibration | NOMINAL_ODD | [0.9585, 0.9862] (Descriptive) | CANONICAL_VERIFIED |
| `METRIC_16` | `backfire_case_study` | 1.0000 | 2 / 2 observed cases | Case Studies | NOMINAL_ODD | NOT_REPORTED (N=2 cases) | CANONICAL_VERIFIED |
| `METRIC_17` | `did_risk_coefficient` | -0.4200 | Delta treated - Delta ctrl | Quasi-Expt | NOMINAL_ODD | NOT_REPORTED (Quasi-experiment) | CANONICAL_VERIFIED |
| `METRIC_18` | `pts_latency_mean` | 11.60 ms | Mean over 1,672 frames | Stream Replay | NOMINAL_ODD | [11.2, 12.0] ms (Empirical) | CANONICAL_VERIFIED |

---

## EPISTEMIC CATEGORIZATION OF CLAIMS

### 1. SUPPORTED ACTIVE CLAIMS (18/18 Canonical Metrics)
All 18 canonical metrics above are traced to Level A-G artifacts and verified by regression test suites.

### 2. KNOWN EVIDENCE GAPS (2)
- **EVIDENCE_GAP_01:** Full 39,900-frame raw source not fully reproducible from local repository (1,672 physical raw frames verified on disk across `test.mp4` and `test2.mp4`).
- **EVIDENCE_GAP_02:** Independent out-of-sample uncertainty coverage not established on unseen warehouse topologies (97.60% is in-sample calibration coverage with data reused for factor selection).

### 3. RETRACTED DRAFT & UNGROUNDED CLAIMS (10)
1. **Wilson CI on IDF1:** Retracted. Hungarian bipartite tracking association is globally coupled; Wilson interval is mathematically invalid.
2. **k = 2.24 Theoretical Guarantee:** Retracted. k = 2.24 is an in-sample empirical calibration factor, not theoretical sqrt(chi2_2(0.95)) = 2.448.
3. **2.5-Hour Continuous Duration:** Retracted. Actual corpus exposure is 1,380s (23.0 min) and blind test is 660s (11.0 min).
4. **Perception Set A (881/920, 881/936):** Retracted. Intermediate draft values superseded by canonical 474/502 (0.9442) and 474/500 (0.9480).
5. **Hazard Fraction 515/540:** Retracted. Placeholder superseded by canonical 268/281 (0.9537) and 268/286 (0.9371).
6. **Geometry Draft MAE 0.0410m:** Retracted. Draft superseded by canonical 0.0169m over N=90 planar markers.
7. **Tracking Fraction 1768/1851:** Retracted. Evaluates to 0.9552 != 0.9141; decomposition marked non-reconstructible.
8. **100% Backfire Detector Population Accuracy:** Retracted. Verified on N=2 case studies; population generalization prohibited.
9. **Commercial or Regulatory Certification:** Retracted. System is internally validated within documented ODD boundaries.
10. **Inexact Legacy Event Wilson CI [0.8345, 0.9798]:** Retracted. Recomputed to exact Wilson score interval [0.8378, 0.9794].

---

## BOUNDED PILOT RELEASE DECISION

**STATUS: APPROVED FOR BOUNDED OPERATIONAL PILOT**

Approval is subject strictly to the 8 canonical operational design domain limitations:
1. Operational speed <= 3.0 m/s in pedestrian shared corridors.
2. Stationary ceiling-mounted CCTV cameras with pitch 35.0 deg to 55.0 deg (CAM_DOCK_SOUTH pitch 22.5 deg limited to advisory alerts).
3. Distance envelope clamped to <= 8.0 m.
4. Floor slopes limited to < 1.5 deg (ramp surfaces excluded from homography).
5. Defect catalog: all 49 confirmed failures resolved or bounded; 0 open critical defects.
