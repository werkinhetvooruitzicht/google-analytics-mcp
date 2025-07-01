#!/bin/bash

# Test MCP flow like n8n does
echo "Testing MCP flow (GET then POST)..."
echo "==================================="

# Your server details
BASE_URL="http://owc8o00osgwcgks880g8wkog.172.201.74.13.sslip.io"
USERNAME="ga4_8nx7aug8"
PASSWORD="XSvU3HfMb48Z2x2Jvqy6E9PqJzUrNP"

# Step 1: GET /stream
echo "[1] Testing GET /stream..."
echo "------------------------"
GET_RESPONSE=$(curl -s -N -H "Accept: text/event-stream" \
     -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" \
     "$BASE_URL/stream")

echo "$GET_RESPONSE" | head -20
echo "..."
echo ""

# Step 2: POST /stream with initialize
echo "[2] Testing POST /stream with initialize..."
echo "-----------------------------------------"
POST_RESPONSE=$(curl -s -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{"tools":{}}},"id":1}' \
     -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" \
     "$BASE_URL/stream")

echo "$POST_RESPONSE"
echo ""

# Step 3: POST /stream with tools/list
echo "[3] Testing POST /stream with tools/list..."
echo "------------------------------------------"
TOOLS_RESPONSE=$(curl -s -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' \
     -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" \
     "$BASE_URL/stream")

echo "$TOOLS_RESPONSE"
echo ""

echo "==================================="
echo "Test complete!"
echo ""
echo "Expected results:"
echo "1. GET should return SSE stream immediately"
echo "2. POST initialize should return JSON-RPC response"
echo "3. POST tools/list should return list of available tools"