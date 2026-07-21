"""
Embed reference documents into Supabase pgvector.

Reads every .txt/.md/.pdf file under rag_docs/ (relative to the project root),
chunks it, embeds the chunks with Voyage AI, and upserts into the
`document_chunks` table — replacing any existing chunks for that file. Run
this manually after adding or editing documents; it is not part of the MCP
server's runtime.

    uv run --project /Users/matthewlazur/garmin-performance/garmin-analysis python -m back_end.rag.ingest
"""

from pathlib import Path
from typing import List

from PyPDF2 import PdfReader

from back_end.db import get_engine
from back_end.rag import rag_repository
from back_end.rag.chunking import chunk_text
from back_end.rag.voyage_client import EMBEDDING_MODEL, get_voyage_client

_DOCS_DIR = Path(__file__).resolve().parents[2] / "rag_docs"
_SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}
_EMBED_BATCH_SIZE = 32


def _read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8")


def _embed_chunks(chunks: List[str]) -> List[List[float]]:
    client = get_voyage_client()
    embeddings: List[List[float]] = []
    for start in range(0, len(chunks), _EMBED_BATCH_SIZE):
        batch = chunks[start:start + _EMBED_BATCH_SIZE]
        result = client.embed(batch, model=EMBEDDING_MODEL, input_type="document")
        embeddings.extend(result.embeddings)
    return embeddings


def ingest_file(engine, path: Path) -> int:
    chunks = chunk_text(_read_text(path))
    if not chunks:
        return 0
    embeddings = _embed_chunks(chunks)
    source = str(path.relative_to(_DOCS_DIR))
    rows = [
        {"content": chunk, "embedding": embedding, "metadata": {"file": source}}
        for chunk, embedding in zip(chunks, embeddings)
    ]
    rag_repository.replace_source_chunks(engine, source, rows)
    return len(rows)


def main() -> None:
    if not _DOCS_DIR.exists():
        raise SystemExit(f"No {_DOCS_DIR} directory found — add reference docs there first.")

    engine = get_engine()
    rag_repository.ensure_schema(engine)

    paths = sorted(
        p for p in _DOCS_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in _SUPPORTED_SUFFIXES
    )
    if not paths:
        print(f"No .txt/.md/.pdf files found under {_DOCS_DIR}")
        return

    for path in paths:
        count = ingest_file(engine, path)
        print(f"{path.relative_to(_DOCS_DIR)}: {count} chunks")


if __name__ == "__main__":
    main()
