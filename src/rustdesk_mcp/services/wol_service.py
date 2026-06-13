"""Wake-on-LAN service for sending magic packets."""

import asyncio
import logging

logger = logging.getLogger(__name__)


class WolService:
    """Send Wake-on-LAN magic packets to wake sleeping machines."""

    def __init__(self):
        self._wakeonlan_available = False
        self._detected()

    def _detected(self):
        try:
            import wakeonlan  # noqa: F401
            self._wakeonlan_available = True
        except ImportError:
            self._wakeonlan_available = False

    @property
    def available(self) -> bool:
        return self._wakeonlan_available

    async def send_magic_packet(
        self,
        mac_address: str,
        broadcast_ip: str = "255.255.255.255",
        port: int = 9,
    ) -> dict:
        """Send a WOL magic packet to the given MAC address."""
        if not self._wakeonlan_available:
            return {
                "success": False,
                "message": "wakeonlan package not installed (pip install wakeonlan)",
            }

        try:
            from wakeonlan import send_magic_packet

            loop = asyncio.get_event_loop()

            def _send():
                send_magic_packet(mac_address, ip_address=broadcast_ip, port=port)

            await loop.run_in_executor(None, _send)

            return {
                "success": True,
                "message": f"Magic packet sent to {mac_address} on {broadcast_ip}:{port}",
                "mac_address": mac_address,
                "broadcast_ip": broadcast_ip,
                "port": port,
            }
        except Exception as e:
            logger.exception(f"Failed to send WOL packet: {e}")
            return {
                "success": False,
                "message": f"Failed to send WOL packet: {e}",
                "mac_address": mac_address,
            }
