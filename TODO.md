# TODO: Migrate browser-mcp from legacy SSE transport to Streamable HTTP

**Status:** DONE (server side, 2026-11-26) — server migrated to Streamable HTTP at `/mcp`, verified with curl. Remaining: update OpenCode client config on 192.168.0.74 (step 4) and confirm with `opencode mcp list`.
**Created:** 2026-11-26
**Priority:** High — OpenCode currently cannot connect at all

## Why (root cause)

OpenCode V2 (v2.4.2) connects to remote MCP servers **only** using the MCP
**Streamable HTTP** transport (its client ships `StreamableHTTPClientTransport`;
there is no legacy SSE client transport). This server currently serves the
**deprecated legacy HTTP+SSE transport** (`mcp.run(transport="sse")` in
`server.py`), which only accepts:

- `GET /sse` (open the event stream)
- `POST /messages/?session_id=...` (send JSON-RPC)

So OpenCode POSTs its `initialize` request to `/sse` and gets:

```
Error POSTing to endpoint: Method Not Allowed (HTTP 405)
```

Evidence (2026-11-26, from 192.168.0.74):

```
POST /sse   -> 405   (what OpenCode does, fails)
GET  /sse   -> 200   (legacy SSE stream, works but OpenCode can't use it)
POST /mcp   -> 404   (Streamable HTTP endpoint does not exist yet)
```

The legacy SSE transport was removed from the MCP spec in the 2025-03-26
revision and is deprecated in the Python SDK.

## Standard required

**MCP Streamable HTTP transport** (spec revision 2025-03-26 or later).

With the Python MCP SDK (`mcp` package), that means:

- **Dependency:** `mcp >= 1.8.0` (Streamable HTTP support was added in 1.8.0;
  recommend the latest 1.x release, e.g. `mcp[cli]==1.12.*`).
  ⚠️ Stay on the **1.x line**: SDK 2.x rewrote the API (`MCPServer` instead of
  `FastMCP`) and would require rewriting `server.py`. Pin to 1.x in
  `requirements.txt` (there is currently no requirements file — add one).
- **Transport:** `mcp.run(transport="streamable-http")`
- **Endpoint:** the SDK serves Streamable HTTP at `streamable_http_path`,
  which defaults to **`/mcp`**. All JSON-RPC (initialize, tools/list,
  tools/call, ...) goes to a single endpoint via POST (and optionally GET for
  server-initiated streams).

## Changes to make (on 192.168.0.10)

### 1. `server.py` — switch the transport (line 137)

```python
# before
    mcp.run(transport="sse")

# after
    mcp.run(transport="streamable-http")
```

Nothing else in `server.py` needs to change: `FastMCP("Browser-Automation",
host="0.0.0.0", port=8000)` works as-is — the Streamable HTTP app binds to the
same host/port and serves `/mcp`.

### 2. Dependencies

Create/update `requirements.txt` in the deployed directory and install:

```
mcp>=1.8.0,<2.0
uvicorn>=0.30
playwright
playwright-stealth
```

(Keep whatever else the current venv needs; the point is to make sure the
`mcp` package in the venv is ≥ 1.8.0 — check with
`venv/bin/pip show mcp`.)

### 3. Restart the service

The deployed copy lives at `/home/m247/workspace/browser_mcp` (note:
underscore, per `service.sh`):

```bash
cd /home/m247/workspace/browser_mcp
./service.sh restart
```

### 4. Update the OpenCode client config (on 192.168.0.74, after the server is up)

Both files currently point at the old SSE URL. Change the URL from
`http://192.168.0.10:8000/sse` to **`http://192.168.0.10:8000/mcp`**:

- `~/.config/opencode/opencode.json` → `mcp.browser-mcp.url`
- `~/opencode.json` → `mcp.browser-mcp.url`

Config changes hot-reload in OpenCode; no restart needed.

## Verification (run after the server restart)

```bash
# 1. Streamable HTTP endpoint exists and answers initialize:
curl -s -i -X POST http://192.168.0.10:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"0.0.1"}}}'
# Expected: 200 with an mcp-session-id header and an initialize result

# 2. Old SSE endpoints should be gone:
curl -s -o /dev/null -w "%{http_code}\n" http://192.168.0.10:8000/sse
# Expected: 404

# 3. OpenCode sees the server as connected (on 192.168.0.74):
opencode mcp list
# Expected: ✓ browser-mcp  connected
```

## Notes

- The server reports `protocolVersion: 2025-03-26` in its initialize response
  (negotiated with clients that request it). No further protocol change
  is required — only the transport migration was needed.
- Keep `host="0.0.0.0"` so the server remains reachable from other machines
  on the LAN (it is intentionally a LAN service).
- `README.md` has been updated to document the Streamable HTTP architecture
  (`http://<host-ip>:8000/mcp`). Done.
