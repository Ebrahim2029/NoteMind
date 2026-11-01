# infrastructure/chroma_admin/stats_service.py

import logging

logger = logging.getLogger("my_app.chroma_admin.stats_service")

from infrastructure.chroma_admin.monitor import ChromaMonitor
from core.repositories.user_repository import UserRepository  # assuming you have this
from infrastructure.database import SessionLocal

class ChromaStatsService:
    def __init__(self, base_url="http://chroma_note_main:8000"):
        self.session = SessionLocal()
        self.monitor = ChromaMonitor(base_url)
        self.user_repo = UserRepository(self.session)

    def get_status(self, tenant: str):
        """Get Chroma stats for one tenant"""
        logger.debug(f"[ChromaStats] Getting status for tenant={tenant}")
        return self.monitor.status_overview(tenant)

    def get_all_status(self):
        """Get Chroma stats for ALL tenants (all users in DB)"""
        overview = {}
        users = self.user_repo.list_all_users()  # you may need to adapt: select all user_ids
        for user in users:
            tenant_id = str(user["id"])
            try:
                overview[tenant_id] = self.monitor.status_overview(tenant_id)
            except Exception as e:
                logger.error(f"[ChromaStats] Failed to get status for tenant={tenant_id}: {e}")
                overview[tenant_id] = {"error": str(e)}
        return overview
