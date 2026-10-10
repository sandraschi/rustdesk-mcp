"""Tests for remote input control (click / type / keys)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rustdesk_mcp.services.advanced_control import AdvancedControlService


@pytest.fixture
def service():
    svc = AdvancedControlService(control_enabled=True)
    svc.last_action_time = 0
    svc.min_action_interval = 0
    return svc


def _mock_window():
    window = MagicMock()
    window.box = MagicMock(left=0, top=0, right=1920, bottom=1080)
    window.activate = MagicMock()
    return window


class TestChordParsing:
    """Pure-function chord conversion tests (no window needed)."""

    def test_ctrl_c(self):
        assert AdvancedControlService.chord_to_pywinauto("ctrl+c") == "^c"

    def test_alt_f4(self):
        assert AdvancedControlService.chord_to_pywinauto("alt+F4") == "%{F4}"

    def test_super_d(self):
        assert AdvancedControlService.chord_to_pywinauto("super+d") == "#d"

    def test_ctrl_shift_s(self):
        assert AdvancedControlService.chord_to_pywinauto("ctrl+shift+s") == "^+s"

    def test_bad_modifier(self):
        with pytest.raises(ValueError, match="Unknown modifier"):
            AdvancedControlService.chord_to_pywinauto("hyper+x")

    def test_empty(self):
        with pytest.raises(ValueError, match="Empty"):
            AdvancedControlService.chord_to_pywinauto("  +  ")


class TestRemoteClick:
    """Click validation and dispatch."""

    @pytest.mark.asyncio
    async def test_bad_button_rejected(self, service):
        result = await service.remote_click(100, 100, button="sideways")
        assert result["success"] is False
        assert "Unknown button" in result["error"]

    @pytest.mark.asyncio
    async def test_out_of_bounds_rejected(self, service):
        service.find_rustdesk_window = MagicMock(return_value=_mock_window())
        result = await service.remote_click(9999, 9999)
        assert result["success"] is False
        assert "outside" in result["error"]

    @pytest.mark.asyncio
    async def test_single_click(self, service):
        service.find_rustdesk_window = MagicMock(return_value=_mock_window())
        with patch("rustdesk_mcp.services.advanced_control.mouse") as mock_mouse:
            result = await service.remote_click(100, 200, button="left")
        assert result["success"] is True
        mock_mouse.click.assert_called_once_with(button="left", coords=(100, 200))

    @pytest.mark.asyncio
    async def test_double_click(self, service):
        service.find_rustdesk_window = MagicMock(return_value=_mock_window())
        with patch("rustdesk_mcp.services.advanced_control.mouse") as mock_mouse:
            result = await service.remote_click(100, 200, double=True)
        assert result["success"] is True
        assert "Double" in result["message"]
        mock_mouse.double_click.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_window(self, service):
        service.find_rustdesk_window = MagicMock(return_value=None)
        result = await service.remote_click(100, 100)
        assert result["success"] is False


class TestSendRemoteKeys:
    """Key-chord validation and dispatch."""

    @pytest.mark.asyncio
    async def test_too_long_rejected(self, service):
        result = await service.send_remote_keys("a" * 65)
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_bad_modifier_rejected(self, service):
        result = await service.send_remote_keys("hyper+x")
        assert result["success"] is False
        assert "Unknown modifier" in result["error"]

    @pytest.mark.asyncio
    async def test_no_window(self, service):
        service.find_rustdesk_window = MagicMock(return_value=None)
        result = await service.send_remote_keys("ctrl+c")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_success(self, service):
        service.find_rustdesk_window = MagicMock(return_value=_mock_window())
        with patch("rustdesk_mcp.services.advanced_control.keyboard") as mock_kb:
            result = await service.send_remote_keys("ctrl+c")
        assert result["success"] is True
        mock_kb.send_keys.assert_called_once_with("^c")

    @pytest.mark.asyncio
    async def test_disabled_by_policy(self):
        svc = AdvancedControlService(control_enabled=False)
        result = await svc.send_remote_keys("ctrl+c")
        assert result["success"] is False
        assert "disabled" in result["error"]
