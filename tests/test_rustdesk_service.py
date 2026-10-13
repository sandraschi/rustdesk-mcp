"""Tests for RustDeskService (aligned to the implemented fork-first contracts)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rustdesk_mcp.services.rustdesk_service import RustDeskService


class TestRustDeskService:
    """Test cases for RustDeskService."""

    @pytest.fixture
    def service(self, temp_dir, mock_config):
        """Create a test service instance."""
        return RustDeskService(mock_config.rustdesk_path, mock_config.rustdesk_config_dir)

    def test_initialization(self, service, mock_config):
        """Test service initialization."""
        assert service.rustdesk_path == mock_config.rustdesk_path
        assert service.config_dir == mock_config.rustdesk_config_dir
        assert service.active_recording is None

    @pytest.mark.asyncio
    async def test_is_running_no_process(self, service, mock_psutil):
        """Test is_running when no RustDesk process is found."""
        assert service.is_running() is False

    @pytest.mark.asyncio
    async def test_is_running_with_process(self, service, mock_psutil):
        """Test is_running when RustDesk process is found."""
        # Mock finding a rustdesk process
        mock_proc = MagicMock()
        mock_proc.info = {"name": "rustdesk"}
        mock_psutil.return_value = [mock_proc]

        assert service.is_running() is True

    @pytest.mark.asyncio
    async def test_get_status(self, service):
        """Test get_status method."""
        with (
            patch.object(service, "is_running", return_value=True),
            patch.object(service, "get_version", return_value="1.2.0"),
            patch.object(service, "get_config", return_value={"test": "config"}),
        ):
            status = await service.get_status()
            assert status["is_running"] is True
            assert status["version"] == "1.2.0"
            assert status["config"] == {"test": "config"}

    @pytest.mark.asyncio
    async def test_run_command_success(self, service):
        """Test successful command execution."""
        result = await service.run_command(["--version"])
        assert result["success"] is True
        assert "output" in result

    @pytest.mark.asyncio
    async def test_run_command_failure(self, service):
        """Test command execution failure."""
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Command failed")
            mock_process.returncode = 1
            mock_proc.return_value = mock_process

            result = await service.run_command(["invalid-command"])
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_run_command_timeout(self, service):
        """Test command execution timeout."""
        with (
            patch("asyncio.create_subprocess_exec") as mock_proc,
            patch("asyncio.wait_for", side_effect=TimeoutError()),
        ):
            mock_process = AsyncMock()
            mock_proc.return_value = mock_process

            result = await service.run_command(["--version"], timeout=1)
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_connect_success(self, service):
        """Test successful peer connection (API path)."""
        with patch.object(service, "_api_request", return_value={"success": True, "data": {}}) as mock_api:
            result = await service.connect("123456789", "password")

            assert result["success"] is True
            assert "session_id" in result
            mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, service):
        """Test failed peer connection (API path)."""
        with patch.object(
            service,
            "_api_request",
            return_value={"success": False, "error": "Connection failed"},
        ):
            result = await service.connect("123456789", "wrongpassword")

            assert result["success"] is False
            assert result["error"] == "Connection failed"

    @pytest.mark.asyncio
    async def test_disconnect_specific_session(self, service):
        """Test disconnecting a specific session."""
        session = await service.session_manager.create_session("123456789", "password")
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.disconnect(session["id"])

            assert result["success"] is True
            assert session["id"] in result["disconnected_sessions"]

    @pytest.mark.asyncio
    async def test_disconnect_all_sessions(self, service):
        """Test disconnecting all sessions."""
        s1 = await service.session_manager.create_session("111111111", "password")
        s2 = await service.session_manager.create_session("222222222", "password")
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.disconnect()

            assert result["success"] is True
            assert len(result["disconnected_sessions"]) == 2
            assert s1["id"] in result["disconnected_sessions"]
            assert s2["id"] in result["disconnected_sessions"]

    @pytest.mark.asyncio
    async def test_transfer_file_upload(self, service):
        """Test file upload via the fork CLI path."""
        result = await service.transfer_file("/local/file.txt", "/remote/file.txt", "upload", peer_id="123")

        assert result["success"] is True
        assert "upload" in result["message"]

    @pytest.mark.asyncio
    async def test_transfer_file_download(self, service):
        """Test file download via the fork CLI path."""
        result = await service.transfer_file("/local/file.txt", "/remote/file.txt", "download", peer_id="123")

        assert result["success"] is True
        assert "download" in result["message"]

    @pytest.mark.asyncio
    async def test_transfer_file_unavailable_without_peer(self, service):
        """Without peer_id/API the transfer falls through to not_implemented."""
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.transfer_file("/local/file.txt", "/remote/file.txt", "upload")

            assert result["success"] is False
            assert result["error_type"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_take_screenshot_with_path(self, service, temp_dir):
        """Test taking screenshot with custom path (CLI path)."""
        screenshot_path = temp_dir / "test_screenshot.png"

        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.take_screenshot(str(screenshot_path))

            assert result["success"] is True
            assert result["data"]["save_path"] == str(screenshot_path)

    @pytest.mark.asyncio
    async def test_take_screenshot_auto_path(self, service):
        """Test taking screenshot with auto-generated path (CLI path)."""
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.take_screenshot()

            assert result["success"] is True
            assert result["data"]["save_path"] == "(auto-named)"

    @pytest.mark.asyncio
    async def test_start_recording_success(self, service):
        """Recording via CLI is not_implemented by design (GUI-only)."""
        result = await service.start_screen_recording()

        assert result["success"] is False
        assert result["error_type"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_start_recording_already_active(self, service):
        """An existing active_recording does not change the not_implemented contract."""
        service.active_recording = {"recording_id": "existing"}

        result = await service.start_screen_recording()

        assert result["success"] is False
        assert result["error_type"] == "not_implemented"
        assert service.active_recording["recording_id"] == "existing"

    @pytest.mark.asyncio
    async def test_stop_recording_success(self, service):
        """Stopping via CLI is not_implemented by design (GUI-only)."""
        service.active_recording = {
            "recording_id": "test-recording",
            "file_path": "/tmp/recording.mp4",
            "is_recording": True,
        }

        result = await service.stop_screen_recording()

        assert result["success"] is False
        assert result["error_type"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_stop_recording_no_active(self, service):
        """Stopping with no recording is not_implemented (same CLI contract)."""
        result = await service.stop_screen_recording()

        assert result["success"] is False
        assert result["error_type"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_monitor_resource_usage(self, service):
        """Test resource usage monitoring (short window, mocked psutil)."""
        result = await service.monitor_resource_usage(duration_seconds=1, interval=0.5)

        assert result["success"] is True
        assert result["summary"]["measurement_count"] >= 1
        assert "cpu" in result["summary"]
        assert "memory" in result["summary"]

    @pytest.mark.asyncio
    async def test_get_connection_quality(self, service):
        """Test connection quality retrieval (psutil network counters)."""
        result = await service.get_connection_quality()

        assert result["success"] is True
        assert result["data"]["bytes_sent"] == 1000000
        assert result["data"]["bytes_recv"] == 2000000
        assert result["method"] == "psutil"

    @pytest.mark.asyncio
    async def test_list_remote_files_success(self, service):
        """Test listing remote files via fork --list-dir rows."""
        fork_output = "[FILE] test.txt 1024b\n[DIR] test_dir 0b"
        with patch.object(service, "run_command", return_value={"success": True, "output": fork_output}):
            result = await service.list_remote_files("/remote/path", peer_id="123")

            assert result["success"] is True
            assert result["method"] == "fork-cli"
            assert result["data"]["files"] == ["[FILE] test.txt 1024b", "[DIR] test_dir 0b"]

    @pytest.mark.asyncio
    async def test_list_remote_files_parse_error(self, service):
        """Empty fork output yields success with an empty file list."""
        with patch.object(service, "run_command", return_value={"success": True, "output": ""}):
            result = await service.list_remote_files("/remote/path", peer_id="123")

            assert result["success"] is True
            assert result["data"]["files"] == []

    @pytest.mark.asyncio
    async def test_list_remote_files_needs_peer_or_api(self, service):
        """Without peer_id/API the listing falls through to not_implemented."""
        result = await service.list_remote_files("/remote/path")

        assert result["success"] is False
        assert result["error_type"] == "not_implemented"
