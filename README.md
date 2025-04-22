# Agent-MCP
local mcp server-client agent

## MCP Server
参考Antropic的 [Model Context Protocol文档](https://docs.anthropic.com/en/docs/agents-and-tools/mcp) 编写本地Web Search MCP Server, 使用Google SerpAPI作为Search API

## MCP Client
本地MCP Client, 实现调用本地部署的MCP Server和调用外部平台Simthery提供的公开MCP Server服务, [Simthery平台](https://smithery.ai/)
参考[Antropic MCP Client Quick Start](https://modelcontextprotocol.io/quickstart/client) 修改调用接口（原文使用Anthropic API）为OpenAI的接口并调整后处理流程，增加一些Json validation
测试使用Qwen2.5系列模型和DeepSeek-V3效果都比较稳定

## 更新
*2025.4.22*
- custom_agents folder planning + researcher agent模仿deep research功能，使用MCP Server
```python
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
```
