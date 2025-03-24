import smithery, os
import mcp
from mcp.client.websocket import websocket_client
import json, time

# Create smithery url endpoint
url = smithery.create_smithery_url("wss://server.smithery.ai/@chuanmingliu/mcp-webresearch/ws", {})
