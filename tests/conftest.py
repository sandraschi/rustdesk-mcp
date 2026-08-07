"""Test configuration and fixtures for RustDesk MCP."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from fastmcp import FastMCP

from rustdesk_mcp.config import Config
from rustdesk_mcp.services.rustdesk_service import RustDeskService
from rustdesk_mcp.services.session_manager import SessionManager
from rustdesk_mcp.tools import RustDeskTools


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration for testing."""
    # Create the required files/directories
    rustdesk_exe = temp_dir / "rustdesk.exe"
    rustdesk_exe.write_text("# Mock rustdesk executable")

    config_dir = temp_dir / "config"
    config_dir.mkdir()

    # Pass values directly to Config constructor
    config = Config(rustdesk_path=str(rustdesk_exe), rustdesk_config_dir=str(config_dir))
    return config


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    return AsyncMock(spec=SessionManager)


@pytest.fixture
def mock_rustdesk_service(mock_config, mock_session_manager):
    """Create a mock RustDesk service."""
    service = MagicMock(spec=RustDeskService)
    service.config = mock_config
    service.session_manager = mock_session_manager
    service.is_running.return_value = True

    # Mock async methods
    service.get_status = AsyncMock(return_value={"is_running": True})
    service.get_version = AsyncMock(return_value="1.2.0")
    service.get_config = AsyncMock(return_value={})
    service.connect = AsyncMock(return_value={"success": True, "session_id": "test-session"})
    service.disconnect = AsyncMock(return_value={"success": True})
    service.transfer_file = AsyncMock(return_value={"success": True})
    service.take_screenshot = AsyncMock(return_value={"success": True, "file_path": "/tmp/test.png"})
    service.start_screen_recording = AsyncMock(return_value={"success": True, "recording_id": "test-recording"})
    service.stop_screen_recording = AsyncMock(return_value={"success": True})
    service.monitor_resource_usage = AsyncMock(return_value={"success": True, "summary": {}})
    service.get_connection_quality = AsyncMock(return_value={"success": True, "connection_quality": {}})
    service.list_remote_files = AsyncMock(return_value={"success": True, "files": []})

    return service


@pytest.fixture
def mock_rustdesk_tools(mock_rustdesk_service):
    """Create mock RustDesk tools."""
    return MagicMock(spec=RustDeskTools)


@pytest.fixture
def test_client(mock_rustdesk_service):
    """Create a test client for FastAPI endpoints."""
    # Mock the global rustdesk_service
    import rustdesk_mcp.server
    from rustdesk_mcp.server import app

    original_service = getattr(rustdesk_mcp.server, "rustdesk_service", None)
    rustdesk_mcp.server.rustdesk_service = mock_rustdesk_service

    with TestClient(app) as client:
        yield client

    # Restore original service
    if original_service is not None:
        rustdesk_mcp.server.rustdesk_service = original_service


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    return MagicMock(spec=FastMCP)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_subprocess():
    """Mock subprocess calls for all tests."""
    with patch("asyncio.create_subprocess_exec") as mock_proc:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'{"success": true}', b"")
        mock_process.returncode = 0
        mock_proc.return_value = mock_process
        yield mock_proc


@pytest.fixture(autouse=True)
def mock_psutil():
    """Mock psutil for system monitoring tests."""
    with (
        patch("psutil.cpu_percent") as mock_cpu,
        patch("psutil.virtual_memory") as mock_mem,
        patch("psutil.disk_usage") as mock_disk,
        patch("psutil.net_io_counters") as mock_net,
        patch("psutil.cpu_count") as mock_count,
        patch("psutil.process_iter") as mock_proc,
    ):
        mock_cpu.return_value = 45.2
        mock_mem.return_value = MagicMock(
            total=17179869184, available=8589934592, percent=50.0, used=8589934592, free=8589934592
        )
        mock_disk.return_value = MagicMock(total=1000204886016, used=500000000000, free=500000000000, percent=50.0)
        mock_net.return_value = MagicMock(
            bytes_sent=1000000, bytes_recv=2000000, packets_sent=50000, packets_recv=60000
        )
        mock_count.side_effect = lambda logical=True: 8 if logical else 4

        # Mock process iteration for RustDesk detection
        mock_proc.return_value = []

        yield


@pytest.fixture
def sample_connection_request():
    """Sample connection request for testing."""
    return {"peer_id": "123456789", "password": "testpassword", "session_id": "test-session-123"}


@pytest.fixture
def sample_file_transfer_request():
    """Sample file transfer request for testing."""
    return {
        "local_path": "/tmp/test.txt",
        "remote_path": "/home/user/test.txt",
        "direction": "upload",
        "session_id": "test-session-123",
    }


@pytest.fixture
def sample_screenshot_request():
    """Sample screenshot request for testing."""
    return {"save_path": "/tmp/screenshot.png", "session_id": "test-session-123"}


@pytest.fixture
def sample_monitoring_request():
    """Sample monitoring request for testing."""
    return {"duration_seconds": 30, "interval": 2.0, "session_id": "test-session-123"}
