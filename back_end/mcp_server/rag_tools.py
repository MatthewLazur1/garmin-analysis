from typing import Any, Dict, List

from back_end.db import get_engine
from back_end.mcp_server.app import mcp
from back_end.rag import rag_repository
from back_end.rag.voyage_client import EMBEDDING_MODEL, get_voyage_client


@mcp.tool()
def rag_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search embedded reference documents (training/coaching methodology, sports
    science) for passages relevant to `query`. Returns up to `top_k` matches,
    each with its source file, matched text, and a similarity score (0-1,
    higher is more relevant). Returns an empty list if no documents have been
    ingested yet — run `python -m back_end.rag.ingest` first.
    """
    engine = get_engine()
    rag_repository.ensure_schema(engine)
    embedding = get_voyage_client().embed(
        [query], model=EMBEDDING_MODEL, input_type="query"
    ).embeddings[0]
    return rag_repository.search(engine, embedding, top_k)
