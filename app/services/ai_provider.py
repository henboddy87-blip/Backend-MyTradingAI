import json
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.config import settings
from app.core.logging import logger

class AIProvider(ABC):
    @abstractmethod
    async def generate_response(self, system_prompt: str, user_prompt: str, json_mode: bool = True) -> str:
        pass

class MockAIProvider(AIProvider):
    """
    Local mock AI provider for rapid development and testing.
    Generates intelligent responses deterministically based on input parameters.
    """
    async def generate_response(self, system_prompt: str, user_prompt: str, json_mode: bool = True) -> str:
        # In mock mode, the AI council service handles the structured synthesis
        return "{}"

class OpenAICompatibleProvider(AIProvider):
    """
    OpenAI-compatible AI provider (OpenAI, DeepSeek, LocalLLM/vLLM, Groq, Ollama)
    """
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_BASE_URL.rstrip('/')
        self.model = settings.AI_MODEL

    async def generate_response(self, system_prompt: str, user_prompt: str, json_mode: bool = True) -> str:
        if not self.api_key:
            logger.warning("AI_API_KEY is not set. Falling back to internal analysis engine.")
            return "{}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content
        except Exception as e:
            logger.error(f"Error calling AI Provider: {e}")
            return "{}"

def get_ai_provider() -> AIProvider:
    if settings.AI_PROVIDER.lower() == "openai" and settings.AI_API_KEY:
        return OpenAICompatibleProvider()
    return MockAIProvider()
