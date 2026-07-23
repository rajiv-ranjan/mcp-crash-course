import asyncio
import logging

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.agents import create_agent

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
            return ChatOllama(model="gemma4:12b",)
        else:
            logger.warning(f"Invalid model choice: {choice}. Please enter 1-3.")

async def main():
    # Select model before starting
    llm = choose_model()
    
    # Configure MCP servers
    logger.info("="*50)
    logger.info("Connecting to MCP Servers...")
    logger.info("="*50)
    
    try:
        client = MultiServerMCPClient(
            {
                "math": {
                    "transport": "stdio",
                    "command": "python3",
                    "args": ["./servers/math_server.py"],
                },
                "weather": {
                    "transport": "http",
                    "url": "http://localhost:8000/mcp",
                }
            }
        )
        
        # Load all tools from configured servers
        all_tools = await client.get_tools()
        tool_names = [tool.name for tool in all_tools]
        
        logger.info("✓ MCP servers connected successfully")
        logger.info(f"Total tools loaded: {len(all_tools)} - {tool_names}")
        logger.info("="*50)
        
    except Exception as e:
        logger.error("="*50)
        logger.error(f"✗ Failed to connect to MCP servers: {e}")
        logger.error("="*50)
        logger.error("Possible reasons:")
        logger.error("1. Math server (stdio): Check if ./servers/math_server.py exists")
        logger.error("2. Weather server (http): Ensure server is running at http://localhost:8000/mcp")
        logger.error("   Start it with: python3 servers/weather_server.py")
        logger.error("="*50)
        logger.error("Exiting application.")
        return
    
    # Create agent with all available tools
    agent = create_agent(llm, all_tools)
    logger.info(f"Agent created successfully with {len(all_tools)} tools")
    
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
    logger.info("Executing test query 1: What is 54 + 2 * 3?")
    result = await agent.ainvoke({"messages": [HumanMessage(content="What is 54 + 2 * 3?")]})
    logger.info(f"A: {result['messages'][-1].content}")
    
    logger.info("Executing test query 2: What is the weather in Bangalore? Take the temperature as T and perform T + 2 * 3?")
    result = await agent.ainvoke({"messages": [HumanMessage(content="What is the weather in Bangalore? Take the temperature as T and perform T + 2 * 3?")]})
    logger.info(f"A: {result['messages'][-1].content}")
        

if __name__ == "__main__":
    logger.info("Application started")
    asyncio.run(main())
    logger.info("Application finished")

