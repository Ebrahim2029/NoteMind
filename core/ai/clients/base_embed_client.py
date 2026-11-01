

from typing import List

from utils.retries import retry_io
from utils.sanitizer import sanitize_text


class BaseEmbedClient:
    """Abstract embeddings client."""

    dim: int = 1536

    @retry_io()
    def embed(self, texts: List[str]) -> List[List[float]]:
        texts = [sanitize_text(t) for t in texts]
        return self._do_embed(texts)

    def _do_embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError
