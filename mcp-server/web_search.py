import json
import requests, asyncio
import re
from selectolax.parser import HTMLParser
from dotenv import load_dotenv
from serpapi import GoogleSearch
import os
from mcp.server.fastmcp import FastMCP
from markdownify import markdownify as md


load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("websearch")

# SEARCH_API_KEY
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")


@mcp.tool()
def get_general_search(query: str):
    """Search information on Google, search mode is safe or off"""
    print(f"Running General Search for {query}")
    params = {
        "engine": "google_light",
        "q": query,
        "google_domain": "google.com",
        "hl": "en",
        "safe": "off",
        "num": 10,
        "api_key": SEARCH_API_KEY,
    }

    result = GoogleSearch(params).get_dict()
    try:
        if result["organic_results"]:
            general_result = result["organic_results"]
            records = []
            for item in general_result:
                try:
                    record = f"[{item['title']}]({item['link']}) - {item['snippet']}"
                    records.append(record)
                except:
                    continue
            return "\n".join(records)
    except:
        return False


@mcp.tool()
def get_image_search(query: str):
    """Search images on Google, search mode is safe or off"""
    print(f"Running Image Search for {query}")
    params = {
        "engine": "google_images",
        "q": query,
        "google_domain": "google.com",
        "hl": "en",
        "safe": "off",
        "filter": 0,
        "num": 20,
        "api_key": SEARCH_API_KEY,
    }

    result = GoogleSearch(params).get_dict()
    try:
        if result["images_results"]:
            image_result = result["images_results"][:20]
            return json.dumps(image_result)
    except:
        return False


@mcp.tool()
def get_video_search(query: str):
    """Search videos on Google, search mode is safe or off"""
    print(f"Running Video Search for {query}")
    params = {
        "api_key": SEARCH_API_KEY,
        "engine": "google_videos",
        "google_domain": "google.com",
        "q": query,
        "gl": "us",
        "hl": "en",
        "safe": "off",
        "num": "20",
        "location": "United States",
        "filter": "0",
    }

    result = GoogleSearch(params).get_dict()
    try:
        if result["video_results"]:
            video_result = result["video_results"][:20]
            return json.dumps(video_result)
    except:
        return False


@mcp.tool()
async def web_reader(urls: list[str]):
    task = [asyncio.create_task(web_reader_task(url)) for url in urls]
    try:
        completed_tasks, _ = await asyncio.wait(
            task, timeout=4.0, return_when=asyncio.ALL_COMPLETED
        )
        result = [t.result() for t in completed_tasks]
        return "\n\n".join(result)
    except asyncio.TimeoutError:
        return "Timeout error, please try again."
    except Exception as e:
        return f"An error occurred: {e}"


async def web_reader_task(url: str):
    try:
        print(f"parsing {url}...")
        headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url=url, headers=headers, timeout=5.0)
        response.raise_for_status()
        html_content = response.text

        tree = HTMLParser(html_content)

        main_content_node = tree.css_first('article, main, [role="main"]')

        if main_content_node:
            html_to_convert = main_content_node.html
        else:
            body_node = tree.body
            if body_node:
                for node in body_node.css(
                    "script, style, nav, footer, header, aside, form, button, input, select, textarea, label, .sidebar, #sidebar, .menu, #menu, .ad, #ad, .advertisement, #advertisement"
                ):
                    node.decompose()
                html_to_convert = body_node.html
            else:
                html_to_convert = html_content

        markdown_text = md(html_to_convert, heading_style="ATX")

        lines = [line.strip() for line in markdown_text.split("\n")]
        cleaned_markdown = "\n".join(line for line in lines if line)

        return cleaned_markdown if cleaned_markdown else " "
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return False


if __name__ == "__main__":
    # test = asyncio.run(web_reader(["https://www.cnn.com/", "https://www.foxnews.com/"]))
    # print(test)
    mcp.run(transport="stdio")
