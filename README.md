# RustDeskMCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A FastMCP 2.10 compliant server for managing RustDesk remote desktop connections through natural language commands.

## Features

- 🚀 **FastMCP 2.10 Compliant** - Full compatibility with the latest FastMCP protocol
- 🖥️ **Remote Desktop Management** - Control RustDesk connections programmatically
- 🔍 **Status Monitoring** - Monitor connection status and system performance
- ⚙️ **Configuration Management** - Update RustDesk settings on the fly
- 🔌 **RESTful API** - Standardized API endpoints for integration
- 🛠️ **Extensible** - Easy to add new features and tools

## Prerequisites

- Python 3.8+
- RustDesk installed on the system
- RustDesk running with API access enabled

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/rustdesk-mcp.git
   cd rustdesk-mcp
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the example:

   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your configuration:

   ```env
   # Server Configuration
   HOST=0.0.0.0
   PORT=8077
   LOG_LEVEL=INFO
   
   # RustDesk Configuration
   RUSTDESK_PATH=C:\\Program Files\\RustDesk\\rustdesk.exe
   RUSTDESK_CONFIG_DIR=%APPDATA%\\RustDesk\\config
   
   # MCP Configuration
   MCP_SERVER_NAME="RustDesk MCP Server"
   ```

## Usage

### Starting the Server

```bash
python -m rustdesk_mcp.server
```

Or using the installed script:

```bash
rustdesk-mcp
```

The server will start on `http://localhost:8077` by default.

### API Documentation

Once the server is running, you can access the following endpoints:

- **API Documentation**: `http://localhost:8077/docs` (Swagger UI)
- **Alternative Documentation**: `http://localhost:8077/redoc` (ReDoc)
- **Health Check**: `http://localhost:8077/health`

### MCP Tools

The following MCP tools are available:

1. **get_rustdesk_status** - Get the current status of the RustDesk service
2. **connect_to_peer** - Connect to a RustDesk peer
3. **disconnect_peer** - Disconnect from the current session
4. **get_connection_info** - Get information about the current connection
5. **get_performance_metrics** - Get system performance metrics
6. **update_rustdesk_config** - Update RustDesk configuration

### Example API Requests

#### Get Service Status

```bash
curl -X 'GET' \
  'http://localhost:8077/api/v1/status' \
  -H 'accept: application/json'
```

#### Connect to a Peer

```bash
curl -X 'POST' \
  'http://localhost:8077/api/v1/connect' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "peer_id": "1234567890",
    "password": "your-password",
    "save_password": false
  }'
```

## Development

### Setting Up for Development

1. Clone the repository
2. Set up a virtual environment
3. Install development dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

### Running Tests

```bash
pytest
```

### Code Style

This project uses:

- **Black** for code formatting
- **isort** for import sorting
- **mypy** for static type checking
- **ruff** for linting

Run the following commands before committing:

```bash
black .
isort .
mypy .
ruff check .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [RustDesk](https://rustdesk.com/) - The open-source remote desktop software
- [FastMCP](https://github.com/yourusername/fastmcp) - The MCP protocol implementation
