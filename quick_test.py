#!/usr/bin/env python3
"""Quick test for RustDesk MCP functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def quick_test():
    """Quick test of RustDesk functionality."""
    try:
        from rustdesk_mcp.services.rustdesk_service import RustDeskService
        from rustdesk_mcp.config import get_config

        print("=== Quick RustDesk Test ===")

        config = get_config()
        service = RustDeskService(config.rustdesk_path, config.rustdesk_config_dir)

        print(f"RustDesk path: {service.rustdesk_path}")
        print(f"Config dir: {service.config_dir}")
        print(f"Mock mode: {service.mock_mode}")
        print(f"Installed: {service.is_installed()}")
        print(f"Running: {service.is_running()}")

        # Test basic status
        status = await service.get_status()
        print(f"Status: {status}")

        print("[SUCCESS] Basic functionality working!")
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)