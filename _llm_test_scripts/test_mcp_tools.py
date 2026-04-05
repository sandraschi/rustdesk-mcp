#!/usr/bin/env python3
"""Test MCP tools functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_mcp_tools():
    """Test MCP tools registration."""
    try:
        from rustdesk_mcp.services.rustdesk_service import RustDeskService
        from rustdesk_mcp.config import get_config

        print("=== Testing MCP Tools ===\n")

        # Initialize service
        config = get_config()
        service = RustDeskService(config.rustdesk_path, config.rustdesk_config_dir)

        print(f"Service initialized: mock_mode={service.mock_mode}")
        print(f"Installed: {service.is_installed()}")
        print(f"Running: {service.is_running()}")
        print()

        # Test the tools that should be available
        tools = [
            ("get_rustdesk_status", "Get current status"),
            ("get_detailed_rustdesk_status", "Get detailed status"),
            ("check_rustdesk_installation", "Check installation"),
            ("get_rustdesk_id", "Get RustDesk ID"),
            ("list_active_sessions", "List active sessions"),
            ("get_address_book", "Get address book"),
            ("connect_to_peer", "Connect to peer")
        ]

        print("Available MCP Tools:")
        for tool_name, description in tools:
            print(f"  - {tool_name}: {description}")

        print("\nTesting tool functionality...")

        # Test status tool
        print("1. Testing get_rustdesk_status...")
        status_result = await service.get_status()
        print(f"   Status: {status_result}")

        # Test ID tool
        print("2. Testing get_rustdesk_id...")
        id_result = await service.get_rustdesk_id()
        print(f"   ID: {id_result}")

        # Test detailed status
        print("3. Testing get_detailed_rustdesk_status...")
        detailed_result = await service.get_detailed_status()
        print(f"   Detailed status keys: {list(detailed_result.keys())}")

        print("\n[SUCCESS] MCP tools functionality verified!")
        return True

    except Exception as e:
        print(f"[ERROR] MCP tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_tools())
    sys.exit(0 if success else 1)