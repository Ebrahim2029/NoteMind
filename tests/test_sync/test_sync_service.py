from __future__ import annotations

from typing import Dict, List

from core.services.sync_service import SyncService
from core.ai.clients.base_embed_client import BaseEmbedClient
from core.ai.clients.chroma_client import ChromaClient


class FakeEmbed(BaseEmbedClient):
    def _do_embed(self, texts: List[str]):
        return [[0.9] * 8 for _ in texts]


class FakeChroma(ChromaClient):
    def __init__(self):
        self.upserts: List[Dict] = []
        self.deletes: List[str] = []

    def upsert(self, ids, embeddings, metadatas):
        for i, m in zip(ids, metadatas):
            self.upserts.append({"id": i, "meta": m})

    def delete(self, ids):
        self.deletes.extend(list(ids))


class FakeRedis:
    def __init__(self):
        self.keys_store: set[str] = set(["search:user-1:abc", "note:123", "chunk:123:1"])

    # Simulate small SCAN
    def scan(self, cursor=0, match: str = "*", count: int = 10):
        matched = [k for k in list(self.keys_store) if _match(k, match)]
        # return all at once
        return 0, matched

    def delete(self, *keys):
        for k in keys:
            if isinstance(k, (bytes, bytearray)):
                k = k.decode()
            self.keys_store.discard(k)


def _match(key: str, pattern: str) -> bool:
    # Very small glob matcher for tests: only supports trailing '*'
    if pattern.endswith("*"):
        return key.startswith(pattern[:-1])
    return key == pattern


def test_sync_service_upsert_and_invalidation():
    chroma = FakeChroma()
    r = FakeRedis()
    svc = SyncService(FakeEmbed(), chroma, redis=r)

    evt = {"op": "create", "note_id": "123", "user_id": "user-1", "title": "T", "content": "C"}
    svc.handle(evt)

    assert chroma.upserts and chroma.upserts[0]["id"] == "123"
    # search user keys should be invalidated
    assert not any(k.startswith("search:user-1:") for k in r.keys_store)


def test_sync_service_delete_and_invalidation():
    chroma = FakeChroma()
    r = FakeRedis()
    svc = SyncService(FakeEmbed(), chroma, redis=r)

    svc.handle({"op": "delete", "note_id": "123", "user_id": "user-1"})
    assert "123" in chroma.deletes
    # note and chunks are purged
    assert "note:123" not in r.keys_store
