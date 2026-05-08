# ClawForge

A visual AI workflow builder that generates production-ready Flutter MVPs through an intuitive drag-and-drop interface.

## Architecture

```
clawforge/
├── apps/
│   ├── web/          # Next.js frontend with React Flow canvas
│   └── api/          # FastAPI backend with LangGraph workflow
├── packages/
│   ├── ui/           # Shared UI components
│   ├── types/        # TypeScript type definitions
│   └── config/       # Shared configs (ESLint, TypeScript, Tailwind)
└── docker-compose.yml
```

## Tech Stack

- **Frontend**: Next.js 15, React Flow (Xyflow), Zustand, TailwindCSS
- **Backend**: FastAPI, LangGraph, Python 3.12
- **LLM**: Claude (Haiku/Sonnet) via Anthropic API, Ollama (local)
- **Database**: SQLite (dev), ChromaDB (RAG)
- **Build**: Turborepo, pnpm, uv

## Quick Start

### Prerequisites

- Node.js 22+
- pnpm 9+
- Python 3.12+
- uv (Python package manager)
- Ollama (optional, for local LLM)
- Docker & Docker Compose (optional)

### Development Setup

1. **Clone and install dependencies:**
   ```bash
   cd clawforge
   make install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Pull local LLM model (optional):**
   ```bash
   make ollama-pull
   ```

4. **Start development servers:**
   ```bash
   make dev
   ```

   Or run separately:
   ```bash
   make web   # http://localhost:3000
   make api   # http://localhost:8000
   ```

### Docker Development

```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

## Workflow Steps

ClawForge guides you through 10 steps to generate a Flutter app:

1. **App Idea** - Define your concept and value proposition
2. **Target Users** - Identify your primary users
3. **Features** - List and prioritize features
4. **UI Design** - Design screens and navigation
5. **Architecture** - Choose tech stack
6. **Backend** - Configure backend services
7. **Environment** - Set up environment variables
8. **Code Generation** - Generate Flutter code
9. **Evaluation** - Review and improve quality
10. **GitHub Publish** - Push to repository

## API Endpoints

### Workflow
- `POST /api/workflow/run` - Generate new app (full workflow)
- `GET /api/v1/config` - Get configuration

### Projects (Iterative Development)
- `GET /api/v1/projects` - List all projects
- `GET /api/v1/projects/{id}` - Get project details
- `POST /api/v1/projects/{id}/chat` - Send refinement request
- `POST /api/v1/projects/{id}/preview` - Generate web preview
- `GET /api/v1/projects/{id}/files` - Get all files
- `GET /api/v1/projects/{id}/messages` - Get chat history

### Dashboard (Phase 4.1)
- `GET /api/v1/dashboard` - Aggregate metrics
- `GET /api/v1/dashboard/projects/{id}/metrics` - Project metrics
- `GET /api/v1/dashboard/cost-breakdown` - Cost by day

### Webhooks (Phase 4.2)
- `POST /webhook/github` - GitHub webhook handler
- `POST /api/v1/webhooks/test-analysis` - Test issue analysis

### Health
- `GET /health` - Health check

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `GITHUB_TOKEN` | GitHub personal access token | Yes |
| `USE_LOCAL_LLM` | Use Ollama for routing | No |
| `MAX_COST_PER_WORKFLOW` | Cost limit in USD | No |

## License

MIT
