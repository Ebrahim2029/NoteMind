

import logging
logger = logging.getLogger("search")  

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4

from api.v1.deps import get_db, get_current_user
from core.services.search_service import SearchService


router = APIRouter(prefix="/api/v1/query", tags=["query"])

# ---------- Schemas ----------
from pydantic import BaseModel
from typing import List, Dict, Any


class QueryRequest(BaseModel):
    notebook_id: str
    query: str
    session_id: str | None = None
    quoted_note_id: str | None = None


class QueryResponse(BaseModel):
    query: str
    relevant_notes: List[Dict[str, Any]]
    ai_response: str
    session_id: str
    quoted_note_id: str | None = None


# ---------- Endpoint ----------
@router.post("", response_model=QueryResponse)
def handle_query(
    body: QueryRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    
    if not body.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )
    
    
    
    # Ensure session id (frontend can send or backend creates)
    session_id = body.session_id or str(uuid4())

    # Init services    
    search_service = SearchService(user.sub, body.notebook_id, session_id)
    # session_service = SessionService(redis_client)
    try:
        ai_response, relevant_notes = search_service.answer(body.query, quoted_note_id=body.quoted_note_id)

    except Exception as e:
        logger.error(f"[QueryAPI] SearchService failed for session={session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query",
        )
    # Update session
    # session_service.add_message(session_id, "user", body.query)
    #session_service.add_message(session_id, "assistant", ai_response)

    return QueryResponse(
        query=body.query,
        relevant_notes=relevant_notes,
        ai_response=ai_response,
        session_id=session_id,
    )


