# ClawForge Makefile
# Common commands for development

.PHONY: install dev build clean docker-up docker-down ollama-pull

# Install all dependencies
install:
	pnpm install
	cd apps/api && uv sync

# Start development servers
dev:
	pnpm dev

# Build all packages
build:
	pnpm build

# Type check all packages
type-check:
	pnpm type-check

# Lint all packages
lint:
	pnpm lint

# Clean build artifacts
clean:
	rm -rf apps/web/.next
	rm -rf apps/web/node_modules
	rm -rf apps/api/__pycache__
	rm -rf apps/api/.venv
	rm -rf packages/*/dist
	rm -rf packages/*/node_modules
	rm -rf node_modules

# Docker commands
docker-up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-build:
	docker compose build

# Pull Ollama model
ollama-pull:
	ollama pull qwen2.5-coder:7b

# Setup everything from scratch
setup: install ollama-pull
	cp .env.example .env
	@echo "Setup complete! Edit .env with your API keys, then run 'make dev'"

# Run API only (for local development without Docker)
api:
	cd apps/api && uv run uvicorn clawforge.main:app --host 0.0.0.0 --port 8000 --reload

# Run web only
web:
	cd apps/web && pnpm dev
