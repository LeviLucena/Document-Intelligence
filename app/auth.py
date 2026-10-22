"""Login simples: credenciais únicas no .env e token assinado com HMAC (sem dependências extras)."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

from .config import settings

_fallback_secret = secrets.token_bytes(32)
_failures: dict[str, deque] = defaultdict(deque)
MAX_FAILURES, WINDOW_S = 5, 300


def enabled() -> bool:
    return bool(settings.auth_password)


def _key() -> bytes:
    return settings.auth_secret.encode() if settings.auth_secret else _fallback_secret


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _sign(body: str) -> str:
    return _b64(hmac.new(_key(), body.encode(), hashlib.sha256).digest())


def create_token(email: str) -> str:
    payload = _b64(json.dumps({"sub": email, "exp": int(time.time()) + settings.token_ttl_hours * 3600}).encode())
    return f"{payload}.{_sign(payload)}"


def verify_token(token: str) -> str | None:
    try:
        payload, sig = token.split(".")
        if not hmac.compare_digest(sig, _sign(payload)):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return data["sub"] if data["exp"] > time.time() else None
    except Exception:
        return None


def check_credentials(email: str, password: str, request: Request) -> bool:
    """Valida login com limite de tentativas por IP (5 falhas / 5 min)."""
    ip = request.client.host if request.client else "?"
    now = time.time()
    attempts = _failures[ip]
    while attempts and now - attempts[0] > WINDOW_S:
        attempts.popleft()
    if len(attempts) >= MAX_FAILURES:
        raise HTTPException(429, "Muitas tentativas. Aguarde alguns minutos.")
    ok_email = hmac.compare_digest(email.strip().lower().encode(), settings.auth_email.lower().encode())
    ok_pass = hmac.compare_digest(password.encode(), settings.auth_password.encode())
    if ok_email and ok_pass:
        attempts.clear()
        return True
    attempts.append(now)
    return False


def require_auth(authorization: str | None = Header(default=None)) -> str:
    if not enabled():
        return "anonymous"
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    user = verify_token(token) if token else None
    if not user:
        raise HTTPException(401, "Sessão inválida ou expirada.")
    return user
