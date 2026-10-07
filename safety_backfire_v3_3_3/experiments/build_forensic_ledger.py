"""
build_forensic_ledger.py
EXP_333_01 FORENSIC RECONCILIATION — Section 4 Observation Ledger Builder
Applies canonical Model H formula and documents all formula deviations.
NO model optimization, retraining, or threshold tuning.
"""
import cv2
import json
import numpy as np
from pathlib import Path
from ultralytics import YOLO

WS = Path(__file__).resolve().parent.parent.parent

# ── 1. Load canonical Model H parameters ──────────────────────────────────────
with open(WS / "outputs/v3_3_3/reconciliation/model_h_lineage.json") as f:
    mh = json.load(f)
params = mh["parameters"]
k0 = params["k0"]
beta_d = params["beta_d"]
beta_l = params["beta_l"]
beta_pitch = params["beta_pitch"]
pitch_threshold = params["pitch_threshold_deg"]
gamma_occ = params["gamma_occ"]
CANONICAL_FORMULA = mh["formula"]

# ── 2. Video ───────────────────────────────────────────────────────────────────
video_path = WS / "data/external_facility/raw/0_te11.mp4"
model_path = WS / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
model = YOLO(str(model_path))

cap = cv2.VideoCapture(str(video_path))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps_video = float(cap.get(cv2.CAP_PROP_FPS))
n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# ── 3. Per-observation data collection ────────────────────────────────────────
observations = []
tracks_by_id = {}
obs_id = 0
frame_idx = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    results = model.track(frame, persist=True, tracker="bytetrack.yaml", conf=0.25, verbose=False)
    for r in results:
        if r.boxes:
            boxes = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            clss  = r.boxes.cls.cpu().numpy()
            tids  = r.boxes.id.cpu().numpy() if r.boxes.id is not None else [None]*len(boxes)

            for box, conf, cls_id, tid in zip(boxes, confs, clss, tids):
                cname = model.names[int(cls_id)]
                y_bottom = float(box[3])
                norm_y = max(0.01, min(1.0, (y_bottom - 200.0) / (height - 200.0)))
                dist_m = max(0.5, 3.0 + 9.0 * (1.0 - norm_y))
                t_int = int(tid) if tid is not None else None

                # ── Canonical Model H terms ───────────────────────────────────
                # k0: always available
                # beta_d * max(0, d - 4.0): calculable
                k_d_term = beta_d * max(0.0, dist_m - 4.0)

                # beta_l * max(0, 300 - L) / 100: NOT EVALUABLE (L unknown)
                # pitch term: NOT EVALUABLE (pitch unknown)
                # occlusion: NONE assumed (no GT)
                k_occ = gamma_occ["NONE"]

                # Evaluable lower bound (L and pitch terms set to zero = optimistic)
                k_lower = k0 + k_d_term + k_occ

                # Theoretical upper bound (worst-case L=0 lux, pitch < 40°)
                k_upper = k0 + k_d_term + beta_l * (max(0.0, 300.0 - 0.0) / 100.0) + beta_pitch * 1.0 + k_occ

                # RUNTIME (incorrect) k as was actually computed
                k_runtime_incorrect = k0 + beta_d * dist_m + beta_l * (1.0 - 0.50) + 0.0 + 0.0

                # Distance stratum
                if dist_m < 4.0:
                    stratum = "near_lt_4m"
                elif dist_m <= 8.0:
                    stratum = "mid_4_to_8m"
                else:
                    stratum = "far_gt_8m"

                obs = {
                    "observation_id": obs_id,
                    "frame_id": frame_idx,
                    "track_id": t_int,
                    "class": cname,
                    "confidence": round(float(conf), 6),
                    "bbox_xyxy": [round(float(v), 2) for v in box],
                    "distance_m_model_estimate": round(dist_m, 6),
                    "distance_evidence_type": "MODEL_ESTIMATE",
                    "distance_stratum": stratum,
                    "illumination_lux": None,
                    "illumination_available": False,
                    "camera_pitch_deg": None,
                    "pitch_available": False,
                    "occlusion_state": "NONE_ASSUMED",
                    "occlusion_gt_available": False,
                    # Canonical Model H breakdown
                    "k_term_k0": k0,
                    "k_term_distance": round(k_d_term, 6),
                    "k_term_illumination": None,
                    "k_term_pitch": None,
                    "k_term_occlusion": k_occ,
                    "k_canonical_lower_bound": round(k_lower, 6),
                    "k_canonical_upper_bound": round(k_upper, 6),
                    # What was actually computed at runtime (incorrect)
                    "k_runtime_computed": round(k_runtime_incorrect, 6),
                    "k_runtime_deviation_from_canonical_lower": round(k_runtime_incorrect - k_lower, 6),
                }
                observations.append(obs)
                obs_id += 1

                if t_int is not None:
                    if t_int not in tracks_by_id:
                        tracks_by_id[t_int] = {
                            "class": cname,
                            "first_frame": frame_idx,
                            "last_frame": frame_idx,
                            "detection_instance_count": 0
                        }
                    tracks_by_id[t_int]["last_frame"] = frame_idx
                    tracks_by_id[t_int]["detection_instance_count"] += 1

    frame_idx += 1

cap.release()

# ── 4. Aggregate statistics ───────────────────────────────────────────────────
total = len(observations)
by_class = {}
for o in observations:
    by_class[o["class"]] = by_class.get(o["class"], 0) + 1

near = sum(1 for o in observations if o["distance_stratum"] == "near_lt_4m")
mid  = sum(1 for o in observations if o["distance_stratum"] == "mid_4_to_8m")
far  = sum(1 for o in observations if o["distance_stratum"] == "far_gt_8m")
assert near + mid + far == total, f"Stratum sum {near+mid+far} != total {total}"

