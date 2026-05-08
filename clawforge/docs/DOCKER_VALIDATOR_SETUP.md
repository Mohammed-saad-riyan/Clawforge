# Docker Validator Setup Guide

ClawForge uses a Docker-based validation system to verify Flutter code before pushing to GitHub.

## Overview

The validation pipeline runs three commands inside a Docker container:

1. **`flutter pub get`** - Resolves dependencies
2. **`dart run build_runner build`** - Generates `.g.dart` and `.freezed.dart` files
3. **`dart analyze`** - Static analysis for errors

If errors are found, the Refiner Agent attempts to fix them automatically (up to 3 iterations).

## Prerequisites

- Docker installed and running
- ~3GB disk space for Flutter SDK image
- Internet connection (first-time image pull)

## Quick Start (Local Development)

```bash
# 1. Pull the Flutter Docker image (~2.5GB)
docker pull ghcr.io/cirruslabs/flutter:stable

# 2. Start the warm container (keeps Flutter SDK ready)
docker run -d \
  --name clawforge-flutter-validator \
  -v /tmp/clawforge-workspaces:/workspaces \
  ghcr.io/cirruslabs/flutter:stable \
  tail -f /dev/null

# 3. Verify it's running
docker ps | grep clawforge-flutter-validator
```

## How It Works

### 1. Warm Container

ClawForge uses a persistent "warm" container to avoid cold-start delays:

- Container stays running with `tail -f /dev/null`
- Flutter SDK is pre-loaded and ready
- Workspaces are mounted at `/workspaces`

### 2. Project Workspaces

Each validation creates a temporary workspace:

```
/tmp/clawforge-workspaces/
├── proj_abc123/
│   ├── lib/
│   ├── pubspec.yaml
│   └── ...
└── proj_def456/
    └── ...
```

### 3. Validation Flow

```
Files Generated
     │
     ▼
┌─────────────────────────────────────┐
│ 1. Copy files to workspace          │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 2. flutter pub get                  │
│    └── Fix pubspec if fails         │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 3. dart run build_runner build      │
│    └── Capture .g.dart files        │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 4. dart analyze --format=machine    │
│    └── Parse errors                 │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ 5. If errors → Refiner Agent fix    │
│    └── Loop back to step 2 (max 3x) │
└─────────────────────────────────────┘
     │
     ▼
Push to GitHub
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAWFORGE_DOCKER_IMAGE` | `ghcr.io/cirruslabs/flutter:stable` | Flutter Docker image |
| `CLAWFORGE_CONTAINER_NAME` | `clawforge-flutter-validator` | Container name |
| `CLAWFORGE_WORKSPACE_BASE` | `/tmp/clawforge-workspaces` | Workspace directory |
| `CLAWFORGE_VALIDATION_TIMEOUT` | `120` | Timeout per command (seconds) |
| `CLAWFORGE_MAX_ITERATIONS` | `3` | Max fix attempts |

### Python Configuration

```python
from clawforge.validator import DockerValidator, ValidationLoop

# Custom validator instance
validator = DockerValidator(
    docker_image="ghcr.io/cirruslabs/flutter:3.19.0",  # Specific version
    container_name="my-flutter-validator",
    workspace_base="/custom/workspaces",
    timeout_seconds=180,
)

# Custom validation loop
loop = ValidationLoop(
    validator=validator,
    max_iterations=5,  # More fix attempts
)
```

## Common Issues

### Container Not Found

```bash
# Check if container exists
docker ps -a | grep clawforge

# If stopped, start it
docker start clawforge-flutter-validator

# If missing, create it
docker run -d \
  --name clawforge-flutter-validator \
  -v /tmp/clawforge-workspaces:/workspaces \
  ghcr.io/cirruslabs/flutter:stable \
  tail -f /dev/null
```

### Permission Errors

```bash
# Ensure workspace directory is writable
sudo chmod -R 777 /tmp/clawforge-workspaces
```

### Out of Disk Space

```bash
# Clean up old workspaces
rm -rf /tmp/clawforge-workspaces/proj_*

# Docker cleanup
docker system prune -f
```

### Timeout Issues

Increase timeout in your configuration:

```python
validator = DockerValidator(timeout_seconds=300)  # 5 minutes
```

