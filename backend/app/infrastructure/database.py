"""
SQLite persistence layer for NeuroVision.
Manages session history and RAG evaluation scores.

All operations are synchronous (sqlite3 is thread-safe in serialized mode).
FastAPI endpoint handlers call these from run_in_executor or directly
given the low concurrency of this educational application.
"""
import json
import sqlite3
import threading
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# ── DB path ───────────────────────────────────────────────────────────────────

_DB_PATH = Path(__file__).parent.parent.parent / "neurovision.db"

# Thread-local connections: one per thread, reused within that thread.
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Return (or create) the thread-local SQLite connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")   # concurrent reads
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


# ── Schema ────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    last_active TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role                TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
    content             TEXT    NOT NULL,
    sources             TEXT    NOT NULL DEFAULT '[]',   -- JSON array
    related_structures  TEXT    NOT NULL DEFAULT '[]',   -- JSON array
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rag_evaluations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT    NOT NULL,
    question            TEXT    NOT NULL,
    answer              TEXT    NOT NULL,
    faithfulness_score  INTEGER,                          -- 1–5, NULL if eval failed
    relevancy_score     INTEGER,                          -- 1–5, NULL if eval failed
    composite_score     REAL,                             -- 0.6*faithfulness + 0.4*relevancy
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rag_traces (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT    NOT NULL,
    query               TEXT    NOT NULL,
    retrieved_chunks    TEXT    NOT NULL DEFAULT '[]',   -- JSON: [{source, similarity_score, content_snippet}]
    context_sent        TEXT    NOT NULL DEFAULT '',     -- exact context passed to LLM
    answer              TEXT    NOT NULL,
    retrieval_ms        INTEGER,
    llm_ms              INTEGER,
    total_ms            INTEGER,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_session  ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_eval_session      ON rag_evaluations(session_id);
CREATE INDEX IF NOT EXISTS idx_eval_created      ON rag_evaluations(created_at);
CREATE INDEX IF NOT EXISTS idx_traces_session    ON rag_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_traces_created    ON rag_traces(created_at);
"""


def init_db() -> None:
    """Create tables if they don't exist. Safe to call multiple times."""
    conn = _get_conn()
    conn.executescript(_DDL)
    conn.commit()
    _purge_old_traces(conn)
    logger.info("database.initialized", path=str(_DB_PATH))


def _purge_old_traces(conn: sqlite3.Connection, keep: int = 1000) -> None:
    """Keep only the most recent `keep` traces. Prevents unbounded growth at scale."""
    deleted = conn.execute(
        """
        DELETE FROM rag_traces
        WHERE id NOT IN (
            SELECT id FROM rag_traces ORDER BY id DESC LIMIT ?
        )
        """,
        (keep,),
    ).rowcount
    conn.commit()
    if deleted:
        logger.info("database.traces_purged", deleted=deleted, max_kept=keep)


# ── Session helpers ───────────────────────────────────────────────────────────

def upsert_session(session_id: str) -> None:
    """Create session row if it doesn't exist; bump last_active timestamp."""
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO sessions (id) VALUES (?)
        ON CONFLICT(id) DO UPDATE SET last_active = datetime('now')
        """,
        (session_id,),
    )
    conn.commit()


def add_message(
    session_id: str,
    role: str,
    content: str,
    sources: Optional[list[str]] = None,
    related_structures: Optional[list[str]] = None,
) -> None:
    """Persist one chat message linked to a session."""
    upsert_session(session_id)
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO chat_messages (session_id, role, content, sources, related_structures)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            role,
            content,
            json.dumps(sources or []),
            json.dumps(related_structures or []),
        ),
    )
    conn.commit()


def get_messages(session_id: str) -> list[dict]:
    """Return all messages for a session ordered by creation time."""
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT role, content, sources, related_structures, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (session_id,),
    ).fetchall()

    return [
        {
            "role": row["role"],
            "content": row["content"],
            "sources": json.loads(row["sources"]),
            "related_structures": json.loads(row["related_structures"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def delete_session(session_id: str) -> bool:
    """Delete a session and all its messages. Returns True if it existed."""
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    return cursor.rowcount > 0


# ── Evaluation helpers ────────────────────────────────────────────────────────

def add_evaluation(
    session_id: str,
    question: str,
    answer: str,
    faithfulness_score: Optional[int],
    relevancy_score: Optional[int],
    composite_score: Optional[float] = None,
) -> None:
    """Store one LLM-as-judge evaluation result."""
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO rag_evaluations
            (session_id, question, answer, faithfulness_score, relevancy_score, composite_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, question, answer, faithfulness_score, relevancy_score, composite_score),
    )
    conn.commit()


def get_evaluation_stats() -> dict:
    """Return aggregate evaluation metrics including composite score."""
    conn = _get_conn()
    row = conn.execute(
        """
        SELECT
            COUNT(*)                          AS total,
            ROUND(AVG(faithfulness_score), 2) AS avg_faithfulness,
            ROUND(AVG(relevancy_score), 2)    AS avg_relevancy,
            ROUND(AVG(composite_score), 2)    AS avg_composite,
            COUNT(CASE WHEN faithfulness_score IS NULL THEN 1 END) AS failed
        FROM rag_evaluations
        """
    ).fetchone()

    recent = conn.execute(
        """
        SELECT session_id, question, faithfulness_score, relevancy_score, composite_score, created_at
        FROM rag_evaluations
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()

    return {
        "total_evaluated": row["total"],
        "avg_faithfulness": row["avg_faithfulness"],
        "avg_relevancy": row["avg_relevancy"],
        "avg_composite": row["avg_composite"],
        "failed_evaluations": row["failed"],
        "recent": [dict(r) for r in recent],
    }


# ── RAG trace helpers ─────────────────────────────────────────────────────────

def add_trace(
    session_id: str,
    query: str,
    retrieved_chunks: list[dict],
    context_sent: str,
    answer: str,
    retrieval_ms: Optional[int],
    llm_ms: Optional[int],
    total_ms: Optional[int],
) -> None:
    """Persist one full RAG pipeline trace."""
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO rag_traces
            (session_id, query, retrieved_chunks, context_sent, answer,
             retrieval_ms, llm_ms, total_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            query,
            json.dumps(retrieved_chunks),
            context_sent[:500],     # 500 chars is enough for analysis; context lives in the vector store
            answer,
            retrieval_ms,
            llm_ms,
            total_ms,
        ),
    )
    conn.commit()


