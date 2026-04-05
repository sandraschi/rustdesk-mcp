"""
Service layer for RustDesk operations.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

import aiohttp
import psutil
from pydantic import BaseModel, Field

from .session_manager import SessionManager
from .rustdesk_socket import RustDeskSocketClient

logger = logging.getLogger(__name__)


class RustDeskService:
    """Service for interacting with RustDesk via API."""

    def __init__(
        self,
        rustdesk_path: Optional[Path],
        config_dir: Optional[Path],
        id_server_host: str = "127.0.0.1",
        id_server_port: int = 21116,
        relay_server_host: str = "127.0.0.1",
        relay_server_port: int = 21117,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_username: Optional[str] = None,
        api_password: Optional[str] = None,
    ):
        """Initialize the RustDesk service.

        Args:
            rustdesk_path: Path to the RustDesk executable (optional for development)
            config_dir: Path to the RustDesk config directory (optional for development)
            api_url: URL of the RustDesk API server (e.g., http://localhost:21114)
            api_key: API key for authentication (optional, will use login if not provided)
            api_username: Username for API login (default: admin)
            api_password: Password for API login (default: from logs)
        """
        self.rustdesk_path = rustdesk_path
        self.config_dir = config_dir

        # Socket client configuration (primary interface)
        self.id_server_host = id_server_host
        self.id_server_port = id_server_port
        self.relay_server_host = relay_server_host
        self.relay_server_port = relay_server_port

        # API configuration (optional fallback)
        self.api_url = api_url or os.getenv("RUSTDESK_API_URL")
        self.api_key = api_key or os.getenv("RUSTDESK_API_KEY")
        self.api_username = api_username or os.getenv("RUSTDESK_API_USERNAME", "admin")
        self.api_password = api_password or os.getenv(
            "RUSTDESK_API_PASSWORD", "vAw7I4V9"
        )

        self.session_manager = SessionManager()
        self.active_recording: Optional[Dict[str, Any]] = None
        self.mock_mode = (
            rustdesk_path is None and api_url is None and id_server_host == "127.0.0.1"
        )
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.jwt_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Initialize socket client for direct RustDesk server communication
        self.socket_client = RustDeskSocketClient(
            id_server_host=id_server_host,
            id_server_port=id_server_port,
            relay_server_host=relay_server_host,
            relay_server_port=relay_server_port,
        )

        if self.mock_mode:
            logger.warning("RustDesk API not configured - running in mock mode")
        else:
            logger.info("RustDesk service initialized with API URL: %s", self.api_url)

    async def _ensure_http_session(self):
        """Ensure we have an active HTTP session."""
        if self.http_session is None or self.http_session.closed:
            # Start with basic headers, auth will be added per request
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        requires_auth: bool = True,
    ) -> Dict[str, Any]:
        """Make an API request to the RustDesk API server."""
        if self.mock_mode:
            return {"success": True, "mock": True, "endpoint": endpoint, "data": data}

        # Ensure we have authentication for protected endpoints
        if requires_auth and not await self._ensure_authenticated():
            return {"success": False, "error": "Authentication failed", "status": 401}

        await self._ensure_http_session()

        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}

        # Add JWT token if we have one and auth is required
        if requires_auth and self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        try:
            if method.upper() == "GET":
                async with self.http_session.get(url, headers=headers) as response:
                    if response.status == 404:
                        return {
                            "success": False,
                            "error": "Endpoint not found",
                            "status": 404,
                        }
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "data": result,
                        "status": response.status,
                    }
            elif method.upper() == "POST":
                async with self.http_session.post(
                    url, json=data, headers=headers
                ) as response:
                    if response.status == 404:
                        return {
                            "success": False,
                            "error": "Endpoint not found",
                            "status": 404,
                        }
                    result = await response.json()
                    return {
                        "success": response.status in [200, 201],
                        "data": result,
                        "status": response.status,
                    }
            elif method.upper() == "DELETE":
                async with self.http_session.delete(url, headers=headers) as response:
                    if response.status == 404:
                        return {
                            "success": False,
                            "error": "Endpoint not found",
                            "status": 404,
                        }
                    result = await response.json() if response.content_length else {}
                    return {
                        "success": response.status == 200,
                        "data": result,
                        "status": response.status,
                    }
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
        except Exception as e:
            logger.exception(f"API request failed: {method} {url}")
            return {"success": False, "error": str(e)}

    async def _login(self) -> bool:
        """Login to the API server and get JWT token."""
        if self.mock_mode:
            return True

        await self._ensure_http_session()

        login_data = {
            "username": self.api_username,
            "password": self.api_password,
            "autoLogin": False,
            "deviceInfo": {
                "name": "RustDesk MCP Server",
                "os": "Windows",
                "type": "server",
            },
        }

        try:
            url = f"{self.api_url.rstrip('/')}/api/login"
            async with self.http_session.post(url, json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if "access_token" in result:
                        self.jwt_token = result["access_token"]
                        # Token expires in 168 hours (7 days) according to config
                        self.token_expires_at = datetime.utcnow() + timedelta(hours=168)
                        logger.info("Successfully logged in to RustDesk API")
                        return True
                    else:
                        logger.error(
                            f"Login failed: No access_token in response: {result}"
                        )
                        return False
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Login failed with status {response.status}: {error_text}"
                    )
                    return False
        except Exception as e:
            logger.exception(f"Login request failed: {e}")
            return False

    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid JWT token."""
        if self.mock_mode:
            return True

        # Check if we have a token and it's not expired
        if self.jwt_token and self.token_expires_at:
            # Refresh token if it expires within 1 hour
            if datetime.utcnow() + timedelta(hours=1) < self.token_expires_at:
                return True

        # Try to login/get new token
        return await self._login()

    async def close(self):
        """Close the HTTP session."""
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()

    async def run_command(
        self, args: List[Union[str, Path]], timeout: int = 30
    ) -> Dict[str, Any]:
        """Run a RustDesk command with error handling.

        Args:
            args: Command arguments to pass to RustDesk
            timeout: Command timeout in seconds

        Returns:
            Dictionary containing command output and status
        """
        if self.mock_mode:
            # Mock mode - simulate command responses
            logger.debug(
                "Mock mode: Running command: %s", " ".join(str(arg) for arg in args)
            )
            await asyncio.sleep(0.1)  # Simulate command delay

            # Return mock responses based on command
            cmd_str = " ".join(str(arg) for arg in args)
            if "--connect" in cmd_str:
                return {"success": True, "output": {"session_id": str(uuid.uuid4())}}
            elif "--disconnect" in cmd_str:
                return {"success": True, "output": {"disconnected": True}}
            elif "--get-id" in cmd_str:
                return {"success": True, "output": "123456789"}
            else:
                return {"success": False, "error": "Mock mode: Command not supported"}

        try:
            if not self.rustdesk_path:
                return {"success": False, "error": "RustDesk executable not configured"}

            cmd = [str(self.rustdesk_path)] + [str(arg) for arg in args]
            logger.debug("Running command: %s", " ".join(cmd))

            env = os.environ.copy()
            if self.config_dir:
                env["RUSTDESK_CONFIG_DIR"] = str(self.config_dir)

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error("Command failed with error: %s", error_msg)
                raise RuntimeError(f"Command failed: {error_msg}")

            output = stdout.decode().strip()
            logger.debug("Command output: %s", output)

            try:
                return {"success": True, "output": json.loads(output) if output else {}}
            except json.JSONDecodeError:
                return {"success": True, "output": output}

        except Exception as e:
            logger.exception("Error running RustDesk command")
            return {"success": False, "error": str(e)}

    def is_running(self) -> bool:
        """Check if RustDesk is currently running.

        Returns:
            bool: True if RustDesk is running, False otherwise
        """
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] and "rustdesk" in proc.info["name"].lower():
                return True
        return False

    def is_installed(self) -> bool:
        """Check if RustDesk is installed.

        Returns:
            bool: True if RustDesk executable is found, False otherwise
        """
        return self.rustdesk_path is not None and self.rustdesk_path.exists()

    async def get_rustdesk_id(self) -> Dict[str, Any]:
        """Get the current RustDesk ID.

        Returns:
            dict: RustDesk ID information
        """
        if self.mock_mode:
            return {"success": True, "id": "MOCK-123456789"}

        result = await self.run_command(["--get-id"])
        if result.get("success", False):
            output = result.get("output", "")
            # Handle different output types
            if isinstance(output, str):
                rustdesk_id = output.strip()
            elif isinstance(output, int):
                rustdesk_id = str(output)
            else:
                rustdesk_id = str(output)

            return {"success": True, "id": rustdesk_id, "method": "cli"}
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to get RustDesk ID"),
                "method": "cli",
            }

    async def list_active_sessions(self) -> Dict[str, Any]:
        """List active RustDesk remote desktop sessions via API.

        Returns:
            dict: Active session information with connection details
        """
        if self.mock_mode:
            return {
                "success": True,
                "sessions": [],
                "count": 0,
                "methods_used": ["api"],
                "note": "Only active remote sessions are listed. 'tracked_session' = managed sessions, 'network_detected' = active network connections, 'log_detected' = recent activity from logs. No local processes shown.",
            }

        try:
            # PRIMARY: Try direct socket communication with RustDesk servers
            try:
                # Test server connectivity first
                connection_test = self.socket_client.test_connection()
                if connection_test["id_server"].get("status") == "connected":
                    # Try to get peer/session information via socket commands
                    # Note: We need to discover the actual command protocol
                    # For now, we'll try some basic commands
                    try:
                        peers = self.socket_client.list_peers()
                        sessions = []

                        # Convert peers to session format
                        for peer in peers:
                            sessions.append(
                                {
                                    "session_id": f"socket_{peer.get('id', 'unknown')}",
                                    "peer_id": peer.get("id", "unknown"),
                                    "status": "connected",
                                    "connection_type": "direct_socket",
                                    "source": "rustdesk_socket",
                                    "details": peer,
                                }
                            )

                        return {
                            "success": True,
                            "sessions": sessions,
                            "count": len(sessions),
                            "methods_used": ["socket"],
                            "note": "Sessions retrieved via direct RustDesk socket communication.",
                        }
                    except Exception as socket_error:
                        logger.debug(f"Socket session query failed: {socket_error}")

            except Exception as conn_error:
                logger.debug(f"Socket connection failed: {conn_error}")

            # FALLBACK 1: Try API server (if configured)
            if not self.mock_mode and self.api_url:
                api_result = await self._api_request("GET", "/api/sessions")

                if api_result.get("success"):
                    sessions = api_result.get("data", {}).get("sessions", [])
                    return {
                        "success": True,
                        "sessions": sessions,
                        "count": len(sessions),
                        "methods_used": ["api"],
                        "note": "Sessions retrieved from RustDesk API server.",
                    }
                elif api_result.get("status") == 404:
                    # API doesn't have a sessions endpoint - try audit logs for recent connections
                    audit_result = await self._api_request("GET", "/api/audit/conn")
                    if audit_result.get("success"):
                        # Parse audit logs to extract recent connection info
                        audit_data = audit_result.get("data", [])
                        sessions = []
                        for entry in audit_data[:10]:  # Last 10 connections
                            if isinstance(entry, dict):
                                sessions.append(
                                    {
                                        "session_id": f"audit_{entry.get('id', 'unknown')}",
                                        "peer_id": entry.get("peer", "unknown"),
                                        "status": "historical",
                                        "last_seen": entry.get("created_at"),
                                        "connection_type": "audit_log",
                                        "source": "api_audit",
                                        "details": entry,
                                    }
                                )

                        return {
                            "success": True,
                            "sessions": sessions,
                            "count": len(sessions),
                            "methods_used": ["api_audit"],
                            "note": "No real-time sessions API available. Showing recent connections from audit logs.",
                        }

            # FALLBACK 2: Check our session manager for locally tracked sessions
            local_sessions = await self.session_manager.list_active_sessions()
            sessions = []
            for session in local_sessions:
                sessions.append(
                    {
                        "session_id": session.get("id"),
                        "peer_id": session.get("peer_id"),
                        "status": session.get("status", "active"),
                        "started_at": session.get("created_at"),
                        "connection_type": "tracked_session",
                        "source": "session_manager",
                    }
                )

            return {
                "success": True,
                "sessions": sessions,
                "count": len(sessions),
                "methods_used": ["session_manager"],
                "note": "Direct socket communication unavailable. Showing locally tracked sessions.",
            }

        except Exception as e:
            logger.exception(f"Failed to list active sessions: {str(e)}")
            return {"success": False, "error": str(e), "sessions": [], "count": 0}

    async def get_address_book(self) -> Dict[str, Any]:
        """Get RustDesk address book information.

        Returns:
            dict: Address book data
        """
        if self.mock_mode:
            return {
                "success": True,
                "address_book": {
                    "entries": [],
                    "count": 0,
                    "note": "Mock mode - no real address book",
                },
            }

        # RustDesk stores address book in config directory
        if not self.config_dir:
            return {"success": False, "error": "Config directory not available"}

        address_book_file = self.config_dir / "addrbook.toml"
        if not address_book_file.exists():
            return {
                "success": True,
                "address_book": {"entries": [], "count": 0, "file_exists": False},
            }

        try:
            # Try different possible formats and files
            possible_files = [
                self.config_dir / "addrbook.toml",
                self.config_dir / "address_book.toml",
                self.config_dir / "peers.json",
                self.config_dir / "addrbook.json",
            ]

            data = None
            used_file = None

            for addr_file in possible_files:
                if addr_file.exists():
                    try:
                        if addr_file.suffix.lower() == ".toml":
                            import tomllib

                            with open(addr_file, "rb") as f:
                                data = tomllib.load(f)
                        else:
                            import json

                            with open(addr_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                        used_file = addr_file
                        break
                    except Exception:
                        continue

            if data is None:
                return {
                    "success": True,
                    "address_book": {
                        "entries": [],
                        "count": 0,
                        "file_exists": False,
                        "note": "No address book file found",
                    },
                }

            entries = []
            peers = data.get("peers", {})

            for peer_id, peer_info in peers.items():
                if isinstance(peer_info, dict):
                    entries.append(
                        {
                            "id": str(peer_id),
                            "alias": peer_info.get("alias", ""),
                            "note": peer_info.get("note", ""),
                            "tags": peer_info.get("tags", []),
                            "last_used": peer_info.get("last_used", None),
                        }
                    )
                else:
                    # Handle simple string entries
                    entries.append(
                        {
                            "id": str(peer_id),
                            "alias": str(peer_info),
                            "note": "",
                            "tags": [],
                            "last_used": None,
                        }
                    )

            return {
                "success": True,
                "address_book": {
                    "entries": entries,
                    "count": len(entries),
                    "file_exists": True,
                    "file_path": str(used_file),
                },
            }

        except PermissionError:
            return {
                "success": True,
                "address_book": {
                    "entries": [],
                    "count": 0,
                    "file_exists": True,
                    "access_denied": True,
                    "note": "Cannot access address book due to permissions",
                },
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read address book: {str(e)}"}

    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed RustDesk status information.

        Returns:
            dict: Comprehensive status information
        """
        status = await self.get_status()

        # Add additional information
        if not self.mock_mode:
            rustdesk_id = await self.get_rustdesk_id()
            sessions = await self.list_active_sessions()
            address_book = await self.get_address_book()

            status.update(
                {
                    "rustdesk_id": rustdesk_id,
                    "active_sessions": sessions,
                    "address_book": address_book,
                }
            )

        return status

    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of RustDesk.

        Returns:
            Dictionary containing RustDesk status information
        """
        return {
            "is_running": self.is_running(),
            "version": await self.get_version(),
            "config": await self.get_config(),
        }

    async def get_version(self) -> str:
        """Get the RustDesk version.

        Returns:
            str: RustDesk version string
        """
        result = await self.run_command(["--version"])
        return result.get("output", "unknown")

    async def get_config(self) -> Dict[str, Any]:
        """Get the current RustDesk configuration.

        Returns:
            dict: Current configuration
        """
        if not self.config_dir:
            return {"error": "No config directory available"}

        config_file = self.config_dir / "config"
        if not config_file.exists():
            return {"status": "config_file_not_found"}

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            logger.warning("Failed to read RustDesk config: %s", e)
            return {"status": "config_read_error", "error": str(e)}

    async def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update RustDesk configuration.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            dict: Updated configuration
        """
        config = await self.get_config()
        config.update(updates)

        config_file = self.config_dir / "config"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        return config

    async def connect(self, peer_id: str, password: str) -> Dict[str, Any]:
        """Connect to a remote peer via API.

        Args:
            peer_id: ID of the peer to connect to
            password: Password for the peer

        Returns:
            dict: Connection result with session information
        """
        # Create a new session
        session = await self.session_manager.create_session(peer_id, password)

        try:
            # Connect using API
            result = await self._api_request(
                "POST", "/api/connect", {"peer_id": peer_id, "password": password}
            )

            if result.get("success", False):
                # Update session status on success
                await self.session_manager.update_session_status(
                    session["id"],
                    "connected",
                    peer_id=peer_id,
                    connected_at=datetime.utcnow().isoformat(),
                )
                return {
                    "success": True,
                    "session_id": session["id"],
                    "message": "Connected successfully",
                    "details": result.get("data", {}),
                }
            else:
                # Update session status on failure
                await self.session_manager.update_session_status(
                    session["id"],
                    "connection_failed",
                    error=result.get("error", "API connection failed"),
                )
                return {
                    "success": False,
                    "error": result.get("error", "Connection failed"),
                    "session_id": session["id"],
                }

        except Exception as e:
            # Update session status on exception
            await self.session_manager.update_session_status(
                session["id"], "error", error=str(e)
            )
            logger.exception(f"Failed to connect to peer {peer_id}")
            return {"success": False, "error": str(e), "session_id": session["id"]}

    async def disconnect(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Disconnect from the current session or a specific session.

        Args:
            session_id: Optional ID of the session to disconnect. If None, disconnects all sessions.

        Returns:
            dict: Disconnection result with session information
        """
        result = {"success": True, "disconnected_sessions": []}

        try:
            if session_id:
                # Disconnect specific session
                session = await self.session_manager.get_session(session_id)
                cmd_result = await self.run_command(["--disconnect"])
                if cmd_result.get("success", False):
                    await self.session_manager.close_session(session_id)
                    result["disconnected_sessions"].append(session_id)
                else:
                    result["success"] = False
                    result["error"] = cmd_result.get(
                        "error", "Failed to disconnect session"
                    )
            else:
                # Disconnect all active sessions
                active_sessions = await self.session_manager.list_active_sessions()
                for session in active_sessions:
                    session_id = session["id"]
                    cmd_result = await self.run_command(["--disconnect"])
                    if cmd_result.get("success", False):
                        await self.session_manager.close_session(session_id)
                        result["disconnected_sessions"].append(session_id)
                    else:
                        logger.warning(
                            "Failed to disconnect session %s: %s",
                            session_id,
                            cmd_result.get("error", "Unknown error"),
                        )

            return result

        except Exception as e:
            logger.exception("Error disconnecting session")
            return {"success": False, "error": str(e)}

    async def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current connection.

        Returns:
            dict: Connection information
        """
        return await self.run_command(["--info"])

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics.

        Returns:
            dict: Performance metrics
        """
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Get memory usage
        memory = psutil.virtual_memory()

        # Get disk usage
        disk = psutil.disk_usage("/")

        # Get network stats
        net_io = psutil.net_io_counters()

        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            },
        }

    async def transfer_file(
        self, local_path: str, remote_path: str, direction: str = "upload"
    ) -> Dict[str, Any]:
        """Transfer files to/from remote peer."""
        return {
            "success": False,
            "error": "File transfer is not supported via RustDesk CLI. Please use alternative methods (SCP/SFTP).",
            "method": "cli",
        }

    async def list_remote_files(self, remote_path: str = "/") -> Dict[str, Any]:
        """List files in remote directory."""
        return {
            "success": False,
            "error": "Remote file listing is not supported via RustDesk CLI.",
            "method": "cli",
        }

    async def take_screenshot(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Capture screenshot of remote desktop."""
        return {
            "success": False,
            "error": "Remote screenshot capture is not supported via RustDesk CLI. Consider using 'mss' for local capture.",
            "method": "cli",
        }

    async def start_screen_recording(
        self, save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start recording the remote desktop session."""
        return {
            "success": False,
            "error": "Screen recording is not supported via RustDesk CLI.",
            "method": "cli",
        }

    async def stop_screen_recording(self) -> Dict[str, Any]:
        """Stop the current screen recording."""
        return {
            "success": False,
            "error": "Screen recording is not supported via RustDesk CLI.",
            "method": "cli",
        }

    async def get_connection_quality(self) -> Dict[str, Any]:
        """Get detailed connection quality metrics."""
        return {
            "success": False,
            "error": "Connection quality metrics are not supported via RustDesk CLI.",
            "method": "cli",
        }

    async def monitor_resource_usage(
        self, duration_seconds: int = 60, interval: float = 5.0
    ) -> Dict[str, Any]:
        """Monitor system resource usage over time.

        Args:
            duration_seconds: Total duration to monitor in seconds
            interval: Time between measurements in seconds

        Returns:
            dict: Resource usage statistics and time series data
        """
        measurements = []
        start_time = time.time()

        try:
            # Ensure reasonable values
            duration_seconds = max(1, min(duration_seconds, 3600))  # Cap at 1 hour
            interval = max(0.5, min(interval, 60.0))  # Between 0.5s and 60s

            logger.info(
                f"Starting resource monitoring for {duration_seconds} seconds with {interval}s interval"
            )

            while time.time() - start_time < duration_seconds:
                # Get current timestamp
                timestamp = time.time()

                # Get performance metrics
                metrics = await self.get_performance_metrics()

                # Get connection quality if available
                conn_quality = {}
                try:
                    conn_result = await self.get_connection_quality()
                    if conn_result.get("success", False):
                        conn_quality = conn_result.get("connection_quality", {})
                except Exception as e:
                    logger.warning(f"Failed to get connection quality: {str(e)}")

                # Add to measurements
                measurements.append(
                    {
                        "timestamp": timestamp,
                        "metrics": metrics,
                        "connection_quality": conn_quality,
                    }
                )

                # Sleep until next interval, but don't sleep longer than remaining duration
                remaining = max(0, (start_time + duration_seconds) - time.time())
                if remaining > 0:
                    await asyncio.sleep(min(interval, remaining))
                else:
                    break

            # Calculate summary statistics
            if measurements:
                # CPU stats
                cpu_percent = [m["metrics"]["cpu"]["percent"] for m in measurements]
                # Memory stats
                mem_percent = [m["metrics"]["memory"]["percent"] for m in measurements]
                # Network stats (if available)
                net_sent = [m["metrics"]["network"]["bytes_sent"] for m in measurements]
                net_recv = [m["metrics"]["network"]["bytes_recv"] for m in measurements]
                # Latency stats (if available)
                latencies = [
                    m.get("connection_quality", {}).get("latency_ms", 0)
                    for m in measurements
                    if m.get("connection_quality", {}).get("latency_ms", 0) > 0
                ]

                summary = {
                    "duration_seconds": time.time() - start_time,
                    "measurement_count": len(measurements),
                    "cpu": {
                        "avg": sum(cpu_percent) / len(cpu_percent),
                        "max": max(cpu_percent),
                        "min": min(cpu_percent),
                    },
                    "memory": {
                        "avg": sum(mem_percent) / len(mem_percent),
                        "max": max(mem_percent),
                        "min": min(mem_percent),
                    },
                    "network": {
                        "bytes_sent": net_sent[-1] - net_sent[0] if net_sent else 0,
                        "bytes_received": net_recv[-1] - net_recv[0] if net_recv else 0,
                    },
                }

                if latencies:
                    summary["latency_ms"] = {
                        "avg": sum(latencies) / len(latencies),
                        "max": max(latencies),
                        "min": min(latencies),
                    }
            else:
                summary = {"error": "No measurements collected"}

            return {
                "success": True,
                "start_time": start_time,
                "end_time": time.time(),
                "summary": summary,
                "measurements": measurements,
            }

        except Exception as e:
            logger.exception(f"Resource monitoring failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "measurements": measurements,
                "duration_seconds": time.time() - start_time,
            }
