#!/usr/bin/env python3
"""
RustDesk Remote Desktop MCP - FastMCP 2.10.0 Implementation
Austrian dev efficiency: Complete remote desktop management through MCP protocol

Provides natural language interface for RustDesk operations.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess
import json
import psutil

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "RustDesk Remote Desktop MCP 🖥️"),
    instructions="""
    Provides comprehensive RustDesk remote desktop management through natural language commands.
    Austrian dev efficiency: Working solutions in hours, not days.
    
    Core capabilities:
    • Remote connection management
    • Server status monitoring  
    • Configuration management
    • Connection history tracking
    • Security settings control
    • Performance monitoring
    
    Example queries:
    - "Connect to remote computer with ID 123456789"
    - "Check RustDesk server status and connections"
    - "Show recent connection history"
    - "Update remote access password"
    - "Get system performance during remote session"
    - "Configure security settings for remote access"
    """,
    dependencies=[
        "fastmcp>=2.10.0",
        "python-dotenv>=1.0.0",
        "psutil>=5.9.0"
    ]
)

# RustDesk configuration
RUSTDESK_PATH = os.getenv("RUSTDESK_PATH", "rustdesk.exe")
RUSTDESK_CONFIG_DIR = os.getenv("RUSTDESK_CONFIG_DIR", str(Path.home() / ".rustdesk"))

class RustDeskAPI:
    def __init__(self, rustdesk_path: str, config_dir: str):
        self.rustdesk_path = rustdesk_path
        self.config_dir = Path(config_dir)
        
    def run_command(self, args: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Run RustDesk command with error handling"""
        try:
            cmd = [self.rustdesk_path] + args
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"RustDesk not found: {self.rustdesk_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def is_running(self) -> bool:
        """Check if RustDesk process is running"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'rustdesk' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get RustDesk configuration"""
        config_file = self.config_dir / "config.json"
        if config_file.exists():
            try:
                return json.loads(config_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to read config: {e}")
        return {}

try:
    rustdesk = RustDeskAPI(RUSTDESK_PATH, RUSTDESK_CONFIG_DIR)
    logger.info("RustDesk MCP Server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RustDesk API: {e}")
    rustdesk = None

# ============================================================================
# CONNECTION MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def get_rustdesk_status() -> Dict[str, Any]:
    """Get RustDesk service status and system information."""
    try:
        logger.info("Getting RustDesk status")
        
        if not rustdesk:
            return {"success": False, "error": "RustDesk API not initialized"}
        
        is_running = rustdesk.is_running()
        config = rustdesk.get_config()
        
        # Get system info
        system_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            "network_connections": len(psutil.net_connections())
        }
        
        return {
            "success": True,
            "rustdesk_running": is_running,
            "config": config,
            "system_info": system_info,
            "message": f"✅ RustDesk is {'running' if is_running else 'not running'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to get RustDesk status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to get RustDesk status: {str(e)}"
        }

@mcp.tool()
def start_rustdesk_service() -> Dict[str, Any]:
    """Start RustDesk service."""
    try:
        logger.info("Starting RustDesk service")
        
        if not rustdesk:
            return {"success": False, "error": "RustDesk API not initialized"}
        
        if rustdesk.is_running():
            return {
                "success": True,
                "message": "✅ RustDesk is already running"
            }
        
        result = rustdesk.run_command(["--service"])
        
        if result["success"]:
            # Wait a moment and check if it started
            import time
            time.sleep(2)
            is_running = rustdesk.is_running()
            
            return {
                "success": is_running,
                "message": f"✅ RustDesk service started" if is_running else "❌ Service may not have started properly"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to start service"),
                "message": "❌ Failed to start RustDesk service"
            }
        
    except Exception as e:
        logger.error(f"Failed to start RustDesk service: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to start RustDesk service: {str(e)}"
        }

