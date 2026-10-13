"""Tests for API routes (aligned to the implemented /api/v1 surface)."""

from unittest.mock import AsyncMock

from rustdesk_mcp.api.v1.routes import get_rustdesk_service
from rustdesk_mcp.server import app


def _override(service):
    """Route all service dependencies to the given mock (cleared by caller)."""
    app.dependency_overrides[get_rustdesk_service] = lambda: service


def _clear():
    app.dependency_overrides.clear()


class TestAPIRoutes:
    """Test cases for API routes."""

    def test_health_check(self, test_client):
        """Test the fleet health check endpoint (served by the probe middleware)."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "mock_mode" in data

    def test_health_v1(self, test_client):
        """Test the versioned health endpoint."""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_get_status_success(self, test_client, mock_rustdesk_service):
        """Test getting RustDesk status successfully."""
        mock_rustdesk_service.get_status = AsyncMock(
            return_value={"is_running": True, "version": "1.2.0", "config": {"test": "config"}}
        )
        _override(mock_rustdesk_service)
        try:
            response = test_client.get("/api/v1/status")
        finally:
            _clear()

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.2.0"
        assert data["rustdesk_running"] is True

    def test_get_status_failure(self, test_client, mock_rustdesk_service):
        """Test getting RustDesk status failure."""
        mock_rustdesk_service.get_status = AsyncMock(side_effect=Exception("Service error"))
        _override(mock_rustdesk_service)
        try:
            response = test_client.get("/api/v1/status")
        finally:
            _clear()

        assert response.status_code == 500
        assert "Error getting service status" in response.json()["detail"]

    def test_get_info_success(self, test_client, mock_rustdesk_service):
        """Test getting service info successfully."""
        mock_rustdesk_service.get_status = AsyncMock(
            return_value={"is_running": True, "version": "1.2.0", "config": {"test": "config"}}
        )
        _override(mock_rustdesk_service)
        try:
            response = test_client.get("/api/v1/info")
        finally:
            _clear()

        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is True
        assert data["version"] == "1.2.0"
        assert data["config"] == {"test": "config"}

    def test_connect_to_peer_success(self, test_client, mock_rustdesk_service):
        """Test successful peer connection via API."""
        mock_rustdesk_service.connect = AsyncMock(return_value={"success": True, "session_id": "test-session"})
        mock_rustdesk_service.update_config = AsyncMock(return_value={})
        _override(mock_rustdesk_service)
        try:
            response = test_client.post(
                "/api/v1/connect",
                json={"peer_id": "123456789", "password": "testpass", "save_password": False},
            )
        finally:
            _clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session_id"] == "test-session"

    def test_connect_to_peer_validation_error(self, test_client):
        """Test peer connection with invalid data (missing peer_id)."""
        response = test_client.post("/api/v1/connect", json={"password": "testpass"})

        assert response.status_code == 422  # Validation error

    def test_disconnect_peer_success(self, test_client, mock_rustdesk_service):
        """Test successful peer disconnection via API."""
        mock_rustdesk_service.disconnect = AsyncMock(
            return_value={"success": True, "disconnected_sessions": ["session-123"]}
        )
        _override(mock_rustdesk_service)
        try:
            response = test_client.post("/api/v1/disconnect")
        finally:
            _clear()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["disconnected_sessions"] == ["session-123"]

    def test_disconnect_failure(self, test_client, mock_rustdesk_service):
        """Test disconnection failure surfaces a 500."""
        mock_rustdesk_service.disconnect = AsyncMock(side_effect=Exception("hangup failed"))
        _override(mock_rustdesk_service)
        try:
            response = test_client.post("/api/v1/disconnect")
        finally:
            _clear()

        assert response.status_code == 500

    def test_get_performance_success(self, test_client, mock_rustdesk_service):
        """Test performance metrics via API."""
        mock_rustdesk_service.get_performance_metrics = AsyncMock(
            return_value={
                "cpu": {"percent": 45.2},
                "memory": {"percent": 60.1},
                "disk": {"percent": 40.0},
                "network": {"bytes_sent": 1000, "bytes_recv": 2000},
            }
        )
        _override(mock_rustdesk_service)
        try:
            response = test_client.get("/api/v1/performance")
        finally:
            _clear()

        assert response.status_code == 200
        assert response.json()["cpu"]["percent"] == 45.2

    def test_get_connection_info_success(self, test_client, mock_rustdesk_service):
        """Test connection info via API."""
        mock_rustdesk_service.get_connection_info = AsyncMock(return_value={"peer_id": "123456789", "connected": False})
        _override(mock_rustdesk_service)
        try:
            response = test_client.get("/api/v1/connection")
        finally:
            _clear()

        assert response.status_code == 200
        data = response.json()
        assert data["peer_id"] == "123456789"
        assert data["connected"] is False

    def test_update_config_success(self, test_client, mock_rustdesk_service):
        """Test config update via API."""
        mock_rustdesk_service.update_config = AsyncMock(return_value={"theme": "dark"})
        _override(mock_rustdesk_service)
        try:
            response = test_client.post("/api/v1/config", json={"updates": {"theme": "dark"}})
        finally:
            _clear()

        assert response.status_code == 200
        assert response.json()["success"] is True

    # Error handling tests
    def test_method_not_allowed(self, test_client):
        """Test method not allowed for endpoints."""
        response = test_client.put("/api/v1/status")
        assert response.status_code == 405

    def test_invalid_json(self, test_client):
        """Test invalid JSON handling (malformed body is a 422 on this stack)."""
        response = test_client.post(
            "/api/v1/connect", content="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, test_client):
        """Test missing required fields in request."""
        response = test_client.post("/api/v1/connect", json={"password": "testpass"})

        assert response.status_code == 422

    def test_service_unavailable(self, test_client, mock_rustdesk_service):
        """Test service failure scenarios surface a 500."""
        mock_rustdesk_service.get_status = AsyncMock(side_effect=Exception("down"))
        _override(mock_rustdesk_service)
        try:
            response = test_client.get("/api/v1/status")
        finally:
            _clear()

        assert response.status_code == 500
