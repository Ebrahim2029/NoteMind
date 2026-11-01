# infrastructure/chroma_api/databases.py
import logging
logger = logging.getLogger("my_app.chroma_api.databases")
from .base import ChromaBaseClient

class DatabaseClient(ChromaBaseClient):
    def list(self, tenant: str):
        path = self._build_path("tenants", tenant, "databases")
        logger.info(f"[DatabaseClient] list database path: {path}")
        return self._request("GET", path)

    def create(self, tenant: str, name: str):
        path = self._build_path("tenants", tenant, "databases")
        logger.info(f"[DatabaseClient] create database path: {path}")
        return self._request("POST", path, json={"name": name})

    def get(self, tenant: str, db: str):
        path = self._build_path("tenants", tenant, "databases", db)
        logger.info(f"[DatabaseClient] Getting database {db} for tenant {tenant}")
        return self._request("GET", path)

    def delete(self, tenant: str, db: str):
        path = self._build_path("tenants", tenant, "databases", db)
        logger.info(f"[DatabaseClient] Deleting database {db} for tenant {tenant}")
        return self._request("DELETE", path)
