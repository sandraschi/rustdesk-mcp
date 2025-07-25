""
API v1 routes for RustDeskMCP.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from ....config import Config, get_config
from ....services.rustdesk_service import RustDeskService
from . import models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["v1"])

# Dependency to get the RustDesk service
def get_rustdesk_service(config: Config = Depends(get_config)) -> RustDeskService:
    """Get the RustDesk service instance."""
    return RustDeskService(config.rustdesk_path, config.rustdesk_config_dir)


@router.get(
    "/status",
    response_model=models.StatusResponse,
    summary="Get service status",
    description="Get the current status of the RustDesk MCP service.",
)
async def get_status(
    service: RustDeskService = Depends(get_rustdesk_service)
) -> Dict[str, Any]:
    """Get the current status of the service."""
    try:
        status_info = await service.get_status()
        return {
            "status": "running",
            "version": status_info.get("version", "unknown"),
            "rustdesk_running": status_info.get("is_running", False),
            "config_path": str(service.config_dir),
        }
    except Exception as e:
        logger.exception("Error getting service status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting service status: {str(e)}",
        )


@router.get(
    "/info",
    response_model=models.ServiceInfo,
    summary="Get RustDesk info",
    description="Get information about the RustDesk service and configuration.",
)
async def get_info(
    service: RustDeskService = Depends(get_rustdesk_service)
) -> Dict[str, Any]:
    """Get information about the RustDesk service."""
    try:
        status_info = await service.get_status()
        return {
            "is_running": status_info.get("is_running", False),
            "version": status_info.get("version", "unknown"),
            "config": status_info.get("config", {}),
        }
    except Exception as e:
        logger.exception("Error getting RustDesk info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting RustDesk info: {str(e)}",
        )


@router.get(
    "/connection",
    response_model=models.ConnectionInfo,
    summary="Get connection info",
    description="Get information about the current RustDesk connection.",
)
async def get_connection_info(
    service: RustDeskService = Depends(get_rustdesk_service)
) -> Dict[str, Any]:
    """Get information about the current connection."""
    try:
        return await service.get_connection_info()
    except Exception as e:
        logger.exception("Error getting connection info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting connection info: {str(e)}",
        )


@router.post(
    "/connect",
    response_model=models.CommandResponse,
    summary="Connect to a peer",
    description="Connect to a RustDesk peer by ID and password.",
)
async def connect_to_peer(
    request: models.ConnectRequest,
    service: RustDeskService = Depends(get_rustdesk_service)
) -> Dict[str, Any]:
    """Connect to a RustDesk peer."""
    try:
        result = await service.connect(request.peer_id, request.password)
        
        if request.save_password:
            # Save the password in the config
            await service.update_config({"saved_peers": {
                request.peer_id: {"password": request.password}
            }})
            
        return {
            "success": True,
            "message": "Connection initiated",
            "data": result,
        }
    except Exception as e:
        logger.exception("Error connecting to peer")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to peer: {str(e)}",
        )


@router.post(
    "/disconnect",
    response_model=models.CommandResponse,
    summary="Disconnect from peer",
    description="Disconnect from the current RustDesk session.",
)
async def disconnect(
    service: RustDeskService = Depends(get_rustdesk_service)
) -> Dict[str, Any]:
    """Disconnect from the current session."""
    try:
        result = await service.disconnect()
        return {
            "success": True,
            "message": "Disconnected",
            "data": result,
        }
    except Exception as e:
        logger.exception("Error disconnecting")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disconnecting: {str(e)}",
        )


@router.get(
    "/performance",
    response_model=models.PerformanceMetrics,
    summary="Get performance metrics",
    description="Get system performance metrics.",
)
async def get_performance(
    service: RustDeskService = Depends(get_rustdesk_service)
) -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        return await service.get_performance_metrics()
    except Exception as e:
        logger.exception("Error getting performance metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting performance metrics: {str(e)}",
        )


@router.post(
    "/config",
    response_model=models.CommandResponse,
    summary="Update configuration",
    description="Update RustDesk configuration.",
)
async def update_config(
    config_update: models.ConfigUpdate,
    service: RustDeskService = Depends(get_rustdesk_service)
) -> Dict[str, Any]:
    """Update RustDesk configuration."""
    try:
        updated_config = await service.update_config(config_update.updates)
        return {
            "success": True,
            "message": "Configuration updated",
            "data": {"config": updated_config},
        }
    except Exception as e:
        logger.exception("Error updating configuration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating configuration: {str(e)}",
        )
