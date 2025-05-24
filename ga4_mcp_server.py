from fastmcp import FastMCP
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest
)
import os
import sys
import json
from pathlib import Path

# Configuration from environment variables
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")

# Validate required environment variables
if not CREDENTIALS_PATH:
    print("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set", file=sys.stderr)
    print("Please set it to the path of your service account JSON file", file=sys.stderr)
    sys.exit(1)

if not GA4_PROPERTY_ID:
    print("ERROR: GA4_PROPERTY_ID environment variable not set", file=sys.stderr)
    print("Please set it to your GA4 property ID (e.g., 123456789)", file=sys.stderr)
    sys.exit(1)

# Validate credentials file exists
if not os.path.exists(CREDENTIALS_PATH):
    print(f"ERROR: Credentials file not found: {CREDENTIALS_PATH}", file=sys.stderr)
    print("Please check the GOOGLE_APPLICATION_CREDENTIALS path", file=sys.stderr)
    sys.exit(1)

# Initialize FastMCP
mcp = FastMCP("Google Analytics 4")

# Load dimensions and metrics from JSON files
def load_dimensions():
    """Load available dimensions from JSON file"""
    try:
        script_dir = Path(__file__).parent
        with open(script_dir / "ga4_dimensions.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: ga4_dimensions.json not found", file=sys.stderr)
        return {}

def load_metrics():
    """Load available metrics from JSON file"""
    try:
        script_dir = Path(__file__).parent
        with open(script_dir / "ga4_metrics.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: ga4_metrics.json not found", file=sys.stderr)
        return {}

@mcp.tool()
def list_dimension_categories():
    """
    List all available GA4 dimension categories with descriptions.
    
    Returns:
        Dictionary of dimension categories and their available dimensions.
    """
    dimensions = load_dimensions()
    result = {}
    for category, dims in dimensions.items():
        result[category] = {
            "count": len(dims),
            "dimensions": list(dims.keys())
        }
    return result

@mcp.tool()
def list_metric_categories():
    """
    List all available GA4 metric categories with descriptions.
    
    Returns:
        Dictionary of metric categories and their available metrics.
    """
    metrics = load_metrics()
    result = {}
    for category, mets in metrics.items():
        result[category] = {
            "count": len(mets),
            "metrics": list(mets.keys())
        }
    return result

@mcp.tool()
def get_dimensions_by_category(category):
    """
    Get all dimensions in a specific category with their descriptions.
    
    Args:
        category: Category name (e.g., 'time', 'geography', 'ecommerce')
        
    Returns:
        Dictionary of dimensions and their descriptions for the category.
    """
    dimensions = load_dimensions()
    if category in dimensions:
        return dimensions[category]
    else:
        available_categories = list(dimensions.keys())
        return {"error": f"Category '{category}' not found. Available categories: {available_categories}"}

@mcp.tool()
def get_metrics_by_category(category):
    """
    Get all metrics in a specific category with their descriptions.
    
    Args:
        category: Category name (e.g., 'user_metrics', 'ecommerce_metrics', 'session_metrics')
        
    Returns:
        Dictionary of metrics and their descriptions for the category.
    """
    metrics = load_metrics()
    if category in metrics:
        return metrics[category]
    else:
        available_categories = list(metrics.keys())
        return {"error": f"Category '{category}' not found. Available categories: {available_categories}"}

@mcp.tool()
def get_ga4_data(
    dimensions=["date"],
    metrics=["totalUsers", "newUsers", "bounceRate", "screenPageViewsPerSession", "averageSessionDuration"],
    date_range_start="7daysAgo",
    date_range_end="yesterday"
):
    """
    Retrieve GA4 metrics data broken down by the specified dimensions.
    
    Args:
        dimensions: List of GA4 dimensions (e.g., ["date", "city"]) or a string 
                    representation (e.g., "[\"date\", \"city\"]" or "date,city").
        metrics: List of GA4 metrics (e.g., ["totalUsers", "newUsers"]) or a string
                 representation (e.g., "[\"totalUsers\"]" or "totalUsers,newUsers").
        date_range_start: Start date in YYYY-MM-DD format or relative date like '7daysAgo'.
        date_range_end: End date in YYYY-MM-DD format or relative date like 'yesterday'.
        
    Returns:
        List of dictionaries containing the requested data, or an error dictionary.
    """
    try:
        # Handle cases where dimensions might be passed as a string from the MCP client
        parsed_dimensions = dimensions
        if isinstance(dimensions, str):
            try:
                # Attempt to parse as JSON array first (e.g., "[\"date\", \"city\"]")
                parsed_dimensions = json.loads(dimensions)
                # Ensure it's a list after parsing; if json.loads gives a single string, wrap it in a list
                if not isinstance(parsed_dimensions, list):
                    parsed_dimensions = [str(parsed_dimensions)]
            except json.JSONDecodeError:
                # If not a valid JSON string, treat as comma-separated (e.g., "date,city" or "date")
                parsed_dimensions = [d.strip() for d in dimensions.split(',')]
        
        # Ensure all elements are non-empty strings after potential parsing
        parsed_dimensions = [str(d).strip() for d in parsed_dimensions if str(d).strip()]

        # Handle cases where metrics might be passed as a string
        parsed_metrics = metrics
        if isinstance(metrics, str):
            try:
                parsed_metrics = json.loads(metrics)
                if not isinstance(parsed_metrics, list):
                     parsed_metrics = [str(parsed_metrics)]
            except json.JSONDecodeError:
                parsed_metrics = [m.strip() for m in metrics.split(',')]
        
        parsed_metrics = [str(m).strip() for m in parsed_metrics if str(m).strip()]

        # Proceed if we have valid dimensions and metrics after parsing
        if not parsed_dimensions:
            return {"error": "Dimensions list cannot be empty after parsing."}
        if not parsed_metrics:
            return {"error": "Metrics list cannot be empty after parsing."}

        # GA4 API Call
        client = BetaAnalyticsDataClient()
        
        # Convert dimensions and metrics to GA4 API format
        dimension_objects = [Dimension(name=d) for d in parsed_dimensions]
        metric_objects = [Metric(name=m) for m in parsed_metrics]
        
        # Build the request
        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=dimension_objects,
            metrics=metric_objects,
            date_ranges=[DateRange(start_date=date_range_start, end_date=date_range_end)]
        )
        
        # Execute the request
        response = client.run_report(request)
        
        # Format the response into a more usable structure
        result = []
        for row_idx, row in enumerate(response.rows):
            data_row = {}
            
            # Extract dimension values
            for i, dimension_header in enumerate(response.dimension_headers):
                # Check if dimension_values has enough elements
                if i < len(row.dimension_values):
                    data_row[dimension_header.name] = row.dimension_values[i].value
                else:
                    data_row[dimension_header.name] = None
                
            # Extract metric values
            for i, metric_header in enumerate(response.metric_headers):
                 # Check if metric_values has enough elements
                if i < len(row.metric_values):
                    data_row[metric_header.name] = row.metric_values[i].value
                else:
                    data_row[metric_header.name] = None
                    
            result.append(data_row)
        
        return result
    except Exception as e:
        error_message = f"Error fetching GA4 data: {str(e)}"
        print(error_message, file=sys.stderr)
        # Include more details if available, e.g. from e.details() for gRPC errors
        if hasattr(e, 'details'):
            error_message += f" Details: {e.details()}"
        return {"error": error_message}

# Start the server when run directly
if __name__ == "__main__":
    # Use stdio transport ONLY - this is critical for MCP with Claude
    print("Starting GA4 MCP server...", file=sys.stderr)
    mcp.run(transport="stdio")