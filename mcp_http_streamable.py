from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator
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
    title="GA4 MCP Streamable Server",
    description="MCP-compatible HTTP Streamable server for Google Analytics 4",
    version="1.0.0"
)

# Basic auth setup
security = HTTPBasic()

# Get auth credentials from environment
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "changeme")

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify basic auth credentials"""
    import logging
    logger = logging.getLogger("uvicorn")
    # TEMPORARILY DISABLED FOR TESTING
    logger.info(f"Auth DISABLED for testing")
    return "test_user"
    
    # logger.info(f"Auth attempt - Username: {credentials.username}, Expected: {API_USERNAME}")
    # 
    # is_correct_username = secrets.compare_digest(
    #     credentials.username.encode("utf8"),
    #     API_USERNAME.encode("utf8")
    # )
    # is_correct_password = secrets.compare_digest(
    #     credentials.password.encode("utf8"),
    #     API_PASSWORD.encode("utf8")
    # )
    # 
    # if not is_correct_username:
    #     logger.info(f"Auth failed - Incorrect username: {credentials.username}")
    # if not is_correct_password:
    #     logger.info(f"Auth failed - Incorrect password")
    # 
    # if not (is_correct_username and is_correct_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect username or password",
    #         headers={"WWW-Authenticate": "Basic"},
    #     )
    # 
    # logger.info(f"Auth success - User: {credentials.username}")
    # return credentials.username

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

async def stream_mcp_response(request: MCPRequest) -> AsyncGenerator[bytes, None]:
    """Generate streaming MCP responses"""
    try:
        response = None
        
        # Handle different MCP methods
        if request.method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "1.0.0",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": "ga4-analytics",
                        "version": "1.0.0"
                    }
                },
                "id": request.id
            }
        
        elif request.method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {
                            "name": "list_dimension_categories",
                            "description": "List all available GA4 dimension categories with descriptions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        },
                        {
                            "name": "list_metric_categories",
                            "description": "List all available GA4 metric categories with descriptions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
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
                                },
                                "required": []
                            }
                        }
                    ]
                },
                "id": request.id
            }
        
        elif request.method == "tools/call":
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            # Call the appropriate tool
            tool_result = None
            if tool_name == "list_dimension_categories":
                tool_result = list_dimension_categories.fn()
            elif tool_name == "list_metric_categories":
                tool_result = list_metric_categories.fn()
            elif tool_name == "get_dimensions_by_category":
                tool_result = get_dimensions_by_category.fn(
                    category=arguments.get("category")
                )
            elif tool_name == "get_metrics_by_category":
                tool_result = get_metrics_by_category.fn(
                    category=arguments.get("category")
                )
            elif tool_name == "get_ga4_data":
                tool_result = get_ga4_data.fn(
                    dimensions=arguments.get("dimensions", ["date"]),
                    metrics=arguments.get("metrics", ["totalUsers", "newUsers"]),
                    date_range_start=arguments.get("date_range_start", "7daysAgo"),
                    date_range_end=arguments.get("date_range_end", "yesterday"),
                    dimension_filter=arguments.get("dimension_filter")
                )
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    },
                    "id": request.id
                }
            
            if tool_result is not None:
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_result, indent=2)
                            }
                        ]
                    },
                    "id": request.id
                }
        
        elif request.method == "resources/list":
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "resources": []
                },
                "id": request.id
            }
        
        elif request.method == "prompts/list":
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "prompts": []
                },
                "id": request.id
            }
        
        else:
            response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                },
                "id": request.id
            }
        
        # Stream the response
        if response:
            yield json.dumps(response).encode('utf-8') + b'\n'
    
    except Exception as e:
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            },
            "id": request.id
        }
        yield json.dumps(error_response).encode('utf-8') + b'\n'

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "GA4 MCP Streamable Server",
        "protocol": "MCP over HTTP Streamable",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "stream": "/stream",
            "mcp": "/mcp",
            "health": "/"
        },
        "transport_types": ["http-streamable", "http"]
    }

@app.get("/stream", tags=["MCP"])
async def mcp_stream_info():
    """
    Stream endpoint info - returns streaming capabilities
    """
    print(f"GET /stream - User: test_user (auth disabled)", file=sys.stderr)
    response = {
        "type": "mcp-streamable",
        "version": "1.0.0",
        "server": "ga4-analytics",
        "endpoint": "/stream",
        "method": "POST",
        "content_type": "application/json",
        "response_type": "application/x-ndjson",
        "authentication": "Basic",
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False,
            "streaming": True
        }
    }
    print(f"GET /stream response: {json.dumps(response)[:100]}...", file=sys.stderr)
    return response

@app.post("/stream", tags=["MCP"])
async def mcp_stream_endpoint(
    request: Request
):
    """
    HTTP Streamable MCP endpoint - handles all MCP requests with streaming responses
    """
    print(f"POST /stream - User: test_user (auth disabled)", file=sys.stderr)
    print(f"Headers: {dict(request.headers)}", file=sys.stderr)
    
    try:
        # Parse the request body
        body = await request.json()
        print(f"Request body: {json.dumps(body)}", file=sys.stderr)
        
        mcp_request = MCPRequest(**body)
        print(f"MCP method: {mcp_request.method}, id: {mcp_request.id}", file=sys.stderr)
        
        # Return streaming response
        return StreamingResponse(
            stream_mcp_response(mcp_request),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        print(f"ERROR in POST /stream: {str(e)}", file=sys.stderr)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )

# Legacy endpoints for compatibility
@app.post("/mcp", tags=["MCP"])
async def mcp_endpoint(
    request: MCPRequest,
    username: str = Depends(verify_credentials)
):
    """
    Standard MCP endpoint (non-streaming)
    """
    # Convert streaming response to standard response
    response_data = b""
    async for chunk in stream_mcp_response(request):
        response_data += chunk
    
    return json.loads(response_data.decode('utf-8'))

@app.get("/mcp", tags=["MCP"])
async def mcp_info(username: str = Depends(verify_credentials)):
    """
    MCP info endpoint - returns server capabilities
    """
    return {
        "type": "mcp",
        "version": "1.0.0",
        "server": "ga4-analytics",
        "transports": ["http-streamable", "http"],
        "endpoints": {
            "stream": "/stream",
            "standard": "/mcp"
        },
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False,
            "logging": False
        },
        "authentication": "Basic"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting GA4 MCP Streamable Server on {host}:{port}", file=sys.stderr)
    print(f"HTTP Streamable endpoint: http://{host}:{port}/stream", file=sys.stderr)
    print(f"Standard MCP endpoint: http://{host}:{port}/mcp", file=sys.stderr)
    print(f"API docs: http://{host}:{port}/docs", file=sys.stderr)
    print(f"Auth configured - Username: {API_USERNAME}", file=sys.stderr)
    print(f"Environment check - GA4_PROPERTY_ID: {os.getenv('GA4_PROPERTY_ID', 'NOT SET')}", file=sys.stderr)
    
    uvicorn.run(app, host=host, port=port, log_level="info")