from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from .auth import authenticate
from .ai import ai_router


def setup_webapp(app: FastAPI, mcp_app=None):
    """Setup static files and API endpoints for the web interface."""

    # Static files (the React build)
    # Standard location: web_sota/dist relative to project root
    static_dir = Path(__file__).parent.parent.parent / "webapp" / "dist"

    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    @app.get("/api/tools", dependencies=[Depends(authenticate)])
    async def list_tools():
        """List available MCP tools."""
        if not mcp_app:
            return {"tools": []}
        return {"tools": [t.name for t in mcp_app.list_tools()]}

    @app.post("/api/chat", dependencies=[Depends(authenticate)])
    async def chat(request: dict):
        """Chat with Local LLM."""
        messages = request.get("messages", [])
        response = await ai_router.chat_with_llm(messages)
        return {"response": response}
