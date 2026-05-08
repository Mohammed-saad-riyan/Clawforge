# ClawForge Full-Loop Workflow Plan

## Current State vs. Target State

### Current Flow (Linear)
```
User Input → Planner → Coder → Claws (eval) → GitHub Push
                                    ↓
                              (one-time fix)
```
**Problems:**
- No real validation (flutter pub get, dart analyze)
- Single-pass fix, no loop
- No tracking of plan vs. actual
- No awareness of user changes after push

### Target Flow (Full Loop with Validation)
```
                    ┌─────────────────────────────────────────────────┐
                    │                   PLAN TRACKER                   │
                    │  (Monitors progress, tracks plan vs. reality)    │
                    └─────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────┐    ┌──────────┐    ┌─────────────┐    ┌───────────────────┐
│  User   │───▶│ Planner  │───▶│   Coder     │───▶│    Validator      │
│  Input  │    │  Agent   │    │   Agent     │    │   (Docker)        │
└─────────┘    └──────────┘    └─────────────┘    └───────────────────┘
                    │                                      │
                    │                              ┌───────┴───────┐
                    │                              │               │
                    │                          PASS ✓         FAIL ✗
                    │                              │               │
                    │                              ▼               ▼
                    │                        ┌──────────┐    ┌──────────┐
                    │                        │  GitHub  │    │ Refiner  │
                    │                        │   Push   │    │  Agent   │
                    │                        └──────────┘    └──────────┘
                    │                              │               │
                    │                              ▼               │
                    │                        ┌──────────┐          │
                    │                        │ Monitor  │◀─────────┘
                    │                        │ Changes  │     (loop back)
                    │                        └──────────┘
                    │                              │
                    │                     (user makes changes)
                    │                              │
                    └──────────────────────────────┘
                         (update plan, continue)
```

---

## New Components Needed

### 1. Docker Validator Service
**Purpose:** Run Flutter commands to validate generated code

**Location:** `apps/api/clawforge/validator/docker_validator.py`

**Responsibilities:**
- Start/manage Docker container with Flutter SDK
- Run validation pipeline:
  1. `flutter pub get` - Check dependencies
  2. `dart run build_runner build` - Generate .g.dart/.freezed.dart
  3. `dart analyze` - Get all errors
- Parse error output into structured format
- Return validation results

**Docker Image:** `ghcr.io/cirruslabs/flutter:stable`

**Interface:**
```python
@dataclass
class ValidationResult:
    success: bool
    stage: str  # "pub_get" | "build_runner" | "analyze"
    errors: list[ValidationError]
    warnings: list[str]
    generated_files: list[str]  # .g.dart files created
    duration_seconds: float

@dataclass
class ValidationError:
    file_path: str
    line: int
    column: int
    message: str
    severity: str  # "error" | "warning" | "info"
    code: str  # e.g., "undefined_class"

class DockerValidator:
    async def validate(self, files: list[dict]) -> ValidationResult
    async def get_container_status() -> str
```

---

### 2. Enhanced Planner Agent with Plan Tracking
**Purpose:** Create detailed plans AND track progress against them

**Location:** Update `apps/api/clawforge/agents/planner.py`

**New Responsibilities:**
- Create a **File Manifest** - List ALL files that should exist
- Define **Checkpoints** - What should be true at each stage
- Track **Plan Adherence** - Is the actual state matching the plan?
- Update plan when user changes requirements

**Output Structure:**
```python
@dataclass
class AppPlan:
    # Existing spec data
    display_name: str
    description: str
    screens: list[ScreenSpec]
    data_models: list[ModelSpec]
    providers: list[ProviderSpec]

    # NEW: File Manifest (explicit list of all expected files)
    file_manifest: list[FileManifestEntry]

    # NEW: Checkpoints
    checkpoints: list[Checkpoint]

    # NEW: Progress tracking
    current_checkpoint: int
    completed_files: list[str]
    validation_status: str  # "pending" | "passing" | "failing"

@dataclass
class FileManifestEntry:
    path: str
    type: str  # "screen" | "widget" | "provider" | "model" | "config" | "generated"
    description: str
    depends_on: list[str]  # Other files this depends on
    required: bool

@dataclass
class Checkpoint:
    name: str
    description: str
    validation_command: str  # e.g., "flutter pub get"
    expected_outcome: str
    blocking: bool  # If failed, stop workflow
```

---

### 3. Validation Loop Orchestrator
**Purpose:** Run validation → fix → re-validate loop

**Location:** `apps/api/clawforge/graph/validation_loop.py`

