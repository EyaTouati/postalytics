"""
Point d'entrée FastAPI — PostalBI La Poste Tunisienne.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import auth, dashboard, users, chatbot
from app.db.session import engine
from app.models.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Créer les tables si elles n'existent pas (utile en dev)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API PostalBI — Plateforme d'analyse prédictive des flux de colis",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "app": settings.APP_TITLE, "version": settings.APP_VERSION}
