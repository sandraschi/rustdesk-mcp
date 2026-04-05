#!/usr/bin/env python3
"""
MCP Server entry point for RustDesk MCP.

This is the FastMCP 2.14.1 compliant server entry point that should be used
by MCP clients and integrations.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rustdesk_mcp.config import get_config
from rustdesk_mcp.services.rustdesk_service import RustDeskService
from rustdesk_mcp.tools import RustDeskTools
from fastmcp import FastMCP


async def main():
    """Main entry point for the MCP server."""
    # Configure logging
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # Get configuration
        config = get_config()
        logger.info(f"Configuration loaded: {config.host}:{config.port}")

        # Initialize RustDesk service and tools
        rustdesk_service = RustDeskService(
            rustdesk_path=config.rustdesk_path,
            config_dir=config.rustdesk_config_dir,
            id_server_host=config.rustdesk_id_server_host,
            id_server_port=config.rustdesk_id_server_port,
            relay_server_host=config.rustdesk_relay_server_host,
            relay_server_port=config.rustdesk_relay_server_port,
            api_url=config.rustdesk_api_url,
            api_key=config.rustdesk_api_key,
            api_username=config.rustdesk_api_username,
            api_password=config.rustdesk_api_password
        )
        rustdesk_tools = RustDeskTools(rustdesk_service)

        if rustdesk_service.mock_mode:
            logger.warning("RustDesk service initialized in mock mode - install RustDesk for full functionality")
        else:
            logger.info("RustDesk service initialized successfully")

        # Create FastMCP server
        mcp = FastMCP(
            name=os.getenv("MCP_SERVER_NAME", "RustDesk MCP Server"),
            version="0.1.0-alpha",
        )

        # Register tools
        await register_tools(mcp, rustdesk_service, rustdesk_tools)

        logger.info("RustDesk MCP Server starting...")
        await mcp.run_stdio_async()

    except Exception as e:
        logger.exception(f"RustDesk MCP Server failed to start: {e}")
        sys.exit(1)


async def register_tools(mcp: FastMCP, service: RustDeskService, tools: RustDeskTools):
    """Register all MCP tools with comprehensive documentation."""

    @mcp.tool()
    async def get_rustdesk_status() -> dict:
        """
        Get comprehensive status information about the RustDesk service and current connections.

        FEATURES:
        - Service availability checking
        - Connection status monitoring
        - Installation verification
        - Mock mode detection for development

        Returns:
            Dictionary containing service status and connection information

        Examples:
            Basic status check: get_rustdesk_status()
        """
        return await service.get_status()

    @mcp.tool()
    async def get_detailed_rustdesk_status() -> dict:
        """
        Get detailed RustDesk status including local ID, active sessions, and address book information.

        FEATURES:
        - Local ID retrieval
        - Active session enumeration
        - Address book contents
        - Network configuration details
        - Performance metrics

        Returns:
            Dictionary containing detailed system status

        Examples:
            Full system status: get_detailed_rustdesk_status()
        """
        return await service.get_detailed_status()

    @mcp.tool()
    async def check_rustdesk_installation() -> dict:
        """
        Check if RustDesk is properly installed and running on the system.

        Returns:
            Dictionary with installation and runtime status
        """
        return {
            "installed": service.is_installed(),
            "running": service.is_running(),
            "executable_path": str(service.rustdesk_path) if service.rustdesk_path else None,
            "config_dir": str(service.config_dir) if service.config_dir else None,
            "mock_mode": service.mock_mode
        }

    @mcp.tool()
    async def get_rustdesk_id() -> dict:
        """
        Retrieve the local RustDesk ID required for remote connections.

        Returns:
            Dictionary containing the local RustDesk ID and validation info
        """
        return await service.get_rustdesk_id()

    @mcp.tool()
    async def list_active_sessions() -> dict:
        """
        List all currently active RustDesk remote desktop sessions.

        Returns:
            Dictionary containing list of active sessions with details
        """
        return await service.list_active_sessions()

    @mcp.tool()
    async def get_address_book() -> dict:
        """
        Retrieve the RustDesk address book containing saved peer connections.

        Returns:
            Dictionary containing address book entries
        """
        return await service.get_address_book()

    @mcp.tool()
    async def connect_to_peer(peer_id: str, password: str, session_id: str | None = None) -> dict:
        """
        Establish a remote desktop connection to a RustDesk peer.

        Args:
            peer_id: The RustDesk ID of the remote machine to connect to
            password: The password set on the remote machine for this connection
            session_id: Optional custom session identifier for tracking

        Returns:
            Dictionary containing connection status and session information
        """
        from rustdesk_mcp.tools import ConnectionRequest
        request = ConnectionRequest(peer_id=peer_id, password=password, session_id=session_id)
        return await tools.connect_to_peer(request)

    @mcp.tool()
    async def disconnect_peer(session_id: str | None = None) -> dict:
        """
        Disconnect from active RustDesk remote desktop sessions.

        Args:
            session_id: Optional session identifier to disconnect specific session

        Returns:
            Dictionary containing disconnection status
        """
        return await tools.disconnect_peer(session_id)

    @mcp.tool()
    async def transfer_file(local_path: str, remote_path: str, direction: str = "upload", session_id: str | None = None) -> dict:
        """
        Transfer files between local and remote RustDesk-connected machines.

        Args:
            local_path: Path to the local file for transfer
            remote_path: Destination path on the remote machine
            direction: Transfer direction - "upload" or "download"
            session_id: Optional session identifier

        Returns:
            Dictionary containing transfer status and details
        """
        from rustdesk_mcp.tools import FileTransferRequest
        request = FileTransferRequest(
            local_path=local_path,
            remote_path=remote_path,
            direction=direction,
            session_id=session_id
        )
        return await tools.transfer_file(request)

    @mcp.tool()
    async def list_remote_files(remote_path: str = "/", session_id: str | None = None) -> dict:
        """
        List files in a remote directory.

        Args:
            remote_path: Path on the remote system to list
            session_id: Optional session identifier

        Returns:
            Dictionary containing file listing
        """
        return await tools.list_remote_files(remote_path, session_id)

    @mcp.tool()
    async def take_screenshot(save_path: str | None = None, session_id: str | None = None) -> dict:
        """
        Capture a screenshot of the remote desktop session.

        Args:
            save_path: Optional path where to save the screenshot
            session_id: Optional session identifier

        Returns:
            Dictionary containing screenshot status and file information
        """
        from rustdesk_mcp.tools import ScreenshotRequest
        request = ScreenshotRequest(save_path=save_path, session_id=session_id)
        return await tools.take_screenshot(request)

    @mcp.tool()
    async def start_recording(save_path: str | None = None, session_id: str | None = None) -> dict:
        """
        Start recording the remote desktop session.

        Args:
            save_path: Optional path to save the recording
            session_id: Optional session identifier

        Returns:
            Dictionary containing recording status
        """
        from rustdesk_mcp.tools import RecordingRequest
        request = RecordingRequest(save_path=save_path, session_id=session_id)
        return await tools.start_recording(request)

    @mcp.tool()
    async def stop_recording(session_id: str | None = None) -> dict:
        """
        Stop the current screen recording.

        Args:
            session_id: Optional session identifier

        Returns:
            Dictionary containing recording stop status
        """
        return await tools.stop_recording(session_id)

    @mcp.tool()
    async def monitor_resources(duration_seconds: int = 60, interval: float = 5.0, session_id: str | None = None) -> dict:
        """
        Monitor system resource usage.

        Args:
            duration_seconds: Duration to monitor in seconds
            interval: Interval between measurements in seconds
            session_id: Optional session identifier

        Returns:
            Dictionary containing resource monitoring data
        """
        from rustdesk_mcp.tools import MonitoringRequest
        request = MonitoringRequest(
            duration_seconds=duration_seconds,
            interval=interval,
            session_id=session_id
        )
        return await tools.monitor_resources(request)

    @mcp.tool()
    async def get_connection_quality(session_id: str | None = None) -> dict:
        """
        Get the current connection quality metrics.

        Args:
            session_id: Optional session identifier

        Returns:
            Dictionary containing connection quality metrics
        """
        return await tools.get_connection_quality(session_id)


if __name__ == "__main__":
    asyncio.run(main())