@mcp.tool()
def get_connection_info() -> Dict[str, Any]:
    """Get current connection information and ID."""
    try:
        logger.info("Getting connection info")
        
        if not rustdesk:
            return {"success": False, "error": "RustDesk API not initialized"}
        
        result = rustdesk.run_command(["--get-id"])
        
        connection_info = {
            "is_running": rustdesk.is_running(),
            "config": rustdesk.get_config()
        }
        
        if result["success"] and result["stdout"]:
            connection_info["id"] = result["stdout"].strip()
        
        return {
            "success": True,
            "connection_info": connection_info,
            "message": "✅ Connection info retrieved"
        }
        
    except Exception as e:
        logger.error(f"Failed to get connection info: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to get connection info: {str(e)}"
        }

# ============================================================================
# REMOTE CONTROL TOOLS
# ============================================================================

@mcp.tool()
def connect_to_remote(remote_id: str, password: Optional[str] = None) -> Dict[str, Any]:
    """Connect to remote computer by ID."""
    try:
        logger.info(f"Connecting to remote ID: {remote_id}")
        
        if not rustdesk:
            return {"success": False, "error": "RustDesk API not initialized"}
        
        args = ["--connect", remote_id]
        if password:
            args.extend(["--password", password])
        
        result = rustdesk.run_command(args)
        
        return {
            "success": result["success"],
            "remote_id": remote_id,
            "message": f"✅ Connection initiated to {remote_id}" if result["success"] else f"❌ Connection failed: {result.get('error')}"
        }
        
    except Exception as e:
        logger.error(f"Failed to connect to remote: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to connect to remote: {str(e)}"
        }

@mcp.tool()
def update_password(new_password: str) -> Dict[str, Any]:
    """Update RustDesk access password."""
    try:
        logger.info("Updating RustDesk password")
        
        if not rustdesk:
            return {"success": False, "error": "RustDesk API not initialized"}
        
        result = rustdesk.run_command(["--password", new_password])
        
        return {
            "success": result["success"],
            "message": "✅ Password updated successfully" if result["success"] else f"❌ Password update failed: {result.get('error')}"
        }
        
    except Exception as e:
        logger.error(f"Failed to update password: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to update password: {str(e)}"
        }

@mcp.tool()
def get_system_performance() -> Dict[str, Any]:
    """Get system performance metrics relevant for remote desktop."""
    try:
        logger.info("Getting system performance metrics")
        
        # Get detailed performance metrics
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\' if os.name == 'nt' else '/')
        network = psutil.net_io_counters()
        
        performance = {
            "cpu": {
                "overall_percent": psutil.cpu_percent(interval=1),
                "per_core": cpu_percent,
                "core_count": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2)
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": round((disk.used / disk.total) * 100, 2)
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }
        
        # Assess remote desktop readiness
        cpu_ok = performance["cpu"]["overall_percent"] < 80
        memory_ok = performance["memory"]["percent"] < 85
        network_active = network.bytes_sent > 0 and network.bytes_recv > 0
        
        readiness_score = sum([cpu_ok, memory_ok, network_active]) / 3 * 100
        
        return {
            "success": True,
            "performance": performance,
            "remote_desktop_readiness": {
                "score_percent": round(readiness_score, 1),
                "cpu_ready": cpu_ok,
                "memory_ready": memory_ok,
                "network_active": network_active,
                "recommendation": "Ready for remote desktop" if readiness_score > 66 else "System may be under load"
            },
            "message": f"✅ Performance metrics retrieved (Readiness: {round(readiness_score, 1)}%)"
        }
        
    except Exception as e:
        logger.error(f"Failed to get system performance: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to get system performance: {str(e)}"
        }

def main():
    """Main server startup"""
    try:
        logger.info("🖥️ Starting RustDesk MCP Server...")
        
        if rustdesk:
            is_running = rustdesk.is_running()
            logger.info(f"RustDesk status: {'Running' if is_running else 'Not running'}")
        
        logger.info("✅ RustDesk MCP Server ready!")
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        raise

if __name__ == "__main__":
    main()
