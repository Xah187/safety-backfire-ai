# Safety Backfire AI — V0.8 Spatial & Interaction Risk Engine

## Objective
Establish the **pre-intervention spatial risk baseline** using the production-stabilized V0.7 CCTV detector.
Transforms raw 2D bounding boxes into ground-projected trajectories, dynamic safety halos, and proximity interaction events.

## Architecture
```text
safety_backfire_v08/
├── core/
│   ├── geometry.py             # Ground-contact footprints and metric distance
│   ├── trajectory.py           # Multi-frame smoothing, velocity & heading
│   ├── safety_zones.py         # Dynamic safety halos (Caution/Danger)
│   └── interaction_engine.py   # Pairwise proximity, TTC, and near-miss detection
├── visualization/
│   └── risk_overlay.py         # Floor halos, proximity lines, and HUD telemetry
├── runs/risk_benchmark/        # Output video, interaction events CSV, baseline summary
├── run_v08_pipeline.py         # Complete end-to-end execution pipeline
└── test.mp4                    # Untouched evaluation video
```

## How It Works
1. **Footprint Anchoring**: Bounding boxes are grounded at $[(x_1+x_2)/2, y_2]$ to prevent 2D perspective height distortions.
2. **Kinematic Smoothing**: Rolling window exponential averaging eliminates detection jitter and derives stable velocity vectors.
3. **Dynamic Halos**: Forklift safety zones elongate in the direction of motion proportionally to speed ($v \times \Delta t_{\text{stopping}}$).
4. **Interaction Engine**: Pairwise distance and approach rates identify near-miss incidents and log the un-intervened baseline risk.

## Run
```bash
cd safety_backfire_v08
python run_v08_pipeline.py
```
