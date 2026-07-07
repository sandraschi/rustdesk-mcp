import time
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from .auth import authenticate
from .ai import ai_router

_START_TIME = time.time()


def setup_webapp(app: FastAPI, mcp_app=None):
    """Setup static files and API endpoints for the web interface."""

    static_dir = Path(__file__).parent.parent.parent / "webapp" / "dist"

    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    @app.get("/api/tools", dependencies=[Depends(authenticate)])
    async def list_tools():
        if not mcp_app:
            return {"tools": []}
        tools = mcp_app.list_tools()
        return {"tools": [{"name": t.name, "description": getattr(t, "description", "")} for t in tools]}

    @app.post("/api/ai/chat")
    async def ai_chat(request: dict):
        messages = request.get("context", {}).get("history", [])
        system_prompt = request.get("system_prompt", "")
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        response = await ai_router.chat_with_llm(messages)
        return {"reply": response}

    @app.post("/api/ai/chat/stream")
    async def ai_chat_stream(request: dict):
        messages = request.get("context", {}).get("history", [])
        system_prompt = request.get("system_prompt", "")
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        return StreamingResponse(ai_router.chat_stream(messages), media_type="text/event-stream")

    @app.get("/api/skills", dependencies=[Depends(authenticate)])
    async def list_skills():
        skills_dir = Path(__file__).parent / "skills"
        if not skills_dir.exists():
            return {"skills": []}
        skills = []
        for item in skills_dir.iterdir():
            if item.is_dir():
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    skills.append({"name": item.name, "path": str(skill_md)})
        return {"skills": skills}

    @app.get("/api/skills/{skill_name}", dependencies=[Depends(authenticate)])
    async def get_skill(skill_name: str):
        skill_path = Path(__file__).parent / "skills" / skill_name / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return "not found"

    @app.get("/api/llm/discover", dependencies=[Depends(authenticate)])
    async def discover_llm():
        import aiohttp
        providers = {}
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get("http://127.0.0.1:11434/api/tags", timeout=aiohttp.ClientTimeout(total=2)) as r:
                        if r.status == 200:
                            data = await r.json()
                            providers["ollama"] = {"status": "available", "models": [m.get("name", "") for m in data.get("models", [])][:5]}
                except Exception:
                    providers["ollama"] = {"status": "unreachable"}
                try:
                    async with session.get("http://127.0.0.1:1234/v1/models", timeout=aiohttp.ClientTimeout(total=2)) as r:
                        if r.status == 200:
                            providers["lmstudio"] = {"status": "available"}
                except Exception:
                    providers["lmstudio"] = {"status": "unreachable"}
        except Exception:
            providers["error"] = "discovery failed"
        return {"providers": providers, "provider": "ollama" if providers.get("ollama", {}).get("status") == "available" else None}

    @app.get("/api/health")
    async def enhanced_health():
        tool_count = len(mcp_app.list_tools()) if mcp_app else 0
        return {
            "status": "ok",
            "server": "rustdesk-mcp",
            "version": "0.1.0",
            "uptime_seconds": int(time.time() - _START_TIME),
            "tool_count": tool_count,
        }
