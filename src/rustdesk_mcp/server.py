"""
RustDeskMCP - FastMCP 2.14.1 Server for RustDesk Remote Desktop Management

Provides natural language interface for RustDesk operations through FastMCP protocol.
"""

import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

import psutil
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status

from fastmcp import FastMCP
from pydantic import Field

from .auth import authenticate
from .config import get_config
from .services.rustdesk_service import RustDeskService
from .services.wol_service import WolService
from .tools import RustDeskTools
from .transport import run_server
from .web import setup_webapp
from .api.v1.routes import router as api_v1_router

logger = logging.getLogger(__name__)
_START_TIME = time.time()

_READ_ONLY = {"readonly": True}
_MUTATING = {}

def _error_response(error: str, error_type: str = "general", **kwargs) -> Dict[str, Any]:
    """Auto-logging error response — traceback logged before returning to caller."""
    logger.exception("Tool error: %s [%s]", error, error_type)
    return {"success": False, "error": error, "error_type": error_type, **kwargs}

# Store the service instances
rustdesk_service: Optional[RustDeskService] = None
rustdesk_tools: Optional[RustDeskTools] = None
wol_service: Optional[WolService] = None

# FastAPI Bridge - Unified with Alexa/Bookmark pattern
web_app = FastAPI(title="Remote Desktop Web Bridge")
app = web_app  # Alias for exception handlers and __init__ export


