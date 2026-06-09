"""
RAG service for NeuroVision educational platform.

Pipeline (explicit, fully traced):
  1. Retrieval  — similarity_search_with_score → top-k chunks + scores
  2. Context    — assemble prompt from retrieved chunks
  3. Generation — LLM call with timing
  4. Return     — ChatResponse + RAGQueryTrace (for background persistence)
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import structlog
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from app.infrastructure.vector_store import VectorStoreService
from app.services.knowledge_base import get_knowledge_documents
from app.domain.models import ChatResponse

logger = structlog.get_logger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""Você é o NeuroVision, um tutor especializado em neuro-oftalmologia para estudantes de medicina e oftalmologistas.

Seu papel é educacional — você explica anatomia, patologias e conexões neurológicas de forma clara, precisa e baseada em evidências.

IMPORTANTE:
- Baseie suas respostas EXCLUSIVAMENTE no contexto fornecido abaixo
- Se a informação não estiver no contexto, diga: "Essa informação não está na minha base de conhecimento atual."
- Sempre mencione a conexão entre o olho e o sistema nervoso central quando relevante
- Use linguagem clara para estudantes, mas precisa para profissionais
- Nunca faça diagnósticos — esta é uma ferramenta educacional
- Estruture respostas longas com subtítulos quando necessário

CONTEXTO DA BASE DE CONHECIMENTO:
{context}

PERGUNTA DO ESTUDANTE:
{question}

RESPOSTA EDUCACIONAL:""",
)


# ── Trace dataclass (internal — never serialized to API) ─────────────────────

@dataclass
class RAGQueryTrace:
    """Full execution trace for one RAG query. Saved to DB as a BackgroundTask."""
    chunks: list[dict] = field(default_factory=list)
    context_sent: str = ""
    retrieval_ms: int = 0
    llm_ms: int = 0
    total_ms: int = 0


# ── Service ───────────────────────────────────────────────────────────────────

class RAGService:
    """
    Retrieval-Augmented Generation service.

    Replaces the opaque RetrievalQA chain with an explicit, timed pipeline
    so every step (retrieval, context assembly, LLM call) is observable.
    """

    def __init__(self, vector_store: VectorStoreService, groq_api_key: str, model: str) -> None:
        self._vector_store = vector_store
        self._groq_api_key = groq_api_key
        self._model = model
        self._llm: Optional[ChatGroq] = None

    def initialize(self) -> None:
        """Ingest knowledge base documents and build the LLM instance."""
        logger.info("rag_service.initializing", model=self._model)

        documents = get_knowledge_documents()
        self._vector_store.ingest_documents(documents)

        self._llm = ChatGroq(
            api_key=self._groq_api_key,
            model=self._model,
            temperature=0.3,
            max_tokens=1024,
        )

        logger.info("rag_service.initialized")

    def query(
        self,
        message: str,
        session_id: Optional[str] = None,
        selected_structure: Optional[str] = None,
    ) -> tuple[ChatResponse, RAGQueryTrace]:
        """
        Execute the RAG pipeline with per-step timing.

        Returns:
            (ChatResponse, RAGQueryTrace) — the public response and the
            internal trace. The caller is responsible for persisting the trace.
        """
        if self._llm is None:
            raise RuntimeError("RAGService not initialized. Call initialize() first.")

        sid = session_id or str(uuid.uuid4())
        trace = RAGQueryTrace()
        t_start = time.perf_counter()

        enriched_query = message
        if selected_structure:
            enriched_query = f"[Estrutura selecionada: {selected_structure}] {message}"

        logger.info(
            "rag_service.query",
            session_id=sid,
            query_length=len(enriched_query),
            structure=selected_structure,
        )

        # ── Step 1: Retrieval (with similarity scores) ────────────────────────
        t_retrieval = time.perf_counter()
        try:
            docs_with_scores = self._vector_store.similarity_search_with_score(
                enriched_query, k=4
            )
        except Exception as e:
            logger.error("rag_service.retrieval_failed", error=str(e))
            raise

        trace.retrieval_ms = int((time.perf_counter() - t_retrieval) * 1000)

        # ── Step 2: Context assembly ──────────────────────────────────────────
        trace.chunks = []
        context_parts: list[str] = []
        sources: set[str] = set()
        related_structures: set[str] = set()

        for doc, score in docs_with_scores:
            source = doc.metadata.get("source", "Literatura médica")
            sources.add(source)

            structure = doc.metadata.get("structure", "")
            if structure:
                related_structures.add(structure)

            # Normalize score: ChromaDB returns L2 distance for normalized
            # vectors; lower = more similar. Convert to 0–1 similarity.
            # With normalize_embeddings=True: similarity ≈ 1 - (score / 2)
            similarity = round(max(0.0, 1.0 - score / 2.0), 4)

            trace.chunks.append({
                "source": source,
                "similarity_score": similarity,
                "content_snippet": doc.page_content[:300],
            })
            context_parts.append(doc.page_content)

        trace.context_sent = "\n\n---\n\n".join(context_parts)
        prompt_text = _PROMPT.format(context=trace.context_sent, question=enriched_query)

        # ── Step 3: LLM generation ────────────────────────────────────────────
        t_llm = time.perf_counter()
        try:
            llm_response = self._llm.invoke([HumanMessage(content=prompt_text)])
        except Exception as e:
            logger.error("rag_service.llm_failed", error=str(e))
            raise

        trace.llm_ms = int((time.perf_counter() - t_llm) * 1000)
        trace.total_ms = int((time.perf_counter() - t_start) * 1000)

        answer = llm_response.content if hasattr(llm_response, "content") else str(llm_response)

        logger.info(
            "rag_service.query_complete",
            session_id=sid,
            retrieval_ms=trace.retrieval_ms,
            llm_ms=trace.llm_ms,
            total_ms=trace.total_ms,
            chunks=len(trace.chunks),
            avg_similarity=round(
                sum(c["similarity_score"] for c in trace.chunks) / len(trace.chunks), 3
            ) if trace.chunks else 0,
        )

        response = ChatResponse(
            answer=answer,
            sources=sorted(sources),
            related_structures=sorted(related_structures),
            session_id=sid,
        )
        return response, trace

    @property
    def is_ready(self) -> bool:
        return self._llm is not None
