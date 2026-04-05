#!/usr/bin/env python3
"""
Simple test to verify the session listing fix.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rustdesk_mcp.services.rustdesk_service import RustDeskService


async def test_session_listing_fix():
    """Test that list_active_sessions doesn't return process lists."""
    print("Testing session listing fix...")

    # Create service in mock mode (no RustDesk installed)
    service = RustDeskService(rustdesk_path=None, config_dir=None)

    # Call list_active_sessions
    result = await service.list_active_sessions()

    print(f"Result: {result}")

    # Verify the result structure
    assert result["success"] is True, "Should return success=True"
    assert isinstance(result["sessions"], list), "Sessions should be a list"
    assert isinstance(result["count"], int), "Count should be an integer"
    assert result["count"] == len(result["sessions"]), "Count should match sessions length"

    # Most importantly - check that no sessions have connection_type "process_only"
    for session in result["sessions"]:
        assert session.get("connection_type") != "process_only", f"Found process-only session: {session}"

    # Check that the note is updated
    assert "No local processes shown" in result["note"], "Note should indicate no processes are shown"

    print("SUCCESS: Test passed! list_active_sessions no longer returns process lists.")
    print(f"Found {result['count']} actual remote sessions (expected 0 in mock mode)")


if __name__ == "__main__":
    asyncio.run(test_session_listing_fix())