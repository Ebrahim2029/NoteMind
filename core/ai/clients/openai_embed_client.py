# core/ai/clients/openai_embed_client.py
import logging
logger = logger = logging.getLogger("my_app.core.ai.clients.openai_embed_client")
import time, logging, os
from utils.retries import retry_io
from utils.sanitizer import sanitize_text
from openai import OpenAI


DEFAULT_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

class OpenAIEmbedClient:
    def __init__(self, model: str | None = None):
        self.model = model or DEFAULT_EMBED_MODEL
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        self._client = OpenAI(api_key=api_key)

    @retry_io()  # ✅ no keyword args
    def embed(self, texts: list[str], meta: dict | None = None) -> list[list[float]]:
        safe_texts = [sanitize_text(t) for t in texts]
        try:
            logger.info(
                f"[OpenAIEmbed] Request: n_texts={len(safe_texts)}, "
                f"total_len={sum(len(t) for t in safe_texts)}, meta={meta}"
            )
            t0 = time.perf_counter()
            resp = self._client.embeddings.create(model=self.model, input=safe_texts)
            elapsed = (time.perf_counter() - t0) * 1000
            vecs = [item.embedding for item in resp.data]
            logger.info(
                f"[OpenAIEmbed] Response: vectors={len(vecs)}, "
                f"dim={len(vecs[0]) if vecs else 0}, latency={elapsed:.2f}ms"
            )
            return vecs
        except Exception as e:
            logger.error(f"[OpenAIEmbed] Error: {e}, meta={meta}", exc_info=True)
            return []
