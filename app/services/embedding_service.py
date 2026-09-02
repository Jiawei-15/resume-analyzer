import os
import math
import re
from typing import Any, Dict, List

from openai import OpenAI, OpenAIError
from sklearn.feature_extraction.text import (
    ENGLISH_STOP_WORDS,
    HashingVectorizer,
    TfidfVectorizer
)
from app.config import get_openai_timeout_seconds
from app.services.openai_retry import call_openai_with_retries


OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_SEMANTIC_SOURCE = f"openai_embedding:{OPENAI_EMBEDDING_MODEL}"
TFIDF_SEMANTIC_SOURCE = "tfidf_fallback"
_TOKEN_PATTERN = re.compile(
    r"c\+\+|c#|[a-z0-9]+(?:[+#.][a-z0-9]+)*"
)


def _tokenize_for_similarity(text: str) -> List[str]:
    if text is None:
        return []

    tokens = _TOKEN_PATTERN.findall(str(text).lower())

    return [
        token
        for token in tokens
        if token not in ENGLISH_STOP_WORDS
    ]


_LOCAL_EMBEDDING_VECTORIZER = HashingVectorizer(
    analyzer=_tokenize_for_similarity,
    alternate_sign=False,
    norm="l2",
    n_features=512
)


class EmbeddingService:
    """
    Provides text embeddings and semantic similarity scoring.

    If USE_OPENAI_EMBEDDINGS=True, it uses OpenAI embeddings.
    Otherwise, it uses local word-level text features so the app can still run.
    """

    def __init__(self):
        self.use_openai = os.getenv("USE_OPENAI_EMBEDDINGS", "False") == "True"
        self.api_key = os.getenv("OPENAI_API_KEY")

        self.client = None

        if self.use_openai and self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=get_openai_timeout_seconds(),
                max_retries=0
            )

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return []

        if self.use_openai and self.client is not None:
            return self._embed_with_openai(text)

        return self._embed_locally(text)

    def _embed_with_openai(self, text: str) -> List[float]:
        response = call_openai_with_retries(
            lambda: self.client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=text
            ),
            operation_name="embeddings"
        )

        return response.data[0].embedding

    def _embed_locally(self, text: str) -> List[float]:
        vector = _LOCAL_EMBEDDING_VECTORIZER.transform([text])
        return vector.toarray()[0].tolist()

    def semantic_similarity(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict[str, Any]:
        if (
            not _tokenize_for_similarity(resume_text)
            or not _tokenize_for_similarity(job_description)
        ):
            return self._semantic_result(
                score=0.0,
                source=TFIDF_SEMANTIC_SOURCE,
                explanation=(
                    "Semantic score is 0 because the resume or job "
                    "description has no comparable text terms."
                )
            )

        if self.use_openai and self.client is not None:
            try:
                score = self._openai_semantic_similarity(
                    resume_text,
                    job_description
                )

                return self._semantic_result(
                    score=score,
                    source=OPENAI_SEMANTIC_SOURCE,
                    explanation=(
                        "Semantic score uses OpenAI text embeddings and "
                        "cosine similarity on a 0-100 scale."
                    )
                )

            except OpenAIError as exc:
                result = self._tfidf_semantic_similarity(
                    resume_text,
                    job_description
                )
                result["score_explanation"] = (
                    "OpenAI embedding similarity was unavailable "
                    f"({type(exc).__name__}); used local word-level "
                    "TF-IDF cosine similarity on a 0-100 scale."
                )
                return result

        return self._tfidf_semantic_similarity(
            resume_text,
            job_description
        )

    def _openai_semantic_similarity(
        self,
        resume_text: str,
        job_description: str
    ) -> float:
        resume_embedding = self._embed_with_openai(resume_text)
        job_embedding = self._embed_with_openai(job_description)

        return self.cosine_similarity(
            resume_embedding,
            job_embedding
        ) * 100.0

    def _tfidf_semantic_similarity(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict[str, Any]:
        vectorizer = TfidfVectorizer(
            analyzer=_tokenize_for_similarity,
            norm="l2"
        )

        matrix = vectorizer.fit_transform(
            [
                resume_text,
                job_description
            ]
        )

        if matrix.shape[1] == 0:
            score = 0.0
        else:
            score = float(
                matrix[0].multiply(matrix[1]).sum()
            ) * 100.0

        return self._semantic_result(
            score=score,
            source=TFIDF_SEMANTIC_SOURCE,
            explanation=(
                "Semantic score uses local word-level TF-IDF cosine "
                "similarity on a 0-100 scale."
            )
        )

    def _semantic_result(
        self,
        score: float,
        source: str,
        explanation: str
    ) -> Dict[str, Any]:
        return {
            "semantic_score": self._normalize_score(score),
            "semantic_source": source,
            "score_explanation": explanation
        }

    def _normalize_score(self, score: float) -> float:
        if not math.isfinite(score):
            return 0.0

        return round(
            min(
                max(score, 0.0),
                100.0
            ),
            2
        )

    def cosine_similarity(
        self,
        vector_a: List[float],
        vector_b: List[float]
    ) -> float:
        if not vector_a or not vector_b:
            return 0.0

        dot_product = sum(
            a * b
            for a, b in zip(vector_a, vector_b)
        )

        magnitude_a = math.sqrt(
            sum(a * a for a in vector_a)
        )

        magnitude_b = math.sqrt(
            sum(b * b for b in vector_b)
        )

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)


_embedding_service = EmbeddingService()


def get_embedding(text: str) -> List[float]:
    """
    Compatibility wrapper for existing code.

    Existing agents call:
    get_embedding(text)

    Internally this uses EmbeddingService.
    """

    return _embedding_service.embed_text(text)


def cosine_similarity(
    vector_a: List[float],
    vector_b: List[float]
) -> float:
    """
    Compatibility wrapper for vector store code.
    """

    return _embedding_service.cosine_similarity(
        vector_a,
        vector_b
    )


def calculate_semantic_similarity(
    resume_text: str,
    job_description: str
) -> Dict[str, Any]:
    return _embedding_service.semantic_similarity(
        resume_text,
        job_description
    )
