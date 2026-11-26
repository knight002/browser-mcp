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

### 1. Launch Chromium with Remote Debugging
The browser must be started with a debugging port enabled.
```bash
chromium --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0
```

### 2. Network Bridging (For Docker/Remote Users)
If the MCP server is running in a container or on another machine, use `socat` to bridge the connection to Chromium's local port:
```bash
socat TCP-LISTEN:9223,fork,reuseaddr TCP:127.0.0.1:9222
```

### 3. Run the Server
The server is managed via a helper script:
```bash
chmod +x service.sh
./service.sh start
```

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
