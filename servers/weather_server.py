import logging
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location.
    
    Returns fixed humidity and temperature for each.
    Other cities return default humidity=0, temperature=30.
    """
    logger.debug(f"get_weather called with location: {location}")
    
    city = location.strip().lower()
    if city == "bangalore":
        humidity = 40
        temperature = 28
    elif city == "mumbai":
        humidity = 80
        temperature = 35
    else:
        humidity = 0
        temperature = 30
    
    result = f"{location.title()} Weather — Humidity: {humidity}%, Temperature: {temperature}°C"
    logger.info(f"Weather data retrieved for {location.title()}: Temperature={temperature}°C, Humidity={humidity}%")
    return result

if __name__ == "__main__":
    logger.info("Starting Weather MCP Server (SSE transport)")
    mcp.run(transport="sse")