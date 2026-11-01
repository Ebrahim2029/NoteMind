# infrastructure/chroma_api/records.py
import logging
logger = logging.getLogger("my_app.infra.chroma_api.records")


from .base import ChromaBaseClient

class RecordClient(ChromaBaseClient):
    def upsert(self, tenant, db, coll_id, ids, embeddings, metadatas=None, documents=None):
        path = self._build_path("tenants", tenant, "databases", db, "collections", coll_id, "upsert")
        payload = {"ids": ids, "embeddings": embeddings}
        if metadatas: payload["metadatas"] = metadatas
        if documents: payload["documents"] = documents
        return self._request("POST", path, json=payload)

    def query(self, tenant_id, db_name, collection_id, query_embeddings, n_results=5, include=None):
        path = self._build_path("tenants", tenant_id, "databases", db_name, "collections", collection_id, "query")
        payload = {"query_embeddings": query_embeddings, "n_results": n_results, "include": include or ["distances", "metadatas", "documents"]}
        return self._request("POST", path, json=payload)

    def delete(self, tenant_id, db_name, collection_id, ids=None, where=None):
        path = self._build_path("tenants", tenant_id, "databases", db_name, "collections", collection_id, "delete")
        payload = {"ids": ids, "where": where}
        return self._request("POST", path, json=payload)

    def get(self, tenant_id, db_name, collection_id, ids=None, where=None, limit=10):
        path = self._build_path("tenants", tenant_id, "databases", db_name, "collections", collection_id, "get")
        payload = {"ids": ids, "where": where, "limit": limit}
        return self._request("POST", path, json=payload)