k_lb = [o["k_canonical_lower_bound"] for o in observations]
k_ub = [o["k_canonical_upper_bound"] for o in observations]
k_rt = [o["k_runtime_computed"] for o in observations]
dists = [o["distance_m_model_estimate"] for o in observations]

k_stats = {
    "note": "Lower bound assumes L_unknown=max(0,300-300)/100=0 and pitch_unknown_term=0. Upper bound assumes L=0lux and pitch<40deg.",
    "lower_bound": {
        "min": float(np.min(k_lb)),
        "max": float(np.max(k_lb)),
        "mean": float(np.mean(k_lb)),
        "median": float(np.median(k_lb)),
        "p95": float(np.percentile(k_lb, 95)),
    },
    "upper_bound": {
        "min": float(np.min(k_ub)),
        "max": float(np.max(k_ub)),
        "mean": float(np.mean(k_ub)),
        "median": float(np.median(k_ub)),
        "p95": float(np.percentile(k_ub, 95)),
    },
    "runtime_incorrect": {
        "min": float(np.min(k_rt)),
        "max": float(np.max(k_rt)),
        "mean": float(np.mean(k_rt)),
        "median": float(np.median(k_rt)),
        "p95": float(np.percentile(k_rt, 95)),
    }
}

# ── 5. Track topology ─────────────────────────────────────────────────────────
forklift_track_ids = sorted(t for t, m in tracks_by_id.items() if m["class"] == "forklift")
person_track_ids   = sorted(t for t, m in tracks_by_id.items() if m["class"] == "person")

# Track fragmentation: determine if multiple IDs can be attributed to one physical object
# We cannot confirm without independent ground truth; we record as FRAGMENTATION_SUSPECTED
track_topology = {}
for tid, meta in tracks_by_id.items():
    cls = meta["class"]
    frames = meta["detection_instance_count"]
    duration_s = round((meta["last_frame"] - meta["first_frame"]) / fps_video, 3)
    track_topology[tid] = {
        "class": cls,
        "first_frame": meta["first_frame"],
        "last_frame": meta["last_frame"],
        "detection_instances": frames,
        "duration_seconds": duration_s,
        "fragmentation_note": (
            "TRACK_FRAGMENTATION_SUSPECTED (likely same physical object; not confirmed by independent GT)"
            if cls == "forklift" and len(forklift_track_ids) > 1
            else "SINGLE_TRACK"
        )
    }

# ── 6. Write artifacts ────────────────────────────────────────────────────────
analysis_dir = WS / "outputs/v3_3_3/exp_333_01/analysis"
analysis_dir.mkdir(exist_ok=True)

# 6a. Full observation ledger (compact: no bbox to keep size manageable)
ledger_rows = []
for o in observations:
    ledger_rows.append({
        "observation_id": o["observation_id"],
        "frame_id": o["frame_id"],
        "track_id": o["track_id"],
        "class": o["class"],
        "confidence": o["confidence"],
        "distance_m": o["distance_m_model_estimate"],
        "distance_evidence_type": o["distance_evidence_type"],
        "distance_stratum": o["distance_stratum"],
        "illumination_lux": o["illumination_lux"],
        "camera_pitch_deg": o["camera_pitch_deg"],
        "occlusion_state": o["occlusion_state"],
        "k_canonical_lower_bound": o["k_canonical_lower_bound"],
        "k_canonical_upper_bound": o["k_canonical_upper_bound"],
        "k_runtime_computed": o["k_runtime_computed"],
        "k_deviation": o["k_runtime_deviation_from_canonical_lower"],
    })

with open(analysis_dir / "observation_level_audit.json", "w") as f:
    json.dump({
        "audit_version": "EXP_333_01_OBSERVATION_LEDGER_V1",
        "audit_timestamp_utc": "2026-09-27T19:15:00Z",
        "video": "0_te11.mp4",
        "video_sha256": "170a97c819e668d899e378e4ec1c417d89df8da3eff4373bf08f9698152babe1",
        "total_frames_processed": frame_idx,
        "total_detection_instances": total,
        "by_class": by_class,
        "distance_strata": {"near_lt_4m": near, "mid_4_to_8m": mid, "far_gt_8m": far, "sum_check": near+mid+far},
        "k_statistics": k_stats,
        "track_topology": track_topology,
        "forklift_track_ids": forklift_track_ids,
        "person_track_ids": person_track_ids,
        "observation_ledger": ledger_rows,
    }, f, indent=2)
    f.write("\n")

print("Observation ledger written:", analysis_dir / "observation_level_audit.json")
print(f"Total observations: {total}")
print(f"  forklift: {by_class.get('forklift',0)}, person: {by_class.get('person',0)}")
print(f"Strata: near={near}, mid={mid}, far={far}, sum={near+mid+far}")
print(f"k lower bound: min={np.min(k_lb):.4f} max={np.max(k_lb):.4f} mean={np.mean(k_lb):.4f} median={np.median(k_lb):.4f} P95={np.percentile(k_lb,95):.4f}")
print(f"k upper bound: min={np.min(k_ub):.4f} max={np.max(k_ub):.4f} mean={np.mean(k_ub):.4f} median={np.median(k_ub):.4f} P95={np.percentile(k_ub,95):.4f}")
print(f"k runtime (incorrect): min={np.min(k_rt):.4f} max={np.max(k_rt):.4f} mean={np.mean(k_rt):.4f}")
print(f"Distance range: [{min(dists):.4f}, {max(dists):.4f}]")
print("Track IDs (forklift):", forklift_track_ids)
print("Track IDs (person):", person_track_ids)
