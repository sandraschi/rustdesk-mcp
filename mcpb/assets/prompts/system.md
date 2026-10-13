# RustDesk MCP Server — System Prompt

## Overview

RustDesk MCP is a FastMCP 3.4+ server that provides natural language remote desktop management through RustDesk. It exposes 21 tools spanning device status, peer connections, address book management, file transfer, screen capture, resource monitoring, Wake-on-LAN, and session lifecycle. Dual transport (stdio for Claude Desktop, HTTP on port 10805 for webapp).

The server connects to RustDesk through multiple channels: direct TCP socket communication with hbbs/hbbr servers (port 21116/21117), REST API calls to RustDesk Pro (JWT-authenticated), and CLI subprocess calls to the rustdesk.exe binary. In the absence of any real RustDesk installation, it runs in mock mode and returns simulated responses.

## Architecture

The server has four layers:

1. **MCP Tool Layer** (`server.py`, `tools_module.py`) — 21 tool functions registered on a FastMCP instance. Each tool uses `Annotated[Field(description=...)]` for parameter documentation, returns structured dicts with `success`, `message`, and domain-specific fields, and is annotated with `READ_ONLY` or `MUTATING` annotations.

2. **Service Layer** (`services/rustdesk_service.py`) — `RustDeskService` class that owns all business logic. Wraps socket communication (`RustDeskSocketClient`), REST API requests (`aiohttp.ClientSession`), and CLI subprocess calls. Handles JWT authentication to RustDesk Pro API, mock mode fallback, and error recovery with suggestions.

3. **Session Manager** (`services/session_manager.py`) — In-memory session tracking with `session_id` (UUID), peer ID, status (`connecting`, `connected`, `disconnected`, `error`), and timestamps. Each `connect_to_peer` creates a tracked session; `disconnect_peer` closes it. Session history is retained for audit.

4. **Infrastructure Services** — `WolService` (sends Wake-on-LAN magic packets via the `wakeonlan` package), `RustDeskSocketClient` (direct TCP socket commands to hbbs:21116 and hbbr:21117).

## Complete Tool Reference

### Status & Discovery Tools

#### get_rustdesk_status
READ_ONLY. Returns comprehensive service status: whether RustDesk is running, installed, mock mode state, connection count, and version string. This is the first tool to call before any operation — it confirms the backend is ready. In mock mode, it returns simulated data.

Return: `{"success": bool, "service_status": str, "connections": int, "installed": bool, "mock_mode": bool, "version": str}`

#### get_detailed_rustdesk_status
READ_ONLY. Extended status including local RustDesk ID (the 9-10 digit identifier that other machines need to connect), active session list with connection types (tracked session, network detected, log detected), address book entries, network interface configuration (IP, gateway, DNS), and performance metrics (CPU, memory, disk, network I/O).

Return: `{"success": bool, "local_id": str, "active_sessions": list, "address_book": list, "network_info": dict, "performance": dict}`

#### check_rustdesk_installation
READ_ONLY. Verifies the RustDesk installation: checks if the executable file exists at the configured path, whether the RustDesk process is currently running, and whether mock mode is active. Returns the resolved executable path and config directory.

Return: `{"installed": bool, "running": bool, "executable_path": str | None, "config_dir": str | None, "mock_mode": bool}`

#### get_rustdesk_id
READ_ONLY. Retrieves the local RustDesk ID by calling `rustdesk.exe --get-id`. This ID is required for other machines to initiate incoming connections. On mock mode, returns MOCK-123456789.

Return: `{"success": bool, "id": str, "valid": bool, "network_reachable": bool}`

### Connection Management Tools

#### list_active_sessions
READ_ONLY. Lists all active RustDesk remote desktop sessions using a multi-method detection strategy. Primary: direct TCP socket communication with hbbs/hbbr servers to query connected peers. Fallback 1: RustDesk Pro API `/api/sessions` or `/api/audit/conn`. Fallback 2: in-memory `SessionManager` for locally tracked sessions. Enhanced detection also scans `psutil.net_connections` for ESTABLISHED connections on RustDesk ports (21116-21119) and parses the connection manager log file for recent activity.

Each session entry includes: `session_id`, `peer_id`/`remote_ip`, `status`, `connection_type` (tracked_session, network_detected, log_detected, process_only), `detected_at` timestamp, and `source`.

Return: `{"success": bool, "sessions": list, "count": int, "methods_used": list}`

