import os
import math
from typing import List

from openai import OpenAI


class EmbeddingService:
    """
    Provides text embeddings.

    If USE_OPENAI_EMBEDDINGS=True, it uses OpenAI embeddings.
    Otherwise, it uses a local fallback embedding so the app can still run.
    """

    def __init__(self):
        self.use_openai = os.getenv("USE_OPENAI_EMBEDDINGS", "False") == "True"
        self.api_key = os.getenv("OPENAI_API_KEY")

        self.client = None

        if self.use_openai and self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return []

        if self.use_openai and self.client is not None:
            return self._embed_with_openai(text)

        return self._embed_locally(text)

    def _embed_with_openai(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        return response.data[0].embedding

    def _embed_locally(self, text: str) -> List[float]:
        text = text.lower()
        vector = [0.0] * 26

        for char in text:
            if "a" <= char <= "z":
                index = ord(char) - ord("a")
                vector[index] += 1.0

        return self._normalize(vector)

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

    def _normalize(self, vector: List[float]) -> List[float]:
        magnitude = math.sqrt(
            sum(value * value for value in vector)
        )

        if magnitude == 0:
            return vector

        return [
            value / magnitude
            for value in vector
        ]


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