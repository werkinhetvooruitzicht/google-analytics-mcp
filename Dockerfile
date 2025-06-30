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
COPY ga4_dimensions.json .
COPY ga4_metrics.json .

# Create directory for credentials
RUN mkdir -p /app/credentials

# Set environment variables with defaults
# Option 1: Use JSON file (default path)
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/ga4-service-account.json

# Option 2: Use individual environment variables (leave empty, set in Coolify)
ENV GA4_PROPERTY_ID=""
ENV GA4_PROJECT_ID=""
ENV GA4_PRIVATE_KEY_ID=""
ENV GA4_PRIVATE_KEY=""
ENV GA4_CLIENT_EMAIL=""
ENV GA4_CLIENT_ID=""

ENV PYTHONUNBUFFERED=1

# The MCP server uses stdio, not HTTP
# If you need HTTP access, you'll need to add a wrapper service

# Run the MCP server
CMD ["python", "ga4_mcp_server.py"]