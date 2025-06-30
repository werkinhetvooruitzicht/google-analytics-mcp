# Use Python 3.10 slim image
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.10-slim

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application files
COPY --chown=appuser:appuser ga4_mcp_server.py .
COPY --chown=appuser:appuser ga4_http_server.py .

# Create directory for credentials
RUN mkdir -p /app/credentials && chown -R appuser:appuser /app

# Set environment variables with defaults
# Google Analytics Configuration
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/ga4-service-account.json
ENV GA4_PROPERTY_ID=""
ENV GA4_PROJECT_ID=""
ENV GA4_PRIVATE_KEY_ID=""
ENV GA4_PRIVATE_KEY=""
ENV GA4_CLIENT_EMAIL=""
ENV GA4_CLIENT_ID=""

# HTTP Server Configuration
ENV PORT=8000
ENV HOST=0.0.0.0
ENV API_USERNAME="admin"
ENV API_PASSWORD="changeme"

# Python configuration
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Expose HTTP port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/', timeout=10).raise_for_status()"

# Run the HTTP server by default
CMD ["python", "ga4_http_server.py"]