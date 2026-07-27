import os
import asyncio
import base64
from datetime import datetime
from playwright.async_api import Page
from browser_manager import browser_manager

async def navigate(url: str, wait_until: str = "domcontentloaded") -> dict:
    page = await browser_manager.get_page()
    try:
        await page.goto(url, wait_until=wait_until)
        title = await page.title()
        screenshot_path = await take_screenshot(page, f"nav_{int(datetime.now().timestamp())}")
        return {
            "content": [
                {"type": "text", "text": f"Navigated to {url}. Page Title: {title}"},
                {"type": "image", "data": await get_image_base64(screenshot_path), "mimeType": "image/png"}
            ]
        }
    except Exception as e:
        await save_debug_state(page, f"nav_error_{int(datetime.now().timestamp())}")
        return {"content": [{"type": "text", "text": f"Navigation failed: {str(e)}"}]}

async def click(selector: str) -> dict:
    page = await browser_manager.get_page()
    try:
        # Try text-based selector first for AI friendliness
        if not selector.startswith(("#", ".", "[", "div", "span", "a")):
            await page.click(f"text={selector}", timeout=5000)
        else:
            await page.click(selector, timeout=5000)
        
        screenshot_path = await take_screenshot(page, f"click_{int(datetime.now().timestamp())}")
        return {
            "content": [
                {"type": "text", "text": f"Successfully clicked {selector}."},
                {"type": "image", "data": await get_image_base64(screenshot_path), "mimeType": "image/png"}
            ]
        }
    except Exception as e:
        await save_debug_state(page, f"click_error_{int(datetime.now().timestamp())}")
        return {"content": [{"type": "text", "text": f"Click failed for {selector}: {str(e)}"}]}

async def type_text(selector: str, text: str) -> dict:
    page = await browser_manager.get_page()
    try:
        if not selector.startswith(("#", ".", "[", "div", "span", "a")):
            sel = f"text={selector}" # This is tricky for typing, usually need a proper selector
            # Fallback to simplified text search if it's just a label that might be near an input
            await page.fill(selector, text) 
        else:
            await page.fill(selector, text)
        
        return {"content": [{"type": "text", "text": f"Typed '{text}' into {selector}."}]}
    except Exception as e:
        await save_debug_state(page, f"type_error_{int(datetime.now().timestamp())}")
        return {"content": [{"type": "text", "text": f"Typing failed for {selector}: {str(e)}"}]}

async def read_page() -> dict:
    page = await browser_manager.get_page()
    try:
        content = await page.content()
        # Simple minification: remove scripts and styles to save tokens
        import re
        clean_html = re.sub(r'<(script|style).*?>.*?</\1>', '', content, flags=re.DOTALL | re.IGNORECASE)
        return {"content": [{"type": "text", "text": clean_html}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Failed to read page: {str(e)}"}]}

async def get_url() -> dict:
    page = await browser_manager.get_page()
    return {"content": [{"type": "text", "text": await page.url}]}

async def take_screenshot(page: Page, name: str) -> str:
    path = f"screenshots/{name}.png"
    await page.screenshot(path=path)
    return path

async def get_image_base64(path: str) -> str:
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def save_debug_state(page: Page, name: str):
    # Save HTML for deep dive debugging
    html = await page.content()
    with open(f"debug/{name}.html", "w", encoding="utf-8") as f:
        f.write(html)
    # Also take a screenshot of the failure
    await take_screenshot(page, f"fail_{name}")
