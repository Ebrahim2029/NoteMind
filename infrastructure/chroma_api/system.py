# infrastructure/chroma_api/system.py
import logging
logger = logging.getLogger("my_app.chroma_api.system")
from .base import ChromaBaseClient

class SystemClient(ChromaBaseClient):
    def identity(self):
        return self._request("GET", self._build_path("auth", "identity"))

    def healthcheck(self):
        return self._request("GET", self._build_path("healthcheck"))

    def heartbeat(self):
        return self._request("GET", self._build_path("heartbeat"))

    def preflight(self):
        return self._request("GET", self._build_path("pre-flight-checks"))

    def reset(self):
        return self._request("POST", self._build_path("reset"))

    def version(self):
        return self._request("GET", self._build_path("version"))
