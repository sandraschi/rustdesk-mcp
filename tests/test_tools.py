"""Tests for RustDeskTools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from rustdesk_mcp.tools import (
    ConnectionRequest,
    FileTransferRequest,
    MonitoringRequest,
    RecordingRequest,
    RustDeskTools,
    ScreenshotRequest,
)


class TestRustDeskTools:
    """Test cases for RustDeskTools."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock RustDesk service."""
        service = MagicMock()
        service.connect = AsyncMock(return_value={"success": True, "session_id": "test-session"})
        service.disconnect = AsyncMock(return_value={"success": True, "disconnected_sessions": ["session-1"]})
        service.transfer_file = AsyncMock(return_value={"success": True})
        service.take_screenshot = AsyncMock(return_value={"success": True, "file_path": "/tmp/test.png"})
        service.start_screen_recording = AsyncMock(return_value={"success": True, "recording_id": "test-recording"})
        service.stop_screen_recording = AsyncMock(return_value={"success": True})
        service.monitor_resource_usage = AsyncMock(return_value={"success": True, "summary": {"cpu": {"avg": 50.0}}})
        service.get_connection_quality = AsyncMock(
            return_value={"success": True, "connection_quality": {"latency_ms": 10}}
        )
        service.list_remote_files = AsyncMock(return_value={"success": True, "files": []})
        service.session_manager = MagicMock()
        service.session_manager.update_session_status = AsyncMock()
        return service

    @pytest.fixture
    def tools(self, mock_service):
        """Create RustDeskTools instance."""
        return RustDeskTools(mock_service)

    @pytest.mark.asyncio
    async def test_connect_to_peer_success(self, tools, mock_service):
        """Test successful peer connection."""
        request = ConnectionRequest(peer_id="123456789", password="testpass", session_id="session-123")

        result = await tools.connect_to_peer(request)

        assert result["success"] is True
        assert result["session_id"] == "test-session"
        assert result["message"] == "Connected successfully"
        mock_service.connect.assert_called_once_with("123456789", "testpass")
        mock_service.session_manager.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_to_peer_failure(self, tools, mock_service):
        """Test failed peer connection."""
        mock_service.connect.return_value = {"success": False, "error": "Connection timeout"}

        request = ConnectionRequest(peer_id="123456789", password="wrongpass")

        result = await tools.connect_to_peer(request)

        assert result["success"] is False
        assert result["error"] == "Connection timeout"
        assert result["peer_id"] == "123456789"

    @pytest.mark.asyncio
    async def test_connect_to_peer_with_session_update_failure(self, tools, mock_service):
        """Test connection with session update failure."""
        mock_service.connect.return_value = {"success": True, "session_id": "test-session"}
        mock_service.session_manager.update_session_status.side_effect = Exception("Session update failed")

        request = ConnectionRequest(peer_id="123456789", password="testpass", session_id="session-123")

        # Should not raise exception, just log error
        result = await tools.connect_to_peer(request)

        assert result["success"] is True
        assert result["session_id"] == "test-session"

    @pytest.mark.asyncio
    async def test_disconnect_peer_specific_session(self, tools, mock_service):
        """Test disconnecting a specific session."""
        mock_service.session_manager.get_session.return_value = {"id": "session-123"}

        result = await tools.disconnect_peer("session-123")

        assert result["success"] is True
        assert "session-123" in result["disconnected_sessions"]
        mock_service.disconnect.assert_called_once_with("session-123")
        mock_service.session_manager.close_session.assert_called_once_with("session-123")

    @pytest.mark.asyncio
    async def test_disconnect_peer_all_sessions(self, tools, mock_service):
        """Test disconnecting all sessions."""
        result = await tools.disconnect_peer()

        assert result["success"] is True
        mock_service.disconnect.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_disconnect_peer_failure(self, tools, mock_service):
        """Test disconnect failure."""
        mock_service.disconnect.return_value = {"success": False, "error": "Disconnect failed"}

        result = await tools.disconnect_peer("session-123")

        assert result["success"] is False
        assert result["error"] == "Disconnect failed"

    @pytest.mark.asyncio
    async def test_transfer_file_success(self, tools, mock_service):
        """Test successful file transfer."""
        request = FileTransferRequest(
            local_path="/local/test.txt", remote_path="/remote/test.txt", direction="upload", session_id="session-123"
        )

        result = await tools.transfer_file(request)

        assert result["success"] is True
        assert result["direction"] == "upload"
        assert result["local_path"] == "/local/test.txt"
        assert result["remote_path"] == "/remote/test.txt"
        mock_service.transfer_file.assert_called_once_with(
            local_path="/local/test.txt", remote_path="/remote/test.txt", direction="upload"
        )
        mock_service.session_manager.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_transfer_file_failure(self, tools, mock_service):
        """Test file transfer failure."""
        mock_service.transfer_file.return_value = {"success": False, "error": "Transfer failed"}

        request = FileTransferRequest(
            local_path="/local/test.txt", remote_path="/remote/test.txt", direction="download"
        )

        result = await tools.transfer_file(request)

        assert result["success"] is False
        assert result["error"] == "Transfer failed"
        assert result["direction"] == "download"

    @pytest.mark.asyncio
    async def test_take_screenshot_success(self, tools, mock_service):
        """Test successful screenshot."""
        request = ScreenshotRequest(save_path="/tmp/test.png", session_id="session-123")

        result = await tools.take_screenshot(request)

        assert result["success"] is True
        assert result["file_path"] == "/tmp/test.png"
        mock_service.take_screenshot.assert_called_once_with("/tmp/test.png")
        mock_service.session_manager.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_take_screenshot_failure(self, tools, mock_service):
        """Test screenshot failure."""
        mock_service.take_screenshot.return_value = {"success": False, "error": "Screenshot failed"}

        request = ScreenshotRequest(save_path="/tmp/test.png")

        result = await tools.take_screenshot(request)

        assert result["success"] is False
        assert result["error"] == "Screenshot failed"

    @pytest.mark.asyncio
    async def test_start_recording_success(self, tools, mock_service):
        """Test successful recording start."""
        request = RecordingRequest(save_path="/tmp/test.mp4", session_id="session-123")

        result = await tools.start_recording(request)

        assert result["success"] is True
        assert result["recording_id"] == "test-recording"
        mock_service.start_screen_recording.assert_called_once_with("/tmp/test.mp4")
        mock_service.session_manager.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_recording_failure(self, tools, mock_service):
        """Test recording start failure."""
        mock_service.start_screen_recording.return_value = {"success": False, "error": "Recording failed"}

        request = RecordingRequest(save_path="/tmp/test.mp4")

        result = await tools.start_recording(request)

        assert result["success"] is False
        assert result["error"] == "Recording failed"

    @pytest.mark.asyncio
    async def test_stop_recording_success(self, tools, mock_service):
        """Test successful recording stop."""
        result = await tools.stop_recording("session-123")

        assert result["success"] is True
        mock_service.stop_screen_recording.assert_called_once()
        mock_service.session_manager.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_recording_failure(self, tools, mock_service):
        """Test recording stop failure."""
        mock_service.stop_screen_recording.return_value = {"success": False, "error": "Stop failed"}

        result = await tools.stop_recording()

        assert result["success"] is False
        assert result["error"] == "Stop failed"

    @pytest.mark.asyncio
    async def test_monitor_resources_success(self, tools, mock_service):
        """Test successful resource monitoring."""
        request = MonitoringRequest(duration_seconds=30, interval=5.0, session_id="session-123")

        result = await tools.monitor_resources(request)

        assert result["success"] is True
        assert result["summary"]["cpu"]["avg"] == 50.0
        mock_service.monitor_resource_usage.assert_called_once_with(duration_seconds=30, interval=5.0)
        mock_service.session_manager.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitor_resources_failure(self, tools, mock_service):
        """Test resource monitoring failure."""
        mock_service.monitor_resource_usage.return_value = {"success": False, "error": "Monitoring failed"}

        request = MonitoringRequest(duration_seconds=30, interval=5.0)

        result = await tools.monitor_resources(request)

        assert result["success"] is False
        assert result["error"] == "Monitoring failed"

    @pytest.mark.asyncio
    async def test_get_connection_quality_success(self, tools, mock_service):
        """Test successful connection quality check."""
        result = await tools.get_connection_quality("session-123")

        assert result["success"] is True
        assert result["connection_quality"]["latency_ms"] == 10
        mock_service.get_connection_quality.assert_called_once()
        mock_service.session_manager.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_connection_quality_failure(self, tools, mock_service):
        """Test connection quality check failure."""
        mock_service.get_connection_quality.return_value = {"success": False, "error": "Quality check failed"}

        result = await tools.get_connection_quality()

        assert result["success"] is False
        assert result["error"] == "Quality check failed"

    @pytest.mark.asyncio
    async def test_list_remote_files_success(self, tools, mock_service):
        """Test successful remote file listing."""
        mock_service.list_remote_files.return_value = {
            "success": True,
            "files": [{"name": "test.txt", "size": 1024}],
            "directory": "/remote",
            "count": 1,
        }

        result = await tools.list_remote_files("/remote", "session-123")

        assert result["success"] is True
        assert result["files"][0]["name"] == "test.txt"
        assert result["count"] == 1
        mock_service.list_remote_files.assert_called_once_with("/remote")
        mock_service.session_manager.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_remote_files_failure(self, tools, mock_service):
        """Test remote file listing failure."""
        mock_service.list_remote_files.return_value = {"success": False, "error": "List failed"}

        result = await tools.list_remote_files("/remote")

        assert result["success"] is False
        assert result["error"] == "List failed"
        assert result["directory"] == "/remote"
