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