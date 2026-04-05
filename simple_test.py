#!/usr/bin/env python3
"""Simple test of RustDesk MCP functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def simple_test():
    """Simple test of key RustDesk functionality."""
    try:
        from rustdesk_mcp.services.rustdesk_service import RustDeskService
        from rustdesk_mcp.config import get_config

        print("=== RustDesk MCP Simple Test ===\n")

        # Initialize service
        config = get_config()
        service = RustDeskService(config.rustdesk_path, config.rustdesk_config_dir)

        print(f"RustDesk Path: {service.rustdesk_path}")
        print(f"Config Dir: {service.config_dir}")
        print(f"Mock Mode: {service.mock_mode}")
        print(f"Installed: {service.is_installed()}")
        print(f"Running: {service.is_running()}")
        print()

        # Test RustDesk ID
        print("Testing RustDesk ID...")
        id_result = await service.get_rustdesk_id()
        print(f"ID Result: {id_result}")
        print()

        # Test status
        print("Testing status...")
        status_result = await service.get_status()
        print(f"Status: {status_result}")
        print()

        print("[SUCCESS] Core functionality working!")
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_test())
    sys.exit(0 if success else 1)