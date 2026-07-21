import json
from typing import Any, Dict, List, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from back_end.rag.voyage_client import EMBEDDING_DIMENSION

_SCHEMA_STATEMENTS = [
    "create extension if not exists vector",
    f"""
    create table if not exists document_chunks (
        id bigint generated always as identity primary key,
        source text not null,
        content text not null,
        embedding vector({EMBEDDING_DIMENSION}) not null,
        metadata jsonb not null default '{{}}'::jsonb,
        created_at timestamptz not null default now()
    )
    """,
    "create index if not exists idx_document_chunks_source on document_chunks(source)",
    "create index if not exists idx_document_chunks_embedding "
    "on document_chunks using hnsw (embedding vector_cosine_ops)",
]


def ensure_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        for statement in _SCHEMA_STATEMENTS:
            conn.execute(text(statement))


def _to_vector_literal(embedding: Sequence[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


def replace_source_chunks(engine: Engine, source: str, rows: List[Dict[str, Any]]) -> None:
    """Delete any existing chunks for `source`, then insert `rows` — a full replace on re-ingest."""
    with engine.begin() as conn:
        conn.execute(text("delete from document_chunks where source = :source"), {"source": source})
        for row in rows:
            conn.execute(
                text(
                    """
                    insert into document_chunks (source, content, embedding, metadata)
                    values (:source, :content, (:embedding)::vector, (:metadata)::jsonb)
                    """
                ),
                {
                    "source": source,
                    "content": row["content"],
                    "embedding": _to_vector_literal(row["embedding"]),
                    "metadata": json.dumps(row.get("metadata", {})),
                },
            )


def search(engine: Engine, query_embedding: Sequence[float], top_k: int = 5) -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                select source, content, metadata,
                       1 - (embedding <=> (:embedding)::vector) as similarity
                from document_chunks
                order by embedding <=> (:embedding)::vector
                limit :top_k
                """
            ),
            {"embedding": _to_vector_literal(query_embedding), "top_k": top_k},
        ).mappings().all()
    return [
        {
            "source": row["source"],
            "content": row["content"],
            "metadata": row["metadata"],
            "similarity": round(float(row["similarity"]), 4),
        }
        for row in rows
    ]
