# ── Stage 1: Builder ──────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

# ── Stage 2: Runtime ─────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

# Non-root user for security
RUN useradd --create-home --shell /bin/bash botuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY core/ ./core/

# Create logs directory owned by botuser
RUN mkdir -p /app/logs && chown -R botuser:botuser /app/logs

USER botuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import core.ai_support_bot; print('ok')" || exit 1

CMD ["python", "-m", "core.ai_support_bot"]
