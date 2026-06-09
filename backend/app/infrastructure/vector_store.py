"""
Vector store abstraction for NeuroVision RAG pipeline.
Uses ChromaDB with HuggingFace sentence-transformers embeddings.
"""
import structlog
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

logger = structlog.get_logger(__name__)

CHROMA_PERSIST_DIR = Path(__file__).parent.parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "neuro_ophthalmology"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class VectorStoreService:
    """
    Manages ChromaDB vector store lifecycle.
    - Initializes embeddings on startup
    - Ingests knowledge base documents
    - Exposes similarity search for RAG
    """

    def __init__(self) -> None:
        self._store: Optional[Chroma] = None
        self._embeddings: Optional[HuggingFaceEmbeddings] = None

    def initialize(self) -> None:
        """Initialize embeddings model and ChromaDB collection."""
        logger.info("vector_store.initializing", model=EMBEDDING_MODEL)

        self._embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False),
        )

        self._store = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=self._embeddings,
        )

        logger.info("vector_store.initialized", collection=COLLECTION_NAME)

    def ingest_documents(self, documents: list[Document]) -> None:
        """
        Ingest documents into the vector store.
        Skips ingestion if collection already has data (idempotent).
        """
        if self._store is None:
            raise RuntimeError("VectorStoreService not initialized. Call initialize() first.")

        existing = self._store._collection.count()
        if existing > 0:
            logger.info("vector_store.already_populated", doc_count=existing)
            return

        logger.info("vector_store.ingesting", count=len(documents))
        self._store.add_documents(documents)
        logger.info("vector_store.ingestion_complete", count=len(documents))

    def add_documents(self, documents: list[Document]) -> None:
        """
        Add new documents to the vector store (post-startup ingestion).
        Unlike ingest_documents, this always adds — used for PDF uploads.
        """
        if self._store is None:
            raise RuntimeError("VectorStoreService not initialized.")

        logger.info("vector_store.adding_documents", count=len(documents))
        self._store.add_documents(documents)
        logger.info("vector_store.documents_added", count=len(documents))

    def similarity_search(self, query: str, k: int = 4) -> list[Document]:
        """Retrieve top-k most relevant documents for a query."""
        if self._store is None:
            raise RuntimeError("VectorStoreService not initialized.")

        return self._store.similarity_search(query, k=k)

    def similarity_search_with_score(
        self, query: str, k: int = 4
    ) -> list[tuple[Document, float]]:
        """
        Retrieve top-k documents with their relevance scores.

        Returns list of (Document, score) tuples.
        Score is cosine similarity (0–1, higher = more relevant) because
        the store is initialized with normalize_embeddings=True.
        """
        if self._store is None:
            raise RuntimeError("VectorStoreService not initialized.")

        return self._store.similarity_search_with_score(query, k=k)

    def as_retriever(self, k: int = 4):
        """Return LangChain-compatible retriever interface."""
        if self._store is None:
            raise RuntimeError("VectorStoreService not initialized.")

        return self._store.as_retriever(search_kwargs={"k": k})

    def list_sources(self) -> list[dict]:
        """
        Returns all unique sources indexed in the collection.
        Groups chunks by source filename with count.
        """
        if self._store is None:
            raise RuntimeError("VectorStoreService not initialized.")

        try:
            result = self._store._collection.get(include=["metadatas"])
            metadatas = result.get("metadatas") or []

            sources: dict[str, dict] = {}
            for meta in metadatas:
                src = meta.get("source", "knowledge_base")
                topic = meta.get("topic", "geral")
                if src not in sources:
                    sources[src] = {"source": src, "topic": topic, "chunks": 0}
                sources[src]["chunks"] += 1

            return sorted(sources.values(), key=lambda x: x["source"])
        except Exception as e:
            logger.error("vector_store.list_sources_error", error=str(e))
            return []

    def total_documents(self) -> int:
        """Returns total number of chunks indexed."""
        if self._store is None:
            return 0
        try:
            return self._store._collection.count()
        except Exception:
            return 0

    @property
    def is_ready(self) -> bool:
        return self._store is not None
