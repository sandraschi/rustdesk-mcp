# Changelog

## 0.2.0 (2026-07-10)

### New Features
- **Headless CLI** — New rustdesk++ fork with full headless operation:
  - `--status` — Print local RustDesk ID, service status, rendezvous/relay servers
  - `--peer-info <peer_id>` — Check peer online status via hbbs
  - `--get-id` — Print local RustDesk ID
  - `--version` — Print version
  - `--send-file`, `--recv-file`, `--list-dir`, `--delete-remote`, `--move-remote`, `--send-dir` — File operations via relay (password optional for passwordless peers)
  - `--api-server [port]` — Start HTTP API server (default 10806)
  - `--ipc-send <peer_id> <local> <remote>` — Send file via IPC tunnel
  - `--login` — OAuth login, prints token
  - `--option <key> [value]` — Get/set config options

### Bug Fixes
- **Server fixes** — Various stability and reliability improvements in the rustdesk++ fork server components

## 0.1.0 (2026-07-07)

### Security
- **CRITICAL: Fixed .env leak in NSIS installer** — build.ps1 now bundles `.env.example` instead of the real `.env` (which contained developer API keys). Updated `tauri.conf.json` to reference `resources/.env.example`.

### New Features
- **File transfer subsystem** — `transfer_file()` now attempts CLI `--file-transfer` first, then REST API, with proper `not_implemented` fallback and actionable suggestions (SCP/SFTP)
- **Streaming chat** — LLM responses stream via SSE (`POST /api/ai/chat/stream`), fall back to non-streaming
- **TTS/STT** — SpeakButton on assistant messages, MicButton on input field (Web Speech API)
- **Zustand state management** — chat state centralized in store with localStorage persistence, 100-msg cap
- **4th personality** — "Security Auditor" added to chat
- **Skills page** (`/skills`) — live skill browser with markdown content from backend
- **API Docs page** (`/api-docs`) — Swagger/ReDoc toggle, quick-ref endpoint strip, iframe embed
- **Fleet discovery** — Apps page now live-scans 25+ known fleet ports for active MCP servers
- **Agentic control endpoints** — `POST /api/control/remote_click` and `POST /api/control/remote_type` wired to backend

### Tool Design
- **Tool annotations** — All 16 tools tagged with `READ_ONLY` or `MUTATING`
- **SOTA docstrings** — All tools migrated to `Annotated[T, Field(description="...")]` parameter docs with `## Return Format` and `## Examples`
- **`_error_response()` helper** (Pattern 3) — auto-logging error helper for all tool boundaries, single `logger.exception()` call covers all call sites
- **`not_implemented` error_type** — All stub tools (`get_connection_quality`, `take_screenshot`, etc.) replaced with real implementations or properly tagged with `error_type` + `suggestions`
- **Hardcoded password removed** — `config.py` default `rustdesk_api_password` changed from `"vAw7I4V9"` to `""`

### Build & CI
- **npm → bun** — Build pipeline switched to bun (`bun install`, `bunx`, `bun run`), `@tauri-apps/api ^2.2.0` added
- **Build gates** — API_BASE port verification, entry point existence check, backend exe size gate (>5 MB)
- **Fixed bare `except: pass`** in `rustdesk-mcp-backend.spec` — now logs metadata copy failures

### Webapp
- **Dashboard** — Exponential backoff retry (1s/2s/4s/8s/16s), `data-testid` on all KPIs, version/uptime display, SOTA health API
- **Sidebar** — Collapse toggle moved to top (fleet standard), added Skills and API Docs links
- **CSS** — `color-scheme: dark` on body and form controls
- **App.tsx** — `/tools` route fixed (was dead link), `/skills` and `/api-docs` routes added
- **Control page** — `remote_click`/`remote_type` now call backend POST endpoints with loading/fail states

### Session Context Injection
- **`.cursorrules`** — Appended RustDesk tool-awareness prompt (concrete tool calls, recall + save actions)
- **`.windsurfrules`** — Created as copy of `.cursorrules`
- **`.claude-plugin/`** — plugin.json + hooks.json with SessionStart text injection
- **`.github/copilot-instructions.md`** — Copilot channel injection

### Documentation
- **`llms.txt`** + **`llms-full.txt`** — Created at repo root (PACKAGING_STANDARDS §5)
- **SKILL.md** — Created at `src/rustdesk_mcp/skills/remote-support/SKILL.md` with all 16 tools, best practices
- **Backend API endpoints** — `GET /api/skills`, `GET /api/skills/{name}`, `GET /api/llm/discover`, `GET /api/health` (SOTA format with server/version/uptime/tool_count), `GET /api/v1/diagnostics`

### Bug Fixes
- **Port inconsistency** — `server.py:main()` port changed from `10802` → `10805`. `config.py` default port from `8077` → `10805`
- **Missing `import psutil`** in server.py — added explicit import
- **`os.sys.argv`** → `sys.argv` in server.py
- **api/v1 router registered** on FastAPI app (was unregistered)
