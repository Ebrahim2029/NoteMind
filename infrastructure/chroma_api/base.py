# infrastructure/chroma_api/base.py
import logging
logger = logging.getLogger("my_app.chroma_api.base")

import os, requests
from typing import Any, Dict

from ..exceptions.chroma_exceptions import ChromaRequestError

class ChromaBaseClient:
    def __init__(self, base_url: str | None = None, token: str | None = None, bypass_proxy: bool = False):
        self.base_url = (base_url or os.getenv("CHROMA_HTTP_URL")).rstrip("/")
        self.api_prefix = "/api/v2"   
        self.token = token or os.getenv("CHROMA_API_TOKEN")
        self.bypass_proxy = bypass_proxy

    def _build_path(self, *parts: str) -> str:
        """Helper to join API prefix + dynamic path parts safely"""
        # Filter out empty/whitespace-only parts and strip slashes
        clean_parts = [str(p).strip("/") for p in parts if str(p).strip()]
        
        # Build the path safely
        if clean_parts:
            path = f"{self.api_prefix.rstrip('/')}/{'/'.join(clean_parts)}"
        else:
            path = self.api_prefix.rstrip('/') + "/"
        
        logger.debug(f"[ChromaBaseClient] Build path: {path}")
        return path

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["x-chroma-token"] = self.token                                                                                                                                      
        return headers

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        logger.info(f"[ChromaAPI] {method} {url}")
        if self.bypass_proxy:
            kwargs["proxies"] = {"http": None, "https": None}

        resp = None
        try:
            # if kwargs.get("json"):
            #     logger.debug(f"[ChromaAPI] Request payload to {url}: {len(kwargs['json']['query_embeddings'][0])} dimensions")
            resp = requests.request(method, url, headers=self._headers(), timeout=10, **kwargs)

            logger.info(f"[ChromaAPI] {method} {url} response: {resp}")

            resp.raise_for_status()
            if resp.text.strip():
                logger.debug(f"[ChromaAPI] {resp.status_code} {resp.text}")
                return resp.json()
            return None
        except requests.HTTPError as e:
            if resp is not None:
                detail = resp.text
                logger.error(f"[ChromaAPI] {method} {url} failed: {resp.status_code} {detail}")
                logger.error(f"[ChromaAPI] Request payload: {kwargs.get('json', {})}")
                raise ChromaRequestError(f"{resp.status_code} {detail}") from e
            raise
        except ChromaRequestError as e:
            logger.error(f"[ChromaAPI] Request error {url}: {e}", exc_info=True)
            raise ChromaRequestError(f"Request error {url}: {e}") from e

