"""
RustDeskMCP - FastMCP 2.10 Server for RustDesk Remote Desktop Management

Provides natural language interface for RustDesk operations through FastMCP protocol.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP, Tool
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Config, get_config
from .api.v1.routes import router as v1_router
from .services.rustdesk_service import RustDeskService
from .tools import RustDeskTools
from .documentation import help_tool
from fastmcp import Tool

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RustDesk MCP Server",
    description="FastMCP 2.10 server for RustDesk remote desktop management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(v1_router)

# Initialize FastMCP
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "RustDesk MCP Server"),
    version="0.1.0",
    log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
)

# Store the service instances
rustdesk_service: Optional[RustDeskService] = None
rustdesk_tools: Optional[RustDeskTools] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    global rustdesk_service, rustdesk_tools
    
    try:
        # Get configuration
        config = get_config()
        
        # Initialize RustDesk service and tools
        rustdesk_service = RustDeskService(config.rustdesk_path, config.rustdesk_config_dir)
        rustdesk_tools = RustDeskTools(rustdesk_service)
        
        # Register tools with MCP
        await register_tools()
        
        logger.info("RustDesk MCP Server initialized successfully")
        
    except Exception as e:
        logger.exception("Failed to initialize RustDesk MCP Server")
        raise


async def register_tools():
    """Register tools with the MCP server."""
    if not rustdesk_service or not rustdesk_tools:
        raise RuntimeError("RustDesk service or tools not initialized")
    
    # Register help tool
    help_tool_def = help_tool.get_tool_definition()
    mcp.tool(
        name=help_tool_def["name"],
        description=help_tool_def["description"],
        args_schema=help_tool_def["parameters"]
    )(help_tool_def["method"])
    
    # Register status tool
    @mcp.tool(
        name="get_rustdesk_status",
        description="Get the current status of the RustDesk service",
    )
    async def get_rustdesk_status() -> Dict[str, Any]:
        """Get the current status of the RustDesk service."""
        return await rustdesk_service.get_status()
    
    # Register connection tools
    @mcp.tool(
        name="connect_to_peer",
        description="Connect to a RustDesk peer",
        args_schema={
            "peer_id": {"type": "string", "description": "ID of the peer to connect to"},
            "password": {"type": "string", "description": "Password for the peer"},
            "session_id": {"type": "string", "description": "Optional session ID for tracking", "required": False}
        }
    )
    async def connect_to_peer(peer_id: str, password: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Connect to a RustDesk peer."""
        from .tools import ConnectionRequest
        request = ConnectionRequest(peer_id=peer_id, password=password, session_id=session_id)
        return await rustdesk_tools.connect_to_peer(request)
    
    @mcp.tool(
        name="disconnect_peer",
        description="Disconnect from a RustDesk peer",
        args_schema={
            "session_id": {"type": "string", "description": "Optional session ID to disconnect. If not provided, disconnects all.", "required": False}
        }
    )
    async def disconnect_peer(session_id: Optional[str] = None) -> Dict[str, Any]:
        """Disconnect from a RustDesk peer or all peers."""
        return await rustdesk_tools.disconnect_peer(session_id)
    
    # File transfer tools
    @mcp.tool(
        name="transfer_file",
        description="Transfer a file to/from a remote peer",
        args_schema={
            "local_path": {"type": "string", "description": "Local file path"},
            "remote_path": {"type": "string", "description": "Remote file path"},
            "direction": {"type": "string", "description": "'upload' or 'download' direction", "default": "upload"},
            "session_id": {"type": "string", "description": "Optional session ID for tracking", "required": False}
        }
    )
    async def transfer_file(local_path: str, remote_path: str, direction: str = "upload", session_id: Optional[str] = None) -> Dict[str, Any]:
        """Transfer a file to/from a remote peer."""
        from .tools import FileTransferRequest
        request = FileTransferRequest(
            local_path=local_path,
            remote_path=remote_path,
            direction=direction,
            session_id=session_id
        )
        return await rustdesk_tools.transfer_file(request)
    
    @mcp.tool(
        name="list_remote_files",
        description="List files in a remote directory",
        args_schema={
            "remote_path": {"type": "string", "description": "Path on the remote system to list", "default": "/"},
            "session_id": {"type": "string", "description": "Optional session ID for tracking", "required": False}
        }
    )
    async def list_remote_files(remote_path: str = "/", session_id: Optional[str] = None) -> Dict[str, Any]:
        """List files in a remote directory."""
        return await rustdesk_tools.list_remote_files(remote_path, session_id)
    
    # Screen capture tools
    @mcp.tool(
        name="take_screenshot",
        description="Take a screenshot of the remote desktop",
        args_schema={
            "save_path": {"type": "string", "description": "Optional path to save the screenshot", "required": False},
            "session_id": {"type": "string", "description": "Optional session ID for tracking", "required": False}
        }
    )
    async def take_screenshot(save_path: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot of the remote desktop."""
        from .tools import ScreenshotRequest
        request = ScreenshotRequest(save_path=save_path, session_id=session_id)
        return await rustdesk_tools.take_screenshot(request)
    
    @mcp.tool(
        name="start_recording",
        description="Start recording the remote desktop session",
        args_schema={
            "save_path": {"type": "string", "description": "Optional path to save the recording", "required": False},
            "session_id": {"type": "string", "description": "Optional session ID for tracking", "required": False}
        }
    )
    async def start_recording(save_path: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Start recording the remote desktop session."""
        from .tools import RecordingRequest
        request = RecordingRequest(save_path=save_path, session_id=session_id)
        return await rustdesk_tools.start_recording(request)
    
    @mcp.tool(
        name="stop_recording",
        description="Stop the current screen recording",
        args_schema={
            "session_id": {"type": "string", "description": "Optional session ID for tracking", "required": False}
        }
    )
    async def stop_recording(session_id: Optional[str] = None) -> Dict[str, Any]:
        """Stop the current screen recording."""
        return await rustdesk_tools.stop_recording(session_id)
    
    # Monitoring tools
    @mcp.tool(
        name="monitor_resources",
        description="Monitor system resource usage",
        args_schema={
            "duration_seconds": {"type": "integer", "description": "Duration to monitor in seconds", "default": 60},
            "interval": {"type": "number", "description": "Interval between measurements in seconds", "default": 5.0},
            "session_id": {"type": "string", "description": "Optional session ID for tracking", "required": False}
        }
    )
    async def monitor_resources(duration_seconds: int = 60, interval: float = 5.0, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Monitor system resource usage."""
        from .tools import MonitoringRequest
        request = MonitoringRequest(
            duration_seconds=duration_seconds,
            interval=interval,
            session_id=session_id
        )
        return await rustdesk_tools.monitor_resources(request)
    
    @mcp.tool(
        name="get_connection_quality",
        description="Get the current connection quality metrics",
        args_schema={
            "session_id": {"type": "string", "description": "Optional session ID for tracking", "required": False}
        }
    )
    async def get_connection_quality(session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get the current connection quality metrics."""
        return await rustdesk_tools.get_connection_quality(session_id)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle global exceptions."""
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# Main entry point
def main():
    """Main entry point for the application."""
    import uvicorn
    
    # Get configuration
    config = get_config()
    
    # Run the FastAPI app with Uvicorn
    uvicorn.run(
        "rustdesk_mcp.server:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level=config.log_level.lower(),
    )


if __name__ == "__main__":
    main()
