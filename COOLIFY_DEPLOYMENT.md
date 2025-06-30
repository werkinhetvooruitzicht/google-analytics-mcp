# Deploying Google Analytics MCP Server with Coolify

## Overview
This guide explains how to deploy the Google Analytics MCP server using Coolify with proper authentication and environment configuration.

## Important Note
MCP servers communicate via stdio (standard input/output), not HTTP. This means they cannot be directly exposed as web services. If you need HTTP access, you'll need to create a wrapper service or use the MCP server through a compatible client like Claude Desktop.

## Deployment Steps

### 1. Prepare Your Repository
Ensure your repository contains:
- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `ga4_mcp_server.py`
- `ga4_dimensions.json`
- `ga4_metrics.json`

### 2. Set Up in Coolify

1. **Create New Service**
   - Choose "Docker Compose" or "Dockerfile" as the service type
   - Connect your GitHub/GitLab repository

2. **Environment Variables**
   
   The server now supports two methods for authentication:

   **Method 1: Individual Environment Variables (Recommended for Coolify)**
   
   Set these in Coolify's environment variables section:
   ```
   GA4_PROPERTY_ID=123456789
   GA4_PROJECT_ID=your-project-id
   GA4_PRIVATE_KEY_ID=your-private-key-id
   GA4_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nyour-private-key-here\n-----END PRIVATE KEY-----
   GA4_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
   GA4_CLIENT_ID=your-client-id
   ```
   
   To get these values:
   1. Open your Google Cloud service account JSON file
   2. Copy each value into the corresponding environment variable
   3. For GA4_PRIVATE_KEY, make sure to include the entire key including BEGIN/END lines
   
   **Method 2: JSON File (Traditional method)**
   
   If you prefer using a JSON file:
   1. Create a persistent volume in Coolify
   2. Upload your `ga4-service-account.json` to the volume
   3. Mount it at `/app/credentials/ga4-service-account.json`
   4. Set only `GA4_PROPERTY_ID` in environment variables

### 3. Authentication Options

Since MCP servers don't expose HTTP endpoints, traditional basic auth doesn't apply. However, you have several options:

#### Option 1: Network Isolation (Recommended)
- Deploy the MCP server in a private network
- Only allow access from authorized services

#### Option 2: Add HTTP Wrapper with Auth
Create an HTTP API wrapper service with authentication:

```yaml
# Add to docker-compose.yml
http-wrapper:
  image: your-wrapper-image
  ports:
    - "8080:8080"
  environment:
    - BASIC_AUTH_USER=${BASIC_AUTH_USER}
    - BASIC_AUTH_PASS=${BASIC_AUTH_PASS}
  depends_on:
    - ga4-mcp-server
```

#### Option 3: Use Coolify's Built-in Auth
- Enable Coolify's authentication features
- Use Coolify's proxy with basic auth
- Configure in Coolify's service settings

### 4. Coolify-Specific Configuration

In Coolify's service configuration:

1. **Build Configuration**
   ```
   Build Pack: Dockerfile
   Dockerfile Location: ./Dockerfile
   ```

2. **Environment Variables**
   ```
   GA4_PROPERTY_ID=123456789
   ```

3. **Volumes** (if using runtime volume for credentials)
   ```
   Source: coolify_volume_name
   Destination: /app/credentials
   ```

4. **Health Check**
   Since MCP servers don't have HTTP endpoints, disable health checks or create a custom one.

### 5. Basic Auth with Coolify

To add basic authentication in Coolify:

1. Go to your service settings in Coolify
2. Navigate to "Security" or "Proxy" settings
3. Enable "Basic Authentication"
4. Set username and password
5. Save and redeploy

Coolify will automatically configure its proxy (Traefik/Caddy) to require basic auth for accessing your service.

## Testing the Deployment

Since MCP servers use stdio, you can't test them with curl. Instead:

1. Use the MCP test client
2. Configure Claude Desktop or another MCP client to connect
3. Check logs in Coolify for any errors

## Security Recommendations

1. **Never commit credentials**
   - Use Coolify's secrets management
   - Keep service account JSON secure

2. **Limit GA4 Permissions**
   - Grant only "Viewer" access to the service account
   - Use property-level permissions, not account-level

3. **Network Security**
   - Use private networks when possible
   - Implement IP whitelisting if needed

4. **Monitor Access**
   - Enable Coolify's logging
   - Monitor GA4 API usage

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**
   - Check volume mounting
   - Verify file path in environment variable

2. **"GA4_PROPERTY_ID not set"**
   - Ensure environment variable is set in Coolify
   - Check for typos in variable name

3. **Connection issues**
   - MCP servers don't expose HTTP ports
   - Use appropriate MCP client for testing

## Alternative: HTTP API Wrapper

If you need HTTP access, consider creating a wrapper service that:
1. Exposes HTTP endpoints
2. Translates HTTP requests to MCP protocol
3. Handles authentication
4. Returns JSON responses

This would require additional development but would make the service more accessible via standard HTTP/REST APIs.