import logging

logger = logging.getLogger("my_app.router.admin")


from fastapi import APIRouter
from infrastructure.chroma_admin.stats_service import ChromaStatsService
from api.v1.schemas.response_schemas import StandardResponse

router = APIRouter(prefix="/admin/chroma", tags=["admin"])
stats = ChromaStatsService()

@router.get("/status/{tenant_id}", response_model=StandardResponse)
def get_chroma_status(tenant_id: str):
    """Check status for a single tenant (user)"""

    logger.debug(f"Requesting Chroma status for tenant: {tenant_id}")
    data = stats.get_status(tenant_id)
    return StandardResponse(
        status="success",
        message="Chroma status retrieved successfully",
        data=data
    )

@router.get("/status")
def get_all_chroma_status():
    """Check status for ALL tenants (all users)"""
    return stats.get_all_status()
