# Validated Applications

ClawForge has generated applications that were built and run on physical mobile devices. This page is the public evidence ledger for representative outputs.

Do not turn this into a long gallery. Select three to five applications that best demonstrate different requirements and engineering paths.

## Evidence standard

For each application, include:

- the original requirement summary;
- the generated GitHub repository;
- generation date and ClawForge commit;
- validation gates that actually ran;
- whether a repair loop was required;
- final analyzer/test/build result;
- screenshot or short recording on a physical device;
- known limitations.

## Application 1: `<name>`

| Field | Evidence |
|---|---|
| Product brief | `<one sentence>` |
| Generated repository | `<GitHub repository>` |
| ClawForge commit | `<sha>` |
| Target | Android / iOS |
| First-pass validation | Pass / Fail |
| Repair iterations | `<count>` |
| Format | Pass / Not run |
| Static analysis | Pass / Not run |
| Tests | Pass / Not run |
| Build | Pass / Not run |
| Physical device | `<device model>` |

### What ClawForge generated

Describe the screens, data model, navigation, state management and notable implementation choices.

### Validation result

Paste a concise summary of actual command results and exit codes. Do not claim checks that were not run.

### Device evidence

Add screenshots under `docs/assets/validated-apps/<app-name>/` or link a short video.

### Known limitations

Document anything unfinished or manually corrected after generation.

---

## Application 2: `<name>`

Repeat the same evidence structure.

---

## Application 3: `<name>`

Repeat the same evidence structure.

## Portfolio interpretation

A generated repository proves code persistence. A successful Flutter toolchain run proves objective engineering gates. A physical-device run proves the application moved beyond generated text and executed in its target environment. Together, those artifacts are the strongest evidence for ClawForge.