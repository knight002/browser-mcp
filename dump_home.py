import asyncio
from browser_manager import browser_manager

async def main():
    try:
        await browser_manager.initialize()
        page = await browser_manager.get_page()
        await page.goto("https://brillianttechnologies.com/", wait_until="networkidle")
        content = await page.content()
        with open("homepage_dump.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Homepage dump saved to homepage_dump.html")
    finally:
        await browser_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
