# GA4 MCP Server for Claude

Connect Google Analytics 4 data directly to Claude AI conversations. Ask questions about your website traffic, user behavior, and analytics data in natural language.

## Prerequisites

**Check your Python setup first:**

```bash
# Check Python version (need 3.8+)
python --version
python3 --version

# Check pip
pip --version
pip3 --version
```

**What you need:**
- Python 3.8 or higher
- Google Analytics 4 property with data
- Service account with Analytics Reporting API access

## Installation

Choose either route:

### Route 1: pip install (Recommended)

```bash
pip install ga4-mcp-server
```

### Route 2: GitHub download

```bash
git clone https://github.com/yourusername/ga4-mcp-server.git
cd ga4-mcp-server
pip install -r requirements.txt
```

## Setup

### Step 1: Get GA4 Credentials

**Part A: Create Service Account in Google Cloud Console**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Create or select a project**:
   - If new: Click "New Project" → Enter project name → Create
   - If existing: Select your project from the dropdown
3. **Enable the Analytics Reporting API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Analytics Reporting API"
   - Click on it → Click "Enable"
4. **Enable the Analytics Data API**:
   - Search for "Google Analytics Data API" 
   - Click on it → Click "Enable"
5. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Enter a name (e.g., "ga4-mcp-server")
   - Click "Create and Continue"
   - Skip role assignment for now → Click "Done"
6. **Download JSON Key**:
   - Click on your newly created service account
   - Go to "Keys" tab → "Add Key" → "Create New Key"
   - Select "JSON" → Click "Create"
   - **Save this file securely** - you'll need the path to it

**Part B: Add Service Account to GA4**

1. **Copy the service account email**:
   - From the downloaded JSON file, find the `client_email` field
   - Copy this email address (looks like: `ga4-mcp-server@your-project.iam.gserviceaccount.com`)

2. **Add to GA4 property**:
   - Go to [Google Analytics](https://analytics.google.com/)
   - Select your GA4 property
   - Click "Admin" (gear icon in bottom left)
   - Under "Property" column → Click "Property access management"
   - Click "+" → "Add users"
   - Paste the service account email
   - Select "Viewer" role (sufficient for reading data)
   - Uncheck "Notify new users by email"
   - Click "Add"

### Step 2: Find Your GA4 Property ID

1. In [Google Analytics](https://analytics.google.com/), select your property
2. Click "Admin" (gear icon)
3. Under "Property" column → Click "Property details" 
4. Copy the **Property ID** (numeric, e.g., `1234567890`)
   - **Note**: This is different from the "Measurement ID" (starts with G-)

### Step 3: Test Your Setup (Optional)

Before configuring Claude, verify your credentials work:

1. **Install Google Analytics Data library**:
   ```bash
   pip install google-analytics-data
   ```

2. **Test script** (save as `test_ga4.py`):
   ```python
   import os
   from google.analytics.data_v1beta import BetaAnalyticsDataClient
   
   # Set your credentials
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

### Step 4: Configure Claude

Add this to your Claude MCP configuration:

**For Route 1 (pip install):**
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

**For Route 2 (GitHub download):**
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
- `/path/to/your/service-account-key.json` with your actual credential file path
- `346085905` with your actual GA4 Property ID
- `/path/to/ga4-mcp-server/` with your actual download path (Route 2 only)

## Usage

Once configured, ask Claude questions like:

- "What's my website traffic for the past week?"
- "Show me user metrics by city for last month"
- "Compare bounce rates between different time periods"
- "What are my top pages by page views?"

## Available Metrics

**Default metrics:**
- totalUsers
- newUsers
- bounceRate
- screenPageViewsPerSession
- averageSessionDuration

**Default dimensions:**
- date

You can customize these by asking Claude to use different GA4 dimensions and metrics.

## Troubleshooting

### Command not found (Route 1)
If `ga4-mcp-server` command not found, try:
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
pip install --user ga4-mcp-server
```

### Credentials not working
1. **Verify the JSON file path** is correct and accessible
2. **Check that the service account has Analytics Reporting API access**:
   - Go to Google Cloud Console → IAM & Admin → IAM
   - Find your service account → Check it has necessary permissions
3. **Ensure the service account email is added as a viewer in GA4**:
   - GA4 → Admin → Property access management
   - Look for your service account email in the list
4. **Verify you're using the Property ID, not Measurement ID**:
   - Property ID: numeric (e.g., `1234567890`) ✅
   - Measurement ID: starts with G- (e.g., `G-XXXXXXXXXX`) ❌

### API quota/rate limit errors
- GA4 has daily quotas and rate limits
- Try reducing the date range in your queries
- Wait a few minutes between large requests

## License

MIT License