"""Tests for RustDeskService."""

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
            patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()),
        ):
            mock_process = AsyncMock()
            mock_proc.return_value = mock_process

            result = await service.run_command(["--version"], timeout=1)
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_connect_success(self, service):
        """Test successful peer connection."""
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.connect("123456789", "password")

            assert result["success"] is True
            assert "session_id" in result

    @pytest.mark.asyncio
    async def test_connect_failure(self, service):
        """Test failed peer connection."""
        with patch.object(service, "run_command", return_value={"success": False, "error": "Connection failed"}):
            result = await service.connect("123456789", "wrongpassword")

            assert result["success"] is False
            assert result["error"] == "Connection failed"

    @pytest.mark.asyncio
    async def test_disconnect_specific_session(self, service):
        """Test disconnecting a specific session."""
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.disconnect("session-123")

            assert result["success"] is True
            assert "session-123" in result["disconnected_sessions"]

    @pytest.mark.asyncio
    async def test_disconnect_all_sessions(self, service):
        """Test disconnecting all sessions."""
        with (
            patch.object(
                service.session_manager, "list_active_sessions", return_value=[{"id": "session-1"}, {"id": "session-2"}]
            ),
            patch.object(service, "run_command", return_value={"success": True}),
        ):
            result = await service.disconnect()

            assert result["success"] is True
            assert len(result["disconnected_sessions"]) == 2

    @pytest.mark.asyncio
    async def test_transfer_file_upload(self, service):
        """Test file upload."""
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.transfer_file("/local/file.txt", "/remote/file.txt", "upload")

            assert result["success"] is True
            assert result["direction"] == "upload"
            assert result["local_path"] == "/local/file.txt"
            assert result["remote_path"] == "/remote/file.txt"

    @pytest.mark.asyncio
    async def test_transfer_file_download(self, service):
        """Test file download."""
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.transfer_file("/local/file.txt", "/remote/file.txt", "download")

            assert result["success"] is True
            assert result["direction"] == "download"

    @pytest.mark.asyncio
    async def test_take_screenshot_with_path(self, service, temp_dir):
        """Test taking screenshot with custom path."""
        screenshot_path = temp_dir / "test_screenshot.png"

        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.take_screenshot(str(screenshot_path))

            assert result["success"] is True
            assert result["file_path"] == str(screenshot_path)
            assert result["type"] == "screenshot"

    @pytest.mark.asyncio
    async def test_take_screenshot_auto_path(self, service):
        """Test taking screenshot with auto-generated path."""
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.take_screenshot()

            assert result["success"] is True
            assert "screenshots/screenshot_" in result["file_path"]
            assert result["file_path"].endswith(".png")

    @pytest.mark.asyncio
    async def test_start_recording_success(self, service):
        """Test starting screen recording successfully."""
        with patch.object(service, "run_command", return_value={"success": True}):
            result = await service.start_screen_recording()

            assert result["success"] is True
            assert "recording_id" in result
            assert "started_at" in result
            assert service.active_recording is not None

    @pytest.mark.asyncio
    async def test_start_recording_already_active(self, service):
        """Test starting recording when one is already active."""
        service.active_recording = {"recording_id": "existing"}

        with (
            patch.object(service, "stop_screen_recording", return_value={"success": True}),
            patch.object(service, "run_command", return_value={"success": True}),
        ):
            result = await service.start_screen_recording()

            assert result["success"] is True
            assert service.active_recording["recording_id"] != "existing"

    @pytest.mark.asyncio
    async def test_stop_recording_success(self, service):
        """Test stopping screen recording successfully."""
        from datetime import datetime

        start_time = datetime.utcnow().isoformat()
        service.active_recording = {
            "recording_id": "test-recording",
            "file_path": "/tmp/recording.mp4",
            "start_time": start_time,
            "is_recording": True,
        }

        with (
            patch("os.path.getsize", return_value=1024000),
            patch.object(service, "run_command", return_value={"success": True}),
        ):
            result = await service.stop_screen_recording()

            assert result["success"] is True
            assert result["recording_id"] == "test-recording"
            assert "duration_seconds" in result
            assert result["file_size"] == 1024000
            assert service.active_recording is None

    @pytest.mark.asyncio
    async def test_stop_recording_no_active(self, service):
        """Test stopping recording when none is active."""
        result = await service.stop_recording()

        assert result["success"] is False
        assert "No active recording" in result["error"]

    @pytest.mark.asyncio
    async def test_monitor_resource_usage(self, service):
        """Test resource usage monitoring."""
        with patch.object(service, "get_performance_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu": {"percent": 50.0},
                "memory": {"percent": 60.0},
                "disk": {"percent": 40.0},
                "network": {"bytes_sent": 1000, "bytes_recv": 2000},
            }

            result = await service.monitor_resource_usage(duration_seconds=5, interval=1.0)

            assert result["success"] is True
            assert result["measurement_count"] >= 1
            assert "summary" in result
            assert "cpu" in result["summary"]
            assert "memory" in result["summary"]

    @pytest.mark.asyncio
    async def test_get_connection_quality(self, service):
        """Test connection quality retrieval."""
        with patch.object(service, "run_command", return_value={"success": True, "output": {}}):
            result = await service.get_connection_quality()

            assert result["success"] is True
            assert "connection_quality" in result
            assert "measured_at" in result

    @pytest.mark.asyncio
    async def test_list_remote_files_success(self, service):
        """Test listing remote files successfully."""
        mock_output = (
            "drwxr-xr-x 2 user group 4096 Jan 1 12:00 test_dir\n-rw-r--r-- 1 user group 1024 Jan 1 12:00 test.txt"
        )

        with patch.object(service, "run_command", return_value={"success": True, "output": mock_output}):
            result = await service.list_remote_files("/remote/path")

            assert result["success"] is True
            assert result["directory"] == "/remote/path"
            assert "files" in result
            assert len(result["files"]) == 2
            assert result["files"][0]["name"] == "test_dir"
            assert result["files"][1]["name"] == "test.txt"

    @pytest.mark.asyncio
    async def test_list_remote_files_parse_error(self, service):
        """Test listing remote files with parsing errors."""
        mock_output = "Invalid format line"

        with patch.object(service, "run_command", return_value={"success": True, "output": mock_output}):
            result = await service.list_remote_files("/remote/path")

            assert result["success"] is True
            assert result["directory"] == "/remote/path"
            assert result["files"] == []
            assert result["count"] == 0
