import asyncio
import os
from browser_manager import browser_manager
from tools import take_screenshot

async def main():
    try:
        await browser_manager.initialize()
        print("Browser initialized.")
        
        # Ensure the directory exists
        os.makedirs("screenshots", exist_ok=True)
        
        base_url = "https://brillianttechnologies.com/"
        page = await browser_manager.get_page()
        
        # Define pages to visit from the menu (identified from HTML dump)
        pages_to_visit = [
            ("Home", base_url),
            ("About", f"{base_url}about.html"),
            ("AI Solutions", f"{base_url}services.html"),
            ("Contact", f"{base_url}contact.html"),
        ]
        
        for text, url in pages_to_visit:
            print(f"Navigating to {text}: {url}...")
            try:
                await page.goto(url, wait_until="networkidle")
                safe_text = "".join([c if c.isalnum() else "_" for c in text])
                await take_screenshot(page, f"menu_{safe_text}")
                print(f"Screenshot saved for {text}.")
            except Exception as e:
                print(f"Failed to visit {text}: {e}")

    except Exception as e:
        print(f"Error during crawling: {e}")
    finally:
        await browser_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
