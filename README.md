# RustDesk MCP Server

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

**FastMCP 3.1.0 compliant server** for managing RustDesk remote desktop connections via the `lejianwen/rustdesk-api`.

## Quick Start

```powershell
git clone https://github.com/sandraschi/rustdesk-mcp
cd rustdesk-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

##  Status: Alpha Release

 **This is an ALPHA release** with multiple implementation approaches available.

###  What's Working (Alpha):

#### **Option 1: Corporate API Integration (Original)**
- **Infrastructure**: Docker containers running, MCP server connected to API
- **Core Issue Fixed**: No more process lists masquerading as remote sessions
- **API Integration**: HTTP calls to `lejianwen/rustdesk-api` instead of non-existent CLI commands
- **Basic Session Management**: Can list and track sessions (authentication pending)

#### **Option 2: Minimal Socket Communication (NEW)**
- **Direct Socket Access**: Communicates directly with RustDesk servers via TCP
- **No Docker Required**: Works with any running RustDesk servers
- **Minimal Dependencies**: Python + sockets only
- **Corporate-Free**: Extracts core functionality without enterprise overhead

###  In Development (Alpha Limitations):
- **API Authentication**: JWT token handling needs refinement (Option 1)
- **Command Protocol**: Discovering actual RustDesk socket commands (Option 2)
- **Full Tool Testing**: Not all MCP tools fully tested with real connections
- **Error Handling**: Some edge cases may not be handled gracefully
- **Production Readiness**: Not recommended for production use yet

##  Implementation Options

This MCP server offers **two approaches** to RustDesk integration:

### Option 1: Corporate API Integration (Default)
**Full-featured but complex** - Uses `lejianwen/rustdesk-api` management server with Docker infrastructure.

### Option 2: Minimal Socket Communication (Recommended)
**Simple and direct** - Communicates via TCP sockets without Docker or enterprise features.

See **[README_minimal.md](README_minimal.md)** for the socket implementation details.

---

##  About lejianwen/rustdesk-api (Option 1)

**Important**: This MCP server integrates with **`lejianwen/rustdesk-api`** - a community-developed management server, NOT official RustDesk APIs (which don't exist).

### Why lejianwen/rustdesk-api?

**Official RustDesk provides:**
- GUI client application only
- Basic CLI setup tools (`--get-id`, `--server`)
- No REST API or programmatic access

**lejianwen/rustdesk-api provides:**
-  **Full REST API** for programmatic RustDesk control
-  **Web admin interface** for user/device management
-  **User authentication** and access control
-  **Address book management** and device organization
-  **Connection logging** and audit trails
-  **OAuth/LDAP integration** for enterprise use

**How it works**: Our MCP server talks to the community API server, which manages official RustDesk relay servers, providing the programmatic access layer that official RustDesk lacks.

## Features

-  **FastMCP 3.1.0 Compliant** - Full compatibility with the latest FastMCP protocol
-  **Remote Desktop Management** - Control RustDesk connections via REST API
-  **Session Monitoring** - Real-time session status (not process lists)
-  **Configuration Management** - Update RustDesk settings programmatically
-  **RESTful API Integration** - Uses `lejianwen/rustdesk-api` for backend operations
-  **Docker Ready** - Complete containerized deployment with RustDesk servers

## Prerequisites

- Python 3.8+
- Docker (for API server deployment)
- `lejianwen/rustdesk-api` running (see setup instructions)

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx rustdesk-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "rustdesk-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/rustdesk-mcp", "run", "rustdesk-mcp"]
  }
}
```
### Option 1: Minimal Socket Setup (Recommended)
**For the socket-based implementation** (no Docker required):

1. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

2. **Configure servers** (optional - defaults to localhost):
   ```env
   RUSTDESK_ID_SERVER_HOST=127.0.0.1
   RUSTDESK_ID_SERVER_PORT=21116
   RUSTDESK_RELAY_SERVER_HOST=127.0.0.1
   RUSTDESK_RELAY_SERVER_PORT=21117
   ```

3. **Run MCP server**:
   ```bash
   python -m rustdesk_mcp.mcp_server
   ```

### Option 2: Full Docker Setup (Corporate)

1. **Clone both repositories:**
   ```bash
   git clone https://github.com/lejianwen/rustdesk-api.git
   cd rustdesk-api
   ```

2. **Run the automated setup:**
   ```powershell
   .\setup-and-run.ps1  # Creates .env, docker-compose, and startup scripts
   ```

3. **Start all services:**
   ```powershell
   .\start-services.ps1  # Starts API server, RustDesk servers, and MCP server
   ```

### Option 2: Manual Setup

1. **Clone and setup MCP server:**
   ```bash
   git clone <rustdesk-mcp-repo>
   cd rustdesk-mcp
   uv pip install -r requirements.txt
   ```

