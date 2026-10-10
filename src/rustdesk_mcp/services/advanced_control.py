"""
Advanced Control Service for RustDesk window automation.
Handles safe input simulation and window management with security guards.
"""

import logging
import os
import time
from typing import Any

import pywinctl as pwc
from pywinauto import keyboard, mouse

logger = logging.getLogger(__name__)


class AdvancedControlService:
    """Service for safe remote control of RustDesk windows."""

    def __init__(self, control_enabled: bool = True):
        self.control_enabled = control_enabled and os.getenv("RUSTDESK_CONTROL_ENABLED", "true").lower() == "true"
        self.last_action_time = 0
        self.min_action_interval = 0.5  # 500ms between actions
        self.audit_log_path = "rustdesk_control.log"

    def _log_audit(self, action: str, details: Any, success: bool):
        """Log remote control actions for auditing."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "FAILED"
        log_entry = f"[{timestamp}] {status} | Action: {action} | Details: {details}\n"
        try:
            with open(self.audit_log_path, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write to audit log: {e}")

    def _check_safety(self) -> tuple[bool, str]:
        """Verify if remote control is enabled and rate-limiting is respected."""
        if not self.control_enabled:
            return False, "Remote control is disabled by policy."

        current_time = time.time()
        if current_time - self.last_action_time < self.min_action_interval:
            return False, "Rate limit exceeded. Please wait between actions."

        return True, ""

    def find_rustdesk_window(self) -> pwc.Window | None:
        """Find the active RustDesk remote session window."""
        windows = pwc.getWindowsWithTitle("RustDesk", condition=pwc.Re.CONTAINS)
        # Filter for windows that look like remote sessions (usually have the ID in title)
        remote_windows = [w for w in windows if "-" in w.title]
        return remote_windows[0] if remote_windows else None

    def validate_bounds(self, window: pwc.Window, x: int, y: int) -> bool:
        """Check if coordinates (x, y) are within the window bounds."""
        rect = window.box
        return rect.left <= x <= rect.right and rect.top <= y <= rect.bottom

    async def remote_click(
        self, x: int, y: int, button: str = "left", double: bool = False
    ) -> dict[str, Any]:
        """Perform a safe mouse click in the RustDesk window."""
        button = button.lower()
        if button not in ("left", "right", "middle"):
            self._log_audit("click", {"x": x, "y": y, "button": button, "error": "bad button"}, False)
            return {"success": False, "error": f"Unknown button '{button}'. Use left, right, or middle."}
        safe, message = self._check_safety()
        if not safe:
            self._log_audit("click", {"x": x, "y": y, "error": message}, False)
            return {"success": False, "error": message}

        window = self.find_rustdesk_window()
        if not window:
            self._log_audit("click", {"x": x, "y": y, "error": "No RustDesk window found"}, False)
            return {
                "success": False,
                "error": "No active RustDesk remote window found.",
            }

        # Convert relative to absolute if needed, or validate absolute
        # For now, we assume absolute coordinates provided by the user/AI
        if not self.validate_bounds(window, x, y):
            self._log_audit("click", {"x": x, "y": y, "error": "Out of bounds"}, False)
            return {
                "success": False,
                "error": f"Coordinates ({x}, {y}) are outside the RustDesk window.",
            }

        try:
            window.activate()
            if double:
                mouse.double_click(button=button, coords=(x, y))
            else:
                mouse.click(button=button, coords=(x, y))
            self.last_action_time = time.time()
            self._log_audit("click", {"x": x, "y": y, "button": button, "double": double}, True)
            kind = "Double-clicked" if double else "Clicked"
            return {"success": True, "message": f"{kind} at ({x}, {y}) with {button} button"}
        except Exception as e:
            self._log_audit("click", {"x": x, "y": y, "error": str(e)}, False)
            return {"success": False, "error": str(e)}

    async def remote_type(self, text: str) -> dict[str, Any]:
        """Perform safe keyboard input in the RustDesk window."""
        safe, message = self._check_safety()
        if not safe:
            self._log_audit("type", {"textLength": len(text), "error": message}, False)
            return {"success": False, "error": message}

        window = self.find_rustdesk_window()
        if not window:
            self._log_audit(
                "type",
                {"textLength": len(text), "error": "No RustDesk window found"},
                False,
            )
            return {
                "success": False,
                "error": "No active RustDesk remote window found.",
            }

        try:
            window.activate()
            # Safety: Limit text length
            if len(text) > 1000:
                return {"success": False, "error": "Text too long for safe typing."}

            keyboard.send_keys(text)
            self.last_action_time = time.time()
            self._log_audit("type", {"textLength": len(text)}, True)
            return {"success": True, "message": f"Typed {len(text)} characters."}
        except Exception as e:
            self._log_audit("type", {"textLength": len(text), "error": str(e)}, False)
            return {"success": False, "error": str(e)}

    @staticmethod
    def chord_to_pywinauto(keys: str) -> str:
        """Convert a '+'-joined chord like 'ctrl+shift+s' to pywinauto send_keys syntax."""
        mods = {"ctrl": "^", "alt": "%", "shift": "+", "super": "#", "win": "#", "meta": "#"}
        parts = [p.strip() for p in keys.split("+") if p.strip()]
        if not parts:
            raise ValueError("Empty key chord")
        *mod_parts, final = parts
        prefix = ""
        for m in mod_parts:
            key = m.lower()
            if key not in mods:
                raise ValueError(f"Unknown modifier '{m}'. Use ctrl, alt, shift, super/win.")
            prefix += mods[key]
        if len(final) == 1:
            return f"{prefix}{final}"
        return f"{prefix}{{{final.upper()}}}"

    async def send_remote_keys(self, keys: str) -> dict[str, Any]:
        """Send a key chord (e.g. 'ctrl+c', 'alt+F4') to the RustDesk window."""
        safe, message = self._check_safety()
        if not safe:
            self._log_audit("keys", {"keys": keys, "error": message}, False)
            return {"success": False, "error": message}

        if len(keys) > 64:
            return {"success": False, "error": "Key chord too long."}

        try:
            combo = self.chord_to_pywinauto(keys)
        except ValueError as e:
            self._log_audit("keys", {"keys": keys, "error": str(e)}, False)
            return {"success": False, "error": str(e)}

        window = self.find_rustdesk_window()
        if not window:
            self._log_audit("keys", {"keys": keys, "error": "No RustDesk window found"}, False)
            return {"success": False, "error": "No active RustDesk remote window found."}

        try:
            window.activate()
            keyboard.send_keys(combo)
            self.last_action_time = time.time()
            self._log_audit("keys", {"keys": keys, "combo": combo}, True)
            return {"success": True, "message": f"Sent keys '{keys}'"}
        except Exception as e:
            self._log_audit("keys", {"keys": keys, "error": str(e)}, False)
            return {"success": False, "error": str(e)}
