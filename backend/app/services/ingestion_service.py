"""
PDF Ingestion Service for NeuroVision.
Processes uploaded PDFs, splits into semantically coherent chunks,
and indexes into ChromaDB for RAG retrieval.
"""
import hashlib
import structlog
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.infrastructure.vector_store import VectorStoreService

logger = structlog.get_logger(__name__)

# Chunk strategy tuned for medical/clinical text
CHUNK_SIZE    = 900   # ~2-3 paragraphs of clinical content
CHUNK_OVERLAP = 180   # preserve context across boundaries
SEPARATORS    = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "]

UPLOAD_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"


class IngestionService:
    """
    Orchestrates the PDF → chunks → vector store pipeline.

    Design decisions:
    - Idempotent: same file ingested twice produces no duplicates (hash check)
    - Chunk metadata preserves source, page, and position for citation
    - Overlap prevents context loss at chunk boundaries
    """

    def __init__(self, vector_store: VectorStoreService) -> None:
        self._vector_store = vector_store
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=SEPARATORS,
            length_function=len,
        )
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def ingest_pdf(self, filename: str, file: BinaryIO) -> dict:
        """
        Process and index a single PDF file.

        Returns:
            dict with filename, pages, chunks_added, skipped (if duplicate)
        """
        content = file.read()
        file_hash = hashlib.md5(content).hexdigest()

        logger.info("ingestion.start", filename=filename, size_bytes=len(content))

        # Duplicate check — same hash = already indexed
        existing = self._vector_store.similarity_search(
            query=f"source:{filename}", k=1
        )
        for doc in existing:
            if doc.metadata.get("file_hash") == file_hash:
                logger.info("ingestion.skipped_duplicate", filename=filename)
                return {
                    "filename": filename,
                    "pages": 0,
                    "chunks_added": 0,
                    "skipped": True,
                    "reason": "Arquivo já indexado (hash idêntico)",
                }

        # Extract text per page
        try:
            reader = PdfReader(UPLOAD_DIR / filename if False else __import__("io").BytesIO(content))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text = text.strip()
                if len(text) > 50:  # skip nearly-empty pages
                    pages_text.append((i + 1, text))
        except Exception as e:
            logger.error("ingestion.pdf_parse_error", filename=filename, error=str(e))
            raise ValueError(f"Falha ao processar PDF '{filename}': {str(e)}")

        if not pages_text:
            raise ValueError(f"PDF '{filename}' não contém texto extraível.")

        # Build documents with full metadata
        raw_docs = [
            Document(
                page_content=text,
                metadata={
                    "source": filename,
                    "page": page_num,
                    "file_hash": file_hash,
                    "topic": "pdf_upload",
                    "structure": "geral",
                },
            )
            for page_num, text in pages_text
        ]

        # Split into semantic chunks
        chunks = self._splitter.split_documents(raw_docs)

        # Tag each chunk with position
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)

        # Add to vector store
        self._vector_store.add_documents(chunks)

        logger.info(
            "ingestion.complete",
            filename=filename,
            pages=len(pages_text),
            chunks=len(chunks),
        )

        return {
            "filename": filename,
            "pages": len(pages_text),
            "chunks_added": len(chunks),
            "skipped": False,
        }

    def list_sources(self) -> list[dict]:
        """Returns all indexed sources with chunk counts."""
        return self._vector_store.list_sources()
