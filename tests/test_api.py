import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "provider": "local"}


def test_ask_without_documents_is_409(client):
    assert client.post("/ask", json={"question": "qualquer coisa"}).status_code == 409


def test_rejects_non_pdf(client):
    r = client.post("/documents", files={"file": ("a.txt", b"oi", "text/plain")})
    assert r.status_code == 400


def test_upload_ask_and_delete(client, pdf_bytes):
    up = client.post("/documents", files={"file": ("plano.pdf", pdf_bytes, "application/pdf")})
    assert up.status_code == 201 and up.json()["pages"] == 2

    r = client.post("/ask", json={"question": "Qual a receita projetada do segundo trimestre?"})
    assert r.status_code == 200
    body = r.json()
    assert body["citations"][0]["doc"] == "plano.pdf" and body["citations"][0]["page"] == 2
    assert "[1]" in body["answer"]
    assert {"total_ms", "input_tokens", "output_tokens", "estimated_cost_usd"} <= body["metrics"].keys()

    assert client.delete("/documents/plano.pdf").status_code == 200
    assert client.get("/documents").json() == []


def test_question_validation(client):
    assert client.post("/ask", json={"question": "a"}).status_code == 422
