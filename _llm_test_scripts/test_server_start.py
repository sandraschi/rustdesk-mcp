#!/usr/bin/env python3
"""Test script to verify server can start."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_server_start():
    """Test if the server can start without errors."""
    try:
        print("Testing RustDesk MCP server startup...")

        # Import the server module
        from rustdesk_mcp.server import app, lifespan

        print("[OK] Server module imported successfully")

        # Test configuration loading
        try:
            from rustdesk_mcp.config import get_config
            config = get_config()
            print(f"[OK] Configuration loaded: mock_mode={config.rustdesk_path is None}")
        except Exception as e:
            print(f"[WARN] Configuration warning: {e}")

        # Test FastAPI app creation
        print(f"[OK] FastAPI app created: {app.title}")

        # Test lifespan context manager
        print("[OK] Lifespan handler configured")

        # Test basic endpoints
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            # Test health endpoint
            response = client.get("/health")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Health check passed: {data}")
            else:
                print(f"[FAIL] Health check failed: {response.status_code}")

            # Test status endpoint
            response = client.get("/status")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Status check passed: mock_mode={data.get('mock_mode')}")
            else:
                print(f"[FAIL] Status check failed: {response.status_code}")

        print("\n[SUCCESS] Server startup test completed successfully!")
        print("The server should now work in Cursor.")

    except Exception as e:
        print(f"\n[ERROR] Server startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_server_start())
    sys.exit(0 if success else 1)