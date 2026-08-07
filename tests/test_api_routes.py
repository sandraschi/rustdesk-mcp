"""Tests for API routes."""


class TestAPIRoutes:
    """Test cases for API routes."""

    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_get_status_success(self, test_client, mock_rustdesk_service):
        """Test getting RustDesk status successfully."""
        mock_rustdesk_service.get_status.return_value = {
            "is_running": True,
            "version": "1.2.0",
            "config": {"test": "config"},
        }

        response = test_client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is True
        assert data["version"] == "1.2.0"
        assert data["config"] == {"test": "config"}

    def test_get_status_failure(self, test_client, mock_rustdesk_service):
        """Test getting RustDesk status failure."""
        mock_rustdesk_service.get_status.side_effect = Exception("Service error")

        response = test_client.get("/api/v1/status")

        assert response.status_code == 500
        assert "error" in response.json()

    def test_connect_to_peer_success(self, test_client, mock_rustdesk_service, mock_rustdesk_tools):
        """Test successful peer connection via API."""
        mock_rustdesk_tools.connect_to_peer.return_value = {
            "success": True,
            "session_id": "test-session",
            "message": "Connected successfully",
        }

        request_data = {"peer_id": "123456789", "password": "testpass", "save_password": False}

        response = test_client.post("/api/v1/connect", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == "test-session"
        mock_rustdesk_tools.connect_to_peer.assert_called_once()

    def test_connect_to_peer_validation_error(self, test_client):
        """Test peer connection with invalid data."""
        request_data = {
            "peer_id": "",  # Invalid empty peer_id
            "password": "testpass",
        }

        response = test_client.post("/api/v1/connect", json=request_data)

        assert response.status_code == 422  # Validation error
        assert "detail" in response.json()

    def test_disconnect_peer_success(self, test_client, mock_rustdesk_tools):
        """Test successful peer disconnection via API."""
        mock_rustdesk_tools.disconnect_peer.return_value = {
            "success": True,
            "disconnected_sessions": ["session-123"],
            "message": "Disconnected successfully",
        }

        response = test_client.post("/api/v1/disconnect")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session-123" in data["disconnected_sessions"]

    def test_transfer_file_success(self, test_client, mock_rustdesk_tools):
        """Test successful file transfer via API."""
        mock_rustdesk_tools.transfer_file.return_value = {
            "success": True,
            "direction": "upload",
            "local_path": "/local/test.txt",
            "remote_path": "/remote/test.txt",
        }

        request_data = {"local_path": "/local/test.txt", "remote_path": "/remote/test.txt", "direction": "upload"}

        response = test_client.post("/api/v1/transfer", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["direction"] == "upload"

    def test_take_screenshot_success(self, test_client, mock_rustdesk_tools):
        """Test successful screenshot via API."""
        mock_rustdesk_tools.take_screenshot.return_value = {
            "success": True,
            "file_path": "/tmp/screenshot.png",
            "file_size": 1024000,
            "created_at": "2025-01-01T12:00:00Z",
        }

        request_data = {"save_path": "/tmp/screenshot.png"}

        response = test_client.post("/api/v1/screenshot", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_path"] == "/tmp/screenshot.png"

    def test_start_recording_success(self, test_client, mock_rustdesk_tools):
        """Test successful recording start via API."""
        mock_rustdesk_tools.start_recording.return_value = {
            "success": True,
            "recording_id": "test-recording",
            "file_path": "/tmp/recording.mp4",
            "started_at": "2025-01-01T12:00:00Z",
        }

        request_data = {"save_path": "/tmp/recording.mp4"}

        response = test_client.post("/api/v1/recording/start", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["recording_id"] == "test-recording"

    def test_stop_recording_success(self, test_client, mock_rustdesk_tools):
        """Test successful recording stop via API."""
        mock_rustdesk_tools.stop_recording.return_value = {
            "success": True,
            "recording_id": "test-recording",
            "duration_seconds": 30.5,
            "file_path": "/tmp/recording.mp4",
            "file_size": 2048000,
        }

        response = test_client.post("/api/v1/recording/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["duration_seconds"] == 30.5

    def test_monitor_resources_success(self, test_client, mock_rustdesk_tools):
        """Test successful resource monitoring via API."""
        mock_rustdesk_tools.monitor_resources.return_value = {
            "success": True,
            "start_time": 1640995200.0,
            "end_time": 1640995230.0,
            "summary": {
                "cpu": {"avg": 45.2, "max": 67.8, "min": 12.3},
                "memory": {"avg": 60.1, "max": 75.2, "min": 45.6},
            },
            "measurements": [],
        }

        request_data = {"duration_seconds": 30, "interval": 5.0}

        response = test_client.post("/api/v1/monitor", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "summary" in data
        assert data["summary"]["cpu"]["avg"] == 45.2

    def test_get_connection_quality_success(self, test_client, mock_rustdesk_tools):
        """Test successful connection quality check via API."""
        mock_rustdesk_tools.get_connection_quality.return_value = {
            "success": True,
            "connection_quality": {
                "latency_ms": 15,
                "bandwidth_mbps": 50.5,
                "packet_loss_percent": 0.1,
                "frame_rate": 30,
                "resolution": "1920x1080",
                "color_depth": 32,
            },
            "measured_at": "2025-01-01T12:00:00Z",
        }

        response = test_client.get("/api/v1/connection-quality")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["connection_quality"]["latency_ms"] == 15

    def test_list_remote_files_success(self, test_client, mock_rustdesk_tools):
        """Test successful remote file listing via API."""
        mock_rustdesk_tools.list_remote_files.return_value = {
            "success": True,
            "directory": "/remote",
            "files": [
                {
                    "permissions": "-rw-r--r--",
                    "links": 1,
                    "owner": "user",
                    "group": "group",
                    "size": 1024,
                    "date": "Jan 1 12:00",
                    "name": "test.txt",
                    "path": "/remote/test.txt",
                }
            ],
            "count": 1,
        }

        response = test_client.get("/api/v1/files?remote_path=/remote")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
        assert data["files"][0]["name"] == "test.txt"

    # Error handling tests
    def test_method_not_allowed(self, test_client):
        """Test method not allowed for endpoints."""
        response = test_client.put("/api/v1/status")
        assert response.status_code == 405

    def test_invalid_json(self, test_client):
        """Test invalid JSON handling."""
        response = test_client.post(
            "/api/v1/connect", data="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, test_client):
        """Test missing required fields in request."""
        request_data = {
            "password": "testpass"
            # Missing peer_id
        }

        response = test_client.post("/api/v1/connect", json=request_data)
        assert response.status_code == 422
        assert "peer_id" in str(response.json())

    def test_service_unavailable(self, test_client):
        """Test service unavailable scenarios."""
        # Mock service not initialized
        import rustdesk_mcp.server

        original_service = getattr(rustdesk_mcp.server, "rustdesk_service", None)
        rustdesk_mcp.server.rustdesk_service = None

        try:
            response = test_client.get("/api/v1/status")
            assert response.status_code == 500
        finally:
            rustdesk_mcp.server.rustdesk_service = original_service
