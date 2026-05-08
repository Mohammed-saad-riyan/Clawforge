# ClawForge Instruction Manual
## AI-Powered Flutter Application Generator

**Version 1.0**
**Last Updated: May 2025**

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Requirements](#2-system-requirements)
3. [Installation Guide](#3-installation-guide)
4. [Configuration](#4-configuration)
5. [Getting Started](#5-getting-started)
6. [Using ClawForge](#6-using-clawforge)
7. [Understanding the Workflow](#7-understanding-the-workflow)
8. [Generated Project Structure](#8-generated-project-structure)
9. [Running Your Generated App](#9-running-your-generated-app)
10. [Troubleshooting](#10-troubleshooting)
11. [Frequently Asked Questions](#11-frequently-asked-questions)
12. [Technical Reference](#12-technical-reference)

---

## 1. Introduction

### 1.1 What is ClawForge?

ClawForge is an AI-powered platform that generates production-ready Flutter applications from natural language descriptions. Simply describe your app idea, specify your target users, list desired features, and define your UI preferences—ClawForge handles the rest.

### 1.2 Key Features

- **Natural Language Input**: Describe your app in plain English
- **Multi-Agent AI System**: Specialized AI agents for different aspects of development
- **Production-Ready Code**: Clean architecture with Riverpod, GoRouter, and Drift
- **GitHub Integration**: Automatic repository creation and code deployment
- **Flutter Best Practices**: Generated code follows industry standards
- **Docker Validation**: Code is validated in isolated Flutter environment

### 1.3 How It Works

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  AI Processing   │───▶│  GitHub Repo    │
│  (Description)  │    │  (Multi-Agent)   │    │  (Flutter App)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 2. System Requirements

### 2.1 For Running ClawForge (Development/Self-Hosted)

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Operating System** | Windows 10, macOS 11, Ubuntu 20.04 | macOS 13+, Ubuntu 22.04 |
| **RAM** | 8 GB | 16 GB |
| **Storage** | 10 GB free | 20 GB free |
| **Node.js** | v18.0.0 | v20.0.0+ |
| **Python** | 3.11 | 3.12+ |
| **Docker** | 20.10+ | Latest |

### 2.2 For Using Generated Flutter Apps

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Flutter SDK** | 3.16.0 | 3.22.0+ |
| **Dart SDK** | 3.2.0 | 3.4.0+ |
| **Android Studio** | 2022.3 | Latest |
| **Xcode (macOS)** | 14.0 | 15.0+ |

### 2.3 Required Accounts

- **GitHub Account**: For repository creation and code storage
- **Supabase Account**: For user authentication (optional for self-hosted)
- **Anthropic API Key**: For Claude AI access (backend)

---

## 3. Installation Guide

### 3.1 Prerequisites Installation

#### Step 1: Install Node.js
```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20

# Verify installation
node --version  # Should show v20.x.x
```

#### Step 2: Install Python with uv
```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

#### Step 3: Install pnpm
```bash
npm install -g pnpm

# Verify installation
pnpm --version
```

#### Step 4: Install Docker
```bash
# macOS (using Homebrew)
brew install --cask docker

# Ubuntu
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Start Docker and verify
docker --version
```

### 3.2 ClawForge Installation

#### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/clawforge.git
cd clawforge
```

#### Step 2: Install Frontend Dependencies
```bash
cd apps/web
pnpm install
```

#### Step 3: Install Backend Dependencies
```bash
cd ../api
uv sync
```

#### Step 4: Pull Docker Images
```bash
# Pull Flutter validation image
docker pull ghcr.io/cirruslabs/flutter:stable
```

---

## 4. Configuration

### 4.1 Environment Variables

#### Frontend Configuration (apps/web/.env.local)

Create the file `apps/web/.env.local`:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend API URL
API_BASE_URL=http://localhost:8000

# GitHub OAuth (optional - for OAuth flow)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

#### Backend Configuration (apps/api/.env)

Create the file `apps/api/.env`:

```env
# Anthropic API Key (Required)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Docker Configuration
DOCKER_FLUTTER_IMAGE=ghcr.io/cirruslabs/flutter:stable

# Supabase Configuration (for project storage)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### 4.2 GitHub Personal Access Token Setup

ClawForge requires a GitHub Personal Access Token (PAT) to create repositories and push code.

#### Step 1: Generate Token
1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
2. Click "Generate new token"
3. Set expiration (recommend 90 days)
4. Select repository permissions:
   - **Contents**: Read and write
   - **Metadata**: Read-only
   - **Pull requests**: Read and write

#### Step 2: Copy Token
Save the token securely—you'll enter it in the ClawForge UI.

### 4.3 Supabase Setup (Optional)

If using Supabase for authentication:

1. Create a new Supabase project at https://supabase.com
2. Go to Settings → API to get your keys
3. Enable Email authentication in Authentication → Providers
4. Run the database migrations:

```sql
-- Create projects table
CREATE TABLE projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  name TEXT NOT NULL,
  description TEXT,
  github_repo_url TEXT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY "Users can view own projects" ON projects
  FOR ALL USING (auth.uid() = user_id);
```

---

## 5. Getting Started

### 5.1 Starting the Servers

#### Option A: Start Both Services Together
```bash
# From the clawforge root directory
pnpm dev
```

#### Option B: Start Services Separately

**Terminal 1 - Backend (Python/FastAPI):**
```bash
cd apps/api
uv run uvicorn clawforge.main:app --reload --port 8000
```

**Terminal 2 - Frontend (Next.js):**
```bash
cd apps/web
pnpm dev
```

### 5.2 Accessing the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs

### 5.3 Creating an Account

1. Click "Sign Up" on the landing page
2. Enter your email and password
3. Verify your email (if using Supabase email verification)
4. Log in with your credentials

---

## 6. Using ClawForge

### 6.1 The Workflow Canvas

After logging in, you'll see the workflow canvas with input nodes:

```
┌─────────────────────────────────────────────────────────────┐
│                    ClawForge Workflow                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   App Idea   │───▶│ Target Users │───▶│   Features   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                              │                              │
│                              ▼                              │
│                      ┌──────────────┐                       │
│                      │  UI Design   │                       │
│                      └──────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Step-by-Step App Generation

#### Step 1: Connect GitHub
1. Click the GitHub icon in the header
2. Enter your Personal Access Token
3. Choose "Create New Repository" or select existing
4. Enter repository name (e.g., "my-flutter-app")

#### Step 2: Describe Your App Idea
Click the "App Idea" node and enter a description:

**Example:**
```
A personal finance tracker that helps users manage their
expenses, set budgets, and visualize spending patterns
with charts and graphs.
```

**Tips for Better Results:**
- Be specific about the app's purpose
- Mention key functionality
- Include any unique features

#### Step 3: Define Target Users
Click the "Target Users" node:

**Example:**
```
Young professionals aged 22-35 who want to track daily
expenses, manage multiple accounts, and save money.
They prefer simple, intuitive interfaces with dark mode
support and quick data entry.
```

#### Step 4: List Features
Click the "Features" node:

**Example:**
```
- Add/edit/delete transactions with categories
- Monthly budget setting per category
- Dashboard with spending overview
- Pie charts for category breakdown
- Line graphs for spending trends
- Export data to CSV
- Recurring transactions
- Multiple currency support
- Search and filter transactions
- Dark mode toggle
```

#### Step 5: Specify UI Design
Click the "UI Design" node:

**Example:**
```
Modern Material Design 3 with rounded corners and soft
shadows. Primary color: Deep Purple (#673AB7).
Dark mode as default. Bottom navigation with 4 tabs:
Home, Transactions, Budget, Settings. Use card-based
layouts for transaction lists. Include subtle animations
for adding transactions.
```

#### Step 6: Generate App
1. Verify all four nodes have content (they'll show green checkmarks)
2. Ensure GitHub is connected (green indicator)
3. Click the **"Generate App"** button
4. Wait for the workflow to complete (typically 3-8 minutes)

### 6.3 Advanced Options (Optional)

Click "Advanced Options" to configure:

| Option | Description | Default |
|--------|-------------|---------|
| **State Management** | Riverpod, Bloc, Provider | Riverpod |
| **Navigation** | GoRouter, Navigator 2.0 | GoRouter |
| **Database** | Drift, Hive, SharedPreferences | Drift |
| **Backend Type** | Offline-first, API-based | Offline-first |
| **Tests** | Basic, Comprehensive, None | Basic |
| **Documentation** | Inline, Full, Minimal | Inline |

---

## 7. Understanding the Workflow

### 7.1 AI Agent Pipeline

When you click "Generate App", the following agents process your request:

```
┌─────────────┐
│  Architect  │  Analyzes requirements, creates app structure
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Coder    │  Generates Dart/Flutter code for each file
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Reviewer   │  Checks code quality, fixes issues
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validator  │  Runs Flutter analyze in Docker container
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   GitHub    │  Creates repo, pushes code, creates PR
└─────────────┘
```

### 7.2 Processing Stages

| Stage | Duration | Description |
|-------|----------|-------------|
| Architecture | 30-60s | Planning app structure |
| Code Generation | 2-4 min | Writing all Dart files |
| Code Review | 30-60s | Quality checks and fixes |
| Validation | 30-60s | Flutter analyze in Docker |
| GitHub Push | 20-40s | Repository operations |

### 7.3 Real-Time Progress

During generation, you'll see live updates:
- Current stage indicator
- Files being generated
- Validation results
- Any warnings or errors

---

## 8. Generated Project Structure

### 8.1 Directory Layout

```
my_flutter_app/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── app/
│   │   ├── app.dart              # MaterialApp configuration
│   │   └── router.dart           # GoRouter configuration
│   ├── core/
│   │   ├── constants/            # App constants, colors, strings
│   │   ├── theme/                # Theme configuration
│   │   ├── utils/                # Utility functions
│   │   └── extensions/           # Dart extensions
│   ├── data/
│   │   ├── models/               # Data models
│   │   ├── repositories/         # Repository implementations
│   │   └── datasources/          # Local/remote data sources
│   ├── domain/
│   │   ├── entities/             # Business entities
│   │   ├── repositories/         # Repository interfaces
│   │   └── usecases/             # Business logic
│   ├── presentation/
│   │   ├── screens/              # UI screens
│   │   ├── widgets/              # Reusable widgets
│   │   └── providers/            # Riverpod providers
│   └── database/
│       └── database.dart         # Drift database setup
├── test/
│   ├── unit/                     # Unit tests
│   ├── widget/                   # Widget tests
│   └── integration/              # Integration tests
├── assets/
│   ├── images/                   # Image assets
│   └── fonts/                    # Custom fonts
├── pubspec.yaml                  # Dependencies
├── analysis_options.yaml         # Lint rules
└── README.md                     # Project documentation
```

### 8.2 Key Files Explained

| File | Purpose |
|------|---------|
| `lib/main.dart` | App initialization, provider scope setup |
| `lib/app/router.dart` | Route definitions using GoRouter |
| `lib/core/theme/app_theme.dart` | Light/dark theme configuration |
| `lib/data/models/*.dart` | Freezed/JsonSerializable models |
| `lib/database/database.dart` | Drift database with tables |
| `lib/presentation/providers/*.dart` | Riverpod state providers |

---

## 9. Running Your Generated App

### 9.1 Clone the Generated Repository

```bash
git clone https://github.com/yourusername/my-flutter-app.git
cd my-flutter-app
```

### 9.2 Install Dependencies

```bash
flutter pub get
```

### 9.3 Generate Required Code

For Freezed models and Drift database:

```bash
dart run build_runner build --delete-conflicting-outputs
```

### 9.4 Run the App

#### On Android Emulator:
```bash
flutter run -d android
```

#### On iOS Simulator (macOS only):
```bash
flutter run -d ios
```

#### On Chrome (Web):
```bash
flutter run -d chrome
```

#### On Desktop:
```bash
# macOS
flutter run -d macos

# Windows
flutter run -d windows

# Linux
flutter run -d linux
```

### 9.5 Build for Production

#### Android APK:
```bash
flutter build apk --release
```

#### iOS:
```bash
flutter build ios --release
```

#### Web:
```bash
flutter build web --release
```

---

## 10. Troubleshooting

### 10.1 Common Issues

#### Issue: "GitHub token invalid" Error
**Cause**: Token expired or lacks required permissions.

**Solution**:
1. Generate a new token with `repo` scope
2. Update token in ClawForge GitHub settings
3. Retry generation

#### Issue: Generation Stuck at "Creating Repository"
**Cause**: GitHub API rate limiting or network issues.

**Solution**:
1. Wait 1-2 minutes and retry
2. Check your GitHub token permissions
3. Verify internet connection

#### Issue: "Backend not reachable" Error
**Cause**: Python backend not running.

**Solution**:
```bash
cd apps/api
uv run uvicorn clawforge.main:app --reload --port 8000
```

#### Issue: Docker Validation Fails
**Cause**: Docker not running or image not pulled.

**Solution**:
```bash
# Start Docker
open -a Docker  # macOS
sudo systemctl start docker  # Linux

# Pull Flutter image
docker pull ghcr.io/cirruslabs/flutter:stable
```

#### Issue: "Connection Lost" but App Generated
**Cause**: Long-running workflow exceeded HTTP timeout.

**Solution**:
- Check your GitHub repository—the code is likely there
- The PR may have been created successfully
- Click "Check GitHub" in the error dialog

### 10.2 Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `AUTH_001` | Not authenticated | Log in again |
| `GH_401` | GitHub token invalid | Regenerate token |
| `GH_403` | Insufficient permissions | Add `repo` scope |
| `GH_404` | Repository not found | Check repo name |
| `GH_422` | Repo already exists | Use different name |
| `API_503` | Backend unavailable | Start backend server |
| `VAL_001` | Flutter validation failed | Check generated code |

### 10.3 Logs Location

| Component | Log Location |
|-----------|--------------|
| Frontend | Browser DevTools Console |
| Backend | Terminal running uvicorn |
| Docker | `docker logs <container_id>` |

---

## 11. Frequently Asked Questions

### General Questions

**Q: How long does app generation take?**
A: Typically 3-8 minutes depending on app complexity.

**Q: Can I customize the generated code?**
A: Yes! The generated code is fully yours to modify.

**Q: What Flutter version is used?**
A: Flutter 3.22+ (stable channel).

**Q: Is the generated code production-ready?**
A: Yes, it follows clean architecture principles and best practices.

### Technical Questions

**Q: Can I use my own backend/API?**
A: Yes, modify the data layer to connect to your API.

**Q: Does it support Firebase?**
A: Not currently, but you can add Firebase manually.

**Q: Can I generate multiple apps?**
A: Yes, each generation creates a new repository.

**Q: Is there a limit on generations?**
A: Limited by your Anthropic API credits.

### Troubleshooting Questions

**Q: Why is my app not building?**
A: Run `dart run build_runner build` to generate code.

**Q: Token keeps expiring?**
A: Use Fine-grained tokens with longer expiration.

**Q: Can I regenerate specific files?**
A: Not currently—regenerate the entire app.

---

## 12. Technical Reference

### 12.1 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/workflow/run` | POST | Start app generation |
| `/api/projects` | GET | List user projects |
| `/api/projects/{id}` | GET | Get project details |
| `/health` | GET | Backend health check |

### 12.2 Workflow Input Schema

```json
{
  "basic_inputs": {
    "app_idea": "string",
    "target_users": "string",
    "features": "string",
    "ui_design": "string"
  },
  "advanced_options": {
    "architecture": {
      "state": "riverpod | bloc | provider",
      "nav": "go_router | navigator",
      "db": "drift | hive | none"
    },
    "backend": {
      "type": "offline-first | api-based"
    },
    "code_settings": {
      "defensive": true,
      "tests": "basic | comprehensive | none",
      "docs": "inline | full | minimal"
    }
  },
  "github_config": {
    "token": "ghp_xxxx",
    "repo_name": "my-app",
    "create_new": true
  }
}
```

### 12.3 Generated Dependencies

Default packages included in generated apps:

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.5.1
  riverpod_annotation: ^2.3.5
  go_router: ^14.2.0
  drift: ^2.18.0
  sqlite3_flutter_libs: ^0.5.21
  freezed_annotation: ^2.4.1
  json_annotation: ^4.9.0
  intl: ^0.19.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.9
  riverpod_generator: ^2.4.0
  freezed: ^2.5.2
  json_serializable: ^6.8.0
  drift_dev: ^2.18.0
  flutter_lints: ^4.0.0
```

### 12.4 Keyboard Shortcuts (Web UI)

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + Enter` | Generate App |
| `Ctrl/Cmd + S` | Save Progress |
| `Ctrl/Cmd + G` | Open GitHub Settings |
| `Escape` | Close Modal |

---

## Support & Resources

- **Documentation**: https://clawforge.dev/docs
- **GitHub Issues**: https://github.com/clawforge/clawforge/issues
- **Discord Community**: https://discord.gg/clawforge

---

**ClawForge v1.0** | Built with Claude AI | MIT License

*Last updated: May 2025*
