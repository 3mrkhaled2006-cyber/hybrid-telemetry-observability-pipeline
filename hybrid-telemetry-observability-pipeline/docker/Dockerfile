# ==============================================================================
# Stage 1: Builder Stage (Compiles & wheels pre-installation)
# ==============================================================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build tools and pip upgrades
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Hardened Runtime Stage (Distroless-like minimal Debian runtime)
# ==============================================================================
FROM python:3.11-slim-bookworm AS runtime

# Install curl for container healthcheck and cleanup package manager caches
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Security: Create unprivileged non-root system user and group (UID/GID 10001)
RUN groupadd -g 10001 telemetry && \
    useradd -u 10001 -g telemetry -s /usr/sbin/nologin -d /app -M telemetry

WORKDIR /app

# Copy isolated virtual environment from builder stage
COPY --from=builder --chown=10001:10001 /opt/venv /opt/venv

# Copy application source code
COPY --chown=10001:10001 src /app/src

# Environment hardening
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIPELINE_HEALTH_PORT=8080 \
    PIPELINE_METRICS_PORT=9102

# Drop privileges to non-root user
USER 10001:10001

# Document exposed ports (8080: Health probes, 9102: Prometheus metrics)
EXPOSE 8080 9102

# Container healthcheck testing liveness probe
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

ENTRYPOINT ["python", "-m", "src.main"]
