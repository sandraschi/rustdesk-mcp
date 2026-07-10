import logging
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ...config import Config, get_config
from ...services.rustdesk_service import RustDeskService
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
    service: RustDeskService = Depends(get_rustdesk_service),
) -> dict[str, Any]:
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
            detail=f"Error getting service status: {e!s}",
        )


@router.get(
    "/info",
    response_model=models.ServiceInfo,
    summary="Get RustDesk info",
    description="Get information about the RustDesk service and configuration.",
)
async def get_info(
    service: RustDeskService = Depends(get_rustdesk_service),
) -> dict[str, Any]:
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
            detail=f"Error getting RustDesk info: {e!s}",
        )


@router.get(
    "/connection",
    response_model=models.ConnectionInfo,
    summary="Get connection info",
    description="Get information about the current RustDesk connection.",
)
async def get_connection_info(
    service: RustDeskService = Depends(get_rustdesk_service),
) -> dict[str, Any]:
    """Get information about the current connection."""
    try:
        return await service.get_connection_info()
    except Exception as e:
        logger.exception("Error getting connection info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting connection info: {e!s}",
        )


@router.post(
    "/connect",
    response_model=models.CommandResponse,
    summary="Connect to a peer",
    description="Connect to a RustDesk peer by ID and password.",
)
async def connect_to_peer(
    request: models.ConnectRequest,
    service: RustDeskService = Depends(get_rustdesk_service),
) -> dict[str, Any]:
    """Connect to a RustDesk peer."""
    try:
        result = await service.connect(request.peer_id, request.password)

        if request.save_password:
            # Save the password in the config
            await service.update_config(
                {"saved_peers": {request.peer_id: {"password": request.password}}}
            )

        return {
            "success": True,
            "message": "Connection initiated",
            "data": result,
        }
    except Exception as e:
        logger.exception("Error connecting to peer")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to peer: {e!s}",
        )


@router.post(
    "/disconnect",
    response_model=models.CommandResponse,
    summary="Disconnect from peer",
    description="Disconnect from the current RustDesk session.",
)
async def disconnect(
    service: RustDeskService = Depends(get_rustdesk_service),
) -> dict[str, Any]:
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
            detail=f"Error disconnecting: {e!s}",
        )


@router.get(
    "/performance",
    response_model=models.PerformanceMetrics,
    summary="Get performance metrics",
    description="Get system performance metrics.",
)
async def get_performance(
    service: RustDeskService = Depends(get_rustdesk_service),
) -> dict[str, Any]:
    """Get system performance metrics."""
    try:
        return await service.get_performance_metrics()
    except Exception as e:
        logger.exception("Error getting performance metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting performance metrics: {e!s}",
        )


@router.post(
    "/config",
    response_model=models.CommandResponse,
    summary="Update configuration",
    description="Update RustDesk configuration.",
)
async def update_config(
    config_update: models.ConfigUpdate,
    service: RustDeskService = Depends(get_rustdesk_service),
) -> dict[str, Any]:
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
            detail=f"Error updating configuration: {e!s}",
        )


@router.get(
    "/health",
    response_model=models.StatusResponse,
    summary="Standard health check",
    description="Get standardized SOTA health status.",
)
async def health_v1():
    """Standardized health check for fleet discovery."""
    return {
        "status": "ok",
        "version": "2026.2.17",
        "rustdesk_running": True,  # Mocked or checked via service
        "config_path": "standardized",
    }


@router.post(
    "/fleet/launch",
    response_model=models.FleetLaunchResponse,
    summary="Fleet launch protocol",
    description="Launch another MCP app via its start.ps1 script.",
)
async def launch_app(request: models.FleetLaunchRequest) -> models.FleetLaunchResponse:
    """Launch another MCP app via its start.ps1 script."""
    path = Path(request.repo_path)
    if not path.exists():
        raise HTTPException(
            status_code=404, detail=f"Path {request.repo_path} does not exist"
        )

    # Security check: Ensure path is within D:/Dev/repos
    try:
        allowed_base = Path("D:/Dev/repos").resolve()
        target_path = path.resolve()
        target_path.relative_to(allowed_base)
    except ValueError:
        raise HTTPException(
            status_code=403, detail="Access denied: Path outside allowed directory"
        )

    start_script = path / "web_sota" / "start.ps1"
    if not start_script.exists():
        start_script = path / "web" / "start.ps1"
        if not start_script.exists():
            start_script = path / "start.ps1"
            if not start_script.exists():
                raise HTTPException(
                    status_code=400, detail="No valid SOTA entry point found"
                )

    try:
        subprocess.Popen(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(start_script),
            ],
            cwd=str(path),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return models.FleetLaunchResponse(
            success=True, message=f"Launched {path.name} successfully"
        )
    except Exception as e:
        logger.error(f"Failed to launch {path.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
