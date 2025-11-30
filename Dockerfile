FROM python:3.13-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies in a cache layer
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --locked --no-install-project --no-editable

# Copy the project into the intermediate image
COPY . /app

# Sync the project and install it
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-editable --no-dev && \
  chmod +x /app/.venv/bin/*

FROM python:3.13-alpine

# Create a non-root user
RUN addgroup -S -g 1000 app && adduser -S -u 1000 -G app app

# Copy the virtual environment
COPY --from=builder --chown=app:app /app/.venv /app/.venv

USER app

CMD ["/app/.venv/bin/oura-scraper"]
