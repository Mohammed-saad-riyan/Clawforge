# Validated Applications

ClawForge has generated Flutter applications that were persisted as GitHub repositories and run on a physical Android device. This page is the public evidence ledger for representative outputs.

The current evidence set contains two very different applications: a multi-mode scientific calculator and a real-time arcade game. That difference matters because it shows the pipeline producing both stateful utility software and frame-driven interactive behavior rather than repeatedly generating the same CRUD template.

## Evidence standard

For each application, this ledger separates what is publicly inspectable from what still needs to be published. No formatter, analyzer, test, build or repair-loop result is marked as passed unless the corresponding run output is available.

## Application 1: Scientific Calculator

| Field | Evidence |
|---|---|
| Product brief | Multi-mode calculator covering basic, scientific and advanced mathematical workflows |
| Generated repository | [Mohammed-saad-riyan/calci](https://github.com/Mohammed-saad-riyan/calci) |
| Target | Android |
| Repository materialized | Verified |
| Physical-device execution | Verified from recorded device run |
| Format gate | Historical result not yet published |
| Static analysis gate | Historical result not yet published |
| Tests | Historical result not yet published |
| Build gate | App installation/run proves a build artifact existed; command output not yet published |
| Repair iterations | Historical trace not yet published |

### What ClawForge generated

The generated Flutter project declares a scientific-calculator product and uses a non-trivial application stack including Riverpod, GoRouter, Drift, Dio, Freezed, JSON serialization and `math_expressions`.

The recorded physical-device run shows a dark Material-style interface with separate calculation modes, a large expression/result area, calculator history/settings controls and a responsive keypad. The visible mode navigation includes Basic, Scientific, Calculus and additional equation-oriented functionality.

This is useful evidence for ClawForge because the output is not only a repository skeleton: the application was installed, launched and interacted with on Android.

### Public implementation evidence

The generated repository's `pubspec.yaml` declares:

- Flutter >= 3.16 and Dart >= 3.2;
- `flutter_riverpod` for state management;
- `go_router` for navigation;
- Drift and SQLite packages for persistence;
- `math_expressions` for expression handling;
- Freezed and JSON code generation;
- `very_good_analysis` and Flutter test tooling.

### Device evidence

A supplied device recording shows the calculator installed alongside the other generated application and then running interactively on Android. A repository-hosted compressed clip or screenshot set should be added under:

```text
docs/assets/validated-apps/scientific-calculator/
```

### Known evidence gap

The generated repository and physical-device execution are verified. The original ClawForge run trace and exact validator command outputs have not yet been published, so this page does not claim first-pass success, analyzer success, test success or a specific repair count.

---

## Application 2: Flappy-Style Arcade Game

| Field | Evidence |
|---|---|
| Product brief | A smooth Flappy-style game with randomized obstacles and continuous score-driven gameplay |
| Generated repository | [Mohammed-saad-riyan/flappygame01](https://github.com/Mohammed-saad-riyan/flappygame01) |
| Target | Android |
| Repository materialized | Verified |
| Physical-device execution | Verified from recorded device run |
| Format gate | Historical result not yet published |
| Static analysis gate | Historical result not yet published |
| Tests | Historical result not yet published |
| Build gate | App installation/run proves a build artifact existed; command output not yet published |
| Repair iterations | Historical trace not yet published |

### What ClawForge generated

The generated application is a real-time mobile game rather than a form-based product. The physical-device run shows:

- continuous character motion;
- tap-driven gameplay;
- randomized pipe obstacles;
- collision-sensitive progression;
- a live score counter;
- custom image assets and a complete game scene.

The generated Flutter project also declares Riverpod, GoRouter, Drift, Dio, Flutter Animate, Freezed and code-generation tooling. Its asset configuration includes dedicated image and icon directories.

### Why this output matters

The calculator and game exercise different engineering paths. The calculator is dominated by expression/state handling and mode-driven UI. The game requires continuous rendering, timing, input response, collision behavior and randomized obstacle flow.

Producing both is stronger evidence of a general application-generation workflow than producing several visually different CRUD dashboards.

### Device evidence

The supplied recording shows the game launched from an Android home screen, running through multiple obstacles and incrementing the score during live play. A repository-hosted compressed clip or screenshot set should be added under:

```text
docs/assets/validated-apps/flappy-game/
```

### Known evidence gap

The generated repository and physical-device execution are verified. The original ClawForge run trace and exact validator outputs still need to be published.

---

## Cross-application physical-device evidence

A single supplied Android recording shows:

1. the generated Flappy-style game installed and running through active gameplay;
2. the generated scientific calculator installed and accepting interaction;
3. both applications present as installed apps on the same physical device.

This is end-to-end evidence that ClawForge outputs progressed beyond model text and repository creation into executable mobile applications.

## Next evidence to publish

The next reconstruction step is to add one fresh, fully traced generation run where every stage is captured from requirements through validation. That run should include:

1. original product requirements;
2. architect output and file manifest;
3. representative coder/reviewer actions;
4. exact validator commands and exit codes;
5. repair iterations, if any;
6. generated GitHub repository and final commit;
7. physical-device installation and run.

## Portfolio interpretation

A generated repository proves code persistence. A successful Flutter toolchain run proves objective engineering gates. A physical-device run proves the application moved beyond generated text and executed in its target environment. The current public evidence strongly establishes repository generation and device execution; the remaining task is to publish validator traces with the same level of rigor.