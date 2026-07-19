# math_server.py
import logging

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    logger.debug(f"add called with a={a}, b={b}")
    result = a + b
    logger.info(f"Addition: {a} + {b} = {result}")
    return result

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    logger.debug(f"multiply called with a={a}, b={b}")
    result = a * b
    logger.info(f"Multiplication: {a} * {b} = {result}")
    return result

if __name__ == "__main__":
    logger.info("Starting Math MCP Server (stdio transport)")
    mcp.run(transport="stdio")