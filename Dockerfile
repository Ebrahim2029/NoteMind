# ------------------------------------------------------------------------------
# Base image & Python setup
# ------------------------------------------------------------------------------
FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and use unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Set workdir
WORKDIR /app

# System deps for psycopg2, compilation, and health/debug tools
# - libpq-dev, gcc: for psycopg2-binary if source build is needed
# - build-essential: for any native extensions in future
# - curl: for simple health/diagnostics
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------------------
# Builder layer: Install Python deps using a deterministic set of requirement files
# ------------------------------------------------------------------------------
FROM base AS builder

# Use a mount to speed up pip caching in Docker builds (BuildKit)
# (This is ignored if BuildKit isn't enabled)
# hadolint ignore=DL3042
RUN --mount=type=cache,target=/root/.cache/pip true

# Copy minimal files first for better layer caching
COPY requirements.txt /app/requirements.txt
# If you’re using the /requirements/ folder (as your tree shows), copy it too
#COPY requirements /app/requirements
RUN pip install --upgrade pip && pip install -r /app/requirements.txt 
# Install dependencies
# Priority order: requirements/all.txt -> requirements/prod.txt -> requirements.txt
# Adjust if you prefer a single file.
# RUN if [ -f /app/requirements/all.txt ]; then \
#         pip install --upgrade pip && pip install -r /app/requirements/all.txt ; \
#     elif [ -f /app/requirements/prod.txt ]; then \
#         pip install --upgrade pip && pip install -r /app/requirements/prod.txt ; \
#     else \
#         pip install --upgrade pip && pip install -r /app/requirements.txt ; \
#     fi

# ------------------------------------------------------------------------------
# Runtime image
# ------------------------------------------------------------------------------
FROM base AS runtime

# Create a non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app
USER app

# Copy installed site-packages from builder layer
# We copy the entire Python site-packages to the same interpreter path
# (works because base and builder share the same python image tag)
COPY --from=builder /usr/local/lib/python3.13 /usr/local/lib/python3.13
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
# Keep .dockerignore up-to-date so we don’t send venvs, .git, etc.
COPY --chown=app:app . /app

# Default environment (override via docker-compose)
ENV APP_ENV=production \
    APP_DEBUG=false

# Expose API port (compose maps to 8080)
EXPOSE 8080

# Healthcheck (the compose file has service-level healthchecks; keeping image lean)
# HEALTHCHECK CMD curl -fsS http://localhost:8080/health || exit 1

# ------------------------------------------------------------------------------
# Entrypoint / CMD
# The same image serves both API and worker by overriding the command in compose:
# - API:    uvicorn main:app --host 0.0.0.0 --port 8080 --proxy-headers --reload
# - Worker: python -m workers.sync_worker
# ------------------------------------------------------------------------------
# Safe default: run API (can be overridden by docker-compose `command:`)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
