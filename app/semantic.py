# app/semantic.py

from openai import OpenAI
from math import sqrt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

from app.config import OPENAI_API_KEY, USE_OPENAI_EMBEDDINGS


def cosine_similarity(vec1, vec2):
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sqrt(sum(a * a for a in vec1))
    norm2 = sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def local_semantic_match(resume_text: str, job_text: str) -> float:
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        score = sk_cosine(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        return round(float(score), 2)
    except Exception:
        resume_words = set(resume_text.lower().split())
        job_words = set(job_text.lower().split())
        overlap = resume_words.intersection(job_words)
        total = len(job_words)
        return round(len(overlap) / total, 2) if total > 0 else 0.0


def openai_semantic_match(resume_text: str, job_text: str) -> float:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[resume_text, job_text]
    )
    resume_vector = response.data[0].embedding
    job_vector = response.data[1].embedding
    score = cosine_similarity(resume_vector, job_vector)
    calibrated_score = max(0, min(1, (score - 0.75) / 0.25))
    return round(float(calibrated_score), 2)


def semantic_match(resume_text: str, job_text: str) -> float:
    if USE_OPENAI_EMBEDDINGS and OPENAI_API_KEY:
        try:
            return openai_semantic_match(resume_text, job_text)
        except Exception:
            pass

    return local_semantic_match(resume_text, job_text)


def get_semantic_source() -> str:
    if USE_OPENAI_EMBEDDINGS and OPENAI_API_KEY:
        return "openai"
    return "local"