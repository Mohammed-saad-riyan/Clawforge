# End-to-End Agent Trace

Capture one real ClawForge generation run here. The goal is to prove orchestration, tool use, validation and recovery rather than only showing the final UI.

## Run metadata

| Field | Value |
|---|---|
| Date | `<date>` |
| ClawForge commit | `<sha>` |
| Model/provider | `<model>` |
| Generated repository | `<repository>` |
| Target device | `<device>` |
| Total duration | `<measured duration>` |

## 1. Product requirements

Record the actual app idea, target users, requested features and UI direction.

## 2. Architect output

Capture the architecture plan, screen list, navigation, data model, state-management choice and file manifest.

## 3. Coder actions

Record representative file operations and important implementation decisions. Avoid dumping every token of model output.

## 4. Reviewer findings

Record issues found before deterministic validation and the changes they triggered.

## 5. Validator run

Capture the exact commands, exit codes and concise diagnostics for the checks that actually ran.

```text
format:  <command> -> <exit code>
analyze: <command> -> <exit code>
tests:   <command> -> <exit code>
build:   <command> -> <exit code>
```

## 6. Repair loop

If validation failed, record:

1. the failing gate;
2. the relevant diagnostic;
3. the repair context returned to the implementation stage;
4. the changed files;
5. the next validation result.

If the run passed first time, say so. Do not manufacture a repair.

## 7. GitHub output

Link the generated repository and identify the final commit produced by the run.

## 8. Physical-device proof

Add a screenshot or short video of the generated application running on the target device.

## 9. Result summary

| Metric | Result |
|---|---|
| First-pass success | Yes / No |
| Repair iterations | `<count>` |
| Final validation | Pass / Fail |
| Repository created | Yes / No |
| Ran on physical device | Yes / No |

## Evidence checklist

- [ ] user requirements
- [ ] architecture output
- [ ] representative tool/file operations
- [ ] reviewer output
- [ ] validator commands and exit codes
- [ ] repair history if applicable
- [ ] generated GitHub repository
- [ ] application running on a device