# RAG reference documents

Drop training/coaching methodology and sports-science reference material here as
`.txt`, `.md`, or `.pdf` files (subfolders are fine — the ingestion script walks
the whole tree). Each file becomes its own `source` in the vector index, so
re-running ingestion after editing a file replaces just that file's chunks.

To (re)build the index after adding or changing files:

```bash
uv run --project /Users/matthewlazur/garmin-performance/garmin-analysis python -m back_end.rag.ingest
```

Requires `VOYAGE_API_KEY` set in `garmin-analysis/.env`.
