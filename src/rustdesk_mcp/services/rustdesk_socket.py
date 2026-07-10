#!/usr/bin/env python3
"""
Minimal RustDesk socket client - extracts the core "trickery" from lejianwen/rustdesk-api

This module provides direct TCP socket communication with RustDesk servers (hbbs/hbbr)
without needing the full management server infrastructure.

Based on lejianwen/rustdesk-api service/serverCmd.go
"""

import logging
import socket
import time

logger = logging.getLogger(__name__)

class RustDeskSocketClient:
    """Minimal client for communicating with RustDesk servers via TCP sockets."""

    DEFAULT_ID_PORT = 21116      # hbbs (ID server)
    DEFAULT_RELAY_PORT = 21117   # hbbr (Relay server)

    def __init__(self, id_server_host: str = "127.0.0.1", id_server_port: int = DEFAULT_ID_PORT,
                 relay_server_host: str = "127.0.0.1", relay_server_port: int = DEFAULT_RELAY_PORT):
        """Initialize the socket client.

        Args:
            id_server_host: Host for ID server (hbbs)
            id_server_port: Port for ID server (default 21116)
            relay_server_host: Host for relay server (hbbr)
            relay_server_port: Port for relay server (default 21117)
        """
        self.id_server = (id_server_host, id_server_port)
        self.relay_server = (relay_server_host, relay_server_port)

    def _send_command(self, server_addr: tuple[str, int], command: str, timeout: float = 1.0) -> str:
        """Send a command to a RustDesk server via TCP socket.

        Based on lejianwen/rustdesk-api SendSocketCmd method.

        Args:
            server_addr: (host, port) tuple for the server
            command: Command string to send
            timeout: Socket timeout in seconds

        Returns:
            Server response as string
        """
        host, port = server_addr

        # Try IPv6 first, then IPv4 (following lejianwen pattern)
        for family, addr in [(socket.AF_INET6, "[::1]"), (socket.AF_INET, host)]:
            try:
                sock = socket.socket(family, socket.SOCK_STREAM)
                sock.settimeout(timeout)

                # Connect to server
                if family == socket.AF_INET6:
                    sock.connect((addr, port))
                else:
                    sock.connect((host, port))

                # Send command
                sock.send(command.encode('utf-8'))

                # Small delay for processing (from lejianwen)
                time.sleep(0.1)

                # Read response
                response = sock.recv(1024).decode('utf-8')

                sock.close()
                return response.strip()

            except OSError as e:
                logger.debug(f"Socket {family} connection to {host}:{port} failed: {e}")
                if sock:
                    sock.close()
                continue

        raise ConnectionError(f"Failed to connect to server at {host}:{port}")

    def send_id_command(self, command: str) -> str:
        """Send command to ID server (hbbs)."""
        return self._send_command(self.id_server, command)

    def send_relay_command(self, command: str) -> str:
        """Send command to relay server (hbbr)."""
        return self._send_command(self.relay_server, command)

    def get_server_info(self) -> dict:
        """Get basic server information."""
        try:
            # Try to get version/info from ID server
            response = self.send_id_command("version")
            return {"id_server": "connected", "version": response}
        except Exception as e:
            return {"id_server": "disconnected", "error": str(e)}

    def list_peers(self) -> list:
        """List connected peers.

        Note: This is a simplified version. The actual peer listing
        would require parsing server-specific protocols.
        """
        # This is where we'd implement actual peer listing commands
        # For now, return empty list as we need to discover the protocol
        return []

    def get_peer_info(self, peer_id: str) -> dict | None:
        """Get information about a specific peer."""
        try:
            # Try basic peer query command
            response = self.send_id_command(f"peer {peer_id}")
            if response:
                return {"peer_id": peer_id, "info": response}
        except Exception as e:
            logger.debug(f"Failed to get peer info for {peer_id}: {e}")
        return None

    def test_connection(self) -> dict:
        """Test connection to both servers."""
        result = {"id_server": {}, "relay_server": {}}

        # Test ID server
        try:
            self.send_id_command("ping")
            result["id_server"] = {"status": "connected"}
        except Exception as e:
            result["id_server"] = {"status": "disconnected", "error": str(e)}

        # Test relay server
        try:
            self.send_relay_command("ping")
            result["relay_server"] = {"status": "connected"}
        except Exception as e:
            result["relay_server"] = {"status": "disconnected", "error": str(e)}

        return result
