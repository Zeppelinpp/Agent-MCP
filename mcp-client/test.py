import json
from agents import Agent, OpenAIChatCompletionsModel, AsyncOpenAI, ItemHelpers, Runner, Tool, ToolCallItem, ToolCallOutputItem, function_tool, MessageOutputItem, set_tracing_disabled
from agents import Agent, AgentHooks, RunContextWrapper, Tool
from typing import Any
from serpapi import GoogleSearch
from agents import function_tool
import requests
from selectolax.parser import HTMLParser

set_tracing_disabled(disabled=True)

class CustomAgentHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name

    async def on_agent_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} started"
        )

    async def on_agent_end(
        self, context: RunContextWrapper, agent: Agent, output: Any
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended with output {output}"
        )

    async def on_handoff(
        self, context: RunContextWrapper, agent: Agent, source: Agent
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {source.name} handed off to {agent.name}"
        )

    async def on_tool_start(
        self, context: RunContextWrapper, agent: Agent, tool: Tool
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} started tool {tool.name}"
        )

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str
    ) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended tool {tool.name} with result {result}"
        )

model = OpenAIChatCompletionsModel(
    model="qwen2.5-72b:q4_k_m",
    openai_client=AsyncOpenAI(
        base_url="http://192.168.88.54:11434/v1",
        api_key="ollama"
    )
)



SERPAPI_KEY = "92df349c4f382ed7d4a1394bf45f9433b04629702ac6267758d727954607ef07"


@function_tool
def web_search(query: str, safe_mode: str, search_type: str):
    """
    Perform a web search using the provided query.

    Args:
        query: The search query string
        safe_mode: Safety level for search results, must be either "on" or "off"
        search_type: The type of search to perform, must be one of "light", "images", "videos"
    """
    params = {
        "engine": f"google_{search_type}",
        "q": query,
        "google_domain": "google.com",
        "hl": "en",
        "safe": safe_mode,
        "num": 5,
        "api_key": SERPAPI_KEY,
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    # print(f"Web search results:\n{results}\n\n")
    return results


@function_tool
def web_reader(url: str):
    """
    Read the content of a web page.

    Args:
        url: The URL of the web page to read
    """
    try:
        # Send a GET request to the URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        # Parse the HTML content
        html = response.text
        parser = HTMLParser(html)

        # Remove unwanted elements
        for tag in parser.css(
            "script, style, noscript, iframe, nav, footer, header, aside, [class*='ad'], [class*='banner'], [class*='menu'], [class*='sidebar'], [class*='nav'], [id*='nav'], [id*='menu'], [id*='sidebar'], [id*='footer'], [id*='header']"
        ):
            tag.decompose()

        # Extract text from the main content
        main_content = ""

        # Try to find the main content element
        main_elements = parser.css("main, article, #content, .content, [role='main']")

        if main_elements:
            # If found specific content containers, use them
            for element in main_elements:
                text = element.text(strip=True)
                if text:
                    main_content += text + "\n\n"
        else:
            # Otherwise get text from the body, filtering out small text blocks
            for tag in parser.css("p, h1, h2, h3, h4, h5, h6, li"):
                text = tag.text(strip=True)
                if (
                    text and len(text) > 20
                ):  # Filter out very short pieces that are likely navigation
                    main_content += text + "\n\n"

        # Clean up the text
        main_content = main_content.strip()

        # Handle empty content
        if not main_content:
            for tag in parser.css("body"):
                main_content = tag.text(strip=True)

        print(f"Web content retrieved:\n{main_content[:1000]}\n\n")
        return main_content

    except Exception as e:
        return f"Error reading web page: {e}"
        
agent = Agent(
    name="Orchestration Agent",
    instructions="""
    You are an specialist in break down a task into subtasks and planning the order of execution
    The output should be a list of subtasks in certain order. Just output the json object, nothing else.
    
    Output in JSON format:
    {
        "subtasks": [
            {
                "name": "subtask1",
                "description": "subtask1 description"
            },
            ...
        ]
    }
    """,
    model=model,
)

arranger = Agent(
    name="Arranger Agent",
    instructions="""
    You will be given a list of subtasks containing the name and description of the subtask. Remember you should finish the tasks in the order of the list and you should not skip any tasks.
    You have several tools to help you accomplish a certain task. After you use a tool, you should always review whether the tool result is enough to finish the subtask. If not, you should consider using other tools or use different parameters for the same tool.
    
    You MUST NOT skip any subtask and you MUST finish all the subtasks. 
    """,
    model=model,
    tools=[web_search, web_reader]
)


async def main():
    result = await Runner.run(
        starting_agent=agent,
        input="""I need the current focus of Stock market and give a advice what stocks should I buy in and why.""",
        hooks=CustomAgentHooks(display_name="Orchestration Agent"),
        max_turns=3,
    )
    try:
        json_result = json.loads(result.final_output.replace("```json", "").replace("```", ""))
    except:
        json_result = result.final_output

    # finish subtasks
    r = await Runner.run(
        starting_agent=arranger,
        input=json.dumps(json_result) if isinstance(json_result, dict) else json_result,
        max_turns=20,
    )
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
    print(f"Final answer: {r.final_output}")
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



