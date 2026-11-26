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
        # Try the selector as-is (CSS/Playwright selector) first, then fall back to a
        # plain-text match. This keeps bare words ("London", "Search") working while
        # also supporting selectors like button[data-at='x'] that the old
        # first-character sniffing misclassified as text.
        try:
            await page.click(selector, timeout=5000)
        except Exception:
            await page.click(f"text={selector}", timeout=5000)
        
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
        # Try the selector as a CSS/Playwright selector first, then fall back to an
        # accessible-label match (bare word like "Email"). The old first-character
        # sniffing misread selectors like button[...] as plain text.
        try:
            await page.fill(selector, text, timeout=5000)
        except Exception:
            await page.get_by_label(selector).first.fill(text, timeout=5000)

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
    return {"content": [{"type": "text", "text": page.url}]}

async def take_screenshot(page: Page, name: str) -> str:
    path = f"screenshots/{name}.png"
    await page.screenshot(path=path)
    return path

async def get_image_base64(path: str) -> str:
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def save_debug_state(page: Page, name: str):
    html = await page.content()
    with open(f"debug/{name}.html", "w", encoding="utf-8") as f:
        f.write(html)
    await take_screenshot(page, f"fail_{name}")


EXTRACT_JOBS_JS = {
    "linkedin": """() => {
        const results = [];
        const seen = new Set();
        const cards = document.querySelectorAll('.job-card-container[data-job-id]');
        cards.forEach(card => {
            const jobId = card.getAttribute('data-job-id');
            if (jobId && !seen.has(jobId)) {
                seen.add(jobId);
                const titleEl = card.querySelector('a.job-card-container__link');
                const companyEl = card.querySelector('.artdeco-entity-lockup__subtitle span');
                const captionSpans = card.querySelectorAll('.artdeco-entity-lockup__caption span');
                let location = 'N/A';
                captionSpans.forEach(s => {
                    const t = s.textContent.trim();
                    if (t && t !== 'Easy Apply' && t !== 'Promoted' && !t.includes('reviewing') && !t.includes('ago') && t.length > 3) {
                        location = t;
                    }
                });
                results.push({
                    id: jobId,
                    title: titleEl ? titleEl.getAttribute('aria-label') || titleEl.textContent.trim() : 'N/A',
                    company: companyEl ? companyEl.textContent.trim() : 'N/A',
                    url: 'https://www.linkedin.com/jobs/view/' + jobId,
                    location: location,
                    source: 'linkedin'
                });
            }
        });
        return results;
    }""",
    "totaljobs": """() => {
        const results = [];
        const seen = new Set();
        const titles = document.querySelectorAll('[data-at="job-item-title"], [data-testid="job-item-title"]');
        titles.forEach(el => {
            const link = el.tagName === 'A' ? el : el.closest('a');
            if (!link) return;
            const href = link.href;
            const idMatch = href.match(/job(\\d+)/);
            const jobId = idMatch ? idMatch[1] : href;
            if (seen.has(jobId)) return;
            seen.add(jobId);
            // Climb to the card container that also holds company/location/salary
            let card = el.parentElement;
            let guard = 0;
            while (card && !card.querySelector('[data-at="job-item-company-name"]') && guard++ < 6) {
                card = card.parentElement;
            }
            const q = sel => card ? (card.querySelector(sel) || null) : null;
            const clean = e => e ? e.textContent.replace(/\\s+/g, ' ').trim() : 'N/A';
            const descEl = q('[data-at="jobcard-content"]');
            results.push({
                id: jobId,
                title: (el.textContent || '').replace(/\\s+/g, ' ').trim() || 'N/A',
                company: clean(q('[data-at="job-item-company-name"]')),
                url: href.split('?')[0],
                location: clean(q('[data-at="job-item-location"]')),
                salary: clean(q('[data-at="job-item-salary-info"]')),
                description: descEl ? descEl.textContent.replace(/\\s+/g, ' ').trim().substring(0, 300) : 'N/A',
                source: 'totaljobs'
            });
        });
        return results;
    }""",
    "generic": """() => {
        const results = [];
        const seen = new Set();
        document.querySelectorAll('a[href]').forEach(link => {
            const href = link.href;
            if (href.includes('/job/') || href.includes('/jobs/') || href.includes('viewjob') || href.includes('jobid=')) {
                if (!seen.has(href)) {
                    seen.add(href);
                    results.push({
                        id: href,
                        title: link.textContent.trim().substring(0, 150) || 'N/A',
                        company: 'N/A',
                        url: href.split('?')[0],
                        location: 'N/A',
                        source: 'generic'
                    });
                }
            }
        });
        return results;
    }"""
}


async def extract_jobs(site: str = "generic") -> dict:
    page = await browser_manager.get_page()
    try:
        js = EXTRACT_JOBS_JS.get(site, EXTRACT_JOBS_JS["generic"])
        jobs = await page.evaluate(js)
        return {"content": [{"type": "text", "text": __import__("json").dumps({"count": len(jobs), "jobs": jobs}, indent=2)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Failed to extract jobs: {str(e)}"}]}


async def scroll(direction: str = "down", amount: int = 500) -> dict:
    page = await browser_manager.get_page()
    try:
        sign = 1 if direction == "down" else -1
        await page.evaluate(f"window.scrollBy(0, {sign * amount})")
        pos = await page.evaluate("({scrollTop: window.scrollY, scrollHeight: document.body.scrollHeight, innerHeight: window.innerHeight})")
        return {"content": [{"type": "text", "text": f"Scrolled {direction} {amount}px. Position: {pos['scrollTop']}/{pos['scrollHeight'] - pos['innerHeight']}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Scroll failed: {str(e)}"}]}


async def wait_for_element(selector: str, timeout: int = 5000) -> dict:
    page = await browser_manager.get_page()
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        count = await page.locator(selector).count()
        return {"content": [{"type": "text", "text": f"Element '{selector}' found. {count} matching element(s) on page."}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Timeout waiting for '{selector}' after {timeout}ms: {str(e)}"}]}


async def fill_application(fields: dict) -> dict:
    page = await browser_manager.get_page()
    filled = []
    failed = []
    for label_or_selector, value in fields.items():
        try:
            if label_or_selector.startswith(("#", ".", "[", "input", "select", "textarea")):
                await page.fill(label_or_selector, str(value), timeout=3000)
                filled.append(label_or_selector)
                continue
            sel = f"text={label_or_selector}"
            await page.fill(sel, str(value), timeout=3000)
            filled.append(label_or_selector)
        except Exception:
            try:
                loc = f"label='{label_or_selector}'"
                await page.locator(loc).first.fill(str(value), timeout=3000)
                filled.append(label_or_selector)
            except Exception as e2:
                failed.append({"field": label_or_selector, "error": str(e2)[:100]})
    return {"content": [{"type": "text", "text": __import__("json").dumps({"filled": filled, "failed": failed}, indent=2)}]}
