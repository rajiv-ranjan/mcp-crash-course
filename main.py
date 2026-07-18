import asyncio

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

def choose_model():
    """Interactive model selection"""
    print("\n=== Select LLM Model ===")
    print("1. OpenAI (gpt-4o-mini)")
    print("2. Ollama - llama3.2:3b")
    print("3. Ollama - gemma4:12b")
    print("4. Ollama - phi4")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            print("Using OpenAI model...")
            return ChatOpenAI()
        elif choice == "2":
            print("Using Ollama llama3.2:3b...")
            return ChatOllama(model="llama3.2:3b")
        elif choice == "3":
            print("Using Ollama gemma4:12b...")
            return ChatOllama(model="gemma4:12b")
        elif choice == "4":
            print("Using Ollama phi4...")
            return ChatOllama(model="phi4")
        else:
            print("Invalid choice. Please enter 1-4.")

stdio_server_params = StdioServerParameters(
    command="python3",
    args=["./servers/math_server.py"],
)

async def main():
    # Select model before starting
    llm = choose_model()
    
    async with stdio_client(stdio_server_params) as (read,write):    
        async with ClientSession(read_stream=read, write_stream=write) as session:
            await session.initialize()
            print("\nMCP session initialized")
            tools = await load_mcp_tools(session)

            agent = create_agent(llm, tools)

            result = await agent.ainvoke({"messages": [HumanMessage(content="What is 54 + 2 * 3?")]})
            print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())

