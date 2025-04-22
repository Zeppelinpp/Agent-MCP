import os, json, asyncio
from dotenv import load_dotenv
from planning import PlanningAgent
from researcher import ResearchAgent
from agents import (
    Runner,
    ToolCallItem,
    ToolCallOutputItem,
    MessageOutputItem,
    ItemHelpers,
    set_default_openai_client,
    set_tracing_disabled,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
)
from agents.mcp import MCPServer, MCPServerStdio

load_dotenv()

LOCAL_SERVER_PATH = os.getenv("LOCAL_SERVER_PATH")
DS_KEY = os.getenv("DS_KEY")
SERVER_IP = os.getenv("SERVER_IP")

async def main():
    # openai client
    openai_client = AsyncOpenAI(
        base_url="https://api.deepseek.com",
        api_key=DS_KEY,
    )
    # ollama client
    ollama_client = AsyncOpenAI(
        base_url="http://{SERVER_IP}:11434/v1",
        api_key="ollama",
    )
    # lm studio mlx client
    lm_studio_client = AsyncOpenAI(
        base_url="http://{SERVER_IP}:1234/v1",
        api_key="lm_studio",
    )
    model = OpenAIChatCompletionsModel(
        model="mlx-community/qwq-32b",
        openai_client=lm_studio_client,
    )
    # disabled tracing
    set_default_openai_client(lm_studio_client, use_for_tracing=False)
    set_tracing_disabled(disabled=True)
    # mcp server
    async with MCPServerStdio(
        params={"command": "python", "args": [LOCAL_SERVER_PATH]}
    ) as server:
        # list tools
        tools = await server.list_tools()
        print(f"Connected to server with tools: {tools}")
        # planning agent
        planning_agent = PlanningAgent(
            name="Planning Agent",
            model=model,
            handoffs=[
                ResearchAgent(
                    name="Research Agent",
                    model=model,
                    mcp_servers=[server],
                )
            ],
        )
        # run
        result_stream = Runner.run_streamed(
            starting_agent=planning_agent,
            input="What's the main focus on the topic of AI in 2025? Give me some trending acedemic papers key points and new technologies overview in 2025",
            max_turns=15,
        )
        async for event in result_stream.stream_events():
            if event.type == "agent_updated_stream_event":
                print(f"Agent updated: {event.new_agent.name}")
            elif event.type == "run_item_stream_event":
                if isinstance(event.item, ToolCallItem):
                    print(f"Call Tool: {event.item.raw_item.name} with args: {event.item.raw_item.arguments}")
                    await asyncio.sleep(0.05)
                elif isinstance(event.item, ToolCallOutputItem):
                    text = json.loads(event.item.output)["text"]
                    print(f"Tool call output: {text[:100]} ...")
                    await asyncio.sleep(0.05)
                elif isinstance(event.item, MessageOutputItem):
                    text = ItemHelpers.text_message_output(event.item)
                    if text:
                        print(f"Running step: {text}")
                        await asyncio.sleep(0.05)
            elif event.type == "raw_response_event":
                try:
                    if event.data.delta:
                        continue
                except Exception as e:
                    print(f"Event: {event.data}")


if __name__ == "__main__":
    asyncio.run(main())
