""
RustDeskMCP - FastMCP 2.10 Server for RustDesk Remote Desktop Management

Provides natural language interface for RustDesk operations through FastMCP protocol.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Config, get_config
from .api.v1.routes import router as v1_router
from .services.rustdesk_service import RustDeskService

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

# Store the RustDesk service instance
rustdesk_service: Optional[RustDeskService] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    global rustdesk_service
    
    try:
        # Get configuration
        config = get_config()
        
        # Initialize RustDesk service
        rustdesk_service = RustDeskService(config.rustdesk_path, config.rustdesk_config_dir)
        
        # Register tools with MCP
        await register_tools()
        
        logger.info("RustDesk MCP Server initialized successfully")
        
    except Exception as e:
        logger.exception("Failed to initialize RustDesk MCP Server")
        raise


async def register_tools():
    """Register tools with the MCP server."""
    @mcp.tool(
        name="get_rustdesk_status",
        description="Get the current status of the RustDesk service",
    )
    async def get_rustdesk_status() -> Dict[str, Any]:
        """Get the current status of the RustDesk service."""
        if not rustdesk_service:
            raise RuntimeError("RustDesk service not initialized")
        return await rustdesk_service.get_status()
    
    @mcp.tool(
        name="connect_to_peer",
        description="Connect to a RustDesk peer",
        args_schema={
            "peer_id": {"type": "string", "description": "ID of the peer to connect to"},
            "password": {"type": "string", "description": "Password for the peer"},
        },
    )
    async def connect_to_peer(peer_id: str, password: str) -> Dict[str, Any]:
        """Connect to a RustDesk peer."""
        if not rustdesk_service:
            raise RuntimeError("RustDesk service not initialized")
        return await rustdesk_service.connect(peer_id, password)
    
    @mcp.tool(
        name="disconnect_peer",
        description="Disconnect from the current RustDesk session",
    )
    async def disconnect_peer() -> Dict[str, Any]:
        """Disconnect from the current session."""
        if not rustdesk_service:
            raise RuntimeError("RustDesk service not initialized")
        return await rustdesk_service.disconnect()
    
    @mcp.tool(
        name="get_connection_info",
        description="Get information about the current RustDesk connection",
    )
    async def get_connection_info() -> Dict[str, Any]:
        """Get information about the current connection."""
        if not rustdesk_service:
            raise RuntimeError("RustDesk service not initialized")
        return await rustdesk_service.get_connection_info()
    
    @mcp.tool(
        name="get_performance_metrics",
        description="Get system performance metrics",
    )
    async def get_performance_metrics() -> Dict[str, Any]:
        """Get system performance metrics."""
        if not rustdesk_service:
            raise RuntimeError("RustDesk service not initialized")
        return await rustdesk_service.get_performance_metrics()
    
    @mcp.tool(
        name="update_rustdesk_config",
        description="Update RustDesk configuration",
        args_schema={
            "updates": {"type": "object", "description": "Configuration updates to apply"},
        },
    )
    async def update_rustdesk_config(updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update RustDesk configuration."""
        if not rustdesk_service:
            raise RuntimeError("RustDesk service not initialized")
        return await rustdesk_service.update_config(updates)


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