@web_app.middleware("http")
async def fleet_public_health(request: Request, call_next):
    """Unauthenticated health for fleet probes (HTTPBasic on other routes)."""
    if request.url.path.rstrip("/") == "/health":
        return JSONResponse(
            {
                "status": "ok",
                "rustdesk_available": rustdesk_service is not None
                and not rustdesk_service.mock_mode,
                "mock_mode": rustdesk_service.mock_mode if rustdesk_service else True,
                "version": "0.1.0",
            }
        )
    return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    global rustdesk_service, rustdesk_tools, wol_service

    # Startup
    try:
        logger.info("Initializing RustDesk MCP Server...")

        # Get configuration
        config = get_config()
        logger.info(f"Configuration loaded: {config.host}:{config.port}")

        # Initialize services
        rustdesk_service = RustDeskService(
            config.rustdesk_path, config.rustdesk_config_dir
        )
        rustdesk_tools = RustDeskTools(rustdesk_service)
        wol_service = WolService()

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
    global rustdesk_service, rustdesk_tools, wol_service
    config = get_config()
    rustdesk_service = RustDeskService(
        config.rustdesk_path, config.rustdesk_config_dir
    )
    rustdesk_tools = RustDeskTools(rustdesk_service)
    wol_service = WolService()
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
    @mcp.tool(annotations=_READ_ONLY)
    async def get_rustdesk_status() -> Dict[str, Any]:
        """Get comprehensive status information about the RustDesk service and current connections.

        ## Return Format
        {"success": bool, "service_status": str, "connections": int, "installed": bool, "mock_mode": bool, "version": str}

        ## Examples
        await get_rustdesk_status()
        """
        return await rustdesk_service.get_status()

    @mcp.tool(annotations=_READ_ONLY)
    async def get_detailed_rustdesk_status() -> Dict[str, Any]:
        """Get detailed RustDesk status including local ID, active sessions, and address book.

        ## Return Format
        {"success": bool, "local_id": str, "active_sessions": list, "address_book": list, "network_info": dict, "performance": dict}

        ## Examples
        await get_detailed_rustdesk_status()

        Notes:
         - Local ID is required for other machines to connect
         - Active sessions show current remote connections
        """
        return await rustdesk_service.get_detailed_status()

    @mcp.tool(annotations=_READ_ONLY)
    async def check_rustdesk_installation() -> Dict[str, Any]:
        """Check if RustDesk is properly installed and running on the system.

        ## Return Format
        {"success": bool, "installed": bool, "running": bool, "executable_path": str | None, "config_dir": str | None, "mock_mode": bool}

        ## Examples
        await check_rustdesk_installation()
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

    @mcp.tool(annotations=_READ_ONLY)
    async def get_rustdesk_id() -> Dict[str, Any]:
        """Retrieve the local RustDesk ID required for remote connections.

        ## Return Format
        {"success": bool, "id": str, "valid": bool, "network_reachable": bool}

        ## Examples
        await get_rustdesk_id()

        Notes:
         - This ID is what other machines need to connect to this computer
         - ID is typically a 9-10 digit number
        """
        return await rustdesk_service.get_rustdesk_id()

    @mcp.tool(annotations=_READ_ONLY)
    async def list_active_sessions() -> Dict[str, Any]:
        """List all currently active RustDesk remote desktop sessions.

        Uses socket communication (primary), REST API (fallback), session manager (final).

        ## Return Format
        {"success": bool, "sessions": list, "count": int, "methods_used": list}

        ## Examples
        await list_active_sessions()
        """
        base_result = await rustdesk_service.list_active_sessions()
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

    @mcp.tool(annotations=_READ_ONLY)
    async def get_address_book() -> Dict[str, Any]:
        """Retrieve the RustDesk address book containing saved peer connections.

        ## Return Format
        {"success": bool, "entries": list, "count": int}

        ## Examples
        await get_address_book()

        Notes:
         - Contains frequently accessed remote machines
         - Aliases make it easier to identify peers
        """
        return await rustdesk_service.get_address_book()

    # Register connection tools
    @mcp.tool(annotations=_MUTATING)
    async def connect_to_peer(
        peer_id: Annotated[str, Field(description="The RustDesk ID of the remote machine (9-10 digit number).")],
        password: Annotated[str, Field(description="The password set on the remote machine for this connection.")],
        session_id: Annotated[Optional[str], Field(description="Optional custom session identifier for tracking.")] = None,
    ) -> Dict[str, Any]:
        """Establish a remote desktop connection to a RustDesk peer.

        ## Return Format
        {"success": bool, "session_id": str, "message": str, "peer_info": dict}

        ## Examples
        await connect_to_peer(peer_id="123456789", password="mypassword")
        await connect_to_peer(peer_id="123456789", password="mypassword", session_id="work-session-1")

        Notes:
         - Connection may take several seconds to establish
         - Session ID helps track multiple concurrent connections
         - Connection remains active until explicitly disconnected
        """
        from .tools import ConnectionRequest

        request = ConnectionRequest(
            peer_id=peer_id, password=password, session_id=session_id
        )
        return await rustdesk_tools.connect_to_peer(request)

    @mcp.tool(annotations=_MUTATING)
    async def disconnect_peer(
        session_id: Annotated[Optional[str], Field(description="Session to disconnect. Omit to disconnect all.")] = None,
    ) -> Dict[str, Any]:
        """Disconnect from active RustDesk remote desktop sessions.

        ## Return Format
        {"success": bool, "disconnected_sessions": list, "remaining_sessions": int, "message": str}

        ## Examples
        await disconnect_peer()
        await disconnect_peer(session_id="session-123")
        """
        return await rustdesk_tools.disconnect_peer(session_id)

    # File transfer tools
    @mcp.tool(annotations=_MUTATING)
    async def transfer_file(
        local_path: Annotated[str, Field(description="Path to the local file for transfer.")],
        remote_path: Annotated[str, Field(description="Destination path on the remote machine.")],
        direction: Annotated[str, Field(description="'upload' (local to remote) or 'download' (remote to local).")] = "upload",
        session_id: Annotated[Optional[str], Field(description="Session identifier for targeting specific connection.")] = None,
        peer_id: Annotated[Optional[str], Field(description="RustDesk peer ID (9-10 digit). Required for fork CLI transfer.")] = None,
    ) -> Dict[str, Any]:
        """Transfer files between local and remote RustDesk-connected machines.

        Tries fork API server first, then fork CLI --send-file/--recv-file,
        then CLI --file-transfer, then returns actionable suggestions.

        ## Return Format
        {"success": bool, "message": str, "data": dict, "error_type": str, "suggestions": list}

        ## Examples
        await transfer_file(local_path="/local/docs/report.pdf", remote_path="/remote/documents/", direction="upload", peer_id="254504451")
        await transfer_file(local_path="/local/downloads/", remote_path="/remote/backup.zip", direction="download")

        Errors:
         - Returns error_type="not_implemented" with SCP/SFTP suggestions when RustDesk CLI lacks --file-transfer
        """
        from .tools import FileTransferRequest

        request = FileTransferRequest(
            local_path=local_path, remote_path=remote_path,
            direction=direction, session_id=session_id, peer_id=peer_id,
        )
        return await rustdesk_tools.transfer_file(request)

    @mcp.tool(annotations=_READ_ONLY)
    async def list_remote_files(
        remote_path: Annotated[str, Field(description="Remote directory path to list.")] = "/",
        session_id: Annotated[Optional[str], Field(description="Session identifier.")] = None,
    ) -> Dict[str, Any]:
        """List files in a remote directory.

        ## Return Format
        {"success": bool, "data": dict, "method": str, "error_type": str, "suggestions": list}

        ## Examples
        await list_remote_files(remote_path="/home/user/documents")

        Errors:
         - Returns error_type="not_implemented" when API server is not configured
        """
        return await rustdesk_tools.list_remote_files(remote_path, session_id)

    # Screen capture tools
    @mcp.tool(annotations=_MUTATING)
    async def take_screenshot(
        save_path: Annotated[Optional[str], Field(description="Path to save the screenshot. Auto-named if omitted.")] = None,
        session_id: Annotated[Optional[str], Field(description="Session identifier.")] = None,
    ) -> Dict[str, Any]:
        """Capture a screenshot of the remote desktop session.

        Requires RustDesk CLI v1.2.0+ or an API server.

        ## Return Format
        {"success": bool, "message": str, "data": dict, "error_type": str, "suggestions": list}

        ## Examples
        await take_screenshot()
        await take_screenshot(save_path="/path/to/screenshot.png")

        Errors:
         - Returns error_type="not_implemented" when CLI lacks screenshot support
        """
        from .tools import ScreenshotRequest

        request = ScreenshotRequest(save_path=save_path, session_id=session_id)
        return await rustdesk_tools.take_screenshot(request)

    @mcp.tool(annotations=_MUTATING)
    async def start_recording(
        save_path: Annotated[Optional[str], Field(description="Path to save the recording.")] = None,
        session_id: Annotated[Optional[str], Field(description="Session identifier.")] = None,
    ) -> Dict[str, Any]:
        """Start recording the remote desktop session.

        Screen recording is not supported via RustDesk CLI. Use the RustDesk GUI.

        ## Return Format
        {"success": bool, "error": str, "error_type": str, "suggestions": list}
        """
        from .tools import RecordingRequest

        request = RecordingRequest(save_path=save_path, session_id=session_id)
        return await rustdesk_tools.start_recording(request)

    @mcp.tool(annotations=_MUTATING)
    async def stop_recording(
        session_id: Annotated[Optional[str], Field(description="Session identifier.")] = None,
    ) -> Dict[str, Any]:
        """Stop the current screen recording.

        ## Return Format
        {"success": bool, "error": str, "error_type": str, "suggestions": list}
        """
        return await rustdesk_tools.stop_recording(session_id)

    # Monitoring tools
    @mcp.tool(annotations=_READ_ONLY)
    async def monitor_resources(
        duration_seconds: Annotated[int, Field(description="Total monitoring duration in seconds (max 3600).")] = 60,
        interval: Annotated[float, Field(description="Time between measurements in seconds (0.5-60).")] = 5.0,
        session_id: Annotated[Optional[str], Field(description="Session identifier.")] = None,
    ) -> Dict[str, Any]:
        """Monitor system resource usage over time.

        Samples CPU, memory, disk, and network at regular intervals.

        ## Return Format
        {"success": bool, "measurements": list, "summary": dict, "duration_seconds": int, "samples": int}

        ## Examples
        await monitor_resources(duration_seconds=30, interval=2.0)

        Notes:
         - duration_seconds is capped at 3600 (1 hour)
         - interval is clamped to 0.5-60s
        """
        from .tools import MonitoringRequest

        request = MonitoringRequest(
            duration_seconds=duration_seconds, interval=interval, session_id=session_id
        )
        return await rustdesk_tools.monitor_resources(request)

    @mcp.tool(annotations=_READ_ONLY)
    async def get_connection_quality(
        session_id: Annotated[Optional[str], Field(description="Session identifier.")] = None,
    ) -> Dict[str, Any]:
        """Get system-level network connection quality metrics.

        Returns real psutil network I/O counters (not RustDesk per-connection stats).

        ## Return Format
        {"success": bool, "data": dict, "note": str, "method": str}

        ## Examples
        await get_connection_quality()

        Notes:
         - Uses psutil system-wide counters, not RustDesk internal quality metrics
         - Returns bytes sent/recv, packets, errors, drops
        """
        return await rustdesk_tools.get_connection_quality(session_id)

    # Wake-on-LAN tool
    @mcp.tool(annotations=_MUTATING)
    async def wake_on_lan(
        mac_address: str,
        broadcast_ip: str = "255.255.255.255",
        port: int = 9,
        hostname: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a Wake-on-LAN magic packet to wake a sleeping machine on the local network.

        Requires the liaison (always-on mini PC) to be on the same LAN as the target.
        Goliath must have WOL enabled in BIOS/UEFI and the network driver must allow
        magic packets to wake the system.

        ## Return Format
        {"success": bool, "message": str, "mac_address": str}

        ## Examples
        await wake_on_lan(mac_address="aa:bb:cc:dd:ee:ff", hostname="goliath")
        await wake_on_lan(mac_address="AA-BB-CC-DD-EE-FF", broadcast_ip="192.168.1.255", port=7)

        Notes:
            - Default port is 9 (UDP discard). Port 7 (echo) also works on many NICs.
            - broadcast_ip defaults to 255.255.255.255 (limited broadcast). For
              cross-subnet, use the specific subnet broadcast (e.g. 192.168.1.255).
            - MAC address formats: aa:bb:cc:dd:ee:ff, AA-BB-CC-DD-EE-FF, aabb.ccdd.eeff
            - After sending the packet, wait 30-60s for the target to boot, then
              use connect_to_peer to establish the RustDesk session.
        """
        if not wol_service:
            return {"success": False, "message": "WOL service not initialized"}
        result = await wol_service.send_magic_packet(mac_address, broadcast_ip, port)
        if hostname:
            result["hostname"] = hostname
        return result


# Exception handlers and route registrations
app.include_router(api_v1_router)

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


# Health check endpoint (no auth — fleet probe + load balancers)
@app.get("/health", dependencies=[])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint — fleet standard format."""
    tool_count = len(mcp.list_tools()) if mcp else 0
    return {
        "status": "ok",
        "server": "rustdesk-mcp",
        "version": "0.1.0",
        "uptime_seconds": int(time.time() - _START_TIME),
        "tool_count": tool_count,
        "rustdesk_available": rustdesk_service is not None
        and not rustdesk_service.mock_mode,
        "mock_mode": rustdesk_service.mock_mode if rustdesk_service else True,
    }


# Main entry point
def main():
    """Main entry point with unified transport handling (FastMCP 2.14.4+)."""
    # Check if we should run the web server instead of just MCP
    if os.getenv("MCP_TRANSPORT") == "http" or "--http" in sys.argv:
        port = int(os.getenv("MCP_PORT", "10805"))
        print(f"Starting Remote Desktop Web Bridge on port {port}...")
        import uvicorn

        uvicorn.run(web_app, host="0.0.0.0", port=port)
    else:
        asyncio.run(init_for_stdio())
        run_server(mcp, server_name="rustdesk-mcp")


if __name__ == "__main__":
    main()
