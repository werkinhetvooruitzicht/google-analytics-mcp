#!/bin/bash

# Test SSE buffering with curl
echo "Testing SSE streaming for buffering issues..."
echo "============================================"

# Your server details
URL="http://owc8o00osgwcgks880g8wkog.172.201.74.13.sslip.io/stream"
USERNAME="ga4_8nx7aug8"
PASSWORD="XSvU3HfMb48Z2x2Jvqy6E9PqJzUrNP"

echo "Testing GET /stream with curl..."
echo "If buffering is disabled, you should see immediate output:"
echo ""

# Test with curl - show timing
curl -N -H "Accept: text/event-stream" \
     -w "\n\nTime stats:\nTotal time: %{time_total}s\nTime to first byte: %{time_starttransfer}s\n" \
     "$URL" 2>&1 | while IFS= read -r line; do
    echo "[$(date +%H:%M:%S.%3N)] $line"
done

echo ""
echo "============================================"
echo "Test complete!"
echo ""
echo "What to look for:"
echo "1. The response should appear immediately (not after a delay)"
echo "2. Time to first byte should be < 1 second"
echo "3. You should see the SSE data streaming in real-time"
echo ""
echo "If you see a long delay before output, buffering is still enabled."