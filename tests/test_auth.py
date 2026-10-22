import pytest
from fastapi.testclient import TestClient

from app import auth
from app.config import settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_email", "admin@x.com")
    monkeypatch.setattr(settings, "auth_password", "segredo-forte")
    monkeypatch.setattr(settings, "auth_secret", "chave-de-teste")
    auth._failures.clear()
    with TestClient(app) as c:
        yield c


def _login(client, email="admin@x.com", password="segredo-forte"):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_status_enabled(client):
    assert client.get("/auth/status").json() == {"enabled": True}


def test_protected_routes_require_token(client):
    assert client.get("/documents").status_code == 401
    assert client.post("/ask", json={"question": "qualquer coisa"}).status_code == 401
    assert client.get("/health").status_code == 200  # público


def test_login_ok_and_token_works(client):
    r = _login(client, email="  ADMIN@x.com ")
    assert r.status_code == 200
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    assert client.get("/auth/me", headers=headers).json() == {"email": "admin@x.com"}
    assert client.get("/documents", headers=headers).status_code == 200


def test_wrong_password_is_401(client):
    assert _login(client, password="errada").status_code == 401


def test_tampered_or_expired_token_rejected(client, monkeypatch):
    token = _login(client).json()["token"]
    bad = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    assert client.get("/documents", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    monkeypatch.setattr(settings, "token_ttl_hours", -1)
    expired = auth.create_token("admin@x.com")
    assert client.get("/documents", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_brute_force_is_throttled(client):
    codes = [_login(client, password=f"x{i}").status_code for i in range(7)]
    assert codes[:5] == [401] * 5 and codes[5:] == [429, 429]
    assert _login(client).status_code == 429  # mesmo a senha certa fica bloqueada na janela
