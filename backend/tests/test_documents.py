from pathlib import Path

from app.documents import extract_document


def test_extracts_text_file(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text(
        "Employees receive twenty annual leave days.",
        encoding="utf-8",
    )

    pages = extract_document(file_path)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "twenty annual leave days" in pages[0].text