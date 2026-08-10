# ============================================================================
# Stage 1 - Build Python dependencies
# ============================================================================

FROM python:3.12-slim AS builder

# Python settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ---------------------------------------------------------------------------
# Use ArvanCloud Debian mirror (for users in Iran)
# ---------------------------------------------------------------------------

RUN sed -i 's|deb.debian.org|mirror.arvancloud.ir|g' \
    /etc/apt/sources.list.d/debian.sources

# ---------------------------------------------------------------------------
# Install build dependencies
# ---------------------------------------------------------------------------

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Install Python packages
# ---------------------------------------------------------------------------

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt


# ============================================================================
# Stage 2 - Runtime Image
# ============================================================================

FROM python:3.12-slim

# Python settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=meterstack2.settings

WORKDIR /app

# ---------------------------------------------------------------------------
# Use ArvanCloud Debian mirror
# ---------------------------------------------------------------------------

RUN sed -i 's|deb.debian.org|mirror.arvancloud.ir|g' \
    /etc/apt/sources.list.d/debian.sources

# ---------------------------------------------------------------------------
# Install runtime libraries
# ---------------------------------------------------------------------------

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Copy installed Python packages
# ---------------------------------------------------------------------------

COPY --from=builder /root/.local /root/.local

ENV PATH="/root/.local/bin:${PATH}"

# ---------------------------------------------------------------------------
# Copy project
# ---------------------------------------------------------------------------

COPY . .

# ---------------------------------------------------------------------------
# Expose Django port
# ---------------------------------------------------------------------------

EXPOSE 8000

# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
CMD python -c "import socket; s=socket.socket(); s.connect(('localhost',8000)); s.close()"

# ---------------------------------------------------------------------------
# Start Gunicorn
# ---------------------------------------------------------------------------

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "meterstack2.wsgi:application"]