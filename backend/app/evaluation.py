from dataclasses import dataclass
from time import perf_counter

from app.vector_store import get_vector_store


@dataclass
class EvaluationQuestion:
    question: str
    expected_document: str
    expected_page: int | None = None


def evaluate_retrieval(
    collection_id: str,
    questions: list[EvaluationQuestion],
    top_k: int,
) -> dict:
    vector_store = get_vector_store()
    retrieval_hits = 0
    citation_hits = 0
    response_times = []

    for item in questions:
        started_at = perf_counter()

        results = vector_store.search(
            collection_id=collection_id,
            question=item.question,
            top_k=top_k,
        )

        response_times.append(
            round((perf_counter() - started_at) * 1000, 2)
        )

        document_found = any(
            result["document_name"] == item.expected_document
            for result in results
        )

        citation_found = any(
            result["document_name"] == item.expected_document
            and (
                item.expected_page is None
                or result["page_number"] == item.expected_page
            )
            for result in results
        )

        retrieval_hits += int(document_found)
        citation_hits += int(citation_found)

    total = len(questions)

    return {
        "question_count": total,
        "top_k": top_k,
        "retrieval_hit_rate": (
            round(retrieval_hits / total, 4) if total else 0
        ),
        "citation_hit_rate": (
            round(citation_hits / total, 4) if total else 0
        ),
        "average_retrieval_ms": (
            round(sum(response_times) / total, 2) if total else 0
        ),
    }