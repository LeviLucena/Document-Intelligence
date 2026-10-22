import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import auth
from .config import settings
from .ingest import chunk_pages, extract_pages
from .providers import get_provider
from .rag import answer
from .store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
log = logging.getLogger("docintel")

STATIC = Path(__file__).parent / "static"


class LoginRequest(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = VectorStore(settings.data_dir)
    app.state.provider = get_provider()
    log.info("provider=%s docs=%d", app.state.provider.name, len(app.state.store.documents()))
    yield


app = FastAPI(title="Document Intelligence API", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "provider": app.state.provider.name}


@app.get("/auth/status")
def auth_status():
    return {"enabled": auth.enabled()}


@app.post("/auth/login")
def login(req: LoginRequest, request: Request):
    if not auth.enabled():
        raise HTTPException(400, "Autenticação desativada.")
    if not auth.check_credentials(req.email, req.password, request):
        raise HTTPException(401, "E-mail ou senha incorretos.")
    email = req.email.strip().lower()
    return {"token": auth.create_token(email), "email": email}


@app.get("/auth/me")
def me(user: str = Depends(auth.require_auth)):
    return {"email": user}


@app.get("/documents", dependencies=[Depends(auth.require_auth)])
def list_documents():
    return app.state.store.documents()


@app.post("/documents", status_code=201, dependencies=[Depends(auth.require_auth)])
async def upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Envie um arquivo PDF.")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Arquivo acima de {settings.max_upload_mb} MB.")
    try:
        pages = extract_pages(data)
    except Exception:
        raise HTTPException(400, "Não consegui ler o PDF.")
    chunks = chunk_pages(pages, settings.chunk_chars, settings.chunk_overlap)
    if not chunks:
        raise HTTPException(422, "O PDF não tem texto extraível (talvez seja escaneado).")
    vectors = app.state.provider.embed([c.text for c in chunks])
    app.state.store.add(file.filename, [(c.page, c.text) for c in chunks], vectors)
    log.info("indexed %s pages=%d chunks=%d", file.filename, len(pages), len(chunks))
    return {"name": file.filename, "pages": len(pages), "chunks": len(chunks)}


@app.delete("/documents/{name}", dependencies=[Depends(auth.require_auth)])
def delete(name: str):
    if not app.state.store.remove(name):
        raise HTTPException(404, "Documento não encontrado.")
    return {"deleted": name}


@app.post("/ask", dependencies=[Depends(auth.require_auth)])
def ask(req: AskRequest):
    if not app.state.store.items:
        raise HTTPException(409, "Nenhum documento indexado ainda.")
    return answer(req.question, app.state.store, app.state.provider, req.top_k)
