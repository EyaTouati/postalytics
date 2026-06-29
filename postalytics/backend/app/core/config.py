"""
Configuration centrale de l'application.
Toutes les variables d'environnement sont lues ici — jamais en dur dans le code.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── Base de données ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postalytics:postalytics@localhost:5432/postalytics_db"

    # ── JWT ─────────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # ── CORS ────────────────────────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── LLM (Phase 4) ───────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"  # "openai" | "mistral" | "mock"

    # ── App ─────────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_TITLE: str = "PostalBI — La Poste Tunisienne"
    APP_VERSION: str = "0.1.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
