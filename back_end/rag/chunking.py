from typing import List

_DEFAULT_CHUNK_CHARS = 1200
_DEFAULT_OVERLAP_CHARS = 200


def chunk_text(
    text: str,
    chunk_chars: int = _DEFAULT_CHUNK_CHARS,
    overlap_chars: int = _DEFAULT_OVERLAP_CHARS,
) -> List[str]:
    """
    Split `text` into overlapping chunks, breaking on paragraph boundaries where
    possible so a chunk doesn't cut a sentence in half.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= chunk_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= chunk_chars:
            current = paragraph
        else:
            # A single paragraph exceeds chunk_chars — hard-split it with overlap.
            step = chunk_chars - overlap_chars
            for start in range(0, len(paragraph), step):
                chunks.append(paragraph[start:start + chunk_chars])
            current = ""
    if current:
        chunks.append(current)
    return chunks
