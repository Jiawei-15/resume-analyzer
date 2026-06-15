from typing import Any, Dict, List, Tuple

from app.services.embedding_service import cosine_similarity


_stored_vectors: List[Dict[str, Any]] = []


def clear_embeddings() -> None:
    """
    Clear all stored vectors.

    This prevents resume chunks from previous requests
    from polluting the current analysis.
    """

    _stored_vectors.clear()


def add_embedding(
    embedding: List[float],
    text: str
) -> None:
    """
    Add one text chunk and its embedding to the in-memory vector store.
    """

    _stored_vectors.append({
        "embedding": embedding,
        "text": text
    })


def search_embedding(
    query_embedding: List[float],
    top_k: int = 3
) -> List[str]:
    """
    Search the most relevant text chunks by cosine similarity.

    Returns only text chunks to stay compatible with your current
    EvidenceRetrievalAgent.
    """

    scored_chunks: List[Tuple[float, str]] = []

    for item in _stored_vectors:
        score = cosine_similarity(
            query_embedding,
            item["embedding"]
        )

        scored_chunks.append(
            (
                score,
                item["text"]
            )
        )

    scored_chunks.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        text
        for score, text in scored_chunks[:top_k]
    ]


def search_embedding_with_scores(
    query_embedding: List[float],
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Search the most relevant text chunks and return scores.

    This is for the future evidence_map upgrade.
    Current code may not use it yet.
    """

    scored_chunks: List[Dict[str, Any]] = []

    for index, item in enumerate(_stored_vectors):
        score = cosine_similarity(
            query_embedding,
            item["embedding"]
        )

        scored_chunks.append({
            "id": index,
            "chunk": item["text"],
            "score": round(score, 4)
        })

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return scored_chunks[:top_k]