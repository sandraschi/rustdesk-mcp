"""
RustDeskMCP - FastMCP 2.14.1 Server for RustDesk Remote Desktop Management

Provides natural language interface for RustDesk operations through FastMCP protocol.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status

from fastmcp import FastMCP

from .auth import authenticate
from .config import get_config
from .services.rustdesk_service import RustDeskService
from .tools import RustDeskTools
from .transport import run_server
from .web import setup_webapp

logger = logging.getLogger(__name__)

# Store the service instances
rustdesk_service: Optional[RustDeskService] = None
rustdesk_tools: Optional[RustDeskTools] = None

# FastAPI Bridge - Unified with Alexa/Bookmark pattern
web_app = FastAPI(
    title="Remote Desktop Web Bridge", dependencies=[Depends(authenticate)]
)
app = web_app  # Alias for exception handlers and __init__ export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    global rustdesk_service, rustdesk_tools

    # Startup
    try:
        logger.info("Initializing RustDesk MCP Server...")

        # Get configuration
        config = get_config()
        logger.info(f"Configuration loaded: {config.host}:{config.port}")

        # Initialize RustDesk service and tools
        rustdesk_service = RustDeskService(
            config.rustdesk_path, config.rustdesk_config_dir
        )
        rustdesk_tools = RustDeskTools(rustdesk_service)

        if rustdesk_service.mock_mode:
            logger.warning(
                "RustDesk service initialized in mock mode - install RustDesk for full functionality"
            )
        else:
            logger.info("RustDesk service initialized successfully")

        # Register tools with MCP
        await register_tools()

        logger.info("RustDesk MCP Server startup complete")

    except Exception as e:
        logger.exception("Failed to initialize RustDesk MCP Server")
        raise

    yield

    # Shutdown
    logger.info("Shutting down RustDesk MCP Server")


# Initialize FastMCP
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "RustDesk MCP Server"),
    version="0.1.0",
)

# Setup webapp bridge
setup_webapp(web_app, mcp_app=mcp)


async def init_for_stdio() -> None:
    """Initialize service and register tools for STDIO mode (called before run_server)."""
    global rustdesk_service, rustdesk_tools
    config = get_config()
    rustdesk_service = RustDeskService(
        config.rustdesk_path, config.rustdesk_config_dir
    )
    rustdesk_tools = RustDeskTools(rustdesk_service)
    if rustdesk_service.mock_mode:
        logger.warning(
            "RustDesk service initialized in mock mode - install RustDesk for full functionality"
        )
    await register_tools()


async def register_tools():
    """Register tools with the MCP server."""
    if not rustdesk_service or not rustdesk_tools:
        raise RuntimeError("RustDesk service or tools not initialized")

    # Register status tools
    @mcp.tool()
    async def get_rustdesk_status() -> Dict[str, Any]:
        """
        Get comprehensive status information about the RustDesk service and current connections.

        FEATURES:
        - Service availability checking
        - Connection status monitoring
        - Installation verification
        - Mock mode detection for development

        Returns:
            Dictionary containing:
            - service_status: Current RustDesk service state
            - connections: Active connection count
            - installed: Whether RustDesk is installed
            - mock_mode: Whether running in mock mode
            - version: RustDesk version if available

        Examples:
            Basic status check: get_rustdesk_status()
            Monitor service health: get_rustdesk_status()

        Notes:
            - Returns mock data when RustDesk is not installed
            - Service status includes running, stopped, or error states
            - Connection count helps monitor active sessions
        """
        return await rustdesk_service.get_status()

    @mcp.tool()
    async def get_detailed_rustdesk_status() -> Dict[str, Any]:
        """
        Get detailed RustDesk status including local ID, active sessions, and address book information.

        FEATURES:
        - Local RustDesk ID retrieval
        - Active session enumeration
        - Address book contents
        - Network configuration details
        - Performance metrics

        Returns:
            Dictionary containing:
            - local_id: This machine's RustDesk ID
            - active_sessions: List of current connections with details
            - address_book: Saved peer connections
            - network_info: IP addresses and ports
            - performance: CPU/memory usage

        Examples:
            Full system status: get_detailed_rustdesk_status()
            Check active connections: get_detailed_rustdesk_status()

        Notes:
            - Local ID is required for other machines to connect
            - Active sessions show current remote connections
            - Address book contains frequently accessed peers
        """
        return await rustdesk_service.get_detailed_status()

    @mcp.tool()
    async def check_rustdesk_installation() -> Dict[str, Any]:
        """
        Check if RustDesk is properly installed and running on the system.

        FEATURES:
        - Installation verification
        - Service status checking
        - Path validation
        - Configuration directory verification
        - Mock mode detection

        Returns:
            Dictionary containing:
            - installed: True if RustDesk executable is found
            - running: True if RustDesk service is currently running
            - executable_path: Full path to RustDesk executable
            - config_dir: Path to RustDesk configuration directory
            - mock_mode: True if using mock implementation

        Examples:
            Installation check: check_rustdesk_installation()
            Service verification: check_rustdesk_installation()

        Notes:
            - Mock mode is used when RustDesk is not installed
            - Executable path helps with troubleshooting installation issues
            - Config directory contains user settings and address book
        """
        return {
            "installed": rustdesk_service.is_installed(),
            "running": rustdesk_service.is_running(),
            "executable_path": str(rustdesk_service.rustdesk_path)
            if rustdesk_service.rustdesk_path
            else None,
            "config_dir": str(rustdesk_service.config_dir)
            if rustdesk_service.config_dir
            else None,
            "mock_mode": rustdesk_service.mock_mode,
        }

    @mcp.tool()
    async def get_rustdesk_id() -> Dict[str, Any]:
        """
        Retrieve the local RustDesk ID required for remote connections.

        FEATURES:
        - Local ID retrieval
        - ID format validation
        - Network reachability check
        - ID persistence verification

        Returns:
            Dictionary containing:
            - id: The local RustDesk ID (numeric string)
            - valid: True if ID format is valid
            - network_reachable: True if ID is accessible over network
            - persistent: True if ID persists across restarts

        Examples:
            Get local ID: get_rustdesk_id()
            Share ID for connection: get_rustdesk_id()

        Notes:
            - This ID is what other machines need to connect to this computer
            - ID is typically a 9-10 digit number
            - ID remains the same across service restarts
        """
        return await rustdesk_service.get_rustdesk_id()

    @mcp.tool()
    async def list_active_sessions() -> Dict[str, Any]:
        """
        List all currently active RustDesk remote desktop sessions.

        FEATURES:
        - Active connection enumeration
        - Session details retrieval
        - Connection duration tracking
        - Remote peer identification
        - Bandwidth usage monitoring

        Returns:
            Dictionary containing:
            - sessions: List of active sessions with details:
                - session_id: Unique session identifier
                - remote_id: Connecting peer's ID
                - remote_ip: Connecting peer's IP address
                - start_time: Session start timestamp
                - duration: Session duration in seconds
                - bandwidth: Current bandwidth usage

        Examples:
            View active connections: list_active_sessions()
            Monitor session activity: list_active_sessions()

        Notes:
            - Shows only currently active connections
            - Session IDs are unique per connection
            - Duration helps identify long-running sessions
        """
        # Get base session information from service
        base_result = await rustdesk_service.list_active_sessions()

        # If we have real sessions from session manager, return those
        if base_result.get("sessions") and any(
            s.get("connection_type") == "tracked_session"
            for s in base_result["sessions"]
        ):
            return base_result

        # Otherwise, enhance with additional detection methods
        sessions = []

        try:
            # Check for established network connections on RustDesk ports
            rustdesk_ports = [21116, 21117, 21118, 21119]
            network_sessions = []

            for conn in psutil.net_connections(kind="inet"):
                if conn.status == "ESTABLISHED" and conn.laddr and conn.raddr:
                    local_port = conn.laddr.port
                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port

                    if local_port in rustdesk_ports or remote_port in rustdesk_ports:
                        network_sessions.append(
                            {
                                "session_id": f"net_{abs(hash(f'{remote_ip}:{remote_port}')) % 10000}",
                                "remote_ip": remote_ip,
                                "remote_port": remote_port,
                                "local_port": local_port,
                                "status": "established",
                                "connection_type": "network_detected",
                                "detected_at": datetime.utcnow().isoformat(),
                                "source": "network_scan",
                            }
                        )

            # Add network sessions to results
            sessions.extend(network_sessions)

            # Parse recent connection manager logs
            try:
                config = get_config()
                if config.rustdesk_config_dir:
                    log_dir = Path(config.rustdesk_config_dir) / "log" / "cm"
                    if log_dir.exists():
                        current_log = log_dir / "RustDesk_rCURRENT.log"
                        if current_log.exists():
                            with open(
                                current_log, "r", encoding="utf-8", errors="ignore"
                            ) as f:
                                lines = f.readlines()[-5:]  # Last 5 lines

                            for line in reversed(lines):
                                if "conn_id:" in line and (
                                    "clipboard" in line or "established" in line
                                ):
                                    try:
                                        parts = line.split()
                                        timestamp = f"{parts[0]} {parts[1]}"
                                        conn_id_part = [
                                            p for p in parts if "conn_id:" in p
                                        ]
                                        if conn_id_part:
                                            conn_id = (
                                                conn_id_part[0]
                                                .split("conn_id:")[1]
                                                .rstrip(",")
                                            )

                                            # Don't duplicate network sessions
                                            if not any(
                                                s.get("connection_id") == conn_id
                                                for s in sessions
                                            ):
                                                sessions.append(
                                                    {
                                                        "session_id": f"conn_{conn_id}",
                                                        "connection_id": conn_id,
                                                        "status": "recent_activity",
                                                        "connection_type": "log_detected",
                                                        "detected_at": timestamp,
                                                        "source": "connection_manager_log",
                                                    }
                                                )
                                    except (IndexError, ValueError, AttributeError):
                                        continue
                                    break  # Only get the most recent
            except Exception as e:
                logger.debug(f"Log parsing failed: {str(e)}")

        except Exception as e:
            logger.debug(f"Enhanced session detection failed: {str(e)}")

        # If no sessions found through enhanced methods, fall back to process info
        if not sessions:
            for proc in psutil.process_iter(["name", "pid", "cmdline"]):
                if proc.info["name"] and "rustdesk" in proc.info["name"].lower():
                    sessions.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cmdline": proc.info["cmdline"],
                            "status": "running",
                            "connection_type": "process_only",
                            "note": "No active remote sessions detected, showing running processes",
                        }
                    )

        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
            "methods_used": ["session_manager", "network_scan", "log_parsing"],
            "note": "Enhanced session detection: 'tracked_session'=managed, 'network_detected'=active connections, 'log_detected'=recent activity, 'process_only'=running processes",
        }

    @mcp.tool()
    async def get_address_book() -> Dict[str, Any]:
        """
        Retrieve the RustDesk address book containing saved peer connections.

        FEATURES:
        - Saved connection retrieval
        - Peer information access
        - Connection history
        - Favorite peer management
        - Alias/name resolution

        Returns:
            Dictionary containing:
            - entries: List of address book entries with:
                - id: Peer ID
                - alias: User-assigned name (if any)
                - last_connected: Timestamp of last connection
                - favorite: True if marked as favorite
                - tags: User-assigned tags for organization

        Examples:
            View saved peers: get_address_book()
            Find favorite connections: get_address_book()

        Notes:
            - Contains frequently accessed remote machines
            - Aliases make it easier to identify peers
            - Favorites appear at the top of RustDesk UI
        """
        return await rustdesk_service.get_address_book()

    # Register connection tools
    @mcp.tool()
    async def connect_to_peer(
        peer_id: str, password: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Establish a remote desktop connection to a RustDesk peer.

        FEATURES:
        - Secure peer-to-peer connections
        - Password authentication
        - Session tracking and management
        - Connection timeout handling
        - Bandwidth optimization
        - Automatic reconnection on failure

        Args:
            peer_id: The RustDesk ID of the remote machine to connect to (9-10 digit number)
            password: The password set on the remote machine for this connection
            session_id: Optional custom session identifier for tracking (auto-generated if not provided)

        Returns:
            Dictionary containing:
            - success: True if connection initiated successfully
            - session_id: Unique identifier for this session
            - message: Status message about the connection attempt
            - peer_info: Information about the connected peer
            - estimated_bandwidth: Expected connection quality

        Examples:
            Basic connection: connect_to_peer("123456789", "mypassword")
            Tracked session: connect_to_peer("123456789", "mypassword", "work-session-1")

        Notes:
            - Connection may take several seconds to establish
            - Password must match the one set on the remote machine
            - Session ID helps track multiple concurrent connections
            - Connection remains active until explicitly disconnected
        """
        from .tools import ConnectionRequest

        request = ConnectionRequest(
            peer_id=peer_id, password=password, session_id=session_id
        )
        return await rustdesk_tools.connect_to_peer(request)

    @mcp.tool()
    async def disconnect_peer(session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Disconnect from active RustDesk remote desktop sessions.

        FEATURES:
        - Individual session disconnection
        - Bulk disconnection (all sessions)
        - Graceful connection teardown
        - Session cleanup and resource release
        - Connection history preservation

        Args:
            session_id: Optional session identifier to disconnect specific session.
                       If not provided, disconnects all active sessions.

        Returns:
            Dictionary containing:
            - success: True if disconnection completed successfully
            - disconnected_sessions: List of session IDs that were disconnected
            - remaining_sessions: Number of sessions still active
            - message: Status message about the disconnection

        Examples:
            Disconnect specific session: disconnect_peer("session-123")
            Disconnect all sessions: disconnect_peer()

        Notes:
            - Specific session disconnection is preferred over bulk disconnection
            - Resources are properly cleaned up on disconnection
            - Session history is preserved for future reference
        """
        return await rustdesk_tools.disconnect_peer(session_id)

    # File transfer tools
    @mcp.tool()
    async def transfer_file(
        local_path: str,
        remote_path: str,
        direction: str = "upload",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transfer files between local and remote RustDesk-connected machines.

        FEATURES:
        - Bidirectional file transfer (upload/download)
        - Large file support with progress tracking
        - Transfer resumption on interruption
        - Compression for faster transfers
        - Integrity verification with checksums
        - Concurrent transfer management

        Args:
            local_path: Path to the local file for transfer
            remote_path: Destination path on the remote machine
            direction: Transfer direction - "upload" (local to remote) or "download" (remote to local)
            session_id: Optional session identifier for targeting specific connection

        Returns:
            Dictionary containing:
            - success: True if transfer completed successfully
            - transfer_id: Unique identifier for this transfer
            - bytes_transferred: Total bytes transferred
            - duration: Transfer duration in seconds
            - checksum: File integrity verification hash

        Examples:
            Upload file: transfer_file("/local/docs/report.pdf", "/remote/documents/", "upload")
            Download file: transfer_file("/local/downloads/", "/remote/backup.zip", "download")

        Notes:
            - Large files are automatically compressed for faster transfer
            - Transfer progress can be monitored via session status
            - Failed transfers can be resumed from interruption point
        """
        from .tools import FileTransferRequest

        request = FileTransferRequest(
            local_path=local_path,
            remote_path=remote_path,
            direction=direction,
            session_id=session_id,
        )
        return await rustdesk_tools.transfer_file(request)

    @mcp.tool()
    async def list_remote_files(
        remote_path: str = "/", session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List files in a remote directory."""
        return await rustdesk_tools.list_remote_files(remote_path, session_id)

    # Screen capture tools
    @mcp.tool()
    async def take_screenshot(
        save_path: Optional[str] = None, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Capture a screenshot of the remote desktop session.

        FEATURES:
        - High-resolution screen capture
        - Multiple monitor support
        - Automatic file naming and organization
        - Various image formats (PNG, JPEG, BMP)
        - Timestamp annotation
        - Clipboard integration

        Args:
            save_path: Optional path where to save the screenshot.
                      If not provided, saves to default location with timestamp.
            session_id: Optional session identifier for targeting specific connection

        Returns:
            Dictionary containing:
            - success: True if screenshot captured successfully
            - file_path: Full path to the saved screenshot file
            - file_size: Size of the screenshot file in bytes
            - resolution: Screenshot dimensions (width x height)
            - format: Image format used (PNG, JPEG, etc.)

        Examples:
            Auto-save screenshot: take_screenshot()
            Save to specific location: take_screenshot("/path/to/screenshot.png")

        Notes:
            - Screenshots are automatically timestamped if no path provided
            - PNG format is used by default for lossless quality
            - Large screenshots may take several seconds to capture
        """
        from .tools import ScreenshotRequest

        request = ScreenshotRequest(save_path=save_path, session_id=session_id)
        return await rustdesk_tools.take_screenshot(request)

    @mcp.tool()
    async def start_recording(
        save_path: Optional[str] = None, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start recording the remote desktop session."""
        from .tools import RecordingRequest

        request = RecordingRequest(save_path=save_path, session_id=session_id)
        return await rustdesk_tools.start_recording(request)

    @mcp.tool()
    async def stop_recording(session_id: Optional[str] = None) -> Dict[str, Any]:
        """Stop the current screen recording."""
        return await rustdesk_tools.stop_recording(session_id)

    # Monitoring tools
    @mcp.tool()
    async def monitor_resources(
        duration_seconds: int = 60,
        interval: float = 5.0,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Monitor system resource usage."""
        from .tools import MonitoringRequest

        request = MonitoringRequest(
            duration_seconds=duration_seconds, interval=interval, session_id=session_id
        )
        return await rustdesk_tools.monitor_resources(request)

    @mcp.tool()
    async def get_connection_quality(
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
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
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "rustdesk_available": rustdesk_service is not None
        and not rustdesk_service.mock_mode,
        "mock_mode": rustdesk_service.mock_mode if rustdesk_service else True,
        "version": "0.1.0",
    }


# Main entry point
def main():
    """Main entry point with unified transport handling (FastMCP 2.14.4+)."""
    # Check if we should run the web server instead of just MCP
    if os.getenv("MCP_TRANSPORT") == "http" or "--http" in os.sys.argv:
        port = int(os.getenv("MCP_PORT", "10802"))
        print(f"Starting Remote Desktop Web Bridge on port {port}...")
        import uvicorn

        uvicorn.run(web_app, host="0.0.0.0", port=port)
    else:
        asyncio.run(init_for_stdio())
        run_server(mcp, server_name="rustdesk-mcp")


if __name__ == "__main__":
    main()