#### connect_to_peer
MUTATING. Establishes a remote desktop connection to a RustDesk peer. Requires the peer's 9-10 digit RustDesk ID and the password configured on the remote machine. Creates a tracked session in the SessionManager with a UUID session ID. Optional `session_id` parameter allows custom tracking labels. Connection may take several seconds to establish; the session remains active until `disconnect_peer` is called.

The tool first attempts API-based connection via `POST /api/connect`, then falls back to `rustdesk.exe --connect <peer_id> --password <password>`. The password is passed as-is — the remote machine must have this password configured.

Return: `{"success": bool, "session_id": str, "message": str, "peer_info": dict}`

#### disconnect_peer
MUTATING. Disconnects one or all active sessions. When called without arguments, disconnects every tracked session. When `session_id` is provided, only that session is disconnected. Uses `rustdesk.exe --disconnect` and updates SessionManager state to `disconnected`. Retains session history for audit.

Return: `{"success": bool, "disconnected_sessions": list, "remaining_sessions": int, "message": str}`

### Address Book Tools

#### get_address_book
READ_ONLY. Reads the RustDesk address book where saved peer connections are stored. RustDesk stores this in `addrbook.toml` (TOML format with `[peers]` section) or as JSON. The tool tries multiple file paths: `addrbook.toml`, `address_book.toml`, `peers.json`, `addrbook.json`. Each entry contains the peer ID, alias (display name), note, tags, and last used timestamp.

Return: `{"success": bool, "entries": list, "count": int}`

#### add_address_book_entry
MUTATING. Adds a peer to the RustDesk address book. Requires the 9-10 digit RustDesk ID. Optional alias (human-readable name), note (description text), and tags (list of strings for categorization) help identify the peer. Writes to `addrbook.toml` in the config directory. Returns an error if the peer ID already exists.

Return: `{"success": bool, "message": str}`

#### update_address_book_entry
MUTATING. Updates an existing address book entry. Each field (alias, note, tags) is optional — omit a field to keep its current value. Reads the current `addrbook.toml`, finds the entry by peer ID, applies the changes, and writes back.

Return: `{"success": bool, "message": str}`

#### remove_address_book_entry
MUTATING. Removes a peer from the address book. Requires the peer ID. Deletes the entry from `addrbook.toml`. Returns an error if the peer ID is not found.

Return: `{"success": bool, "message": str}`

### File Transfer Tools

#### transfer_file
MUTATING. Transfers files between local and remote RustDesk-connected machines. Direction is `"upload"` (local to remote) or `"download"` (remote to local). Uses a multi-strategy fallback chain:

1. **RustDesk++ fork API** (fastest): Probes `http://127.0.0.1:10806/api/v1/file/upload` with POST JSON (local_path, remote_path, direction). 10s timeout.
2. **RustDesk++ fork CLI**: Calls `rustdesk.exe --send-file <peer_id> <local> <remote>` (upload) or `--recv-file <peer_id> <remote> <local>` (download). Requires `peer_id`. 20s timeout.
3. **Stock RustDesk CLI**: Calls `rustdesk.exe --file-transfer <args>`. 120s timeout.
4. **RustDesk Pro API**: If `RUSTDESK_API_URL` is configured, calls `POST /api/peer/file`.

If all methods fail, returns `error_type="not_implemented"` with suggestions: use SCP/SFTP, use RustDesk GUI drag-and-drop, upgrade to RustDesk CLI v1.2.0+, or configure `RUSTDESK_API_URL`.

Return: `{"success": bool, "message": str, "data": dict, "error_type": str, "suggestions": list}`

#### list_remote_files
READ_ONLY. Lists files in a remote directory. Requires the RustDesk API server (Pro version) configured via `RUSTDESK_API_URL`. Calls `GET /api/peer/files?path=<remote_path>`. Without API server, returns `error_type="not_implemented"` with SSH/SFTP suggestions.

Return: `{"success": bool, "data": dict, "method": str, "error_type": str, "suggestions": list}`

#### compare_folders
READ_ONLY. Compares a local directory against a remote directory. Reads local files via `pathlib.Path`, lists remote files via `list_remote_files`, then cross-references. Reports five categories:
- **only_local**: files present locally but not on remote
- **only_remote**: files present on remote but not locally
- **size_mismatch**: files on both sides with different sizes (includes both sizes)
- **newer_local**: common files with newer modification time locally
- **newer_remote**: common files with newer modification time on remote
- **identical**: files matching in name, size, and modification time

