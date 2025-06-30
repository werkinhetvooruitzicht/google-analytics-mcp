# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ga4_mcp_server.py .
COPY ga4_http_server.py .

# Create directory for credentials
RUN mkdir -p /app/credentials

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

ENV PYTHONUNBUFFERED=1

# Expose HTTP port
EXPOSE 8000

# Run the HTTP server by default
CMD ["python", "ga4_http_server.py"]