# Safety Backfire AI — Detection Benchmark V0.2

This benchmark tests detection-only first. Tracking is intentionally disabled so we can separate detector quality from tracker failures.

## 1. Put files together

```text
safety_backfire_v02/
├── benchmark_detection.py
└── test.mp4
```

Copy your `test.mp4` into this folder.

## 2. Create environment on the MacBook Pro M5

Use Python 3.11 or 3.12 for the cleanest current PyTorch/Ultralytics setup.

```bash
cd ~/Projects/safety-backfire-ai
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch torchvision torchaudio
python -m pip install ultralytics opencv-python numpy pandas
```

Check Apple GPU support:

```bash
python - <<'PY'
import torch
print("PyTorch:", torch.__version__)
print("MPS built:", torch.backends.mps.is_built())
print("MPS available:", torch.backends.mps.is_available())
PY
```

PyTorch documents MPS support for Apple Silicon/macOS. Ultralytics documents `device="mps"`, `imgsz`, `conf`, and video prediction. 

## 3. Run benchmark

```bash
python benchmark_detection.py
```

It runs three configurations:

- A: YOLO26n, 640px, confidence 0.50
- B: YOLO26s, 960px, confidence 0.50
- C: YOLO26s, 1280px, confidence 0.35

Outputs are written to:

```text
runs/detection_benchmark/
```

## 4. Why these tests

A low confidence threshold can recover small/weak objects but also increases false positives. Larger image size can help small objects but costs more inference time. Therefore we compare quality and speed before adding tracking.

## 5. Next decision rule

Do not select the fastest run automatically.

Review the three annotated videos and record:

- false positives on static objects
- missed people
- missed forklifts
- intermittent detections
- duplicate detections
- small-object misses

Then choose the configuration with the best detection quality. Only after that do we benchmark ByteTrack vs BoT-SORT.
