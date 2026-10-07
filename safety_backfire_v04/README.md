# Safety Backfire AI — V0.4 Dataset Engineering

## Objective
Fix the V0.3 CCTV domain-shift failure by adding CCTV-like annotated examples and hard negatives, **without training on the golden stress-test video** (`test.mp4`).

## Golden rule
`test.mp4` is a held-out stress test. Do NOT copy its frames into `stress_train/` or the V0.4 training dataset.

Use other warehouse/CCTV videos for training hard negatives and annotations. The included extracted frames from `test.mp4` are for visual inspection only.

## Pipeline
1. Put the V0.3/base YOLO dataset at `data/base_yolo/` (must contain `images/{train,valid,test}` and `labels/{train,valid,test}`).
2. Put **other** CCTV videos under `data/source_videos/`.
3. Run `tools/extract_frames.py` to sample diverse frames from training-source videos.
4. Run `tools/mine_hard_negatives.py` with the V0.3 `best.pt`. It saves frames where V0.3 predicts forklift/person and a CSV manifest. Manually inspect these; false forklift predictions become hard negatives.
5. Annotate the selected CCTV frames with only two classes:
   - `forklift`
   - `person`
   Empty-label images are valid hard negatives.
6. Place annotated images + YOLO `.txt` labels in `data/stress_train/images/` and `data/stress_train/labels/`.
7. Run `tools/audit_v04.py`.
8. Run `tools/build_v04.py` to create a leakage-safe merged dataset.
9. Run `train_v04.py`.
10. Evaluate V0.4 on the untouched `test.mp4` using `test_video_v04.py`.

## Annotation rules
- Tight boxes around the visible object.
- If a forklift is partially occluded but identifiable, annotate the visible object extent consistently with your annotation tool.
- Annotate every visible person in selected frames, not only the obvious one.
- Do not label boxes, pallets, shelves, carts, or machinery as forklift.
- If a frame contains no forklift/person, keep its label file empty. This is a hard negative.

## Recommended V0.4 composition
Start with roughly:
- 60–70% original dataset
- 20–30% CCTV-like annotated images
- 10–20% hard-negative images

Do not artificially force these percentages if the available data differs; the audit report should drive the decision.

## Mac M5 24GB
Training is configured for Apple Silicon MPS and a conservative batch size. If MPS memory is tight, reduce `batch` from 8 to 4.
