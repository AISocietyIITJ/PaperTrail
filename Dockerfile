FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (caches this layer if deps don't change)
COPY pyproject.toml uv.lock ./

# Install dependencies into a project-local venv
RUN uv sync --frozen --no-install-project

# Copy the rest of your code
COPY . .

# Make sure the venv's binaries are used
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src

# Default command: run training
CMD ["python", "-m", "mnist_task.train"]