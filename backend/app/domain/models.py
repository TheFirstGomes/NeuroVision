"""
Domain models for NeuroVision platform.
Defines all request/response schemas with strict typing.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question")
    session_id: Optional[str] = Field(default=None, description="Session ID for context continuity")
    structure: Optional[str] = Field(default=None, description="Currently selected anatomical structure")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="RAG-generated answer")
    sources: list[str] = Field(default_factory=list, description="Source references used")
    related_structures: list[str] = Field(default_factory=list, description="Related anatomical structures")
    session_id: str = Field(..., description="Session ID")


class AnatomyStructure(BaseModel):
    id: str = Field(..., description="Structure identifier")
    name: str = Field(..., description="Clinical name")
    description: str = Field(..., description="Educational description")
    neurological_connections: list[str] = Field(default_factory=list)
    associated_pathologies: list[str] = Field(default_factory=list)
    clinical_relevance: str = Field(default="", description="Why this structure matters clinically")


class AnatomyResponse(BaseModel):
    structure: AnatomyStructure
    highlight_color: str = Field(default="#00ff88", description="Three.js highlight color")


class ClassificationResponse(BaseModel):
    condition: str
    condition_en: str
    confidence: float
    severity: str
    neurological_flag: bool
    neurological_note: str
    features_detected: list[str]
    explanation: str
    related_structures: list[str]
    disclaimer: str
    classifier_method: str = "feature_based"


# ── Clinical Cases ─────────────────────────────────────────────────────────────

class CaseQuestion(BaseModel):
    question: str
    answer: str
    explanation: str


class CasePatient(BaseModel):
    age: int
    sex: str
    chief_complaint: str
    history: str
    examination: str


class ClinicalCase(BaseModel):
    id: str
    title: str
    category: str
    difficulty: int = Field(..., ge=1, le=3, description="1=básico, 2=intermediário, 3=avançado")
    related_structure: str = Field(..., description="Structure ID for 3D viewer")
    visual_field_structure: str = Field(..., description="Structure ID for visual field simulator")
    patient: CasePatient
    questions: list[CaseQuestion]
    teaching_point: str


class CaseListItem(BaseModel):
    id: str
    title: str
    category: str
    difficulty: int
    related_structure: str


class HealthResponse(BaseModel):
    status: str
    rag_ready: bool
    model: str
    version: str


# ── Session history ────────────────────────────────────────────────────────────

class SessionMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    sources: list[str] = Field(default_factory=list)
    related_structures: list[str] = Field(default_factory=list)
    created_at: str


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: list[SessionMessage]


# ── RAG evaluation ─────────────────────────────────────────────────────────────

class EvaluationStats(BaseModel):
    total_evaluated: int
    avg_faithfulness: Optional[float]
    avg_relevancy: Optional[float]
    avg_composite: Optional[float]
    failed_evaluations: int
    recent: list[dict]


# ── RAG tracing ────────────────────────────────────────────────────────────────

class RAGChunk(BaseModel):
    source: str
    similarity_score: float
    content_snippet: str


class RAGTrace(BaseModel):
    id: int
    session_id: str
    query: str
    retrieved_chunks: list[RAGChunk]
    answer: str
    retrieval_ms: Optional[int]
    llm_ms: Optional[int]
    total_ms: Optional[int]
    created_at: str


class RAGTraceStats(BaseModel):
    total_traces: int
    avg_retrieval_ms: Optional[float]
    avg_llm_ms: Optional[float]
    avg_total_ms: Optional[float]
    min_total_ms: Optional[int]
    max_total_ms: Optional[int]
    avg_similarity_score: Optional[float]
    low_similarity_ratio: float
