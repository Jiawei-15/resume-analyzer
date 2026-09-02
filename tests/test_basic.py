import os
import sqlite3
import threading
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


os.environ["OPENAI_API_KEY"] = ""
os.environ["USE_OPENAI_EMBEDDINGS"] = "False"

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_HISTORY_DB = REPO_ROOT / "history.db"
REPO_HISTORY_DB_EXISTED_AT_IMPORT = REPO_HISTORY_DB.exists()
REPO_HISTORY_DB_STAT_AT_IMPORT = (
    REPO_HISTORY_DB.stat()
    if REPO_HISTORY_DB_EXISTED_AT_IMPORT
    else None
)


@pytest.fixture(autouse=True)
def assert_repo_history_db_unchanged():
    existed = REPO_HISTORY_DB.exists()
    stat = REPO_HISTORY_DB.stat() if existed else None

    yield

    assert REPO_HISTORY_DB.exists() is existed

    if stat is not None:
        current_stat = REPO_HISTORY_DB.stat()
        assert current_stat.st_mtime_ns == stat.st_mtime_ns
        assert current_stat.st_size == stat.st_size


@pytest.fixture(autouse=True)
def clear_vector_store_between_tests():
    from app.services.vector_store import clear_all_embeddings_for_tests

    clear_all_embeddings_for_tests()
    yield
    clear_all_embeddings_for_tests()


@pytest.fixture()
def isolated_database(tmp_path, monkeypatch):
    db_path = tmp_path / "history.db"
    monkeypatch.setenv(
        "AI_RECRUITMENT_COPILOT_DB_PATH",
        str(db_path)
    )

    from app.database import init_db

    init_db()

    return db_path


@pytest.fixture()
def client(isolated_database):
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def install_fake_orchestrator(monkeypatch, match_results):
    from app.services import resume_service

    result_sequence = list(match_results)

    class FakeOrchestrator:
        calls = 0

        def run(self, resume_text, job_description):
            index = min(
                FakeOrchestrator.calls,
                len(result_sequence) - 1
            )
            FakeOrchestrator.calls += 1

            return build_fake_orchestrator_result(
                result_sequence[index]
            )

    monkeypatch.setattr(
        resume_service,
        "RecruitmentOrchestrator",
        FakeOrchestrator
    )


def build_fake_orchestrator_result(config):
    match_score = config["match_score"]
    matched_skills = config["matched_skills"]
    missing_skills = config["missing_skills"]
    feedback = config["feedback"]

    job_profile = config.get(
        "job_profile",
        {
            "job_title": "Backend Developer",
            "industry": "Software",
            "required_skills": ["Python", "FastAPI", "SQLite"],
            "preferred_skills": ["Docker"],
            "soft_skills": ["Communication"],
            "responsibilities": ["Build API services"]
        }
    )

    resume_profile = config.get(
        "resume_profile",
        {
            "candidate_title": "Backend Engineer",
            "technical_skills": ["Python", "FastAPI"],
            "domain_skills": ["Recruiting Automation"],
            "soft_skills": ["Communication"],
            "work_evidence": []
        }
    )

    match_result = {
        "dynamic_match_score": match_score,
        "dynamic_matched_skills": matched_skills,
        "dynamic_missing_skills": missing_skills,
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_requirements": matched_skills,
        "missing_requirements": missing_skills,
        "feedback": feedback,
        "recommendations": [],
        "risk_flags": []
    }

    for key in (
        "semantic_score",
        "semantic_source",
        "score_explanation"
    ):
        if key in config:
            match_result[key] = config[key]

    return {
        "trace": [
            {
                "agent": "Fake Match Pipeline",
                "success": True,
                "result": {}
            }
        ],
        "job_profile": job_profile,
        "resume_profile": resume_profile,
        "evidence_profile": {
            "retrieved_evidence": "Relevant resume evidence.",
            "chunks_count": 1,
            "retrieved_chunks_count": 1
        },
        "match_result": match_result,
        "rewrite_profile": {
            "rewrite_suggestions": [
                "Add clearer SQLite project evidence."
            ],
            "used_fallback": False,
            "llm_error": None
        }
    }


