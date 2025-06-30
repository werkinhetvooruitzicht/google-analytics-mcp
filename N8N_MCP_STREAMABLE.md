# n8n MCP Client Integration Guide - HTTP Streamable

This guide explains how to use the GA4 MCP Server with n8n's MCP Client node using the HTTP Streamable transport (recommended).

## Prerequisites

1. Deploy the GA4 MCP Streamable Server using Docker
2. Have your Google Analytics 4 credentials configured
3. Note down your API username and password from `.env`

## Server Endpoints

The server runs on port 8000 and provides:

### HTTP Streamable Endpoint (Recommended)
- **POST** `/stream` - Main MCP protocol endpoint with streaming support
- Requires Basic Auth
- Content-Type: `application/json`
- Response: `application/x-ndjson` (newline-delimited JSON)

### Standard Endpoints
- **GET** `/` - Health check (no auth required)
- **GET** `/mcp` - Server info and capabilities
- **POST** `/mcp` - Standard MCP endpoint (non-streaming)

## n8n MCP Client Configuration

### 1. Create MCP Client Credentials

1. In n8n, go to **Credentials** → **Create New**
2. Search for **MCP Client (HTTP Streamable) API**
3. Configure:
   - **HTTP Streamable URL**: `http://owc8o00osgwcgks880g8wkog.172.201.74.13.sslip.io/stream`
   - **Additional Headers**: (one per line)
     ```
     Authorization:Basic Z2E0XzhueDdhdWc4OnYmdSc6XDhoeCV2PUU5e1FYd2AkTj5DKQ==
     Content-Type:application/json
     Accept:application/x-ndjson
     ```

Note: Make sure there's no space after the colon in headers (e.g., `Authorization:Basic` not `Authorization: Basic`)

### 2. Add MCP Client Node to Workflow

1. Add an **MCP Client** node to your workflow
2. Configure:
   - **Connection Type**: `HTTP Streamable`
   - **Credential**: Select the credential you created
   - **Operation**: Choose from available operations

### 3. Available Operations

- **List Tools** - Get all available GA4 tools
- **Execute Tool** - Run a specific tool
- **List Resources** - Currently returns empty (GA4 doesn't use resources)
- **List Prompts** - Currently returns empty (GA4 doesn't use prompts)

## Available Tools

### 1. `list_dimension_categories`
Lists all GA4 dimension categories.

**No parameters required**

Example response:
```json
{
  "time": {
    "count": 16,
    "dimensions": ["date", "dateHour", "day", "hour", "month", "week", "year", ...]
  },
  "geography": {
    "count": 5,
    "dimensions": ["city", "cityId", "country", "countryId", "region"]
  },
  ...
}
```

### 2. `list_metric_categories`
Lists all GA4 metric categories.

**No parameters required**

### 3. `get_dimensions_by_category`
Get dimensions for a specific category.

**Parameters:**
```json
{
  "category": "geography"
}
```

### 4. `get_metrics_by_category`
Get metrics for a specific category.

**Parameters:**
```json
{
  "category": "user_metrics"
}
```

### 5. `get_ga4_data`
Retrieve GA4 analytics data.

**Parameters:**
```json
{
  "dimensions": ["date", "country"],
  "metrics": ["totalUsers", "sessions", "bounceRate"],
  "date_range_start": "30daysAgo",
  "date_range_end": "yesterday",
  "dimension_filter": {
    "filter": {
      "fieldName": "country",
      "stringFilter": {
        "value": "Netherlands",
        "matchType": "EXACT"
      }
    }
  }
}
```

## Example Workflow

### Basic Example: Get User Metrics

1. **MCP Client Node 1** - List available tools:
   - Operation: `List Tools`
   
2. **MCP Client Node 2** - Get user metrics:
   - Operation: `Execute Tool`
   - Tool: `get_ga4_data`
   - Parameters:
     ```json
     {
       "dimensions": ["date"],
       "metrics": ["totalUsers", "newUsers", "activeUsers"],
       "date_range_start": "7daysAgo",
       "date_range_end": "yesterday"
     }
     ```

### Advanced Example: Filtered Analytics

```json
{
  "dimensions": ["date", "deviceCategory", "country"],
  "metrics": ["sessions", "bounceRate", "averageSessionDuration"],
  "date_range_start": "30daysAgo",
  "date_range_end": "yesterday",
  "dimension_filter": {
    "andGroup": {
      "expressions": [
        {
          "filter": {
            "fieldName": "country",
            "stringFilter": {
              "value": "United States",
              "matchType": "EXACT"
            }
          }
        },
        {
          "filter": {
            "fieldName": "deviceCategory",
            "stringFilter": {
              "value": "mobile",
              "matchType": "EXACT"
            }
          }
        }
      ]
    }
  }
}
```

## Using with AI Agents

To use the MCP Client as a tool in AI Agents:

1. Set environment variable:
   ```bash
   N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true
   ```

2. In your AI Agent node:
   - Enable the MCP Client as a tool
   - Configure with your GA4 MCP credentials

3. Example prompts:
   - "Get the total users from the last 7 days"
   - "Show me traffic by country for last month"
   - "What's the bounce rate for mobile users?"

## Troubleshooting

### Connection Issues
- Verify the URL ends with `/stream`
- Check Basic Auth header is correctly formatted
- Ensure the server is running and accessible

### Authentication Errors
- Verify username and password are correct
- Check the Authorization header format: `Authorization: Basic <base64>`

### Empty Results
- Check date ranges are valid
- Verify dimension and metric names are correct
- Ensure GA4 property has data for the requested period

## Environment Variables

Required environment variables for the server:

```bash
# GA4 Configuration
GA4_PROPERTY_ID=your_property_id
GA4_PROJECT_ID=your-project-id
GA4_PRIVATE_KEY_ID=your-key-id
GA4_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
GA4_CLIENT_EMAIL=service-account@project.iam.gserviceaccount.com
GA4_CLIENT_ID=your-client-id

# API Authentication
API_USERNAME=ga4_8nx7aug8
API_PASSWORD="your-secure-password"
```