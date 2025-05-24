# Google Analytics MCP Server

[![PyPI version](https://badge.fury.io/py/google-analytics-mcp.svg)](https://badge.fury.io/py/google-analytics-mcp)
[![PyPI downloads](https://img.shields.io/pypi/dm/google-analytics-mcp.svg)](https://pypi.org/project/google-analytics-mcp/)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/surendranb/google-analytics-mcp)](https://github.com/surendranb/google-analytics-mcp/releases)
[![GitHub all releases](https://img.shields.io/github/downloads/surendranb/google-analytics-mcp/total.svg)](https://github.com/surendranb/google-analytics-mcp/releases)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://github.com/surendranb/google-analytics-mcp)

Connect Google Analytics 4 data to Claude, Cursor and other MCP clients. Query your website traffic, user behavior, and analytics data in natural language with access to 200+ GA4 dimensions and metrics.

**Compatible with:** Claude, Cursor and other MCP clients.

## Prerequisites

**Check your Python setup:**

```bash
# Check Python version (need 3.8+)
python --version
python3 --version

# Check pip
pip --version
pip3 --version
```

**Required:**
- Python 3.8 or higher
- Google Analytics 4 property with data
- Service account with Analytics Reporting API access

## Installation

Choose either method:

### Method 1: pip install (Recommended)

```bash
pip install google-analytics-mcp
```

### Method 2: GitHub download

```bash
git clone https://github.com/surendranb/google-analytics-mcp.git
cd google-analytics-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Setup

### Step 1: Get GA4 Credentials

**Part A: Create Service Account in Google Cloud Console**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Create or select a project**:
   - New project: Click "New Project" → Enter project name → Create
   - Existing project: Select from dropdown
3. **Enable the Analytics APIs**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Analytics Reporting API" → Click "Enable"
   - Search for "Google Analytics Data API" → Click "Enable"
4. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Enter name (e.g., "ga4-mcp-server")
   - Click "Create and Continue"
   - Skip role assignment → Click "Done"
5. **Download JSON Key**:
   - Click your service account
   - Go to "Keys" tab → "Add Key" → "Create New Key"
   - Select "JSON" → Click "Create"
   - Save the JSON file - you'll need its path

**Part B: Add Service Account to GA4**

1. **Get service account email**:
   - Open the JSON file
   - Find the `client_email` field
   - Copy the email (format: `ga4-mcp-server@your-project.iam.gserviceaccount.com`)

2. **Add to GA4 property**:
   - Go to [Google Analytics](https://analytics.google.com/)
   - Select your GA4 property
   - Click "Admin" (gear icon at bottom left)
   - Under "Property" → Click "Property access management"
   - Click "+" → "Add users"
   - Paste the service account email
   - Select "Viewer" role
   - Uncheck "Notify new users by email"
   - Click "Add"

### Step 2: Find Your GA4 Property ID

1. In [Google Analytics](https://analytics.google.com/), select your property
2. Click "Admin" (gear icon)
3. Under "Property" → Click "Property details" 
4. Copy the **Property ID** (numeric, e.g., `1234567890`)
   - **Note**: This is different from the "Measurement ID" (starts with G-)

### Step 3: Test Your Setup (Optional)

Verify your credentials:

1. **Install Google Analytics Data library**:
   ```bash
   pip install google-analytics-data
   ```

2. **Create test script** (save as `test_ga4.py`):
   ```python
   import os
   from google.analytics.data_v1beta import BetaAnalyticsDataClient
   
   # Set credentials path
   os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/your/service-account-key.json"
   
   # Test connection
   client = BetaAnalyticsDataClient()
   print("✅ GA4 credentials working!")
   ```

3. **Run test**:
   ```bash
   python test_ga4.py
   ```

If you see "✅ GA4 credentials working!" you're ready to proceed.

### Step 4: Configure Your MCP Client

Add this to your MCP client configuration:

**For Method 1 (pip install):**
```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "ga4-mcp-server",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "GA4_PROPERTY_ID": "346085905"
      }
    }
  }
}
```

**For Method 2 (GitHub download):**
```json
{
  "mcpServers": {
    "ga4-analytics": {
      "command": "/full/path/to/ga4-mcp-server/venv/bin/python",
      "args": ["/full/path/to/ga4-mcp-server/ga4_mcp_server.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/your/service-account-key.json",
        "GA4_PROPERTY_ID": "346085905"
      }
    }
  }
}
```

**Replace:**
- `/path/to/your/service-account-key.json` with your JSON file path
- `346085905` with your GA4 Property ID
- `/path/to/ga4-mcp-server/` with your download path (Method 2 only)

## Usage

Once configured, ask your MCP client questions like:

### **Discovery & Exploration:**
- "What GA4 dimension categories are available?"
- "Show me all ecommerce metrics"  
- "What dimensions can I use for geographic analysis?"

### **Traffic Analysis:**
- "What's my website traffic for the past week?"
- "Show me user metrics by city for last month"
- "Compare bounce rates between different date ranges"

### **Multi-Dimensional Analysis:**
- "Show me revenue by country and device category for last 30 days"
- "Analyze sessions and conversions by campaign and source/medium"
- "Compare user engagement across different page paths and traffic sources"

### **E-commerce Analysis:**
- "What are my top-performing products by revenue?"
- "Show me conversion rates by traffic source and device type"
- "Analyze purchase behavior by user demographics"

## Available Tools

The server provides 5 main tools:

1. **`get_ga4_data`** - Retrieve GA4 data with custom dimensions and metrics
2. **`list_dimension_categories`** - Browse available dimension categories
3. **`list_metric_categories`** - Browse available metric categories  
4. **`get_dimensions_by_category`** - Get dimensions for a specific category
5. **`get_metrics_by_category`** - Get metrics for a specific category

## Dimensions & Metrics

Access to **200+ GA4 dimensions and metrics** organized by category:

### **Dimension Categories:**
- **Time**: date, hour, month, year, etc.
- **Geography**: country, city, region
- **Technology**: browser, device, operating system
- **Traffic Source**: campaign, source, medium, channel groups
- **Content**: page paths, titles, content groups
- **E-commerce**: item details, transaction info
- **User Demographics**: age, gender, language
- **Google Ads**: campaign, ad group, keyword data
- **And 10+ more categories**

### **Metric Categories:**
- **User Metrics**: totalUsers, newUsers, activeUsers
- **Session Metrics**: sessions, bounceRate, engagementRate
- **E-commerce**: totalRevenue, transactions, conversions
- **Events**: eventCount, conversions, event values
- **Advertising**: adRevenue, returnOnAdSpend
- **And more specialized metrics**

## Troubleshooting

### Command not found (Method 1)
If `google-analytics-mcp` command not found, try:
```json
{
  "command": "python3",
  "args": ["-m", "ga4_mcp_server"]
}
```

### Python version issues
- Use `python3` instead of `python` if you have both Python 2 and 3
- Use `pip3` instead of `pip` if needed

### Permission errors
```bash
# Try user install instead of system-wide
pip install --user google-analytics-mcp
```

### Credentials not working
1. **Verify the JSON file path** is correct and accessible
2. **Check service account permissions**:
   - Go to Google Cloud Console → IAM & Admin → IAM
   - Find your service account → Check permissions
3. **Verify GA4 access**:
   - GA4 → Admin → Property access management
   - Check for your service account email
4. **Verify ID type**:
   - Property ID: numeric (e.g., `1234567890`) ✅
   - Measurement ID: starts with G- (e.g., `G-XXXXXXXXXX`) ❌

### API quota/rate limit errors
- GA4 has daily quotas and rate limits
- Try reducing the date range in your queries
- Wait a few minutes between large requests

## Project Structure

```
google-analytics-mcp/
├── ga4_mcp_server.py       # Main MCP server
├── ga4_dimensions.json     # All available GA4 dimensions  
├── ga4_metrics.json        # All available GA4 metrics
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Package configuration
├── README.md              # This file
└── claude-config-template.json  # MCP configuration template
```

## License

MIT License