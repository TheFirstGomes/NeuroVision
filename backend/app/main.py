"""
NeuroVision — FastAPI application entrypoint.
Neuro-ophthalmology educational platform backend.
"""
import structlog
from contextlib import asynccontextmanager
from typing import AsyncIterator

from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.domain.models import (
    ChatRequest,
    ChatResponse,
    AnatomyResponse,
    ClassificationResponse,
    EvaluationStats,
    HealthResponse,
    ClinicalCase,
    CaseListItem,
    SessionHistoryResponse,
    SessionMessage,
    RAGTrace,
    RAGChunk,
    RAGTraceStats,
)
from app.infrastructure import database as db
from app.infrastructure.security import sanitize_filename, validate_image, validate_pdf
from app.infrastructure.vector_store import VectorStoreService
from app.services.evaluation_service import EvaluationService
from app.services.rag_service import RAGService
from app.services.ingestion_service import IngestionService
from app.services.classifier_service import ClassifierService
from app.services.anatomy_service import get_anatomy_structure, list_structures
from app.services.cases_service import list_cases, get_case

logger = structlog.get_logger(__name__)


# ── Settings ──────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    allowed_origins: str = "http://localhost:3000"
    anthropic_api_key: str = ""   # Optional — enables Claude Vision classifier
    cnn_model_path: str = ""      # Optional — path to ONNX model; defaults to backend/models/

    class Config:
        env_file = ".env"


settings = Settings()

# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# ── App State ─────────────────────────────────────────────────────────────────

vector_store = VectorStoreService()
rag_service = RAGService(
    vector_store=vector_store,
    groq_api_key=settings.groq_api_key,
    model=settings.groq_model,
)
ingestion_service = IngestionService(vector_store=vector_store)
classifier_service = ClassifierService(
    anthropic_api_key=settings.anthropic_api_key or None,
    cnn_model_path=settings.cnn_model_path or None,
)
evaluation_service = EvaluationService(
    groq_api_key=settings.groq_api_key,
    model=settings.groq_model,
)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("neurovision.startup")

    db.init_db()
    vector_store.initialize()
    rag_service.initialize()

    logger.info("neurovision.ready")
    yield

    logger.info("neurovision.shutdown")


# ── FastAPI ───────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NeuroVision API",
    description="Neuro-ophthalmology educational platform — RAG-powered chat and 3D anatomy",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── System ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """System health and readiness check."""
    return HealthResponse(
        status="healthy" if rag_service.is_ready else "initializing",
        rag_ready=rag_service.is_ready,
        model=settings.groq_model,
        version="2.0.0",
    )


