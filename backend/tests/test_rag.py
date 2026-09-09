from app.rag import generate_answer


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "response": "Employees receive twenty leave days [1]."
        }


def test_refuses_when_no_sources_are_available():
    answer = generate_answer(
        question="How many leave days are available?",
        retrieved_chunks=[],
    )

    assert answer == (
        "I couldn't find that information in the uploaded documents."
    )


def test_generates_answer_using_ollama(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("app.rag.httpx.post", fake_post)

    chunks = [
        {
            "document_name": "handbook.pdf",
            "page_number": 14,
            "text": "Employees receive twenty annual leave days.",
        }
    ]

    answer = generate_answer(
        question="How many leave days are available?",
        retrieved_chunks=chunks,
    )

    assert answer == "Employees receive twenty leave days [1]."