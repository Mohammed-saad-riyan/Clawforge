# syntax=docker/dockerfile:1

# Base stage with Python and uv
FROM python:3.12-slim AS base
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Development stage
FROM base AS development
COPY pyproject.toml ./
RUN uv sync --dev
COPY . .
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "clawforge.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS production
COPY pyproject.toml ./
RUN uv sync --no-dev
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "clawforge.main:app", "--host", "0.0.0.0", "--port", "8000"]
