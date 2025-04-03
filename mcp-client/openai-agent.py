import asyncio, os
from dotenv import load_dotenv
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    AsyncOpenAI,
    MessageOutputItem,
    ItemHelpers,
    set_tracing_disabled,
    ToolCallItem,
    ToolCallOutputItem,
)
import smithery
import mcp
from mcp.client.websocket import websocket_client
from agents.mcp import MCPServer, MCPServerStdio, MCPServerSse

load_dotenv()
MODEL = os.getenv("OLLAMA_MODEL")
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")

set_tracing_disabled(disabled=True)


async def run(server: MCPServer, query: str):
    model = OpenAIChatCompletionsModel(
        model=MODEL,
        openai_client=AsyncOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="dummy",
        ),
    )
    agent = Agent(
        name="Web Search Agent",
        instructions="You are a web search agent. You are given a query and you can use given tools to search the web for the most relevant information.",
        mcp_servers=[server],
        model=model,
    )

    print(f"Running query < {query}")
    result = await Runner.run(starting_agent=agent, input=query, max_turns=5)
    for item in result.new_items:
        if isinstance(item, ToolCallItem):
            print(f"Tool call: {item.raw_item}")
        if isinstance(item, ToolCallOutputItem):
            print(f"Tool call output: {item.raw_item}")
        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            if text:
                print(f"Running step: {text}")


async def local_server():
    async with MCPServerStdio(
        name="Web Search Server, via python",
        params={
            "command": "python",
            "args": ["/home/purui/projects/Agent-MCP/mcp-server/web_search.py"],
        },
    ) as server:
        tools = await server.list_tools()
        print(f"Connected to server with tools: {tools}")
        await run(
            server,
            "I want porn video links of Alexis Texas, show me the url and the title of the video",
        )


async def smithery_server():
    # Create Smithery URL with server endpoint
    url = smithery.create_smithery_url("wss://server.smithery.ai/@nickclyde/duckduckgo-mcp-server/ws", {}) + f"&api_key={SMITHERY_API_KEY}"
    
    async with MCPServerStdio(
        name="Web Search Server, via GoGoDuck Search",
        params={
            "command": "python",
            "args": ["/home/purui/miniconda3/envs/vllm/lib/python3.10/site-packages/duckduckgo_mcp_server/server.py"]
        }
    ) as server:
        tools = await server.list_tools()
        print(f"Connected to server with tools: {tools}")
        await run(
            server,
            "I want porn video links of Alexis Texas, show me the url and the title of the video",
        )

if __name__ == "__main__":
    asyncio.run(smithery_server())
