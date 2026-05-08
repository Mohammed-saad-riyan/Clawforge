# ClawForge Code Review Report

**Date**: April 2026
**Scope**: Full backend + frontend integration review

---

## Executive Summary

Conducted a comprehensive code review of the ClawForge system, including:
- Docker Validator implementation
- Backend-Frontend API integration
- Project page routing
- Iterative development (chat) interface

**Issues Found**: 4
**Issues Fixed**: 4
**Status**: All critical issues resolved

---

## Issues Found and Fixed

### Issue 1: 404 Error on Dashboard → Project Links

**Severity**: High
**Location**: `apps/web/app/dashboard/page.tsx`

**Problem**: Dashboard linked to `/projects/${project.id}` (plural) but the actual route is `/project/[id]` (singular).

**Root Cause**: Inconsistent route naming between dashboard links and actual page location.

**Fix Applied**:
```tsx
// Before
href={`/projects/${project.id}`}

// After
href={`/project/${project.id}`}
```

**File**: `apps/web/app/dashboard/page.tsx` line 254

---

### Issue 2: Missing Dashboard API Route in Frontend

**Severity**: Medium
**Location**: `apps/web/app/api/v1/dashboard/`

**Problem**: Dashboard page fetches from `/api/v1/dashboard` but no Next.js API route existed to proxy this to the backend.

**Root Cause**: Frontend API route was never created; dashboard would fail to load.

**Fix Applied**: Created new file `apps/web/app/api/v1/dashboard/route.ts`

```typescript
export async function GET(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': user.id,
    },
  });

  const result = await response.json();
  return NextResponse.json(result);
}
```

---

### Issue 3: Incomplete ProjectDetail Model

**Severity**: Medium
**Location**: `apps/api/clawforge/models/workflow.py`

**Problem**: `ProjectDetail` model was missing fields required by the frontend:
- `target_users`
- `features`
- `ui_design`
- `messages`
- `full_spec`

**Root Cause**: Model was created before iterative development feature was fully designed.

**Fix Applied**:
```python
class ProjectDetail(BaseModel):
    project_id: str
    app_name: str
    app_idea: str
    target_users: str = ""        # Added
    features: str = ""            # Added
    ui_design: str = ""           # Added
    github_repo: str = ""
    files: list[dict[str, str]] = Field(default_factory=list)
    messages: list[dict[str, Any]] = Field(default_factory=list)  # Added
    full_spec: dict[str, Any] = Field(default_factory=dict)       # Added
    message_count: int = 0
    iteration_count: int = 0
    total_cost_cents: int = 0
    created_at: str
    updated_at: str
```

---

### Issue 4: Incomplete Project API Response

**Severity**: Medium
**Location**: `apps/api/clawforge/main.py`

**Problem**: The `/api/v1/projects/{project_id}` endpoint didn't return all the fields the frontend expected.

**Fix Applied**: Updated the endpoint to return all fields:
```python
return ProjectDetail(
    project_id=project.project_id,
    app_name=project.app_name,
    app_idea=project.app_idea,
    target_users=getattr(project, 'target_users', ''),    # Added
    features=getattr(project, 'features', ''),            # Added
    ui_design=getattr(project, 'ui_design', ''),          # Added
    github_repo=project.github_repo,
    files=project.files,
    messages=[...],                                        # Added
    full_spec=getattr(project, 'full_spec', {}),          # Added
    ...
)
```

---

## Architecture Review

### Backend Structure (FastAPI)

```
apps/api/clawforge/
├── main.py              # FastAPI app with all endpoints
├── agents/              # AI agents (Planner, Coder, Refiner, etc.)
├── validator/           # NEW: Docker-based validation
│   ├── docker_validator.py
│   ├── error_parser.py
│   └── validation_loop.py
├── graph/               # LangGraph workflow
│   └── workflow.py
├── storage/             # Project persistence
│   └── project_store.py
├── models/              # Pydantic models
│   └── workflow.py
├── dashboard/           # Dashboard metrics
└── webhooks/            # GitHub webhooks
```

### Frontend Structure (Next.js)

