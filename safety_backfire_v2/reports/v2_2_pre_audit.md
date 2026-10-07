# V2.2 Pre-Validation Audit Report
**Date**: 2026-09-21  
**Scope**: Complete pipeline audit of Safety Backfire AI V2.1  
**Status of Physical Ground Truth**: ❌ NOT AVAILABLE

---

## 1. كيف يتم حساب المسافة

```
Footprint → pixel_to_world(cx, foot_y) → world_pt (x_m, y_m)
compute_metric_distance(p1_world, p2_world) → Euclidean distance in meters
```

**التحقق من الحدود**: كلا النقطتين يجب أن تقعا داخل `src_pts ± 100px margin`.  
**الخطر**: معاملات Homography (`src_pts`, `dst_pts`) **مُقدَّرة يدوياً** وغير مُتحقَّق منها ميدانياً.  
**حالة التحقق الفيزيائي**: ⚠️ NOT VALIDATED

---

## 2. كيف يتم حساب TTC

```
v_rel = forklift_vel - person_vel  (m/s vectors)
v_approach = dot(v_rel, r_hat)     (projection onto line of sight)
TTC = distance_m / v_approach      (if v_approach > 0.1)
```

**حالات الاستثناء**: إذا `v_approach ≤ 0.1` → `NO_APPROACH`. إذا لا توجد بيانات → `UNDEFINED`.  
**حالة التحقق**: ✅ ALGORITHMICALLY VALIDATED (synthetic). ⚠️ NOT YET VALIDATED (real-world).

---

## 3. كيف يتم إنشاء InteractionEvent

```
كل إطار: لكل زوج (person_id, forklift_id) في منطقة VALID:
  إذا pair_key موجود في active_events: تحديث الحدث
  إذا غير موجود: إنشاء حدث جديد
  إذا آخر رؤية > max_gap_frames=15: إغلاق الحدث
```

**الحد الأدنى**: يتطلب `distance_m` صحيحاً من Homography.  
**النتيجة**: إذا لم يكن هناك حالات تفاعل صالحة → `Events = 0`.

---

## 4. كيف يتم تحديد Track ID

```
YOLO.track(source, persist=True, tracker="bytetrack.yaml")
→ boxes.id → int Track ID (ByteTrack assignment)
```

**التعيين**: ByteTrack يُعيّن IDs عبر IoU matching + Kalman filter re-identification.  
**الخسارة والاستعادة**: عند استعادة track مفقود، قد يُعطى ID جديد → fragmentation.

---

## 5. كيف يتم التعامل مع Missing Detections

- **ByteTrack**: يحتفظ بالـ track داخلياً لعدد محدود من الإطارات
- **EventEngine**: `max_gap_frames=15` — الحدث يظل مفتوحاً حتى 15 إطاراً بعد آخر رؤية
- **النتيجة**: فجوة > 15 إطار = حدث جديد عند الظهور التالي

---

## 6. كيف يتم تحديد Calibration Bounds

```python
margin = 100.0  # pixels
calib_x_min = min(src_pts[:,0]) - 100  = 210 - 100 = 110
calib_x_max = max(src_pts[:,0]) + 100  = 430 + 100 = 530
calib_y_min = min(src_pts[:,1]) - 100  = 180 - 100 = 80
calib_y_max = max(src_pts[:,1]) + 100  = 340 + 100 = 440
```

⚠️ **تحذير**: الـ margin=100px يُوسّع المنطقة المقبولة بشكل كبير قد يسمح بنقاط خارج نطاق الـ Homography الدقيق.

---

## 7. كيف يتم حساب Risk Exposure

```
distance_risk  = w_min * exp(-scale * min_dist) + w_med * exp(-scale * median_dist)
duration_risk  = base * duration + caution_mult * time_in_caution + danger_mult * time_in_danger
kinematic_risk = min(peak_speed * w_speed, max_contribution)
total          = distance_risk + duration_risk + kinematic_risk
```

**المعاملات**: محددة في `config/risk_weights.yaml` — **project-defined، ليست معايير صناعية**.

---

## 8. كيف يتم حساب Evidence Confidence

```
confidence = 1.0 - Σ(penalties)
  - 0.4 إذا zero events
  - 0.3 إذا >50% أحداث قصيرة (<0.2s)
  - 0.1 × n إذا n أحداث خارج حدود Calibration
  - 0.4 إذا tracking_failure_rate > 20%
```

⚠️ **تحذير حرج**: High YOLO confidence **لا يرفع** مستوى الأدلة. الثقة مبنية على جودة التتبع وكمية الأحداث **فقط**.

---

## 9. كيف يُصدر Decision Engine النتيجة

| الإشارة | الشرط |
|---------|-------|
| `INSUFFICIENT_EVIDENCE` | إذا evidence_level == INSUFFICIENT |
| `SAFETY_BACKFIRE` | strength ≥ 0.7 |
| `RISK_IMPROVEMENT` | risk_change < 0 AND counterfactual consistent |
| `NO_SIGNIFICANT_CHANGE` | الحالة الافتراضية |

**النتيجة الحالية على test.mp4**: `INSUFFICIENT_EVIDENCE` (confidence=0.2)  
**النتيجة على test2.mp4**: `NO_SIGNIFICANT_CHANGE` (confidence=0.12)

---

## الثغرات المُحددة (Gaps)

| الثغرة | الخطورة |
|--------|---------|
| Homography parameters غير مُتحقَّق منها ميدانياً | 🔴 عالية |
| لا توجد annotations بشرية للفيديو | 🔴 عالية |
| Physical distance validation = NOT COMPUTABLE | 🔴 عالية |
| IDF1/Recall لـ CCTV = NOT COMPUTABLE | 🟡 متوسطة |
| Risk weights غير مشتقة من معايير صناعية | 🟡 متوسطة |
| لا توجد intervention metadata | 🟡 متوسطة |
| TTC real-world validation = NOT COMPUTABLE | 🟡 متوسطة |
| Footprint extraction لا تأخذ ارتفاع الجسم بعين الاعتبار | 🟡 متوسطة |
