# infrastructure/chroma_api/collections.py
import logging
logger = logging.getLogger("my_app.chroma_api.collections")

from .base import ChromaBaseClient

class CollectionClient(ChromaBaseClient):
    def list(self, tenant: str, db: str):
        path = self._build_path("tenants", tenant, "databases", db, "collections")
        return self._request("GET", path)

    def create(self, tenant: str, db: str, name: str, metadata: dict | None = None, get_or_create: bool = True):
        path = self._build_path("tenants", tenant, "databases", db, "collections")
        payload = {"name": name, "get_or_create": get_or_create}
        if metadata is not None: payload["metadata"] = metadata
        payload["configuration"] = {
            "hnsw": {
                "space": "cosine",
                "ef_construction": 200,
                "ef_search": 64,
                "max_neighbors": 32,
                "resize_factor": 1.2,
                "sync_threshold": 5000,
            }
        }

        logger.info(f"[CollectionClient] collection path: {path}")
        logger.info(f"[CollectionClient] collection payload: {payload}")
        return self._request("POST", path, json=payload)

    def get(self, tenant: str, db: str, coll_id: str):
        path = self._build_path("tenants", tenant, "databases", db, "collections", coll_id)
        return self._request("GET", path)

    def update(self, tenant: str, db: str, coll_id: str, new_name: str | None = None, new_metadata: dict | None = None):
        path = self._build_path("tenants", tenant, "databases", db, "collections", coll_id)
        payload = {"new_name": new_name, "new_metadata": new_metadata}
        return self._request("PUT", path, json=payload)

    def delete(self, tenant: str, db: str, coll_id: str):
        path = self._build_path("tenants", tenant, "databases", db, "collections", coll_id)
        return self._request("DELETE", path)

    def count(self, tenant: str, db: str, coll_id: str):
        path = self._build_path("tenants", tenant, "databases", db, "collections", coll_id, "count")
        return self._request("GET", path)

    def retrieve_collectionID(self, tenant_id: str, db_name: str, collection_name: str) -> str:
        """Make sure a collection exists, return its ID"""
        payload = self.get(tenant_id, db_name, collection_name)
        collection_id = payload["id"]
        return collection_id