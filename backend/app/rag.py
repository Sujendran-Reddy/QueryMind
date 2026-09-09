import httpx


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"


def generate_answer(
    question: str,
    retrieved_chunks: list[dict],
) -> str:
    if not retrieved_chunks:
        return "I couldn't find that information in the uploaded documents."

    context = "\n\n".join(
        (
            f"[Source {index}]\n"
            f"Document: {chunk['document_name']}\n"
            f"Page: {chunk['page_number']}\n"
            f"Content: {chunk['text']}"
        )
        for index, chunk in enumerate(retrieved_chunks, start=1)
    )

    prompt = f"""
You are QueryMind, a document intelligence assistant.

Answer using only the supplied sources.

Rules:
- Do not use outside knowledge.
- Cite claims using [1], [2], and so on.
- Never invent facts or citations.
- If the answer is unavailable, respond exactly:
  I couldn't find that information in the uploaded documents.

Sources:
{context}

Question:
{question}

Answer:
""".strip()

    response = httpx.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()["response"].strip()