# Use uv's ARM64 Python base image
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --no-cache

# Copy application code
COPY agent.py ./
COPY app/ ./app/

# Expose port
EXPOSE 8080

# Run application
CMD ["uv", "run", "uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]