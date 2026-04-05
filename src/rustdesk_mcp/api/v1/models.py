"""
Pydantic models for RustDeskMCP API v1.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl


class StatusResponse(BaseModel):
    """Response model for service status."""

    status: str = Field(..., description="Current service status")
    version: str = Field(..., description="Service version")
    rustdesk_running: bool = Field(..., description="Whether RustDesk is running")
    config_path: str = Field(..., description="Path to RustDesk config")


class ServiceInfo(BaseModel):
    """Information about the RustDesk service."""

    is_running: bool = Field(..., description="Whether the service is running")
    version: str = Field(..., description="RustDesk version")
    pid: Optional[int] = Field(None, description="Process ID if running")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Service configuration"
    )


class ConnectionInfo(BaseModel):
    """Information about a RustDesk connection."""

    peer_id: str = Field(..., description="Peer ID")
    connected: bool = Field(..., description="Whether connected to peer")
    last_connected: Optional[str] = Field(None, description="Last connection timestamp")
    connection_stats: Optional[Dict[str, Any]] = Field(
        None, description="Connection statistics"
    )


class PerformanceMetrics(BaseModel):
    """System performance metrics."""

    cpu: Dict[str, Any] = Field(..., description="CPU usage statistics")
    memory: Dict[str, Any] = Field(..., description="Memory usage statistics")
    disk: Dict[str, Any] = Field(..., description="Disk usage statistics")
    network: Dict[str, Any] = Field(..., description="Network I/O statistics")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class ConnectRequest(BaseModel):
    """Request model for connecting to a peer."""

    peer_id: str = Field(..., description="Peer ID to connect to")
    password: str = Field(..., description="Password for the peer")
    save_password: bool = Field(False, description="Whether to save the password")


class ConfigUpdate(BaseModel):
    """Model for updating RustDesk configuration."""

    updates: Dict[str, Any] = Field(..., description="Configuration updates to apply")


class CommandResponse(BaseModel):
    """Response model for command execution."""

    success: bool = Field(..., description="Whether the command was successful")
    message: str = Field(..., description="Result message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class SystemInfo(BaseModel):
    """System information."""

    os: str = Field(..., description="Operating system name")
    os_version: str = Field(..., description="Operating system version")
    hostname: str = Field(..., description="System hostname")
    cpu_cores: int = Field(..., description="Number of CPU cores")
    total_memory: int = Field(..., description="Total system memory in bytes")
    uptime: int = Field(..., description="System uptime in seconds")


class FleetLaunchRequest(BaseModel):
    """Request model for launching a fleet application."""

    repo_path: str = Field(..., description="Absolute path to the repository root")


class FleetLaunchResponse(BaseModel):
    """Response model for fleet launch operation."""

    success: bool = Field(..., description="Whether the launch was successful")
    message: str = Field(..., description="Result message")
