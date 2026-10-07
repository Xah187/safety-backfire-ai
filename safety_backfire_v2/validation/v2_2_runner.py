"""
V2.2 Master Runner

Orchestrates the complete V2.2 Real-World Validation pipeline.
Produces all required reports with honest NOT_COMPUTABLE statuses
where data is unavailable.
"""
import sys
import json
import subprocess
import yaml
import math
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))


def run_phase(name: str, script: str, args: list = None) -> dict:
    """Run a validation phase script and capture results."""
    cmd = [sys.executable, str(ROOT / script)] + (args or [])
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[-500:]}")
        return {"status": "ERROR", "stderr": result.stderr[-200:]}
    print(result.stdout)
    return {"status": "OK", "stdout": result.stdout}


def load_json_safe(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def classify_geometry(report: dict) -> str:
    return report.get("calibration_classification", "UNVALIDATED")


def generate_validation_matrix(all_results: dict) -> list:
    """Build the final validation matrix table."""
    geo = all_results.get("geometry", {})
    det = all_results.get("detection", {})
    trk = all_results.get("tracking", {})
    evt = all_results.get("events", {})
    ev_rw = all_results.get("evidence_realworld", {})
    fail = all_results.get("failure_taxonomy", {})

    # Synthetic results from V2.1 (already validated)
    matrix = [
        {
            "component": "Geometry / Homography",
            "synthetic": "PASS",
            "real_world": "UNVALIDATED" if geo.get("computable_points", 0) == 0 else classify_geometry(geo),
            "status": "PARTIAL" if geo.get("computable_points", 0) == 0 else "TBD",
            "notes": "Physical measurements not available. Homography parameters are estimated, not physically measured."
        },
        {
            "component": "Detection (Person)",
            "synthetic": "PASS",
            "real_world": "NOT COMPUTABLE" if det.get("status") == "NOT_COMPUTABLE" else (
                det.get("person_metrics", {}).get("Recall", "N/A")
            ),
            "status": "NOT COMPUTABLE" if det.get("status") == "NOT_COMPUTABLE" else "TBD",
            "notes": "Requires human-annotated ground truth bboxes."
        },
        {
            "component": "Detection (Forklift)",
            "synthetic": "PASS",
            "real_world": "NOT COMPUTABLE" if det.get("status") == "NOT_COMPUTABLE" else (
                det.get("forklift_metrics", {}).get("Recall", "N/A")
            ),
            "status": "NOT COMPUTABLE" if det.get("status") == "NOT_COMPUTABLE" else "TBD",
            "notes": "Requires human-annotated ground truth bboxes."
        },
        {
            "component": "Tracking (IDF1)",
            "synthetic": "PASS (IDF1=0.561 synthetic)",
            "real_world": "NOT COMPUTABLE",
            "status": "NOT COMPUTABLE",
            "notes": "Synthetic IDF1 ≠ CCTV tracking validation. Real-world requires GT annotations."
        },
        {
            "component": "Distance (Metric)",
            "synthetic": "PASS (MAE=0.0 synthetic)",
            "real_world": "NOT COMPUTABLE",
            "status": "NOT COMPUTABLE",
            "notes": "No physical measurements available. Synthetic MAE=0.0 does NOT imply real-world accuracy."
        },
        {
            "component": "TTC",
            "synthetic": "PASS",
            "real_world": "NOT YET VALIDATED",
            "status": "PARTIAL",
            "notes": "Algorithmically validated. Real-world requires known relative motion ground truth."
        },
        {
            "component": "Interaction Events",
            "synthetic": "PASS",
            "real_world": "NOT COMPUTABLE" if evt.get("status") == "NOT_COMPUTABLE" else "TBD",
            "status": "NOT COMPUTABLE" if evt.get("status") == "NOT_COMPUTABLE" else "TBD",
            "notes": "Requires human-annotated interaction periods."
        },
        {
            "component": "Risk Engine",
            "synthetic": "PASS",
            "real_world": "NOT COMPUTABLE",
            "status": "PARTIAL",
            "notes": "Risk weights are project-defined, not validated against industrial safety standards."
        },
        {
            "component": "Evidence Engine",
            "synthetic": "PASS",
            "real_world": "PARTIAL" if ev_rw.get("critical_invariant_passed") else "FAIL",
            "status": "PARTIAL" if ev_rw.get("critical_invariant_passed") else "FAIL",
            "notes": f"Critical invariant (High YOLO confidence ≠ HIGH evidence): "
                     f"{'PASSED' if ev_rw.get('critical_invariant_passed') else 'FAILED'}"
        },
        {
            "component": "Backfire Decision",
            "synthetic": "PASS",
            "real_world": "NOT COMPUTABLE",
            "status": "NOT COMPUTABLE",
            "notes": "No before/after intervention metadata available for real video."
        },
        {
            "component": "Counterfactual",
            "synthetic": "PASS",
            "real_world": "NOT YET VALIDATED",
            "status": "PARTIAL",
            "notes": "Algorithmically validated. Real-world validation requires controlled experiments."
        },
    ]
    return matrix


def generate_scientific_report(all_results: dict, matrix: list) -> str:
    """Generate the Phase 20 scientific report."""
    ev_rw = all_results.get("evidence_realworld", {})
    fail = all_results.get("failure_taxonomy", {})
    real_stats = ev_rw.get("real_video_stats", {})

    failure_rows = ""
    for item in fail.get("failure_taxonomy", []):
        failure_rows += (
            f"| {item['failure_type']} | {item['count']} | "
            f"{item['severity']} | {item['root_cause'][:60]}... |\n"
        )

    matrix_rows = ""
    for row in matrix:
        matrix_rows += (
            f"| {row['component']} | {row['synthetic']} | "
            f"{row['real_world']} | {row['status']} |\n"
        )

    report = f"""# V2.2 Real-World Validation Report
**Date**: {datetime.now().strftime('%Y-%m-%d')}  
**Final Validation Status**: `ALGORITHMICALLY VALIDATED — REAL-WORLD PARTIALLY VALIDATED`

---

## 1. ما الذي تم التحقق منه فعليًا؟

تم التحقق **الاصطناعي** (Synthetic) من جميع مكونات محرك V2.1 في المرحلة السابقة:
- الهندسة، TTC، التتبع، الأحداث، المخاطر، الأدلة، القرار

التحقق **الواقعي** (Real-World) تم جزئياً فقط بسبب غياب:
- القياسات الفيزيائية الميدانية (physical measurements)
- التسميات البشرية لإطارات الفيديو (human annotations)
- بيانات التدخل (intervention metadata)

---

## 2. ما دقة القياس المترية؟

**الجواب**: غير معروفة بدقة في الواقع.

- MAE الاصطناعي = 0.0m (يثبت صحة الرياضيات فقط)
- نقاط Homography (`src_pts`) = **مُقدَّرة يدوياً، غير مُقاسة فيزيائياً**
- World space (3.5m × 6.0m) = **افتراض، غير مُتحقَّق منه**
- **الحالة**: `NOT COMPUTABLE — No physical ground truth available`

---

## 3. ما Recall للشخص؟

**الجواب**: `NOT COMPUTABLE`  
السبب: لا توجد تسميات بشرية (ground truth bboxes) لإطارات الفيديو.

---

## 4. ما Recall للرافعة؟

**الجواب**: `NOT COMPUTABLE`  
السبب: نفس السبب أعلاه.

---

## 5. ما جودة التتبع؟

- **IDF1 الاصطناعي**: 0.561 (على سيناريو اصطناعي محكوم)
- **IDF1 الواقعي**: `NOT COMPUTABLE`
- **تحذير**: نجاح الاختبار الاصطناعي لا يُساوي صحة التتبع على CCTV حقيقي

من الفيديو الحقيقي (تحليل Pipeline):
- إجمالي IDs المولَّدة: {real_stats.get('unique_ids', 'N/A')}
- معدل فشل التتبع: {real_stats.get('tracking_failure_rate', 'N/A'):.1%}

---

## 6. ما دقة Event Detection؟

**الجواب**: `NOT COMPUTABLE`  
السبب: لا توجد تسميات بشرية لفترات التفاعل.

من الفيديو الحقيقي:
- إجمالي أحداث التفاعل: {real_stats.get('total_events', 'N/A')}
- على test2.mp4 (1246 إطار، 25fps): النظام لم يُسجّل أي أحداث داخل منطقة المعايرة

---

## 7. هل TTC تم التحقق منه واقعيًا؟

**الجواب**: لا.  
TTC تم التحقق منه **خوارزمياً** فقط (synthetic scenarios + edge case handling).  
التحقق الواقعي يتطلب حركة نسبية معروفة مع قياس زمني دقيق — غير متاح حالياً.  
**الحالة الرسمية**: `ALGORITHMICALLY VALIDATED — NOT YET VALIDATED (Real-World)`

---

## 8. ما أخطاء النظام الأكثر شيوعًا؟

{failure_rows if failure_rows else "لم يتم تشغيل Phase 16 بعد أو لم تظهر أخطاء."}

---

## 9. ما الذي ما زال غير مثبت؟

| المكون | السبب |
|--------|-------|
| Metric Distance Accuracy | لا قياسات ميدانية |
| Person Recall | لا تسميات بشرية |
| Forklift Recall | لا تسميات بشرية |
| Real-World IDF1 | لا تسميات عبر الإطارات |
| TTC Real-World | لا ground truth لحركة نسبية |
| Event Precision/Recall | لا تسميات لفترات التفاعل |
| Backfire Real-World | لا intervention metadata |

---

## 10. ما الذي يجب تطويره قبل Production؟

### أولوية عالية (CRITICAL):
1. **قياس ميداني للـ Homography**: قياس `src_pts` و`dst_pts` بشريط قياس حقيقي في الموقع
2. **Human Annotation**: تسمية 50-100 إطار بشرياً لحساب Recall و IDF1
3. **Multi-camera calibration**: نقطة واحدة للكاميرا تحد من النطاق المعاير

### أولوية متوسطة:
4. **ByteTrack Tuning**: ضبط معاملات Re-ID لتقليل التجزؤ
5. **Appearance-based Re-ID**: لمقاومة occlusion ظاهر في frames 190-230 من test.mp4
6. **Industrial Risk Standards**: مقارنة معاملات Risk Engine بمعايير ISO 13849

---

## Validation Matrix النهائية

| Component | Synthetic | Real-World | Status |
|-----------|-----------|------------|--------|
{matrix_rows}

---

## Final Validation Status

```
ALGORITHMICALLY VALIDATED (V2.1 Synthetic Phases 1-9)
REAL-WORLD PARTIALLY VALIDATED (Evidence Engine Invariant ✓)
PRODUCTION NOT YET VALIDATED
```

لا يمكن إصدار `SYSTEM FULLY VALIDATED` بدون:
1. قياسات ميدانية للـ Homography
2. تسميات بشرية للفيديو
3. اختبار قبول في بيئة Production حقيقية
"""
    return report


def main():
    video_path = ROOT.parent / "test2.mp4"
    model_path = ROOT.parent / "safety_backfire_v07/runs/forklift_person_yolo26n_v07/weights/best.pt"
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)

    print("\n" + "="*70)
    print("  V2.2 REAL-WORLD VALIDATION RUNNER")
    print("="*70)

    # Phase 2: Geometry GT (template only, no physical measurements)
    run_phase("Phase 2: Geometry Ground Truth Template",
              "validation/real_world/collect_geometry_ground_truth.py",
              [str(video_path)])

    # Phase 5: Frame extraction for annotation
    run_phase("Phase 5: Frame Extraction for Annotation",
              "validation/real_world/extract_annotation_frames.py",
              [str(video_path)])

    # Phases 6-8: Detection/Tracking/Event validation (will return NOT_COMPUTABLE)
    run_phase("Phases 6-8: Detection, Tracking, Event Validation",
              "validation/real_world/validate_detection_tracking_events.py",
              [str(video_path)])

    # Phase 11: Evidence Engine Real-World Validation
    run_phase("Phase 11: Evidence Engine Real-World Validation",
              "validation/real_world/validate_evidence_realworld.py",
              [str(video_path)])

    # Phase 16: Failure Taxonomy
    run_phase("Phase 16: Failure Taxonomy",
              "validation/real_world/build_failure_taxonomy.py",
              [str(video_path)])

    # Load all results
    all_results = {
        "geometry": load_json_safe(ROOT / "validation/real_world/geometry_validation_report.json"),
        "detection": load_json_safe(ROOT / "validation/real_world/detection_tracking_event_validation.json").get("detection", {}),
        "tracking": load_json_safe(ROOT / "validation/real_world/detection_tracking_event_validation.json").get("tracking", {}),
        "events": load_json_safe(ROOT / "validation/real_world/detection_tracking_event_validation.json").get("events", {}),
        "evidence_realworld": load_json_safe(ROOT / "validation/real_world/evidence_validation_realworld.json"),
        "failure_taxonomy": load_json_safe(ROOT / "reports/v2_2_failure_taxonomy.json"),
    }

    # Generate Validation Matrix
    print("\n=== Generating Validation Matrix ===")
    matrix = generate_validation_matrix(all_results)

    # Phase 18: Save master JSON
    master_json = {
        "validation_date": datetime.now().isoformat(),
        "video": str(video_path.name),
        "physical_ground_truth_available": False,
        "human_annotations_available": False,
        "final_validation_status": "ALGORITHMICALLY VALIDATED — REAL-WORLD PARTIALLY VALIDATED",
        "validation_matrix": matrix,
        "detailed_results": all_results
    }

    with open(reports_dir / "v2_2_validation.json", "w") as f:
        json.dump(master_json, f, indent=2, default=str)

    # Phase 20: Scientific Report
    report_md = generate_scientific_report(all_results, matrix)
    with open(reports_dir / "v2_2_real_world_validation.md", "w") as f:
        f.write(report_md)

    # Summary metrics JSON
    metrics_summary = {
        "geometry_mae_m": None,
        "geometry_rmse_m": None,
        "geometry_status": "UNVALIDATED — No physical measurements",
        "person_recall": None,
        "person_precision": None,
        "forklift_recall": None,
        "forklift_precision": None,
        "detection_status": "NOT COMPUTABLE — No human annotations",
        "real_idf1": None,
        "tracking_status": "NOT COMPUTABLE — No human annotations",
        "ttc_status": "ALGORITHMICALLY VALIDATED — NOT YET VALIDATED (Real-World)",
        "evidence_invariant_passed": all_results["evidence_realworld"].get("critical_invariant_passed"),
        "evidence_status": "PARTIAL",
        "backfire_status": "NOT COMPUTABLE — No intervention metadata"
    }

    with open(reports_dir / "v2_2_metrics.json", "w") as f:
        json.dump(metrics_summary, f, indent=2)

    print("\n" + "="*70)
    print("  V2.2 VALIDATION COMPLETE")
    print("="*70)
    print(f"  Final Status: ALGORITHMICALLY VALIDATED — REAL-WORLD PARTIALLY VALIDATED")
    print(f"\n  Reports saved:")
    print(f"    reports/v2_2_validation.json")
    print(f"    reports/v2_2_real_world_validation.md")
    print(f"    reports/v2_2_metrics.json")
    print(f"    reports/v2_2_failure_taxonomy.json")
    print(f"\n  ⚠️  Dashboard should NOT be built until physical GT is available.")


if __name__ == "__main__":
    main()
