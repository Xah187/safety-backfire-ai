# DATA PROVENANCE & SIM-TO-REAL GAP ASSESSMENT
## NVIDIA PhysicalAI-SmartSpaces (Warehouse_026 & Warehouse_027) as Synthetic Benchmark Data for Safety-Critical Evaluation

**Document Identifier**: `DP-SRGA-V3.3.3-01`  
**Classification**: Safety Assurance Technical Report / Regulatory Evidence File  
**Author**: Senior Safety Assurance & Data Provenance Lead  
**Applicable Frameworks**: ISO 3691-4:2023, ISO 13849-1:2023, ASME V&V 40, EU AI Act (Arts. 10–15)  
**Target Systems**: Safety Backfire AI / Model H Dynamic Uncertainty Inflation Pipeline (v3.3.3)  
**Publication Date**: 2026-09-28  
**Audit Status**: CRITICAL INTEGRITY CORRECTION & FORMAL PROVENANCE RE-CLASSIFICATION  

---

## EXECUTIVE SUMMARY (REGULATORY & INDUSTRIAL ASSURANCE BRIEF)

This document establishes a mandatory, permanent correction to the data provenance classification of the video and calibration assets utilized during benchmark evaluations `RUN_003` and `RUN_004` within experiment `EXP_333_01_EXTERNAL_FACILITY`.

**Core Finding**: Previous internal engineering reports and summary briefings incorrectly characterized the benchmark data sourced from `nvidia/PhysicalAI-SmartSpaces` (`Warehouse_026` and `Warehouse_027`) as *"authentic warehouse facilities"*, *"real-world test captures"*, and *"independently surveyed facilities"*. This characterization is **factually false**. Official documentation from NVIDIA unequivocally specifies that the PhysicalAI-SmartSpaces benchmark is **synthetically generated using NVIDIA Omniverse (Isaac Sim) and Cosmos Transfer**.

**Impact on System Certification**: Under harmonized functional safety and machinery safety standards (ISO 3691-4:2023, ISO 13849-1), as well as the EU AI Act (Regulation (EU) 2024/1689, Articles 10 and 15), **synthetic simulation data alone cannot validate a safety function or support a claim of Achieved Performance Level (PLr d/e)**. Synthetic generation inherently decouples camera rendering from physical sensor artifacts (photodiode shot noise, dynamic range clipping, motion blur, rolling shutter, lens distortion variance) and decouples worker behavior from real-world stochastic human dynamics.

**Action Taken & Technical Posture**:
1. **Re-Classification**: All test assets from `Warehouse_026` and `Warehouse_027` are permanently classified as **High-Fidelity Synthetic Simulation Benchmarks**.
2. **Preserved Capabilities**: Algorithmic scalability, mathematical pipeline correctness, ground-plane homography projection logic ($H_{\text{img}\to\text{ground}} = (P_{:,[0,1,3]})^{-1}$), extrinsic matrix decomposition, and zero-runtime-divergence execution across 11 synchronized camera streams (19,800 frames, 45,836 synthetic detections) remain **fully verified as software-in-the-loop (SIL) achievements**.
3. **Expunged Claims**: Any assertion of real-world perception accuracy (F1, Precision, Recall), multi-target tracking continuity (IDF1, MOTA), illumination robustness, or safety certification readiness is **formally declared unverified and invalid without authenticated physical operational data**.
4. **Strategic Strengthening**: By voluntarily identifying, declaring, and correcting this provenance mischaracterization, the Safety Backfire AI project eliminates legal, regulatory, and scientific vulnerabilities, establishing an audit-proof foundation for transition to real-world pilot validation (Milestone V3.4).

---

## SECTION 1 — SOURCE CLASSIFICATION (MANDATORY)

### 1.1 Unambiguous Classification: SYNTHETIC DATA
The data assets ingested and evaluated under `RUN_003` (`Warehouse_026`) and `RUN_004` (`Warehouse_027`) are **SYNTHETIC DATA**. They are computer-generated visual renderings created within virtual environments, NOT physical video streams captured by physical photons hitting physical charge-coupled devices (CCD) or complementary metal-oxide-semiconductor (CMOS) sensors mounted in a physical building.

### 1.2 Origin & Generative Pipeline Authority
* **Dataset Identifier**: `nvidia/PhysicalAI-SmartSpaces` (Multi-Target Multi-Camera Tracking Benchmark)
* **Hosting Authority**: Hugging Face Hub (`https://huggingface.co/datasets/nvidia/PhysicalAI-SmartSpaces`)
* **Primary Source Citation**: NVIDIA Corporation, *PhysicalAI-SmartSpaces: A Large-Scale Synthetic Perception Benchmark for Physical AI in Smart Spaces*, NVIDIA Research (2025/2026).
* **Official Dataset Card Statement**:
  > *"This dataset is synthetically generated with Omniverse and Cosmos Transfer. This dataset consists of over 280 hours of video from across nearly 1,800 cameras from indoor scenes in warehouses, hospitals, retail, and more."*
* **License**: Creative Commons Attribution 4.0 International (CC-BY-4.0).