**Flow:**
```
                    ┌────────────────────────┐
                    │   Start Validation     │
                    │    (max 3 iterations)  │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  1. flutter pub get    │
                    └───────────┬────────────┘
                                │
                         ┌──────┴──────┐
                         │             │
                       PASS          FAIL
                         │             │
                         ▼             ▼
              ┌──────────────┐  ┌──────────────┐
              │ 2. build_    │  │ Fix pubspec  │
              │    runner    │  │ (Refiner)    │
              └──────┬───────┘  └──────┬───────┘
                     │                 │
                     │          (loop back to 1)
                     │
              ┌──────┴──────┐
              │             │
            PASS          FAIL
              │             │
              ▼             ▼
   ┌──────────────┐  ┌──────────────┐
   │ 3. dart      │  │ Just capture │
   │    analyze   │  │ .g.dart files│
   └──────┬───────┘  └──────┬───────┘
          │                 │
   ┌──────┴──────┐          │
   │             │          │
 PASS          FAIL         │
   │             │          │
   ▼             ▼          │
┌─────┐    ┌──────────┐     │
│ OK! │    │ Fix code │     │
│     │    │ (Refiner)│     │
└─────┘    └────┬─────┘     │
                │           │
         (loop back to 3)   │
                            │
                    ┌───────┴───────┐
                    │ All iterations │
                    │   exhausted    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌────────────────┐
                    │ Return current │
                    │ state + errors │
                    └────────────────┘
```

**Configuration:**
```python
VALIDATION_CONFIG = {
    "max_iterations": 3,
    "timeout_seconds": 120,
    "fail_on_warnings": False,
    "auto_fix_enabled": True,
}
```

---

### 4. Enhanced Refiner Agent with Error Context
**Purpose:** Fix specific errors based on validation output

**Location:** Update `apps/api/clawforge/agents/refiner.py`

**Input Enhancement:**
```python
class RefinerInput:
    # Existing
    message: str  # User's refinement request OR auto-generated
    conversation_history: list[ChatMessage]

    # NEW: Validation context
    validation_errors: list[ValidationError]
    error_file_contents: dict[str, str]  # Relevant files
    plan: AppPlan  # The expected plan

    # NEW: Fix mode
    mode: str  # "user_request" | "auto_fix_validation" | "auto_fix_missing"
```

**Output Enhancement:**
```python
class RefinerOutput:
    files_changed: list[dict]
    explanation: str

    # NEW
    errors_addressed: list[str]  # Which errors were fixed
    remaining_issues: list[str]  # Known but not fixed
    suggested_next_steps: list[str]
```

---

### 5. GitHub Monitor Service
**Purpose:** Watch for user changes after push

**Location:** `apps/api/clawforge/github/monitor.py`

**Responsibilities:**
- Poll for new commits on the repo
- Diff changes since last known state
- Detect what files user modified
- Trigger plan reconciliation when changes detected

**Interface:**
```python
class GitHubMonitor:
    async def get_changes_since(
        self,
        repo: str,
        since_commit: str,
        token: str
    ) -> ChangeSet

    async def reconcile_plan(
        self,
        plan: AppPlan,
        changes: ChangeSet
    ) -> PlanUpdate

@dataclass
class ChangeSet:
    commits: list[Commit]
    files_added: list[str]
    files_modified: list[str]
    files_deleted: list[str]
    diff_summary: str

@dataclass
class PlanUpdate:
    plan_changed: bool
    new_requirements_detected: list[str]
    conflicts: list[str]
    suggested_actions: list[str]
```

---

## New Workflow Graph

### Phase 1: Planning
```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│          PLANNER AGENT              │
│  • Analyze requirements             │
│  • Create file manifest             │
│  • Define checkpoints               │
│  • Output: AppPlan                  │
└─────────────────────────────────────┘
    │
    ▼
Plan Review (optional user approval)
```

### Phase 2: Code Generation
```
AppPlan
    │
    ▼
┌─────────────────────────────────────┐
│           CODER AGENT               │
│  • Generate files per manifest      │
│  • Check off completed files        │
│  • Report: generated vs. expected   │
└─────────────────────────────────────┘
    │
    ▼
Generated Files + Coverage Report
```

### Phase 3: Validation Loop (NEW)
```
Generated Files
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│              VALIDATION LOOP                             │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Docker Container (Flutter SDK)                  │    │
│  │                                                  │    │
│  │  1. flutter pub get                              │    │
│  │     └── Fix pubspec if fails                     │    │
│  │                                                  │    │
│  │  2. dart run build_runner build                  │    │
│  │     └── Commit .g.dart / .freezed.dart           │    │
│  │                                                  │    │
│  │  3. dart analyze                                 │    │
│  │     └── Parse errors → Refiner → Loop            │    │
│  │                                                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Max 3 iterations, then proceed with warnings            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Validated Files (or best-effort + error list)
```

