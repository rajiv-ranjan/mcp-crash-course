import asyncio
import logging
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# MCP Server Configuration
STDIO_SERVER_PARAMS = StdioServerParameters(
    command="python3",
    args=["./servers/math_server.py"],
)

# SSE Server URL (assuming it runs on default port)
SSE_SERVER_URL = "http://localhost:8000/sse"

def choose_model():
    """Interactive model selection"""
    logger.info("=== Select LLM Model ===")
    logger.info("1. OpenAI (gpt-4o-mini)")
    logger.info("2. Ollama - llama3.2:3b")
    logger.info("3. Ollama - gemma4:12b")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            logger.info("User selected OpenAI model (gpt-4o-mini)")
            return ChatOpenAI()
        elif choice == "2":
            logger.info("User selected Ollama llama3.2:3b")
            return ChatOllama(model="llama3.2:3b")
        elif choice == "3":
            logger.info("User selected Ollama gemma4:12b")
            return ChatOllama(model="gemma4:12b")
        else:
            logger.warning(f"Invalid model choice: {choice}. Please enter 1-3.")

async def initialize_mcp_servers(stack: AsyncExitStack):
    """
    Initialize and connect to MCP servers (stdio and SSE).
    
    Args:
        stack: AsyncExitStack to manage async context managers
        
    Returns:
        tuple: (all_tools, sse_connected)
            - all_tools: List of tools from all connected servers
            - sse_connected: Boolean indicating if SSE server connected successfully
    """
    all_tools = []
    
    logger.info("="*50)
    logger.info("Connecting to MCP Servers...")
    logger.info("="*50)
    
    # Connect to stdio MCP server (math_server)
    stdio_read, stdio_write = await stack.enter_async_context(
        stdio_client(STDIO_SERVER_PARAMS)
    )
    stdio_session = await stack.enter_async_context(
        ClientSession(read_stream=stdio_read, write_stream=stdio_write)
    )
    
    init_result = await stdio_session.initialize()
    mcp_server_name = init_result.serverInfo.name if init_result and init_result.serverInfo else "Unknown"
    logger.info(f"✓ Stdio MCP server ({mcp_server_name}) connected successfully")
    
    stdio_tools = await load_mcp_tools(stdio_session)
    stdio_tool_names = [tool.name for tool in stdio_tools]
    logger.info(f"Stdio tools loaded: {stdio_tool_names}")
    all_tools.extend(stdio_tools)
    
    # Try to connect to SSE MCP server (weather_server)
    sse_connected = False
    try:
        sse_read, sse_write = await stack.enter_async_context(
            sse_client(SSE_SERVER_URL)
        )
        sse_session = await stack.enter_async_context(
            ClientSession(read_stream=sse_read, write_stream=sse_write)
        )
        
        init_result = await sse_session.initialize()
        mcp_server_name = init_result.serverInfo.name if init_result and init_result.serverInfo else "Unknown"
        logger.info(f"✓ SSE MCP server ({mcp_server_name}) connected successfully")
        
        sse_tools = await load_mcp_tools(sse_session)
        sse_tool_names = [tool.name for tool in sse_tools]
        logger.info(f"SSE tools loaded: {sse_tool_names}")
        all_tools.extend(sse_tools)
        sse_connected = True
        
    except Exception as e:
        logger.error(f"✗ Failed to connect to SSE MCP server: {e}")
        logger.warning(f"Make sure the weather server is running at {SSE_SERVER_URL}")
        logger.info("Continuing with stdio tools only...")
    
    # Display total tools loaded
    tool_names = [tool.name for tool in all_tools]
    logger.info(f"Total tools loaded: {len(all_tools)} - {tool_names}")
    if not sse_connected:
        logger.warning("SSE server unavailable - using stdio tools only")
    logger.info("="*50)
    
    return all_tools, sse_connected

async def main():
    # Select model before starting
    llm = choose_model()
    
    # Connect to both MCP servers using AsyncExitStack for clean parallel management
    async with AsyncExitStack() as stack:
        # Initialize MCP servers and load tools
        all_tools, sse_connected = await initialize_mcp_servers(stack)
        
        # Get tool names for display
        tool_names = [tool.name for tool in all_tools]

        # Define system prompt with tool-calling instructions
        system_prompt = """You are a helpful assistant with access to tools. Follow these rules:

IMPORTANT RULES:
1. DO NOT assume or make up any data, values, or information
2. If you need live data, current information, or any computation - YOU MUST call the appropriate tool
3. ALWAYS use available tools for calculations, data retrieval, or any task they can perform
4. If a tool is not available for the requested task, clearly state that you cannot perform it
5. Be precise and only provide information that comes from tool results or is explicitly stated by the user

TOOL-SPECIFIC INSTRUCTIONS:

Weather Tool (get_weather):
- When users ask about weather, temperature, humidity, climate, or weather conditions for any location, use the get_weather tool
- Extract the location name from the user's query and pass it as the location parameter
- Examples: "What's the weather in Bangalore?", "How hot is Mumbai?", "Tell me the temperature in Delhi"

Math Tools (add, multiply):
- Use these tools for any arithmetic calculations
- Do not calculate manually - always call the appropriate tool
"""

        # Create agent once with all available tools
        agent = create_agent(llm, all_tools, system_prompt=system_prompt)
        logger.info(f"Agent created successfully with {len(all_tools)} tools (with system prompt)")
        
        # Display configuration summary
        logger.info("="*50)
        logger.info("AGENT CONFIGURATION")
        logger.info("="*50)
        logger.info(f"LLM Model: {llm.__class__.__name__}")
        if hasattr(llm, 'model_name'):
            logger.info(f"Model Name: {llm.model_name}")
        elif hasattr(llm, 'model'):
            logger.info(f"Model Name: {llm.model}")
        logger.info(f"Available Tools: {tool_names}")
        logger.info(f"Number of Tools: {len(all_tools)}")
        logger.info("="*50)

        # Execute test queries
        logger.info("Executing test query 1: Math calculation")
        result = await agent.ainvoke({"messages": [HumanMessage(content="What is 54 + 2 * 3?")]})
        logger.info("Q: What is 54 + 2 * 3?")
        logger.info(f"A: {result['messages'][-1].content}")
        logger.debug(f"Query 1 full response: {result['messages'][-1].content}")

        logger.info("Executing test query 2: Weather + Math calculation")
        result = await agent.ainvoke({"messages": [HumanMessage(content="What is the weather in Bangalore? Take the temperature as T and perform T + 2 * 3?")]})
        logger.info("Q: What is the weather in Bangalore? Take the temperature as T and perform T + 2 * 3?")
        logger.info(f"A: {result['messages'][-1].content}")
        logger.debug(f"Query 2 full response: {result['messages'][-1].content}")

if __name__ == "__main__":
    logger.info("Application started")
    asyncio.run(main())
    logger.info("Application finished")

