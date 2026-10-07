# Safety Backfire AI — V0.5 Tracking Stress Test

This version answers one question before any further training:

**Does the V0.4 detector + ByteTrack produce stable object identities over time?**

Previous V0.4 testing used `model.predict()`, so no tracking IDs could appear.

## Run

Place this folder inside the project containing:

runs/forklift_person_yolo26n_v04/weights/best.pt
test.mp4

Activate your venv and run:

```bash
python tracking_benchmark.py
```

Outputs:

```text
runs/v05_tracking_stress_test/
├── tracked.mp4
├── tracking_events.csv
└── tracking_summary.json
```

## What to inspect

1. Open `tracked.mp4`.
2. Check whether the same real person keeps the same ID.
3. Check whether the real forklift keeps the same ID.
4. Check whether false-positive forklifts receive long-lived IDs.
5. Check whether IDs disappear and reappear frequently.
6. Inspect `tracking_summary.json`.
7. Do not treat `id_switch_proxy_count` as a formal HOTA/ID-switch metric. It is only a diagnostic signal.

## Decision rule

- If detections are wrong and tracks are stable: fix the detector/data.
- If detections are mostly correct but tracks fragment: tune tracking.
- If both are poor: fix detector/data first; tracking is not the root cause.

## Hardware

Designed for MacBook Pro M5 / 24GB using MPS.
