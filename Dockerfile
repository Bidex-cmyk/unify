FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

FROM base AS builder
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ ./src/
COPY README.md ./
RUN uv sync --frozen --no-dev

FROM base AS runtime
COPY --from=builder /app/.venv /app/.venv
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY README.md ./
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "unify.main:app", "--host", "0.0.0.0", "--port", "8000"]