## Production Deployment

### Hetzner CX21 (~$6/month)

1. **SSH into server**:
   ```bash
   ssh root@your-server-ip
   ```

2. **Install Docker**:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

3. **Pull Flutter image**:
   ```bash
   docker pull ghcr.io/cirruslabs/flutter:stable
   ```

4. **Start warm container**:
   ```bash
   docker run -d \
     --name clawforge-flutter-validator \
     --restart unless-stopped \
     -v /tmp/clawforge-workspaces:/workspaces \
     ghcr.io/cirruslabs/flutter:stable \
     tail -f /dev/null
   ```

5. **Configure ClawForge API** to connect to this container

### Resource Requirements

- **CPU**: 2 vCPU minimum
- **RAM**: 4GB minimum
- **Disk**: 10GB for Flutter SDK + workspaces
- **Network**: Outbound for pub.dev packages

## Testing the Validator

### Manual Test

```bash
# Create test project
mkdir -p /tmp/clawforge-workspaces/test_project/lib
cat > /tmp/clawforge-workspaces/test_project/pubspec.yaml << 'EOF'
name: test_app
description: Test Flutter app
version: 1.0.0
environment:
  sdk: '>=3.0.0 <4.0.0'
dependencies:
  flutter:
    sdk: flutter
EOF

cat > /tmp/clawforge-workspaces/test_project/lib/main.dart << 'EOF'
import 'package:flutter/material.dart';
void main() => runApp(const MaterialApp(home: Text('Hello')));
EOF

# Run validation
docker exec clawforge-flutter-validator bash -c "
  cd /workspaces/test_project && \
  flutter pub get && \
  dart analyze
"
```

### Python Test

```python
import asyncio
from clawforge.validator import DockerValidator

async def test_validation():
    validator = DockerValidator()

    # Ensure container is running
    running = await validator.ensure_container_running()
    print(f"Container running: {running}")

    # Get container status
    status = await validator.get_container_status()
    print(f"Container status: {status}")

    # Test files
    files = [
        {
            "path": "pubspec.yaml",
            "content": """
name: test_app
description: Test Flutter app
version: 1.0.0
environment:
  sdk: '>=3.0.0 <4.0.0'
dependencies:
  flutter:
    sdk: flutter
"""
        },
        {
            "path": "lib/main.dart",
            "content": """
import 'package:flutter/material.dart';
void main() => runApp(const MaterialApp(home: Text('Hello')));
"""
        }
    ]

    # Run validation
    result = await validator.validate(files, project_id="test_001")
    print(f"Validation passed: {result.success}")
    print(f"Errors: {len(result.all_errors)}")
    print(f"Warnings: {len(result.all_warnings)}")

asyncio.run(test_validation())
```

## Monitoring

### Check Validation Logs

```bash
# Recent container logs
docker logs clawforge-flutter-validator --tail 100

# Live logs
docker logs -f clawforge-flutter-validator
```

### Resource Usage

```bash
# Container stats
docker stats clawforge-flutter-validator

# Workspace disk usage
du -sh /tmp/clawforge-workspaces
```

## Cleanup

### Stop and Remove Container

```bash
docker stop clawforge-flutter-validator
docker rm clawforge-flutter-validator
```

### Remove Image

```bash
docker rmi ghcr.io/cirruslabs/flutter:stable
```

### Clean Workspaces

```bash
rm -rf /tmp/clawforge-workspaces
```

## Architecture Notes

### Why Docker?

- **Isolation**: Each project runs in a clean environment
- **Consistency**: Same Flutter version across all validations
- **No Host Pollution**: Flutter SDK stays in container
- **Easy Updates**: Just pull new image version

### Why Warm Container?

- **Speed**: No container startup delay (~5s saved)
- **Resource Efficiency**: One container reused for all projects
- **State Persistence**: Flutter pub cache stays warm

### Why Not .g.dart Committed?

Per user preference, generated files (`.g.dart`, `.freezed.dart`) are NOT committed to GitHub. Instead:

1. Build runner runs during validation
2. Generated files are captured for reference
3. README includes build instructions
4. Users run `dart run build_runner build` locally

This keeps the repo clean and ensures users have matching generated code.
