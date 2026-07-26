import asyncio
from browser_manager import browser_manager
from tools import navigate

async def main():
    try:
        await browser_manager.initialize()
        print("Browser initialized.")
        result = await navigate("https://brillianttechnologies.com/")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