def get_traces(session_id: Optional[str] = None, limit: int = 20) -> list[dict]:
    """Return recent traces, optionally filtered by session."""
    conn = _get_conn()
    if session_id:
        rows = conn.execute(
            """
            SELECT id, session_id, query, retrieved_chunks, answer,
                   retrieval_ms, llm_ms, total_ms, created_at
            FROM rag_traces WHERE session_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, session_id, query, retrieved_chunks, answer,
                   retrieval_ms, llm_ms, total_ms, created_at
            FROM rag_traces
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    result = []
    for row in rows:
        r = dict(row)
        r["retrieved_chunks"] = json.loads(r["retrieved_chunks"])
        result.append(r)
    return result


def get_traces_stats() -> dict:
    """Aggregate latency and similarity metrics across all traces."""
    conn = _get_conn()

    latency = conn.execute(
        """
        SELECT
            COUNT(*)                      AS total,
            ROUND(AVG(retrieval_ms), 1)   AS avg_retrieval_ms,
            ROUND(AVG(llm_ms), 1)         AS avg_llm_ms,
            ROUND(AVG(total_ms), 1)       AS avg_total_ms,
            MIN(total_ms)                 AS min_total_ms,
            MAX(total_ms)                 AS max_total_ms
        FROM rag_traces
        """
    ).fetchone()

    # Compute avg similarity across all chunks of all traces in Python
    # (SQLite has limited JSON support in older versions)
    chunk_rows = conn.execute(
        "SELECT retrieved_chunks FROM rag_traces WHERE retrieved_chunks != '[]'"
    ).fetchall()

    scores: list[float] = []
    low_sim_queries = 0
    for row in chunk_rows:
        chunks = json.loads(row[0])
        chunk_scores = [c.get("similarity_score", 0) for c in chunks if c.get("similarity_score") is not None]
        if chunk_scores:
            avg = sum(chunk_scores) / len(chunk_scores)
            scores.append(avg)
            if avg < 0.5:
                low_sim_queries += 1

    total_with_chunks = len(scores)
    avg_similarity = round(sum(scores) / total_with_chunks, 4) if scores else None
    low_sim_ratio = round(low_sim_queries / total_with_chunks, 4) if total_with_chunks else 0.0

    return {
        "total_traces": latency["total"],
        "avg_retrieval_ms": latency["avg_retrieval_ms"],
        "avg_llm_ms": latency["avg_llm_ms"],
        "avg_total_ms": latency["avg_total_ms"],
        "min_total_ms": latency["min_total_ms"],
        "max_total_ms": latency["max_total_ms"],
        "avg_similarity_score": avg_similarity,
        "low_similarity_ratio": low_sim_ratio,
    }
