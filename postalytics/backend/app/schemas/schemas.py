"""
Schémas Pydantic — validation des données d'entrée/sortie des API.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models.models import UserRole


# ── Auth ────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── Utilisateurs ────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole
    region_assignee: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    region_assignee: Optional[str] = None
    est_actif: Optional[bool] = None


class UserOut(UserBase):
    id: int
    est_actif: bool
    created_at: datetime

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()


# ── KPIs Dashboard ──────────────────────────────────────────────────────────────

class VolumeParRegion(BaseModel):
    region: str
    portee: str
    total_colis: int
    total_montant: float


class RepartitionNature(BaseModel):
    nature: str
    total: int
    pourcentage: float


class RepartitionService(BaseModel):
    type_service: str
    total: int
    pourcentage: float
    ca_total: float


class CAParDestination(BaseModel):
    pays: str
    portee: str
    ca_total: float
    volume: int


class EvolutionMensuelle(BaseModel):
    annee: int
    mois: int
    label: str  # "Jan 2024"
    volume: int
    ca: float


class KPIResume(BaseModel):
    """KPIs globaux affichés en haut du dashboard."""
    total_colis: int
    total_ca: float
    colis_international: int
    taux_international: float
    colis_anomalie: int


# ── Segmentation clients (Phase 3) ──────────────────────────────────────────────

class SegmentClient(BaseModel):
    segment: str
    nb_clients: int
    volume_moyen: float
    ca_moyen: float


# ── Prévisions (Phase 3) ─────────────────────────────────────────────────────────

class PrevisionVolume(BaseModel):
    label: str       # "Jan 2025"
    annee: int
    mois: int
    volume_prevu: float
    borne_inf: Optional[float] = None
    borne_sup: Optional[float] = None
    est_prevision: bool  # False = historique réel, True = prévision future


# ── Chatbot (Phase 4) ────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None   # retourné en mode debug
    sources: Optional[List[str]] = None
