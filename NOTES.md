# MCP Crash Course - Multi-Server Setup

This project demonstrates connecting to multiple MCP servers (stdio and SSE) using LangChain MCP Adapters.

## Architecture

```
┌─────────────────┐
│   LangChain     │
│     Agent       │
└────────┬────────┘
         │
         ├─────────────┬─────────────┐
         │             │             │
    ┌────▼────┐   ┌───▼────┐   ┌───▼────┐
    │  Model  │   │ Math   │   │Weather │
    │ (LLM)   │   │ Tools  │   │ Tools  │
    └─────────┘   └────────┘   └────────┘
                  (stdio MCP)  (SSE MCP)
```

## MCP Servers

### 1. Math Server (stdio)
- **Transport**: stdio (launched automatically)
- **Location**: `servers/math_server.py`
- **Tools**:
  - `add(a, b)` - Add two numbers
  - `multiply(a, b)` - Multiply two numbers

### 2. Weather Server (SSE)
- **Transport**: SSE (Server-Sent Events over HTTP)
- **Location**: `servers/weather_server.py`
- **URL**: `http://localhost:8000/sse`
- **Tools**:
  - `get_weather(location)` - Get weather for a location
- **Note**: Must be started manually before running main.py

## Setup Instructions

### 1. Install Dependencies

```bash
uv sync
```

### 2. Start the Weather Server (Terminal 1)

```bash
# Option 1: Use the helper script
./start_weather_server.sh

# Option 2: Run directly
python3 servers/weather_server.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000
```

### 3. Run the Main Application (Terminal 2)

```bash
uv run python main.py
```

## How It Works

### Connection Flow

1. **Model Selection**: Choose between OpenAI or local Ollama models
2. **stdio Server**: Automatically launched and connected (Math server)
3. **SSE Server**: Connects to already-running weather server at `http://localhost:8000/sse`
4. **Tool Loading**: Tools from both servers are loaded via `langchain-mcp-adapters`
5. **Agent Creation**: A single agent is created with combined tools from both servers
6. **Query Execution**: Agent can use any tool from either server

### Code Structure

```python
# Connect to stdio server (auto-launched)
async with stdio_client(STDIO_SERVER_PARAMS) as (read, write):
    async with ClientSession(...) as stdio_session:
        stdio_tools = await load_mcp_tools(stdio_session)
        
        # Connect to SSE server (must be running)
        async with sse_client(SSE_SERVER_URL) as (sse_read, sse_write):
            async with ClientSession(...) as sse_session:
                sse_tools = await load_mcp_tools(sse_session)
                
                # Combine all tools
                all_tools = stdio_tools + sse_tools
                
                # Create agent with all tools
                agent = create_agent(llm, all_tools, system_prompt=...)
```

## Example Queries

The application runs two test queries:

### Query 1: Math Calculation
```
Q: What is 54 + 2 * 3?
A: 60 (uses multiply and add tools from Math server)
```

### Query 2: Weather + Math
```
Q: What is the weather in Bangalore? Take the temperature as T and perform T + 2 * 3?
A: Bangalore Weather — Humidity: 40%, Temperature: 28°C. T + 2 * 3 = 34
(uses get_weather from Weather server, then multiply and add from Math server)
```

## Configuration

### Change SSE Server URL

Edit in `main.py`:
```python
SSE_SERVER_URL = "http://localhost:8000/sse"  # Change port if needed
```

### Change stdio Server

Edit in `main.py`:
```python
STDIO_SERVER_PARAMS = StdioServerParameters(
    command="python3",
    args=["./servers/your_server.py"],  # Change server file
)
```

## Error Handling

If the SSE server is not running, you'll see:
```
✗ Failed to connect to SSE MCP server: [error details]
  Make sure the weather server is running at http://localhost:8000/sse
  Continuing with stdio tools only...
```

The application will continue with only the stdio tools (math operations).

## Troubleshooting

### Weather Server Won't Start

**Error**: Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Connection Refused to SSE Server

1. Verify server is running: `curl http://localhost:8000/sse`
2. Check firewall settings
3. Ensure URL in `main.py` matches server URL

### Tool Calls Not Working

Check the AGENT CONFIGURATION output shows all expected tools:
```
Available Tools: ['add', 'multiply', 'get_weather']
Number of Tools: 3
```

## System Prompt

The agent uses a strict system prompt to ensure it always uses tools:

```
IMPORTANT RULES:
1. DO NOT assume or make up any data, values, or information
2. If you need live data, current information, or any computation - YOU MUST call the appropriate tool
3. ALWAYS use available tools for calculations, data retrieval, or any task they can perform
4. If a tool is not available for the requested task, clearly state that you cannot perform it
5. Be precise and only provide information that comes from tool results or is explicitly stated by the user
```

This prevents the LLM from making up data and forces it to use available tools.