Return: `{"success": bool, "local_dir": str, "remote_dir": str, "only_local": [str], "only_remote": [str], "size_mismatch": [{"file": str, "local_size": int, "remote_size": int}], "newer_local": [str], "newer_remote": [str], "identical": [str], "local_count": int, "remote_count": int}`

#### sync_folder
MUTATING. Synchronizes a local directory with a remote directory. Runs `compare_folders` first, then transfers files that are missing or newer in the source. Supports two directions:
- `"to_remote"`: pushes local changes to remote (uploads only_local + newer_local files)
- `"to_local"`: pulls remote changes to local (downloads only_remote + newer_remote files)

`dry_run=True` (default) previews what would be transferred without actually copying. Set `dry_run=False` to execute transfers. Each file is transferred via `transfer_file` with error collection. Requires `peer_id` for the fork CLI transfer path.

Return: `{"success": bool, "direction": str, "dry_run": bool, "transferred": [str], "skipped": [str], "errors": [str], "total": int}`

### Screen Capture Tools

#### take_screenshot
MUTATING. Captures a screenshot of the remote desktop session. Requires RustDesk CLI v1.2.0+ or a configured API server. When successful, returns the save path. If the CLI lacks screenshot support, returns `error_type="not_implemented"` with suggestions: update RustDesk, use GUI, or configure API server.

Return: `{"success": bool, "message": str, "data": dict, "error_type": str, "suggestions": list}`

#### start_recording
MUTATING. Starts recording the remote desktop session. Screen recording is not supported via RustDesk CLI; the RustDesk GUI must be used. Returns `error_type="not_implemented"` with suggestions to use RustDesk GUI or OBS Studio.

Return: `{"success": bool, "error": str, "error_type": str, "suggestions": list}`

#### stop_recording
MUTATING. Stops the current screen recording. Same limitations as `start_recording` — returns not_implemented with GUI suggestion.

Return: `{"success": bool, "error": str, "error_type": str, "suggestions": list}`

### Monitoring Tools

#### monitor_resources
READ_ONLY. Monitors system resource usage over time. Samples CPU percentage (per-core), memory (total, available, percent, used, free), disk (total, used, free, percent), and network I/O (bytes sent/recv, packets sent/recv) at regular intervals. Duration is capped at 3600 seconds (1 hour); interval is clamped to 0.5-60 seconds.

Returns both raw measurements (timestamps with full metric snapshots) and summary statistics (avg/max/min for CPU and memory, total bytes transferred for network, optional latency stats).

Key parameters:
- `duration_seconds`: total monitoring period (max 3600)
- `interval`: time between samples (0.5-60s)

Return: `{"success": bool, "measurements": list, "summary": dict, "duration_seconds": int, "samples": int}`

#### get_connection_quality
READ_ONLY. Returns system-level network I/O counters from psutil (not RustDesk per-connection quality metrics). Includes bytes sent/recv, packets sent/recv, errors (in/out), and drops (in/out). Note that these are aggregate system metrics, not per-connection RustDesk stats.

Return: `{"success": bool, "data": dict, "note": str, "method": str}`

### Network Tools

#### wake_on_lan
MUTATING. Sends a Wake-on-LAN magic packet to wake a sleeping machine on the local network. Uses the `wakeonlan` Python package (requires `pip install wakeonlan`).

Key parameters:
- `mac_address`: Target MAC in any common format (aa:bb:cc:dd:ee:ff, AA-BB-CC-DD-EE-FF, aabb.ccdd.eeff)
- `broadcast_ip`: Subnet broadcast address. Default `255.255.255.255` (limited broadcast works on local subnet). For cross-subnet WOL, use the specific subnet broadcast (e.g., `192.168.1.255`).
- `port`: UDP port for the magic packet. Default 9 (discard). Port 7 (echo) also works on most NICs.
- `hostname`: Optional hostname for display purposes (not used in packet).

Prerequisites: The liaision machine must be on the same LAN. The target must have WOL enabled in BIOS/UEFI. The network driver must allow magic packets. After sending the packet, wait 30-60 seconds for the target to boot before attempting `connect_to_peer`.

Return: `{"success": bool, "message": str, "mac_address": str, "broadcast_ip": str, "port": int}`

### Prefab UI Card Tools

#### show_rustdesk_status_card
READ_ONLY, app=True. Renders RustDesk service status as a rich in-chat Prefab card with version, service status badge (Online/Offline), connection count badge, mock mode indicator, and installation status.

