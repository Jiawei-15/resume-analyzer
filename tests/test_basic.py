from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_page_loads():
    response = client.get("/")
    assert response.status_code == 200


def test_docs_page_loads():
    response = client.get("/docs")
    assert response.status_code == 200


def test_upload_rejects_missing_file():
    response = client.post("/upload")
    assert response.status_code == 422


def test_match_rejects_missing_file_and_job_description():
    response = client.post("/match")
    assert response.status_code == 422


def test_analyze_txt_resume():
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


def test_match_txt_resume_with_job_description():
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

    assert isinstance(result["dynamic_match_score"], float)
    assert 0.0 <= result["dynamic_match_score"] <= 1.0

    assert isinstance(result["dynamic_matched_skills"], list)
    assert isinstance(result["dynamic_missing_skills"], list)
    assert isinstance(result["job_profile"], dict)
    assert isinstance(result["resume_profile"], dict)
    assert isinstance(result["retrieved_evidence"], str)
    assert isinstance(result["rewrite_suggestions"], list)
    assert isinstance(result["agent_trace"], list)

    assert len(result["agent_trace"]) > 0


def test_match_rejects_short_job_description():
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


def test_upload_rejects_unsupported_file_type():
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


def test_history_returns_list():
    response = client.get("/history")

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert isinstance(body["data"], list)