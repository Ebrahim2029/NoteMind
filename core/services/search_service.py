import logging
logger = logging.getLogger("my_app.services.search_service")


from datetime import datetime, timezone
from typing import Dict, List

from utils.cache_keys import search_key, DEFAULT_TTL_SECONDS
from utils.sanitizer import sanitize_text
from core.ai.retrieval.pipeline import RetrievalPipeline, assemble_prompt
from core.ai.clients.base_llm_client import BaseLLMClient
from core.ai.clients.openai_embed_client import OpenAIEmbedClient
from core.ai.clients.chroma_client import ChromaClient
from core.ai.clients.openai_client import OpenAIClient
from infrastructure.cache import redis_client
from core.services.session_service import SessionService
from utils.intents import extract_intent
from langdetect import detect 
from app_config import app_settings
from api.v1.deps import get_db
from core.repositories.note_repository import NoteRepository

class SearchService:
    """
    Orchestrates the RAG flow:
    - cache-first on search results
    - embed + chroma query
    - filter threshold >= 0.82
    - rank & take top 3
    - assemble prompt & call LLM
    """

    def __init__(self, user_id: str, notebook_name: str, session_id: str):

        self.user_id = user_id
        self.notebook_name = notebook_name
        self.session_id = session_id
        self.embed_client = OpenAIEmbedClient()
        self.chroma_client = ChromaClient()
        self.llm_client = OpenAIClient()
        self.redis = redis_client
        self.retrieval = RetrievalPipeline(self.embed_client, self.chroma_client)
        self.llm = self.llm_client
    
    def answer(self, question: str, quoted_note_id: str | None = None):
        question = sanitize_text(question)

        # If user quoted a note → direct fetch
        if quoted_note_id:
            logger.info(f"[SearchService] Quoted note {quoted_note_id}, skipping retrieval")
            repo = NoteRepository()
            note = repo.get_by_id(quoted_note_id)
            if not note:
                return "Sorry, I couldn’t find the quoted note.", []
            
            notes = [{
                "id": note.id,
                "score": 1.0,
                "title": note.title,
                "content": note.content,
                "tags": note.tags,
                "is_pinned": note.is_pinned,
                "is_archived": note.is_archived,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "last_accessed_at": note.last_accessed_at,
            }]

            prompt = assemble_prompt(
                question,
                notes,
                history=[],
                intents=[],
            )
            reply = self.llm.generate([
                {"role": "system", "content": "You are NoteMind, a notes assistant. The user explicitly quoted a note below."},
                {"role": "user", "content": prompt},
            ])
            # ✅ persist to session + DB
            if self.session_id:
                session_service = SessionService(self.redis)
                session_service.add_interaction(self.session_id, question, reply)
                session_service.add_notes(self.session_id, notes)
                session_service.add_intent(self.session_id, extract_intent(question))

                try:
                    lang = detect(question)
                except Exception:
                    lang = "unknown"

                session_service.add_context(
                    self.session_id,
                    {"language": lang, "timestamp": datetime.now(timezone.utc).isoformat()},
                )

                db = next(get_db())
                session_service.add_interaction_persistent(
                    db, self.session_id, question, reply, notes, lang, quoted_note_id=quoted_note_id
                )

            return reply, notes

        # ✅ Else → normal retrieval (your existing pipeline)
        return self._answer_with_retrieval(question)


    def _answer_with_retrieval(self, question: str) -> str:
                # Safe Redis key
        question = sanitize_text(question)
        key = search_key(self.user_id, question)

        if self.redis:
            cached = self.redis.get(key)
            
            # If answer question is cached return cached value
            if cached:
                if isinstance(cached, bytes):
                    reply = cached.decode("utf-8")
                else:
                    reply = cached
                logger.info(f"[SearchService] Retrieved cached answer for question: {question}")
                return reply, []   # ✅ always return tuple
                
        threshold = app_settings.RETRIEVAL_THRESHOLD
        # If cache miss, run retrieval
        results = self.retrieval.retrieve_top(
            question,
            self.user_id,
            self.notebook_name,
            threshold=threshold
        )

        
        if not results:
            logger.info(f"[SearchService] No relevant notes found for question: {question}")
            ai_response = "I'm sorry, I couldn't find any relevant notes."
            return ai_response, []

        # Each result already contains id, score, content, extra_metadata
        notes = [
            {
                "id": r["id"],
                "score": r["score"],
                "title": r.get("title"),
                "content": r.get("content"),
                "tags": r.get("tags"),
                "is_pinned": r.get("is_pinned"),
                "is_archived": r.get("is_archived"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "last_accessed_at": r.get("last_accessed_at"),
            }
            for r in results
        ]


        logger.debug(f"[SearchService] Retrieved notes for {self.session_id}")
        # ✅ Session integration
        history, intents, recent_notes, ctx = [], [], [], {}

        if self.session_id:
            session_service = SessionService(self.redis)
            history = session_service.get_history(self.session_id)
            intents = session_service.get_recent_intents(self.session_id)
            recent_notes = session_service.get_recent_notes(self.session_id)
            ctx = session_service.get_context(self.session_id)
            logger.debug(f"[SearchService] Session context for {self.session_id}: {ctx}")
            logger.debug(f"[SearchService] Session history for {self.session_id}: {history}")
            logger.debug(f"[SearchService] Session intents for {self.session_id}: {intents}")
            logger.debug(f"[SearchService] Session recent notes for {self.session_id}: {recent_notes}")

        # Merge current results with previous notes
        all_notes = notes + recent_notes

        logger.debug(f"[SearchService] All notes for prompt assembly: {all_notes}")

        prompt = assemble_prompt(
            question,
            all_notes,
            history=history,
            intents=intents,
        )
        logger.info(f"[SearchService] Generated prompt for LLM:\n{prompt}")

        current_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        reply = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": (
                        "You are NoteMind, an AI assistant that helps users manage and "
                        "reason about their notes.\n\n"
                        "Guidelines:\n"
                        f"- Current system datetime: {current_dt} (use this to interpret appointments, reminders, and time-sensitive data).\n"
                        "- Always respond in the SAME LANGUAGE as the user’s query. Supported: English, Arabic, French, Spanish, Russian.\n"
                        "- Use ONLY the retrieved notes, history, and intents provided.\n"
                        "- Be concise, clear, and structured (bullet points, short paragraphs).\n"
                        "- Respect metadata: pinned = priority, archived = less relevant.\n"
                        "- Do not hallucinate: if information is missing, say you don’t have enough details.\n"
                        "- When referencing dates/times in notes, align them with the current system time."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
        )
        # Cache with default TTL from cache_keys
        if self.redis:
            self.redis.setex(key, DEFAULT_TTL_SECONDS, reply)
        
        
               # Session tracking
        if self.session_id:
            session_service = SessionService(self.redis)
            session_service.add_interaction(self.session_id, question, reply)
            session_service.add_notes(self.session_id, notes)
            session_service.add_intent(self.session_id, extract_intent(question))

            try:
                lang = detect(question)
            except Exception:
                lang = "unknown"
            session_service.add_context(
                self.session_id,
                {"language": lang, "timestamp": datetime.now(timezone.utc).isoformat()},
            )

            # Persist in DB
            db = next(get_db())
            session_service.add_interaction_persistent(
                db, self.session_id, question, reply, results, lang
            )
        return reply, notes

