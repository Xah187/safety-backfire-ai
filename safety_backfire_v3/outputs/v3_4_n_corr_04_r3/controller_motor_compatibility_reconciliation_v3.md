# V3.4-N-CORR-04-R3 — Controller / Motor Compatibility Reconciliation (v3)

**Document:** `outputs/v3_4_n_corr_04_r3/controller_motor_compatibility_reconciliation_v3.md`
**Supersedes:** `r2_r1/controller_compatibility_reconciliation_v2.md`

```text
MOTOR_CONTROLLER_COMPATIBILITY  = BLOCKED
VEHICLE_FUNCTIONAL_SAFETY_CLAIM = NOT_ESTABLISHED
```

```text
MODEL_H = FROZEN | PRODUCTION_MODEL = UNCHANGED | FIELD_DATA = ZERO
PHYSICAL_CAPTURE_AUTHORIZATION = NOT_GRANTED | RESEARCH_DAQ_ACTUATION_AUTHORITY = ZERO
```

**Source note.** External statements are from web search summaries (2026-10-05): Curtis pages, distributor and third-party pages (`EXTERNAL_VIA_SEARCH_SUMMARY`). No primary Curtis manual or datasheet is archived in the repository. Nothing here is a verified statement about the *physical unit*.

---

## 1. The logic is rewritten: no categorical statements either way

This document does **not** assert:

* that a 1238E **cannot** control a PMSM (no such negative is evidenced);
* that a PMSM **requires** any specific absolute-angle sensor — rotor-position feedback requirements are a property of the *exact controller configuration and control method*, not a universal property of "PMSM";
* that any 1238E can or does control the project's motor.

It asserts only that the evidence needed to decide for the **exact unit configuration** is absent.

## 2. Documentation conflict (classified)

| Source class | Statement (as found) | Note |
| :--- | :--- | :--- |
| Current official Curtis product listing | 1238E is an **AC-induction** controller; **SE** variants have separate model documentation and may support induction/PM-AC (R2-R1 finding, retained) | current-generation naming |
| Distributor / third-party / older family manuals (`1232E/34E/36E/38E & 1232SE/34SE/36SE/38SE` family manual references) | E/SE family described as capable of induction **and** surface-PM motors | possibly different documentation generation or software/option configuration |

```text
DOCUMENTATION_CONFLICT_CLASS = DOCUMENTATION_GENERATION_AND_CONFIGURATION_RECONCILIATION
```

This is **not resolvable from documents alone**. The same part family can be documented differently across generations, and the *enabled* motor-control capability is a function of the unit's software/option set and parameter configuration.

## 3. What must be established for the exact unit (all currently missing)

| Dimension | Why it is separate | Repository evidence | Status |
| :--- | :--- | :--- | :---: |
| **Exact controller model** | Dash number/revision determine voltage/current class and variant (`1238E-5421` is the name used in project documents; no nameplate evidence) | document text only | `UNVERIFIED` |
| **Firmware / software generation** | Capability and documentation generation depend on it | none | `MISSING` |
| **Enabled motor-control capability** | A hardware family can have motor-type support enabled/disabled by software or option | none | `MISSING` |
| **VCL / application configuration** | Vehicle-specific logic can change control behaviour, including shutdown/STO handling | none | `MISSING` |
| **Motor type** | Vehicle documentation cites a 5.5 kW **PMSM**; no motor nameplate/datasheet retrieved | secondary vehicle documentation | `UNVERIFIED` |
| **Motor parameterization** | Parameter set must match the motor and control method | none | `MISSING` |
| **Commutation / alignment evidence** | *If* the configuration uses it, alignment evidence appropriate to that configuration is required; the type of feedback is **not** presumed here | none | `MISSING` |

`MOTOR_CONTROLLER_COMPATIBILITY = BLOCKED` unless the exact unit configuration (all rows) is independently established. R2-R1 text that listed "encoder commutation alignment logs" and "Curtis PMSM software license" as closure items presumed a feedback type and a licensing scheme; those items are replaced by the table above.

## 4. Consequences for other R3 documents

* Rebound/back-EMF mechanisms that exist only for a spinning permanent-magnet rotor are **candidates conditional on the motor type** (`persistence_semantics_v5.md` §6).
* `tau_eff` cannot be attributed to a controller/motor combination; its generalization stays prohibited.

## 5. Safety classification: expunged unless exact-unit documentation applies

* "SIL 3 / PL e" for the controller: **ungrounded; expunged** (R2-R1 finding retained).
* R2-R1 also wrote that "certain Curtis documents state that 1238E architecture can support up to … PL d … SIL 2 for specific drive-inhibit sub-functions". That sentence is **withdrawn**: it repeated an unattributed claim; the document, edition and exact function were never identified.
* External pages describe a family-level dual-microprocessor architecture and EN ISO 13849-1 compliance claims. Classification: `MANUFACTURER_FAMILY_LEVEL_STATEMENT — NOT TRANSFERABLE`. It is **not** a claim about `1238E-5421`, a drive-inhibit function, or this vehicle.
* A PL/SIL statement may be cited only if the **manufacturer's safety documentation for the exact model/variant, firmware and function** is in the repository and applies. None is.
* Component-level manufacturer claims (if ever established) and a **vehicle-level functional-safety claim** are separate; no vehicle-level claim is made:

```text
COMPONENT_LEVEL_SAFETY_CLAIM_FOR_EXACT_UNIT = NOT_ESTABLISHED
VEHICLE_FUNCTIONAL_SAFETY_CLAIM             = NOT_ESTABLISHED
ISO_13849_PL / IEC_61508_SIL                = NOT_CLAIMED
```

## 6. Withdrawn / downgraded R2-R1 statements

| R2-R1 statement | Disposition |
| :--- | :--- |
| "customized OEM firmware or proprietary VCL packages can implement synchronous d-q control on certain 1238E hardware revisions with appropriate encoder/Hall interfaces" | **Withdrawn** — asserted "industrial practice" without a source; presumes feedback hardware |
| "Certain Curtis documents state … PL d, SIL 2" | **Withdrawn** — unattributed (Section 5) |
| "Clarify motor type … If PMSM, provide Curtis PMSM software license, encoder commutation alignment logs …" | **Replaced** by the dimension table (Section 3) |

## 7. Status

```text
CURTIS_1238E_STANDARD_MOTOR_TYPE (current official documentation) = AC_INDUCTION
MOTOR_CONTROLLER_COMPATIBILITY                                    = BLOCKED
EXACT_UNIT_CONFIGURATION                                          = NOT_ESTABLISHED
```
