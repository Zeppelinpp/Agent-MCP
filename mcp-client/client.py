import asyncio
from typing import Optional, List
from contextlib import AsyncExitStack
import json, os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI(
            api_key="dummy",
            base_url="http://localhost:11434/v1",
        )
    # methods will go here
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]

        # Initial LLM API call
        response = self.openai.chat.completions.create(
            model="huihui_ai/qwen2.5-1m-abliterated:14b-instruct-q8_0",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        final_text = []

        # Check if we have tool calls in the response
        tool_calls = response.choices[0].message.tool_calls
        print(f"tool_calls: {tool_calls}")
        if tool_calls:
            # Handle tool calls
            assistant_message = {"role": "assistant", "content": response.choices[0].message.content}
            if response.choices[0].message.content:
                final_text.append(response.choices[0].message.content)
            
            # Add tool calls to assistant message
            assistant_message["tool_calls"] = []
            
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                tool_id = tool_call.id

                # Parse the arguments if they're a string
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        print(f"Warning: Couldn't parse tool arguments: {tool_args}")
                        tool_args = {}

                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                
                # For the message history, convert tool_args back to string if it's a dict
                tool_args_str = json.dumps(tool_args) if isinstance(tool_args, dict) else tool_args
                
                # Add the result to messages in a simpler format
                # First add the assistant's message that called the tool
                messages.append({
                    "role": "assistant",
                    "content": f"I'll help you with that by using the {tool_name} tool."
                })
                
                # Then add the tool result as user message
                messages.append({
                    "role": "user",
                    "content": f"Result from {tool_name}: {result.content}"
                })
                
                # Get next response from LLM
                print(f"Sending messages: {json.dumps(messages, indent=2)}")  # Debug the messages
                response = self.openai.chat.completions.create(
                    model="huihui_ai/qwen2.5-1m-abliterated:14b-instruct-q8_0",
                    max_tokens=1000,
                    messages=messages,
                    tools=available_tools
                )
                
                print(f"Response received: {response}")  # Debug the response
                
                # Make sure we capture the model's final answer
                if hasattr(response.choices[0].message, 'content') and response.choices[0].message.content:
                    final_answer = response.choices[0].message.content
                    final_text.append(final_answer)
                    print(f"Added to final_text: {final_answer}")  # Debug what's being added
        else:
            # Simple text response with no tool calls
            if response.choices[0].message.content:
                final_text.append(response.choices[0].message.content)
        
        # Make sure we have something to return, even if final_text is empty
        if not final_text:
            return "No response generated. There might be an issue with the model's response."
        
        result = "\n".join(final_text)
        print(f"Final result: {result}")  # Debug the final result
        return result
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break
                
                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
        
        
async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())