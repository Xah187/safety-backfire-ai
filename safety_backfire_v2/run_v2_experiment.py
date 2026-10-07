import sys
from pathlib import Path
import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from core.event_engine import EventEngine
from core.geometry import GroundPlaneCalibrator, compute_metric_distance, load_default_calibrator
from core.risk_engine import RiskEngine
from core.kinematics import calculate_world_velocity, compute_metric_ttc
from core.trajectory import TrajectoryEngine
from core.comparison import ComparisonEngine
from core.redistribution import RiskRedistributionEngine
from core.severity import SeverityEngine
from core.semantics import SemanticClassifier
from core.evidence import EvidenceEngine
from core.counterfactual import CounterfactualEngine
from core.intervention import Intervention, InterventionExperiment
from core.decision import DecisionEngine
from core.explainability import ExplainabilityLayer
from core.output_schema import OutputManager
from core.operator_relation import OperatorVehicleRelationEngine

def run_experiment():
    print("=== Starting Safety Backfire V2 Experiment ===")
    
    # 1. Setup
    model_path = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
    video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "safety_backfire_v08/test.mp4"
    output_dir = ROOT / "outputs"
    
    if not model_path.exists() or not video_path.exists():
        print("Model or video not found!")
        return
        
    model = YOLO(str(model_path))
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30.0
    cap.release()
    
    # 2. Initialize Engines
    calibrator = load_default_calibrator()
    trajectory_engine = TrajectoryEngine()
    event_engine = EventEngine()
    relation_engine = OperatorVehicleRelationEngine()
    out_manager = OutputManager(str(output_dir))
    
    # Segment definitions (Split the video in half for the experiment)
    split_frame = total_frames // 2
    before_frames = split_frame
    after_frames = total_frames - split_frame
    
    frame_idx = 0
    tracking_failures = 0
    
    print(f"Video length: {total_frames} frames @ {fps} FPS. Split at frame {split_frame}.")
    
    # 3. Processing Loop
    for result in model.track(
        source=str(video_path),
        stream=True,
        persist=True,
        tracker="bytetrack.yaml",
        imgsz=960,
        conf=0.08,
        iou=0.70,
        device="cpu",
        classes=[0, 1],
        verbose=False
    ):
        frame_idx += 1
        timestamp = frame_idx / fps
        boxes = result.boxes
        
        if boxes is None or len(boxes) == 0:
            tracking_failures += 1
            event_engine.process_frame_interactions(frame_idx, timestamp, [])
            continue
            
        ids = boxes.id
        xyxy = boxes.xyxy.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)
        
        persons = []
        forklifts = []
        
        for i, cls_id in enumerate(clss):
            tid = int(ids[i].item()) if ids is not None and ids[i] is not None else None
            if tid is None: continue
            
            box = [int(v) for v in xyxy[i]]
            raw_bbox = box  # Preserve for relation engine
            cx = (box[0] + box[2]) / 2.0
            foot_y = box[3]
            
            # Map to world
            world_pt = calibrator.pixel_to_world((cx, foot_y))
            if world_pt is None: continue # Extrapolation check
            
            c_name = model.names[int(cls_id)]
            zone = "SAFE" # Simplification for tracking
            
            # Update trajectory
            trajectory_engine.update(tid, c_name, timestamp, world_pt[0], world_pt[1], zone)
            traj = trajectory_engine.get_trajectory(tid)
            
            vel = (0.0, 0.0)
            if traj and traj.points and traj.points[-1].velocity_m_s is not None:
                speed = traj.points[-1].velocity_m_s
                dir_rad = traj.points[-1].direction_deg * (3.14159/180.0)
                import math
                vel = (speed * math.cos(dir_rad), speed * math.sin(dir_rad))
                
            entity = {"id": tid, "pos": world_pt, "vel": vel, "px": (cx, foot_y), "bbox": raw_bbox}
            
            if c_name == "person":
                persons.append(entity)
            elif c_name == "forklift":
                forklifts.append(entity)
                
        frame_interactions = []
        
        # V2.5: Classify operator/pedestrian relations
        relations = relation_engine.classify_frame(persons, forklifts, frame_idx)
        # Build lookup: person_id -> relation to each forklift
        operator_pairs = set()
        for rel in relations:
            if rel["relation"] == "OPERATOR_ON_VEHICLE" and rel["forklift_id"] is not None:
                operator_pairs.add((rel["person_id"], rel["forklift_id"]))
        
        # Calculate interactions (skip operator-on-vehicle pairs)
        for p in persons:
            for f in forklifts:
                # V2.5: Skip if person is classified as operator of this forklift
                if (p["id"], f["id"]) in operator_pairs:
                    continue
                    
                geo_res = compute_metric_distance(p["px"], f["px"], calibrator)
                if geo_res["calibration_status"] != "VALID": continue
                
                dist_m = geo_res["distance_m"]
                ttc_res = compute_metric_ttc(p["pos"], f["pos"], p["vel"], f["vel"], dist_m)
                
                # Determine Zone
                if dist_m < 1.5:
                    zone = "DANGER"
                elif dist_m < 3.0:
                    zone = "CAUTION"
                else:
                    zone = "SAFE"
                    
                risk_score = 0.0  # Computed at Event level later by RiskEngine
                
                # Find person's relation for metadata
                person_rel = next(
                    (r for r in relations if r["person_id"] == p["id"]),
                    {"relation": "INDEPENDENT_PEDESTRIAN", "confidence": 1.0}
                )
                
                frame_interactions.append({
                    "person_id": p["id"],
                    "forklift_id": f["id"],
                    "distance_meters": dist_m,
                    "approach_speed_px_s": ttc_res["relative_velocity_m_s"],
                    "zone_status": zone,
                    "risk_exposure_score": risk_score,
                    "person_relation": person_rel["relation"],
                    "relation_confidence": person_rel["confidence"]
                })
                
        event_engine.process_frame_interactions(frame_idx, timestamp, frame_interactions)
        
    # V2.5: Print relation summary
    rel_summary = relation_engine.get_summary()
    print(f"\nRelation summary: {rel_summary}")
    print("Tracking complete. Processing semantics and severity...")
    event_engine.close_all_events()
    
    # 4. Resolve Events
    all_events = event_engine.historical_events
    for evt in all_events:
        evt.semantic_type = SemanticClassifier.classify(evt)
        sev = SeverityEngine.calculate_severity(evt)
        evt.severity_level = sev["severity_level"]
        
    all_event_dicts = [e.to_dict() for e in all_events]
    
    # Split into Before and After
    before_events = [e for e in all_event_dicts if e["start_frame"] <= split_frame]
    after_events = [e for e in all_event_dicts if e["start_frame"] > split_frame]
    
    print(f"Events Before: {len(before_events)}, Events After: {len(after_events)}")
    
    # 5. Pipeline Analysis
    comparison = ComparisonEngine.compare(before_events, after_events)
    redistribution = RiskRedistributionEngine.analyze_redistribution(before_events, after_events)
    counterfactual = CounterfactualEngine.analyze(before_events, after_events, before_frames, after_frames)
    
    # Evaluate Evidence
    evidence_b = EvidenceEngine.evaluate_segment_evidence(all_events, total_frames, tracking_failures)
    
    # Decision
    verdict = DecisionEngine.assess(evidence_b, comparison["metrics"], redistribution, counterfactual)
    
    # Intervention Experiment Linkage
    intervention = Intervention("INT_001", "POLICY_CHANGE", "GLOBAL", "Simulated split for experiment")
    experiment = InterventionExperiment("EXP_V2_1", intervention, before_events, after_events)
    
    # Explainability
    explanation = ExplainabilityLayer.generate_explanation(verdict, comparison["metrics"], redistribution, before_events, after_events)
    
    # 6. Save Outputs
    out_manager.save_events(all_event_dicts)
    
    # Extract trajectories
    all_trajs = [t.get_metrics() for t in trajectory_engine.active_trajectories.values()]
    out_manager.save_trajectories(all_trajs)
    
    out_manager.save_comparison(comparison)
    out_manager.save_evidence(evidence_b)
    
    backfire_assessment = {
        "experiment_metadata": experiment.get_metadata(),
        "verdict": verdict,
        "explanation": explanation
    }
    out_manager.save_backfire_assessment(backfire_assessment)
    
    print("=== V2 Experiment Complete ===")
    print(f"Final Signal: {verdict['signal']}")
    print(f"Confidence: {verdict['confidence']}")
    print(f"Explanation: {explanation['summary']}")
    print(f"Outputs saved to {output_dir}")

if __name__ == "__main__":
    run_experiment()
