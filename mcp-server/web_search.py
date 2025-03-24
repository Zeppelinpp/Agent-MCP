from typing import Any
from dotenv import load_dotenv
import serpapi
import httpx, os
from mcp.server.fastmcp import FastMCP

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("websearch")

# SEARCH_API_KEY
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")

@mcp.tool()
def get_general_search(query: str, mode: str = "safe"):
    """Search information on Google, search mode is safe or off"""
    params = {
        "engine": "google_light",
        "q": query,
        "google_domain": "google.com",
        "hl": "en",
        "safe": mode,
        "num": 5,
        "api_key": "92df349c4f382ed7d4a1394bf45f9433b04629702ac6267758d727954607ef07",
    }

    result = serpapi.search(params).get_dict()
    try:
        if result["organic_results"]:
            general_result = result["organic_results"]
            return general_result
    except:
        return False
    
@mcp.tool()
def get_image_search(query: str, mode: str = "safe"):
    """Search images on Google, search mode is safe or off"""
    
    params = {
        "engine": "google_images",
        "q": query,
        "google_domain": "google.com",
        "hl": "en",
        "safe": mode,
        "num": 20,
        "api_key": SEARCH_API_KEY,
    }

    result = serpapi.search(params).get_dict()
    try:
        if result["images_results"]:
            image_result = result["images_results"][:20]
            return image_result
    except:
        return False

@mcp.tool()
def get_video_search(query: str, mode: str = "safe"):
    """Search videos on Google, search mode is safe or off"""
    params = {
        "engine": "google_videos",
        "q": query,
        "google_domain": "google.com",
        "hl": "en",
        "safe": mode,
        "num": 20,
        "api_key": SEARCH_API_KEY,
    }

    result = serpapi.search(params).get_dict()
    try:
        if result["videos_results"]:
            video_result = result["videos_results"][:20]
            return video_result
    except:
        return False
    
if __name__ == "__main__":
    mcp.run(transport="stdio")