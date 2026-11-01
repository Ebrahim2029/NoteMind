# infrastructure/chroma_admin/monitor.py
import logging
logger = logging.getLogger("my_app.chroma_admin.monitor")
from infrastructure.chroma_api.tenants import TenantClient
from infrastructure.chroma_api.databases import DatabaseClient
from infrastructure.chroma_api.collections import CollectionClient
from infrastructure.chroma_api.base import ChromaBaseClient

class ChromaMonitor:
    def __init__(self, base_url="http://chroma_note_main:8000"):
        self.base_url = base_url

        # If you want proxy bypass here:
        self.chroma = ChromaBaseClient(base_url, bypass_proxy=True)

        # ✅ these clients should get the base_url string, not the ChromaBaseClient instance
        self.tenants = TenantClient(self.base_url)
        self.databases = DatabaseClient(self.base_url)
        self.collections = CollectionClient(self.base_url)
    def get_tenant(self, tenant: str):
        """Check if tenant exists"""
        return self.tenants.get(tenant)

    def list_databases(self, tenant: str):
        return self.databases.list(tenant)

    def list_collections(self, tenant: str, db: str):
        return self.collections.list(tenant, db)

    def collection_count(self, tenant: str, db: str, coll_id: str):
        return self.collections.count(tenant, db, coll_id)

    def status_overview(self, tenant: str):
        """Returns databases → collections → counts for one tenant"""
        overview = {}
        try:
            self.get_tenant(tenant)  # validate exists
        except Exception:
            logger.warning(f"[ChromaMonitor] Tenant {tenant} not found")
            return {False}

        dbs = self.list_databases(tenant)
        if not dbs:
            logger.debug(f"[ChromaMonitor] No databases found for tenant={tenant}")
            return {False}
        for d in dbs:
            dname = d.get("name")
            overview[dname] = {}
            colls = self.list_collections(tenant, dname)
            for c in colls:
                cname = c.get("name")
                cid = c.get("id")
                try:
                    cnt = self.collection_count(tenant, dname, cid)
                except Exception as e:
                    logger.error(f"[ChromaMonitor] Failed to count docs: {e}")
                    cnt = "error"
                overview[dname][cname] = cnt
        return overview
