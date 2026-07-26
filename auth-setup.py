import asyncio
from playwright.async_api import async_playwright
from browser_manager import browser_manager

async def main():
    # For setup, we MUST run in headful mode to let the user log in manually
    print("Starting AUTH-SETUP in HEADFUL mode...")
    print("Please perform your logins now. Once done, close the browser or use Ctrl+C.")
    
    await browser_manager.initialize()
    page = await browser_manager.get_page()
    
    # Keep it open for the user to interact with
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await browser_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
