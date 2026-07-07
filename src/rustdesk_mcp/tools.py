"""
MCP Tools for RustDesk operations.

This module provides MCP-compatible tool definitions for the RustDesk service.
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import asyncio
import logging

from pydantic import BaseModel, Field

from .services.rustdesk_service import RustDeskService

logger = logging.getLogger(__name__)

# Request/Response Models
class ConnectionRequest(BaseModel):
    """Request model for connection operations."""
    peer_id: str = Field(..., description="ID of the peer to connect to")
    password: str = Field(..., description="Password for the peer connection")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")


class FileTransferRequest(BaseModel):
    """Request model for file transfer operations."""
    local_path: str = Field(..., description="Local file path")
    remote_path: str = Field(..., description="Remote file path")
    direction: str = Field("upload", description="'upload' or 'download'")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")
    peer_id: Optional[str] = Field(None, description="RustDesk peer ID for the remote machine")


class ScreenshotRequest(BaseModel):
    """Request model for screenshot operations."""
    save_path: Optional[str] = Field(None, description="Optional path to save the screenshot")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")


class RecordingRequest(BaseModel):
    """Request model for screen recording operations."""
    save_path: Optional[str] = Field(None, description="Optional path to save the recording")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")


class MonitoringRequest(BaseModel):
    """Request model for resource monitoring."""
    duration_seconds: int = Field(60, description="Duration to monitor in seconds")
    interval: float = Field(5.0, description="Interval between measurements in seconds")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")


class RustDeskTools:
    """MCP tools for RustDesk remote desktop operations."""
    
    def __init__(self, rustdesk_service: RustDeskService):
        """Initialize with a RustDeskService instance."""
        self.rustdesk = rustdesk_service
    
    async def connect_to_peer(self, request: ConnectionRequest) -> Dict[str, Any]:
        """Connect to a remote peer.
        
        Args:
            request: Connection request parameters
            
        Returns:
            dict: Connection result with session information
        """
        try:
            result = await self.rustdesk.connect(request.peer_id, request.password)
            
            # If we have a session ID in the request, update the session
            if request.session_id:
                await self.rustdesk.session_manager.update_session_status(
                    request.session_id,
                    "connected" if result.get("success", False) else "connection_failed",
                    peer_id=request.peer_id,
                    **result
                )
            
            return {
                "success": result.get("success", False),
                "session_id": result.get("session_id"),
                "message": "Connected successfully" if result.get("success") else "Connection failed",
                "details": result
            }
            
        except Exception as e:
            logger.exception(f"Failed to connect to peer: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "peer_id": request.peer_id
            }
    
    async def disconnect_peer(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Disconnect from a peer or all peers.
        
        Args:
            session_id: Optional session ID to disconnect. If None, disconnects all.
            
        Returns:
            dict: Disconnection result
        """
        try:
            result = await self.rustdesk.disconnect(session_id)
            
            if session_id and result.get("success", False):
                # Update session status if we're disconnecting a specific session
                await self.rustdesk.session_manager.update_session_status(
                    session_id,
                    "disconnected",
                    disconnected_at=result.get("disconnected_at")
                )
            
            return {
                "success": result.get("success", False),
                "disconnected_sessions": result.get("disconnected_sessions", []),
                "message": "Disconnected successfully" if result.get("success") else "Disconnection failed"
            }
            
        except Exception as e:
            logger.exception(f"Failed to disconnect: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def transfer_file(self, request: FileTransferRequest) -> Dict[str, Any]:
        """Transfer a file to/from a remote peer.
        
        Args:
            request: File transfer request parameters
            
        Returns:
            dict: Transfer result with status and details
        """
        try:
            result = await self.rustdesk.transfer_file(
                local_path=request.local_path,
                remote_path=request.remote_path,
                direction=request.direction,
                peer_id=request.peer_id,
            )
            
            # Update session if we have a session ID
            if request.session_id:
                await self.rustdesk.session_manager.update_session_status(
                    request.session_id,
                    "file_transfer_completed" if result.get("success") else "file_transfer_failed",
                    transfer_result=result
                )
            
            return {
                "success": result.get("success", False),
                "direction": request.direction,
                "local_path": request.local_path,
                "remote_path": request.remote_path,
                "details": result
            }
            
        except Exception as e:
            logger.exception(f"File transfer failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "direction": request.direction,
                "local_path": request.local_path,
                "remote_path": request.remote_path
            }
    
    async def take_screenshot(self, request: ScreenshotRequest) -> Dict[str, Any]:
        """Take a screenshot of the remote desktop.
        
        Args:
            request: Screenshot request parameters
            
        Returns:
            dict: Screenshot information including file path
        """
        try:
            result = await self.rustdesk.take_screenshot(request.save_path)
            
            # Update session if we have a session ID
            if request.session_id:
                await self.rustdesk.session_manager.update_session_status(
                    request.session_id,
                    "screenshot_taken" if result.get("success") else "screenshot_failed",
                    screenshot_result=result
                )
            
            return result
            
        except Exception as e:
            logger.exception(f"Failed to take screenshot: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "save_path": request.save_path
            }
    
    async def start_recording(self, request: RecordingRequest) -> Dict[str, Any]:
        """Start recording the remote desktop session.
        
        Args:
            request: Recording request parameters
            
        Returns:
            dict: Recording information including recording ID
        """
        try:
            result = await self.rustdesk.start_screen_recording(request.save_path)
            
            # Update session if we have a session ID
            if request.session_id and result.get("success"):
                await self.rustdesk.session_manager.update_session_status(
                    request.session_id,
                    "recording_started",
                    recording_id=result.get("recording_id"),
                    recording_path=result.get("file_path")
                )
            
            return result
            
        except Exception as e:
            logger.exception(f"Failed to start recording: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "save_path": request.save_path
            }
    
    async def stop_recording(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Stop the current screen recording.
        
        Args:
            session_id: Optional session ID to associate with this recording
            
        Returns:
            dict: Recording information including file path and duration
        """
        try:
            result = await self.rustdesk.stop_screen_recording()
            
            # Update session if we have a session ID
            if session_id and result.get("success"):
                await self.rustdesk.session_manager.update_session_status(
                    session_id,
                    "recording_stopped",
                    recording_duration=result.get("duration_seconds"),
                    recording_path=result.get("file_path")
                )
            
            return result
            
        except Exception as e:
            logger.exception(f"Failed to stop recording: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def monitor_resources(self, request: MonitoringRequest) -> Dict[str, Any]:
        """Monitor system resource usage.
        
        Args:
            request: Monitoring request parameters
            
        Returns:
            dict: Resource usage statistics and time series data
        """
        try:
            result = await self.rustdesk.monitor_resource_usage(
                duration_seconds=request.duration_seconds,
                interval=request.interval
            )
            
            # Update session if we have a session ID
            if request.session_id:
                await self.rustdesk.session_manager.update_session_status(
                    request.session_id,
                    "monitoring_completed" if result.get("success") else "monitoring_failed",
                    monitoring_summary=result.get("summary", {})
                )
            
            return result
            
        except Exception as e:
            logger.exception(f"Resource monitoring failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": request.duration_seconds,
                "interval": request.interval
            }
    
    async def get_connection_quality(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get the current connection quality metrics.
        
        Args:
            session_id: Optional session ID to associate with this request
            
        Returns:
            dict: Connection quality metrics
        """
        try:
            result = await self.rustdesk.get_connection_quality()
            
            # Update session if we have a session ID
            if session_id and result.get("success"):
                await self.rustdesk.session_manager.update_session_status(
                    session_id,
                    "connection_quality_checked",
                    connection_quality=result.get("connection_quality", {})
                )
            
            return result
            
        except Exception as e:
            logger.exception(f"Failed to get connection quality: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_remote_files(self, remote_path: str = "/", session_id: Optional[str] = None) -> Dict[str, Any]:
        """List files in a remote directory.
        
        Args:
            remote_path: Path on the remote system to list
            session_id: Optional session ID to associate with this request
            
        Returns:
            dict: Directory listing with file information
        """
        try:
            result = await self.rustdesk.list_remote_files(remote_path)
            
            # Update session if we have a session ID
            if session_id and result.get("success"):
                await self.rustdesk.session_manager.update_session_status(
                    session_id,
                    "remote_files_listed",
                    directory=remote_path,
                    file_count=len(result.get("files", []))
                )
            
            return result
            
        except Exception as e:
            logger.exception(f"Failed to list remote files: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "directory": remote_path
            }
