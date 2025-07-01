from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
import uvicorn
import os
import sys
import secrets
from datetime import datetime

# Import the GA4 functions from the MCP server
from ga4_mcp_server import (
    load_dimensions, load_metrics, GA4_PROPERTY_ID,
    credentials, BetaAnalyticsDataClient, DateRange, Dimension, 
    Metric, RunReportRequest, Filter, FilterExpression, 
    FilterExpressionList
)
import json

app = FastAPI(
    title="GA4 Analytics API for n8n",
    description="HTTP API wrapper for Google Analytics 4 data access",
    version="1.0.0"
)

# Basic auth setup
security = HTTPBasic()

# Get auth credentials from environment
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "changeme")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify basic auth credentials"""
    # TEMPORARILY DISABLED FOR TESTING
    return "test_user"
    
    # is_correct_username = secrets.compare_digest(
    #     credentials.username.encode("utf8"),
    #     API_USERNAME.encode("utf8")
    # )
    # is_correct_password = secrets.compare_digest(
    #     credentials.password.encode("utf8"),
    #     API_PASSWORD.encode("utf8")
    # )
    # if not (is_correct_username and is_correct_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect username or password",
    #         headers={"WWW-Authenticate": "Basic"},
    #     )
    # return credentials.username

# Add CORS middleware to allow n8n to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your n8n domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class GA4DataRequest(BaseModel):
    dimensions: Union[List[str], str] = Field(
        default=["date"],
        description="List of GA4 dimensions or comma-separated string"
    )
    metrics: Union[List[str], str] = Field(
        default=["totalUsers", "newUsers", "bounceRate"],
        description="List of GA4 metrics or comma-separated string"
    )
    date_range_start: str = Field(
        default="7daysAgo",
        description="Start date (YYYY-MM-DD or relative like '7daysAgo')"
    )
    date_range_end: str = Field(
        default="yesterday",
        description="End date (YYYY-MM-DD or relative like 'yesterday')"
    )
    dimension_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="GA4 FilterExpression as JSON object"
    )

class CategoryResponse(BaseModel):
    count: int
    items: List[str]

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "GA4 Analytics API",
        "property_id": GA4_PROPERTY_ID,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/dimensions", tags=["Metadata"])
async def list_dimensions(username: str = Depends(verify_credentials)):
    """List all available dimension categories"""
    dimensions = load_dimensions()
    result = {}
    for category, dims in dimensions.items():
        result[category] = {
            "count": len(dims),
            "dimensions": list(dims.keys())
        }
    return result

@app.get("/dimensions/{category}", tags=["Metadata"])
async def get_dimensions_by_category(category: str, username: str = Depends(verify_credentials)):
    """Get all dimensions in a specific category with descriptions"""
    dimensions = load_dimensions()
    if category in dimensions:
        return dimensions[category]
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found. Available: {list(dimensions.keys())}"
        )

@app.get("/metrics", tags=["Metadata"])
async def list_metrics(username: str = Depends(verify_credentials)):
    """List all available metric categories"""
    metrics = load_metrics()
    result = {}
    for category, mets in metrics.items():
        result[category] = {
            "count": len(mets),
            "metrics": list(mets.keys())
        }
    return result

@app.get("/metrics/{category}", tags=["Metadata"])
async def get_metrics_by_category(category: str, username: str = Depends(verify_credentials)):
    """Get all metrics in a specific category with descriptions"""
    metrics = load_metrics()
    if category in metrics:
        return metrics[category]
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found. Available: {list(metrics.keys())}"
        )

@app.post("/data", tags=["Analytics"])
async def get_ga4_data(request: GA4DataRequest, username: str = Depends(verify_credentials)):
    """
    Retrieve GA4 analytics data
    
    Example request body:
    ```json
    {
        "dimensions": ["date", "country"],
        "metrics": ["totalUsers", "sessions"],
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
    """
    try:
        # Parse dimensions
        parsed_dimensions = request.dimensions
        if isinstance(request.dimensions, str):
            parsed_dimensions = [d.strip() for d in request.dimensions.split(',')]
        
        # Parse metrics
        parsed_metrics = request.metrics
        if isinstance(request.metrics, str):
            parsed_metrics = [m.strip() for m in request.metrics.split(',')]
        
        # Validate inputs
        if not parsed_dimensions:
            raise HTTPException(status_code=400, detail="Dimensions list cannot be empty")
        if not parsed_metrics:
            raise HTTPException(status_code=400, detail="Metrics list cannot be empty")
        
        # Build filter expression if provided
        filter_expression = None
        if request.dimension_filter:
            filter_expression = build_filter_expression(request.dimension_filter)
            if filter_expression is None:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid dimension_filter structure or invalid dimension name"
                )
        
        # Make GA4 API call
        if credentials:
            client = BetaAnalyticsDataClient(credentials=credentials)
        else:
            client = BetaAnalyticsDataClient()
        
        dimension_objects = [Dimension(name=d) for d in parsed_dimensions]
        metric_objects = [Metric(name=m) for m in parsed_metrics]
        
        api_request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=dimension_objects,
            metrics=metric_objects,
            date_ranges=[DateRange(
                start_date=request.date_range_start,
                end_date=request.date_range_end
            )],
            dimension_filter=filter_expression
        )
        
        response = client.run_report(api_request)
        
        # Format response
        result = []
        for row in response.rows:
            data_row = {}
            for i, dimension_header in enumerate(response.dimension_headers):
                if i < len(row.dimension_values):
                    data_row[dimension_header.name] = row.dimension_values[i].value
            for i, metric_header in enumerate(response.metric_headers):
                if i < len(row.metric_values):
                    data_row[metric_header.name] = row.metric_values[i].value
            result.append(data_row)
        
        return {
            "data": result,
            "rowCount": len(result),
            "dimensions": parsed_dimensions,
            "metrics": parsed_metrics,
            "dateRange": {
                "start": request.date_range_start,
                "end": request.date_range_end
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching GA4 data: {str(e)}"
        )

def build_filter_expression(filter_dict: Dict[str, Any]) -> Optional[FilterExpression]:
    """Build GA4 FilterExpression from dictionary"""
    try:
        # Load valid dimensions
        valid_dimensions = set()
        dims_json = load_dimensions()
        for cat in dims_json.values():
            valid_dimensions.update(cat.keys())
        
        return _build_filter_expr_recursive(filter_dict, valid_dimensions)
    except Exception as e:
        print(f"Error building filter expression: {e}", file=sys.stderr)
        return None

def _build_filter_expr_recursive(expr: Dict[str, Any], valid_dimensions: set) -> Optional[FilterExpression]:
    """Recursive helper to build FilterExpression"""
    if 'andGroup' in expr:
        expressions = []
        for e in expr['andGroup']['expressions']:
            built_expr = _build_filter_expr_recursive(e, valid_dimensions)
            if built_expr is None:
                return None
            expressions.append(built_expr)
        return FilterExpression(and_group=FilterExpressionList(expressions=expressions))
    
    if 'orGroup' in expr:
        expressions = []
        for e in expr['orGroup']['expressions']:
            built_expr = _build_filter_expr_recursive(e, valid_dimensions)
            if built_expr is None:
                return None
            expressions.append(built_expr)
        return FilterExpression(or_group=FilterExpressionList(expressions=expressions))
    
    if 'notExpression' in expr:
        built_expr = _build_filter_expr_recursive(expr['notExpression'], valid_dimensions)
        if built_expr is None:
            return None
        return FilterExpression(not_expression=built_expr)
    
    if 'filter' in expr:
        f = expr['filter']
        field = f.get('fieldName')
        if not field or field not in valid_dimensions:
            return None
        
        if 'stringFilter' in f:
            sf = f['stringFilter']
            match_type_map = {
                'EXACT': Filter.StringFilter.MatchType.EXACT,
                'BEGINS_WITH': Filter.StringFilter.MatchType.BEGINS_WITH,
                'ENDS_WITH': Filter.StringFilter.MatchType.ENDS_WITH,
                'CONTAINS': Filter.StringFilter.MatchType.CONTAINS,
                'FULL_REGEXP': Filter.StringFilter.MatchType.FULL_REGEXP,
                'PARTIAL_REGEXP': Filter.StringFilter.MatchType.PARTIAL_REGEXP
            }
            match_type = match_type_map.get(
                sf.get('matchType', 'EXACT'),
                Filter.StringFilter.MatchType.EXACT
            )
            
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
    
    return None

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting GA4 HTTP API server on {host}:{port}")
    print(f"API docs available at http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)