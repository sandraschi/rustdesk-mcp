"""
RustDeskMCP - FastMCP 2.10 Server for RustDesk Remote Desktop Management

Provides natural language interface for RustDesk operations through FastMCP protocol.
"""

__version__ = "0.1.0"

from .config import Config, get_config
from .server import app, mcp

__all__ = ["app", "mcp", "Config", "get_config"]
