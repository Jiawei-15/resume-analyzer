from openai import OpenAI
from math import sqrt

from app.config import OPENAI_API_KEY, USE_OPENAI_EMBEDDINGS


def cosine_similarity(vec1, vec2):
    dot = sum(a * b for a, b in zip(vec1, vec2))

    norm1 = sqrt(sum(a * a for a in vec1))
    norm2 = sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)


def basic_semantic_match(resume_text: str, job_text: str) -> float:
    resume_words = set(resume_text.lower().split())
    job_words = set(job_text.lower().split())

    overlap = resume_words.intersection(job_words)

    total = len(job_words)

    if total == 0:
        return 0.0

    return round(len(overlap) / total, 2)


def openai_semantic_match(resume_text: str, job_text: str) -> float:
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[resume_text, job_text]
    )

    resume_vector = response.data[0].embedding
    job_vector = response.data[1].embedding

    score = cosine_similarity(
        resume_vector,
        job_vector
    )

    return round(float(score), 2)


def semantic_match(resume_text: str, job_text: str) -> float:
    if USE_OPENAI_EMBEDDINGS and OPENAI_API_KEY:
        try:
            return openai_semantic_match(resume_text, job_text)
        except Exception:
            return basic_semantic_match(
                resume_text,
                job_text
            )

    return basic_semantic_match(
        resume_text,
        job_text
    )