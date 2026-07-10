#!/usr/bin/env python3
"""
Backend Bridge for RustDesk MCP Webapp.
Exposes MCP tools via FastAPI on port 10805.
"""

import logging
import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

from rustdesk_mcp.config import get_config
from rustdesk_mcp.services.rustdesk_service import RustDeskService
from rustdesk_mcp.tools_module import RustDeskTools
from rustdesk_mcp.web import setup_webapp

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rustdesk-web-bridge")

app = FastAPI(title="RustDesk MCP Web Bridge")

# Enable CORS for the webapp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
mcp = None
service = None
tools = None


@app.on_event("startup")
async def startup_event():
    global mcp, service, tools
    config = get_config()

    # Initialize service and tools
    service = RustDeskService(
        rustdesk_path=config.rustdesk_path,
        config_dir=config.rustdesk_config_dir,
        id_server_host=config.rustdesk_id_server_host,
        id_server_port=config.rustdesk_id_server_port,
        relay_server_host=config.rustdesk_relay_server_host,
        relay_server_port=config.rustdesk_relay_server_port,
        api_url=config.rustdesk_api_url,
        api_key=config.rustdesk_api_key,
        api_username=config.rustdesk_api_username,
        api_password=config.rustdesk_api_password,
    )
    tools = RustDeskTools(service)

    # Initialize FastMCP server for tool registration
    mcp = FastMCP(name="RustDesk MCP Server")

    # We don't necessarily need to register tools with MCP here if we just call the service/tools directly,
    # but setup_webapp expects mcp if we want to list tools.
    # Actually, let's just use the setup_webapp function from web.py
    setup_webapp(app, mcp_app=mcp)

    logger.info("RustDesk Web Bridge initialized on port 10805")


@app.get("/api/status")
async def get_status():
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return await service.get_status()


@app.get("/api/detailed-status")
async def get_detailed_status():
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return await service.get_detailed_status()


@app.post("/api/connect")
async def connect(remote_id: str, password: str | None = None):
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return await service.connect_to_peer(remote_id, password)


@app.post("/api/control/{action}")
async def control_action(action: str, body: dict | None = None):
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        if action == "remote_click":
            from rustdesk_mcp.services.advanced_control import AdvancedControlService
            ctrl = AdvancedControlService()
            result = await ctrl.remote_click(
                x=body.get("x", 100) if body else 100,
                y=body.get("y", 100) if body else 100,
            )
            return {"success": True, "action": action, "result": result}
        elif action == "remote_type":
            text = body.get("text", "") if body else ""
            from rustdesk_mcp.services.advanced_control import AdvancedControlService
            ctrl = AdvancedControlService()
            result = await ctrl.remote_type(text)
            return {"success": True, "action": action, "result": result}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    except Exception as e:
        logger.exception(f"Control action {action} failed")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10805)
