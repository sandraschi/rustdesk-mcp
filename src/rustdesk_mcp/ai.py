import json as _json
import os
import httpx
import structlog
from typing import List, Dict, Any, Optional
from fastapi.responses import StreamingResponse

logger = structlog.get_logger(__name__)


class AIRouter:
    """Standardized AI router for rustdesk-mcp."""

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "ollama")
        self.endpoint = os.getenv("AI_ENDPOINT", "http://localhost:11434")
        self.model = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")

    async def chat_with_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call the configured LLM provider (non-streaming)."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if self.provider == "ollama":
                    response = await client.post(
                        f"{self.endpoint}/api/chat",
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": False,
                        },
                    )
                    return response.json()["message"]["content"]
                return f"[MOCK] Provider {self.provider} not fully integrated yet."
        except Exception as e:
            logger.error(f"AI call failed: {str(e)}")
            return f"Error: {str(e)}"

    async def chat_stream(self, messages: List[Dict[str, str]]):
        """Streaming response from the configured LLM provider."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if self.provider == "ollama":
                    async with client.stream(
                        "POST",
                        f"{self.endpoint}/api/chat",
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": True,
                        },
                    ) as response:
                        async for line in response.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                data = _json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except (_json.JSONDecodeError, KeyError):
                                pass
                else:
                    yield f"Provider {self.provider} streaming not configured."
        except Exception as e:
            logger.error(f"AI stream failed: {str(e)}")
            yield f"Error: {str(e)}"


ai_router = AIRouter()
