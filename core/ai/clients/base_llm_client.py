

from typing import Any, Dict, List

from utils.retries import retry_io
from utils.sanitizer import sanitize_text, sanitize_metadata


class BaseLLMClient:
    """Abstract LLM client with retry/backoff and safety sanitization."""

    #model: str = "gpt-4o-mini"  # placeholder; overridden by concrete client
    model: str = "gpt-3.5-turbo"
    timeout_seconds: int = 20

    @retry_io()
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        safe_messages = [
            {"role": m["role"], "content": sanitize_text(m["content"])} for m in messages
        ]
        return self._do_generate(safe_messages, **kwargs)

    def _do_generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        raise NotImplementedError
