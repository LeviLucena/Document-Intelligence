from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    # "local" roda sem AWS (embeddings por hash + resposta extrativa); "bedrock" usa a AWS.
    provider: str = "local"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0"

    data_dir: Path = ROOT / "data"
    chunk_chars: int = 900
    chunk_overlap: int = 150
    top_k: int = 4
    max_upload_mb: int = 20

    # Login: com AUTH_PASSWORD vazio a autenticação fica desligada (uso local sem tela de login).
    auth_email: str = "admin@docintel.local"
    auth_password: str = ""
    auth_secret: str = ""  # chave para assinar tokens; se vazia, usa uma aleatória por execução
    token_ttl_hours: int = 12

    # USD por 1.000 tokens (entrada, saída) — ajuste conforme a tabela vigente da AWS.
    price_in_per_1k: float = 0.00025
    price_out_per_1k: float = 0.00125


settings = Settings()
