from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys
import secrets
import json
import asyncio
from datetime import datetime

# Import MCP functions
from ga4_mcp_server import (
    list_dimension_categories,
    list_metric_categories,
    get_dimensions_by_category,
    get_metrics_by_category,
    get_ga4_data
)

app = FastAPI(
    title="GA4 MCP Bridge for n8n",
    description="MCP-compatible HTTP bridge for Google Analytics 4",
    version="1.0.0"
)

# Basic auth setup
security = HTTPBasic()

# Get auth credentials from environment
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "changeme")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify basic auth credentials"""
    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        API_USERNAME.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        API_PASSWORD.encode("utf8")
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP Protocol Models
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[int] = None

class MCPError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[MCPError] = None
    id: Optional[int] = None

# MCP endpoints
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "GA4 MCP Bridge",
        "protocol": "MCP over HTTP",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/mcp", tags=["MCP"])
async def mcp_endpoint(
    request: MCPRequest,
    username: str = Depends(verify_credentials)
):
    """
    MCP Protocol endpoint - handles all MCP requests
    
    Example request:
    ```json
    {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
    ```
    """
    try:
        # Handle different MCP methods
        if request.method == "initialize":
            return MCPResponse(
                jsonrpc="2.0",
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "ga4-analytics",
                        "version": "1.0.0"
                    }
                },
                id=request.id
            )
        
        elif request.method == "tools/list":
            return MCPResponse(
                jsonrpc="2.0",
                result={
                    "tools": [
                        {
                            "name": "list_dimension_categories",
                            "description": "List all available GA4 dimension categories with descriptions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "list_metric_categories",
                            "description": "List all available GA4 metric categories with descriptions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_dimensions_by_category",
                            "description": "Get all dimensions in a specific category with their descriptions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "category": {
                                        "type": "string",
                                        "description": "Category name (e.g., 'time', 'geography', 'ecommerce')"
                                    }
                                },
                                "required": ["category"]
                            }
                        },
                        {
                            "name": "get_metrics_by_category",
                            "description": "Get all metrics in a specific category with their descriptions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "category": {
                                        "type": "string",
                                        "description": "Category name (e.g., 'user_metrics', 'ecommerce_metrics')"
                                    }
                                },
                                "required": ["category"]
                            }
                        },
                        {
                            "name": "get_ga4_data",
                            "description": "Retrieve GA4 metrics data broken down by the specified dimensions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "dimensions": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "default": ["date"],
                                        "description": "List of GA4 dimensions"
                                    },
                                    "metrics": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "default": ["totalUsers", "newUsers"],
                                        "description": "List of GA4 metrics"
                                    },
                                    "date_range_start": {
                                        "type": "string",
                                        "default": "7daysAgo",
                                        "description": "Start date (YYYY-MM-DD or relative)"
                                    },
                                    "date_range_end": {
                                        "type": "string",
                                        "default": "yesterday",
                                        "description": "End date (YYYY-MM-DD or relative)"
                                    },
                                    "dimension_filter": {
                                        "type": "object",
                                        "description": "Optional GA4 FilterExpression"
                                    }
                                }
                            }
                        }
                    ]
                },
                id=request.id
            )
        
        elif request.method == "tools/call":
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            # Call the appropriate tool
            if tool_name == "list_dimension_categories":
                result = list_dimension_categories()
            elif tool_name == "list_metric_categories":
                result = list_metric_categories()
            elif tool_name == "get_dimensions_by_category":
                result = get_dimensions_by_category(
                    category=arguments.get("category")
                )
            elif tool_name == "get_metrics_by_category":
                result = get_metrics_by_category(
                    category=arguments.get("category")
                )
            elif tool_name == "get_ga4_data":
                result = get_ga4_data(
                    dimensions=arguments.get("dimensions", ["date"]),
                    metrics=arguments.get("metrics", ["totalUsers", "newUsers"]),
                    date_range_start=arguments.get("date_range_start", "7daysAgo"),
                    date_range_end=arguments.get("date_range_end", "yesterday"),
                    dimension_filter=arguments.get("dimension_filter")
                )
            else:
                return MCPResponse(
                    jsonrpc="2.0",
                    error=MCPError(
                        code=-32601,
                        message=f"Unknown tool: {tool_name}"
                    ),
                    id=request.id
                )
            
            return MCPResponse(
                jsonrpc="2.0",
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                },
                id=request.id
            )
        
        else:
            return MCPResponse(
                jsonrpc="2.0",
                error=MCPError(
                    code=-32601,
                    message=f"Method not found: {request.method}"
                ),
                id=request.id
            )
    
    except Exception as e:
        return MCPResponse(
            jsonrpc="2.0",
            error=MCPError(
                code=-32603,
                message="Internal error",
                data=str(e)
            ),
            id=request.id
        )

# Legacy REST endpoints for backward compatibility
@app.get("/api/dimensions", tags=["REST API"])
async def list_dimensions_rest(username: str = Depends(verify_credentials)):
    """REST endpoint for listing dimensions"""
    return list_dimension_categories()

@app.get("/api/metrics", tags=["REST API"])
async def list_metrics_rest(username: str = Depends(verify_credentials)):
    """REST endpoint for listing metrics"""
    return list_metric_categories()

@app.get("/api/dimensions/{category}", tags=["REST API"])
async def get_dimensions_by_category_rest(
    category: str,
    username: str = Depends(verify_credentials)
):
    """REST endpoint for getting dimensions by category"""
    return get_dimensions_by_category(category)

@app.get("/api/metrics/{category}", tags=["REST API"])
async def get_metrics_by_category_rest(
    category: str,
    username: str = Depends(verify_credentials)
):
    """REST endpoint for getting metrics by category"""
    return get_metrics_by_category(category)

class GA4DataRequest(BaseModel):
    dimensions: List[str] = Field(default=["date"])
    metrics: List[str] = Field(default=["totalUsers", "newUsers"])
    date_range_start: str = Field(default="7daysAgo")
    date_range_end: str = Field(default="yesterday")
    dimension_filter: Optional[Dict[str, Any]] = None

@app.post("/api/data", tags=["REST API"])
async def get_ga4_data_rest(
    request: GA4DataRequest,
    username: str = Depends(verify_credentials)
):
    """REST endpoint for getting GA4 data"""
    return get_ga4_data(
        dimensions=request.dimensions,
        metrics=request.metrics,
        date_range_start=request.date_range_start,
        date_range_end=request.date_range_end,
        dimension_filter=request.dimension_filter
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting GA4 MCP Bridge on {host}:{port}")
    print(f"MCP endpoint: http://{host}:{port}/mcp")
    print(f"API docs: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)