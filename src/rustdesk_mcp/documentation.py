"""
Documentation for RustDesk MCP Server.

This module provides comprehensive documentation for the RustDesk MCP server,
including tool descriptions, usage examples, and feature overview.
"""
from typing import Any

# Main documentation structure
MCP_DOCS = {
    "server_info": {
        "name": "RustDesk MCP Server",
        "version": "0.1.0",
        "description": "FastMCP 2.10 server for RustDesk remote desktop management",
        "features": [
            "Remote desktop connection management",
            "File transfer between local and remote systems",
            "Screen capture and recording",
            "System resource monitoring",
            "Session management and tracking"
        ]
    },
    "tools": {
        "connection": [
            {
                "name": "connect_to_peer",
                "description": "Establish a connection to a remote RustDesk peer",
                "parameters": [
                    {"name": "peer_id", "type": "str", "required": True, "description": "ID of the peer to connect to"},
                    {"name": "password", "type": "str", "required": True, "description": "Password for the peer"},
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID for tracking"}
                ],
                "returns": "Dict with connection status and session information"
            },
            {
                "name": "disconnect_peer",
                "description": "Disconnect from a connected peer or all peers",
                "parameters": [
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID to disconnect"}
                ],
                "returns": "Dict with disconnection status"
            }
        ],
        "file_transfer": [
            {
                "name": "transfer_file",
                "description": "Transfer files between local and remote systems",
                "parameters": [
                    {"name": "local_path", "type": "str", "required": True, "description": "Local file path"},
                    {"name": "remote_path", "type": "str", "required": True, "description": "Remote file path"},
                    {"name": "direction", "type": "str", "required": False, "default": "upload", "description": "'upload' or 'download'"},
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID"}
                ],
                "returns": "Dict with transfer status and details"
            },
            {
                "name": "list_remote_files",
                "description": "List files in a remote directory",
                "parameters": [
                    {"name": "remote_path", "type": "str", "required": False, "default": "/", "description": "Path to list"},
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID"}
                ],
                "returns": "Dict with directory listing"
            }
        ],
        "screen_capture": [
            {
                "name": "take_screenshot",
                "description": "Capture a screenshot of the remote desktop",
                "parameters": [
                    {"name": "save_path", "type": "str", "required": False, "description": "Optional path to save the screenshot"},
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID"}
                ],
                "returns": "Dict with screenshot information"
            },
            {
                "name": "start_recording",
                "description": "Start recording the remote desktop session",
                "parameters": [
                    {"name": "save_path", "type": "str", "required": False, "description": "Optional path to save the recording"},
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID"}
                ],
                "returns": "Dict with recording status"
            },
            {
                "name": "stop_recording",
                "description": "Stop the current screen recording",
                "parameters": [
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID"}
                ],
                "returns": "Dict with recording information"
            }
        ],
        "monitoring": [
            {
                "name": "monitor_resources",
                "description": "Monitor system resource usage",
                "parameters": [
                    {"name": "duration_seconds", "type": "int", "required": False, "default": 60, "description": "Duration in seconds"},
                    {"name": "interval", "type": "float", "required": False, "default": 5.0, "description": "Interval between measurements"},
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID"}
                ],
                "returns": "Dict with resource usage statistics"
            },
            {
                "name": "get_connection_quality",
                "description": "Get current connection quality metrics",
                "parameters": [
                    {"name": "session_id", "type": "str", "required": False, "description": "Optional session ID"}
                ],
                "returns": "Dict with connection quality metrics"
            }
        ],
        "system": [
            {
                "name": "get_rustdesk_status",
                "description": "Get the current status of the RustDesk service",
                "parameters": [],
                "returns": "Dict with service status information"
            },
            {
                "name": "help",
                "description": "Get help about available MCP tools and features",
                "parameters": [
                    {"name": "tool_name", "type": "str", "required": False, "description": "Optional tool name to get specific help"}
                ],
                "returns": "Structured help documentation"
            }
        ]
    },
    "examples": {
        "basic_connection": """
        # Connect to a remote peer
        await connect_to_peer(
            peer_id="123-456-789",
            password="secure-password",
            session_id="my-session-1"
        )
        """,
        "file_transfer": """
        # Upload a file to remote system
        await transfer_file(
            local_path="/local/path/file.txt",
            remote_path="/remote/path/",
            direction="upload",
            session_id="my-session-1"
        )
        """,
        "screen_capture": """
        # Take a screenshot
        await take_screenshot(
            save_path="/screenshots/screen.png",
            session_id="my-session-1"
        )

        # Start recording
        await start_recording(
            save_path="/recordings/session.mp4",
            session_id="my-session-1"
        )
        """
    }
}

class HelpTool:
    """Help tool for RustDesk MCP server documentation."""

    @staticmethod
    async def get_help(tool_name: str | None = None) -> dict[str, Any]:
        """
        Get help documentation for the MCP server or a specific tool.

        Args:
            tool_name: Optional name of the tool to get specific help for

        Returns:
            Dict containing help documentation
        """
        if tool_name:
            # Find the specific tool in the documentation
            for category, tools in MCP_DOCS["tools"].items():
                for tool in tools:
                    if tool["name"] == tool_name:
                        return {
                            "tool": tool_name,
                            "description": tool["description"],
                            "parameters": tool["parameters"],
                            "returns": tool["returns"],
                            "category": category
                        }
            return {"error": f"Tool '{tool_name}' not found"}

        # Return complete documentation if no specific tool is requested
        return MCP_DOCS

    @classmethod
    def get_tool_definition(cls):
        """Get the MCP tool definition for the help command."""
        return {
            "name": "help",
            "description": "Get help about available MCP tools and features",
            "parameters": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool to get specific help for",
                    "required": False
                }
            },
            "method": cls.get_help
        }

# Export the help tool for easy registration
help_tool = HelpTool()
