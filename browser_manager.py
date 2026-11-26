import os
import asyncio
import subprocess
import urllib.request
from playwright.async_api import async_playwright, BrowserContext, Page
from playwright_stealth import Stealth

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BROWSER_PID_FILE = os.path.join(APP_DIR, "browser.pid")
BROWSER_LOG_FILE = os.path.join(APP_DIR, "browser.log")


def cdp_alive(endpoint: str) -> bool:
    try:
        with urllib.request.urlopen(f"{endpoint}/json/version", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def launch_browser(endpoint: str, headless: bool = False):
    """Launch Chromium with CDP enabled. Writes the shared browser.pid so
    service.sh can still manage/stop the process."""
    port = endpoint.rsplit(":", 1)[-1]
    browser_bin = os.environ.get("BROWSER_BIN", "chromium")
    chrome_args = os.environ.get("CHROME_ARGS", f"--remote-debugging-port={port} --no-first-run --no-default-browser-check")
    if headless:
        chrome_args += " --headless=new"
    log = open(BROWSER_LOG_FILE, "ab")
    proc = subprocess.Popen(
        [browser_bin] + chrome_args.split(),
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    with open(BROWSER_PID_FILE, "w") as f:
        f.write(str(proc.pid))
    return proc


class BrowserManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    async def initialize(self, endpoint="http://127.0.0.1:9222", headless: bool = False) -> bool:
        """Returns True if a (re)connection was established, False if already connected."""
        if self.initialized:
            connected = False
            try:
                connected = self.browser.is_connected()
            except Exception:
                pass
            if connected and cdp_alive(endpoint):
                return False
            print("Existing browser connection lost, re-initializing...")
            await self._teardown()

        if not cdp_alive(endpoint):
            print(f"CDP not reachable at {endpoint}, launching browser...")
            launch_browser(endpoint, headless=headless)
            for _ in range(20):
                if cdp_alive(endpoint):
                    break
                await asyncio.sleep(0.5)
            else:
                raise RuntimeError(f"Browser did not come up at {endpoint} after 10s. Check {BROWSER_LOG_FILE}")

        self.playwright = await async_playwright().start()

        # Connect to an existing browser instance via CDP
        self.browser = await self.playwright.chromium.connect_over_cdp(endpoint)
        self.context: BrowserContext = self.browser.contexts[0]

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
        return True

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
                self.active_page: Page = await self.context.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(self.active_page)
        return self.active_page

    async def _teardown(self):
        try:
            if self.initialized:
                await self.context.close()
        except Exception:
            pass
        try:
            await self.playwright.stop()
        except Exception:
            pass
        self.initialized = False

    async def cleanup(self):
        await self._teardown()

# Singleton instance
browser_manager = BrowserManager()
