#!/bin/bash
# Start the Weather SSE MCP Server

echo "Starting Weather SSE MCP Server on http://localhost:8000/sse"
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 servers/weather_server.py
