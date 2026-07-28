import os
import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page
from playwright_stealth import Stealth

class BrowserManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    async def initialize(self, endpoint="http://172.24.0.1:9223"):
        if self.initialized:
            return

        self.playwright = await async_playwright().start()

        # Connect to an existing browser instance via CDP
        browser = await self.playwright.chromium.connect_over_cdp(endpoint)
        self.context: BrowserContext = browser.contexts[0]

        # Create a default page or use the first existing one
        pages = self.context.pages
        if pages:
            self.active_page: Page = pages[0]
        else:
            self.active_page: Page = await self.context.new_page()
        
        # Apply stealth using the Stealth class
        stealth = Stealth()
        await stealth.apply_stealth_async(self.active_page)

        # Handle new tabs (redirections to external sites)
        self.context.on("page", self._handle_new_page)

        self.initialized = True
        print(f"Browser connected via CDP at: {endpoint}")

    async def _handle_new_page(self, page: Page):
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        self.active_page = page
        print(f"Switched to new tab: {page.url}")

    async def get_page(self) -> Page:
        if not self.initialized:
            raise RuntimeError("BrowserManager not initialized. Call initialize() first.")
        if self.active_page.is_closed():
            pages = self.context.pages
            if pages:
                self.active_page = pages[0]
            else:
                self.active_page = await self.context.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(self.active_page)
        return self.active_page

    async def cleanup(self):
        if self.initialized:
            await self.context.close()
            await self.playwright.stop()
            self.initialized = False

# Singleton instance
browser_manager = BrowserManager()
