

import logging
logger = logging.getLogger("search")  

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4

from api.v1.deps import get_db, get_current_user
from core.services.search_service import SearchService
from core.services.session_service import SessionService
from core.ai.retrieval.pipeline import RetrievalPipeline, assemble_prompt
from core.ai.clients.openai_embed_client import OpenAIEmbedClient
from core.ai.clients.chroma_client import ChromaClient
from core.ai.clients.openai_client import OpenAIClient
from core.repositories.note_repository import NoteRepository
from infrastructure.cache import redis_client

router = APIRouter(prefix="/api/v1/query", tags=["query"])

# ---------- Schemas ----------
from pydantic import BaseModel
from typing import List, Dict, Any


class QueryRequest(BaseModel):
    notebook_id: str
    query: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    query: str
    #relevant_notes: List[Dict[str, Any]]
    #ai_response: str
    session_id: str


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
    
    

    # Ensure session id
    session_id = body.session_id or str(uuid4())

    # Init services
    embed_client = OpenAIEmbedClient()
    chroma_client = ChromaClient()
    llm_client = OpenAIClient()
    pipeline = RetrievalPipeline(embed_client, chroma_client)
    search_service = SearchService(redis_client, pipeline, llm_client)
    session_service = SessionService(redis_client)

    


    # Load note metadata
    note_repo = NoteRepository(db)
    meta_lookup = note_repo.get_meta_lookup([])

    logger.info(f"[Query] meta_lookup: {meta_lookup}")

    #note_ids = [str(n.id.value) for n in db.query(note_repo.db.query(note_repo.db.query).column_descriptions)]  # placeholder
    # Instead of all, we fetch lazily — meta_lookup will be used per candidate
    # Better: meta_lookup built for retrieval candidates
    # So first just prepare empty dict; we’ll hydrate after retrieval
    

    # Run retrieval
    top_ids = pipeline.retrieve_top(body.query, meta_lookup, user.sub, body.notebook_id)
    meta_lookup = note_repo.get_meta_lookup([uuid for uuid in top_ids])
    relevant_notes = [meta_lookup[nid] for nid in top_ids if nid in meta_lookup]

    # # Assemble full prompt with session context
    # history = session_service.get_history(session_id)
    # intents = session_service.get_recent_intents(session_id)
    # prompt = assemble_prompt(body.query, relevant_notes, history, intents)
    # # Log prompt assembly and check for failure
    # if not prompt:
    #     logger.info(f"[AssemblePrompt] Final prompt for user={user.id.value}: \n{prompt}")
    #     logger.warning(f"[AssemblePrompt] Failed to assemble prompt for user={user.id.value}")
    #     return QueryResponse(
    #         query=body.query,
    #         relevant_notes=relevant_notes,
    #         ai_response="Failed to generate prompt.",
    #         session_id=session_id
    #     )

    # # AI response
    # ai_response = llm_client.generate(
    #     [
    #         {"role": "system", "content": "You are a helpful notes assistant."},
    #         {"role": "user", "content": prompt},
    #     ]
    # )

    # # Update session
    # session_service.add_message(session_id, "user", body.query)
    # session_service.add_message(session_id, "assistant", ai_response)

    # return QueryResponse(
    #     query=body.query,
    #     relevant_notes=relevant_notes,
    #     ai_response=ai_response,
    #     session_id=session_id,
    # )

    logger.info(f"[Query] User: {user.sub} username: {user.username} role: {user.roles} exp: {user.exp}")
    return QueryResponse(
            query="hi",
            #relevant_notes=notes,
            #ai_response="Failed to generate prompt.",
            session_id="session_id"
        )
    

    # uuid_list = [
    #     "1a976d94-fdfb-4e06-9674-2eb0b212eb50",
    #     "2ab45d8b-368d-4936-875d-860d9da84e16",
    #     "3f964575-119d-425c-be09-c7663de5b3cb",
    #     "4a6ce1cd-c486-42e7-8f64-9a0c19462214",
    #     "51a7ab38-b250-425c-8780-686029559e77",
    #     "96a099b7-c02c-4eb0-8930-166c4983b29e",
    #     "9d1449a1-aa80-467c-a3f7-ee7bb66439df",
    #     "a70d438d-e097-4aad-adf6-7ee1ce445adb",
    #     "a747a54b-57e9-4cf9-96b9-7b88278d9225",
    #     "ce63107b-7262-48ec-99b5-185f7c553b93",
    #     "f73df045-5b32-4557-a05f-a033ee9486de"
    # ]