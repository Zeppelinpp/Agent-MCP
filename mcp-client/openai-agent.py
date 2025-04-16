import asyncio, os
import smithery, json
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
from mcp.client.websocket import websocket_client
from agents.mcp import MCPServer, MCPServerStdio, MCPServerSse


load_dotenv()
MODEL = os.getenv("OLLAMA_MODEL")
DS_KEY = os.getenv("DS_KEY")
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")
LOCAL_SERVER_PATH = os.getenv("LOCAL_SERVER_PATH")
SMITHERY_SERVER_PATH = os.getenv("SMITHERY_SERVER_PATH")
set_tracing_disabled(disabled=True)


async def run(server: MCPServer, query: str):
    model = OpenAIChatCompletionsModel(
        model="deepseek-chat",
        openai_client=AsyncOpenAI(
            base_url="https://api.deepseek.com/",
            api_key=DS_KEY,
        ),
    )
    agent = Agent(
        name="Web Search Agent",
        instructions="You are a web search agent. You are given a query and you can use given tools to search the web for the most relevant information.",
        mcp_servers=[server],
        model=model,
    )

    print(f"Running query: {query}")
    result = await Runner.run(starting_agent=agent, input=query, max_turns=5)
    for item in result.new_items:
        if isinstance(item, ToolCallItem):
            print(f"Call Tool: {item.raw_item.name} with args: {item.raw_item.arguments}")
            await asyncio.sleep(0.05)
        if isinstance(item, ToolCallOutputItem):
            text = json.loads(item.output)["text"]
            print(f"Tool call output: {text[:100]} ...")
            await asyncio.sleep(0.05)
        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            if text:
                print(f"Running step: {text}")
                await asyncio.sleep(0.05)

async def local_server():
    async with MCPServerStdio(
        name="Web Search Server, via python",
        params={
            "command": "python",
            "args": [LOCAL_SERVER_PATH],
        },
    ) as server:
        tools = await server.list_tools()
        print(f"Connected to server with tools: {tools}")
        await run(
            server,
            "I want detailed information about the latest news of CNN, Fox today.",
        )


async def smithery_server():
    # Create Smithery URL with server endpoint
    url = smithery.create_smithery_url("wss://server.smithery.ai/@nickclyde/duckduckgo-mcp-server/ws", {}) + f"&api_key={SMITHERY_API_KEY}"
    
    async with MCPServerStdio(
        name="Web Search Server, via GoGoDuck Search",
        params={
            "command": "python",
            "args": [SMITHERY_SERVER_PATH]
        }
    ) as server:
        tools = await server.list_tools()
        print(f"Connected to server with tools: {tools}")
        await run(
            server,
            "I want detailed information about the latest news of CNN, Fox today.",
        )

if __name__ == "__main__":
    asyncio.run(local_server())
