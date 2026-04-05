import os
import httpx
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger(__name__)


class AIRouter:
    """Standardized AI router for rustdesk-mcp."""

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "ollama")
        self.endpoint = os.getenv("AI_ENDPOINT", "http://localhost:11434")
        self.model = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")

    async def chat_with_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call the configured LLM provider."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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

                # Add LM Studio / OpenAI compatible patterns here if needed
                return f"[MOCK] Provider {self.provider} not fully integrated yet."
        except Exception as e:
            logger.error(f"AI call failed: {str(e)}")
            return f"Error: {str(e)}"


ai_router = AIRouter()