2. **Deploy API server:**
   ```bash
   cd ../rustdesk-api
   docker-compose -f docker-compose-setup.yaml up -d
   ```

3. **Configure environment:**
   ```bash
   # .env file should contain:
   RUSTDESK_API_URL=http://localhost:21114
   RUSTDESK_API_KEY=<generated-key>
   ```

###  Agentic Control & Safety
This server supports autonomous orchestration (clicks/typing) via FastMCP sampling. 
**Please read the [Agentic Control Guide](docs/mcp-technical/agentic-control.md)** before enabling these features.
- Mandatory Explicit Consent
- Coordinate Sanitization
- Action Auditing

4. **Start MCP server**:
    ```bash
    python -m rustdesk_mcp.mcp_server
    ```

## Usage

### Starting the Server

```bash
python -m rustdesk_mcp.mcp_server
```

The MCP server will connect to the API at `http://localhost:21114` and start on port 8077.

##  Packaging & Distribution

This repository is SOTA 2026 compliant and uses the officially validated `@anthropic-ai/mcpb` workflow for distribution.

### Pack Extension
To generate a `.mcpb` distribution bundle with complete source code and automated build exclusions:
```bash
# SOTA 2026 standard pack command
mcpb pack . dist/rustdesk-mcp.mcpb
```

### Web Interfaces

- **API Admin**: http://localhost:21114/_admin/ (username: admin, password: from logs)
- **API Server**: http://localhost:21114 (REST endpoints)
- **MCP Server**: Port 8077 (FastMCP protocol)

### MCP Tools Available

The following MCP tools are available via the API:

1. **list_active_sessions** - Get active remote sessions (no process lists!)
2. **connect_to_peer** - Connect to a RustDesk peer
3. **disconnect_peer** - Disconnect from sessions
4. **get_address_book** - Access address book
8. **get_detailed_rustdesk_status** - Comprehensive status
9. **remote_click** - [DANGEROUS] Perform mouse clicks in remote window
10. **remote_type** - [DANGEROUS] Inject keyboard input to remote session
11. **agentic_workflow_tool** - [SEP-1577] Orchestrate autonomous remote tasks

### Example Usage

**List Active Sessions:**
```python
# Via MCP - returns real remote sessions, not processes
result = await list_active_sessions()
print(f"Active sessions: {result['count']}")
```

**Connect to Peer:**
```python
await connect_to_peer("123456789", "password123")
```

## Architecture

```
    HTTP         Relay     
   MCP Server     lejianwen API     RustDesk Server  
   (Port 8077)                   (Port 21114)                  (hbbs/hbbr)      
                                 Web Admin                                      
                                 REST API                                       
                           
                                                                                       
                                                                                       
                                                                            
                                                                             RustDesk Clients 
                                                                               (GUI/CLI)      
                                                                            
```

### Component Explanations:

- **MCP Server (Port 8077)**: FastMCP protocol interface providing tools for AI assistants
- **lejianwen/rustdesk-api (Port 21114)**: Community management server providing:
  - REST API for programmatic control
  - Web admin interface for management
  - User authentication and device management
  - Address book and connection logging
- **RustDesk Server (hbbs/hbbr)**: Official relay servers handling P2P connections
- **RustDesk Clients**: Standard GUI/CLI clients that connect through the servers

**Why this architecture?** Official RustDesk lacks APIs, so we use the community API server as the management layer.

## Development

### Setting Up for Development

1. **Clone repositories:**
   ```bash
   git clone <rustdesk-mcp-repo>
   git clone https://github.com/lejianwen/rustdesk-api.git
   ```

2. **Setup Python environment:**
   ```bash
   cd rustdesk-mcp
   uv pip install -r requirements.txt
   ```

3. **Deploy API server:**
   ```bash
   cd ../rustdesk-api
   docker-compose -f docker-compose-setup.yaml up -d
   ```

### Running Tests

```bash
# Test API integration
python test_api.py

# Run MCP server tests
pytest tests/
```

### API Integration Details

- **Authentication**: Uses API key from environment
- **Endpoints**: All calls proxy through `lejianwen/rustdesk-api`
- **Fallback**: Session manager provides local tracking when API unavailable
- **Fixed Issue**: No more process lists - only real remote sessions

## Troubleshooting

- **API Connection Failed**: Check Docker containers are running
- **Authentication Errors**: Verify API key in .env file
- **Session Lists Empty**: This is correct - no fake process entries


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[lejianwen/rustdesk-api](https://github.com/lejianwen/rustdesk-api)** - Community API server that made this possible
- **[RustDesk](https://rustdesk.com/)** - The open-source remote desktop software
- **[FastMCP](https://FastMCP 3.1.0com/)** - The MCP protocol implementation

---

**Status**:  **API Integration Complete** - Real remote sessions, no process lists!
