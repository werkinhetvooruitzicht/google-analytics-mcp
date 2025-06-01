from fastmcp import FastMCP
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, Filter, FilterExpression, FilterExpressionList
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
        with open(script_dir / "ga4_dimensions_json.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: ga4_dimensions_json.json not found", file=sys.stderr)
        return {}

def load_metrics():
    """Load available metrics from JSON file"""
    try:
        script_dir = Path(__file__).parent
        with open(script_dir / "ga4_metrics_json.json", "r") as f:
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
    date_range_end="yesterday",
    dimension_filter=None
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
        dimension_filter: (Optional) JSON string or dict representing a GA4 FilterExpression. See GA4 API docs for structure.
        
    Returns:
        List of dictionaries containing the requested data, or an error dictionary.
    """
    try:
        # Handle cases where dimensions might be passed as a string from the MCP client
        parsed_dimensions = dimensions
        if isinstance(dimensions, str):
            try:
                parsed_dimensions = json.loads(dimensions)
                if not isinstance(parsed_dimensions, list):
                    parsed_dimensions = [str(parsed_dimensions)]
            except json.JSONDecodeError:
                parsed_dimensions = [d.strip() for d in dimensions.split(',')]
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

        # Validate dimension_filter and build FilterExpression if provided
        filter_expression = None
        if dimension_filter:
            print(f"DEBUG: Processing dimension_filter: {dimension_filter}", file=sys.stderr)
            
            # Load valid dimensions from ga4_dimensions_json.json
            valid_dimensions = set()
            dims_json = load_dimensions()
            for cat in dims_json.values():
                valid_dimensions.update(cat.keys())
            
            # Parse filter input
            if isinstance(dimension_filter, str):
                try:
                    filter_dict = json.loads(dimension_filter)
                except Exception as e:
                    return {"error": f"Failed to parse dimension_filter JSON: {e}"}
            elif isinstance(dimension_filter, dict):
                filter_dict = dimension_filter
            else:
                return {"error": "dimension_filter must be a JSON string or dict."}

            # Recursive helper to build FilterExpression from dict
            def build_filter_expr(expr):
                try:
                    if 'andGroup' in expr:
                        expressions = []
                        for e in expr['andGroup']['expressions']:
                            built_expr = build_filter_expr(e)
                            if built_expr is None:
                                return None
                            expressions.append(built_expr)
                        return FilterExpression(and_group=FilterExpressionList(expressions=expressions))
                    
                    if 'orGroup' in expr:
                        expressions = []
                        for e in expr['orGroup']['expressions']:
                            built_expr = build_filter_expr(e)
                            if built_expr is None:
                                return None
                            expressions.append(built_expr)
                        return FilterExpression(or_group=FilterExpressionList(expressions=expressions))
                    
                    if 'notExpression' in expr:
                        built_expr = build_filter_expr(expr['notExpression'])
                        if built_expr is None:
                            return None
                        return FilterExpression(not_expression=built_expr)
                    
                    if 'filter' in expr:
                        f = expr['filter']
                        field = f.get('fieldName')
                        if not field:
                            print(f"DEBUG: Missing fieldName in filter: {f}", file=sys.stderr)
                            return None
                        if field not in valid_dimensions:
                            print(f"DEBUG: Invalid dimension '{field}'. Valid: {sorted(list(valid_dimensions))[:10]}...", file=sys.stderr)
                            return None
                        
                        if 'stringFilter' in f:
                            sf = f['stringFilter']
                            # Map string match types to API enum values
                            match_type_map = {
                                'EXACT': Filter.StringFilter.MatchType.EXACT,
                                'BEGINS_WITH': Filter.StringFilter.MatchType.BEGINS_WITH,
                                'ENDS_WITH': Filter.StringFilter.MatchType.ENDS_WITH,
                                'CONTAINS': Filter.StringFilter.MatchType.CONTAINS,
                                'FULL_REGEXP': Filter.StringFilter.MatchType.FULL_REGEXP,
                                'PARTIAL_REGEXP': Filter.StringFilter.MatchType.PARTIAL_REGEXP
                            }
                            match_type = match_type_map.get(sf.get('matchType', 'EXACT'), Filter.StringFilter.MatchType.EXACT)
                            
                            return FilterExpression(filter=Filter(
                                field_name=field,
                                string_filter=Filter.StringFilter(
                                    value=sf.get('value', ''),
                                    match_type=match_type,
                                    case_sensitive=sf.get('caseSensitive', False)
                                )
                            ))
                        
                        if 'inListFilter' in f:
                            ilf = f['inListFilter']
                            return FilterExpression(filter=Filter(
                                field_name=field,
                                in_list_filter=Filter.InListFilter(
                                    values=ilf.get('values', []),
                                    case_sensitive=ilf.get('caseSensitive', False)
                                )
                            ))
                    
                    print(f"DEBUG: Unrecognized filter structure: {expr}", file=sys.stderr)
                    return None
                    
                except Exception as e:
                    print(f"DEBUG: Exception in build_filter_expr: {e}", file=sys.stderr)
                    return None
            
            filter_expression = build_filter_expr(filter_dict)
            if filter_expression is None:
                return {"error": "Invalid or unsupported dimension_filter structure, or invalid dimension name."}

        # GA4 API Call
        client = BetaAnalyticsDataClient()
        dimension_objects = [Dimension(name=d) for d in parsed_dimensions]
        metric_objects = [Metric(name=m) for m in parsed_metrics]
        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=dimension_objects,
            metrics=metric_objects,
            date_ranges=[DateRange(start_date=date_range_start, end_date=date_range_end)],
            dimension_filter=filter_expression if filter_expression else None
        )
        response = client.run_report(request)
        result = []
        for row_idx, row in enumerate(response.rows):
            data_row = {}
            for i, dimension_header in enumerate(response.dimension_headers):
                if i < len(row.dimension_values):
                    data_row[dimension_header.name] = row.dimension_values[i].value
                else:
                    data_row[dimension_header.name] = None
            for i, metric_header in enumerate(response.metric_headers):
                if i < len(row.metric_values):
                    data_row[metric_header.name] = row.metric_values[i].value
                else:
                    data_row[metric_header.name] = None
            result.append(data_row)
        return result
    except Exception as e:
        error_message = f"Error fetching GA4 data: {str(e)}"
        print(error_message, file=sys.stderr)
        if hasattr(e, 'details'):
            error_message += f" Details: {e.details()}"
        return {"error": error_message}

# Start the server when run directly
if __name__ == "__main__":
    # Use stdio transport ONLY - this is critical for MCP with Claude
    print("Starting GA4 MCP server...", file=sys.stderr)
    mcp.run(transport="stdio")