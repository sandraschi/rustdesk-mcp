#!/usr/bin/env python3
"""Test script to verify RustDesk integration features."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_rustdesk_features():
    """Test RustDesk integration features."""
    try:
        print("Testing RustDesk MCP features...")

        # Import the server module
        from rustdesk_mcp.server import app
        from rustdesk_mcp.services.rustdesk_service import RustDeskService
        from rustdesk_mcp.config import get_config

        print("[OK] Server module imported successfully")

        # Get configuration
        config = get_config()
        print(f"[OK] Configuration loaded: mock_mode={config.rustdesk_path is None}")

        # Create service instance
        service = RustDeskService(config.rustdesk_path, config.rustdesk_config_dir)
        print(f"[OK] Service created: mock_mode={service.mock_mode}")

        # Test basic functionality
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            print("\n=== Testing Endpoints ===")

            # Test health endpoint
            response = client.get("/health")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Health check: rustdesk_available={data.get('rustdesk_available')}, mock_mode={data.get('mock_mode')}")
            else:
                print(f"[FAIL] Health check failed: {response.status_code}")

            # Test status endpoint
            response = client.get("/status")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Status check: server={data.get('server')}")
                if 'installation' in data:
                    inst = data['installation']
                    print(f"    - Installed: {inst.get('installed')}")
                    print(f"    - Running: {inst.get('running')}")
                    print(f"    - Executable: {inst.get('executable_path')}")
            else:
                print(f"[FAIL] Status check failed: {response.status_code}")

            # Test API endpoints
            print("\n=== Testing API Endpoints ===")

            # Test status API
            response = client.get("/api/v1/status")
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] API status: is_running={data.get('is_running')}")
            else:
                print(f"[FAIL] API status failed: {response.status_code}")

        # Test service methods directly
        print("\n=== Testing Service Methods ===")

        # Test installation check
        installed = service.is_installed()
        running = service.is_running()
        print(f"[OK] Installation check: installed={installed}, running={running}")

        # Test ID retrieval
        print("[TEST] Getting RustDesk ID...")
        id_result = await service.get_rustdesk_id()
        if id_result.get('success'):
            print(f"[OK] RustDesk ID: {id_result.get('id')}")
        else:
            print(f"[INFO] ID retrieval failed: {id_result.get('error')}")

        # Test session listing
        print("[TEST] Listing active sessions...")
        session_result = await service.list_active_sessions()
        if session_result.get('success'):
            print(f"[OK] Active sessions: {session_result.get('count')} found")
        else:
            print(f"[INFO] Session listing failed: {session_result.get('error')}")

        # Test address book
        print("[TEST] Getting address book...")
        ab_result = await service.get_address_book()
        if ab_result.get('success'):
            ab = ab_result.get('address_book', {})
            print(f"[OK] Address book: {ab.get('count', 0)} entries")
        else:
            print(f"[INFO] Address book failed: {ab_result.get('error')}")

        print("\n=== Test Results ===")
        print(f"RustDesk Executable: {service.rustdesk_path}")
        print(f"Config Directory: {service.config_dir}")
        print(f"Mock Mode: {service.mock_mode}")
        print(f"Installed: {installed}")
        print(f"Running: {running}")

        print("\n[SUCCESS] RustDesk feature tests completed!")
        return True

    except Exception as e:
        print(f"\n[ERROR] RustDesk feature tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rustdesk_features())
    sys.exit(0 if success else 1)