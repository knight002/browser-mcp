import os
import asyncio
from mcp.server.fastmcp import FastMCP
from browser_manager import browser_manager
import tools

# Initialize FastMCP server with network settings for remote access
mcp = FastMCP(
    "Browser-Automation", 
    host="0.0.0.0", 
    port=8000
)

@mcp.tool()
async def setup_session(profile_name: str = "default", headless: bool = True) -> str:
    """Initializes the browser session with a specific profile."""
    await browser_manager.initialize()
    return f"Browser initialized with profile {profile_name} (headless={headless})."

@mcp.tool()
async def navigate(url: str) -> str:
    """Navigate to a specific URL."""
    result = await tools.navigate(url)
    return result["content"][0]["text"]

@mcp.tool()
async def click(selector: str) -> str:
    """Click an element using CSS selector or text."""
    result = await tools.click(selector)
    return result["content"][0]["text"]

@mcp.tool()
async def type_text(selector: str, text: str) -> str:
    """Type text into a field."""
    result = await tools.type_text(selector, text)
    return result["content"][0]["text"]

@mcp.tool()
async def read_page() -> str:
    """Read the current page content (minified HTML)."""
    result = await tools.read_page()
    return result["content"][0]["text"]

@mcp.tool()
async def get_url() -> str:
    """Get the current URL of the active page."""
    result = await tools.get_url()
    return result["content"][0]["text"]

@mcp.tool()
async def screenshot() -> str:
    """Capture a screenshot and return the path to it."""
    import time
    page = await browser_manager.get_page()
    path = await tools.take_screenshot(page, f"manual_{int(time.time())}")
    return f"Screenshot saved to {path}"

if __name__ == "__main__":
    # Run as an SSE server on port 8000 for remote access
    mcp.run(transport="sse")

