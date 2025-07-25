"""
Service layer for RustDesk operations.
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import psutil
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RustDeskService:
    """Service for interacting with RustDesk."""

    def __init__(self, rustdesk_path: Path, config_dir: Path):
        """Initialize the RustDesk service.
        
        Args:
            rustdesk_path: Path to the RustDesk executable
            config_dir: Path to the RustDesk config directory
        """
        self.rustdesk_path = rustdesk_path
        self.config_dir = config_dir
        logger.info("RustDesk service initialized with path: %s", rustdesk_path)

    async def run_command(
        self, 
        args: List[Union[str, Path]], 
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Run a RustDesk command with error handling.
        
        Args:
            args: Command arguments to pass to RustDesk
            timeout: Command timeout in seconds
            
        Returns:
            Dictionary containing command output and status
        """
        try:
            cmd = [str(self.rustdesk_path)] + [str(arg) for arg in args]
            logger.debug("Running command: %s", " ".join(cmd))
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"RUSTDESK_CONFIG_DIR": str(self.config_dir)}
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
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
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'rustdesk' in proc.info['name'].lower():
                return True
        return False

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
        config_file = self.config_dir / "config"
        if not config_file.exists():
            return {}
            
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to read RustDesk config: %s", e)
            return {}

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
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        return config

    async def connect(self, peer_id: str, password: str) -> Dict[str, Any]:
        """Connect to a remote peer.
        
        Args:
            peer_id: ID of the peer to connect to
            password: Password for the peer
            
        Returns:
            dict: Connection result
        """
        return await self.run_command(["--connect", peer_id, "--password", password])

    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect from the current session.
        
        Returns:
            dict: Disconnection result
        """
        return await self.run_command(["--disconnect"])

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
        disk = psutil.disk_usage('/')
        
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