```
apps/web/
├── app/
│   ├── page.tsx                    # Main workflow page
│   ├── dashboard/page.tsx          # Dashboard
│   ├── project/[id]/page.tsx       # Project detail + chat
│   ├── (auth)/                     # Auth pages
│   └── api/
│       ├── workflow/run/route.ts   # Workflow execution
│       ├── projects/               # Project CRUD
│       │   ├── route.ts
│       │   └── [id]/
│       │       ├── route.ts
│       │       ├── chat/route.ts
│       │       ├── files/route.ts
│       │       └── push/route.ts
│       └── v1/dashboard/route.ts   # NEW: Dashboard proxy
├── components/
│   └── project/
│       ├── file-tree.tsx           # File browser
│       ├── code-viewer.tsx         # Code display
│       └── project-chat.tsx        # Chat interface
└── lib/stores/
    ├── auth-store.ts
    ├── github-store.ts
    ├── project-store.ts
    └── workflow-store.ts
```

---

## API Endpoints

### Workflow Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/workflow/run` | Execute full workflow |

### Project Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/projects` | List all projects |
| GET | `/api/v1/projects/{id}` | Get project details |
| POST | `/api/v1/projects/{id}/chat` | Chat for refinements |
| GET | `/api/v1/projects/{id}/files` | Get all files |
| POST | `/api/v1/projects/{id}/push` | Push to GitHub |
| DELETE | `/api/v1/projects/{id}` | Delete project |

### Dashboard Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/dashboard` | Get dashboard metrics |
| GET | `/api/v1/dashboard/projects/{id}/metrics` | Project metrics |
| GET | `/api/v1/dashboard/cost-breakdown` | Cost by day |

---

## New Features Implemented

### 1. Docker Validator Service

**Purpose**: Validate Flutter code before pushing to GitHub

**Components**:
- `DockerValidator`: Manages warm Docker container with Flutter SDK
- `ValidationLoop`: Orchestrates validate → fix → repeat cycle (max 3 iterations)
- Error parsers for `dart analyze`, `flutter pub get`, `build_runner`

**Workflow Integration**:
```
finalize_spec → generate_code → evaluate_code → validate_code → publish_github
                                                     ↑
                                              NEW: Docker validation
```

### 2. Iterative Development Interface

**Purpose**: Allow users to refine generated apps through chat

**Components**:
- `ProjectChat`: Chat interface with suggestion prompts
- `FileTree`: File browser with missing file indicators
- `CodeViewer`: Syntax-highlighted code display
- `RefinerAgent`: AI agent for code modifications

---

## Test Results

### Backend Module Tests
```
✅ Validator module OK
✅ Agents module OK
✅ Workflow module OK
✅ Storage module OK
✅ Models module OK
✅ Main FastAPI app OK
```

### Frontend TypeScript Check
```
✅ No TypeScript errors
```

---

## Recommendations

### Immediate (Before Production)

1. **Add unit tests** for Docker validator
2. **Implement push to GitHub** in project detail page (currently returns "not yet implemented")
3. **Add error boundaries** in React components

### Short-term

1. **Database migration**: Replace file-based storage with PostgreSQL
2. **Rate limiting** on API endpoints
3. **Logging**: Add structured logging with correlation IDs

### Long-term

1. **WebSocket support** for real-time validation status
2. **Caching layer** for frequently accessed projects
3. **Multi-tenant isolation** with user-scoped data

---

## Files Modified

| File | Change |
|------|--------|
| `apps/web/app/dashboard/page.tsx` | Fixed project link routes |
| `apps/web/app/api/v1/dashboard/route.ts` | Created new file |
| `apps/api/clawforge/models/workflow.py` | Added missing fields to ProjectDetail |
| `apps/api/clawforge/main.py` | Updated project API response |
| `apps/api/clawforge/validator/*` | New validator module (3 files) |
| `apps/api/clawforge/graph/workflow.py` | Added validation step |
| `apps/api/clawforge/agents/refiner.py` | Added auto-fix mode |
| `apps/api/clawforge/agents/__init__.py` | Export RefinerAgent |

---

## Running the Application

### Prerequisites
```bash
# Pull Flutter Docker image
docker pull ghcr.io/cirruslabs/flutter:stable

# Start warm container
docker run -d \
  --name clawforge-flutter-validator \
  -v /tmp/clawforge-workspaces:/workspaces \
  ghcr.io/cirruslabs/flutter:stable \
  tail -f /dev/null
```

### Start Backend
```bash
cd apps/api
python -m clawforge.main
```

### Start Frontend
```bash
cd apps/web
pnpm dev
```

### Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Conclusion

All identified issues have been fixed. The system now properly:
1. Routes from dashboard to project pages
2. Provides complete project data to the frontend
3. Supports iterative development via chat interface
4. Validates code using Docker before pushing to GitHub

The codebase is in good shape for further development and testing.
