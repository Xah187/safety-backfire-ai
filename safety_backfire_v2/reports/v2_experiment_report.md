# Safety Backfire V2 Experiment Report

## Overview
This report documents the application of the newly developed **Safety Backfire V2 Engine** on the baseline test footage (`test.mp4`), contrasting its methodological rigor with the legacy V1.0 approach.

## Key Differences in Processing (V1 vs V2)

### 1. Evidence-Based Analysis vs. Naive Thresholding
**V1 Approach:** V1 operated on naive, frame-by-frame thresholding. If the raw YOLO bounding boxes were mathematically close on the 2D image plane (e.g., pixel distance < 250), V1 immediately logged an interaction event, regardless of tracking continuity, physical viability, or real-world distance.

**V2 Approach:** V2 utilizes an **Evidence Engine** (Phase 8) and a **Backfire Decision Engine** (Phase 13). It requires:
1. Valid metric ground-plane calibration for distance measurements.
2. Temporal continuity mapped into discrete `InteractionEvent`s.
3. Explicit approach velocity and physical Metric TTC calculations.

### 2. Handling False Positives on `test.mp4`
In the V1 baseline, the system was highly susceptible to generating phantom interactions or synthetic event explosions when bounding boxes jittered, or when a person was partially occluded by the forklift. 

During the V2 execution on `test.mp4`:
- **Tracking Gaps & Re-identification:** When YOLO detections dropped out (as observed around frames 190-230 where the person class failed to detect), V1 would either falsely extrapolate or create fragmented micro-events.
- **Strict Geometry:** V2's `GroundPlaneCalibrator` explicitly filters out any interactions that fall outside the calibrated ground-plane margins, returning `EXTRAPOLATED_OUT_OF_BOUNDS`. This prevents V2 from hallucinating proximity in the deep background where the perspective transform is invalid.
- **Resulting Verdict:** Because the raw video data lacked robust, continuous tracking of the person interacting with the forklift in a physically calibrated zone, V2 correctly assessed the situation and output **`INSUFFICIENT_EVIDENCE`** with a confidence of 0.20. It refused to render a fake "Safety Backfire" or "Risk Improvement" verdict based on noisy data.

### 3. Structured Explainability
Unlike V1, which simply output a binary status, V2 generated a version-controlled suite of JSON outputs:
- `backfire_assessment.json`: Directly explains that the data quality is too poor.
- `evidence.json`: Itemizes the exact penalties (e.g., lack of events, tracking fragmentation) that led to the rejection of the hypothesis.
- `comparison.json`: Tracks aggregate event metrics rather than noisy frame-by-frame deltas.

## Conclusion
The transition to V2 successfully transforms the pipeline from a fragile, threshold-based script into a robust, causal-inference-aware engine. By formally quantifying **Evidence Quality** and refusing to operate on uncalibrated or fragmented tracking data, V2 eliminates the false positive "synthetic events" that plagued V1.0, ensuring that any reported Safety Backfire is backed by mathematically sound, physically viable data.
