# Browser Automation MCP Server

A powerful Model Context Protocol (MCP) server that transforms an AI agent into a web-agent capable of interacting with complex, high-security websites like LinkedIn and TotalJobs.

## 🌟 Overview
This service provides a stateful browser interface for LLMs. Unlike typical stateless scrapers, this server maintains a **persistent browser context**, allowing the AI to inherit authenticated sessions (cookies, localStorage) and behave like a human user.

## 🚀 Core Capabilities

### 1. Atomic Toolset
The agent has low-level control over the browser through these tools:
*   **`navigate(url)`**: Moves to a specific page and waits for network idle.
*   **`click(selector)`**: Flexibly clicks elements using CSS selectors or plain text (e.g., "Apply Now").
*   **`type_text(selector, text)`**: Inputs text into fields with human-like behavior.
*   **`read_page()`**: Returns a minified version of the DOM, stripping scripts and styles to save tokens while preserving structural data (ARIA labels, IDs).
*   **`screenshot()`**: Captures the current viewport for visual verification.
*   **`get_url()`**: Verifies the current page location—essential for detecting redirects.

### 2. Session Persistence & Auth
*   **Existing Browser Session**: Connects to an already-running Chromium instance via the Chrome DevTools Protocol (CDP), inheriting its cookies, logins, and localStorage.
*   **Self-Healing**: If the browser is not running when `setup_session` is called, the server launches it automatically on demand (and `service.sh` can manage its lifecycle too).

### 3. Bot Evasion & Stealth
*   **Playwright Stealth**: Integrates `playwright-stealth` to hide automation fingerprints and bypass aggressive bot detection on professional networking sites.
*   **Humanized Interaction**: configured to minimize "automation" triggers through custom browser arguments.

### 4. Multimodal Feedback Loop (Vision)
Designed for Vision-capable LLMs (like Gemma 4):
*   **Visual Audit Trail**: Every action automatically saves a screenshot to `/screenshots`, creating a step-by-step visual history of the agent's journey.
*   **Rich Output**: Tools provide both textual summaries and image paths, enabling the AI to "see" pop-ups, CAPTCHAs, or layout shifts.

### 5. Resilience & Debugging
*   **Automatic Tab Management**: Automatically detects and switches focus when a click opens a new tab (e.g., redirecting from LinkedIn to a company career portal).
*   **Crash Dumps**: On tool failure, the server performs a "dump" of the raw, uncleaned HTML to `/debug`, allowing developers to inspect the exact state that caused the error.

## 🛠️ Technical Architecture
- **Runtime**: Python / FastMCP
- **Engine**: Playwright (Chromium), attached to a running browser over CDP
- **Storage**: Local filesystem for screenshots and debug dumps.
- **Communication**: MCP Streamable HTTP transport (endpoint `/mcp`, port 8000).

## 📈 Example Workflow: Job Application
1.  **Discovery**: `navigate` $\rightarrow$ LinkedIn Jobs $\rightarrow$ `type_text` search terms $\rightarrow$ `read_page`.
2.  **Evaluation**: `click` specific job card $\rightarrow$ `read_page` description $\rightarrow$ `screenshot` for audit.
3.  **Pivot**: `click` "Apply" $\rightarrow$ Server detects new tab $\rightarrow$ AI switches context to external site.
4.  **Execution**: `read_page` form fields $\rightarrow$ `type_text` personal details $\rightarrow$ `screenshot` success page.
