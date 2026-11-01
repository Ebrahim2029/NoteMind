

import os
from typing import Dict, List

from openai import OpenAI
from core.ai.clients.base_llm_client import BaseLLMClient
from utils.retries import retry_io


class OpenAIClient(BaseLLMClient):
    """OpenAI Chat Completions integration with retries."""

    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # default if env not set
    api_key: str | None = os.getenv("OPENAI_API_KEY")

    def __init__(self) -> None:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment.")
        self.client = OpenAI(api_key=self.api_key)

    @retry_io()
    def _do_generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Calls OpenAI Chat Completions API.

        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
            kwargs: additional parameters like temperature, max_tokens, etc.

        Returns:
            Assistant response string.
        """
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 512),
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            # Surface errors for debugging/logging
            raise RuntimeError(f"OpenAIClient error: {e}") from e
