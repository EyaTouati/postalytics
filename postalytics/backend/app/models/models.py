"""
Modèles SQLAlchemy — schéma en étoile La Poste Tunisienne.

Table de faits : fait_colis
Dimensions    : dim_client, dim_destination, dim_service, dim_temps, dim_origine
Utilisateurs  : users (authentification applicative)

NOTE : les noms de colonnes ici sont ceux du Data Warehouse (après ETL).
Quand les vraies données arrivent, seul le script ETL change — pas ces modèles.
"""
import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


# ── Enums métier ────────────────────────────────────────────────────────────────

class NatureColis(str, enum.Enum):
    MARCHANDISE = "Marchandise"
    DOCUMENT = "Document"


class TypeService(str, enum.Enum):
    NORMAL = "Normal"
    EXPRESS_NORMAL = "Express normal"
    EXPRESS_PERSONNALISE = "Express personnalisé"


class Portee(str, enum.Enum):
    NATIONAL = "National"
    INTERNATIONAL = "International"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RESPONSABLE = "responsable"
    AGENT_REGIONAL = "agent_regional"


# ── Dimension : Temps ────────────────────────────────────────────────────────────

class DimTemps(Base):
    __tablename__ = "dim_temps"

    id = Column(Integer, primary_key=True, index=True)
    date_complete = Column(Date, unique=True, nullable=False, index=True)
    jour = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    annee = Column(Integer, nullable=False, index=True)
    semaine = Column(Integer, nullable=False)
    jour_semaine = Column(String(20), nullable=False)  # "Lundi", "Mardi"…
    est_weekend = Column(Boolean, default=False)

    colis = relationship("FaitColis", back_populates="dim_temps")


# ── Dimension : Client ────────────────────────────────────────────────────────────

class DimClient(Base):
    __tablename__ = "dim_client"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=False)
    ville = Column(String(100), nullable=True)
    # Segment calculé par la Phase 3 (ML) — null jusqu'à l'exécution du notebook
    segment = Column(String(50), nullable=True)

    envois = relationship("FaitColis", foreign_keys="FaitColis.expediteur_id", back_populates="expediteur")
    receptions = relationship("FaitColis", foreign_keys="FaitColis.destinataire_id", back_populates="destinataire")


# ── Dimension : Origine ─────────────────────────────────────────────────────────

class DimOrigine(Base):
    __tablename__ = "dim_origine"

    id = Column(Integer, primary_key=True, index=True)
    ville = Column(String(100), nullable=False)
    region = Column(String(100), nullable=False, index=True)
    pays = Column(String(100), nullable=False, default="Tunisie")

    colis = relationship("FaitColis", back_populates="dim_origine")


# ── Dimension : Destination ─────────────────────────────────────────────────────

class DimDestination(Base):
    __tablename__ = "dim_destination"

    id = Column(Integer, primary_key=True, index=True)
    pays = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=True)
    portee = Column(Enum(Portee), nullable=False, index=True)

    colis = relationship("FaitColis", back_populates="dim_destination")


# ── Dimension : Service ─────────────────────────────────────────────────────────

class DimService(Base):
    __tablename__ = "dim_service"

    id = Column(Integer, primary_key=True, index=True)
    type_service = Column(Enum(TypeService), nullable=False, unique=True)
    tarif_base = Column(Float, nullable=False)
    delai_standard = Column(Integer, nullable=False)  # en jours

    colis = relationship("FaitColis", back_populates="dim_service")


# ── Table de faits : Colis ──────────────────────────────────────────────────────

class FaitColis(Base):
    __tablename__ = "fait_colis"

    id = Column(Integer, primary_key=True, index=True)
    num_colis = Column(String(50), unique=True, nullable=False, index=True)
    poids = Column(Float, nullable=False)
    montant = Column(Float, nullable=False)
    nature = Column(Enum(NatureColis), nullable=False, index=True)

    # Clés étrangères vers les dimensions
    temps_id = Column(Integer, ForeignKey("dim_temps.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("dim_service.id"), nullable=False)
    expediteur_id = Column(Integer, ForeignKey("dim_client.id"), nullable=False, index=True)
    destinataire_id = Column(Integer, ForeignKey("dim_client.id"), nullable=False)
    origine_id = Column(Integer, ForeignKey("dim_origine.id"), nullable=False, index=True)
    destination_id = Column(Integer, ForeignKey("dim_destination.id"), nullable=False, index=True)

    # Indicateur anomalie (Phase 3 ML) — null jusqu'à exécution du notebook
    est_anomalie = Column(Boolean, nullable=True, default=None)

    # Relations
    dim_temps = relationship("DimTemps", back_populates="colis")
    dim_service = relationship("DimService", back_populates="colis")
    expediteur = relationship("DimClient", foreign_keys=[expediteur_id], back_populates="envois")
    destinataire = relationship("DimClient", foreign_keys=[destinataire_id], back_populates="receptions")
    dim_origine = relationship("DimOrigine", back_populates="colis")
    dim_destination = relationship("DimDestination", back_populates="colis")


# ── Utilisateurs applicatifs (RBAC) ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    # Pour les agents régionaux : région assignée (null pour admin/responsable)
    region_assignee = Column(String(100), nullable=True)
    est_actif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
