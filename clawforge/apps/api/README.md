# ClawForge API

FastAPI backend for ClawForge workflow orchestration - an AI-powered Flutter app generator.

## Features

### Core Features
- LangGraph workflow for Flutter app generation
- Multi-agent architecture (Router, Planner, Coder, Claws, GitHub)
- Hybrid LLM support (Claude + Ollama)
- RAG with Flutter code examples
- GitHub integration for repository management

### Phase 4 Features
- **Dashboard & Metrics**: Project statistics, cost tracking, activity timelines
- **GitHub Webhooks**: Auto-analysis of issues, PR acknowledgment, push tracking
- **Autofixers**: Automated code repair with configurable thresholds

### Phase 5 Features
- **Supabase Integration**:
  - Authentication (signup, login, logout, password reset)
  - PostgreSQL database with RLS policies
  - Real-time subscriptions support
- **Component Library**: Pre-built Flutter components (similar to shadcn/ui)
  - Auth screens (login, signup, forgot password)
  - Navigation (bottom nav, drawer, tab bar)
  - Settings (settings screen, profile, theme provider)
  - Backend integrations (Supabase, Firebase, REST API clients)

## Development

### Prerequisites
- Python 3.12+
- uv package manager
- Supabase account (for auth and database)

### Environment Setup

Create a `.env` file with:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# LLM Configuration
ANTHROPIC_API_KEY=your-anthropic-key
OLLAMA_BASE_URL=http://localhost:11434

# GitHub Configuration
GITHUB_TOKEN=your-github-token
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

### Database Setup

Run the migration SQL in your Supabase dashboard:

```bash
# The migration file is at:
# clawforge/supabase/migrations/001_initial_schema.sql
```

### Running the Server

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn clawforge.main:app --reload --port 8000
```

## API Endpoints

### Health & Status
- `GET /health` - Health check

### Workflows
- `POST /api/workflows` - Create workflow
- `GET /api/workflows/{id}` - Get workflow status
- `POST /api/workflows/{id}/steps/{step}` - Submit step input

### Authentication (Phase 5)
- `POST /api/v1/auth/signup` - Create new account
- `POST /api/v1/auth/login` - Sign in with email/password
- `POST /api/v1/auth/logout` - Sign out (requires auth)
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/forgot-password` - Request password reset

### Dashboard (Phase 4)
- `GET /api/v1/dashboard/stats` - Get project statistics
- `GET /api/v1/dashboard/projects/{id}/metrics` - Get project metrics
- `GET /api/v1/dashboard/activity` - Get recent activity

### GitHub Webhooks (Phase 4)
- `POST /api/v1/webhooks/github` - GitHub webhook endpoint
- `GET /api/v1/webhooks/github/events` - List webhook events
- `GET /api/v1/webhooks/github/events/{id}` - Get specific event

### Component Library (Phase 5)
- `GET /api/v1/components` - List all components
- `GET /api/v1/components/{id}` - Get component details
- `GET /api/v1/components/category/{category}` - List by category
- `GET /api/v1/components/search?q={query}` - Search components

## Component Library

The component library provides pre-built Flutter components that are copied as source code (similar to shadcn/ui approach).

### Categories

| Category | Components |
|----------|------------|
| **Auth** | Login Screen, Signup Screen, Forgot Password, Auth Provider, Auth Wrapper |
| **Navigation** | Bottom Nav Scaffold, Drawer Scaffold, Tab Bar Scaffold |
| **Settings** | Settings Screen, Profile Screen, Theme Provider |
| **Backend** | Supabase Client, Supabase Auth Provider, Supabase Database Service, Firebase Core, Firebase Auth Provider, Firestore Service, REST API Client, API Interceptors |

### Usage

Components include:
- Complete Dart/Flutter source files
- Required pubspec.yaml dependencies
- Component dependencies (e.g., login screen requires auth provider)

## Architecture

```
clawforge/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── supabase/            # Supabase integration
│   ├── client.py        # Supabase client
│   ├── auth.py          # Auth operations
│   ├── database.py      # Database operations
│   └── migrations/      # SQL migrations
├── components/          # Component library
│   ├── library.py       # Component registry
│   ├── auth.py          # Auth components
│   ├── navigation.py    # Navigation components
│   ├── settings.py      # Settings components
│   └── backend.py       # Backend integration components
├── dashboard/           # Dashboard module
│   └── metrics.py       # Metrics tracking
├── webhooks/            # Webhook handlers
│   └── github.py        # GitHub webhook processing
├── agents/              # LangGraph agents
├── tools/               # Agent tools
├── rag/                 # RAG system
└── storage/             # Storage abstraction
```

## Security

- All database tables use Row Level Security (RLS)
- Service key used only for server-side operations
- User data isolated by user_id policies
- Webhook signatures verified with HMAC-SHA256

## License

Private - ClawForge
