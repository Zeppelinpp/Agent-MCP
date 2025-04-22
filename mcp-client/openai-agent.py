import asyncio, os
import smithery, json
from typing import List
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

async def run_with_multiple_servers(servers: List[MCPServer], query: str):
    model = OpenAIChatCompletionsModel(
        model="deepseek-chat",
        openai_client=AsyncOpenAI(
            base_url="https://api.deepseek.com/",
            api_key=DS_KEY,
        ),
    )
    # model = OpenAIChatCompletionsModel(
    #     model="Qwen2.5-14B",
    #     openai_client=AsyncOpenAI(
    #         base_url="http://192.168.88.68:8002/v1",
    #         api_key=DS_KEY,
    #     ),
    # )
    agent = Agent(
        name="Web Search Agent",
        instructions="You are a web search agent. You are given a query and you can use given tools to search the web for the most relevant information.",
        mcp_servers=servers,
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
    url = "https://rag-web-browser.apify.actor/sse"
    
    async with MCPServerSse(
        name="Web Search Server",
        params={
            "url": url,
        }
    ) as server:
        tools = await server.list_tools()
        print(f"Connected to server with tools: {tools}")
        await run(
            server,
            "I want detailed information about the latest news of CNN, Fox today.",
        )
    
async def multiple_servers_run():
    # third party server
    web_fetch_server = MCPServerStdio(
        name="Server to fetch web content by urls",
        params={
            "command": "uvx",
            "args":["mcp-server-fetch"]
        }
    )
    # local server
    web_search_server = MCPServerStdio(
        name="Server to get web urls",
        params={
            "command": "python",
            "args": [LOCAL_SERVER_PATH],
        },
    )
    mcp_servers = [web_fetch_server, web_search_server]
    async with web_fetch_server as fs, web_search_server as ss:
        for server in mcp_servers:
            tools = await server.list_tools()
            print(f"Connected to server with tools: {tools}\n\n")
        await run_with_multiple_servers(
            servers=[fs, ss],
            query="Write me a report about the latest focus of the US stock market. I need it be comprehensive. Review the content and use tool to get best result.",
        )
    print("Done")

if __name__ == "__main__":
    asyncio.run(multiple_servers_run())
