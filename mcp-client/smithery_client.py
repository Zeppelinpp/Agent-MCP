import smithery, os, asyncio, json
import mcp
from mcp.client.websocket import websocket_client

# Create smithery url endpoint
url = smithery.create_smithery_url("wss://server.smithery.ai/@chuanmingliu/mcp-webresearch/ws", {})

async def connect_to_smithery(url):
    async with websocket_client(url) as streams:
        return mcp.ClientSession(*streams)

async def main():
    session = await connect_to_smithery(url)
    await session.list_tools()

if __name__ == "__main__":
    asyncio.run(main())