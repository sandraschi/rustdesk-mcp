#!/usr/bin/env python3
"""
MCP Server entry point for RustDesk MCP (secondary — primary is server.py:main).

This is the FastMCP 2.14.1 compliant server entry point that should be used
by MCP clients and integrations. Includes advanced control tools not in server.py.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

from rustdesk_mcp.config import get_config
from rustdesk_mcp.server import run_server_async
from rustdesk_mcp.services.advanced_control import AdvancedControlService
from rustdesk_mcp.services.rustdesk_service import RustDeskService
from rustdesk_mcp.services.wol_service import WolService
from rustdesk_mcp.tools_module import RustDeskTools

_READ_ONLY = {"readonly": True}
_MUTATING = {}


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
            api_password=config.rustdesk_api_password,
        )
        advanced_control = AdvancedControlService()
        wol_service = WolService()
        rustdesk_tools = RustDeskTools(rustdesk_service)

        if rustdesk_service.mock_mode:
            logger.warning(
                "RustDesk service initialized in mock mode - install RustDesk for full functionality"
            )
        else:
            logger.info("RustDesk service initialized successfully")

        # Create FastMCP server
        mcp = FastMCP(
            name=os.getenv("MCP_SERVER_NAME", "RustDesk MCP Server"),
            version="0.1.0-alpha",
        )

        # Register tools
        await register_tools(mcp, rustdesk_service, rustdesk_tools, advanced_control, wol_service)

        logger.info("RustDesk MCP Server starting...")
        await run_server_async(mcp, server_name="rustdesk-mcp")

    except Exception as e:
        logger.exception(f"RustDesk MCP Server failed to start: {e}")
        sys.exit(1)


async def register_tools(
    mcp: FastMCP,
    service: RustDeskService,
    tools: RustDeskTools,
    advanced_control: AdvancedControlService,
    wol_service: WolService,
):
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
            "executable_path": str(service.rustdesk_path)
            if service.rustdesk_path
            else None,
            "config_dir": str(service.config_dir) if service.config_dir else None,
            "mock_mode": service.mock_mode,
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
    async def connect_to_peer(
        peer_id: str, password: str, session_id: str | None = None
    ) -> dict:
        """
        Establish a remote desktop connection to a RustDesk peer.

        Args:
            peer_id: The RustDesk ID of the remote machine to connect to
            password: The password set on the remote machine for this connection
            session_id: Optional custom session identifier for tracking

        Returns:
            Dictionary containing connection status and session information
        """
        from rustdesk_mcp.tools_module import ConnectionRequest

        request = ConnectionRequest(
            peer_id=peer_id, password=password, session_id=session_id
        )
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
    async def transfer_file(
        local_path: str,
        remote_path: str,
        direction: str = "upload",
        session_id: str | None = None,
    ) -> dict:
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
        from rustdesk_mcp.tools_module import FileTransferRequest

        request = FileTransferRequest(
            local_path=local_path,
            remote_path=remote_path,
            direction=direction,
            session_id=session_id,
        )
        return await tools.transfer_file(request)

    @mcp.tool()
    async def list_remote_files(
        remote_path: str = "/", session_id: str | None = None
    ) -> dict:
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
    async def take_screenshot(
        save_path: str | None = None, session_id: str | None = None
    ) -> dict:
        """
        Capture a screenshot of the remote desktop session.

        Args:
            save_path: Optional path where to save the screenshot
            session_id: Optional session identifier

        Returns:
            Dictionary containing screenshot status and file information
        """
        from rustdesk_mcp.tools_module import ScreenshotRequest

        request = ScreenshotRequest(save_path=save_path, session_id=session_id)
        return await tools.take_screenshot(request)

    @mcp.tool()
    async def start_recording(
        save_path: str | None = None, session_id: str | None = None
    ) -> dict:
        """
        Start recording the remote desktop session.

        Args:
            save_path: Optional path to save the recording
            session_id: Optional session identifier

        Returns:
            Dictionary containing recording status
        """
        from rustdesk_mcp.tools_module import RecordingRequest

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
    async def monitor_resources(
        duration_seconds: int = 60, interval: float = 5.0, session_id: str | None = None
    ) -> dict:
        """
        Monitor system resource usage.

        Args:
            duration_seconds: Duration to monitor in seconds
            interval: Interval between measurements in seconds
            session_id: Optional session identifier

        Returns:
            Dictionary containing resource monitoring data
        """
        from rustdesk_mcp.tools_module import MonitoringRequest

        request = MonitoringRequest(
            duration_seconds=duration_seconds, interval=interval, session_id=session_id
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

    @mcp.tool()
    async def wake_on_lan(
        mac_address: str,
        broadcast_ip: str = "255.255.255.255",
        port: int = 9,
        hostname: str | None = None,
    ) -> dict:
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
        result = await wol_service.send_magic_packet(mac_address, broadcast_ip, port)
        if hostname:
            result["hostname"] = hostname
        return result

    @mcp.tool()
    async def remote_click(x: int, y: int, button: str = "left") -> dict:
        """
        [DANGEROUS] Perform a mouse click at specified coordinates in the remote RustDesk window.

        This tool requires strict authorization and sanitization. Use coordinates
        relative to the remote desktop or as identified via vision tools.

        Args:
            x (int): Absolute X coordinate on the screen.
            y (int): Absolute Y coordinate on the screen.
            button (str): Mouse button to click (left, right, middle). Defaults to 'left'.

        SECURITY: Logs every action and validates window bounds.
        """
        from rustdesk_mcp import advanced_control

        return await advanced_control.remote_click(x, y, button)

    @mcp.tool()
    async def remote_type(text: str) -> dict:
        """
        [DANGEROUS] Send keyboard input to the active remote RustDesk window.

        Args:
            text (str): The text to type into the remote session.

        SECURITY: Rate-limited and logged.
        """
        from rustdesk_mcp import advanced_control

        return await advanced_control.remote_type(text)

    @mcp.tool()
    async def agentic_workflow_tool(goal: str) -> dict:
        """
        [SEP-1577] Orchestrate complex remote tasks using FastMCP sampling.

        This tool uses autonomous orchestration to achieve high-level goals on the
        remote desktop by combining vision, clicks, and typing.

        Args:
            goal (str): The high-level objective (e.g., "Install a specific software").

        SECURITY: Requires explicit user confirmation for each stage of the sampled workflow.
        """
        # This will use mcp.get_context() to sample the LLM once implemented
        return {
            "success": True,
            "message": f"Orchestrating goal: {goal}",
            "mode": "sampling",
        }


if __name__ == "__main__":
    import asyncio

    from rustdesk_mcp.server import run_server_async

    asyncio.run(run_server_async(server_name="rustdesk-mcp"))