#### show_active_sessions_card
READ_ONLY, app=True. Renders active sessions as a Prefab card. Shows up to 10 sessions with session ID, connection type, remote IP, and status. Each session is a nested Card component. Shows "No active sessions" when empty.

#### show_address_book_card
READ_ONLY, app=True. Renders address book entries as a Prefab card. Shows up to 20 entries with peer ID, alias, and username. Shows "No address book entries" when empty.

#### show_installation_card
READ_ONLY, app=True. Renders installation check details as a Prefab card with installation badge (Installed/Not installed), service status badge (Running/Stopped), executable path, config directory, and mock mode indicator.

## Transport Modes

- **stdio** (default): `python -m rustdesk_mcp` — standard for Claude Desktop integration
- **HTTP**: `MCP_TRANSPORT=http MCP_PORT=10805 python -m rustdesk_mcp` — used by the React webapp and Tauri desktop app

## Error Handling

All tools follow the fleet error handling standard:
- On success: `{"success": true, ...domain-specific fields}`
- On failure: `{"success": false, "error": str, "error_type": str, "suggestions": list}`
- `error_type` values: `"not_implemented"` (capability not available in current RustDesk version), `"system_error"` (OS-level failure), `"general"` (catch-all)
- `suggestions` provides actionable recovery steps

The `_error_response()` helper in `server.py` auto-logs the exception traceback via `logger.exception()` before returning, so every tool failure is captured in server logs without per-tool instrumentation.

## Prefab UI Cards

The server registers four Prefab card tools for rich in-chat visualizations. These are registered as `@mcp.tool(app=True)` and render structured UI in MCP hosts that support the App protocol. They provide the same data as their JSON counterparts but in a human-readable card layout with badges, separators, and nested sections.

Cards use `prefab_ui.components`: `Badge`, `Card`, `CardContent`, `CardHeader`, `CardTitle`, `Div`, `Heading`, `Row`, `Separator`, `Text`. Each card has a `title` metadata field and a `view` tree of components.

## Session Lifecycle

Every connection goes through a defined lifecycle managed by the `SessionManager`:

1. **Connecting** — The session is created when `connect_to_peer` is called. State persists even if the actual network connection is still being established.
2. **Connected** — Updated when the API or CLI confirms the connection succeeded. The session is now tracked with the peer ID and connection timestamp.
3. **File Transfer / Monitoring** — Intermediate states (`file_transfer_completed`, `screenshot_taken`, `monitoring_completed`, `connection_quality_checked`) are recorded as annotations on the active session. These do not change the connection status.
4. **Disconnected** — Explicit `disconnect_peer` transitions the session to disconnected. The session is moved out of the active dict but retained in the history list for audit.
5. **Error** — Any exception during connect or disconnect transitions the session to error state with the error message recorded.

Sessions that are not explicitly disconnected remain in the active sessions dict indefinitely. Call `list_active_sessions` periodically to audit and `disconnect_peer` to clean up stale entries. The session history is append-only and grows unbounded within a single server process lifetime; a production deployment should implement periodic pruning.

## Transport Protocol Details

The `run_server` function in `transport.py` handles the dual transport mode:

### STDIO Mode
- Default mode. The MCP server communicates over stdin/stdout using JSON-RPC messages wrapped in newline-delimited JSON.
- Used by Claude Desktop and other MCP clients that launch the server as a subprocess.
- The `init_for_stdio()` function initializes services and registers tools before entering the event loop.

### HTTP Mode
- Activated via `MCP_TRANSPORT=http` or `--http` flag.
- The web_app FastAPI instance runs on the configured `MCP_PORT` (default 10805).
- The FastAPI app serves both the MCP HTTP transport (for SSE/streamable HTTP clients) and the REST API endpoints under `/api/v1/`.
- A health check is available at the unauthenticated `/health` endpoint, which returns server name, version, uptime, tool count, and RustDesk availability status.
- All other API routes are protected by HTTP Basic authentication per the fleet standard.

## Socket Communication (hbbs/hbbr)

The `RustDeskSocketClient` provides direct TCP socket communication with RustDesk infrastructure servers:

- **hbbs (ID Server)** — Port 21116. Handles peer ID registration and lookup. The client can connect, send commands (`version`, `ping`, `peer <id>`), and receive responses.
- **hbbr (Relay Server)** — Port 21117. Handles peer-to-peer relay connections.

The socket client is used primarily for session discovery (listing connected peers) and server health checks. It implements the protocol from lejianwen/rustdesk-api with IPv6-first connection attempts and fallback to IPv4. Each socket command has a 1-second timeout.

