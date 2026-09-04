import pytest

from app.chunking import chunk_document
from app.documents import ExtractedPage


def test_chunks_keep_page_numbers_and_overlap():
    page = ExtractedPage(
        page_number=7,
        text="one two three four five six",
    )

    chunks = chunk_document(
        pages=[page],
        chunk_size=4,
        overlap=2,
    )

    assert len(chunks) == 2
    assert chunks[0].text == "one two three four"
    assert chunks[1].text == "three four five six"
    assert chunks[0].page_number == 7
    assert chunks[1].page_number == 7


def test_overlap_cannot_equal_chunk_size():
    with pytest.raises(ValueError):
        chunk_document(
            pages=[ExtractedPage(1, "example text")],
            chunk_size=100,
            overlap=100,
        )