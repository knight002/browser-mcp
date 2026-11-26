# Browser MCP Server

A Model Context Protocol (MCP) server that allows LLMs and AI agents to control a running Chromium browser instance in real-time via the Chrome DevTools Protocol (CDP).

## 🚀 Overview

This service acts as a bridge between an AI agent and a live browser. Instead of launching a fresh headless browser for every request, it connects to an existing Chromium session. This allows the agent to:
- Use your existing browser cookies, sessions, and logins.
- Interact with pages exactly as a human would.
- Receive visual feedback via screenshots.
- Bypass many anti-bot detections using `playwright-stealth`.

## 🛠 Architecture

`Agent` $\rightarrow$ `MCP Client` $\rightarrow$ `Browser MCP Server (Streamable HTTP)` $\rightarrow$ `CDP Bridge/Proxy` $\rightarrow$ `Running Chromium`

## ⚙️ Setup & Installation

### 1. Run the Server (starts Chromium too)
The server is managed via a helper script. `start` launches Chromium with
remote debugging enabled (CDP on port 9222) and then starts the MCP server:
```bash
chmod +x service.sh
./service.sh start
```

The browser can also be managed independently:
```bash
./service.sh browser start    # launch Chromium with CDP on port 9222
./service.sh browser stop     # stop the managed Chromium
./service.sh browser status   # check browser/CDP state
./service.sh status           # shows both server and browser state
```

Options can be overridden via environment variables:
```bash
CDP_PORT=9333 BROWSER_BIN=/usr/bin/chromium ./service.sh browser start
CHROME_ARGS="--remote-debugging-port=9222 --user-data-dir=/tmp/profile" ./service.sh browser start
```

If Chromium is already running with CDP on the expected port, the script detects
it and will not launch a duplicate.

**Self-healing:** the `setup_session` tool also starts Chromium on demand. If the
CDP endpoint is unreachable when an agent calls `setup_session` (e.g. the browser
was closed or never started), the server launches it automatically and connects.
So `./service.sh start` starting the browser is a convenience, not a requirement.

## 🛠 Available Tools for Agents

Once connected, the agent has access to the following tools:

| Tool | Description | Input |
| :--- | :--- | :--- |
| `navigate` | Go to a specific URL | `url` |
| `click` | Click an element | `selector` (CSS or text) |
| `type_text` | Fill input fields | `selector`, `text` |
| `read_page` | Extract minified HTML content | - |
| `get_url` | Get current active URL | - |
| `screenshot` | Capture current view as PNG | - |

## 📁 Project Structure

- `browser_manager.py`: Handles the CDP connection and browser state.
- `tools.py`: Implementation of high-level browser actions.
- `server.py`: The FastMCP server implementing Streamable HTTP transport on port 8000.
- `service.sh`: Management script for start/stop/restart operations.
- `screenshots/`: Directory where session images are saved.

## 🌐 Remote Access
The server binds to `0.0.0.0:8000`. Remote clients can connect via the Streamable HTTP endpoint:
`http://<host-ip>:8000/mcp`
