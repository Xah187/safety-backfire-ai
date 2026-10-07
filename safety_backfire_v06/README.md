# Safety Backfire AI — V0.6 Failure Gallery

Purpose:
Turn the V0.5 tracking output into a structured error-analysis set before any new training.

## What this does

1. Reads the V0.5 `tracking_events.csv`.
2. Groups detections into tracks.
3. Ranks long forklift tracks with low displacement as **possible persistent false positives**.
4. Saves representative crops (first/middle/last/peak-confidence).
5. Saves person-track representatives for continuity review.
6. Creates `annotation_review.csv` with a blank `human_label` column.
7. Produces `failure_gallery_report.json`.

Important:
- The rankings are NOT ground truth.
- A stationary forklift can be real.
- A short person track can be correct or a miss.
- `test.mp4` remains a test/stress artifact; do not train on it.

## Run

```bash
python tools/analyze_v05.py
```

Then inspect:

```text
failure_gallery/
├── forklift_ranked/
├── person_tracks/
├── annotation_review.csv
├── track_stats.json
└── failure_gallery_report.json
```

For the next dataset iteration, manually label candidate crops using:
- `true_forklift`
- `true_person`
- `background`
- `uncertain`

Only `true_forklift`/`true_person` become positive examples.
`background` becomes a hard negative.
`uncertain` stays out of training.

## Next step

Use footage from a DIFFERENT but visually similar warehouse/CCTV source for new training images when possible. Do not copy the final stress-test video into training.
