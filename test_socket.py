#!/usr/bin/env python3
"""Test script for the minimal RustDesk socket client."""

import sys
from pathlib import Path

# Add MCP path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rustdesk_mcp.services.rustdesk_socket import RustDeskSocketClient

def test_socket_client():
    """Test the socket client functionality."""
    print("TESTING: RustDesk Socket Client...")

    client = RustDeskSocketClient()

    print("TESTING: Server connection test...")
    try:
        connection_result = client.test_connection()
        print(f"Connection test result: {connection_result}")

        if connection_result["id_server"].get("status") == "connected":
            print("SUCCESS: ID server connected")
        else:
            print("ERROR: ID server not connected")

        if connection_result["relay_server"].get("status") == "connected":
            print("SUCCESS: Relay server connected")
        else:
            print("ERROR: Relay server not connected")

    except Exception as e:
        print(f"Connection test failed: {e}")

    print("TESTING: Server info...")
    try:
        info = client.get_server_info()
        print(f"Server info: {info}")
    except Exception as e:
        print(f"Server info failed: {e}")

    print("TESTING: Peer listing...")
    try:
        peers = client.list_peers()
        print(f"Peers found: {len(peers)}")
        for peer in peers[:5]:  # Show first 5
            print(f"  - {peer}")
    except Exception as e:
        print(f"Peer listing failed: {e}")

if __name__ == "__main__":
    test_socket_client()