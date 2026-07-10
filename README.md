# RustDesk MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.4+-7c5cfc)](https://github.com/jlowin/fastmcp)
[![Just](https://img.shields.io/badge/just-ready_to_go-7c5cfc?logo=just&logoColor=white)](https://github.com/casey/just)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

FastMCP 3.4+ server for RustDesk remote desktop management. 16 tools for device status, peer connections, file transfers, Wake-on-LAN, resource monitoring, and session management. Dual transport (stdio + HTTP), Tauri 2.0 NSIS desktop app, and React webapp.

## Quick Start

```bash
uvx rustdesk-mcp
```

Or from source:
```bash
git clone https://github.com/sandraschi/rustdesk-mcp
cd rustdesk-mcp
uv sync && uv run rustdesk-mcp
```

## Tools (16)

All tools have SOTA docstrings with `Annotated[Field(description=...)]` parameters, `## Return Format`, and `## Examples`. Tools annotated with `READ_ONLY` or `MUTATING` annotations.

| Tool | Annotation | Description |
|------|-----------|-------------|
| `get_rustdesk_status` | READ_ONLY | Service status, connection count, mock mode |
| `get_detailed_rustdesk_status` | READ_ONLY | Local ID, sessions, address book, network, performance |
| `check_rustdesk_installation` | READ_ONLY | Installation check, service state, path validation |
| `get_rustdesk_id` | READ_ONLY | Local RustDesk ID for incoming connections |
| `list_active_sessions` | READ_ONLY | Sessions via socket, API, log parsing, session manager |
| `get_address_book` | READ_ONLY | Saved peers from addrbook.toml |
| `connect_to_peer` | MUTATING | Connect to remote machine by ID + password |
| `disconnect_peer` | MUTATING | Disconnect specific session or all sessions |
| `transfer_file` | MUTATING | Upload/download files (CLI + API fallback) |
| `list_remote_files` | READ_ONLY | List remote directory files (API server required) |
| `take_screenshot` | MUTATING | Capture screenshot (CLI v1.2.0+ or API) |
| `start_recording` | MUTATING | Start recording (GUI-only, CLI unsupported) |
| `stop_recording` | MUTATING | Stop recording |
| `monitor_resources` | READ_ONLY | CPU/memory/disk/network sampling over time |
| `get_connection_quality` | READ_ONLY | System-level network I/O counters |
| `wake_on_lan` | MUTATING | Send magic packet to wake sleeping machine |

## Architecture

```
AI Agent (Claude/Cursor/OpenCode)
    |
    v
FastMCP Server (stdio or HTTP :10805)
    |
    +-- RustDeskService
    |       +-- RustDeskSocketClient (TCP to hbbs:21116 / hbbr:21117)
    |       +-- REST API (JWT auth, optional pro server)
    |       +-- CLI subprocess (rustdesk.exe)
    |
    +-- SessionManager (in-memory session tracking)
    +-- WolService (Wake-on-LAN magic packets)
    +-- FastAPI web_app (:10805 -- REST API)
    +-- React webapp (:10804 -- Vite hosted locally)

Native distribution:
    NSIS installer (Tauri 2.0) -- single-file desktop app
    .mcpb bundle -- Claude Desktop distribution
```

## Transport

| Mode | Usage |
|------|-------|
| stdio | `python -m rustdesk_mcp` (default, Claude Desktop) |
| HTTP | `MCP_TRANSPORT=http MCP_PORT=10805 python -m rustdesk_mcp` |

## Webapp

React 19 + Vite 7 + Tailwind 3 + TypeScript 5.9 on port **10804**. Features:

- **Dashboard**: Health KPIs with exponential backoff retry, `data-testid` on all metrics, version/uptime display
- **Chat**: 4 personalities + Custom, skill-based preprompt (fetched from `/api/skills` on mount), streaming response, TTS (SpeakButton on messages), STT (MicButton on input), localStorage persistence (100-msg cap), export .txt, zustand state management
- **Tools**: Dynamic discovery from `/api/tools`, annotation badges (READ/RW), expandable drill-down
- **Skills**: Live skill browser with markdown content fetched from backend
- **API Docs**: Swagger UI / ReDoc toggle, quick-ref endpoint strip
- **Control**: Remote click/type wired to `POST /api/control/`, security guard toggle
- **Apps**: Dynamic fleet discovery — live port scan across 25+ known fleet ports
- **Logging**: Ring-buffer log viewer with filter, search, pagination, JSON/CSV export

## Desktop (Tauri 2.0 NSIS)

```bash
just build-native   # PyInstaller + Rust + NSIS in one command
just cua-nsis-test  # 7-phase smoke test (install -> launch -> verify -> uninstall)
```

Single installer, embedded backend (not `externalBin`), PREINSTALL/PREUNINSTALL kill hooks, optional MCP client registration in Cursor/Claude Desktop.

## LLM Discovery

On mount, the webapp probes:
- Ollama on `:11434` (probes `/api/tags`)
- LM Studio on `:1234` (probes `/v1/models`)

Provider status shown as green/red dot in chat header.

## Skills

The server ships one skill (`remote-support`) stored at `src/rustdesk_mcp/skills/remote-support/SKILL.md`. Loaded automatically by the chat page as the base system prompt.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `RUSTDESK_PATH` | auto-detect | Path to rustdesk.exe |
| `RUSTDESK_CONFIG_DIR` | auto-detect | Config directory |
| `RUSTDESK_API_URL` | (none) | Pro API server URL |
| `RUSTDESK_API_USERNAME` | admin | API username |
| `RUSTDESK_API_PASSWORD` | (none) | API password |
| `MCP_TRANSPORT` | stdio | stdio or http |
| `MCP_PORT` | 10805 | HTTP port |
| `AI_PROVIDER` | ollama | LLM provider |
| `AI_ENDPOINT` | http://localhost:11434 | LLM endpoint |
| `AI_MODEL` | gemini-2.0-flash-exp | LLM model |

## Development

```bash
just lint       # ruff check + biome check
just fix        # ruff --fix + biome --write
just test       # pytest tests/
start.ps1       # Full stack: backend + webapp
just build-native  # NSIS installer
```

## Dist

| Track | Artifact | For |
|-------|----------|-----|
| Native | `native/target/release/bundle/nsis/*-setup.exe` | End-user desktop install |
| MCPB | `mcpb pack . dist/rustdesk-mcp.mcpb` | Claude Desktop |

## RustDesk++ Headless CLI

### Info
- `--status` — Local RustDesk ID, service status, rendezvous/relay servers
- `--peer-info <peer_id>` — Check if a peer is online via hbbs
- `--get-id` — Print local RustDesk ID
- `--version` — Print version

### File Operations (relay-based, password optional for passwordless peers)
- `--send-file <peer_id> <local> <remote> [password]` — Send file to peer
- `--recv-file <peer_id> <remote> <local> [password]` — Receive file from peer
- `--list-dir <peer_id> <remote_path> [password]` — List remote directory
- `--delete-remote <peer_id> <remote_path> [password]` — Delete remote file
- `--move-remote <peer_id> <old_path> <new_path> [password]` — Move/rename remote file
- `--send-dir <peer_id> <local_dir> <remote_dir> [password]` — Send directory contents

### Server
- `--api-server [port]` — Start HTTP API server (default 10806)
- `--ipc-send <peer_id> <local> <remote>` — Send file via IPC tunnel

### Auth
- `--login` — OAuth login, prints token
- `--option <key> [value]` — Get/set config options

### Standard RustDesk Flags
`--password`, `--option`, `--config`, `--install-service`, etc. also available.

## License

MIT