## API Integration (RustDesk Pro)

When `RUSTDESK_API_URL` is configured, the server connects to a RustDesk Pro API server:

1. **Authentication**: JWT-based. The server posts to `/api/login` with username/password credentials. The returned `access_token` is cached in memory for its 168-hour (7-day) validity period and used in the `Authorization: Bearer` header for subsequent API calls.
2. **Session Queries**: `GET /api/sessions` for real-time session listing, or `GET /api/audit/conn` for historical connection logs.
3. **File Operations**: `POST /api/peer/file` for file transfer, `GET /api/peer/files?path=` for remote directory listing.
4. **Connection Control**: `POST /api/connect` for initiating peer connections.

All API requests use aiohttp with a 30-second timeout and automatic re-authentication on token expiry.

## CLI Subprocess Integration

The server can invoke the RustDesk CLI binary (`rustdesk.exe`) directly for operations that the API or socket do not support:

- `--get-id`: Retrieve local RustDesk ID
- `--version`: Get installed version
- `--connect <peer_id> --password <password>`: Initiate connection
- `--disconnect`: End connection
- `--screenshot [--output <path>]`: Capture screenshot (v1.2.0+)
- `--send-file / --recv-file`: Headless file transfer (rustdesk++ fork)
- `--file-transfer`: Stock CLI file transfer (v1.2.0+)

CLI commands run in a subprocess with configurable timeout (default 30s, file transfers up to 120s). The RustDesk config directory is passed as the `RUSTDESK_CONFIG_DIR` environment variable. Output is parsed as JSON when possible; raw stdout is returned when JSON parsing fails.

## Mock Mode

When no RustDesk installation, API URL, or local hbbs/hbbr server is detected, the server runs in **mock mode**. This is indicated by `mock_mode: true` in status responses. Mock mode:

- Returns simulated data for all status and ID tools
- Returns `error_type="not_implemented"` with suggestions for connection, file transfer, screenshot, and recording tools
- Allows the server and webapp to run and be tested without a real RustDesk installation
- Is intended for development and demonstration only — all real functionality requires a RustDesk installation

## Error Handling Standard

All tools implement the fleet-wide error handling protocol from `TOOL_DESIGN_STANDARDS.md`:

1. **Structured error responses**: Every failure returns `{"success": false, "error": str, "error_type": str}` with domain-appropriate error types:
   - `"not_implemented"`: The operation requires a capability not available in the current RustDesk installation or version. Always accompanied by `suggestions` with alternative approaches.
   - `"system_error"`: OS-level failure (permissions, file not found, process crash). Accompanied by the system error message.
   - `"general"`: Catch-all for unexpected errors. The full traceback is logged server-side.

2. **Recovery suggestions**: Tools that return `"not_implemented"` include a `suggestions` list with actionable steps the user or agent can take. Examples include: "Install RustDesk for real file transfer", "Use SCP/SFTP as alternative", "Configure RUSTDESK_API_URL for API-based transfer", "Use RustDesk GUI to drag-and-drop files".

3. **Auto-logging**: Every tool boundary calls `_error_response()` which uses `logger.exception()` to capture the full traceback before returning the error dict. This ensures no exception is ever silently swallowed, without requiring per-tool try/except instrumentation.

4. **Module-import hardening**: Tool registration functions raise exceptions on failure (they do not return `False` silently). A failure to import a tool module crashes the server at startup rather than shipping a degraded server with missing tools.

5. **Bare except prevention**: All cleanup functions (orphan process killing, temporary file cleanup) log warnings with tracebacks on failure instead of silent `pass`.

## Prefab UI Library

The `prefab-ui>=0.14.0` package provides the component model for in-chat rich cards:

- `Badge(text, variant)`: Colored status indicator with `default`, `secondary`, `success`, `destructive`, `warning` variants
- `Card`, `CardHeader`, `CardTitle`, `CardContent`: Nested card containers for grouping session information
- `Div`: Layout container with optional `children` list
- `Heading(text)`: Section titles
- `Row(label, value)`: Key-value pair display
- `Separator()`: Visual divider
- `Text(content)`: Plain text content

Each Prefab card is registered as a separate `@mcp.tool(app=True)` function and returns a `PrefabApp` object wrapping the component tree. The `content` parameter (plain text) is available as a fallback for hosts that do not support App rendering.

## Directory Structure