### 1.3 Labeling & Ground Truth Provenance
* **Labeling Methodology**: Fully automated extraction directly from the 3D physics engine and scene graph in **Isaac Sim / Omniverse**. Bounding boxes, 3D world coordinates, and instance IDs are computed via geometric projection of 3D asset meshes onto virtual camera sensor planes. There is zero human-in-the-loop manual annotation.
* **Ground Truth Availability for Evaluation Scenes**:
  * For training and validation subsets of PhysicalAI-SmartSpaces, automatic ground-truth JSON files (`MTMC_Tracking_2025`/`2026` schema) are distributed.
  * For the designated evaluation/test subsets—including `Warehouse_026` (4 cameras) and `Warehouse_027` (7 cameras)—**ground truth annotations are withheld by NVIDIA** to serve as a blind evaluation benchmark.
  * Consequently, not only is the data synthetic, but **no ground truth is accessible locally**, rendering any computation of error residuals or detection accuracy mathematically impossible.

### 1.4 Formal Declaration of What the Dataset IS and IS NOT

```
┌────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────┐
│ WHAT THE DATASET IS                                    │ WHAT THE DATASET IS NOT                                │
├────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ • A high-fidelity, physically based rendering (PBR)    │ • Authentic physical closed-circuit television (CCTV)  │
│   synthetic benchmark.                                 │   or industrial machine-vision footage.                │
│ • A multi-camera virtual simulation built in NVIDIA    │ • A physical warehouse facility with real industrial   │
│   Omniverse (Isaac Sim) with Cosmos Transfer filters.  │   workers, real forklifts, or physical air hazards.    │
│ • A rigorous testbed for software-in-the-loop (SIL)     │ • A physical survey with total-station-measured camera │
│   stress-testing, memory leak detection, and pipeline  │   extrinsic/intrinsic positions or physical tilt.      │
│   concurrency across 11 synchronized camera streams.   │ • A valid basis for claiming real-world camera F1,     │
│ • A mathematically exact check of ground-plane         │   precision, recall, IDF1, or safety coverage.         │
│   homography inversion on virtual pinhole cameras.     │ • A compliance-grade artifact under ISO 3691-4 or      │
│ • Synthetic visual proxy data for structural design.   │   ISO 13849-1 for functional safety validation.        │
└────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## SECTION 2 — SIMULATION PIPELINE DESCRIPTION

Based on published technical disclosures by NVIDIA for Omniverse, Isaac Sim, and Cosmos Transfer, the generative architecture producing `Warehouse_026` and `Warehouse_027` consists of the following components:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               NVIDIA SIMULATION ARCHITECTURE                            │
│                                                                                         │
│  ┌───────────────────────┐      ┌────────────────────────┐      ┌────────────────────┐  │
│  │   Omniverse USD       │      │   Isaac Sim Physics    │      │  Cosmos Transfer   │  │
│  │   Scene Graph         │ ───► │   (PhysX / RTX PBR)    │ ───► │  Neural Style &    │  │
│  │ • 3D CAD Geometry     │      │ • Kinematic Actors     │      │  Photorealism Ref. │  │
│  │ • Virtual Cameras     │      │ • Ray Tracing Core     │      │ • Latent Diffusion │  │
│  │ • PBR Material Shaders│      │ • Perfect Projection   │      │ • Video Inpainting │  │
│  └───────────────────────┘      └────────────────────────┘      └────────────────────┘  │
│                                                                            │            │
│                                                                            ▼            │
│                                                                 ┌────────────────────┐  │
│                                                                 │ Encoded H.264 MP4  │  │
│                                                                 │ 1080p @ 30 FPS     │  │
│                                                                 │ + Virtual Extr/Int │  │
│                                                                 └────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Simulation Subsystems
1. **Scene Composition (Universal Scene Description - USD)**:
   * 3D structural assets (industrial racking, concrete floors, steel columns, wooden pallets, standardized corrugated cardboard boxes).
   * Static lighting primitives (rectangular luminous ceiling luminaires, simulated high-pressure sodium or LED area lights).
   * Static camera placements attached to virtual beam prims with exact 6-DOF transform vectors $[R \mid t]$.
2. **Actor Animation & Kinematics (Isaac Sim / PhysX)**:
   * Rigged human character meshes driven by motion-capture (mocap) libraries or procedural navigation graphs executing pre-scripted waypoints.
   * Automated Guided Vehicles (AGVs) and forklift meshes following spline-based paths with simplified kinematic vehicle physics.
3. **Ray-Tracing & Sensor Simulation (RTX Renderer)**:
   * Path-traced rendering with arbitrary output variables (AOVs), depth buffers, surface normals, and instance segmentation masks.
   * Virtual cameras parameterized by ideal pinhole intrinsic matrices ($f_x, f_y, c_x, c_y$) with zero or mathematically synthesized Brown-Conrady radial distortion.
4. **Neural Post-Processing (Cosmos Transfer)**:
   * Generative diffusion/latent-transfer network applied across rendered frames to increase surface grit, subtle ambient occlusion variations, and texture micro-detail, aiming to bridge the visual uncanny valley.

### 2.2 Boundary Between Modeled vs. Unmodeled Real-World Physics

```
┌───────────────────────────────────────────────┬──────────────────────────────────────────────────────────┐
│ EXPLICITLY SIMULATED IN OMNIVERSE / COSMOS    │ EXPLICITLY NOT SIMULATED OR UNVERIFIED (REALITY GAPS)    │
├───────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
│ • Nominal 3D CAD geometry and layout          │ • CMOS sensor dark current, thermal noise, PRNU, FPN     │
│ • Idealized diffuse and specular PBR shaders  │ • Analog-to-digital converter (ADC) dynamic range cut    │
│ • Kinematic human mesh translations           │ • Hardware auto-exposure (AE) hunting & gain adjustments │
│ • Virtual camera extrinsic rotation/matrices  │ • Real-world optical lens flare, vignetting, chromatic aberration │
│ • Primary light source geometric occlusion    │ • Dust, airborne particulate scattering, oily lens smudge│
│ • Multi-view perspective consistency          │ • Unpredictable human reflexes, trips, slips, irregular gait│
│ • Frame synchronization across virtual views  │ • Physical lux telemetry (incident illuminance in lumens/m²)│
│ • Nominal ground-plane planarity ($Z=0$)      │ • Floor unevenness, tire skid marks, structural vibrations │
└───────────────────────────────────────────────┴──────────────────────────────────────────────────────────┘
```

---

## SECTION 3 — SIM-TO-REAL GAP ASSESSMENT (CORE AUDIT)

A systematic gap analysis was conducted across four physical and operational domains. Every identified gap directly threatens uncorrected computer vision pipelines by inducing **optimistic bias**—the dangerous illusion that an algorithm is more reliable than it would be in a physical industrial environment.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                SIM-TO-REAL GAP SEVERITY MATRIX                                 │
│                                                                                                │
│   HIGH SEVERITY   │ [Illumination / Lux]      [Optical Sensor Noise]    [Human Behavior]       │
│                   │ Physical lux absent       Thermal/gain noise absent Hesitations unmodeled  │
│                   ├────────────────────────────────────────────────────────────────────────────┤
│   MEDIUM SEVERITY │ [Edge Occlusion Sharpness] [Camera Rigidity/Drift]   [Dynamic Range]       │
│                   │ Perfect rendered edges    Vibration absent          Clipped shadows absent │
│                   ├────────────────────────────────────────────────────────────────────────────┤
│   LOW / NEGLIGIBLE│ [Camera Extrinsic Geometry] [Nominal Aspect Ratios]                        │
│                   │ Rigorously checked in SIL  Pinhole model conformal                         │
│                   └────────────────────────────────────────────────────────────────────────────┘
│                     LOW CONFIDENCE ◄──────────────────────────────► HIGH CONFIDENCE            │
│                                        EVIDENCE BASE                                           │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Perception-Level Gaps

#### Gap 3.1.1: Visual Domain & Sensor Electronics Gap
* **Description**: Real industrial CCTV and machine vision cameras utilize cost-optimized CMOS image sensors (e.g., Sony Starvis or OnSemi AR series) that suffer from physical electronic noise: fixed-pattern noise (FPN), photon shot noise, reset noise, and thermal dark current. Under standard warehouse lighting ($50 - 150 \text{ lux}$), cameras operate at high analog gain (ISO 800–3200), introducing significant high-frequency chroma and luma grain that degrades neural network feature maps. Additionally, rolling-shutter artifacts distort moving forklift masts and walking worker limbs.
* **Synthetic Manifestation**: Omniverse/Cosmos generates perfectly converged ray bundles or temporally filtered diffuse surfaces. Even when neural post-processing adds grain, it lacks the signal-dependent Poisson-Gaussian distribution of physical sensor noise.
* **Risk to Safety**: **Over-Optimistic**. YOLO-based object detectors retain high confidence on crisp, clean synthetic edges, but drop confidence or produce bounding box jitter when exposed to high-gain CMOS grain.

#### Gap 3.1.2: Illumination & Photometric (Lux) Gap
* **Description**: Model H relies upon incident light level ($L$, measured in physical $\text{lux}$) as a first-class physical uncertainty driver. Real industrial luminaires feature non-uniform lumen depreciation, strobe flicker ($100/120 \text{ Hz}$ ballasts), and severe backlighting when warehouse high-bay doors open to exterior sunlight ($10,000 - 80,000 \text{ lux}$ contrast). Real cameras respond with aggressive Auto-Exposure (AE) and Auto-White-Balance (AWB) hunting that causes multi-frame contrast washouts.
* **Synthetic Manifestation**: Omniverse scenes feature static, perfectly balanced tone-mapped lighting. No physical radiometer or lux meter logged actual flux density in lumens/$\text{m}^2$. Pixel values are normalized RGB floats without physical photometric anchors.
* **Risk to Safety**: **Severe Over-Optimism**. The absence of physical lux data forced Model H into `INPUT_INSUFFICIENT` status. Evaluating perception without physical illumination dynamics masks sensor blindness under backlighting and shadow-transition zones.

#### Gap 3.1.3: Occlusion Silhouette & Volumetric Edge Gap
* **Description**: In physical warehouses, occlusions are messy: shrink-wrap plastic creates semi-transparent, reflective, and distorted silhouettes; cardboard boxes bulge and tear; stacked pallets have irregular gaps through which limbs appear fragmented.
* **Synthetic Manifestation**: In Isaac Sim, 3D CAD bounding meshes possess knife-sharp polygonal boundaries. Even with Cosmos style transfer, bounding occluders remain geometrically pristine solid primitives.
* **Risk to Safety**: **Over-Optimistic**. Bounding box regression and ByteTrack association algorithms perform substantially better against knife-sharp, solid polygonal boundaries than against translucent shrink-wrap or ragged edge silhouettes.

#### Gap 3.1.4: Material Reflectance & Surface Scatter Gap
* **Description**: Real warehouse concrete floors develop high-gloss polishing in traffic lanes, rubber tire scuff marks, oil droplets, and specular reflections that mirror high-bay light fixtures directly into ceiling cameras.
* **Synthetic Manifestation**: While Omniverse utilizes physically based rendering (PBR) Bidirectional Scattering Distribution Functions (BSDF), synthetic floor maps cannot model the chaotic, localized micro-reflections and glare blinding caused by unevenly worn epoxy or concrete seals.
* **Risk to Safety**: **Moderate Over-Optimism**. False positive worker reflections in polished floors are suppressed in synthetic renderings, artificially inflating detector precision.

---

### 3.2 Geometry-Level Gaps

#### Gap 3.2.1: Camera Calibration & Extrinsic Mounting Provenance
* **Description**: In physical industrial safety systems (e.g., compliant with ISO 3691-4 Annex H), camera extrinsics $[R \mid t]$ and intrinsics $K$ must be validated via on-site survey methods: total-station laser theodolites, calibrated floor targets with known GPS/local coordinates, and precision optical targets to quantify lens distortion residuals ($k_1, k_2, p_1, p_2$). Physical camera brackets also experience mechanical drift, thermal expansion, and structural vibration from overhead cranes.
* **Synthetic Manifestation**: The calibration matrices supplied in `Warehouse_026` and `Warehouse_027` are mathematical extractions from the virtual camera transform nodes in the Omniverse USD stage. The reported reprojection error ($RMSE \sim 0.05 - 0.09 \text{ px}$) represents machine-precision floating-point projection, NOT empirical surveying accuracy.
* **Risk to Safety**: **Unknown / Deceptive**. While this validates that our software geometry engine computes inverse ground-plane coordinates ($H_{\text{img}\to\text{ground}}$) without mathematical error, it provides zero assurance that the pipeline can tolerate physical bracket sagging, thermal lens warping, or non-coplanar warehouse floors.

#### Gap 3.2.2: The Camera Pitch Empirical Finding in Synthetic Context
* **Empirical Observation in RUN_003 & RUN_004**: The measured depression angles across the 11 synthetic cameras averaged $27.74^\circ$ and $27.42^\circ$, refuting the theoretical assumption that cameras would operate at steep overhead angles ($\ge 40^\circ$).
* **Sim-to-Real Nuance**: This finding reflects the **design choices of the NVIDIA 3D environment artists and layout engineers** who constructed the USD scene. While it strongly mirrors common-sense surveillance mounting (achieving long corridor lines of sight), it cannot be cited as an *"independently surveyed empirical measurement of physical American or European warehouses"*. It is an architectural property of the benchmark scene geometry.

---

### 3.3 Behavioral-Level Gaps

#### Gap 3.3.1: Human Stochasticity & Micro-Behaviors
* **Description**: Real industrial warehouse workers display complex, unpredictable behaviors: stepping backward without looking, crouching behind pallets to inspect barcodes, leaning into racking bays, wearing varying personal protective equipment (PPE) with high-visibility retro-reflective stripes that create blooming artifacts under direct light, and clustering closely during shift changes.
* **Synthetic Manifestation**: The human actors in `Warehouse_026` and `Warehouse_027` are driven by scripted character animation tracks or goal-directed motion planning. They exhibit smooth, steady-velocity bipedal walking cycles, maintain artificial interpersonal spacing, and wear uniform clothing textures without retro-reflective optical flare.
* **Risk to Safety**: **Significant Over-Optimism**. Track fragmentation and identity-switching are drastically lower on synthetic bipedal animations than on physical humans who suddenly crouch, bend, turn, or interact with physical handheld equipment.

#### Gap 3.3.2: Mobile Machinery Dynamics & Aerodynamics
* **Description**: Physical forklifts and reach trucks experience tire slip, mast oscillation during acceleration/braking, dynamic chassis tilting under load, and generate particulate exhaust or dust plumes that obscure cameras.
* **Synthetic Manifestation**: Forklifts in Isaac Sim are rigid bodies translating along planar curves. Mast vibration, hydraulic leak patches, and dust dispersion are completely absent.
* **Risk to Safety**: **Moderate Over-Optimism**.

#### Gap 3.3.3: Rare Event & Safety-Critical Edge Case Representation
* **Description**: Under functional safety standards, the primary concern is the tail of the risk distribution: near-misses, pedestrian stepping into a blind intersection, loads falling from racking, or emergency braking events.
* **Synthetic Manifestation**: The benchmark video sequences depict benign, nominal operating conditions. Zero catastrophic edge cases, near-collisions, or rapid emergency decelerations are depicted in the sequences analyzed.
* **Risk to Safety**: **Severe Under-Representation of Hazard Space**.

---

### 3.4 Quantified Risk of Sim-to-Real Shift

The following table synthesizes the gap analysis into a formal risk evaluation, specifying whether each factor induces optimistic bias, the magnitude of the divergence, the evidentiary basis, and our audit confidence level:

```
┌─────────────────────────────────┬───────────────────┬──────────────┬─────────────────────────┬──────────────────┐
│ SIM-TO-REAL GAP DIMENSION       │ OPTIMISTIC BIAS?  │ MAGNITUDE    │ EVIDENCE BASIS          │ CONFIDENCE LEVEL │
├─────────────────────────────────┼───────────────────┼──────────────┼─────────────────────────┼──────────────────┤
│ 1. CMOS Sensor Grain & Noise    │ YES (Optimistic)  │ Significant  │ CV Sensor Literature    │ HIGH             │
│ 2. Photometric / Lux Telemetry  │ YES (Optimistic)  │ Critical     │ Model H Math Audit      │ HIGH             │
│ 3. Auto-Exposure / Glare Flare  │ YES (Optimistic)  │ Significant  │ Physical Camera Bench   │ HIGH             │
│ 4. Optical Lens Distortion Drift│ UNKNOWN           │ Moderate     │ Photogrammetry Theory   │ MEDIUM           │
│ 5. Physical Floor Non-Planarity │ YES (Optimistic)  │ Moderate     │ Civil Survey Standards  │ HIGH             │
│ 6. Occlusion Edge Crispness     │ YES (Optimistic)  │ Significant  │ Computer Vision Bench   │ HIGH             │
│ 7. Human Motion Stochasticity   │ YES (Optimistic)  │ Critical     │ Industrial Safety Logs  │ HIGH             │
│ 8. Retro-Reflective PPE Glare   │ YES (Optimistic)  │ Significant  │ High-Vis Optical Audits │ MEDIUM           │
│ 9. Safety-Critical Near-Misses  │ YES (Optimistic)  │ Critical     │ Hazard Analysis (FMEA)  │ HIGH             │
└─────────────────────────────────┴───────────────────┴──────────────┴─────────────────────────┴──────────────────┘
```

---

## SECTION 4 — LIMITS OF VALID CLAIMS

To uphold absolute scientific rigor and protect the organization from liability, all public, technical, and regulatory representations must respect the strict boundary between **Allowed Claims** and **Forbidden Claims**.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BOUNDARY OF LEGITIMATE CLAIMS                                    │
│                                                                                                  │
│   ALLOWED CLAIMS (Software & Architecture)          FORBIDDEN CLAIMS (Physical Safety & Metrics)  │
│   ┌──────────────────────────────────────────┐      ┌──────────────────────────────────────────┐ │
│   │ • Multi-camera pipeline concurrency      │      │ • Claiming field F1, Precision, Recall   │ │
│   │ • Zero memory leaks across 19,800 frames │  X   │ • Claiming tracking IDF1 / MOTA          │ │
│   │ • Pinhole inverse homography math        │ ───► │ • Declaring ISO 3691-4 conformance       │ │
│   │ • Extrinsic 3D matrix decomposition      │      │ • Claiming certified optical coverage    │ │
│   │ • Automated ODD classification logic     │      │ • Asserting real-world worker protection │ │
│   └──────────────────────────────────────────┘      └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Allowed Claims (Scientifically & Legally Defensible)
The following statements are verified and may be made with complete confidence:

1. **Software Pipeline Scalability**: The perception and tracking execution harness successfully processed 19,800 frames across 11 synchronized camera streams at 30 FPS without memory leaks, process crashes, or thread deadlocks.
2. **Inverse Geometry Engine Correctness**: The mathematical implementation of ground-plane homography projection ($H_{\text{img}\to\text{ground}} = (P_{:,[0,1,3]})^{-1}$) and camera optical axis decomposition from $3 \times 4$ projection matrices operates with mathematical precision on simulated pinhole cameras.
3. **Architectural Metric Computation**: The software correctly extracts ground-plane metric distance $d$ relative to camera projection center $C_{xy} = (-R^T t)_{xy}$ and applies the continuous risk penalty $\beta_{\text{dist}} \cdot d$.
4. **Autonomous ODD Stratification**: The system successfully profiled 45,836 synthetic detections into domain categories (In-ODD, Degraded, Out-of-ODD), correctly flagging long-range corridor dilution in `Camera_0001` (77.6% $>10\text{m}$) and `Camera_0004` (54.7% $>10\text{m}$).
5. **Frozen Baseline Governance**: The Model H uncertainty multiplier engine executed under strict governance with zero runtime parameter tuning and zero hash drift across baseline files.

### 4.2 Forbidden Claims (Prohibited Without Authenticated Physical Data)
The following statements **CANNOT be made under any circumstances** based on current evidence:

```
┌───────────────────────────────────┬────────────────────────────────────────────────────────────────────┐
│ FORBIDDEN CLAIM                   │ REQUIRED EVIDENCE TO PERMIT CLAIM                                  │
├───────────────────────────────────┼────────────────────────────────────────────────────────────────────┤
│ 1. "Perception F1 / Precision /   │ Dual-annotated physical human ground truth on authenticated        │
│    Recall is X%"                  │ CCTV footage with inter-annotator agreement (Cohen's Kappa >= 0.90)│
│ 2. "Tracking IDF1 / MOTA / HOTA   │ Continuous spatio-temporal identity annotations across physical    │
│    is certified at X%"            │ multi-camera overlap zones in an operating facility.               │
│ 3. "Model H covers illumination   │ Synchronized, calibrated physical lux meter data logged at camera  │
│    conditions in real warehouses" │ viewpoints across shifting day/night/artificial lighting.          │
│ 4. "The system is ISO 3691-4 or   │ Formal Hardware/Software-in-the-Loop test campaign conducted on    │
│    ISO 13849 certified"           │ physical automated industrial vehicles under accredited test labs. │
│ 5. "Real-world worker safety is   │ Empirical collision-avoidance field trials with dummy targets and  │
│    guaranteed by the pipeline"    │ authenticated physical hardware safety interlocks.                 │
│ 6. "Empirically validated on real-│ Full provenance audit proving footage originated from physical     │
│    world warehouse facilities"    │ facility optical sensors, total station survey logs, and building. │
└───────────────────────────────────┴────────────────────────────────────────────────────────────────────┘
```

---

## SECTION 5 — REGULATORY & STANDARDS POSITION

Evaluating perception systems intended for industrial machinery using synthetic simulation data triggers specific mandates under international safety standards and emerging artificial intelligence regulations.

### 5.1 ISO 3691-4:2023 (Driverless Industrial Trucks and Their Systems)
* **Standard Mandate**: Clause 4.2 and Annex H mandate that perception-based personnel detection systems (active opto-electronic protective devices responsive to diffuse reflection, AOPDDRs) must reliably detect human test pieces (5th percentile human to 95th percentile human in various postures) under all rated environmental operating conditions.
* **Impact of Synthetic Data**: Synthetic data does not constitute validation evidence under ISO 3691-4. Annex H requires testing under physical environmental limits: direct sunlight glare, artificial lighting variations, floor reflectance extremes, and degraded optical surfaces. 
* **Formal Position**: Synthetic benchmark evaluation provides preliminary architectural verification (Software-in-the-Loop), but **cannot satisfy the validation requirements of ISO 3691-4 Clause 5**.

### 5.2 ISO 13849-1:2023 (Safety of Machinery — Safety-Related Parts of Control Systems)
* **Standard Mandate**: Defines Performance Levels (PL a through PL e) based on Architecture Category, Mean Time to Dangerous Failure ($\text{MTTF}_{\text{D}}$), Diagnostic Coverage ($\text{DC}$), and Common Cause Failure ($\text{CCF}$).
* **Impact of Synthetic Data**: A Performance Level (e.g., PL d) **cannot be claimed from neural network inferences evaluated on synthetic data**. ISO 13849-1 requires quantitative failure mode effects analysis and systematic software verification against specification faults.
* **Formal Position**: Model H is an advisory risk-inflation layer. Even if integrated into a safety system, its safety integrity level or performance level **cannot be established using synthetic simulation benchmarks**.

### 5.3 ASME V&V 40 (Verification and Validation in Computational Modeling)
* **Standard Mandate**: Governs the credibility of computational models through verification (solving equations correctly) and validation (solving the right equations to represent physical reality), calibrated against the *Model Risk* (decision consequence).
* **Impact of Synthetic Data**: Under ASME V&V 40:
  * **Code Verification**: SATISFIED. Unit tests, hash manifests, and geometry checks prove the math is computed correctly.
  * **Calculation Verification**: SATISFIED. Pinhole homography inversion and extrinsic vector math are numerically converged.
  * **Model Validation**: **NOT ESTABLISHED**. The computational model (simulated camera in Omniverse) has not been validated against experimental physical comparator data from physical cameras.
* **Formal Position**: The credibility factor under ASME V&V 40 is limited to Code/Calculation Verification. Model Validation remains unfulfilled.

### 5.4 EU Artificial Intelligence Act (Regulation (EU) 2024/1689)
* **Articles 10 & 15 (Data Governance and Accuracy / Robustness / Cybersecurity)**:
  * Article 10(2) requires that training, validation, and testing datasets shall be relevant, sufficiently representative, and, to the best extent possible, free of errors and complete in view of the intended purpose.
  * Article 10(3) requires datasets to take into account the characteristics or aspects specific to the specific geographical, contextual, or operational setting within which the high-risk AI system is intended to be used.
  * Article 15 requires high-risk AI systems to achieve appropriate levels of accuracy, robustness, and cybersecurity, declared transparently.
* **Formal Position**: Classifying synthetic data as "authentic real-world facilities" would violate Article 10 transparency obligations and expose the organization to administrative penalties under Article 99. Re-classifying the data as synthetic, acknowledging its domain limitations, and defining a physical validation plan directly satisfies the compliance mandates of Articles 10, 11 (Technical Documentation), and 15.

### 5.5 Definitive Standards Declaration

> **"Synthetic benchmark data alone is strictly insufficient for safety validation, performance level certification, or regulatory approval under ISO 3691-4, ISO 13849-1, and EU AI Act Art. 10–15. Real-world physical validation data with verified sensor telemetry and human ground-truth annotation is legally, scientifically, and non-negotiably required."**

---

## SECTION 6 — CORRECTIVE ACTIONS & ROADMAP

To systematically remediate this provenance failure, the project shall execute the following phased roadmap:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               PHASED REMEDIATION ROADMAP                                       │
│                                                                                                │
│  PHASE 1: IMMEDIATE            PHASE 2: SHORT-TERM             PHASE 3: MEDIUM-TERM            │
│  (Days 1 - 7)                  (Month 1 - 2)                   (Month 3 - 4)                   │
│  ┌────────────────────────┐    ┌────────────────────────┐      ┌────────────────────────┐      │
│  │ • Expunge all false    │    │ • Deploy 1-camera      │      │ • Collect 10-camera    │      │
│  │   "authentic/real-     │───►│   physical pilot rig   │ ───► │   cross-facility dataset│      │
│  │   world" descriptors   │    │ • Calibrated lux meter │      │ • Dual human bounding  │      │
│  │ • Seal DP-SRGA Report  │    │ • In-situ laser survey │      │   box & track annot.   │      │
│  │ • Re-issue V3.3.3 docs │    │ • Initial sim-to-real  │      │ • Physical Model H     │      │
│  │                        │    │   gap measurement      │      │   conformance audit    │      │
│  └────────────────────────┘    └────────────────────────┘      └────────────────────────┘      │
│                                                                              │                 │
│                                                                              ▼                 │
│                                                                 PHASE 4: LONG-TERM             │
│                                                                 (Month 5 - 6)                  │
│                                                                 ┌────────────────────────┐     │
│                                                                 │ • Milestone V3.4 Gate  │     │
│                                                                 │ • ISO 3691-4 Annex H   │     │
│                                                                 │   Compliance Dossier   │     │
│                                                                 │ • Third-party cert.    │     │
│                                                                 └────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Immediate Actions (Current Milestone V3.3.3)
1. **Documentary Expungement**: Execute text replacements across all project reports, JSON manifests, and briefings as specified in Section 7.
2. **Registry & Gate Update**: Update `final_v3_3_3_gate_status.json` and release documents to reflect:
   * Data Classification: `SYNTHETIC_BENCHMARK_SIMULATION`
   * Benchmark Environment: `NVIDIA_OMNIVERSE_COSMOS_TRANSFER`
   * Mathematical Pipeline Status: `VERIFIED_IN_SIMULATION`
   * Real-World Generalization: `UNTESTED_PENDING_PHYSICAL_DATA`
3. **Internal Governance Briefing**: Brief all engineering and research personnel on the strict prohibition against conflating high-fidelity simulation renders with physical camera footage.

### Phase 2: Short-Term Actions (Month 1–2: Pilot Physical Deployment)
1. **Physical Sensor Test Rig**: Mount a calibrated machine vision camera (e.g., Basler or Lucid PoE CMOS) alongside a synchronized NIST-traceable digital lux meter (logging at 10 Hz) in an operating industrial loading dock or warehouse corridor.
2. **In-Situ Optical Survey**: Measure exact 3D camera coordinates and ground-plane survey markers using a total station or precision laser rangefinder; calibrate lens intrinsics using an industrial $1.5\text{m}$ checkerboard target.
3. **Sim-to-Real Empirical Residual Measurement**: Run the V3.3.3 pipeline on this physical stream and compare detection confidence, edge jitter, and bounding box stability directly against the synthetic `Warehouse_026/027` benchmarks.

### Phase 3: Medium-Term Actions (Month 3–4: Annotated Multi-Camera Dataset)
1. **Multi-Camera Capture Campaign**: Record synchronized video streams across $\ge 4$ overlapping camera views in an operational warehouse during normal production shifts.
2. **Human Ground-Truth Annotation**: Contract a professional, ISO 9001-certified data annotation vendor to generate tight 2D bounding boxes and persistent multi-camera tracking IDs across $\ge 10,000$ frames with dual-pass QA verification.
3. **Model H Input Activation**: Ingest synchronized lux logs into the pipeline, lifting the `INPUT_INSUFFICIENT` status and enabling empirical validation of $\beta_{\text{lux}} \cdot j(L)$.

### Phase 4: Long-Term Actions (Month 5–6: Certification Dossier V3.4)
1. **Formal Safety Case Dossier**: Compile the complete verification and validation dossier conforming to ISO 13849-1 (Software Safety Lifecycle) and ISO 3691-4 Annex H.
2. **Third-Party Notified Body Review**: Submit the physical empirical dataset, Model H mathematical specifications, and safety case documentation to an accredited safety auditor (e.g., TÜV SÜD or UL Solutions) for formal safety concept assessment.

---

## SECTION 7 — DOCUMENTATION CORRECTION TABLE

The following table provides the exhaustive register of erroneous phrasing across project documents, specifying the required replacement and the technical rationale:

```
┌───────────────────────────────────────────────────┬───────────────────────────────────────────────────┬───────────────────────────────────────────────────┐
│ ORIGINAL STATEMENT (ERRONEOUS)                    │ CORRECTED STATEMENT                               │ TECHNICAL & AUDIT RATIONALE                       │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "authentic, independently surveyed warehouse      │ "high-fidelity, simulated warehouse environments  │ PhysicalAI-SmartSpaces is synthetically generated │
│ facilities"                                       │ rendered in NVIDIA Omniverse"                     │ via Omniverse; no physical survey was conducted.  │
│ [V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md, L15]       │                                                   │                                                   │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "real-world test captures"                        │ "synthetic benchmark video sequences"             │ Official NVIDIA dataset card states: "synthetically│
│ [RUN_003_FORENSIC_AUDIT/forensic_audit_report.md] │                                                   │ generated with Omniverse and Cosmos Transfer."    │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "independently surveyed"                          │ "simulation-derived with virtual calibration      │ Extrinsics and intrinsics are virtual scene graph │
│ [Multiple occurrences across reports]             │ matrices"                                         │ transforms, not total-station physical surveys.   │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "In authentic logistics facilities, cameras are   │ "In realistic simulated warehouse layouts, cameras│ The depression angle was observed in a synthetic  │
│ mounted on structural ceiling beams..."           │ are positioned with shallow depression angles..." │ 3D scene model, not verified across physical hubs.│
│ [V3_3_3_CROSS_SCENE_FORENSIC_REPORT.md, L55]       │                                                   │                                                   │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "using authentic, multi-camera warehouse          │ "using multi-camera synthetic benchmark sequences │ Eliminates misleading authenticity claims in the  │
│ recordings from NVIDIA PhysicalAI-SmartSpaces"    │ from the NVIDIA PhysicalAI-SmartSpaces benchmark" │ RUN_003 report.                                   │
│ [EXP_333_01_RUN_003_REPORT.md, L17]              │                                                   │                                                   │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "7-camera real-world benchmark NVIDIA             │ "7-camera synthetic benchmark NVIDIA              │ Eliminates false "real-world" claim in the        │
│ PhysicalAI-SmartSpaces (Warehouse_027)"           │ PhysicalAI-SmartSpaces (Warehouse_027)"           │ RUN_004 report.                                   │
│ [EXP_333_01_RUN_004_REPORT.md, L18]              │                                                   │                                                   │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "Warehouse_026 is an authentic test capture"      │ "Warehouse_026 is an Omniverse synthetic test     │ Corrects false verification claim in audit        │
│ [RUN_003_FORENSIC_AUDIT/audit_manifest.json, L21] │ scene"                                            │ manifest.                                         │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "NVIDIA PhysicalAI-SmartSpaces authentic          │ "NVIDIA PhysicalAI-SmartSpaces synthetic CAD      │ Corrects ODD facility condition record.           │
│ warehouse; specific building identity unpublished"│ warehouse scene model"                            │                                                   │
│ [odd_observation_ledger.json, L73]                │                                                   │                                                   │
├───────────────────────────────────────────────────┼───────────────────────────────────────────────────┼───────────────────────────────────────────────────┤
│ "The overall repository contains predominantly    │ "The PhysicalAI-SmartSpaces benchmark is entirely │ Corrects the erroneous claim that test scenes were│
│ synthetic data; however, Warehouse_026/027 are    │ synthetic; test scenes are rendered simulations   │ real-world exceptions.                            │
│ authentic real-world test captures"               │ with ground truth withheld."                      │                                                   │
│ [official_source_provenance.json, L17]            │                                                   │                                                   │
└───────────────────────────────────────────────────┴───────────────────────────────────────────────────┴───────────────────────────────────────────────────┘
```

---

## CONCLUDING SAFETY ASSURANCE STATEMENT

The voluntary execution of this Data Provenance and Sim-to-Real Gap Assessment confirms that the Safety Backfire AI project operates under uncompromising scientific integrity. 

By formally expunging all unverified real-world claims and accurately classifying the NVIDIA PhysicalAI-SmartSpaces evaluations as **Software-in-the-Loop Synthetic Benchmarks**, we:
1. Prevent catastrophic liability associated with premature safety claims under ISO 3691-4 and ISO 13849-1;
2. Comply fully with the data governance and transparency mandates of Articles 10 and 15 of the EU AI Act;
3. Clarify precisely what was accomplished (rigorous mathematical, geometric, and pipeline scalability verification across 11 synchronized camera streams); and
4. Establish an indisputable, audit-proof mandate for physical data acquisition in Milestone V3.4.

**Document Status**: APPROVED & SEALED  
**Classification**: CANONICAL DATA PROVENANCE BASELINE  
**Effective Date**: 2026-09-28
