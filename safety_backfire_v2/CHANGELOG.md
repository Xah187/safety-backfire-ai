# Safety Backfire V2 Changelog

## [2.0.0-phase18] - 2026-09-20
### Added
- Authored final Quality Report (`reports/v2_experiment_report.md`) detailing the transition from V1's naive thresholding to V2's evidence-based architecture.

## [2.0.0-phase17] - 2026-09-20
### Added
- Master execution script (`run_v2_experiment.py`) running the entire V2 pipeline on baseline video data.
- Generates fully versioned JSON outputs into `outputs/` folder.

## [2.0.0-phase16] - 2026-09-20
### Added
- Automated master test suite (`test_all.py`) validating the entire analytical pipeline from geometry mapping to explainability rendering.

## [2.0.0-phase15] - 2026-09-20
### Added
- `core/output_schema.py` to enforce a unified JSON output schema across the pipeline.
- Schema explicitly includes `schema_version` and `engine_version` to prevent random ad-hoc formatting.

## [2.0.0-phase14] - 2026-09-20
### Added
- `core/explainability.py` to map complex verdicts back to their constituent data points.
- Creates traceable JSON mapping `Conclusion -> Evidence -> Event -> Frames`.

## [2.0.0-phase13] - 2026-09-20
### Added
- `core/decision.py` to synthesize all metrics (evidence, comparison, redistribution, counterfactual) into a single decision engine.
- Prevents rendering a verdict on insufficient evidence.

## [2.0.0-phase12] - 2026-09-20
### Added
- `core/counterfactual.py` for rate-based estimation of expected vs observed risk.
- Explicit labeling (`CONSISTENT_WITH_BACKFIRE`, `NO_STRONG_SIGNAL`) avoiding absolute causal language.

## [2.0.0-phase11] - 2026-09-20
### Added
- `core/intervention.py` to formally link Before and After segments to a specific physical or policy intervention.
- `InterventionExperiment` class explicitly declaring that temporal differences alone do not equal causality.

## [2.0.0-phase10] - 2026-09-20
### Added
- `core/redistribution.py` to analyze spatial shifts in risk.
- Explicit logic to detect if risk decreased in one area but increased in another, isolating the "displaced risk" phenomenon.

## [2.0.0-phase9] - 2026-09-20
### Added
- `core/comparison.py` to compare Event-level and Risk-level metrics before and after interventions.
- Calculates absolute change, percentage change, and explicit direction (INCREASE, DECREASE, NO_CHANGE).
- Removes naive frame-by-frame comparison in favor of aggregated event comparison.

## [2.0.0-phase8] - 2026-09-20
### Added
- `core/evidence.py` to evaluate the quality of evidence supporting a verdict.
- Quantifies penalties for track fragmentation, missing metric calibrations, and lack of observations.
- Assigns an explicit `evidence_level` (`HIGH`, `MODERATE`, `LOW`, `INSUFFICIENT`).

## [2.0.0-phase7] - 2026-09-20
### Added
- `core/severity.py` to calculate a composite `severity_score` (0-100) combining distance, speed, duration, and zone.
- Added categorical severity levels (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
- Semantic multiplier applied to severity (e.g., crossing/near-miss boost).

## [2.0.0-phase6] - 2026-09-20
### Added
- `core/semantics.py` to classify interactions based on spatial-temporal patterns rather than just static distance.
- Behavioral categories (`POTENTIAL_NEAR_MISS`, `CROSSING`, `STATIONARY_PROXIMITY`, `APPROACHING`, `DIVERGING`).

## [2.0.0-phase5] - 2026-09-20
### Added
- `core/trajectory.py` for tracking historical points in world coordinates.
- Spatial smoothing for velocity over a temporal window to eliminate jitter.
- Extraction of advanced trajectory metrics: displacement, length, peak velocity, and zone transitions.

## [2.0.0-phase4] - 2026-09-19
### Added
- `core/kinematics.py` for physical world velocity and metric TTC computation.
- Explicit TTC statuses (`VALID`, `NO_APPROACH`, `UNDEFINED`) to avoid hardcoded dummy values.
- Physics-based approach velocity calculation via relative vector dot products.

## [2.0.0-phase3] - 2026-09-19
### Added
- `core/geometry.py` with rigorous ground-plane constraints.
- `compute_metric_distance` function that explicitly returns calibration status and rejects extrapolation outside the homography region.
- Test suite validating geometry bounding rules.

## [2.0.0-phase2] - 2026-09-19
### Added
- `RiskEngine` to compute a multi-factor `risk_exposure_score` using spatial and temporal factors.
- YAML configuration `risk_weights.yaml` for safety heuristics to avoid hardcoding in Python.
- Test suite for `RiskEngine` verifying higher risk scores for dangerous interactions.

## [2.0.0-phase1] - 2026-09-19
### Added
- `InteractionEvent` class to group contiguous frames of person-forklift interactions into discrete events.
- `EventEngine` class that manages event lifecycles (NEW -> ACTIVE -> ENDED) with a configurable `max_gap_frames` to handle temporary tracking losses.
- Test suite for `EventEngine` to validate gap bridging and event culmination.
### Fixed
- Fixed bug where `process_frame_interactions` failed to split events when the gap limit was exceeded prior to updating active frames.