# ── Education ─────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse, tags=["Education"])
@limiter.limit("30/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    """
    Educational RAG chat endpoint.
    Answers neuro-ophthalmology questions based on peer-reviewed literature.
    Rate limit: 30 requests/minute per IP.
    """
    if not rag_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is still initializing. Please retry in a few seconds.",
        )

    logger.info("chat.request", message_length=len(body.message), structure=body.structure)

    try:
        response, trace = rag_service.query(
            message=body.message,
            session_id=body.session_id,
            selected_structure=body.structure,
        )
    except Exception as e:
        logger.error("chat.error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar a pergunta. Tente novamente.",
        )

    # Persist messages in background
    background_tasks.add_task(db.add_message, response.session_id, "user", body.message)
    background_tasks.add_task(
        db.add_message,
        response.session_id,
        "assistant",
        response.answer,
        response.sources,
        response.related_structures,
    )

    # Persist full RAG trace in background
    background_tasks.add_task(
        db.add_trace,
        response.session_id,
        body.message,
        trace.chunks,
        trace.context_sent,
        response.answer,
        trace.retrieval_ms,
        trace.llm_ms,
        trace.total_ms,
    )

    # LLM-as-judge evaluation in background — now uses actual chunks
    background_tasks.add_task(
        evaluation_service.evaluate,
        response.session_id,
        body.message,
        response.answer,
        trace.chunks,
    )

    return response


# ── Anatomy ───────────────────────────────────────────────────────────────────

@app.get("/anatomy", tags=["Anatomy"])
async def list_anatomy_structures() -> list[dict]:
    """Lists all available anatomical structures for the 3D viewer."""
    return list_structures()


@app.get("/anatomy/{structure_id}", response_model=AnatomyResponse, tags=["Anatomy"])
async def get_anatomy(structure_id: str) -> AnatomyResponse:
    """Returns educational data for a specific anatomical structure."""
    result = get_anatomy_structure(structure_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found. Call /anatomy to list available structures.",
        )
    return result


# ── Classification ────────────────────────────────────────────────────────────

@app.post("/classify", response_model=ClassificationResponse, tags=["Classification"])
@limiter.limit("10/minute")
async def classify_image(
    request: Request,
    file: UploadFile = File(...),
) -> ClassificationResponse:
    """
    Analyze a fundoscopy image and return educational classification.
    Magic byte validation ensures the upload is a real JPEG/PNG.
    Rate limit: 10 requests/minute per IP.
    """
    if not rag_service.is_ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG service initializing.")

    safe_name = sanitize_filename(file.filename or "image")
    image_data = await file.read()

    if len(image_data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Imagem excede 20MB.")

    # Magic byte check — rejects disguised executables
    validate_image(image_data, safe_name)

    logger.info("classify.received", filename=safe_name, size=len(image_data))

    try:
        result = classifier_service.classify(image_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error("classify.error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao processar imagem.")

    # Generate RAG explanation (trace discarded — classify is not a chat session)
    try:
        rag_response, _ = rag_service.query(
            message=result.rag_query,
            selected_structure=result.related_structures[0] if result.related_structures else None,
        )
        explanation = rag_response.answer
    except Exception as e:
        logger.warning("classify.rag_fallback", error=str(e))
        explanation = f"Condição identificada: {result.condition}. Consulte um oftalmologista para avaliação clínica."

    return ClassificationResponse(
        condition=result.condition,
        condition_en=result.condition_en,
        confidence=result.confidence,
        severity=result.severity,
        neurological_flag=result.neurological_flag,
        neurological_note=result.neurological_note,
        features_detected=result.features_detected,
        explanation=explanation,
        related_structures=result.related_structures,
        disclaimer=result.disclaimer,
        classifier_method=result.classifier_method,
    )


# ── Knowledge Base ────────────────────────────────────────────────────────────

@app.post("/ingest", tags=["Knowledge Base"])
@limiter.limit("5/minute")
async def ingest_pdf(
    request: Request,
    file: UploadFile = File(...),
) -> dict:
    """
    Upload and index a PDF into the RAG knowledge base.
    Idempotent: same file uploaded twice won't create duplicate chunks.
    Magic byte validation ensures only real PDFs are accepted.
    Rate limit: 5 requests/minute per IP.
    """
    if not rag_service.is_ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG service is still initializing.")

    safe_name = sanitize_filename(file.filename or "document.pdf")

    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Apenas arquivos PDF são aceitos.")

    pdf_data = await file.read()

    if len(pdf_data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Arquivo excede o limite de 50MB.")

    # Magic byte check — rejects non-PDF disguised as PDF
    validate_pdf(pdf_data, safe_name)

    logger.info("ingest.received", filename=safe_name, size=len(pdf_data))

    try:
        import io
        result = ingestion_service.ingest_pdf(filename=safe_name, file=io.BytesIO(pdf_data))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error("ingest.error", filename=safe_name, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao processar o PDF.")

    return result


@app.get("/documents", tags=["Knowledge Base"])
async def list_documents() -> dict:
    """Returns all indexed sources with chunk counts and total."""
    sources = ingestion_service.list_sources()
    total = vector_store.total_documents()
    return {"total_chunks": total, "sources": sources}


# ── Clinical Cases ────────────────────────────────────────────────────────────

@app.get("/cases", response_model=list[CaseListItem], tags=["Clinical Cases"])
async def list_clinical_cases() -> list[CaseListItem]:
    """Returns the list of available clinical cases (without full content)."""
    return list_cases()


@app.get("/cases/{case_id}", response_model=ClinicalCase, tags=["Clinical Cases"])
async def get_clinical_case(case_id: str) -> ClinicalCase:
    """Returns a full clinical case including patient history, questions and answers."""
    case = get_case(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")
    return case


# ── Session history ───────────────────────────────────────────────────────────

@app.get("/sessions/{session_id}/messages", response_model=SessionHistoryResponse, tags=["Sessions"])
async def get_session_messages(session_id: str) -> SessionHistoryResponse:
    """
    Returns the persisted chat history for a session.
    Used by the frontend to restore conversation across page reloads.
    """
    messages = db.get_messages(session_id)
    return SessionHistoryResponse(
        session_id=session_id,
        messages=[SessionMessage(**m) for m in messages],
    )


@app.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str) -> dict:
    """Deletes a session and all its messages."""
    existed = db.delete_session(session_id)
    if not existed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return {"deleted": session_id}


# ── RAG Evaluation ────────────────────────────────────────────────────────────

@app.get("/evaluation/stats", response_model=EvaluationStats, tags=["Evaluation"])
async def get_evaluation_stats() -> EvaluationStats:
    """
    Aggregate LLM-as-judge scores.
    Faithfulness (1–5) + Relevancy (1–5) → Composite = 0.6F + 0.4R.
    """
    stats = db.get_evaluation_stats()
    return EvaluationStats(**stats)


# ── RAG Tracing ───────────────────────────────────────────────────────────────

@app.get("/traces/stats", response_model=RAGTraceStats, tags=["Observability"])
async def get_trace_stats() -> RAGTraceStats:
    """
    Aggregate latency and retrieval quality metrics across all RAG queries.

    Key signals:
    - avg_retrieval_ms / avg_llm_ms — latency breakdown
    - avg_similarity_score — retrieval quality (< 0.5 = poor chunk match)
    - low_similarity_ratio — fraction of queries below the 0.5 similarity threshold
    """
    stats = db.get_traces_stats()
    return RAGTraceStats(**stats)


@app.get("/traces", response_model=list[RAGTrace], tags=["Observability"])
async def get_traces(session_id: Optional[str] = None, limit: int = 20) -> list[RAGTrace]:
    """
    Recent RAG pipeline traces with retrieved chunks, similarity scores, and latencies.
    Optionally filter by session_id.
    """
    rows = db.get_traces(session_id=session_id, limit=min(limit, 100))
    return [
        RAGTrace(
            id=r["id"],
            session_id=r["session_id"],
            query=r["query"],
            retrieved_chunks=[RAGChunk(**c) for c in r["retrieved_chunks"]],
            answer=r["answer"],
            retrieval_ms=r["retrieval_ms"],
            llm_ms=r["llm_ms"],
            total_ms=r["total_ms"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
