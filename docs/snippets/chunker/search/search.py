

import logging
logger = logging.getLogger("search")  

import os
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from openai import embeddings
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.v1.deps import requires_role, get_db
from core.ai.clients.base_embed_client import BaseEmbedClient
from core.ai.clients.chroma_client import ChromaClient
from core.ai.clients.openai_client import OpenAIClient
from core.ai.clients.openai_embed_client import OpenAIEmbedClient
from core.ai.retrieval.pipeline import RetrievalPipeline, assemble_prompt
from core.repositories.note_repository import NoteRepository
from core.services.session_service import SessionService
from utils.intents import extract_intent
from infrastructure.cache import redis_client
from utils.cache_keys import search_key, DEFAULT_TTL_SECONDS

router = APIRouter(prefix="/api/v1/search", tags=["search"])


class SearchRequest(BaseModel):
    user_id: str
    question: str
    session_id: Optional[str] = None


class SearchResponse(BaseModel):
    answer: str
    notes: List[Dict[str, str]] = []


@router.post("", response_model=SearchResponse, dependencies=[Depends(requires_role("user"))])
def search(req: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    # Embeddings client
    embed_client = OpenAIEmbedClient()
    chroma_client = ChromaClient()
    retrieval = RetrievalPipeline(embed_client=embed_client, chroma=chroma_client)
    llm = OpenAIClient()
    notes_repo = NoteRepository(db)
    session = SessionService()

    # Record user message in session (if provided)
    if req.session_id:
        session.add_message(req.session_id, "user", req.question)
        session.add_intent(req.session_id, extract_intent(req.question))

    # Cache check
    key = search_key(req.user_id, req.question)
    cached = redis_client.get(key)
    if cached:
        # Also record assistant answer in history for continuity
        if req.session_id:
            session.add_message(req.session_id, "assistant", cached)
        return SearchResponse(answer=cached)
    
    # embeddings = embed_client.embed([req.question])
    # if not embeddings or not isinstance(embeddings, list):
    #     return SearchResponse(answer="Failed to generate embeddings for the question.", notes=[])
    # [q_emb] = embeddings

    # raw_pairs = ChromaClient().query(q_emb, top_k=10)
    # candidate_ids: List[str] = [nid for nid, _ in raw_pairs]
    # try:
    #     uuids = [UUID(x) for x in candidate_ids]
    # except Exception:
    #     uuids = []
    # meta_lookup = notes_repo.get_meta_lookup(uuids)


    # Retrieve top and touch last_accessed
    #top_ids = retrieval.retrieve_top(req.question, meta_lookup, user_id=req.user_id)
    # 🚨 If no notes found → return directly


    #  Retrieval via pipeline, with tenant=user_id
    meta_lookup = notes_repo.get_meta_lookup([])
    top_ids = retrieval.retrieve_top(req.question, meta_lookup, tenant_id=req.user_id)

    if not top_ids:
        return SearchResponse(answer="Notes not found to answer this question.")
    
    for nid in top_ids:
        try:
            notes_repo.touch_accessed(UUID(nid))
        except Exception:
            pass

     # Hydrate metadata
    notes = [meta_lookup.get(i, {"title": f"Note {i}", "content": ""}) for i in top_ids]

    # Build prompt with session memory
    history = session.get_history(req.session_id) if req.session_id else []
    intents = session.get_recent_intents(req.session_id) if req.session_id else []
    prompt = assemble_prompt(req.question, notes, history=history, intents=intents)

    # Log prompt assembly and check for failure
    if not prompt:
        logger.info(f"[AssemblePrompt] Final prompt for user={req.user_id}: \n{prompt}")
        logger.warning(f"[AssemblePrompt] Failed to assemble prompt for user={req.user_id}")
        return SearchResponse(answer="Failed to generate prompt.", notes=[])
    
    answer = llm.generate(
        [{"role": "system", "content": "You are a helpful notes assistant."},
         {"role": "user", "content": prompt}]
    )

    # Persist
    redis_client.setex(key, DEFAULT_TTL_SECONDS, answer)
    if req.session_id:
        session.add_message(req.session_id, "assistant", answer)

    return SearchResponse(answer=answer, notes=notes)
