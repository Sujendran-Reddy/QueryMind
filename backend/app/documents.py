from dataclasses import dataclass
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@dataclass
class ExtractedPage:
    page_number: int
    text: str


def extract_document(file_path: Path) -> list[ExtractedPage]:
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        reader = PdfReader(file_path)

        return [
            ExtractedPage(
                page_number=index + 1,
                text=page.extract_text() or "",
            )
            for index, page in enumerate(reader.pages)
        ]

    if extension == ".docx":
        document = Document(file_path)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)

        return [ExtractedPage(page_number=1, text=text)]

    if extension in {".txt", ".md"}:
        text = file_path.read_text(encoding="utf-8", errors="replace")

        return [ExtractedPage(page_number=1, text=text)]

    raise ValueError("Unsupported document type")