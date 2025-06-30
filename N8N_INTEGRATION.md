# n8n Integration Guide for GA4 HTTP API

This guide explains how to use the GA4 HTTP API with n8n workflows.

## Prerequisites

1. Deploy the GA4 HTTP API server using Docker
2. Have your Google Analytics 4 credentials configured
3. Note down your API username and password from `.env`

## API Endpoints

The API runs on port 8000 by default and provides these endpoints:

### Health Check (No Auth Required)
- **GET** `/`
- Returns server status and GA4 property ID

### List Dimension Categories
- **GET** `/dimensions`
- Requires Basic Auth
- Returns all available dimension categories

### Get Dimensions by Category
- **GET** `/dimensions/{category}`
- Requires Basic Auth
- Example categories: `time`, `geography`, `technology`, `traffic_source`

### List Metric Categories
- **GET** `/metrics`
- Requires Basic Auth
- Returns all available metric categories

### Get Metrics by Category
- **GET** `/metrics/{category}`
- Requires Basic Auth
- Example categories: `user_metrics`, `session_metrics`, `ecommerce_metrics`

### Get GA4 Data
- **POST** `/data`
- Requires Basic Auth
- Request body example:
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
        "value": "United States",
        "matchType": "EXACT"
      }
    }
  }
}
```

## n8n HTTP Request Configuration

### Basic Setup

1. Add an **HTTP Request** node in n8n
2. Configure authentication:
   - Authentication: **Basic Auth**
   - Username: `ga4_8nx7aug8` (or your configured username)
   - Password: Your configured password

### Example: Get User Metrics by Country

1. **HTTP Request** node configuration:
   - Method: `POST`
   - URL: `http://your-server:8000/data`
   - Authentication: Basic Auth
   - Body Content Type: `JSON`
   - Body:
   ```json
   {
     "dimensions": ["date", "country"],
     "metrics": ["totalUsers", "newUsers", "activeUsers"],
     "date_range_start": "7daysAgo",
     "date_range_end": "yesterday"
   }
   ```

### Example: Filter by Specific Country

```json
{
  "dimensions": ["date", "city"],
  "metrics": ["sessions", "bounceRate", "averageSessionDuration"],
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

### Example: E-commerce Analytics

```json
{
  "dimensions": ["date", "itemName"],
  "metrics": ["itemRevenue", "itemPurchaseQuantity", "itemViews"],
  "date_range_start": "7daysAgo",
  "date_range_end": "yesterday"
}
```

## Advanced Filtering

The API supports complex filters using `andGroup`, `orGroup`, and `notExpression`:

### AND Filter Example
```json
{
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

### OR Filter Example
```json
{
  "dimension_filter": {
    "orGroup": {
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
            "fieldName": "country",
            "stringFilter": {
              "value": "Canada",
              "matchType": "EXACT"
            }
          }
        }
      ]
    }
  }
}
```

## n8n Workflow Tips

1. **Error Handling**: Add an **IF** node after the HTTP Request to check if the request was successful
2. **Data Transformation**: Use **Code** or **Set** nodes to transform the GA4 data for your needs
3. **Scheduling**: Use **Schedule Trigger** node to fetch GA4 data at regular intervals
4. **Multiple Requests**: Chain multiple HTTP Request nodes to get different metrics/dimensions

## Environment Variables for Docker

When deploying with Docker, ensure these environment variables are set:

```bash
# Required
GA4_PROPERTY_ID=your_property_id
API_USERNAME=your_username
API_PASSWORD=your_secure_password

# GA4 Credentials (use one of these options)
# Option 1: Individual variables
GA4_PROJECT_ID=your-project-id
GA4_PRIVATE_KEY_ID=your-key-id
GA4_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
GA4_CLIENT_EMAIL=service-account@project.iam.gserviceaccount.com
GA4_CLIENT_ID=your-client-id

# Option 2: JSON file
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/ga4-service-account.json
```

## Troubleshooting

1. **401 Unauthorized**: Check your Basic Auth credentials
2. **400 Bad Request**: Verify your dimension/metric names and filter structure
3. **500 Internal Server Error**: Check server logs and ensure GA4 credentials are properly configured
4. **Empty Results**: Verify date range and filters aren't too restrictive

## API Documentation

Once deployed, visit `http://your-server:8000/docs` for interactive API documentation (Swagger UI).