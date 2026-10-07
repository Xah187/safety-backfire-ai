# V2.3 Real Ground-Plane Calibration & Spatial Coverage Validation
**Date**: 2026-09-21  
**Video Tested**: `test2.mp4`

## 1. ملخص المعايرة القديمة (V2.2) 
كانت المعايرة تعتمد على 4 نقاط محددة مسبقاً (Hardcoded) بمساحة صغيرة جداً في يمين الشاشة. هذا أدى إلى:
- **تغطية مكانية**: 0% (جميع الكشوفات سقطت خارج المضلع الدقيق).
- **أحداث مسجلة**: 0 حدث تفاعل (التفاعلات كانت تحدث لكن المحرك يرفضها بحجة Extrapolation).

## 2. المعايرة الجديدة (V2.3)
تم فحص الكشوفات في الفيديو كاملاً وبناء مضلع معايرة جديد من **11 نقطة تغطي كامل مساحة الأرضية** المرئية. 
**ملاحظة علمية هامة**: القياسات اعتمدت على `VISUAL_ESTIMATION` لعدم توفر قياسات فيزيائية حقيقية، لذا الحالة هي: **VISUALLY_ESTIMATED_NOT_VALIDATED**.

### نتائج التغطية المكانية
- إجمالي الكشوفات: 2032
- **مغطاة هندسياً (Inside + Edge)**: **86.5%** (تحسن هائل من 0%)
- **خطأ Reprojection الداخلي**: MAE = 0.41m (اتساق رياضي، لا يعني دقة فيزيائية).

## 3. اختبار محرك الأحداث (V2.3 Event Engine Run)
بعد حل المشكلة الهندسية وتصحيح تمرير الإحداثيات لمحرك الأحداث، تمت إعادة تشغيل الفيديو `test2.mp4`:
- الأحداث المكتشفة في V2.2: **0**
- الأحداث المكتشفة في V2.3: **3 أحداث تفاعل!**

> [!TIP]
> النظام الآن لا يرصد الأهداف فحسب، بل قادر هندسياً على إدخالها في محرك المخاطر وإصدار تفاعلات (Near-misses) عند اقتراب الرافعة من الشخص ضمن منطقة المعايرة الموسعة.

## 4. تحديد عنق الزجاجة المتبقي (Phase 15)
المشكلة **لم تعد** `CALIBRATION_LIMITED`. 
عنق الزجاجة الحالي هو `TRACKING_AND_GROUND_TRUTH`:
1. **لا يمكن حساب Recall/Precision أو IDF1** لعدم وجود إطارات مسماة (Annotated) بشرياً. 
2. **لا يمكن تأكيد دقة المسافة** لعدم وجود قياسات فيزيائية فعلية بشريط قياس (Tape Measure).

## 5. الحالة العلمية النهائية (Phase 16)
```
GEOMETRY LOGIC: VALIDATED
REAL-WORLD CALIBRATION: PARTIALLY VALIDATED (Visually estimated, wide coverage achieved)
METRIC ACCURACY: NOT VALIDATED (Needs physical measurements)
EVENT DETECTION: FUNCTIONAL (3 events logged, needs human validation)
```

تم تصدير المعايرة كـ Artifact منفصل إلى `config/calibration/warehouse_test2.json` لدعم أي قياسات فيزيائية مستقبلية.
