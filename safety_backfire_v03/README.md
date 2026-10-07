# Safety Backfire AI — V0.3

Specialized forklift/person detector baseline.

Dataset: keremberke/forklift-object-detection (421 images, CC BY 4.0). Keep attribution/license information.

Pipeline: download -> COCO to YOLO -> audit -> fine-tune YOLO26n on MPS -> validate -> test on test.mp4.