```
src/rustdesk_mcp/
├── server.py              # FastMCP server, FastAPI bridge, all 21 tool registrations
├── tools_module.py        # ConnectionRequest, FileTransferRequest, ScreenshotRequest,
│                          # RecordingRequest, MonitoringRequest models
├── tools/
│   └── prefab_cards.py    # Prefab card tools (status, sessions, address book, install)
├── services/
│   ├── rustdesk_service.py   # RustDeskService — all business logic
│   ├── rustdesk_socket.py    # RustDeskSocketClient — TCP to hbbs/hbbr
│   ├── session_manager.py    # SessionManager — in-memory session lifecycle
│   └── wol_service.py        # WolService — Wake-on-LAN magic packets
├── config.py              # Configuration loading from env vars
├── transport.py           # Dual transport (stdio + HTTP)
├── web.py                 # Webapp setup
└── skills/
    └── remote-support/
        └── SKILL.md       # Skill definition for chat preprompt
```

## Dependencies

The server depends on these core packages:

- `fastmcp>=3.4.2`: MCP protocol implementation with FastAPI integration, Prefab UI support, and tool annotations
- `fastapi`: REST API layer for webapp integration and health checks
- `pydantic>=2.0.0`: Request/response model validation
- `psutil>=5.9.0`: System performance monitoring, network connection scanning, process detection
- `aiohttp>=3.8.0`: Async HTTP client for RustDesk Pro API calls
- `structlog>=23.0.0`: Structured logging
- `prefab-ui>=0.14.0`: In-chat rich card rendering
- `wakeonlan>=3.1.0`: WOL magic packet generation
- `pywinauto>=0.6.8`: Windows UI automation
- `pywinctl>=0.3.0`: Window control utilities

## Security Considerations

1. **Credentials in transit**: Passwords are transmitted to the RustDesk Pro API and CLI as-is. No encryption is applied beyond what RustDesk's own protocol provides.
2. **No secret storage**: The server does not store passwords. Session passwords exist only in memory during `connect_to_peer` and are discarded when the session is closed.
3. **API authentication**: The RustDesk Pro API JWT token is cached in memory with a 168-hour expiry. It is never written to disk.
4. **CLI sanitization**: CLI arguments are list-constructed (not string-interpolated) to prevent shell injection. `asyncio.create_subprocess_exec` is used instead of `subprocess.run` with `shell=True`.
5. **Mock mode safety**: In mock mode, no external connections are made and no real commands are executed. All data is simulated.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `RUSTDESK_PATH` | auto-detect | Path to rustdesk.exe |
| `RUSTDESK_CONFIG_DIR` | auto-detect | Config directory (contains addrbook.toml, config) |
| `RUSTDESK_API_URL` | (none) | RustDesk Pro API server URL |
| `RUSTDESK_API_USERNAME` | admin | API login username |
| `RUSTDESK_API_PASSWORD` | (none) | API login password |
| `RUSTDESK_FORK_API_PORT` | 10806 | RustDesk++ fork API port |
| `MCP_PORT` | 10805 | HTTP transport port |
| `MCP_TRANSPORT` | stdio | Transport mode (stdio or http) |
| `AI_PROVIDER` | ollama | LLM provider for webapp chat |
| `AI_ENDPOINT` | http://localhost:11434 | LLM endpoint |
| `AI_MODEL` | gemini-2.0-flash-exp | LLM model |

## rustdesk++ Fork CLI Reference

The rustdesk++ fork extends the official RustDesk CLI with headless operations:

- `--status` — Local RustDesk ID, service status, rendezvous/relay servers
- `--peer-info <peer_id>` — Check peer online status via hbbs
- `--get-id` — Print local RustDesk ID
- `--version` — Print version
- `--send-file <peer_id> <local> <remote> [password]` — Send file to peer
- `--recv-file <peer_id> <remote> <local> [password]` — Receive file from peer
- `--list-dir <peer_id> <remote_path> [password]` — List remote directory
- `--delete-remote <peer_id> <remote_path> [password]` — Delete remote file
- `--move-remote <peer_id> <old_path> <new_path> [password]` — Move/rename remote file
- `--send-dir <peer_id> <local_dir> <remote_dir> [password]` — Send directory contents
- `--api-server [port]` — Start HTTP API server (default 10806)
- `--ipc-send <peer_id> <local> <remote>` — Send file via IPC tunnel through active GUI
- `--login` — OAuth login for public RustDesk server, prints token
- `--option <key> [value]` — Get/set config options
