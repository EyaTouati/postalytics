"""
Gestion de la session SQLAlchemy.
Remplacer DATABASE_URL dans .env pour pointer vers la vraie base de données.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # vérifie la connexion avant chaque requête
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency FastAPI — injecte une session DB dans les routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
