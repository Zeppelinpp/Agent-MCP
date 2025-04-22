import asyncio, json, os
from dotenv import load_dotenv
from agents import (
    Agent,
    Runner,
    OpenAIChatCompletionsModel,
    AsyncOpenAI,
    ToolCallItem,
    ToolCallOutputItem,
    MessageOutputItem,
    ItemHelpers,
    set_tracing_disabled,
    set_default_openai_client,
)
from agents.mcp import MCPServer, MCPServerStdio

load_dotenv()

set_tracing_disabled(disabled=True)

LOCAL_SERVER_PATH = os.getenv("LOCAL_SERVER_PATH")
DS_KEY = os.getenv("DS_KEY")

class PlanningAgent(Agent):
    def __init__(
        self,
        name: str,
        model: str | OpenAIChatCompletionsModel | None = None,
        instructions: str | None = None,
        **kwargs,
    ):
        instructions = (
        """
        You are a planning agent. You are given a task and you need to plan the steps to complete the task. 
        Once you have planned the steps, output the steps in list first then you need to handoff the steps as tasks to appropriate agents.
        """
            if instructions is None
            else instructions
        )
        super().__init__(name=name, model=model, instructions=instructions, **kwargs)


if __name__ == "__main__":
    openai_client = AsyncOpenAI(
        base_url="https://api.deepseek.com",
        api_key=DS_KEY,
    )
    set_default_openai_client(openai_client, use_for_tracing=False)
    async def main():
        async with MCPServerStdio(
            params={"command": "python", "args": [LOCAL_SERVER_PATH]}
        ) as server:
            tools = await server.list_tools()
            print(f"Connected to server with tools: {tools}")
            planning_agent = PlanningAgent(
                name="Planning Agent",
                model=OpenAIChatCompletionsModel(
                    model="deepseek-chat",
                    openai_client=openai_client,
                ),
                mcp_servers=[server],
            )

            result_stream = Runner.run_streamed(
                starting_agent=planning_agent,
                input="I want to know main focus on stock market nowadays and tell me the top 3 stocks to invest in",
                max_turns=10,
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
                    print(f"Raw response: {event.data}")
                

    asyncio.run(main())
