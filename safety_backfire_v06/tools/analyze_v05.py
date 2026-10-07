from pathlib import Path
from collections import defaultdict, Counter
import csv, json, math, shutil
import cv2

if (Path.cwd() / "tracking_events.csv").is_file():
    ROOT = Path.cwd()
elif (Path(__file__).resolve().parent.parent / "tracking_events.csv").is_file():
    ROOT = Path(__file__).resolve().parent.parent
else:
    ROOT = Path(__file__).resolve().parent
CSV = ROOT / "tracking_events.csv"
VIDEO = ROOT / "test.mp4"
OUT = ROOT / "failure_gallery"
OUT.mkdir(exist_ok=True)

rows = []
with CSV.open(newline="") as f:
    for r in csv.DictReader(f):
        rows.append({
            "frame": int(r["frame"]),
            "time_sec": float(r["time_sec"]),
            "class": r["class"],
            "track_id": None if r["track_id"] == "" else int(r["track_id"]),
            "confidence": float(r["confidence"]),
            "x1": int(r["x1"]), "y1": int(r["y1"]),
            "x2": int(r["x2"]), "y2": int(r["y2"]),
        })

groups = defaultdict(list)
for r in rows:
    if r["track_id"] is not None:
        groups[(r["class"], r["track_id"])].append(r)

track_stats = []
for (cls, tid), rs in groups.items():
    rs = sorted(rs, key=lambda x: x["frame"])
    centers = [((x["x1"]+x["x2"])/2, (x["y1"]+x["y2"])/2) for x in rs]
    first, last = centers[0], centers[-1]
    displacement = math.hypot(last[0]-first[0], last[1]-first[1])
    mean_conf = sum(x["confidence"] for x in rs)/len(rs)
    min_conf = min(x["confidence"] for x in rs)
    max_conf = max(x["confidence"] for x in rs)
    # Path length in pixels.
    path = 0.0
    for a,b in zip(centers, centers[1:]):
        path += math.hypot(b[0]-a[0], b[1]-a[1])

    track_stats.append({
        "class": cls,
        "track_id": tid,
        "frames": len(rs),
        "first_frame": rs[0]["frame"],
        "last_frame": rs[-1]["frame"],
        "duration_sec": rs[-1]["time_sec"] - rs[0]["time_sec"] + 1/29.97,
        "mean_confidence": mean_conf,
        "min_confidence": min_conf,
        "max_confidence": max_conf,
        "start_center": list(first),
        "end_center": list(last),
        "displacement_px": displacement,
        "path_length_px": path,
        "mobility_ratio": path / max(displacement, 1.0),
    })

# Long, low-mobility forklift tracks are high-value FP candidates.
# This is a ranking heuristic, NOT automatic truth labeling.
forklift_candidates = sorted(
    [x for x in track_stats if x["class"] == "forklift"],
    key=lambda x: (
        -x["frames"],
        x["displacement_px"],
        x["mean_confidence"]
    )
)

person_tracks = sorted(
    [x for x in track_stats if x["class"] == "person"],
    key=lambda x: -x["frames"]
)

(OUT / "track_stats.json").write_text(json.dumps(track_stats, indent=2))

# Select representative frames from tracks:
# - first
# - middle
# - last
# - confidence peak
def representative(rs):
    rs = sorted(rs, key=lambda x: x["frame"])
    if len(rs) == 1:
        return rs
    idxs = {0, len(rs)//2, len(rs)-1}
    peak = max(range(len(rs)), key=lambda i: rs[i]["confidence"])
    idxs.add(peak)
    return [rs[i] for i in sorted(idxs)]

cap = cv2.VideoCapture(str(VIDEO))
if not cap.isOpened():
    raise RuntimeError(f"Cannot open video: {VIDEO}")

records = []

def save_crop(r, category, rank):
    cap.set(cv2.CAP_PROP_POS_FRAMES, r["frame"] - 1)
    ok, frame = cap.read()
    if not ok:
        return None
    pad = 20
    h, w = frame.shape[:2]
    x1 = max(0, r["x1"] - pad); y1 = max(0, r["y1"] - pad)
    x2 = min(w, r["x2"] + pad); y2 = min(h, r["y2"] + pad)
    crop = frame[y1:y2, x1:x2]
    path = OUT / category
    path.mkdir(exist_ok=True)
    name = f"rank_{rank:02d}_frame_{r['frame']:04d}_t_{r['time_sec']:.2f}_id_{r['track_id']}.jpg"
    full = path / name
    cv2.imwrite(str(full), crop)
    return str(full.relative_to(ROOT))

for idx, s in enumerate(forklift_candidates[:12], start=1):
    rs = sorted(groups[("forklift", s["track_id"])], key=lambda x: x["frame"])
    for r in representative(rs):
        p = save_crop(r, "forklift_ranked", idx)
        if p:
            records.append({
                "category": "forklift_ranked",
                "rank": idx,
                "reason": "long track; inspect whether the tracked object is a real forklift or a persistent false positive",
                "record": r,
                "track_stats": s,
                "file": p
            })

for idx, s in enumerate(person_tracks[:6], start=1):
    rs = sorted(groups[("person", s["track_id"])], key=lambda x: x["frame"])
    for r in representative(rs):
        p = save_crop(r, "person_tracks", idx)
        if p:
            records.append({
                "category": "person_tracks",
                "rank": idx,
                "reason": "representative person track; inspect continuity and missed intervals",
                "record": r,
                "track_stats": s,
                "file": p
            })

# Create frame-level audit list for manual review.
audit = []
for r in rows:
    if r["class"] in {"forklift", "person"} and r["track_id"] is not None:
        audit.append(r)
with (OUT / "annotation_review.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "frame","time_sec","class","track_id","confidence",
        "x1","y1","x2","y2","human_label"
    ])
    w.writeheader()
    for r in audit:
        r2 = dict(r)
        r2["human_label"] = ""
        w.writerow(r2)

report = {
    "total_rows": len(rows),
    "unique_tracks": len(track_stats),
    "tracks_by_class": dict(Counter(x["class"] for x in track_stats)),
    "top_forklift_candidates": forklift_candidates[:12],
    "person_tracks": person_tracks[:6],
    "warning": "No human labels are inferred. Ranked forklift candidates are only triage heuristics.",
}
(OUT / "failure_gallery_report.json").write_text(json.dumps(report, indent=2))

cap.release()

print(json.dumps(report, indent=2))
print("\nFailure gallery:", OUT)
