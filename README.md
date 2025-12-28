# RustDesk MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)](https://github.com/lejianwen/rustdesk-api)
[![Version](https://img.shields.io/badge/Version-0.1.0--alpha-blue.svg)]()

**FastMCP 2.14.1 compliant server** for managing RustDesk remote desktop connections via the `lejianwen/rustdesk-api`.

## 🎯 Status: Alpha Release

⚠️ **This is an ALPHA release** - Core functionality works but some features are incomplete.

### ✅ What's Working (Alpha):
- **Infrastructure**: Docker containers running, MCP server connected to API
- **Core Issue Fixed**: No more process lists masquerading as remote sessions
- **API Integration**: HTTP calls to `lejianwen/rustdesk-api` instead of non-existent CLI commands
- **Basic Session Management**: Can list and track sessions (authentication pending)

### 🚧 In Development (Alpha Limitations):
- **API Authentication**: JWT token handling needs refinement
- **Full Tool Testing**: Not all MCP tools fully tested with real connections
- **Error Handling**: Some edge cases may not be handled gracefully
- **Production Readiness**: Not recommended for production use yet

## 🤔 About lejianwen/rustdesk-api

**Important**: This MCP server integrates with **`lejianwen/rustdesk-api`** - a community-developed management server, NOT official RustDesk APIs (which don't exist).

### Why lejianwen/rustdesk-api?

**Official RustDesk provides:**
- GUI client application only
- Basic CLI setup tools (`--get-id`, `--server`)
- No REST API or programmatic access

**lejianwen/rustdesk-api provides:**
- ✅ **Full REST API** for programmatic RustDesk control
- ✅ **Web admin interface** for user/device management
- ✅ **User authentication** and access control
- ✅ **Address book management** and device organization
- ✅ **Connection logging** and audit trails
- ✅ **OAuth/LDAP integration** for enterprise use

**How it works**: Our MCP server talks to the community API server, which manages official RustDesk relay servers, providing the programmatic access layer that official RustDesk lacks.

## Features

- 🚀 **FastMCP 2.14.1 Compliant** - Full compatibility with the latest FastMCP protocol
- 🖥️ **Remote Desktop Management** - Control RustDesk connections via REST API
- 🔍 **Session Monitoring** - Real-time session status (not process lists)
- ⚙️ **Configuration Management** - Update RustDesk settings programmatically
- 🔌 **RESTful API Integration** - Uses `lejianwen/rustdesk-api` for backend operations
- 🛠️ **Docker Ready** - Complete containerized deployment with RustDesk servers

## Prerequisites

- Python 3.8+
- Docker (for API server deployment)
- `lejianwen/rustdesk-api` running (see setup instructions)

## Installation

### Option 1: Full Docker Setup (Recommended)

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
   pip install -r requirements.txt
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

4. **Start MCP server:**
   ```bash
   python -m rustdesk_mcp.mcp_server
   ```

## Usage

### Starting the Server

```bash
python -m rustdesk_mcp.mcp_server
```

The MCP server will connect to the API at `http://localhost:21114` and start on port 8077.

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
5. **take_screenshot** - Capture remote screen
6. **transfer_file** - File operations
7. **get_rustdesk_status** - Service status
8. **get_detailed_rustdesk_status** - Comprehensive status

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
┌─────────────────┐    HTTP     ┌──────────────────┐    Relay     ┌──────────────────┐
│   MCP Server    │◄───────────►│ lejianwen API    │◄────────────►│ RustDesk Server  │
│   (Port 8077)   │             │   (Port 21114)   │              │ (hbbs/hbbr)      │
│                 │             │   Web Admin      │              │                  │
│                 │             │   REST API       │              │                  │
└─────────────────┘             └──────────────────┘              └──────────────────┘
                                                                                       │
                                                                                       ▼
                                                                            ┌──────────────────┐
                                                                            │ RustDesk Clients │
                                                                            │   (GUI/CLI)      │
                                                                            └──────────────────┘
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
   pip install -r requirements.txt
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[lejianwen/rustdesk-api](https://github.com/lejianwen/rustdesk-api)** - Community API server that made this possible
- **[RustDesk](https://rustdesk.com/)** - The open-source remote desktop software
- **[FastMCP](https://fastmcp.com/)** - The MCP protocol implementation

---

**Status**: ✅ **API Integration Complete** - Real remote sessions, no process lists!
