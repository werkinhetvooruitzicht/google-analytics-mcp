# n8n MCP Client Integration Guide

This guide explains how to use the GA4 MCP Bridge with n8n's MCP Client node.

## Prerequisites

1. Deploy the GA4 MCP Bridge using Docker
2. Have your Google Analytics 4 credentials configured
3. Note down your API username and password from `.env`

## MCP Bridge Endpoints

The bridge runs on port 8000 and provides:

### MCP Endpoints
- **GET** `/mcp` - MCP server info and capabilities (requires Basic Auth)
- **POST** `/mcp` - Main MCP protocol endpoint (requires Basic Auth)

### Health Check
- **GET** `/` - Server status (no auth required)

## n8n MCP Client Configuration

### 1. Add MCP Client Node

In your n8n workflow:
1. Add an **MCP Client** node
2. Configure the connection:
   - **Server URL**: `http://owc8o00osgwcgks880g8wkog.172.201.74.13.sslip.io/mcp`
   - **Authentication**: Basic Auth
   - **Username**: `ga4_8nx7aug8` (or your configured username)
   - **Password**: Your configured password

### 2. Available MCP Tools

The MCP server exposes these tools:

#### `list_dimension_categories`
Lists all available GA4 dimension categories.
- No parameters required

#### `list_metric_categories`
Lists all available GA4 metric categories.
- No parameters required

#### `get_dimensions_by_category`
Get dimensions for a specific category.
- **Parameters**:
  - `category`: string (e.g., "time", "geography", "technology")

#### `get_metrics_by_category`
Get metrics for a specific category.
- **Parameters**:
  - `category`: string (e.g., "user_metrics", "session_metrics")

#### `get_ga4_data`
Retrieve GA4 analytics data.
- **Parameters**:
  - `dimensions`: array of strings (default: ["date"])
  - `metrics`: array of strings (default: ["totalUsers", "newUsers"])
  - `date_range_start`: string (default: "7daysAgo")
  - `date_range_end`: string (default: "yesterday")
  - `dimension_filter`: object (optional)

## Example MCP Requests

### Initialize Connection
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "id": 1
}
```

### List Available Tools
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2
}
```

### Call a Tool - Get User Metrics
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_ga4_data",
    "arguments": {
      "dimensions": ["date", "country"],
      "metrics": ["totalUsers", "sessions", "bounceRate"],
      "date_range_start": "30daysAgo",
      "date_range_end": "yesterday"
    }
  },
  "id": 3
}
```

### Call a Tool with Filters
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_ga4_data",
    "arguments": {
      "dimensions": ["date", "city"],
      "metrics": ["sessions", "bounceRate"],
      "date_range_start": "7daysAgo",
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
  },
  "id": 4
}
```

## n8n Workflow Example

1. **MCP Client Node**: Configure connection as above
2. **Function Node**: Process the MCP response
3. **Set Node**: Transform data for your needs

## Legacy REST API

The bridge also provides REST endpoints for backward compatibility:
- `GET /api/dimensions`
- `GET /api/metrics`
- `GET /api/dimensions/{category}`
- `GET /api/metrics/{category}`
- `POST /api/data`

## Troubleshooting

1. **Connection Failed**: Check URL and authentication
2. **Method Not Found**: Ensure you're using correct MCP methods
3. **Internal Error**: Check server logs and GA4 credentials
4. **Empty Results**: Verify date ranges and filters

## Environment Variables

Ensure these are set in your deployment:
```bash
# Required
GA4_PROPERTY_ID=your_property_id
API_USERNAME=your_username
API_PASSWORD=your_password

# GA4 Credentials
GA4_PROJECT_ID=your-project-id
GA4_PRIVATE_KEY_ID=your-key-id
GA4_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
GA4_CLIENT_EMAIL=service-account@project.iam.gserviceaccount.com
GA4_CLIENT_ID=your-client-id
```