### Phase 4: Quality & Push
```
Validated Files
    │
    ▼
┌─────────────────────────────────────┐
│           CLAWS AGENT               │
│  • Final quality evaluation         │
│  • Accessibility check              │
│  • Performance check                │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│          GITHUB AGENT               │
│  • Create/use repo                  │
│  • Push all files (including .g.dart)│
│  • Create PR with validation status │
└─────────────────────────────────────┘
    │
    ▼
Project saved for iterative development
```

### Phase 5: Monitoring & Iteration (Post-Push)
```
Project Page (User)
    │
    ├──────────────────────┐
    │                      │
    ▼                      ▼
Chat Interface      GitHub Monitor
(user prompts)      (polls for changes)
    │                      │
    │                      ▼
    │              ┌─────────────────┐
    │              │ Detect Changes  │
    │              │ • New commits   │
    │              │ • File diffs    │
    │              └────────┬────────┘
    │                       │
    └───────────┬───────────┘
                │
                ▼
        ┌─────────────────────────────┐
        │   PLAN RECONCILIATION       │
        │   • Compare with plan       │
        │   • Update plan if needed   │
        │   • Identify new work       │
        └─────────────────────────────┘
                │
                ▼
        ┌─────────────────────────────┐
        │      REFINER AGENT          │
        │   • Apply requested changes │
        │   • Generate new files      │
        │   • Run validation loop     │
        └─────────────────────────────┘
                │
                ▼
        Push updated files to GitHub
```

---

## Updated WorkflowState

```python
class WorkflowState(TypedDict):
    # ... existing fields ...

    # NEW: Plan tracking
    app_plan: AppPlan
    file_manifest: list[FileManifestEntry]
    plan_checkpoints: list[Checkpoint]
    current_checkpoint_idx: int

    # NEW: Validation state
    validation_results: list[ValidationResult]
    validation_iteration: int
    validation_passed: bool
    validation_errors: list[ValidationError]
    generated_dart_files: list[str]  # .g.dart, .freezed.dart

    # NEW: GitHub monitoring
    last_known_commit: str
    user_changes_detected: bool
    pending_reconciliation: bool

    # NEW: Loop control
    max_validation_iterations: int
    current_phase: str  # "planning" | "coding" | "validating" | "fixing" | "publishing" | "monitoring"
```

---

## Implementation Order

### Phase 1: Docker Validator (Foundation)
1. Create `validator/docker_validator.py`
2. Create `validator/error_parser.py` - Parse dart analyze output
3. Create Docker management utilities
4. Test locally with sample Flutter projects
5. **Deliverable:** Can run validation on any files, get structured errors

### Phase 2: Validation Loop
1. Create `graph/validation_loop.py`
2. Integrate with Refiner Agent for auto-fix
3. Add validation step to main workflow (after code generation)
4. **Deliverable:** Code is validated before push, errors are fixed

### Phase 3: Enhanced Planner
1. Add file manifest generation to Planner
2. Add checkpoint definition
3. Track plan adherence during workflow
4. **Deliverable:** Plan explicitly lists all expected files

### Phase 4: GitHub Monitoring
1. Create `github/monitor.py`
2. Add change detection
3. Integrate with project page for notifications
4. **Deliverable:** Detect when user makes changes

### Phase 5: Full Loop Integration
1. Connect monitoring to plan reconciliation
2. Update workflow to support multiple iterations
3. Add UI for plan tracking
4. **Deliverable:** Full self-healing loop

---

## Docker Setup

### Development (Local)
```bash
# Pull Flutter image
docker pull ghcr.io/cirruslabs/flutter:stable

# Start persistent container
docker run -d \
  --name clawforge-flutter \
  -v /tmp/clawforge-workspaces:/workspaces \
  ghcr.io/cirruslabs/flutter:stable \
  tail -f /dev/null

# Run validation
docker exec clawforge-flutter bash -c "
  cd /workspaces/project-123 && \
  flutter pub get && \
  dart run build_runner build --delete-conflicting-outputs && \
  dart analyze
"
```

### Production (Hetzner/AWS)
Same setup, just on a remote server. Container stays warm for fast execution.

---

## Success Metrics

1. **Validation Pass Rate:** % of projects that pass validation on first push
2. **Error Fix Success:** % of validation errors auto-fixed
3. **Time to Clean Build:** How long until code is error-free
4. **User Intervention Rate:** How often users need to manually fix issues
5. **Plan Adherence:** % of planned files actually generated

---

## Open Questions

1. **Container persistence:** Keep one warm container vs. spin up per project?
2. **Timeout handling:** What if validation takes too long?
3. **Partial success:** Push with warnings, or block until clean?
4. **Generated file strategy:** Commit .g.dart files or add build instructions?
5. **Monitor frequency:** How often to poll GitHub for changes?

---

## Next Steps

1. [ ] Review this plan
2. [ ] Decide on open questions
3. [ ] Start with Phase 1: Docker Validator
4. [ ] Test validation loop locally
5. [ ] Integrate into main workflow
