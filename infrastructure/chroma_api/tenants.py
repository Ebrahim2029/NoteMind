# infrastructure/chroma_api/tenants.py
import logging
logger = logging.getLogger("my_app.chroma_api.tenants")
from .base import ChromaBaseClient

class TenantClient(ChromaBaseClient):
    def create(self, name: str):
        path = self._build_path("tenants")
        return self._request("POST", path, json={"name": name})

    def get(self, tenant: str):
        path = self._build_path("tenants", tenant)
        return self._request("GET", path)
        

    def update(self, tenant: str, resource_name: str):
        path = self._build_path("tenants", tenant)
        return self._request("PATCH", path, json={"resource_name": resource_name})
    def delete(self, tenant: str):
        path = self._build_path("tenants", tenant)
        return self._request("DELETE", path)
