from dataclasses import dataclass

from app.documents import ExtractedPage


@dataclass
class TextChunk:
    page_number: int
    chunk_index: int
    text: str


def chunk_document(
    pages: list[ExtractedPage],
    chunk_size: int = 500,
    overlap: int = 75,
) -> list[TextChunk]:
    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size")

    chunks: list[TextChunk] = []
    chunk_index = 0

    for page in pages:
        words = page.text.split()
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk_text = " ".join(words[start:end]).strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        text=chunk_text,
                    )
                )
                chunk_index += 1

            if end >= len(words):
                break

            start += chunk_size - overlap

    return chunks