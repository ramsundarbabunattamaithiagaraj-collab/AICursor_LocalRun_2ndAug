"""Centralized application configuration.

Loads defaults from YAML (config/config.yaml) and overlays sensitive/
environment-specific values from environment variables (.env). This keeps
secrets out of source control while allowing non-sensitive defaults to live
in version-controlled YAML, per project standards (never hardcode secrets).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_ROOT / ".env")


class AppSettings(BaseModel):
    name: str = "RetailIQ Platform"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class DatabaseSettings(BaseModel):
    url: str = "sqlite:///./data/retailiq.db"
    echo: bool = False


class AuthSettings(BaseModel):
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 1440
    secret_key: str = "insecure-dev-secret-change-me"


class RagSettings(BaseModel):
    enabled: bool = True
    vector_db: str = "chromadb"
    persist_directory: str = "./data/chroma"
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    fallback_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    image_embedding_model: str = "openai/clip-vit-base-patch32"
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k: int = 5


class AiFrameworkSettings(BaseModel):
    name: str = "CrewAI"
    default_llm: str = "gpt-4o-mini"
    groq_model: str = "groq/llama-3.3-70b-versatile"
    temperature: float = 0.2
    memory_enabled: bool = True
    retry: int = 3
    max_iterations: int = 5


class LoggingSettings(BaseModel):
    level: str = "INFO"
    file: str = "./logs/retailiq.log"
    max_bytes: int = 5_242_880
    backup_count: int = 5


class DomainSettings(BaseModel):
    name: str = "Retail"


class Settings(BaseModel):
    app: AppSettings = AppSettings()
    server: ServerSettings = ServerSettings()
    database: DatabaseSettings = DatabaseSettings()
    auth: AuthSettings = AuthSettings()
    rag: RagSettings = RagSettings()
    ai_framework: AiFrameworkSettings = AiFrameworkSettings()
    logging: LoggingSettings = LoggingSettings()
    domain: DomainSettings = DomainSettings()

    openai_api_key: str | None = None
    groq_api_key: str | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_settings() -> Settings:
    config_path = BACKEND_ROOT / os.getenv("CONFIG_PATH", "config/config.yaml")
    raw = _load_yaml(config_path)

    settings = Settings(**raw) if raw else Settings()

    # Environment variables always win over YAML for secrets/deployment values.
    settings.auth.secret_key = os.getenv("SECRET_KEY", settings.auth.secret_key)
    settings.database.url = os.getenv("DATABASE_URL", settings.database.url)
    settings.app.environment = os.getenv("ENVIRONMENT", settings.app.environment)
    settings.app.debug = os.getenv("DEBUG", str(settings.app.debug)).lower() == "true"
    settings.openai_api_key = os.getenv("OPENAI_API_KEY") or None
    settings.groq_api_key = os.getenv("GROQ_API_KEY") or None

    if os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"):
        settings.auth.access_token_expire_minutes = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])

    return settings


def get_backend_root() -> Path:
    return BACKEND_ROOT
