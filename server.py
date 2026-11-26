import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime
from functools import wraps
from mcp.server.fastmcp import FastMCP
from browser_manager import browser_manager
import tools

LOG_FILE = "/tmp/browser_mcp.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("browser-mcp")


def log_tool_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        call_id = f"{func.__name__}_{int(time.time() * 1000)}"
        params = {k: v for k, v in kwargs.items() if k != "self"}
        logger.info(f"TOOL_CALL | {call_id} | {func.__name__} | params={json.dumps(params)}")
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = round((time.time() - start) * 1000)
            result_preview = result[:200] if isinstance(result, str) else str(result)[:200]
            logger.info(f"TOOL_OK   | {call_id} | {func.__name__} | {elapsed}ms | result={result_preview}")
            return result
        except Exception as e:
            elapsed = round((time.time() - start) * 1000)
            logger.error(f"TOOL_ERR  | {call_id} | {func.__name__} | {elapsed}ms | error={e}")
            raise
    return wrapper


# Initialize FastMCP server with network settings for remote access
mcp = FastMCP(
    "Browser-Automation",
    host="0.0.0.0",
    port=8000
)

@mcp.tool()
@log_tool_call
async def setup_session(profile_name: str = "default", headless: bool = True) -> str:
    """Initializes the browser session with a specific profile. Idempotent: safe to call repeatedly."""
    if browser_manager.initialized:
        return f"Session already active, continuing with existing session."
    await browser_manager.initialize()
    return f"Browser initialized with profile {profile_name} (headless={headless})."

@mcp.tool()
@log_tool_call
async def navigate(url: str) -> str:
    """Navigate to a specific URL."""
    result = await tools.navigate(url)
    return result["content"][0]["text"]

@mcp.tool()
@log_tool_call
async def click(selector: str) -> str:
    """Click an element using CSS selector or text."""
    result = await tools.click(selector)
    return result["content"][0]["text"]

@mcp.tool()
@log_tool_call
async def type_text(selector: str, text: str) -> str:
    """Type text into a field."""
    result = await tools.type_text(selector, text)
    return result["content"][0]["text"]

@mcp.tool()
@log_tool_call
async def read_page() -> str:
    """Read the current page content (minified HTML)."""
    result = await tools.read_page()
    return result["content"][0]["text"]

@mcp.tool()
@log_tool_call
async def get_url() -> str:
    """Get the current URL of the active page."""
    result = await tools.get_url()
    return result["content"][0]["text"]

@mcp.tool()
@log_tool_call
async def screenshot() -> str:
    """Capture a screenshot and return the path to it."""
    page = await browser_manager.get_page()
    path = await tools.take_screenshot(page, f"manual_{int(time.time())}")
    return f"Screenshot saved to {path}"

@mcp.tool()
@log_tool_call
async def extract_jobs(site: str = "generic") -> str:
    """Extract job listings from the current page as structured JSON. Supported sites: linkedin, totaljobs, generic."""
    result = await tools.extract_jobs(site)
    return result["content"][0]["text"]

@mcp.tool()
@log_tool_call
async def scroll(direction: str = "down", amount: int = 500) -> str:
    """Scroll the page up or down by a given amount in pixels."""
    result = await tools.scroll(direction, amount)
    return result["content"][0]["text"]

@mcp.tool()
@log_tool_call
async def wait_for_element(selector: str, timeout: int = 5000) -> str:
    """Wait for a CSS selector to appear on the page."""
    result = await tools.wait_for_element(selector, timeout)
    return result["content"][0]["text"]

@mcp.tool()
@log_tool_call
async def fill_application(fields: str) -> str:
    """Fill multiple form fields at once. Pass a JSON dict of {selector_or_label: value} pairs. Handles text inputs, dropdowns, and file uploads (for resume)."""
    import json as _json
    parsed = _json.loads(fields) if isinstance(fields, str) else fields
    result = await tools.fill_application(parsed)
    return result["content"][0]["text"]

if __name__ == "__main__":
    logger.info("Browser MCP Server starting on port 8000")
    mcp.run(transport="streamable-http")