def post_match(client, filename="resume.txt"):
    return post_match_with_content(
        client=client,
        filename=filename,
        resume_text="Python developer with FastAPI, SQLite, Docker, and Git experience.",
        job_description=(
            "We are hiring a backend developer with Python, FastAPI, "
            "SQLite, Docker, and Git experience."
        )
    )


def post_match_with_content(
    client,
    filename,
    resume_text,
    job_description
):
    files = {
        "file": (
            filename,
            resume_text.encode("utf-8"),
            "text/plain"
        )
    }

    data = {
        "job_description": job_description
    }

    return client.post(
        "/match",
        files=files,
        data=data
    )


def test_root_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200


def test_docs_page_loads(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_upload_rejects_missing_file(client):
    response = client.post("/upload")
    assert response.status_code == 422


def test_match_rejects_missing_file_and_job_description(client):
    response = client.post("/match")
    assert response.status_code == 422


def test_analyze_txt_resume(client):
    files = {
        "file": (
            "resume.txt",
            b"Python developer with FastAPI, SQL, Docker, and Git experience.",
            "text/plain"
        )
    }

    response = client.post(
        "/analyze",
        files=files
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["filename"] == "resume.txt"
    assert body["data"]["summary"]["skills_count"] > 0

    found_skills = [
        skill.lower()
        for skill in body["data"]["skills"]["found"]
    ]

    assert "python" in found_skills
    assert "fastapi" in found_skills


def test_match_txt_resume_with_job_description(client):
    files = {
        "file": (
            "resume.txt",
            b"Python developer with FastAPI, SQL, Docker, and Git experience.",
            "text/plain"
        )
    }

    data = {
        "job_description": (
            "We are hiring a backend developer with Python, FastAPI, "
            "SQL, Docker, and Git experience."
        )
    }

    response = client.post(
        "/match",
        files=files,
        data=data
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["filename"] == "resume.txt"

    result = body["data"]

    assert "dynamic_match_score" in result
    assert "dynamic_matched_skills" in result
    assert "dynamic_missing_skills" in result
    assert "job_profile" in result
    assert "resume_profile" in result
    assert "retrieved_evidence" in result
    assert "rewrite_suggestions" in result
    assert "agent_trace" in result
    assert "used_fallback" in result
    assert "llm_error" in result

    assert isinstance(result["dynamic_match_score"],(int, float))
    assert 0.0 <= result["dynamic_match_score"] <= 1.0

    assert isinstance(result["dynamic_matched_skills"], list)
    assert isinstance(result["dynamic_missing_skills"], list)
    assert isinstance(result["job_profile"], dict)
    assert isinstance(result["resume_profile"], dict)
    assert isinstance(result["retrieved_evidence"], str)
    assert isinstance(result["rewrite_suggestions"], list)
    assert isinstance(result["agent_trace"], list)

    assert len(result["agent_trace"]) > 0


@pytest.mark.parametrize(
    ("alpha_filename", "beta_filename"),
    [
        ("alpha-resume.txt", "beta-resume.txt"),
        ("same-name.txt", "same-name.txt")
    ]
)
def test_concurrent_match_requests_use_isolated_vector_contexts(
    client,
    monkeypatch,
    alpha_filename,
    beta_filename
):
    from app.agents import recruitment_agents
    from app.main import app

    alpha_query_waiting = threading.Event()
    beta_finished = threading.Event()

    def controlled_get_embedding(text):
        if "ALPHA_JOB_MARKER" in text:
            alpha_query_waiting.set()

            if not beta_finished.wait(timeout=10):
                raise AssertionError("Timed out waiting for beta request.")

        if "ALPHA_VECTOR_MARKER" in text:
            return [1.0, 0.0]

        if "BETA_VECTOR_MARKER" in text:
            return [0.0, 1.0]

        return [0.5, 0.5]

    monkeypatch.setattr(
        recruitment_agents,
        "get_embedding",
        controlled_get_embedding
    )

    alpha_resume = (
        "ALPHA_VECTOR_MARKER alpha-only resume evidence. "
        "Python FastAPI SQLite Docker Git."
    )
    beta_resume = (
        "BETA_VECTOR_MARKER beta-only resume evidence. "
        "Python FastAPI SQLite Docker Git."
    )
    alpha_job = (
        "ALPHA_JOB_MARKER We are hiring a backend developer with "
        "Python, FastAPI, SQLite, Docker, and Git experience."
    )
    beta_job = (
        "BETA_JOB_MARKER We are hiring a backend developer with "
        "Python, FastAPI, SQLite, Docker, and Git experience."
    )

    def submit_match(filename, resume_text, job_description):
        with TestClient(app) as threaded_client:
            return post_match_with_content(
                client=threaded_client,
                filename=filename,
                resume_text=resume_text,
                job_description=job_description
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        alpha_future = executor.submit(
            submit_match,
            alpha_filename,
            alpha_resume,
            alpha_job
        )

        assert alpha_query_waiting.wait(timeout=10)

        beta_future = executor.submit(
            submit_match,
            beta_filename,
            beta_resume,
            beta_job
        )

        try:
            beta_response = beta_future.result(timeout=10)
        finally:
            beta_finished.set()

        alpha_response = alpha_future.result(timeout=10)

    assert alpha_response.status_code == 200
    assert beta_response.status_code == 200

    alpha_evidence = alpha_response.json()["data"]["retrieved_evidence"]
    beta_evidence = beta_response.json()["data"]["retrieved_evidence"]

    assert "ALPHA_VECTOR_MARKER" in alpha_evidence
    assert "alpha-only resume evidence" in alpha_evidence
    assert "BETA_VECTOR_MARKER" not in alpha_evidence
    assert "beta-only resume evidence" not in alpha_evidence

    assert "BETA_VECTOR_MARKER" in beta_evidence
    assert "beta-only resume evidence" in beta_evidence
    assert "ALPHA_VECTOR_MARKER" not in beta_evidence
    assert "alpha-only resume evidence" not in beta_evidence


def test_vector_context_is_cleaned_after_evidence_failure(
    client,
    monkeypatch
):
    from app.agents import recruitment_agents
    from app.services import vector_store

    class FakeUUID:
        hex = "failed-request-vector-namespace"

    def failing_get_embedding(text):
        if "FAIL_QUERY_MARKER" in text:
            raise RuntimeError("forced embedding failure")

        if "LEAK_VECTOR_MARKER" in text:
            return [1.0, 0.0]

        return [0.0, 1.0]

    monkeypatch.setattr(
        recruitment_agents.uuid,
        "uuid4",
        lambda: FakeUUID()
    )
    monkeypatch.setattr(
        recruitment_agents,
        "get_embedding",
        failing_get_embedding
    )

    response = post_match_with_content(
        client=client,
        filename="failed-evidence.txt",
        resume_text=(
            "LEAK_VECTOR_MARKER temporary resume evidence. "
            "Python FastAPI SQLite Docker Git."
        ),
        job_description=(
            "FAIL_QUERY_MARKER We are hiring a backend developer with "
            "Python, FastAPI, SQLite, Docker, and Git experience."
        )
    )

    assert response.status_code == 200

    result = response.json()["data"]

    assert result["retrieved_evidence"] == ""
    assert result["evidence_profile"]["error"] == "Evidence retrieval failed."
    assert vector_store.search_embedding(
        [1.0, 0.0],
        namespace="failed-request-vector-namespace"
    ) == []


def test_vector_store_requires_explicit_namespace():
    from app.services.vector_store import (
        add_embedding,
        clear_embeddings,
        search_embedding,
        search_embedding_with_scores
    )

    with pytest.raises(TypeError):
        add_embedding([1.0], "resume evidence")

    with pytest.raises(TypeError):
        clear_embeddings()

    with pytest.raises(TypeError):
        search_embedding([1.0])

    with pytest.raises(TypeError):
        search_embedding_with_scores([1.0])

    with pytest.raises(ValueError, match="namespace is required"):
        add_embedding(
            [1.0],
            "resume evidence",
            namespace=""
        )


def test_tfidf_semantic_scores_related_text_above_unrelated():
    from app.services.embedding_service import calculate_semantic_similarity

    job_description = (
        "Hiring a backend engineer for Python FastAPI APIs, SQLite data "
        "storage, Docker deployment, and pytest automation."
    )
    related_resume = (
        "Built Python FastAPI services with SQLite persistence, Docker "
        "containers, and pytest integration tests."
    )
    unrelated_resume = (
        "Prepared espresso drinks, arranged pastry displays, sanitized "
        "kitchen stations, and handled cafe inventory."
    )

    related = calculate_semantic_similarity(
        related_resume,
        job_description
    )
    unrelated = calculate_semantic_similarity(
        unrelated_resume,
        job_description
    )

    assert related["semantic_source"] == "tfidf_fallback"
    assert unrelated["semantic_source"] == "tfidf_fallback"
    assert 0.0 <= related["semantic_score"] <= 100.0
    assert 0.0 <= unrelated["semantic_score"] <= 100.0
    assert related["semantic_score"] > unrelated["semantic_score"]
    assert unrelated["semantic_score"] == 0.0


def test_tfidf_semantic_scores_identical_text_near_maximum():
    from app.services.embedding_service import calculate_semantic_similarity

    text = (
        "Python FastAPI SQLite Docker pytest backend API development "
        "with reliable production monitoring."
    )

    result = calculate_semantic_similarity(
        text,
        text
    )

    assert result["semantic_source"] == "tfidf_fallback"
    assert result["semantic_score"] == 100.0


@pytest.mark.parametrize(
    ("resume_text", "job_description"),
    [
        ("", "Python backend role."),
        ("Python backend experience.", ""),
        ("!!! ... ;;;", "??? --- !!!"),
        ("the and or", "with for by")
    ]
)
def test_tfidf_semantic_handles_empty_or_non_comparable_text(
    resume_text,
    job_description
):
    from app.services.embedding_service import calculate_semantic_similarity

    result = calculate_semantic_similarity(
        resume_text,
        job_description
    )

    assert result["semantic_source"] == "tfidf_fallback"
    assert result["semantic_score"] == 0.0
    assert "no comparable text terms" in result["score_explanation"]


def test_tfidf_semantic_is_stable_for_case_and_punctuation():
    from app.services.embedding_service import calculate_semantic_similarity

    noisy = calculate_semantic_similarity(
        "PYTHON, FastAPI; SQL!!! Docker???",
        "python fastapi sql docker"
    )
    clean = calculate_semantic_similarity(
        "python fastapi sql docker",
        "python fastapi sql docker"
    )

    assert noisy["semantic_source"] == "tfidf_fallback"
    assert noisy["semantic_score"] == clean["semantic_score"]
    assert noisy["semantic_score"] == 100.0


def test_tfidf_semantic_does_not_score_letter_overlap_as_semantic_match():
    from app.services.embedding_service import calculate_semantic_similarity

    result = calculate_semantic_similarity(
        "catering hospitality kitchen service",
        "python api backend docker"
    )

    assert result["semantic_source"] == "tfidf_fallback"
    assert result["semantic_score"] == 0.0


def test_openai_embedding_error_uses_tfidf_fallback(monkeypatch):
    from app.services import embedding_service

    service = embedding_service._embedding_service

    monkeypatch.setattr(
        service,
        "use_openai",
        True
    )
    monkeypatch.setattr(
        service,
        "client",
        object()
    )

    def unavailable_embedding(text):
        raise embedding_service.OpenAIError("embedding service unavailable")

    monkeypatch.setattr(
        service,
        "_embed_with_openai",
        unavailable_embedding
    )

    result = embedding_service.calculate_semantic_similarity(
        "Python FastAPI SQLite backend developer.",
        "Hiring Python FastAPI backend engineer with SQLite."
    )

    assert result["semantic_source"] == "tfidf_fallback"
    assert result["semantic_score"] > 0.0
    assert "OpenAI embedding similarity was unavailable" in result["score_explanation"]


def test_semantic_programming_errors_are_not_treated_as_fallback(monkeypatch):
    from app.services import embedding_service

    service = embedding_service._embedding_service

    monkeypatch.setattr(
        service,
        "use_openai",
        True
    )
    monkeypatch.setattr(
        service,
        "client",
        object()
    )
    monkeypatch.setattr(
        service,
        "_openai_semantic_similarity",
        lambda resume_text, job_description: (_ for _ in ()).throw(
            TypeError("programming bug")
        )
    )

    with pytest.raises(TypeError, match="programming bug"):
        embedding_service.calculate_semantic_similarity(
            "Python FastAPI backend developer.",
            "Hiring Python FastAPI backend engineer."
        )


def test_match_semantic_programming_error_is_not_success(
    isolated_database,
    monkeypatch
):
    from app.main import app
    from app.agents import recruitment_agents

    def broken_semantic_score(resume_text, job_description):
        raise TypeError("semantic programming bug")

    monkeypatch.setattr(
        recruitment_agents,
        "calculate_semantic_similarity",
        broken_semantic_score
    )

    with TestClient(
        app,
        raise_server_exceptions=False
    ) as test_client:
        response = post_match_with_content(
            client=test_client,
            filename="semantic-programming-error.txt",
            resume_text="Python FastAPI backend developer with SQLite.",
            job_description=(
                "Hiring a Python FastAPI backend engineer with SQLite "
                "and reliable API delivery experience."
            )
        )

        assert response.status_code == 500
        assert test_client.get("/history").json()["data"] == []


def test_match_and_history_include_tfidf_semantic_score(client):
    response = post_match_with_content(
        client=client,
        filename="semantic-fallback.txt",
        resume_text=(
            "Built Python FastAPI backend APIs with SQLite persistence, "
            "Docker deployment, Git workflows, and pytest coverage."
        ),
        job_description=(
            "We need a Python FastAPI backend engineer with SQLite, "
            "Docker, Git, and automated testing experience."
        )
    )

    assert response.status_code == 200

    result = response.json()["data"]

    assert result["semantic_source"] == "tfidf_fallback"
    assert 0.0 <= result["semantic_score"] <= 100.0
    assert result["semantic_score"] > 0.0
    assert "TF-IDF" in result["score_explanation"]
    assert 0.0 <= result["match_score"] <= 1.0

    history_response = client.get("/history")
    assert history_response.status_code == 200

    history = history_response.json()["data"]

    assert history[0]["filename"] == "semantic-fallback.txt"
    assert history[0]["semantic_score"] == result["semantic_score"]
    assert history[0]["semantic_source"] == "tfidf_fallback"


def test_match_persists_history_row_and_returns_it(
    client,
    monkeypatch
):
    install_fake_orchestrator(
        monkeypatch,
        [
            {
                "match_score": 0.67,
                "semantic_score": 0.91,
                "semantic_source": "unit_test_semantic",
                "score_explanation": "Controlled persistence score.",
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": ["SQLite"],
                "feedback": [
                    "Strong backend alignment.",
                    "Add SQLite project evidence."
                ]
            }
        ]
    )

    response = post_match(
        client,
        filename="history-candidate.txt"
    )

    assert response.status_code == 200

    result = response.json()["data"]

    assert result["filename"] == "history-candidate.txt"
    assert result["dynamic_match_score"] == 0.67
    assert result["dynamic_matched_skills"] == ["Python", "FastAPI"]
    assert result["dynamic_missing_skills"] == ["SQLite"]

    history_response = client.get("/history")
    assert history_response.status_code == 200

    history = history_response.json()["data"]

    assert len(history) == 1

    row = history[0]

    assert row["filename"] == "history-candidate.txt"
    assert row["match_score"] == 0.67
    assert row["semantic_score"] == 0.91
    assert row["semantic_source"] == "unit_test_semantic"
    assert row["score_explanation"] == "Controlled persistence score."
    assert row["resume_skills"] == [
        "Python",
        "FastAPI",
        "Recruiting Automation",
        "Communication"
    ]
    assert row["matched_skills"] == ["Python", "FastAPI"]
    assert row["missing_skills"] == ["SQLite"]
    assert row["feedback"] == [
        "Strong backend alignment.",
        "Add SQLite project evidence."
    ]


def test_history_keeps_recent_unique_filename_behavior(
    client,
    isolated_database,
    monkeypatch
):
    install_fake_orchestrator(
        monkeypatch,
        [
            {
                "match_score": 0.25,
                "semantic_score": 0.4,
                "semantic_source": "first_pass",
                "score_explanation": "First duplicate result.",
                "matched_skills": ["Python"],
                "missing_skills": ["SQLite"],
                "feedback": ["First duplicate feedback."]
            },
            {
                "match_score": 0.9,
                "semantic_score": 0.95,
                "semantic_source": "unique_pass",
                "score_explanation": "Unique file result.",
                "matched_skills": ["Python", "FastAPI", "SQLite"],
                "missing_skills": [],
                "feedback": ["Unique file feedback."]
            },
            {
                "match_score": 0.75,
                "semantic_score": 0.8,
                "semantic_source": "second_pass",
                "score_explanation": "Latest duplicate result.",
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": ["SQLite"],
                "feedback": ["Latest duplicate feedback."]
            }
        ]
    )

    first_duplicate = post_match(
        client,
        filename="duplicate.txt"
    )
    unique = post_match(
        client,
        filename="unique.txt"
    )
    second_duplicate = post_match(
        client,
        filename="duplicate.txt"
    )

    assert first_duplicate.status_code == 200
    assert unique.status_code == 200
    assert second_duplicate.status_code == 200

    with closing(sqlite3.connect(isolated_database)) as conn:
        rows = conn.execute(
            "SELECT filename FROM analyses ORDER BY id"
        ).fetchall()

    filenames = [
        row[0]
        for row in rows
    ]

    assert filenames == [
        "duplicate.txt",
        "unique.txt",
        "duplicate.txt"
    ]

    history = client.get("/history").json()["data"]
    history_filenames = [
        row["filename"]
        for row in history
    ]

    assert history_filenames.count("duplicate.txt") == 1
    assert history_filenames.count("unique.txt") == 1
    assert history[0]["filename"] == "duplicate.txt"
    assert history[0]["match_score"] == 0.75
    assert history[0]["semantic_source"] == "second_pass"
    assert history[0]["matched_skills"] == ["Python", "FastAPI"]
    assert history[0]["feedback"] == ["Latest duplicate feedback."]


def test_persistence_programming_error_is_not_silently_swallowed(
    client,
    monkeypatch
):
    install_fake_orchestrator(
        monkeypatch,
        [
            {
                "match_score": 0.5,
                "matched_skills": ["Python"],
                "missing_skills": ["SQLite"],
                "feedback": ["Persistence should fail visibly."]
            }
        ]
    )

    from app.services import resume_service

    def broken_save_analysis(**kwargs):
        raise TypeError("contract mismatch")

    monkeypatch.setattr(
        resume_service,
        "save_analysis",
        broken_save_analysis
    )

    with pytest.raises(TypeError, match="contract mismatch"):
        post_match(
            client,
            filename="broken-persistence.txt"
        )


def test_repository_history_db_is_not_used_during_tests(client):
    response = client.get("/history")

    assert response.status_code == 200

    if not REPO_HISTORY_DB_EXISTED_AT_IMPORT:
        assert not REPO_HISTORY_DB.exists()
    else:
        current_stat = REPO_HISTORY_DB.stat()
        assert current_stat.st_mtime_ns == REPO_HISTORY_DB_STAT_AT_IMPORT.st_mtime_ns
        assert current_stat.st_size == REPO_HISTORY_DB_STAT_AT_IMPORT.st_size


def test_match_rejects_short_job_description(client):
    files = {
        "file": (
            "resume.txt",
            b"Python developer with FastAPI experience.",
            "text/plain"
        )
    }

    data = {
        "job_description": "Python"
    }

    response = client.post(
        "/match",
        files=files,
        data=data
    )

    assert response.status_code == 400
    assert "too short" in response.json()["detail"].lower()


def test_upload_rejects_unsupported_file_type(client):
    files = {
        "file": (
            "resume.exe",
            b"fake content",
            "application/octet-stream"
        )
    }

    response = client.post(
        "/upload",
        files=files
    )

    assert response.status_code == 400
    assert "supported" in response.json()["detail"].lower()


def test_history_returns_list(client):
    response = client.get("/history")

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert isinstance(body["data"], list)
