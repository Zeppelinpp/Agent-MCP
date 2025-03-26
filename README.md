# Agent-MCP
local mcp server-client agent

## MCP Server
参考Antropic的 [Model Context Protocol文档](https://docs.anthropic.com/en/docs/agents-and-tools/mcp) 编写本地Web Search MCP Server, 使用Google SerpAPI作为Search API

## MCP Client
本地MCP Client, 实现调用本地部署的MCP Server和调用外部平台Simthery提供的公开MCP Server服务, [Simthery平台](https://smithery.ai/)
参考[Antropic MCP Client Quick Start](https://modelcontextprotocol.io/quickstart/client) 修改调用接口（原文使用Anthropic API）为OpenAI的接口并调整后处理流程，增加一些Json validation
测试使用Qwen2.5系列模型和DeepSeek-V3效果都比较稳定
