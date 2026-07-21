import os

import voyageai

# voyage-3's native output dimension. Keep this in sync with the `vector(N)`
# column width in rag_repository._SCHEMA_STATEMENTS if the model ever changes.
EMBEDDING_MODEL = "voyage-3"
EMBEDDING_DIMENSION = 1024

_voyage_client = None


def get_voyage_client() -> voyageai.Client:
    """Lazily construct the Voyage AI client and reuse it for the life of the process."""
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    return _voyage_client
