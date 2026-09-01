from threading import RLock
from typing import Any, Dict, List, Tuple

from app.services.embedding_service import cosine_similarity


_stored_vectors_by_namespace: Dict[str, List[Dict[str, Any]]] = {}
_store_lock = RLock()


def _namespace_key(namespace: str) -> str:
    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("Vector store namespace is required.")

    return namespace


def clear_embeddings(*, namespace: str) -> None:
    """
    Clear stored vectors for one request namespace.
    """

    with _store_lock:
        _stored_vectors_by_namespace.pop(
            _namespace_key(namespace),
            None
        )


def clear_all_embeddings_for_tests() -> None:
    """
    Clear the in-memory store between isolated tests.
    """

    with _store_lock:
        _stored_vectors_by_namespace.clear()


def add_embedding(
    embedding: List[float],
    text: str,
    *,
    namespace: str
) -> None:
    """
    Add one text chunk and its embedding to the in-memory vector store.
    """

    namespace_key = _namespace_key(namespace)

    with _store_lock:
        _stored_vectors_by_namespace.setdefault(
            namespace_key,
            []
        ).append({
            "embedding": embedding,
            "text": text
        })


def search_embedding(
    query_embedding: List[float],
    top_k: int = 3,
    *,
    namespace: str
) -> List[str]:
    """
    Search the most relevant text chunks by cosine similarity.

    Returns only text chunks to stay compatible with your current
    EvidenceRetrievalAgent.
    """

    stored_vectors = _get_stored_vectors_snapshot(namespace)
    scored_chunks: List[Tuple[float, str]] = []

    for item in stored_vectors:
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
    top_k: int = 3,
    *,
    namespace: str
) -> List[Dict[str, Any]]:
    """
    Search the most relevant text chunks and return scores.

    This is for the future evidence_map upgrade.
    Current code may not use it yet.
    """

    stored_vectors = _get_stored_vectors_snapshot(namespace)
    scored_chunks: List[Dict[str, Any]] = []

    for index, item in enumerate(stored_vectors):
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


def _get_stored_vectors_snapshot(
    namespace: str
) -> List[Dict[str, Any]]:
    with _store_lock:
        return [
            {
                "embedding": list(item["embedding"]),
                "text": item["text"]
            }
            for item in _stored_vectors_by_namespace.get(
                _namespace_key(namespace),
                []
            )
        ]
