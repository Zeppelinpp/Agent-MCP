# Agent-MCP
local mcp server-client agent

## MCP Server
参考Antropic的 [Model Context Protocol文档](https://docs.anthropic.com/en/docs/agents-and-tools/mcp) 编写本地Web Search MCP Server, 使用Google SerpAPI作为Search API

## MCP Client
本地MCP Client, 实现调用本地部署的MCP Server和调用外部平台Simthery提供的公开MCP Server服务, [Simthery平台](https://smithery.ai/)
参考[Antropic MCP Client Quick Start](https://modelcontextprotocol.io/quickstart/client) 修改调用接口（原文使用Anthropic API）为OpenAI的接口并调整后处理流程，增加一些Json validation
测试使用Qwen2.5系列模型和DeepSeek-V3效果都比较稳定

## 测试结果
```
python ./mcp-client/openai-agent.py
```
Terminal output:
```
Connected to server with tools: [Tool(name='get_general_search', description='Search information on Google, search mode is safe or off', inputSchema={'properties': {'query': {'title': 'Query', 'type': 'string'}}, 'required': ['query'], 'title': 'get_general_searchArguments', 'type': 'object'}), Tool(name='get_image_search', description='Search images on Google, search mode is safe or off', inputSchema={'properties': {'query': {'title': 'Query', 'type': 'string'}}, 'required': ['query'], 'title': 'get_image_searchArguments', 'type': 'object'}), Tool(name='get_video_search', description='Search videos on Google, search mode is safe or off', inputSchema={'properties': {'query': {'title': 'Query', 'type': 'string'}}, 'required': ['query'], 'title': 'get_video_searchArguments', 'type': 'object'}), Tool(name='web_reader', description='', inputSchema={'properties': {'urls': {'items': {'type': 'string'}, 'title': 'Urls', 'type': 'array'}}, 'required': ['urls'], 'title': 'web_readerArguments', 'type': 'object'})]
Running query: I want detailed information about the latest news of CNN, Fox today.
Call Tool: get_general_search with args: {"query": "latest news CNN today"}
Call Tool: get_general_search with args: {"query": "latest news Fox today"}
Tool call output: [CNN: Breaking News, Latest News and Videos](https://www.cnn.com/) - View the latest news and breaki ...
Tool call output: [Fox News - Breaking News Updates | Latest News Headlines ...](https://www.foxnews.com/) - Latest Br ...
Call Tool: web_reader with args: {"urls": ["https://www.cnn.com/", "https://www.foxnews.com/"]}
Tool call output: [Trump’s tariffs](/politics/live-news/trump-news-tariffs-immigration-04-15-25/index.html)
[Ousted Ru ...
Running step: Here are the latest updates from CNN and Fox News today:

### CNN Latest News:
1. **Trump’s Tariffs**: China’s export restrictions on rare earth minerals are impacting America’s industries, with little room for retaliation.
2. **Global Health**: A "historic" WHO agreement on pandemics has been reached.
3. **Climate Crisis**: Pakistan and India are experiencing severe heatwaves.
4. **Technology**: Nvidia faces a $5.5 billion hit due to US restrictions on chip exports to China.
5. **Politics**: Trump is considering drastic cuts to the State Department and funding for international organizations.
6. **Exclusive**: Ecuador’s president expressed openness to US forces assisting in a crackdown on gangs.
7. **Science**: A breakthrough in 3D brain mapping has been achieved.
8. **Entertainment**: Coachella 2025 showcased standout celebrity looks.

For more details, visit [CNN](https://www.cnn.com/).

### Fox News Latest News:
1. **Politics**: The Trump administration has referred NY AG Letitia James for possible prosecution over alleged mortgage fraud.     
2. **Breaking News**: An American pastor kidnapped at gunpoint was rescued after a shootout.
3. **International**: U.S.-Iran talks are set to continue in Rome.
4. **Technology**: Smartphones and computers are exempt from Trump’s latest tariffs.
5. **Health**: CDC reports show varying treatment rates for depression in the US.

For more details, visit [Fox News](https://www.foxnews.com/).

Let me know if you'd like more information on any specific topic!
```
