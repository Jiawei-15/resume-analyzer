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

    response = client.post("/analyze", files=files)

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["filename"] == "resume.txt"
    assert body["data"]["summary"]["skills_count"] > 0
    assert "python" in body["data"]["skills"]["found"]
    assert "fastapi" in body["data"]["skills"]["found"]

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

    response = client.post("/match", files=files, data=data)

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["filename"] == "resume.txt"

    summary = body["data"]["summary"]
    skills = body["data"]["skills"]
    analysis = body["data"]["analysis"]

    assert 0.0 <= summary["match_score"] <= 1.0
    assert 0.0 <= summary["semantic_score"] <= 1.0
    assert summary["semantic_source"] in ("openai", "local")

    assert "python" in skills["matched_skills"]
    assert "fastapi" in skills["matched_skills"]
    assert isinstance(analysis["feedback"], list)

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

    response = client.post("/match", files=files, data=data)

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

    response = client.post("/upload", files=files)

    assert response.status_code == 400
    assert "supported" in response.json()["detail"].lower()

def test_history_returns_list():
    response = client.get("/history")

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert isinstance(body["data"], list)