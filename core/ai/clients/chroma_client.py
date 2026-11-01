"""
ChromaClient wrapper (high-level).
Delegates to infrastructure/chroma_api clients for REST calls.
"""
import logging

from infrastructure import database
logger = logging.getLogger("chroma_client")

import os
from typing import Iterable, List, Tuple

from infrastructure.chroma_api.tenants import TenantClient
from infrastructure.chroma_api.databases import DatabaseClient
from infrastructure.chroma_api.collections import CollectionClient
from infrastructure.chroma_api.records import RecordClient
from infrastructure.chroma_api.system import SystemClient
from infrastructure.exceptions.chroma_exceptions import(
    ChromaRequestError,
    ChromaTenantAPIError,
    ChromaDatabaseAPIError,
    ChromaCollectionAPIError,
    ChromaRecordAPIError,
    ChromaSystemAPIError
)


class ChromaClient:
    def __init__(
        self,
        base_url: str | None = None,
        tenant_id: str | None = None,
        database_name: str | None = None,
    ):
        self.base_url = base_url

        # Low-level API clients
        self.tenants = TenantClient(self.base_url)
        self.databases = DatabaseClient(self.base_url)
        self.collections = CollectionClient(self.base_url)
        self.records = RecordClient(self.base_url)
        self.system = SystemClient(self.base_url)

    # -------------------- Helpers --------------------
    def _ensure_collection(self, tenant_id: str, db_name: str, collection_name: str) -> str:
        """Make sure a collection exists, return its ID"""
        logger.debug(f"[ChromaClient] Ensuring collection {collection_name} in {tenant_id}/{db_name}")
        payload = self.collections.get(tenant_id, db_name, collection_name)
        logger.debug(f"[ChromaClient] Ensured collection {collection_name} in {tenant_id}/{db_name}: {payload}")
        collection_id = payload["id"]
        return collection_id

    # -------------------- Public API --------------------
    def upsert(
        self,
        tenant_id: str,
        db_name: str,
        collection_name: str,
        documents: List[dict],
        note_ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[dict],
    ):
        


        if not note_ids or len(note_ids) != len(embeddings) or len(note_ids) != len(metadatas):
            logger.error(f"[ChromaClient] Invalid upsert lengths note_ids={len(note_ids)} embeddings={len(embeddings)} metadatas={len(metadatas)}")
            return 
        
        try:
            collection_id = self.collections.retrieve_collectionID(tenant_id, db_name, collection_name)
            logger.debug(f"[ChromaClient] upsert: collection_id:  {collection_id}")
            logger.info(
                f"[ChromaClient] Upserting {len(note_ids)} records into {tenant_id}/{db_name}/{collection_id} "
                f"| note_id={note_ids[0]}, metadatas_len={metadatas[0]}"
            )
            return self.records.upsert(tenant_id, db_name, collection_id, note_ids, embeddings, metadatas, documents)
            #logger.debug(f"[ChromaClient] collection_id:  {collection_id}")
            #return
        except ChromaRequestError as e:
            logger.error(
                f"[ChromaClient] Upsert failed tenant={tenant_id} db={db_name} coll={collection_id}: {e}",
                exc_info=True,
            )

    def delete(self, tenant_id: str, db_name: str, collection_id: str, note_ids: Iterable[str]):
        try:
            coll_id = self.collections.retrieve_collectionID(tenant_id, db_name, collection_id)
            logger.info(f"[ChromaClient] Deleting {len(list(note_ids))} records from {tenant_id}/{db_name}/{collection_id}")
            return self.records.delete(tenant_id, db_name, coll_id, ids=list(note_ids))
        except ChromaRequestError as e:
            logger.error(
                f"[ChromaClient] Delete failed tenant={tenant_id} db={db_name} coll={collection_id}: {e}",
                exc_info=True,
            )

    def query(
        self,
        tenant_id: str,
        db_name: str,
        collection_name: str,
        embedding: List[float],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:

        collection_id = None
        try:
            logger.debug(f"[ChromaClient] tenant_id:  {tenant_id} db_name:  {db_name} collection_name:  {collection_name} ")
            collection_id = self.collections.retrieve_collectionID(tenant_id, db_name, collection_name)
            if not collection_id:
                logger.error(f"[ChromaClient] Collection {collection_name} does not exist in db={db_name}, tenant={tenant_id}")
                return []
            logger.debug(f"[ChromaClient] query: collection_id:  {collection_id}")
            resp = self.records.query(
                tenant_id,
                db_name,
                collection_id,
                query_embeddings=[embedding],
                n_results=top_k,
                include=["distances", "metadatas", "documents"],
            )

            
            ids = resp.get("ids", [[]])[0]
            dists = resp.get("distances", [[]])[0]
            documents = resp.get("documents", [[]])[0]
            metadatas = resp.get("metadatas", [[]])[0]
            # Return tuples with all information
            results = []
            
            for nid, dist, doc, meta in zip(ids, dists, documents, metadatas):
                # Cosine distance → similarity in [0,1]
                similarity_score = 1.0 - (float(dist) / 2.0)
                results.append((nid, similarity_score, doc, meta))
            logger.debug(f"[ChromaClient][query] results: {results}")
            return results
        except ChromaCollectionAPIError as e:
            logger.error(
                f"[ChromaClient] Query failed tenant={tenant_id} db={db_name} coll={collection_id}: {e}",
                exc_info=True,
            )
            return []
        except ChromaRequestError as e:
            logger.error(
                f"[ChromaClient] Unexpected error in query tenant={tenant_id} db={db_name} coll={collection_id}: {e}",
                exc_info=True,
            )
            return []

    # -------------------- System API passthrough --------------------
    def healthcheck(self):
        return self.system.healthcheck()

    def version(self):
        return self.system.version()

    def identity(self):
        return self.system.identity()
