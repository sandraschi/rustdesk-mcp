#!/usr/bin/env python3
"""Test the updated list_active_sessions method."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_sessions():
    """Test the list_active_sessions method."""
    try:
        from rustdesk_mcp.services.rustdesk_service import RustDeskService
        from rustdesk_mcp.config import get_config

        print("=== Testing list_active_sessions ===")

        config = get_config()
        service = RustDeskService(config.rustdesk_path, config.rustdesk_config_dir)

        print(f"Mock mode: {service.mock_mode}")
        print(f"Installed: {service.is_installed()}")
        print(f"Running: {service.is_running()}")

        # Test the updated method
        result = await service.list_active_sessions()
        print(f"Result: {result}")

        print("[SUCCESS] Method executed!")
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sessions())
    sys.exit(0 if success else 1)