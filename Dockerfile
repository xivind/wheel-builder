FROM python:3.11-slim

# Use uv as a drop in replacement for pip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies from the lockfile, fail the build if uv.lock is out of sync with pyproject.toml
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-cache
ENV PATH="/app/.venv/bin:$PATH"

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Create data and logs directories
RUN mkdir -p /app/data/logs

# Expose port
EXPOSE 8004

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004", "--log-config", "uvicorn_log_config.ini"]

# Healthcheck using curl to test HTTP endpoint
HEALTHCHECK --interval=600s --timeout=10s --retries=3 \
  CMD curl -sSf -o /dev/null -w "%{http_code}" http://127.0.0.1:8004 || exit 1
